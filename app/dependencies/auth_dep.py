from fastapi import Depends, Cookie, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_jwt
from app.db.database import get_session
from app.models.user_model import User


async def get_current_user(
    db: AsyncSession = Depends(get_session),
    pp_token: str | None = Cookie(None),
) -> User:
    """
    Resolve the user corresponding to the access-token cookie.

    Raises 401 if token is missing, invalid, expired, or user not found.
    """
    if not pp_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    try:
        payload = decode_jwt(pp_token)
        if payload.get("prp") != "access":
            raise ValueError
        user_id: str = payload["sub"]
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    return user
