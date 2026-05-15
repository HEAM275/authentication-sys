from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from .role import RoleSchema

class UserSchema(BaseModel):

    uuid : UUID
    username : str
    email: str
    is_active: bool
    created_at : datetime
    roles: List[RoleSchema] = []

    model_config = ConfigDict(from_attributes= True)


class CreateUserSchema(BaseModel):

    username: str
    email: str
    password: str
    roles : List[UUID] | None = None

    @field_validator("password")
    @classmethod
    def validate_password_length(cls, v: str) -> str:
        byte_length = len(v.encode("utf-8"))
        if byte_length > 72:
            raise ValueError(f"Contraseña excede el límite de 72 bytes (tiene {byte_length})")
        return v


class UpdateUserSchema(BaseModel):

    username: str | None = None
    email: str | None = None
    password: str | None = None
    roles : List[UUID] | None = None
    is_active: bool | None = None