from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional
import uuid
from uuid import UUID
from datetime import datetime
from enum import Enum

class VisibilityMode(str, Enum):
    solo = "solo"       
    private = "private"
    

class DifficultyLevel(str, Enum):
    easy   = "easy"
    medium = "medium"
    hard   = "hard"
    
class EyeCalibration(BaseModel):
    """Shape your front-end actually sends; keep it open-ended for now."""
    points: list[dict]

class TrainingCreate(BaseModel):
    duration_seconds: int = Field(..., gt=0)
    visibility_mode: VisibilityMode
    difficulty: DifficultyLevel
    eye_calibration: Optional[EyeCalibration] = None
    date: Optional[datetime] = None 

class TrainingOut(BaseModel):
    id: UUID
    presentation_id: UUID
    duration_seconds: int
    visibility_mode: VisibilityMode
    difficulty: DifficultyLevel
    eye_calibration: Optional[EyeCalibration]
    total_score: float
    date: datetime
    video_url: Optional[str]  

    model_config = ConfigDict(from_attributes=True)

class TrainingScorePatch(BaseModel):
    total_score: float = Field(..., ge=0)




