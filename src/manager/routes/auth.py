from fastapi import APIRouter, Depends, Request, status, Query, HTTPException
from sqlmodel import Session

from ...manager.schemas.user import CreateUserSchema
from ...core.database import get_db
from ..schemas.auth import LoginRequest, TokenResponse, RefreshRequest
from ..services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["AUTH"])

@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    client_ip = request.client.host
    if "x-forwarded-for" in request.headers:
        client_ip = request.headers["x-forwarded-for"].split(",")[0].strip()

    service = AuthService(db)
    return await service.login(data.email, data.password, client_ip)

@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    data: RefreshRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    service = AuthService(db)
    
    # Obtener el access token del header
    auth_header = request.headers.get("Authorization")
    access_token = None
    if auth_header and auth_header.startswith("Bearer "):
        access_token = auth_header.split(" ", 1)[1]
    
    # Revocar both tokens
    service.revoke_refresh_token(data.refresh_token)
    if access_token:
        await service.revoke_access_token(access_token)
    
    return {"message": "Sesion cerrada correctamente"}

@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    data: RefreshRequest,
    db: Session = Depends(get_db)
):
    service = AuthService(db)
    user = service.get_user_by_refresh_token(data.refresh_token)

    service.revoke_refresh_token(data.refresh_token)
    
    return service.create_tokens(str(user.uuid))


@router.post("/register",status_code=status.HTTP_200_OK)
def register_user(
    data: CreateUserSchema,
    db: Session = Depends(get_db)
): 
    service = AuthService(db)
    return service.register_user(user_data= data)

@router.get("/verify-email", status_code=status.HTTP_200_OK)
def verify_user_by_token(
    token: str = Query(...),
    db: Session = Depends(get_db)
):
    service = AuthService(db)
    try:
        service.verify_email_token(token)
        return {"message":"Correo verificado con exito, ya puede iniciar sesion"}
    except HTTPException:
        raise