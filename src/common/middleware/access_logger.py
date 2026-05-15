import logging
import os
import time
import json
from datetime import datetime, date
from typing import Any, Dict, Union, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from ...core.config import settings


#Directorio de logs ( a nivel de raiz)
LOG_DIR = os.path.join(os.getcwd(), "logs")
os.makedirs(LOG_DIR, exist_ok=True)


class AccessLoggerMiddleware(BaseHTTPMiddleware):
    """
    Middleware para registrar accesos a la API con info 
    """

    def __init__(self, app, app_name: str = "default"):
        super().__init__(app)
        self.app_name = str(app_name).replace("/","-").replace(" ","_"),
        self._setup_logger()

    def _setup_logger(self):
        """Configura el logger diario por aplicación"""
        log_filename = f"access_{self.app_name}_{date.today().strftime('%Y-%m-%d')}.log"
        lof_path = os.path.join(LOG_DIR, log_filename)

        self.logger = logging.getLogger(f"access_logger.{self.app_name}")
        self.logger.setLevel(logging.DEBUG)

        if self.logger.handlers:
            return
        
        handler = logging.FileHandler(lof_path, encoding= "utf-8")
        formatter = logging.Formatter(settings.LOG_FORMAT, datefmt="%Y-%M-%D %H:%M:%S")
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.propagate = False

    def _get_client_ip(self, request: Request) -> str:
        
        x_forwarded_for = request.headers.get("x-forwarded-for")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
    
    def _sanitize_recursive(self, data: Any) -> Any:

        SENSITIVE_KEYS = {"password", "token", "secret", "access_token", "refresh_token"}

        if isinstance(data, dict):
            sanitized = {}
            for k, v in data.items():
                key_lower = str(k).lower()
                if any(s in key_lower for s in SENSITIVE_KEYS):
                    sanitized[k] = "***"
                else:
                    sanitized[k] = self._sanitize_recursive(v)
            return sanitized
        elif isinstance(data, list):
            return [self._sanitize_recursive(item) for item in data]
        else:
            return data
        
    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()

        #obtener metadatos de la solicitud
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        query_params = dict(request.query_params)

        body = None
        if request.method in ("POST", "PUT", "PATCH"):
            try:
                body_bytes = await request.body()
                if body_bytes:
                    try:
                        body = json.loads(body_bytes.decode("utf-8"))
                        body = self._sanitize_recursive(body)
                    except (json.JSONDecodeError, UnicodeEncodeError):
                        body_str = body_bytes.decode("utf-8", errors="replace")
                        if any(kw in body_str.lower() for kw in ["password", "token", "secret"]):
                            body = "[sanitized text]"
                        else:
                            body = "[text/plain]"
            except Exception:
                body = "[failed to read body]"

        try:
            response = await call_next(request)
        except Exception as e:
            duration = time.time() - start_time
            self._log_entry(
                request=request,
                status_code=500,
                duration=duration,
                client_ip=client_ip,
                user_agent=user_agent,
                query_params=query_params,
                body=body,
                level="ERROR",
                error=str(e),
            )
            raise e
        duration = time.time() - start_time
        status_code = response.status_code

        if 500 <= status_code < 600:
            level = "ERROR"
        elif 400 <= status_code < 500:
            level = "WARNING"
        else:
            level = "INFO"

        self._log_entry(
            request=request,
            status_code=status_code,
            duration=duration,
            client_ip=client_ip,
            user_agent=user_agent,
            query_params=query_params,
            body=body,
            level=level,
        )
        
        return response
    
    def _log_entry(
        self,
        request: Request,
        status_code: int,
        duration: float,
        client_ip: str,
        user_agent: str,
        query_params: dict,
        body: Any,
        level: str,
        error: Optional[str] = None,
    ):
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "app_name": self.app_name,
            "method": request.method,
            "path": str(request.url.path),
            "query_params": query_params,
            "status_code": status_code,
            "duration_ms": round(duration * 1000, 2),
            "client_ip": client_ip,
            "user_agent": user_agent,
            "body": body,
        }
        if error:
            log_data["error"] = error

        message = json.dumps(log_data, ensure_ascii=False, separators=(",", ":"), default=str)

        if level == "ERROR":
            self.logger.error(message)
        elif level == "WARNING":
            self.logger.warning(message)
        else:
            self.logger.info(message)