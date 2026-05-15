"""
⚠️ DEPRECATED: Este módulo ya NO se usa.

El envío de correos se ha migrado a usar el servicio email-service mediante
peticiones HTTP. Ver src/utils/email.py para la implementación actual.

Este archivo se mantiene por referencia histórica y compatibilidad.
"""

from fastapi_mail import FastMail, ConnectionConfig, MessageType, MessageSchema
from src.core.config import settings

def get_mail_client() -> FastMail:
    config = ConnectionConfig(
        MAIL_USERNAME=settings.SMTP_USER,
        MAIL_PASSWORD=settings.SMTP_PASSWORD,
        MAIL_FROM=settings.SMTP_FROM_EMAIL,
        MAIL_PORT=settings.SMTP_PORT,
        MAIL_SERVER=settings.SMTP_HOST,
        MAIL_FROM_NAME=settings.SMTP_FROM_NAME,
        MAIL_STARTTLS=True,
        MAIL_SSL_TLS=False,
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=True,
    )
    return FastMail(config)

def create_message(
    recipients: list[str],
    subject: str,
    body: str,
    subtype: MessageType = MessageType.html
) -> MessageSchema:
    
    
    return MessageSchema(
        recipients= recipients,
        subject= subject,
        body= body,
        subtype= subtype,
    )