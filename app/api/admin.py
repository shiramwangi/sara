"""
Admin endpoints for system management
"""

import logging
import structlog
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from app.database import get_db
from app.models import Interaction, KnowledgeBase, CalendarAvailability

logger = structlog.get_logger()
router = APIRouter()


@router.get("/admin/stats")
async def get_system_stats(
    days: int = Query(7, ge=1, le=365, description="Number of days to include in stats"),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive system statistics
    """
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get interaction statistics
        total_interactions = db.query(Interaction).filter(
            Interaction.created_at >= start_date
        ).count()
        
        successful_interactions = db.query(Interaction).filter(
            Interaction.status == "completed",
            Interaction.created_at >= start_date
        ).count()
        
        failed_interactions = db.query(Interaction).filter(
            Interaction.status == "failed",
            Interaction.created_at >= start_date
        ).count()
        
        # Get average processing time
        avg_processing_time = db.query(
            func.avg(Interaction.processing_time_ms)
        ).filter(
            Interaction.processing_time_ms.isnot(None),
            Interaction.created_at >= start_date
        ).scalar() or 0
        
        # Get knowledge base stats
        total_faqs = db.query(KnowledgeBase).count()
        active_faqs = db.query(KnowledgeBase).filter(KnowledgeBase.is_active == True).count()
        
        # Get calendar availability stats
        availability_rules = db.query(CalendarAvailability).count()
        
        return {
            "period_days": days,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "interactions": {
                "total": total_interactions,
                "successful": successful_interactions,
                "failed": failed_interactions,
                "success_rate": (successful_interactions / total_interactions * 100) if total_interactions > 0 else 0
            },
            "performance": {
                "avg_processing_time_ms": round(avg_processing_time, 2)
            },
            "knowledge_base": {
                "total_faqs": total_faqs,
                "active_faqs": active_faqs
            },
            "calendar": {
                "availability_rules": availability_rules
            }
        }
        
    except Exception as e:
        logger.error("Error getting system stats", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/admin/knowledge-base")
async def list_knowledge_base(
    category: Optional[str] = Query(None, description="Filter by category"),
    active_only: bool = Query(True, description="Show only active FAQs"),
    limit: int = Query(100, ge=1, le=1000, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: Session = Depends(get_db)
):
    """
    List knowledge base entries
    """
    try:
        query = db.query(KnowledgeBase)
        
        # Apply filters
        if category:
            query = query.filter(KnowledgeBase.category == category)
        if active_only:
            query = query.filter(KnowledgeBase.is_active == True)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination and ordering
        faqs = query.order_by(desc(KnowledgeBase.created_at)).offset(offset).limit(limit).all()
        
        return {
            "faqs": [
                {
                    "id": faq.id,
                    "question": faq.question,
                    "answer": faq.answer,
                    "keywords": faq.keywords,
                    "category": faq.category,
                    "is_active": faq.is_active,
                    "created_at": faq.created_at,
                    "updated_at": faq.updated_at
                }
                for faq in faqs
            ],
            "total_count": total_count,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error("Error listing knowledge base", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


from fastapi import Body


@router.post("/admin/knowledge-base")
async def create_faq(
    question: str = Body(...),
    answer: str = Body(...),
    keywords: List[str] = Body(...),
    category: str = Body("general"),
    db: Session = Depends(get_db)
):
    """
    Create a new FAQ entry
    """
    try:
        faq = KnowledgeBase(
            question=question,
            answer=answer,
            keywords=keywords,
            category=category,
            is_active=True
        )
        
        db.add(faq)
        db.commit()
        db.refresh(faq)
        
        return {
            "id": faq.id,
            "question": faq.question,
            "answer": faq.answer,
            "keywords": faq.keywords,
            "category": faq.category,
            "is_active": faq.is_active,
            "created_at": faq.created_at
        }
        
    except Exception as e:
        logger.error("Error creating FAQ", error=str(e))
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/admin/knowledge-base/{faq_id}")
async def update_faq(
    faq_id: int,
    question: Optional[str] = None,
    answer: Optional[str] = None,
    keywords: Optional[List[str]] = None,
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """
    Update an existing FAQ entry
    """
    try:
        faq = db.query(KnowledgeBase).filter(KnowledgeBase.id == faq_id).first()
        
        if not faq:
            raise HTTPException(status_code=404, detail="FAQ not found")
        
        # Update fields if provided
        if question is not None:
            faq.question = question
        if answer is not None:
            faq.answer = answer
        if keywords is not None:
            faq.keywords = keywords
        if category is not None:
            faq.category = category
        if is_active is not None:
            faq.is_active = is_active
        
        faq.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(faq)
        
        return {
            "id": faq.id,
            "question": faq.question,
            "answer": faq.answer,
            "keywords": faq.keywords,
            "category": faq.category,
            "is_active": faq.is_active,
            "updated_at": faq.updated_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating FAQ", faq_id=faq_id, error=str(e))
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/admin/knowledge-base/{faq_id}")
async def delete_faq(
    faq_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete an FAQ entry
    """
    try:
        faq = db.query(KnowledgeBase).filter(KnowledgeBase.id == faq_id).first()
        
        if not faq:
            raise HTTPException(status_code=404, detail="FAQ not found")
        
        db.delete(faq)
        db.commit()
        
        return {"message": "FAQ deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting FAQ", faq_id=faq_id, error=str(e))
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")
