from fastapi import APIRouter, Depends, status, HTTPException
from sqlmodel import Session
from typing import List
from uuid import UUID


from ...common.auth.dependencies import get_current_user, require_role
from ...common.auth.user import AppUser
from ...core.database import get_db
from ..schemas.role import RoleSchema
from ..schemas.user import UserSchema, CreateUserSchema, UpdateUserSchema
from ..services.user import UserService

router = APIRouter(prefix="/users", tags=["USERS"])


@router.get(
    "/",
    response_model=List[UserSchema],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_role("admin"))],  # Solo admin puede listar
)
def list_users(
    db: Session = Depends(get_db),
    offset: int = 0,
    limit: int = 100,
):
    service = UserService(db)
    return service.list_users(offset=offset, limit=limit)


@router.get(
    "/{user_uuid}",
    response_model=UserSchema,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_role("admin"))],
)
def get_user(
    user_uuid: UUID,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    service = UserService(db)
    user = service.get_user(user_uuid)

    # Solo el propio usuario o un admin puede ver el perfil completo
    if not current_user.is_authenticated:
        raise HTTPException(status_code=401, detail="No autenticado")
    if str(current_user.user_id) != str(user_uuid) or "admin" not in current_user.roles:
        raise HTTPException(status_code=403, detail="Acceso denegado")

    return user


@router.post(
    "/",
    response_model=UserSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin"))],  # Solo admin crea usuarios
)
def create_user(
    user_data: CreateUserSchema,
    db: Session = Depends(get_db),
):
    service = UserService(db)
    return service.create_user(user_data)


@router.put(
    "/{user_uuid}",
    response_model=UserSchema,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_role("admin"))],
)
def update_user(
    user_uuid: UUID,
    user_data: UpdateUserSchema,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    service = UserService(db)
    
    # Validar permisos
    if not current_user.is_authenticated:
        raise HTTPException(status_code=401, detail="No autenticado")
    if str(current_user.user_id) != str(user_uuid) and "admin" not in current_user.roles:
        raise HTTPException(status_code=403, detail="No puedes editar este usuario")

    return service.update_user(user_uuid, user_data)


@router.delete(
    "/{user_uuid}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_role("admin"))],  # Solo admin desactiva
)
def delete_user(
    user_uuid: UUID,
    db: Session = Depends(get_db),
):
    service = UserService(db)
    service.delete_user(user_uuid)
    return {"message": "Usuario desactivado correctamente"}


# ========================
# Rutas de gestión de roles (delegadas al RoleService)
# ========================

@router.post(
    "/{user_uuid}/roles/{role_uuid}",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin"))],
)
def assign_role_to_user(
    user_uuid: UUID,
    role_uuid: UUID,
    db: Session = Depends(get_db),
):
    service = UserService(db)
    service.assign_role_to_user(user_uuid, role_uuid)
    return {"message": "Rol asignado correctamente"}


@router.delete(
    "/{user_uuid}/roles/{role_uuid}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_role("admin"))],
)
def remove_role_from_user(
    user_uuid: UUID,
    role_uuid: UUID,
    db: Session = Depends(get_db),
):
    service = UserService(db)
    service.remove_role_from_user(user_uuid, role_uuid)
    return {"message": "Rol eliminado correctamente"}


@router.get(
    "/{user_uuid}/roles",
    response_model=List[RoleSchema],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_role("admin"))],
)
def get_user_roles(
    user_uuid: UUID,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    # Validar acceso
    if not current_user.is_authenticated:
        raise HTTPException(status_code=401, detail="No autenticado")
    if str(current_user.user_id) != str(user_uuid) and "admin" not in current_user.roles:
        raise HTTPException(status_code=403, detail="Acceso denegado")

    service = UserService(db)
    return service.get_user_roles(user_uuid)