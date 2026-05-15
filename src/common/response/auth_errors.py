from fastapi.responses import JSONResponse
from fastapi import status
from typing import Optional

class AuthErrorResponse:
    """Modelo interno para estructurar errores de autenticación."""
    def __init__(self, detail: str, error_code: str):
        self.detail = detail
        self.error_code = error_code

    def to_dict(self) -> dict:
        return {"detail": self.detail, "error_code": self.error_code}


def unauthorized_response(
    detail: str = "No autorizado",
    error_code: str = "AUTH_001"
) -> JSONResponse:
    """Error 401: Usuario no autenticado o credenciales inválidas."""
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content=AuthErrorResponse(detail, error_code).to_dict(),
        headers={"WWW-Authenticate": "Bearer"},
    )


def forbidden_response(
    detail: str = "Acceso denegado",
    error_code: str = "AUTH_002"
) -> JSONResponse:
    """Error 403: Usuario autenticado pero sin permisos suficientes."""
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content=AuthErrorResponse(detail, error_code).to_dict(),
    )


def token_expired_response() -> JSONResponse:
    """Error 401: Token JWT ha expirado."""
    return unauthorized_response(
        detail="Token expirado",
        error_code="AUTH_003"
    )


def token_invalid_response() -> JSONResponse:
    """Error 401: Token JWT mal formado, firma inválida o corrupto."""
    return unauthorized_response(
        detail="Token inválido",
        error_code="AUTH_004"
    )


def token_blacklisted_response() -> JSONResponse:
    """Error 401: Token JWT ha sido revocado (lista negra)."""
    return unauthorized_response(
        detail="Token revocado",
        error_code="AUTH_005"
    )


def user_inactive_response() -> JSONResponse:
    """Error 401: Cuenta de usuario desactivada."""
    return unauthorized_response(
        detail="Cuenta inactiva",
        error_code="AUTH_006"
    )


def invalid_credentials_response() -> JSONResponse:
    """Error 401: Email o contraseña incorrectos."""
    return unauthorized_response(
        detail="Credenciales inválidas",
        error_code="AUTH_007"
    )


def insufficient_permissions_response() -> JSONResponse:
    """Error 403: Rol o permiso insuficiente para la acción solicitada."""
    return forbidden_response(
        detail="Permisos insuficientes",
        error_code="AUTH_008"
    )