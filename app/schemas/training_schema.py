from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional
import uuid
from uuid import UUID
from datetime import datetime
from enum import Enum
from .training_results_schema import TrainingResultOut

class VisibilityMode(str, Enum):
    solo = "solo"       
    private = "private"
    
class SlideEvent(BaseModel):
    timestamp: float
    page: int

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
    slide_events: Optional[List[SlideEvent]] = None

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
    slide_events: Optional[List[SlideEvent]]  
    training_results: List[TrainingResultOut] = []

    model_config = ConfigDict(from_attributes=True)

class TrainingScorePatch(BaseModel):
    total_score: float = Field(..., ge=0)




