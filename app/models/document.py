from datetime import datetime
from typing import Optional, Literal
from beanie import Document as BeanieDocument, Indexed, PydanticObjectId
from pydantic import Field

class Document(BeanieDocument):
    firebase_uid: str = Indexed()
    type: Literal["resume", "certificate", "github"]
    gridfs_id: Optional[PydanticObjectId] = None
    github_url: Optional[str] = None
    filename: Optional[str] = None
    mime_type: Optional[str] = None
    hash_sha256: str
    size_bytes: int = 0
    status: Literal["pending", "analyzing", "done", "failed"] = "pending"
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "documents"
        indexes = ["firebase_uid", "status"]
