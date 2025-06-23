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
from app.utils.eye_tracking import calculate_eye_tracking
from app.schemas.training_schema import SlideEvent
from app.services.training.training_service import TrainingService

router = APIRouter()
class StartPayload(BaseModel):
    training_id: str

class FinishPayload(BaseModel):
    training_id: str
    prefix: str
    slide_events: Optional[List[SlideEvent]] = None
    blendshapes: Optional[list] = None  # <--- NEU


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
    video_url = public_object_url(final_key)

    training = await db.get(Training, data.training_id)
    if training is None:
        raise HTTPException(404, "training not found")
    
    if data.slide_events:
        training.slide_events = [e.model_dump() for e in data.slide_events]

    training_service = TrainingService(db)
    await training_service.set_video_url(training.id, video_url)
    tmp_path = download_object_to_tmpfile(final_key)
    audio_analysis = analyse_local_file(tmp_path)

    heatmap, attention_score = None, None
    eye_tracking_results = None
    if data.blendshapes:
        heatmap, attention_score = calculate_eye_tracking(data.blendshapes)
        eye_tracking_results = {"scores": heatmap, "total_score": attention_score}

    stmt = select(TrainingResult).where(TrainingResult.training_id == data.training_id)
    existing_result = await db.execute(stmt)
    existing_result = existing_result.scalar_one_or_none()

    if existing_result:
        existing_result.audio_scores = audio_analysis
        existing_result.audio_total_score = audio_analysis["total_score"]
        if heatmap is not None:
            existing_result.eye_tracking_scores = heatmap
            existing_result.eye_tracking_total_score = attention_score
        existing_result.created_at = datetime.now(timezone.utc)
        result = existing_result
    else:
        result = TrainingResult(
            training_id=data.training_id,
            audio_scores=audio_analysis,
            audio_total_score=audio_analysis["total_score"],
            eye_tracking_scores=heatmap,
            eye_tracking_total_score=attention_score,
            created_at=datetime.now(timezone.utc)
        )
        db.add(result)
        print(f"[DB-DEBUG] Added new TrainingResult to session: {result}")
        await db.flush()
        print(f"[DB-DEBUG] After flush, TrainingResult id: {result.id}")

    try:
        await db.commit()
        print(f"[DB-DEBUG] After commit, TrainingResult id: {result.id}")
    except Exception as e:
        print(f"[DB-ERROR] Commit failed: {e}")
        raise
    await db.refresh(result)
    print(f"[DB-DEBUG] Committed and refreshed TrainingResult {result.id}")
    print(f"[DB-DEBUG] Final TrainingResult: audio_scores={result.audio_scores}, audio_total_score={result.audio_total_score}, eye_tracking_scores={result.eye_tracking_scores}, eye_tracking_total_score={result.eye_tracking_total_score}")

    return {
        "object": final_key,
        "url": video_url,
        "analysis": {
            "audio": audio_analysis,
            "eye_tracking": eye_tracking_results
        },
        "result_id": str(result.id)
    }


