from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.presentation_model import Presentation
from app.models.presentation_model import Training

class TrainingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_training(self, presentation_id, data):
        training = Training(
            presentation_id=presentation_id,
            total_score=data.total_score,
            date=data.date or datetime.now(timezone.utc),
        )
        self.db.add(training)
        await self.db.commit()
        await self.db.refresh(training)
        return training


