import logging
import hashlib
from typing import List, Annotated
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.core.firebase import require_student
from app.core.database import get_gridfs
from app.models.document import Document
from app.schemas.document import UploadResponse, GitHubSubmitRequest, DocumentListResponse, APIResponse
from app.core.config import settings

# Setup logging
logger = logging.getLogger(__name__)

router = APIRouter()

ALLOWED_MIME_TYPES = {
    "application/pdf": "pdf",
    "image/jpeg": "jpeg",
    "image/png": "png",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "application/msword": "doc"
}

# More robust Magic Numbers
MAGIC_NUMBERS = [
    (b"\x25\x50\x44\x46", "application/pdf"),
    (b"\xff\xd8", "image/jpeg"),
    (b"\x89\x50\x4e\x47\x0d\x0a\x1a\x0a", "image/png"),
    (b"\x50\x4b\x03\x04", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"), # Zip/Docx
    (b"\xd0\xcf\x11\xe0", "application/msword") # Older Doc
]

def validate_magic_bytes(content: bytes) -> str:
    for magic, mime in MAGIC_NUMBERS:
        if content.startswith(magic):
            return mime
    return None

@router.get("/readiness", response_model=APIResponse)
async def check_readiness(user: Annotated[dict, Depends(require_student)]):
    """
    Checks if the student has fulfilled the 3/3 requirement:
    1. One Resume
    2. At least one Certificate
    3. GitHub URL
    """
    docs = await Document.find(Document.firebase_uid == user["uid"]).to_list()
    
    has_resume = any(d.type == "resume" for d in docs)
    has_cert = any(d.type == "certificate" for d in docs)
    has_github = any(d.type == "github" for d in docs)
    
    ready = has_resume and has_cert and has_github
    
    status = {
        "has_resume": has_resume,
        "has_certificate": has_cert,
        "has_github": has_github,
        "is_ready": ready,
        "missing": [
            k for k, v in {
                "resume": has_resume,
                "certificate": has_cert,
                "github": has_github
            }.items() if not v
        ]
    }
    
    return {
        "success": True,
        "message": "Readiness status retrieved",
        "data": status
    }

@router.post("/upload", response_model=APIResponse, status_code=201)
async def upload_document(
    files: List[UploadFile] = File(...),
    doc_type: str = Form(..., alias="type"),
    user: dict = Depends(require_student)
):
    """
    Handles Multi-part Form upload for one or more files.
    - If type is 'resume', only the first file is processed (or error if multiple).
    - If type is 'certificate', all files are processed.
    """
    logger.info(f"Received {len(files)} files for type '{doc_type}' from user {user['uid']}")

    if doc_type not in ["resume", "certificate"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid type '{doc_type}'. Must be 'resume' or 'certificate'."
        )

    if doc_type == "resume" and len(files) > 1:
        raise HTTPException(status_code=400, detail="Only one resume file allowed per upload.")

    results = []
    
    for file in files:
        # Read content
        content = await file.read()
        if not content:
            logger.warning(f"Skipping empty file: {file.filename}")
            continue
            
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail=f"File {file.filename} too large (max 10MB)")

        # Validate mime type by magic bytes
        mime_type = validate_magic_bytes(content)
        if not mime_type:
            if file.content_type in ALLOWED_MIME_TYPES:
                mime_type = file.content_type
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported format for {file.filename}. Only PDF, JPEG, PNG, DOCX allowed.")

        # SHA-256 hash
        hash_sha256 = hashlib.sha256(content).hexdigest()

        # Check if duplicate for this user
        existing = await Document.find_one(
            Document.firebase_uid == user["uid"],
            Document.hash_sha256 == hash_sha256
        )
        
        if existing:
            results.append(UploadResponse(
                document_id=str(existing.id),
                type=existing.type,
                hash_sha256=existing.hash_sha256,
                status=existing.status,
                filename=existing.filename
            ))
            continue

        # Store in GridFS
        bucket_name = "resumes" if doc_type == "resume" else "certificates"
        bucket = get_gridfs(bucket_name)
        
        async with bucket.open_upload_stream(
            file.filename,
            metadata={
                "firebase_uid": user["uid"],
                "type": doc_type,
                "mime_type": mime_type,
                "hash_sha256": hash_sha256
            }
        ) as stream:
            await stream.write(content)
        
        gridfs_id = stream._id

        # Create Document record
        doc = Document(
            firebase_uid=user["uid"],
            type=doc_type,
            gridfs_id=gridfs_id,
            filename=file.filename,
            mime_type=mime_type,
            hash_sha256=hash_sha256,
            size_bytes=len(content),
            status="pending"
        )
        await doc.insert()
        
        results.append(UploadResponse(
            document_id=str(doc.id),
            type=doc.type,
            hash_sha256=doc.hash_sha256,
            status=doc.status,
            filename=doc.filename
        ))

    return {
        "success": True,
        "message": f"{len(results)} file(s) processed successfully",
        "data": results
    }

@router.post("/github", response_model=APIResponse, status_code=201)
async def submit_github(
    request: GitHubSubmitRequest,
    user: Annotated[dict, Depends(require_student)]
):
    url = request.github_url.strip()
    if not url.startswith("https://github.com/"):
        raise HTTPException(status_code=400, detail="Invalid GitHub URL. Must start with https://github.com/")
    
    parts = url.replace("https://github.com/", "").split("/")
    if len(parts) < 1 or not parts[0]:
        raise HTTPException(status_code=400, detail="Invalid GitHub URL. Missing username.")

    hash_sha256 = hashlib.sha256(url.encode()).hexdigest()
    
    # Check if exists
    existing = await Document.find_one(
        Document.firebase_uid == user["uid"],
        Document.type == "github"
    )
    
    if existing:
        existing.github_url = url
        existing.hash_sha256 = hash_sha256
        existing.status = "pending"
        await existing.save()
        return {
            "success": True,
            "message": "GitHub URL updated",
            "data": UploadResponse(
                document_id=str(existing.id),
                type=existing.type,
                hash_sha256=existing.hash_sha256,
                status=existing.status,
                github_url=existing.github_url
            )
        }

    doc = Document(
        firebase_uid=user["uid"],
        type="github",
        github_url=url,
        hash_sha256=hash_sha256,
        status="pending"
    )
    await doc.insert()

    return {
        "success": True,
        "message": "GitHub URL submitted successfully",
        "data": UploadResponse(
            document_id=str(doc.id),
            type=doc.type,
            hash_sha256=doc.hash_sha256,
            status=doc.status,
            github_url=doc.github_url
        )
    }

@router.get("/my", response_model=APIResponse)
async def get_my_documents(user: Annotated[dict, Depends(require_student)]):
    docs = await Document.find(Document.firebase_uid == user["uid"]).to_list()
    
    response_docs = []
    for d in docs:
        response_docs.append(UploadResponse(
            document_id=str(d.id),
            type=d.type,
            hash_sha256=d.hash_sha256,
            status=d.status,
            filename=d.filename,
            github_url=d.github_url
        ))
    
    return {
        "success": True,
        "message": "Documents retrieved successfully",
        "data": response_docs
    }
