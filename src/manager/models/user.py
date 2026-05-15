from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional
from datetime import datetime, timedelta
from uuid import UUID, uuid4

class UserRole(SQLModel, table= True):
    __tablename__ = "user_role"
    __table_args__ = {"schema": "auth_sys"}

    user_id: UUID = Field(foreign_key="auth_sys.users.uuid", primary_key=True)
    role_id: UUID = Field(foreign_key="auth_sys.roles.uuid", primary_key=True)

class User(SQLModel, table= True):
    __tablename__= "users"
    __table_args__= {"schema":"auth_sys"}

    uuid : UUID = Field(default_factory= uuid4, primary_key=True)
    username: str = Field(unique= True, index= True, max_length=50)
    email: str = Field(unique= True, index= True, max_length= 100)
    hashed_password: str
    is_active: bool = Field(default= True)
    created_at: datetime = Field(default_factory= datetime.now)
    email_verified: bool = Field(default= False)
    roles: List['Role'] = Relationship(back_populates="users", link_model=UserRole)


class Role(SQLModel, table= True):
    __tablename__= "roles"
    __table_args__ = {"schema": "auth_sys"}

    uuid: UUID = Field(default_factory=uuid4, primary_key= True)
    name: str = Field(unique= True, max_length=50)
    description: Optional[str] = Field(default=None, max_length=200)

    users: List["User"] = Relationship(back_populates="roles", link_model=UserRole)