from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from jose import jwt, JWTError
from ...common.response.auth_errors import (
    unauthorized_response,
    token_invalid_response,
    token_blacklisted_response,
)
from ...core.cache import redis_client
from ...core.config import settings
import logging

logger = logging.getLogger(__name__)

class TokenBlacklistMiddleware(BaseHTTPMiddleware):

    """
    """
    PUBLIC_PATHS = {
        "/auth/verify-email",
        "/auth/login",
        "/auth/logout",
        "/auth/refresh",
        "/auth/register",
        "/health",
        "/",
        "/docs",
        "/openapi.json",
        "/redoc",
    }

    async def dispatch(self, request: Request, call_next) -> Response:
        print("🔍 Middleware ejecutado para:", request.url.path)
        if request.url.path in self.PUBLIC_PATHS:
            return await call_next(request)
        
        # 1 obtener el token de la request
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            return unauthorized_response(
                detail= "Token de autenticacion requerido",
                error_code="AUTH_001"
            )
        
        token = auth_header.split(" ",1)[1]
        
        #2 try to decodificarlo
        try:
            jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        except JWTError:
            return token_invalid_response()
        
        try: 
            is_blacklisted = await redis_client.exists(f"blacklist:{token}")
            if is_blacklisted:
                return token_blacklisted_response()
        except Exception as e:
            logger.error(f"Error al conectar con Redis: {e}")

            return unauthorized_response(
                detail = "Error de autenticacion temporal try later",
                error_code= "AUTH_009"
            )
        response = await call_next(request)
        return response