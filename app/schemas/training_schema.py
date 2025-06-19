from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional
import uuid
from datetime import datetime

class TrainingCreate(BaseModel):
    total_score: float
    date: Optional[datetime] = None

class TrainingOut(BaseModel):
    id: uuid.UUID
    presentation_id: uuid.UUID
    total_score: float
    date: datetime

    model_config = ConfigDict(from_attributes=True)   