import httpx
from ..core.config import settings


async def send_verification_email(to_email: str, token: str) -> None:
    """
    Envía un correo de verificación de email usando el servicio de correo
    (email-service).
    
    Este método hace una petición HTTP al servicio email-service en lugar
    de intentar enviar directamente por SMTP.
    """
    verify_url = f"{settings.AUTH_SERVICE_URL}/auth/verify-email?token={token}"

    body = f"""
    <p>Gracias por registrarte</p>
    <p>Por favor, confirma tu correo haciendo clic en el enlace</p>
    <a href="{verify_url}" style="display:inline-block;padding:10px 20px;background:#007bff;color:white;text-decoration:none;border-radius:4px;">
        Confirmar correo
    </a>
    <p>El enlace expira en 24 horas.</p>
    """

    payload = {
        "to_email": to_email,
        "subject": "Confirma tu cuenta",
        "body": body
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{settings.EMAIL_SERVICE_URL}/email/send",
                json=payload
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            print(f"Error al enviar correo de verificación a {to_email}: {str(e)}")
            raise
