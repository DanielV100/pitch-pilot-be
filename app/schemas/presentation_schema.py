from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional
import uuid
from datetime import datetime
from app.schemas.training_schema import TrainingOut, TrainingOutSlim  

class PresentationCreate(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str]
    tags: List[str] = []
    file_url: Optional[str] = None

class PresentationFindingOut(BaseModel):
    id: uuid.UUID
    findings: dict
    total_score: float
    cockpit_score: Optional[float]
    flight_path_score: Optional[float]
    altitude_score: Optional[float]
    preflight_check_score: Optional[float]
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PresentationOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: Optional[str]
    tags: List[str]
    file_url: Optional[str]
    trainings: List[TrainingOut] = []
    finding_entries: List[PresentationFindingOut] = []

    model_config = ConfigDict(from_attributes=True)

class PresentationOutSlim(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: Optional[str]
    tags: List[str]
    file_url: Optional[str]
    trainings: List[TrainingOutSlim] = []

    model_config = ConfigDict(from_attributes=True)



