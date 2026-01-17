"""Project Bootstrap Web App - Backend API."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import structlog

from app.config import get_settings
from app.api.v1.router import api_router
from app.core.database import engine
from app.models.base import Base
from app.core.logging import setup_logging
from app.services.orchestration_service import OrchestrationService
# Import all models to register them with SQLAlchemy
from app.models import Project, ExecutionStep, ApprovalGate, AgentResult

settings = get_settings()
logger = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging()
    logger.info("Starting Project Bootstrap API", version=settings.app_version)

    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")

    # Recover any interrupted workflows from previous session
    orchestration = OrchestrationService()
    await orchestration.recover_interrupted_workflows()

    yield
    # Shutdown
    await engine.dispose()
    logger.info("Shutting down Project Bootstrap API")

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Multi-agent orchestration system for automated project scaffolding",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# CORS middleware - allow all origins in development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.app_version}
