from fastapi.responses import JSONResponse
from fastapi import status
from datetime import datetime
from src.common.response.error_schema import ErrorResponse

def error_response(
    detail: str,
    error_code: str,
    status_code: int = status.HTTP_400_BAD_REQUEST,
    include_timestamp: bool = False,
) -> JSONResponse:
    
    content = {"detail": detail,
              "error_code": error_code}
    if include_timestamp:
        content["timestamp"] = datetime.utcnow().isoformat()
    return JSONResponse(status_code=status_code, content= content)