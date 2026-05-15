# src/common/auth/token.py
from jose import jwt, JWTError
from typing import Optional
from ..auth.user import AppUser, AnonymousAppUser
from ...core.config import settings

def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None

def create_app_user_from_token(token: str) -> AppUser:
    payload = decode_token(token)
    if payload:
        return AppUser(
            user_id=payload.get("sub"),
            username=payload.get("username"),
            email=payload.get("email"),
            email_verified= payload.get("email_verified", False),
            roles=payload.get("roles", []),
            permissions=payload.get("permissions", []),
        )
    return AnonymousAppUser()

