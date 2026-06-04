from datetime import datetime
from typing import Optional, Literal, Annotated, Any
from pydantic import BaseModel, EmailStr, Field, BeforeValidator

# Helper to convert MongoDB ObjectId to str
def str_validator(v: Any) -> str:
    if v is None:
        return None
    return str(v)

class UserSyncRequest(BaseModel):
    firebase_uid: str
    email: EmailStr
    role: Literal["student", "recruiter"]
    display_name: Optional[str] = None

class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    role: Literal["student", "recruiter"]
    display_name: Optional[str] = None

class UserResponse(BaseModel):
    # Using 'id' and allowing it to be populated from '_id' or 'id'
    id: Annotated[str, BeforeValidator(str_validator)] = Field(alias="_id")
    firebase_uid: str
    email: EmailStr
    role: str
    display_name: Optional[str] = None
    created_at: datetime

    class Config:
        populate_by_name = True
        from_attributes = True
        # Explicitly handle common MongoDB/Beanie patterns
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class RoleUpdateRequest(BaseModel):
    role: Literal["student", "recruiter"]
