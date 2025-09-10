"""
Idempotency utilities for webhook handling
"""

import logging
import structlog
from datetime import datetime, timedelta
from typing import Set
from sqlalchemy.orm import Session

from app.models import Interaction, InteractionStatus

logger = structlog.get_logger()

# In-memory cache for processed call IDs (in production, use Redis)
processed_call_ids: Set[str] = set()


async def check_idempotency(db: Session, call_id: str) -> bool:
    """
    Check if a call_id has already been processed
    """
    try:
        # Check in-memory cache first
        if call_id in processed_call_ids:
            return True
        
        # Check database
        existing_interaction = db.query(Interaction).filter(
            Interaction.call_id == call_id
        ).first()
        
        if existing_interaction:
            # Add to cache
            processed_call_ids.add(call_id)
            return True
        
        return False
        
    except Exception as e:
        logger.error("Error checking idempotency", call_id=call_id, error=str(e))
        return False


async def mark_processed(db: Session, call_id: str) -> None:
    """
    Mark a call_id as processed
    """
    try:
        # Add to in-memory cache
        processed_call_ids.add(call_id)
        
        # Clean up old entries from cache (keep last 1000)
        if len(processed_call_ids) > 1000:
            # Remove oldest entries (simple cleanup)
            processed_call_ids.clear()
        
        logger.debug("Call ID marked as processed", call_id=call_id)
        
    except Exception as e:
        logger.error("Error marking call as processed", call_id=call_id, error=str(e))


async def cleanup_old_processed_ids() -> None:
    """
    Clean up old processed IDs from cache
    """
    try:
        # In production, this would clean up Redis cache
        # For now, we'll just clear the in-memory cache periodically
        processed_call_ids.clear()
        logger.info("Cleaned up old processed IDs")
        
    except Exception as e:
        logger.error("Error cleaning up processed IDs", error=str(e))
