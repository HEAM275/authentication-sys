from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError

from ...common.response.error_schema import ErrorResponse
from ...common.exceptions.custom import AuthError
from ...core.config import settings

import logging

logger = logging.getLogger(__name__)

async def auth_exception_handler(request: Request, exc: AuthError):

    return JSONResponse(
        status_code= exc.status_code,
        content= ErrorResponse(
            detail= exc.detail,
            error_code=exc.error_code
        ).model_dump(),
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):

    logger.warning(f"Validation error in {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code= status.HTTP_422_UNPROCESSABLE_CONTENT,
        content= ErrorResponse(
            detail= "Datos de entrada inválidos",
            error_code="VALIDATION_ERROR"
        ).model_dump(),
    )

async def integrity_exception_handler(request: Request, exc: IntegrityError):

    logger.error(f"Integrity error in {request.url.path}: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ErrorResponse(
            detail="Violación de integridad: dato ya existente o inválido",
            error_code= "INTEGRITY_ERROR"
        ).model_dump(),
    )

async def general_exception_handler(request: Request, exc: Exception):

    logger.error(f"Unexpected error in {request.url.path}: {str(exc)}", exc_info=True)
    if settings.ENVIRONMENT == "development":
        detail = str(exc)
        error_code = "DEBUG_INTERNAL_ERROR"
    else:
        detail= "Error interno del servidor"
        error_code = "INTERNAL_ERROR"
    return JSONResponse(
        status_code= status.HTTP_500_INTERNAL_SERVER_ERROR,
        content= ErrorResponse(
            detail=detail,
            error_code= error_code
        ).model_dump(),
    )