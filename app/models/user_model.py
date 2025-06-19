from sqlalchemy import UUID, Column, String, Boolean, DateTime, func
from datetime import datetime
from sqlalchemy.orm import declarative_base, Mapped, mapped_column
import uuid
from .base_model import Base  

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4  
    )
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email:    Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    is_active:   Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),       
        server_default=func.now()      
    )
