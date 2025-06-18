from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt
from app.db.database import get_session          
from app.schemas.user_schema import UserCreate, UserLogin, UserOut
from app.services.authentication.user_authentication_service import UserService
from app.core.config import settings
from datetime import timedelta
from app.core.security import create_jwt

router = APIRouter()


@router.post("/signup", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def signup(payload: UserCreate, db: AsyncSession = Depends(get_session)):
    service = UserService(db)
    try:
        user = await service.create_user(payload)
        return user
    except ValueError as e:
        if str(e) == "email_or_username_taken":
            raise HTTPException(status_code=400, detail="Email or username already taken")
        raise


@router.get("/verify")
async def verify_email(token: str, db: AsyncSession = Depends(get_session)):
    try:
        data = jwt.decode(token, settings.JWT_SECRET, [settings.JWT_ALGO])
        if data.get("prp") != "verify":
            raise HTTPException(400, "invalid_token")
        user_id: str = data["sub"]
    except JWTError:
        raise HTTPException(status_code=400, detail="invalid_or_expired_token")

    service = UserService(db)
    await service.verify_email(user_id)
    return {"message": "Email verified successfully"}


@router.post("/login")
async def login(form: UserLogin, db: AsyncSession = Depends(get_session)):
    service = UserService(db)
    if not form.email: 
        user = await service.authenticate(form.username, form.password)
    else:
        user = await service.authenticate(form.email, form.password)
    if not user or not user.is_verified:
        raise HTTPException(status_code=401, detail="invalid_credentials")
    access = create_jwt(
        subject=str(user.id),
        expires_in=timedelta(minutes=30),
        purpose="access",
    )
    return {"access_token": access, "token_type": "bearer"}
