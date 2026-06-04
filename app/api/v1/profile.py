from fastapi import APIRouter

router = APIRouter()

@router.get("/status")
async def status():
    return {"status": "profile router active"}
