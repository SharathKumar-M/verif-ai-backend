from datetime import datetime
from typing import Optional, Literal
from beanie import Document, Indexed
from pydantic import Field, EmailStr

class User(Document):
    firebase_uid: str = Indexed(unique=True)
    email: EmailStr = Indexed()
    role: Literal["student", "recruiter"]
    display_name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "users"
        indexes = ["firebase_uid", "email"]
