# src/core/config.py
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict
from datetime import datetime, timezone


class Settings(BaseSettings):
    """
    Configuración central del sistema de autenticación.
    Todas las variables se leen automáticamente desde .env.
    """

    # ========================================
    # 🔌 CONFIGURACIÓN DE BASE DE DATOS
    # ========================================

    DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/sys_database",
        description="URL de conexión a PostgreSQL. Usa 'postgresql+asyncpg://' si usas async."
    )
    # → Define la conexión a la base de datos donde se almacenan usuarios, roles, logs, etc.

    DATABASE_SCHEMA: str = Field(
        default="public",
        description="Esquema de PostgreSQL. Útil si usas múltiples esquemas."
    )
    ALEMBIC_SCHEMA: str = Field(default="auth_sys")
    # → Permite organizar tablas en esquemas separados (por ejemplo, por entorno o microservicio).

    # ========================================
    # 🔐 CONFIGURACIÓN DE JWT (AUTENTICACIÓN)
    # ========================================

    SECRET_KEY: str = Field(
        description="Clave secreta para firmar tokens JWT. ¡Debe ser larga, aleatoria y secreta!"
    )
    # → Esencial para la seguridad. Si alguien la conoce, puede generar tokens válidos.
    # → En producción: genera con `openssl rand -base64 48`

    ALGORITHM: str = Field(
        default="HS256",
        description="Algoritmo de firma JWT. HS256 es suficiente para la mayoría de casos."
    )
    # → Algoritmo criptográfico para firmar tokens. No cambies a menos que necesites RS256.

    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        description="Duración del token de acceso (en minutos)."
    )
    # → Token corto: se usa en cada solicitud. Renovable con refresh token.

    REFRESH_TOKEN_EXPIRE_MINUTES: int = Field(
        default=1440,  # 24 horas
        description="Duración del token de refresco (en minutos)."
    )
    # → Token largo: usado para obtener un nuevo access token sin volver a loguearse.

    # ========================================
    # 🧠 CONFIGURACIÓN DE REDIS
    # ========================================

    REDIS_URL: str = Field(
        default="redis://127.0.0.1:6380/0",
        description="URL completa para conectar a Redis."
    )
    # → Usado para: lista negra de tokens, caché, y como broker de Celery.

    REDIS_HOST: str = Field(default="localhost", description="Host de Redis.")
    REDIS_PORT: int = Field(default=6380, description="Puerto de Redis.")
    REDIS_DB: int = Field(default=0, description="Base de datos de Redis (0-15).")
    REDIS_PASSWORD: str = Field(default='NONE')
    # → Útil si necesitas conectarte a Redis con parámetros separados (ej. en Docker).

    # ========================================
    # 🧵 CONFIGURACIÓN DE CELERY (TAREAS ASÍNCRONAS)
    # ========================================

    CELERY_BROKER_URL: str = Field(
        default="redis://127.0.0.1:6379/0",
        description="URL del broker de mensajes para Celery."
    )
    # → Donde Celery escucha nuevas tareas (Redis, RabbitMQ, etc.).

    CELERY_RESULT_BACKEND: str = Field(
        default="redis://127.0.0.1:6379/0",
        description="Backend para almacenar resultados de tareas."
    )
    # → Donde se guardan los resultados de las tareas (puede ser la misma URL que el broker).

    CELERY_TASK_TIME_LIMIT: int = Field(
        default=300,
        description="Límite de tiempo para una tarea (en segundos)."
    )
    # → Si una tarea dura más, se cancela automáticamente.

    CELERY_WORKER_CONCURRENCY: int = Field(
        default=4,
        description="Número de tareas concurrentes por worker."
    )
    # → Útil para ajustar el consumo de recursos en producción.

    # ========================================
    # ✉️ CONFIGURACIÓN DE CORREO ELECTRÓNICO (SMTP)
    # ========================================

    SMTP_HOST: str = Field(default="smtp.gmail.com", description="Servidor SMTP.")
    SMTP_PORT: int = Field(default=587, description="Puerto SMTP (587 para TLS).")
    SMTP_USER: str = Field(default="your-email@gmail.com", description="Usuario SMTP.")
    SMTP_PASSWORD: str = Field(default="your-app-password", description="Contraseña o app password.")
    SMTP_FROM_NAME: str = Field(default="Servicio de Autenticación", description="Nombre del remitente.")
    SMTP_FROM_EMAIL: str = Field(default="your-email@gmail.com", description="Email del remitente.")
    # → Usado para enviar emails: bienvenida, recuperación de contraseña, alertas, etc.

    # ========================================
    # 🌐 METADATOS DE LA API (FastAPI)
    # ========================================

    API_TITLE: str = Field(default="API de Autenticación", description="Título de la API.")
    API_DESCRIPTION: str = Field(default="Sistema central de autenticación y gestión de usuarios.", description="Descripción de la API.")
    API_VERSION: str = Field(default="1.0.0", description="Versión semántica de la API.")
    API_HOST: str = Field(default="127.0.0.1", description="Host de desarrollo.")
    API_PORT: int = Field(default=8000, description="Puerto de desarrollo.")
    # → Información que aparece en la documentación de Swagger.

    # ========================================
    # 📝 CONFIGURACIÓN DE LOGGING
    # ========================================

    LOG_LEVEL: str = Field(default="INFO", description="Nivel de logs: DEBUG, INFO, WARNING, ERROR.")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Formato de los mensajes de log."
    )
    LOG_FILE: Optional[str] = Field(
        default=None,
        description="Archivo donde guardar logs. Si es None, usa stdout."
    )
    # → Permite rastrear errores, accesos y eventos del sistema.

    # ========================================
    # 🌍 CONFIGURACIÓN DE ENTORNO
    # ========================================

    ENVIRONMENT: str = Field(default="development", description="Entorno: development, staging, production.")
    DEBUG: bool = Field(default=True, description="Habilita modo debug (solo en desarrollo).")
    # → Cambia el comportamiento de la app según el entorno (ej. más logs en dev).

    # ========================================
    # 🔄 CONFIGURACIÓN DE CORS
    # ========================================

    ALLOWED_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:5173",
        description="Dominios permitidos para CORS (separados por comas)."
    )

    @property
    def allowed_origins_list(self) -> List[str]:
        """Convierte la cadena de orígenes en una lista limpia."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]
    # → Permite que el frontend (React, Vue, etc.) haga peticiones a esta API.

    # ========================================
    # 🛡️ CONFIGURACIÓN DE SEGURIDAD
    # ========================================

    MAX_LOGIN_ATTEMPTS: int = Field(
        default=5,
        description="Máximo de intentos de login antes de bloquear temporalmente."
    )
    LOGIN_LOCKOUT_TIME: int = Field(
        default=300,  # 5 minutos
        description="Tiempo de bloqueo tras intentos fallidos (en segundos)."
    )
    AUDIT_ENABLED: bool = Field(
        default=True,
        description="Habilita el registro de eventos de auditoría."
    )
    AUDIT_RETENTION_DAYS: int = Field(
        default=30,
        description="Días que se conservan los logs de auditoría."
    )
    TASK_TIMEOUT: int = Field(
        default=300,
        description="Tiempo máximo de ejecución de tareas asíncronas (segundos)."
    )
    # → Protege contra ataques de fuerza bruta y permite rastrear accesos.

    # ========================================
    # 🔗 CONFIGURACIÓN DE SERVICIOS EXTERNOS
    # ========================================

    AUTH_SERVICE_URL: str = Field(
        default="http://localhost:8000",
        description="URL base del servicio de autenticación (útil para otros microservicios)."
    )
    RESERVAS_SERVICE_URL: str = Field(
        default="http://localhost:8001",
        description="URL base del servicio de reservas (o cualquier otro microservicio)."
    )
    EMAIL_SERVICE_URL: str = Field(
        default="http://localhost:8002",
        description="URL base del servicio de correo electrónico."
    )
    # → Permite que otros servicios se comuniquen con este sistema.

    FRONTEND_URL: str = Field(default="http://localhost:5173")

    model_config = ConfigDict(
        env_file=Path(__file__).resolve().parent.parent.parent / ".env",
        env_file_encoding = "utf-8",
        case_sensitive = False,
    )

    def now(self) -> datetime:
        return datetime.now(timezone.utc)

# Instancia global de configuración
settings = Settings()