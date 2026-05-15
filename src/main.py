import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .common.middleware.access_logger import AccessLoggerMiddleware
from .common.middleware.token_blacklist import TokenBlacklistMiddleware

# Rutas
from .manager.routes.user import router as user_router
from .manager.routes.role import router as role_router
from .manager.routes.auth import router as auth_router
from .manager.routes.test_routes import router as test

from .common.exceptions.handlers import (
    auth_exception_handler,
    validation_exception_handler,
    integrity_exception_handler,
    general_exception_handler,
)

from .common.exceptions.custom import AuthError
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError

# Configurar logging global
logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL))

app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(AccessLoggerMiddleware, app_name="auth-system")
app.add_middleware(TokenBlacklistMiddleware)

app.add_exception_handler(AuthError, auth_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(IntegrityError, integrity_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Rutas
app.include_router(auth_router)   
app.include_router(user_router)   
app.include_router(role_router)
app.include_router(test)

@app.get("/health", tags=["HEALTH"])
def health_check():
    return {"status": "ok", "service": "auth-system"}