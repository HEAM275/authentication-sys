from fastapi import APIRouter, Depends, status
from sqlmodel import Session
from typing import List, Annotated, Optional
from uuid import UUID


from ...common.auth.dependencies import get_current_user, require_role
from ...common.auth.user import AppUser
from ...core.database import get_db

from ..schemas.role import RoleSchema, CreateRoleSchema, UpdateRoleSchema
from ..services.role import RoleService


router = APIRouter(prefix="/roles", tags=['ROLES'])


@router.get('/', response_model=List[RoleSchema], 
            status_code= status.HTTP_200_OK,
            dependencies=[Depends(require_role("admin"))],)
def list(
    db: Session = Depends(get_db),
    offset : int = 0,
    limit : int = 100
):
    service = RoleService(db)
    return service.list_roles(offset= offset, limit= limit)

@router.get('/{uuid}', response_model = RoleSchema,
            status_code= status.HTTP_200_OK,
            dependencies=[Depends(require_role("admin"))],)
def read_role(
    uuid: UUID,
    db: Session = Depends(get_db)
):
    service= RoleService(db)
    return service.get_role(uuid)

@router.post('/', response_model = RoleSchema, 
            status_code= status.HTTP_201_CREATED,
            dependencies=[Depends(require_role("admin"))],
            )
def create_role(
    data : CreateRoleSchema,
    db: Session = Depends(get_db),
):
    service = RoleService(db)
    return service.create_role(data)

@router.put('/{uuid}', response_model= RoleSchema,
            status_code= status.HTTP_200_OK,
            dependencies=[Depends(require_role("admin"))],)
def update_role(
    data: UpdateRoleSchema,
    uuid : UUID,
    db: Session = Depends(get_db)
    ):
    service = RoleService(db)

    return service.update_role(uuid, data)

@router.delete('/{uuid}', 
            status_code= status.HTTP_200_OK,
            dependencies=[Depends(require_role("admin"))],)
def delete_role(
    uuid: UUID,
    db: Session = Depends(get_db)
):
    service = RoleService(db)
    return service.delete_role(uuid)