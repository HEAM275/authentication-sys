# src/common/auth/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ..auth.token import create_app_user_from_token
from ..auth.user import AppUser, AnonymousAppUser

# Esquema de seguridad: Bearer Token
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> AppUser:
    """
    Dependencia para endpoints protegidos.
    Lanza 401 si el token es inválido o no está presente.
    """
    user = create_app_user_from_token(credentials.credentials)
    if not user.is_authenticated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

async def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(security, use_cache=False)
) -> AppUser:
    """
    Dependencia para endpoints con acceso opcional (ej. landing page).
    Si el token es inválido, devuelve un AnonymousAppUser.
    """
    if not credentials or not credentials.credentials:
        return AnonymousAppUser()
    return create_app_user_from_token(credentials.credentials)

def require_role(required_role: str):
    def role_checker(current_user: AppUser = Depends(get_current_user)) -> AppUser:
        if not current_user.is_authenticated:
            raise HTTPException(status_code=401, detail="No autenticado")
        
        if required_role not in current_user.roles:
            raise HTTPException(status_code=403, detail=f"Se requiere rol '{required_role}'")
        return current_user
    return role_checker
    