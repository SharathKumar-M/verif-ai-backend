from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorGridFSBucket
from beanie import init_beanie
from app.core.config import settings

motor_client: AsyncIOMotorClient = None
motor_db: AsyncIOMotorDatabase = None

async def init_mongodb():
    global motor_client, motor_db
    motor_client = AsyncIOMotorClient(settings.MONGODB_URI)
    motor_db = motor_client[settings.MONGODB_DB_NAME]
    
    # Initialize Beanie with models
    from app.models.user import User
    from app.models.document import Document
    await init_beanie(
        database=motor_db,
        document_models=[User, Document]
    )
    print(f"✅ Connected to MongoDB: {settings.MONGODB_DB_NAME}")

async def close_mongodb():
    global motor_client
    if motor_client:
        motor_client.close()
        print("🔌 MongoDB connection closed")

def get_gridfs(bucket_name: str) -> AsyncIOMotorGridFSBucket:
    """Returns a GridFS bucket instance (resumes or certificates)"""
    return AsyncIOMotorGridFSBucket(motor_db, bucket_name=bucket_name)
