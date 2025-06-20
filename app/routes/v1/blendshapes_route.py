import json
import uuid
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.db.database import get_session
from app.services.blendshapes_service import BlendshapeService
from app.models.presentation_model import Blendshape
from pydantic import BaseModel, Field
from typing import List
from app.schemas.blendshapes_schema import BlendshapeOut

router = APIRouter()

class BlendshapeInput(BaseModel):
    training_id: UUID
    timestamp: float = Field(..., example=12.345)
    scores: dict = Field(..., example={"jawOpen": 0.23, "eyeBlinkLeft": 0.05})


@router.websocket("/ws/add")
async def stream_blendshapes_batch(
    websocket: WebSocket,
    db: AsyncSession = Depends(get_session)
):
    await websocket.accept()
    service = BlendshapeService(db)

    buffer = []
    BATCH_SIZE = 30  

    try:
        while True:
            message = await websocket.receive_text()
            try:
                payload = json.loads(message)
                buffer.append({
                    "training_id": uuid.UUID(payload["training_id"]),
                    "timestamp": payload["timestamp"],
                    "scores": payload["scores"],
                })

                if len(buffer) >= BATCH_SIZE:
                    await service.add_blendshapes_bulk(buffer)
                    buffer.clear()

            except Exception as e:
                print(f"[WS] Error parsing message: {e}")
    except WebSocketDisconnect:
        print("[WS] Disconnected, flushing buffer...")
        if buffer:
            await service.add_blendshapes_bulk(buffer)



@router.get("/{training_id}", response_model=List[BlendshapeOut])
async def get_blendshapes_by_training(
    training_id: UUID,
    db: AsyncSession = Depends(get_session)
):
    service = BlendshapeService(db)
    frames = await service.get_blendshapes_by_training(training_id)
    if not frames:
        raise HTTPException(status_code=404, detail="No blendshapes found for this training")
    return frames
