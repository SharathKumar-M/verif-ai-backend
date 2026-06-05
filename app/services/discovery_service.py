from typing import List, Optional
from app.core.firebase import get_firestore
from app.schemas.discover import DiscoveryQuery, DiscoveryResponse
from app.schemas.profile import ProfileResponse
from google.cloud.firestore_v1.base_query import FieldFilter

class DiscoveryService:
    @staticmethod
    async def search_profiles(query: DiscoveryQuery) -> DiscoveryResponse:
        db = get_firestore()
        profiles_ref = db.collection("profiles")
        
        # Firestore is limited in complex queries (no native OR for arrays easily without multiple queries)
        # But we can do basic filtering
        fs_query = profiles_ref.where(filter=FieldFilter("is_public", "==", True))
        
        if query.min_trust_score > 0:
            fs_query = fs_query.where(filter=FieldFilter("trust_score", ">=", query.min_trust_score))
            
        if query.domain:
            fs_query = fs_query.where(filter=FieldFilter("domain", "==", query.domain))
            
        if query.location:
            fs_query = fs_query.where(filter=FieldFilter("location", "==", query.location))

        # Skills filtering - Firestore "array_contains_any"
        if query.skills:
            fs_query = fs_query.where(filter=FieldFilter("skills", "array_contains_any", query.skills))

        # Order and paginate
        fs_query = fs_query.order_by("trust_score", direction="DESCENDING")
        fs_query = fs_query.offset(query.offset).limit(query.limit)
        
        docs = await fs_query.get()
        results = []
        for doc in docs:
            data = doc.to_dict()
            data["firebase_uid"] = doc.id
            results.append(ProfileResponse(**data))
            
        # Get total (Note: count() is a separate costly operation in Firestore, but for hackathon we'll just use len or skip)
        total = len(results) # Simplified
        
        return DiscoveryResponse(total=total, results=results)

    @staticmethod
    async def shortlist_student(recruiter_uid: str, student_uid: str):
        db = get_firestore()
        shortlist_ref = db.collection("shortlists").document(recruiter_uid)
        
        doc = await shortlist_ref.get()
        if doc.exists:
            uids = doc.to_dict().get("student_uids", [])
            if student_uid not in uids:
                uids.append(student_uid)
                await shortlist_ref.update({"student_uids": uids})
        else:
            await shortlist_ref.set({"student_uids": [student_uid]})
            
    @staticmethod
    async def get_shortlisted_students(recruiter_uid: str) -> List[ProfileResponse]:
        db = get_firestore()
        shortlist_doc = await db.collection("shortlists").document(recruiter_uid).get()
        if not shortlist_doc.exists:
            return []
            
        student_uids = shortlist_doc.to_dict().get("student_uids", [])
        if not student_uids:
            return []
            
        # Batch get profiles
        results = []
        for uid in student_uids:
            doc = await db.collection("profiles").document(uid).get()
            if doc.exists:
                data = doc.to_dict()
                data["firebase_uid"] = doc.id
                results.append(ProfileResponse(**data))
        
        return results
