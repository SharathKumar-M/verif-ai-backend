import logging
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import firebase_admin

from app.core.config import settings
from app.core.database import init_mongodb, close_mongodb, motor_client
from app.core.firebase import init_firebase

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize MongoDB and Firebase
    await init_mongodb()
    init_firebase()
    yield
    # Shutdown: Close connections
    await close_mongodb()

app = FastAPI(
    title="VERIF-AI API",
    description="AI Academic Profile & Skill Verification Backend",
    version="1.0.0",
    lifespan=lifespan
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """
    Handle 422 errors and return in standard project format.
    Ensures detail is JSON serializable.
    """
    errors = []
    for error in exc.errors():
        # Manually build a clean, serializable error object
        clean_error = {
            "loc": list(error.get("loc", [])),
            "msg": str(error.get("msg", "")),
            "type": str(error.get("type", ""))
        }
        
        if "input" in error:
            # Crucial: UploadFile or other objects must be stringified
            clean_error["input"] = str(error["input"])
            
        if "ctx" in error:
            # Crucial: Context objects like ValueErrors must be stringified
            ctx = error["ctx"]
            if isinstance(ctx, dict):
                clean_error["ctx"] = {k: str(v) for k, v in ctx.items()}
            else:
                clean_error["ctx"] = str(ctx)
                
        errors.append(clean_error)

    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": "Validation Error",
            "detail": errors
        }
    )

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    health_status = {
        "status": "healthy",
        "mongodb": "disconnected",
        "firebase": "disconnected"
    }
    
    # Test MongoDB
    try:
        if motor_client:
            await motor_client.admin.command('ping')
            health_status["mongodb"] = "connected"
    except Exception as e:
        logger.error(f"MongoDB health check failed: {e}")
        health_status["status"] = "degraded"

    # Test Firebase
    try:
        firebase_admin.get_app()
        health_status["firebase"] = "connected"
    except Exception as e:
        logger.error(f"Firebase health check failed: {e}")
        health_status["status"] = "degraded"

    return health_status

@app.get("/")
async def root():
    return {
        "message": "VERIF-AI API",
        "docs": "/docs",
        "version": "1.0.0"
    }

# Dynamically include routers from app/api/v1/
router_modules = [
    ("auth", "/api/v1/auth", "Auth"),
    ("documents", "/api/v1/documents", "Documents"),
    ("analysis", "/api/v1/analysis", "Analysis"),
    ("profile", "/api/v1/profile", "Profile"),
    ("discover", "/api/v1/discover", "Discovery"),
    ("verification", "/api/v1/verification", "Verification"),
]

for module_name, prefix, tag in router_modules:
    try:
        module = __import__(f"app.api.v1.{module_name}", fromlist=["router"])
        app.include_router(module.router, prefix=prefix, tags=[tag])
        logger.info(f"Successfully included router: {module_name}")
    except (ImportError, AttributeError) as e:
        logger.warning(f"Could not include router {module_name}: {e}")
