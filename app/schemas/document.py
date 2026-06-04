from typing import List, Optional, Literal, Any
from pydantic import BaseModel, HttpUrl

class UploadResponse(BaseModel):
    document_id: str
    type: str
    hash_sha256: str
    status: str
    filename: Optional[str] = None
    github_url: Optional[str] = None

class GitHubSubmitRequest(BaseModel):
    github_url: str

class APIResponse(BaseModel):
    success: bool
    data: Any
    message: str

class DocumentListResponse(BaseModel):
    success: bool = True
    documents: List[UploadResponse]
