from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_session
from app.services.presentation.presentation_service import PresentationService
from app.schemas.presentation_schema import PresentationCreate, PresentationOut
from app.models.user_model import User
from app.dependencies.auth_dep import get_current_user
from app.models.presentation_model import Presentation, Training

router = APIRouter()

@router.post("/add-presentation", response_model=PresentationOut, status_code=status.HTTP_201_CREATED)
async def create_presentation(
    payload: PresentationCreate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    service = PresentationService(db)
    return await service.create_presentation(current_user.id, payload)

@router.get("/get-presentations", response_model=list[PresentationOut])
async def get_presentations_for_current_user(
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Presentation).where(Presentation.user_id == current_user.id)
    )
    return result.scalars().all()
