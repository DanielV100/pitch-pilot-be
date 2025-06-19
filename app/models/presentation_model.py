# app/models/presentation_and_training.py

from sqlalchemy import String, ForeignKey, Text, DateTime, Float
from sqlalchemy.orm import relationship, mapped_column, Mapped, declarative_base
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB  
import uuid
from datetime import datetime
from .base_model import Base  

class Presentation(Base):
    __tablename__ = "presentations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    tags: Mapped[list[str]] = mapped_column(ARRAY(String), default=[])
    file_url: Mapped[str] = mapped_column(String(255), nullable=True)
    # DEPRECATED: Remove this in future migration
    # findings: Mapped[dict] = mapped_column(JSONB, default=dict)

    trainings: Mapped[list["Training"]] = relationship(
        "Training", back_populates="presentation", cascade="all, delete", 
        lazy="selectin",  
    )

    finding_entries: Mapped[list["PresentationFinding"]] = relationship(
        "PresentationFinding",
        back_populates="presentation",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class Training(Base):
    __tablename__ = "trainings"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    presentation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("presentations.id"), nullable=False)
    total_score: Mapped[float] = mapped_column(Float, nullable=False)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    presentation: Mapped["Presentation"] = relationship("Presentation", back_populates="trainings")

class PresentationFinding(Base):
    __tablename__ = "presentation_findings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    presentation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("presentations.id", ondelete="CASCADE"), nullable=False
    )
    findings: Mapped[dict] = mapped_column(JSONB, default=dict)
    total_score: Mapped[float] = mapped_column(Float, nullable=False)
    cockpit_score: Mapped[float] = mapped_column(Float, nullable=True)
    flight_path_score: Mapped[float] = mapped_column(Float, nullable=True)
    altitude_score: Mapped[float] = mapped_column(Float, nullable=True)
    preflight_check_score: Mapped[float] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    is_active: Mapped[bool] = mapped_column(default=False)
    presentation: Mapped["Presentation"] = relationship("Presentation", back_populates="finding_entries")

