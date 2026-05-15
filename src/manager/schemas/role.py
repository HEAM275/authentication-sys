from pydantic import BaseModel, ConfigDict
from uuid import UUID


class RoleSchema(BaseModel):

    uuid : UUID
    name : str
    description: str | None = None

    model_config = ConfigDict(from_attributes= True)

class CreateRoleSchema(BaseModel):

    name: str
    description: str | None = None

class UpdateRoleSchema(CreateRoleSchema):
    pass


class UserRoleSchema(BaseModel):
    user_id: UUID
    role_id: UUID

    model_config = ConfigDict(from_attributes=True)