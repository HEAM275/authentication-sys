from fastapi import APIRouter, HTTPException, Query
from ...utils.email import send_verification_email
import uuid

router = APIRouter(prefix="/test", tags=["Test"])

@router.get("/send-test-email")
async def send_test_email(to_email: str = Query(..., description=" email de prueba")):

    fake_token = str(uuid.uuid4())

    try:
        await send_verification_email(to_email, fake_token)
        return {"message": f"Correo de prueba enviado a {to_email}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al enviar correo: {str(e)}")