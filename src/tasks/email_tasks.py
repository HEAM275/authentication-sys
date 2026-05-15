# src/tasks/email_tasks.py
import asyncio
from ..core.celery_app import celery_app
from ..utils.email import send_verification_email


@celery_app.task(bind=True, max_retries=3)
def send_verification_email_task(self, email: str, token: str):
    """
    Tarea de Celery para enviar correos de verificación.
    Intenta enviar hasta 3 veces ante fallos.
    """
    try:
        # Esta función se ejecuta en el worker de Celery (es síncrona)
        asyncio.run(send_verification_email(email, token))
    except Exception as exc:
        # Reintentar con backoff exponencial
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
