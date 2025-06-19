from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field
from typing import List, Optional

class Finding(BaseModel):
    type: int = Field(..., description="1: Typos, 2: Topic Depth, 3: Structure, 4: Visuals")
    text_excerpt: str
    suggestion: str
    explanation: str
    confidence: int
    importance: int
    severity: int

class SlideFindings(BaseModel):
    page: int
    findings: List[Finding]

class FindingsResponse(BaseModel):
    slides: List[SlideFindings]

class PresentationFindingOut(BaseModel):
    id: UUID
    presentation_id: UUID
    findings: dict
    total_score: float
    cockpit_score: Optional[float]
    flight_path_score: Optional[float]
    altitude_score: Optional[float]
    preflight_check_score: Optional[float]
    created_at: datetime
    is_active: bool

    model_config = {"from_attributes": True}