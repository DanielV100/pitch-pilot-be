from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional
import uuid
from uuid import UUID
from datetime import datetime

class TrainingCreate(BaseModel):
    total_score: float
    date: Optional[datetime] = None


class TrainingOut(BaseModel):
    id: UUID
    presentation_id: UUID
    total_score: float
    date: datetime

    model_config = ConfigDict(from_attributes=True)

