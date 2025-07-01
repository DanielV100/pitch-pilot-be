from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from uuid import uuid4

from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.minio_helper import create_upload_urls, compose_to_single, download_object_to_tmpfile, public_object_url
from app.dependencies.auth_dep import get_session
from app.models.presentation_model import Blendshape, PresentationFinding, Training, TrainingResult
from minio import Minio
from app.utils.audio.audio_analysis_helper import analyse_local_file
from app.schemas.training_schema import SlideEvent
from app.services.training.training_service import TrainingService
from app.utils.eye_tracking.eye_tracking import calculate_eye_tracking, calculate_attention_score

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
    video_url = public_object_url(final_key)

    training = await db.get(Training, data.training_id)
    if training is None:
        raise HTTPException(404, "training not found")
    if data.slide_events:
        training.slide_events = [e.model_dump() for e in data.slide_events]
    blendshapes = (
        await db.execute(
            select(Blendshape)
            .where(Blendshape.training_id == data.training_id)
            .order_by(Blendshape.timestamp.asc())
        )
    ).scalars().all()

    blendshape_dicts = [
        {"timestamp": b.timestamp, "scores": b.scores}
        for b in blendshapes
    ]
    training_service = TrainingService(db)
    await training_service.set_video_url(training.id, video_url)
    tmp_path = download_object_to_tmpfile(final_key)
    audio_analysis = analyse_local_file(tmp_path)
    heatmap = {}
    attention_score = 0.0
    eye_tracking_results = None
    if blendshape_dicts:
        heatmap, _ = calculate_eye_tracking(blendshape_dicts)
        attention_score = calculate_attention_score(blendshape_dicts)
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
        await db.flush()

    await db.commit()
    await db.refresh(result)

    presentation_id = training.presentation_id

    finding = (
        await db.execute(
            select(PresentationFinding)
            .where(
                PresentationFinding.presentation_id == presentation_id,
                PresentationFinding.is_active == True
            )
            .order_by(desc(PresentationFinding.created_at))
            .limit(1)
        )
    ).scalars().first()

    if not finding:
        finding = (
            await db.execute(
                select(PresentationFinding)
                .where(PresentationFinding.presentation_id == presentation_id)
                .order_by(desc(PresentationFinding.created_at))
                .limit(1)
            )
        ).scalars().first()

    content_score = finding.total_score if finding else 0.0

    # 2. Calculate total score
    scores = [
        attention_score*100 if attention_score is not None else 0.0,
        audio_analysis["total_score"] if audio_analysis and "total_score" in audio_analysis else 0.0,
        content_score if content_score is not None else 0.0,
    ]
    total_score = sum(scores) / 3.0

    # 3. Save to training
    training.total_score = total_score
    await db.flush()

    return {
        "object": final_key,
        "url": video_url,
        "total_score": total_score,
        "analysis": {
            "audio": audio_analysis,
            "eye_tracking": eye_tracking_results
        },
        "result_id": str(result.id)
    }