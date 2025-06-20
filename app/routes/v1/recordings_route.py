from fastapi import APIRouter, Depends, HTTPException
from uuid import uuid4

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.minio_helper import create_upload_urls, compose_to_single
from app.utils.minio_helper import public_object_url
from app.dependencies.auth_dep import get_session
from app.models.presentation_model import Training

router = APIRouter()
class StartPayload(BaseModel):
    training_id: str

class FinishPayload(BaseModel):
    training_id: str
    prefix: str


@router.post("/start")
def start_recording(data: StartPayload):
    prefix = f"{data.training_id}/{uuid4()}"
    urls = create_upload_urls(prefix)
    return {"prefix": prefix, "urls": urls}

@router.post("/finish", response_model=dict[str, str])
async def finish_recording(
    data: FinishPayload, db: AsyncSession = Depends(get_session)
):
    final_key = f"{data.training_id}/{data.prefix.split('/')[-1]}.webm"
    compose_to_single(data.prefix, final_key)
    training: Training | None = await db.get(Training, data.training_id)
    if training is None:
        raise HTTPException(404, "training not found")

    training.video_url = public_object_url(final_key)
    db.commit()

    return {"object": final_key, "url": training.video_url}
