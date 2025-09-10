"""
Knowledge Base Service for FAQ management
"""

import logging
import structlog
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.database import get_db
from app.models import KnowledgeBase

logger = structlog.get_logger()


class KnowledgeBaseService:
    """Service for managing and searching the knowledge base"""
    
    def __init__(self):
        pass
    
    async def search_faq(self, query: str) -> Optional[str]:
        """
        Search for FAQ answer based on user query
        """
        try:
            # Get database session
            db = next(get_db())
            
            # Search for matching FAQs
            faqs = db.query(KnowledgeBase).filter(
                and_(
                    KnowledgeBase.is_active == True,
                    or_(
                        KnowledgeBase.question.ilike(f"%{query}%"),
                        KnowledgeBase.answer.ilike(f"%{query}%")
                    )
                )
            ).all()
            
            if not faqs:
                # Try keyword matching
                faqs = await self._search_by_keywords(query, db)
            
            if faqs:
                # Return the best match (first one for now)
                best_match = faqs[0]
                logger.info("FAQ found", question=best_match.question, category=best_match.category)
                return best_match.answer
            
            return None
            
        except Exception as e:
            logger.error("Error searching FAQ", error=str(e))
            return None
        finally:
            db.close()
    
    async def _search_by_keywords(self, query: str, db: Session) -> List[KnowledgeBase]:
        """Search FAQs by keywords"""
        try:
            # Split query into keywords
            keywords = query.lower().split()
            
            # Search for FAQs that contain any of the keywords
            faqs = db.query(KnowledgeBase).filter(
                and_(
                    KnowledgeBase.is_active == True,
                    or_(*[
                        KnowledgeBase.keywords.contains([keyword])
                        for keyword in keywords
                    ])
                )
            ).all()
            
            return faqs
            
        except Exception as e:
            logger.error("Error searching by keywords", error=str(e))
            return []
    
    async def get_faq_by_id(self, faq_id: int) -> Optional[KnowledgeBase]:
        """Get FAQ by ID"""
        try:
            db = next(get_db())
            faq = db.query(KnowledgeBase).filter(KnowledgeBase.id == faq_id).first()
            return faq
        except Exception as e:
            logger.error("Error getting FAQ by ID", faq_id=faq_id, error=str(e))
            return None
        finally:
            db.close()
    
    async def get_faqs_by_category(self, category: str) -> List[KnowledgeBase]:
        """Get FAQs by category"""
        try:
            db = next(get_db())
            faqs = db.query(KnowledgeBase).filter(
                and_(
                    KnowledgeBase.category == category,
                    KnowledgeBase.is_active == True
                )
            ).all()
            return faqs
        except Exception as e:
            logger.error("Error getting FAQs by category", category=category, error=str(e))
            return []
        finally:
            db.close()
    
    async def create_faq(
        self,
        question: str,
        answer: str,
        keywords: List[str],
        category: str = "general"
    ) -> Optional[KnowledgeBase]:
        """Create a new FAQ entry"""
        try:
            db = next(get_db())
            
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
            
            logger.info("FAQ created", faq_id=faq.id, question=question)
            return faq
            
        except Exception as e:
            logger.error("Error creating FAQ", error=str(e))
            db.rollback()
            return None
        finally:
            db.close()
    
    async def update_faq(
        self,
        faq_id: int,
        question: Optional[str] = None,
        answer: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        category: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Optional[KnowledgeBase]:
        """Update an existing FAQ entry"""
        try:
            db = next(get_db())
            
            faq = db.query(KnowledgeBase).filter(KnowledgeBase.id == faq_id).first()
            if not faq:
                return None
            
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
            
            db.commit()
            db.refresh(faq)
            
            logger.info("FAQ updated", faq_id=faq_id)
            return faq
            
        except Exception as e:
            logger.error("Error updating FAQ", faq_id=faq_id, error=str(e))
            db.rollback()
            return None
        finally:
            db.close()
    
    async def delete_faq(self, faq_id: int) -> bool:
        """Delete an FAQ entry"""
        try:
            db = next(get_db())
            
            faq = db.query(KnowledgeBase).filter(KnowledgeBase.id == faq_id).first()
            if not faq:
                return False
            
            db.delete(faq)
            db.commit()
            
            logger.info("FAQ deleted", faq_id=faq_id)
            return True
            
        except Exception as e:
            logger.error("Error deleting FAQ", faq_id=faq_id, error=str(e))
            db.rollback()
            return False
        finally:
            db.close()
    
    async def get_all_categories(self) -> List[str]:
        """Get all FAQ categories"""
        try:
            db = next(get_db())
            categories = db.query(KnowledgeBase.category).filter(
                KnowledgeBase.is_active == True
            ).distinct().all()
            return [cat[0] for cat in categories if cat[0]]
        except Exception as e:
            logger.error("Error getting categories", error=str(e))
            return []
        finally:
            db.close()
    
    async def search_similar_faqs(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for similar FAQs and return ranked results"""
        try:
            db = next(get_db())
            
            # Get all active FAQs
            faqs = db.query(KnowledgeBase).filter(KnowledgeBase.is_active == True).all()
            
            # Simple similarity scoring based on keyword overlap
            query_keywords = set(query.lower().split())
            scored_faqs = []
            
            for faq in faqs:
                faq_keywords = set(faq.keywords) if faq.keywords else set()
                question_keywords = set(faq.question.lower().split())
                answer_keywords = set(faq.answer.lower().split())
                
                # Calculate similarity score
                keyword_overlap = len(query_keywords.intersection(faq_keywords))
                question_overlap = len(query_keywords.intersection(question_keywords))
                answer_overlap = len(query_keywords.intersection(answer_keywords))
                
                total_score = keyword_overlap * 3 + question_overlap * 2 + answer_overlap
                
                if total_score > 0:
                    scored_faqs.append({
                        "faq": faq,
                        "score": total_score
                    })
            
            # Sort by score and return top results
            scored_faqs.sort(key=lambda x: x["score"], reverse=True)
            
            return [
                {
                    "id": item["faq"].id,
                    "question": item["faq"].question,
                    "answer": item["faq"].answer,
                    "category": item["faq"].category,
                    "score": item["score"]
                }
                for item in scored_faqs[:limit]
            ]
            
        except Exception as e:
            logger.error("Error searching similar FAQs", error=str(e))
            return []
        finally:
            db.close()
