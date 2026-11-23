import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.app.core.config import settings
from backend.app.models import init_db_async
from backend.app.api.v1.auth import router as auth_router
from backend.app.api.v1.intake import router as intake_router
from backend.app.api.v1.reports import router as reports_router
from backend.app.api.v1.doctor import router as doctor_router
from backend.app.api.v1.seed import router as seed_router
from backend.app.api.v1.voice import router as voice_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("ayush_intake")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing AyushIntake API & Database...")
    await init_db_async()
    logger.info(f"Database schemas ready. Environment: {settings.APP_ENV}")
    yield
    logger.info("AyushIntake API shutting down cleanly.")

app = FastAPI(
    title="AyushIntake API",
    description="Pre-OPD AI Voice Assistant & Clinical Triage for Ministry of Ayush",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(intake_router, prefix="/api/v1")
app.include_router(reports_router, prefix="/api/v1")
app.include_router(doctor_router, prefix="/api/v1")
app.include_router(seed_router, prefix="/api/v1")
app.include_router(voice_router)

# Mount static file routes for thumbnails and report previews
app.mount("/api/v1/reports/file", StaticFiles(directory=str(settings.UPLOAD_DIR)), name="uploaded_files")

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "AyushIntake",
        "version": "1.0.0",
        "disclaimer": "Draft prepared from patient answers. Not a diagnosis.",
        "crisis_helpline": settings.CRISIS_HELPLINE_NUMBER
    }
