from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from jose import jwt
from app.core.config import settings  

pwd_ctx = CryptContext(
    schemes=["argon2"], 
    deprecated="auto"
)

def hash_password(plain: str) -> str:
    return pwd_ctx.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)



def create_jwt(subject: str, expires_in: timedelta, purpose: str = "access") -> str:
    now   = datetime.now(timezone.utc)
    to_encode = {
        "sub": subject,
        "prp": purpose,                       
        "exp": int((now + expires_in).timestamp()),
    }
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGO)

