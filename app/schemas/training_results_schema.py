from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

class TrainingResultCreate(BaseModel):
    training_id: UUID
    eye_tracking_scores: Optional[dict] = Field(
        default=None, example={"center": 0.92, "left": 0.07, "right": 0.01}
    )
    eye_tracking_total_score: Optional[float] = Field(
        default=None, example=0.88
    )
    audio_scores: Optional[dict] = Field(
        default=None, example={"clarity": 0.91, "volume": 0.76}
    )
    audio_total_score: Optional[float] = Field(
        default=None, example=0.82
    )

class TrainingResultOut(BaseModel):
    id: UUID
    training_id: UUID
    eye_tracking_scores: Optional[dict]
    eye_tracking_total_score: Optional[float]
    audio_scores: Optional[dict]
    audio_total_score: Optional[float]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
