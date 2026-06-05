from fastapi import APIRouter, Depends, HTTPException
from app.core.firebase import verify_firebase_token, get_firestore
from app.schemas.profile import ProfileUpdate, ProfileResponse
from datetime import datetime

router = APIRouter()

@router.get("/me", response_model=ProfileResponse)
async def get_my_profile(user: dict = Depends(verify_firebase_token)):
    db = get_firestore()
    doc = await db.collection("profiles").document(user["uid"]).get()
    
    if not doc.exists:
        # Create default profile if not exists
        profile_data = {
            "display_name": user.get("name", "User"),
            "bio": "",
            "skills": [],
            "domain": "Unknown",
            "location": "Remote",
            "is_public": False,
            "trust_score": 0.0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        await db.collection("profiles").document(user["uid"]).set(profile_data)
        profile_data["firebase_uid"] = user["uid"]
        return profile_data
        
    data = doc.to_dict()
    data["firebase_uid"] = doc.id
    return data

@router.patch("/me", response_model=ProfileResponse)
async def update_my_profile(
    update_data: ProfileUpdate, 
    user: dict = Depends(verify_firebase_token)
):
    db = get_firestore()
    profile_ref = db.collection("profiles").document(user["uid"])
    
    doc = await profile_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Profile not found")
        
    update_dict = update_data.model_dump(exclude_unset=True)
    update_dict["updated_at"] = datetime.utcnow()
    
    await profile_ref.update(update_dict)
    
    updated_doc = await profile_ref.get()
    data = updated_doc.to_dict()
    data["firebase_uid"] = updated_doc.id
    return data

@router.get("/{uid}", response_model=ProfileResponse)
async def get_public_profile(uid: str, user: dict = Depends(verify_firebase_token)):
    db = get_firestore()
    doc = await db.collection("profiles").document(uid).get()
    
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Profile not found")
        
    data = doc.to_dict()
    
    # Only allow recruiters or the user themselves to see private profiles
    if not data.get("is_public", False):
        if user["uid"] != uid and user.get("role") != "recruiter":
            raise HTTPException(status_code=403, detail="Profile is private")
            
    data["firebase_uid"] = doc.id
    return data
