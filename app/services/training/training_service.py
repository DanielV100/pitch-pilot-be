from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.presentation_model import Presentation
from app.models.presentation_model import Training
from app.schemas.training_schema import TrainingCreate
from uuid import UUID

class TrainingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_training(
        self, presentation_id: UUID, dto: TrainingCreate
    ) -> Training:
        instance = Training(
            presentation_id=presentation_id,
            duration_seconds=dto.duration_seconds,
            visibility_mode=dto.visibility_mode,
            difficulty=dto.difficulty,
            eye_calibration=dto.eye_calibration.model_dump()
            if dto.eye_calibration
            else None,
            total_score=0.0,                      
            date=dto.date or datetime.utcnow(),
        )
        self.db.add(instance)
        await self.db.commit()
        await self.db.refresh(instance)
        return instance

    async def set_score(self, training_id: UUID, score: float) -> Training:
        training: Training | None = await self.db.get(Training, training_id)
        if training is None:
            raise LookupError("Training not found")
        training.total_score = score
        await self.db.commit()
        await self.db.refresh(training)
        return training

    



