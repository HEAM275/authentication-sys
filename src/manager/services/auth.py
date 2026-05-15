import asyncio
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, Request, status
from sqlmodel import Session, select

import hashlib
import secrets
from jose import jwt

from ...common.exceptions.custom import AuthError
from ...core.cache import redis_client
from ...core.config import settings
from ...manager.models.token import EmailVerificationToken, RefreshToken
from ...manager.models.user import User, Role
from ...manager.schemas.user import CreateUserSchema, UserSchema
from ...manager.services.role import RoleService
from ...utils.security import verify_password, generate_secure_token, get_password_hash
from ...utils.email import send_verification_email
from ...tasks.email_tasks import send_verification_email_task


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.role_service = RoleService(db)
        self.redis = redis_client

    # ==============================
    # PROTECCIÓN CONTRA FUERZA BRUTA
    # ==============================

    async def is_login_blocked(self, email: str, ip: str) -> bool:
        """Verifica si el login está bloqueado por email o IP."""
        email_key = f"login_block:email:{email}"
        ip_key = f"login_block:ip:{ip}"
        email_blocked = await self.redis.exists(email_key)
        ip_blocked = await self.redis.exists(ip_key)
        return bool(email_blocked or ip_blocked)

    async def record_failed_login(self, email: str, ip: str) -> int:
        """Registra un intento fallido y devuelve el número actual de intentos."""
        MAX_ATTEMPTS = 5
        BLOCK_DURATION = 300  # 5 minutos en segundos

        email_attempts_key = f"login_attempts:email:{email}"
        ip_attempts_key = f"login_attempts:ip:{ip}"

        email_attempts = await self.redis.incr(email_attempts_key)
        ip_attempts = await self.redis.incr(ip_attempts_key)

        if email_attempts == 1:
            await self.redis.expire(email_attempts_key, BLOCK_DURATION)
        if ip_attempts == 1:
            await self.redis.expire(ip_attempts_key, BLOCK_DURATION)

        if email_attempts >= MAX_ATTEMPTS:
            await self.redis.setex(f"login_block:email:{email}", BLOCK_DURATION, "blocked")
        if ip_attempts >= MAX_ATTEMPTS:
            await self.redis.setex(f"login_block:ip:{ip}", BLOCK_DURATION, "blocked")

        return max(email_attempts, ip_attempts)

    async def reset_login_attempts(self, email: str, ip: str) -> None:
        """Resetea los contadores tras login exitoso."""
        await self.redis.delete(f"login_attempts:email:{email}")
        await self.redis.delete(f"login_attempts:ip:{ip}")

    # ==============================
    # AUTENTICACIÓN Y REGISTRO
    # ==============================

    def authenticate_user(self, email: str, password: str) -> User:
        user = self.db.exec(select(User).where(User.email == email)).first()
        if not user or not user.is_active:
            raise AuthError(detail="Credenciales inválidas", error_code="AUTH_001")
        if not user.email_verified:
            raise AuthError(detail="Verifica tu correo antes de iniciar sesión",error_code="AUTH_001",
                            status_code=403,)
        if not verify_password(password, user.hashed_password):
            raise AuthError(detail="Credenciales inválidas", error_code="AUTH_001")
        return user

    async def login(self, email: str, password: str, client_ip: str) -> dict:
        """Login con protección contra fuerza bruta."""
        # 1. Verificar bloqueo
        if await self.is_login_blocked(email, client_ip):
            raise AuthError(
                detail="Demasiados intentos fallidos. Inténtalo de nuevo más tarde.",
                error_code="AUTH_010",
                status_code=429,
            )

        # 2. Intentar autenticar
        try:
            user = self.authenticate_user(email, password)
        except AuthError:
            # Registrar intento fallido
            await self.record_failed_login(email, client_ip)
            raise  # Re-lanzar el error

        # 3. Resetear contadores y crear tokens
        await self.reset_login_attempts(email, client_ip)
        return self.create_tokens(str(user.uuid))

    def create_tokens(self, user_uuid: str) -> dict:
        refresh_token = generate_secure_token(128)
        refresh_token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()

        db_token = RefreshToken(
            token=refresh_token_hash,
            user_id=user_uuid,
            expires_at=settings.now() + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES),
        )
        self.db.add(db_token)
        self.db.commit()

        user = self.db.exec(select(User).where(User.uuid == user_uuid)).first()
        role_names = [role.name for role in user.roles]

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = self._create_access_token(
            data={
                "sub": str(user_uuid),
                "username": user.username,
                "email": user.email,
                "roles": role_names,
            },
            expires_delta=access_token_expires
        )
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    def _create_access_token(self, data: dict, expires_delta: timedelta) -> str:
        to_encode = data.copy()
        expire = settings.now() + expires_delta
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    # ==============================
    # TOKENS DE REFRESCO
    # ==============================

    def revoke_refresh_token(self, refresh_token: str) -> None:
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        token = self.db.exec(
            select(RefreshToken).where(RefreshToken.token == token_hash)
        ).first()
        if token and not token.revoked:
            token.revoked = True
            self.db.add(token)
            self.db.commit()

    async def revoke_access_token(self, access_token: str) -> None:
        """
        Agrega el access_token a la lista negra en Redis.
        El token será válido hasta su fecha de expiración.
        """
        try:
            # Decodificar el token sin validar la firma para obtener el tiempo de expiración
            decoded = jwt.decode(
                access_token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            
            # Obtener el tiempo de expiración (exp) del token
            exp_timestamp = decoded.get("exp")
            if not exp_timestamp:
                return
            
            # Calcular TTL (time to live) en segundos
            current_time = datetime.now(timezone.utc).timestamp()
            ttl = int(exp_timestamp - current_time)
            
            # Solo agregar a blacklist si aún no ha expirado
            if ttl > 0:
                await self.redis.setex(
                    f"blacklist:{access_token}",
                    ttl,
                    "blacklisted"
                )
        except Exception as e:
            # Log error pero no falla el logout
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error al agregar token a blacklist: {e}")

    def get_user_by_refresh_token(self, refresh_token: str) -> User:
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        token = self.db.exec(
            select(RefreshToken)
            .where(RefreshToken.token == token_hash)
            .where(RefreshToken.revoked == False)
        ).first()
        if not token or token.is_expired():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
        user = self.db.get(User, token.user_id)
        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario inactivo")
        return user

    # ==============================
    # REGISTRO
    # ==============================

    def register_user(self, user_data: CreateUserSchema) -> dict:
        if self.db.exec(select(User).where(User.email == user_data.email)).first():
            raise HTTPException(status_code=400, detail="Email ya registrado")
        if self.db.exec(select(User).where(User.username == user_data.username)).first():
            raise HTTPException(status_code=400, detail="Nombre de usuario no válido")

        hashed_password = get_password_hash(user_data.password)
        customer = self.db.exec(select(Role).where(Role.name == "customer")).first()

        user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            is_active=True,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        if customer:
            self.role_service.assign_role_to_user(user.uuid, customer.uuid)

        raw_token = secrets.token_urlsafe(64)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

        verification = EmailVerificationToken(
            user_id= user.uuid,
            token= token_hash,
            expires_at= expires_at,
            used= False
        )
        self.db.add(verification)
        self.db.commit()

        send_verification_email_task.delay(user.email, raw_token)

        return {"message": "Usuario registrado. Revisa tu correo para confirmar."}

    def verify_email_token(self, raw_token: str) -> None:
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        token_record = self.db.exec(
            select(EmailVerificationToken).where(EmailVerificationToken.token == token_hash)
        ).first()

        if not token_record:
            raise HTTPException(status_code=400, detail="Token inválido")
        if token_record.used:
            raise HTTPException(status_code=400, detail="Token ya usado")
        if token_record.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="Token expirado")

        user = self.db.get(User, token_record.user_id)
        if not user:
            raise HTTPException(status_code=400, detail="Usuario no encontrado")

        user.email_verified = True
        token_record.used = True
        self.db.add(user)
        self.db.add(token_record)
        self.db.commit()