from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional
import uuid
from datetime import datetime

class PresentationCreate(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str]
    tags: List[str] = []
    findings: Optional[dict] = {}
    file_url: Optional[str] = None

class PresentationOut(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str]
    tags: List[str]
    findings: dict
    file_url: Optional[str]
    user_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)   