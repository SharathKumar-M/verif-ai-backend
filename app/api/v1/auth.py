from fastapi import APIRouter, Depends, HTTPException, status
from app.core.firebase import verify_firebase_token, get_firestore, require_recruiter
from app.models.user import User
from app.schemas.auth import UserSyncRequest, UserResponse, RoleUpdateRequest, UserRegisterRequest
from datetime import datetime
import firebase_admin
from firebase_admin import auth
import httpx
from app.core.config import settings

router = APIRouter()

async def set_firebase_role(uid: str, role: str):
    """
    Set custom claims in Firebase Auth for RBAC.
    """
    try:
        # firebase_admin is synchronous, but we call it here.
        # In a high-traffic app, use anyio.to_thread.run_sync
        auth.set_custom_user_claims(uid, {"role": role})
    except Exception as e:
        print(f"⚠️ Failed to set custom claims for {uid}: {e}")

@router.post("/register")
async def register_user(request: UserRegisterRequest):
    """
    Register a new user in Firebase Auth and sync with local databases.
    Returns user data and idToken.
    """
    # 1. Create user in Firebase via REST API (to get idToken)
    firebase_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={settings.FIREBASE_API_KEY}"
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(firebase_url, json={
            "email": request.email,
            "password": request.password,
            "returnSecureToken": True
        })
        
        if resp.status_code != 200:
            error_data = resp.json()
            raise HTTPException(
                status_code=resp.status_code,
                detail={
                    "success": False,
                    "error": "Firebase Registration Failed",
                    "detail": error_data.get("error", {}).get("message", "Unknown error")
                }
            )
        
        fb_data = resp.json()
        firebase_uid = fb_data["localId"]
        id_token = fb_data["idToken"]

    # 2. Update display name & Set Custom Claims in Firebase Auth
    try:
        auth.update_user(firebase_uid, display_name=request.display_name)
        await set_firebase_role(firebase_uid, request.role)
    except Exception as e:
        print(f"⚠️ Failed to update Firebase user profile: {e}")

    # 3. Perform Sync Logic (MongoDB + Firestore)
    user = await User.find_one(User.firebase_uid == firebase_uid)
    if not user:
        user = User(
            firebase_uid=firebase_uid,
            email=request.email,
            role=request.role,
            display_name=request.display_name
        )
        await user.insert()

    # Sync to Firestore
    try:
        db = get_firestore()
        if db:
            await db.collection("users").document(firebase_uid).set({
                "email": request.email,
                "role": request.role,
                "display_name": request.display_name,
                "updated_at": datetime.utcnow(),
                "created_at": user.created_at
            }, merge=True)
    except Exception as e:
        print(f"❌ Firestore sync failed: {e}")

    return {
        "success": True,
        "message": "User registered and synced successfully",
        "data": {
            "user": UserResponse.model_validate(user, from_attributes=True),
            "idToken": id_token
        }
    }

@router.post("/sync")
async def sync_user(
    request: UserSyncRequest,
    decoded_token: dict = Depends(verify_firebase_token)
):
    """
    Upsert user in MongoDB and Firestore.
    """
    if decoded_token.get("uid") != request.firebase_uid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "error": "Forbidden",
                "detail": "Token UID does not match request UID"
            }
        )

    # 1. MongoDB Upsert
    user = await User.find_one(User.firebase_uid == request.firebase_uid)
    if user:
        user.email = request.email
        user.display_name = request.display_name
        user.role = request.role
        user.updated_at = datetime.utcnow()
        await user.save()
        message = "User updated successfully"
    else:
        user = User(
            firebase_uid=request.firebase_uid,
            email=request.email,
            role=request.role,
            display_name=request.display_name
        )
        await user.insert()
        message = "User created successfully"

    # 2. Sync to Firebase Custom Claims (Ensure token matches DB)
    await set_firebase_role(request.firebase_uid, request.role)

    # 3. Firestore Upsert (Async)
    try:
        db = get_firestore()
        if db:
            await db.collection("users").document(request.firebase_uid).set({
                "email": request.email,
                "role": request.role,
                "display_name": request.display_name,
                "updated_at": datetime.utcnow(),
                "created_at": user.created_at
            }, merge=True)
    except Exception as e:
        print(f"❌ Firestore sync failed: {e}")

    return {
        "success": True,
        "message": message,
        "data": UserResponse.model_validate(user, from_attributes=True)
    }

@router.get("/me")
async def get_me(decoded_token: dict = Depends(verify_firebase_token)):
    """
    Get current user profile from MongoDB.
    """
    firebase_uid = decoded_token.get("uid")
    user = await User.find_one(User.firebase_uid == firebase_uid)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": "Not Found",
                "detail": "User not found in system. Please sync first."
            }
        )
    
    return {
        "success": True,
        "message": "User profile retrieved",
        "data": UserResponse.model_validate(user, from_attributes=True)
    }

@router.put("/role")
async def update_role(
    request: RoleUpdateRequest,
    # Restricted to recruiters only
    admin_user: dict = Depends(require_recruiter)
):
    """
    Update user role in MongoDB and Firestore.
    NOTE: Only recruiters can call this endpoint.
    Currently updates the CURRENT user's role.
    """
    firebase_uid = admin_user.get("uid")
    user = await User.find_one(User.firebase_uid == firebase_uid)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": "Not Found",
                "detail": "User not found"
            }
        )

    user.role = request.role
    user.updated_at = datetime.utcnow()
    await user.save()

    # Sync to Firebase Custom Claims
    await set_firebase_role(firebase_uid, request.role)

    # Sync to Firestore (Async)
    try:
        db = get_firestore()
        if db:
            await db.collection("users").document(firebase_uid).update({
                "role": request.role,
                "updated_at": datetime.utcnow()
            })
    except Exception as e:
        print(f"❌ Firestore role update failed: {e}")

    return {
        "success": True,
        "message": "Role updated successfully",
        "data": UserResponse.model_validate(user, from_attributes=True)
    }

@router.get("/health")
async def auth_health():
    """
    Check connectivity to MongoDB and Firebase.
    """
    mongodb_status = "ok"
    firebase_status = "ok"

    try:
        from app.core.database import motor_client
        await motor_client.admin.command('ping')
    except Exception:
        mongodb_status = "error"

    try:
        firebase_admin.get_app()
    except Exception:
        firebase_status = "error"

    return {
        "success": True,
        "message": "Auth service health",
        "data": {
            "firebase": firebase_status,
            "mongodb": mongodb_status
        }
    }
