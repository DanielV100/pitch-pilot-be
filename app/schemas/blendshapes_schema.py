from pydantic import BaseModel
from typing import List
from uuid import UUID

class BlendshapeEntry(BaseModel):
    index: int
    score: float
    categoryName: str
    displayName: str

class BlendshapeOut(BaseModel):
    id: UUID
    training_id: UUID
    timestamp: float
    scores: List[BlendshapeEntry]

    class Config:
        model_config = {"from_attributes": True}
