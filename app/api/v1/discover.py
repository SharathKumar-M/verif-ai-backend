from fastapi import APIRouter, Depends, HTTPException
from app.core.firebase import require_recruiter
from app.schemas.discover import DiscoveryQuery, DiscoveryResponse, ShortlistRequest, ShortlistResponse
from app.services.discovery_service import DiscoveryService
from typing import List

router = APIRouter()

@router.post("/search", response_model=DiscoveryResponse)
async def search_students(
    query: DiscoveryQuery, 
    user: dict = Depends(require_recruiter)
):
    """
    Recruiters search for verified students.
    """
    return await DiscoveryService.search_profiles(query)

@router.post("/shortlist", response_model=ShortlistResponse)
async def shortlist_student(
    req: ShortlistRequest, 
    user: dict = Depends(require_recruiter)
):
    """
    Add a student to recruiter's shortlist.
    """
    await DiscoveryService.shortlist_student(user["uid"], req.student_uid)
    return {"success": True, "message": "Student shortlisted successfully"}

@router.get("/shortlist", response_model=List[dict]) # List of profiles
async def get_shortlist(user: dict = Depends(require_recruiter)):
    """
    Get all shortlisted students for the recruiter.
    """
    return await DiscoveryService.get_shortlisted_students(user["uid"])
