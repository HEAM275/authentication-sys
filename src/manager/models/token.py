from datetime import datetime, timedelta, timezone
from sqlmodel import SQLModel, Field
from uuid import UUID
from ...core.config import settings

class RefreshToken(SQLModel, table= True):
    
    __tablename__= "refresh_tokens"
    __table_args__= {"schema": "auth_sys"}

    id: int = Field(default=None, primary_key=True)
    token: str = Field(unique=True, index= True)
    user_id: UUID = Field(foreign_key="auth_sys.users.uuid")
    expires_at: datetime = Field()
    revoked: bool = Field(default= False)

    def is_expired(self) -> bool:
        now = settings.now()  # UTC
        expires_at = self.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        else:
            expires_at = expires_at.astimezone(timezone.utc)
        return now > expires_at

class EmailVerificationToken(SQLModel, table= True):

    __tablename__= "email_verification_tokens"
    __table_args__= {"schema": "auth_sys"}

    id: int = Field(default= None, primary_key= True)
    user_id: UUID = Field(foreign_key= "auth_sys.users.uuid")
    token: str = Field(unique= True, index= True)
    expires_at: datetime = Field()
    used: bool = Field(default= False)