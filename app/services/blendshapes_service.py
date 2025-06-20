# app/services/blendshape_service.py

import uuid
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.presentation_model import  Blendshape


class BlendshapeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_blendshapes_bulk(self, items: list[dict]) -> None:
        objects = [
            Blendshape(
                training_id=item["training_id"],
                timestamp=item["timestamp"],
                scores=jsonable_encoder(item["scores"]),
            )
            for item in items
        ]
        self.db.add_all(objects)
        await self.db.commit()
        
    async def get_blendshapes_by_training(
        self, training_id: uuid.UUID
    ) -> list[Blendshape]:
        from sqlalchemy import select

        result = await self.db.execute(
            select(Blendshape).where(Blendshape.training_id == training_id)
        )
        return result.scalars().all()
