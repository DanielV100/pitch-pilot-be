from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.db.database import get_session
from app.services.training.training_service import TrainingService
from app.schemas.training_schema import TrainingCreate, TrainingOut
from app.models.presentation_model import Presentation

router = APIRouter()

@router.post(
    "/{presentation_id}/add-training",
    response_model=TrainingOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_training(
    presentation_id: UUID,
    training_data: TrainingCreate,
    db: AsyncSession = Depends(get_session),
):
    service = TrainingService(db)
    result = await db.execute(select(Presentation).where(Presentation.id == presentation_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Presentation not found")

    training = await service.add_training(presentation_id, training_data)
    return training
