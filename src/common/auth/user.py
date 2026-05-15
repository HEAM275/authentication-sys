# src/common/auth/user.py
from typing import Optional, List
from pydantic import BaseModel
from uuid import UUID

class AppUser(BaseModel):
    user_id: Optional[UUID] = None
    username: Optional[str] = None
    email: Optional[str] = None
    email_verified: bool = False
    roles: List[str] = []
    permissions: List[str] = []

    @property
    def is_authenticated(self) -> bool:
        return self.user_id is not None

class AnonymousAppUser(AppUser):
    
    @property
    def is_authenticated(self) -> bool:
        return False
    
    def __init__(self):
        super().__init__(
            user_id=None,
            username=None,
            email=None,
            email_verified= False,
            roles=[],
            permissions=[],
        )