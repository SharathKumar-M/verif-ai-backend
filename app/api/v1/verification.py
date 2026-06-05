from fastapi import APIRouter, Depends, HTTPException
from app.core.firebase import verify_firebase_token, get_firestore
from typing import List

router = APIRouter()

@router.get("/{verification_id}")
async def get_verification_details(
    verification_id: str, 
    user: dict = Depends(verify_firebase_token)
):
    """
    Get full details of a specific verification run.
    """
    db = get_firestore()
    doc = await db.collection("verifications").document(verification_id).get()
    
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Verification not found")
        
    data = doc.to_dict()
    student_uid = data["student_uid"]
    
    # Check permissions
    if user["uid"] != student_uid and user.get("role") != "recruiter":
        raise HTTPException(status_code=403, detail="Forbidden")
        
    # Fetch agent results and research logs
    results_query = db.collection("ai_results").where("student_uid", "==", student_uid).order_by("created_at", direction="DESCENDING").limit(3)
    results_docs = await results_query.get()
    agent_results = [d.to_dict() for d in results_docs]
    
    logs_query = db.collection("research_logs").where("student_uid", "==", student_uid).order_by("created_at", direction="DESCENDING").limit(3)
    logs_docs = await logs_query.get()
    research_logs = [d.to_dict() for d in logs_docs]
    
    return {
        "success": True,
        "data": {
            "verification": data,
            "agent_results": agent_results,
            "research_logs": research_logs
        }
    }
