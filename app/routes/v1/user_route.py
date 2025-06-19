from fastapi import APIRouter, Cookie, Depends
from app.schemas.user_schema import UserDAO
from app.dependencies.auth_dep import get_current_user
from app.models.user_model import User

router = APIRouter()

@router.get("/get-captain", response_model=UserDAO)
async def get_captain(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/debug-cookies")
async def debug_cookie(pp_token: str | None = Cookie(None)):
    return {"pp_token": pp_token}