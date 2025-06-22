from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from uuid import uuid4

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.minio_helper import create_upload_urls, compose_to_single, download_object_to_tmpfile, public_object_url
from app.dependencies.auth_dep import get_session
from app.models.presentation_model import Training, TrainingResult
from minio import Minio
from app.utils.audio.audio_analysis_helper import analyse_local_file
from app.schemas.training_schema import SlideEvent

router = APIRouter()
class StartPayload(BaseModel):
    training_id: str

class FinishPayload(BaseModel):
    training_id: str
    prefix: str
    slide_events: Optional[List[SlideEvent]] = None


@router.post("/start")
def start_recording(data: StartPayload):
    prefix = f"{data.training_id}/{uuid4()}"
    urls = create_upload_urls(prefix)
    return {"prefix": prefix, "urls": urls}


@router.post("/finish", response_model=dict)
async def finish_recording(
    data: FinishPayload, db: AsyncSession = Depends(get_session)
):
    final_key = f"{data.training_id}/{data.prefix.split('/')[-1]}.webm"
    compose_to_single(data.prefix, final_key)

    training = await db.get(Training, data.training_id)
    if training is None:
        raise HTTPException(404, "training not found")
    
    if data.slide_events:
        training.slide_events = [e.model_dump() for e in data.slide_events]

    tmp_path = download_object_to_tmpfile(final_key)
    analysis = analyse_local_file(tmp_path)

    stmt = select(TrainingResult).where(TrainingResult.training_id == data.training_id)
    existing_result = await db.execute(stmt)
    existing_result = existing_result.scalar_one_or_none()

    if existing_result:
        existing_result.audio_scores = analysis
        existing_result.audio_total_score = analysis["total_score"]
        existing_result.created_at = datetime.now(timezone.utc)
        result = existing_result
    else:
        result = TrainingResult(
            training_id=data.training_id,
            audio_scores=analysis,
            audio_total_score=analysis["total_score"],
            created_at=datetime.now(timezone.utc)
        )
        db.add(result)

    await db.commit()
    await db.refresh(result)

    return {
        "object": final_key,
        "url": public_object_url(final_key),
        "analysis": analysis,
        "result_id": str(result.id)
    }


