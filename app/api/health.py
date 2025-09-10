"""
Health check endpoints
"""

import logging
import structlog
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db
from app.models import HealthResponse

logger = structlog.get_logger()
router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint
    """
    try:
        # Check database connection
        db_connected = True
        try:
            db.execute(text("SELECT 1"))
        except Exception as e:
            logger.error("Database health check failed", error=str(e))
            db_connected = False
        
        return HealthResponse(
            status="healthy" if db_connected else "unhealthy",
            timestamp=datetime.utcnow(),
            version="1.0.0",
            database_connected=db_connected
        )
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(status_code=500, detail="Health check failed")


@router.get("/health/ready")
async def readiness_check(db: Session = Depends(get_db)):
    """
    Readiness check for Kubernetes
    """
    try:
        # Check if database is accessible
        db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:
        logger.error("Readiness check failed", error=str(e))
        raise HTTPException(status_code=503, detail="Service not ready")


@router.get("/health/live")
async def liveness_check():
    """
    Liveness check for Kubernetes
    """
    return {"status": "alive"}
