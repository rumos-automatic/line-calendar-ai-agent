"""
Health check endpoints
"""
from fastapi import APIRouter, Response
from src.core.firestore import get_db
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {"status": "healthy"}


@router.get("/health/ready")
async def readiness_check():
    """
    Readiness check - verifies all dependencies are available
    """
    try:
        # Check Firestore connection
        db = get_db()
        # Try to read from a collection (it doesn't need to exist)
        _ = db.collection('_health_check').limit(1).get()
        
        return {"status": "ready", "checks": {"firestore": "ok"}}
        
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return Response(
            content={"status": "not ready", "error": str(e)},
            status_code=503
        )