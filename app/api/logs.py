"""
Logs and audit endpoints
"""

import logging
import structlog
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models import Interaction, InteractionLog, ChannelType, InteractionStatus

logger = structlog.get_logger()
router = APIRouter()


@router.get("/logs/{call_id}")
async def get_interaction_log(
    call_id: str,
    db: Session = Depends(get_db)
):
    """
    Get interaction log by call_id
    """
    try:
        interaction = db.query(Interaction).filter(Interaction.call_id == call_id).first()
        
        if not interaction:
            raise HTTPException(status_code=404, detail="Interaction not found")
        
        return {
            "call_id": interaction.call_id,
            "channel": interaction.channel,
            "status": interaction.status,
            "intent": interaction.intent,
            "intent_confidence": interaction.intent_confidence,
            "extracted_slots": interaction.extracted_slots,
            "contact_info": {
                "name": interaction.contact_name,
                "email": interaction.contact_email,
                "phone": interaction.contact_phone
            },
            "response_text": interaction.response_text,
            "calendar_event_id": interaction.calendar_event_id,
            "error_message": interaction.error_message,
            "processing_time_ms": interaction.processing_time_ms,
            "created_at": interaction.created_at,
            "updated_at": interaction.updated_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error retrieving interaction log", call_id=call_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/logs")
async def list_interactions(
    channel: Optional[ChannelType] = Query(None, description="Filter by channel"),
    status: Optional[InteractionStatus] = Query(None, description="Filter by status"),
    intent: Optional[str] = Query(None, description="Filter by intent"),
    limit: int = Query(50, ge=1, le=1000, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: Session = Depends(get_db)
):
    """
    List interactions with optional filtering
    """
    try:
        query = db.query(Interaction)
        
        # Apply filters
        if channel:
            query = query.filter(Interaction.channel == channel)
        if status:
            query = query.filter(Interaction.status == status)
        if intent:
            query = query.filter(Interaction.intent == intent)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination and ordering
        interactions = query.order_by(desc(Interaction.created_at)).offset(offset).limit(limit).all()
        
        return {
            "interactions": [
                {
                    "call_id": interaction.call_id,
                    "channel": interaction.channel,
                    "status": interaction.status,
                    "intent": interaction.intent,
                    "intent_confidence": interaction.intent_confidence,
                    "contact_name": interaction.contact_name,
                    "created_at": interaction.created_at,
                    "updated_at": interaction.updated_at
                }
                for interaction in interactions
            ],
            "total_count": total_count,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error("Error listing interactions", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/logs/stats/summary")
async def get_interaction_stats(
    days: int = Query(7, ge=1, le=365, description="Number of days to include in stats"),
    db: Session = Depends(get_db)
):
    """
    Get interaction statistics summary
    """
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get total interactions
        total_interactions = db.query(Interaction).filter(
            Interaction.created_at >= start_date
        ).count()
        
        # Get interactions by channel
        channel_stats = {}
        for channel in ChannelType:
            count = db.query(Interaction).filter(
                Interaction.channel == channel,
                Interaction.created_at >= start_date
            ).count()
            channel_stats[channel.value] = count
        
        # Get interactions by status
        status_stats = {}
        for status in InteractionStatus:
            count = db.query(Interaction).filter(
                Interaction.status == status,
                Interaction.created_at >= start_date
            ).count()
            status_stats[status.value] = count
        
        # Get interactions by intent
        intent_stats = db.query(
            Interaction.intent,
            db.func.count(Interaction.id).label('count')
        ).filter(
            Interaction.created_at >= start_date,
            Interaction.intent.isnot(None)
        ).group_by(Interaction.intent).all()
        
        intent_stats_dict = {intent: count for intent, count in intent_stats}
        
        return {
            "period_days": days,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_interactions": total_interactions,
            "by_channel": channel_stats,
            "by_status": status_stats,
            "by_intent": intent_stats_dict
        }
        
    except Exception as e:
        logger.error("Error getting interaction stats", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")
