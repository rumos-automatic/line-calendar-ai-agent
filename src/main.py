"""
LINE Google Calendar Agent - Main Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from src.core.config import settings
from src.core.logging import setup_logging
from src.routers import webhook, liff, tasks, health

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle
    """
    # Startup
    logger.info(f"Starting application in {settings.ENVIRONMENT} mode")
    logger.info(f"Project: {settings.GOOGLE_CLOUD_PROJECT}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")


# Create FastAPI app
app = FastAPI(
    title="LINE Google Calendar Agent",
    description="Integration service for LINE and Google Calendar",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(webhook.router, prefix="/webhook", tags=["webhook"])
app.include_router(liff.router, prefix="/liff", tags=["liff"])
app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "LINE Google Calendar Agent",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT
    }