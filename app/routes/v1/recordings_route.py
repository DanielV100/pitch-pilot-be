# routes/recording.py
from fastapi import APIRouter, Depends
from uuid import uuid4

from pydantic import BaseModel
from app.utils.minio_helper import create_upload_urls, compose_to_single

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


@router.post("/finish")
def finish_recording(data: FinishPayload):
    final_name = f"{data.training_id}/{data.prefix.split('/')[-1]}.webm"
    compose_to_single(data.prefix, final_name)
    # TODO: save `final_name` to Postgres
    return {"object": final_name}
