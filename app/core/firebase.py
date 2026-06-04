import json
import firebase_admin
from firebase_admin import credentials, auth
from google.cloud import firestore
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings

bearer = HTTPBearer()
firestore_db: firestore.AsyncClient = None

def init_firebase():
    global firestore_db
    try:
        # Check if already initialized
        firebase_admin.get_app()
    except ValueError:
        creds_dict = settings.firebase_creds_dict
        creds = credentials.Certificate(creds_dict)
        firebase_admin.initialize_app(creds)
    
    # Initialize Async Firestore Client
    # We use the service account info from settings
    firestore_db = firestore.AsyncClient.from_service_account_info(settings.firebase_creds_dict)
    print("✅ Firebase & Async Firestore initialized")

def get_firestore() -> firestore.AsyncClient:
    return firestore_db

async def verify_firebase_token(creds: HTTPAuthorizationCredentials = Depends(bearer)) -> dict:
    try:
        # firebase_admin.auth calls are synchronous but usually fast/CPU-bound for token verification
        # however, it's safer to run in a threadpool if it does networking, 
        # but verify_id_token is mostly local crypto verification after keys are cached.
        return auth.verify_id_token(creds.credentials)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

async def require_student(user: dict = Depends(verify_firebase_token)) -> dict:
    if user.get("role") != "student":
        raise HTTPException(status_code=403, detail="Access forbidden: Students only")
    return user

async def require_recruiter(user: dict = Depends(verify_firebase_token)) -> dict:
    if user.get("role") != "recruiter":
        raise HTTPException(status_code=403, detail="Access forbidden: Recruiters only")
    return user
