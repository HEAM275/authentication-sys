from typing import List, Optional
from uuid import UUID
from datetime import datetime
from fastapi import HTTPException, status
from sqlmodel import Session, select, func



from ..models.user import Role, UserRole, User
from ..schemas.role import RoleSchema, UserRoleSchema, CreateRoleSchema, UpdateRoleSchema

"""

====================
=== ROLE SERVICE ===
====================

"""


class RoleService:

    def __init__(self, db : Session):
        self.db = db


    def list_roles(self, offset: int =0, limit: int = 100) -> List[RoleSchema]:

        roles = self.db.exec(select(Role).offset(offset).limit(limit)).all()

        return [RoleSchema.model_validate(role) for role in roles]
    

    def get_role(self, role_uuid: UUID) -> RoleSchema:

        role = self.db.get(Role, role_uuid)
        if not role:
            raise HTTPException(
                status_code = status.HTTP_404_NOT_FOUND,
                detail= "Rol no encontrado"
            )
        return RoleSchema.model_validate(role)
    
    def create_role(self, role_data: CreateRoleSchema) -> RoleSchema:

        existing = self.db.exec(select(Role).where(Role.name == role_data.name)).first()
        if existing:
            raise HTTPException(
                status_code= status.HTTP_400_BAD_REQUEST,
                detail= "El rol ya existe"
            )
        
        role = Role(
            name= role_data.name,
            description=role_data.description
        )
        self.db.add(role)
        self.db.commit()
        self.db.refresh(role)

        return RoleSchema.model_validate(role)
    

    def update_role(self, role_uuid: UUID, role_data: UpdateRoleSchema) -> RoleSchema:
        
        role = self.db.get(Role, role_uuid)
        if not role:
            raise HTTPException(
                status_code= status.HTTP_404_NOT_FOUND
            )
        if role_data.name and role_data.name != role.name:
            existing = self.db.exec(
                select(Role).where(Role.name == role_data.name)
            ).first()
            if existing:
                raise HTTPException(
                    status_code= status.HTTP_400_BAD_REQUEST,
                    detail= "Otro rol ya tiene ese nombre"
                )
            
        update_data = role_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(role,key,value)
        self.db.add(role)
        self.db.commit()
        self.db.refresh(role)
        return RoleSchema.model_validate(role)
    

    def delete_role(self, role_uuid: UUID) -> None:

        role = self.db.get(Role, role_uuid)
        if not role:
            raise HTTPException(
                status_code= status.HTTP_404_NOT_FOUND
            )
        user_assigned = self.db.exec(
            select(UserRole).where(UserRole.role_id == role_uuid)
        ).first()
        if user_assigned:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se puede eliminar un rol asignado a usuarios"
            )

        self.db.delete(role)
        self.db.commit()

    """
    ========================================
    === GESTIÓN DE ASIGNACIÓN A USUARIOS ===
    ========================================
    """

    def assign_role_to_user(self, user_uuid: UUID, role_uuid: UUID) -> None:
        """Asigna un rol a un usuario."""
        user = self.db.get(User, user_uuid)
        role = self.db.get(Role, role_uuid)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rol no encontrado"
            )

        # Verificar si ya está asignado
        existing = self.db.exec(
            select(UserRole)
            .where(UserRole.user_id == user_uuid)
            .where(UserRole.role_id == role_uuid)
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El rol ya está asignado al usuario"
            )

        user_role = UserRole(user_id=user_uuid, role_id=role_uuid)
        self.db.add(user_role)
        self.db.commit()

    def remove_role_from_user(self, user_uuid: UUID, role_uuid: UUID) -> None:
        """Quita un rol de un usuario."""
        user_role = self.db.exec(
            select(UserRole)
            .where(UserRole.user_id == user_uuid)
            .where(UserRole.role_id == role_uuid)
        ).first()

        if not user_role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El usuario no tiene asignado ese rol"
            )

        self.db.delete(user_role)
        self.db.commit()

    def get_user_roles(self, user_uuid: UUID) -> List[RoleSchema]:
        """Obtiene todos los roles asignados a un usuario."""
        user = self.db.get(User, user_uuid)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )

        roles = self.db.exec(
            select(Role)
            .join(UserRole, UserRole.role_id == Role.uuid)
            .where(UserRole.user_id == user_uuid)
        ).all()

        return [RoleSchema.model_validate(role) for role in roles]