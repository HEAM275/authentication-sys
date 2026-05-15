# src/auth/services/user_service.py
from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlmodel import Session, select

from ..models.user import User,Role
from ..schemas.user import UserSchema, CreateUserSchema, UpdateUserSchema
from ..schemas.role import RoleSchema
from .role import RoleService  # ← dependencia explícita

from ...utils.security import get_password_hash  # ← hashea contraseñas



""" 
=====================
=== USER SERVICES ===
=====================
"""

class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.role_service = RoleService(db)  # 👈 reutiliza la lógica de roles

    def create_user(self, user_data: CreateUserSchema) -> UserSchema:
        """Crea un nuevo usuario y opcionalmente le asigna roles."""
        # Verificar unicidad
        if self.db.exec(select(User).where(User.email == user_data.email)).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email ya registrado"
            )
        if self.db.exec(select(User).where(User.username == user_data.username)).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nombre de usuario ya en uso"
            )

        # Hashear contraseña
        hashed_password = get_password_hash(user_data.password)

        # Crear usuario
        user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            is_active=True,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        # Asignar roles si se proporcionan
        if user_data.roles:
            for role_uuid in user_data.roles:
                self.role_service.assign_role_to_user(user.uuid, role_uuid)

        return UserSchema.model_validate(user)

    def get_user(self, user_uuid: UUID) -> UserSchema:
        user = self.db.get(User, user_uuid)
        if not user or user.is_active == False:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        return UserSchema.model_validate(user)

    def list_users(self, offset: int = 0, limit: int = 100) -> List[UserSchema]:
        users = self.db.exec(select(User).where(User.is_active == True).offset(offset).limit(limit)).all()
        return [UserSchema.model_validate(u) for u in users]

    def update_user(self, user_uuid: UUID, user_data: UpdateUserSchema) -> UserSchema:
        user = self.db.get(User, user_uuid)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )

        update_data = user_data.model_dump(exclude_unset=True)

        if "roles" in update_data:
            role_uuids = update_data.pop("roles")
            if role_uuids is not None:
                roles = self.db.exec(select(Role).where(Role.uuid.in_(role_uuids))).all()
                print(roles)
                if len(roles) != len(role_uuids):
                    raise HTTPException(status_code=400,
                                        detail="Rol no existente")
        # Actualizar contraseña si se envía
        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))

        # Verificar unicidad de email/username (si cambian)
        if "email" in update_data and update_data["email"] != user.email:
            if self.db.exec(select(User).where(User.email == update_data["email"])).first():
                raise HTTPException(400, "Email ya en uso")
        if "username" in update_data and update_data["username"] != user.username:
            if self.db.exec(select(User).where(User.username == update_data["username"])).first():
                raise HTTPException(400, "Nombre de usuario ya en uso")

        # Aplicar cambios
        for key, value in update_data.items():
            setattr(user, key, value)

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        if role_uuids is not None:
            user.roles.clear()
            self.db.commit()

            for role_uuid in role_uuids:
                self.assign_role_to_user(user.uuid, role_uuid)

        return UserSchema.model_validate(user)

    def delete_user(self, user_uuid: UUID) -> None:
        """Desactiva (no elimina) al usuario por seguridad."""
        user = self.db.get(User, user_uuid)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        user.is_active = False
        self.db.add(user)
        self.db.commit()

    # === OPERACIONES DE ROLES (delegadas a RoleService) ===

    def assign_role_to_user(self, user_uuid: UUID, role_uuid: UUID) -> None:
        """Delega a RoleService."""
        self.role_service.assign_role_to_user(user_uuid, role_uuid)

    def remove_role_from_user(self, user_uuid: UUID, role_uuid: UUID) -> None:
        """Delega a RoleService."""
        self.role_service.remove_role_from_user(user_uuid, role_uuid)

    def get_user_roles(self, user_uuid: UUID) -> List[RoleSchema]:
        """Delega a RoleService."""
        return self.role_service.get_user_roles(user_uuid)