from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user_model import User
from app.schemas.user_schema import UserCreate
from app.core.security import hash_password, verify_password
from app.services.authentication.email_service import send_verification_email
from app.core.security import create_jwt
from datetime import timedelta

class UserService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user(self, data: UserCreate) -> User:
        q = select(User).where((User.email == data.email) | (User.username == data.username))
        if (await self.db.execute(q)).scalar():
            raise ValueError("email_or_username_taken")

        user = User(
            username=data.username,
            email=data.email.lower(),
            password_hash=hash_password(data.password),
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        token = create_jwt(
            subject=str(user.id),
            expires_in=timedelta(hours=24),
            purpose="verify",
        )
        await send_verification_email(user, token)
        return user

    async def verify_email(self, user_id: str):
        user = await self.db.get(User, user_id)
        if not user:
            raise ValueError("user_not_found")
        user.is_verified = True
        await self.db.commit()

    async def authenticate(self, email_or_username: str, password: str) -> User | None:
        q = select(User).where(
            (User.email == email_or_username) | (User.username == email_or_username)
        )
        row = (await self.db.execute(q)).scalar_one_or_none()
        if row and verify_password(password, row.password_hash):
            return row
        return None