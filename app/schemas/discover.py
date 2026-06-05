from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.profile import ProfileResponse

class DiscoveryQuery(BaseModel):
    skills: List[str] = Field(default_factory=list)
    min_trust_score: float = 0.0
    domain: Optional[str] = None
    location: Optional[str] = None
    limit: int = 20
    offset: int = 0

class DiscoveryResponse(BaseModel):
    total: int
    results: List[ProfileResponse]

class ShortlistRequest(BaseModel):
    student_uid: str

class ShortlistResponse(BaseModel):
    success: bool
    message: str
