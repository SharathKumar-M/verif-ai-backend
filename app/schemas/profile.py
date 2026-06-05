from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class ProfileBase(BaseModel):
    display_name: str
    bio: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    domain: Optional[str] = None
    location: Optional[str] = None
    is_public: bool = False

class ProfileUpdate(BaseModel):
    display_name: Optional[str] = None
    bio: Optional[str] = None
    skills: Optional[List[str]] = None
    domain: Optional[str] = None
    location: Optional[str] = None
    is_public: Optional[bool] = None

class ProfileResponse(ProfileBase):
    firebase_uid: str
    trust_score: float = 0.0
    verdict: Optional[str] = None
    verified_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
