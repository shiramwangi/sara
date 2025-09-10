"""
Database configuration and session management
"""

import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.config import settings
from app.models import Base

logger = logging.getLogger(__name__)

# Create database engine
if settings.database_url.startswith("sqlite"):
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=settings.debug
    )
else:
    engine = create_engine(
        settings.database_url,
        echo=settings.debug,
        pool_pre_ping=True,
        pool_recycle=300
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def init_db():
    """Initialize database tables"""
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
        # TODO: Add initial data seeding here
        # await seed_initial_data()
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def seed_initial_data():
    """Seed initial data into the database"""
    from app.models import KnowledgeBase, CalendarAvailability
    
    db = SessionLocal()
    try:
        # Check if knowledge base is empty
        if db.query(KnowledgeBase).count() == 0:
            # Add sample FAQ entries
            sample_faqs = [
                {
                    "question": "What are your business hours?",
                    "answer": "We're open Monday through Friday from 9 AM to 5 PM, and Saturday from 10 AM to 2 PM.",
                    "keywords": ["hours", "business hours", "open", "time"],
                    "category": "general"
                },
                {
                    "question": "How can I schedule an appointment?",
                    "answer": "You can schedule an appointment by calling us, sending a WhatsApp message, or using our online booking system. Just let me know your preferred date and time!",
                    "keywords": ["schedule", "appointment", "booking", "book"],
                    "category": "scheduling"
                },
                {
                    "question": "What services do you offer?",
                    "answer": "We offer a wide range of services including consultations, follow-ups, and specialized treatments. Please let me know what you're looking for and I can provide more details.",
                    "keywords": ["services", "offer", "what do you do", "treatments"],
                    "category": "services"
                }
            ]
            
            for faq in sample_faqs:
                kb_entry = KnowledgeBase(**faq)
                db.add(kb_entry)
            
            logger.info("Sample FAQ data seeded")
        
        # Check if calendar availability is empty
        if db.query(CalendarAvailability).count() == 0:
            # Add default availability (Monday-Friday 9-5)
            availability_rules = []
            for day in range(5):  # Monday to Friday
                availability_rules.append(CalendarAvailability(
                    day_of_week=day,
                    start_time="09:00",
                    end_time="17:00",
                    is_available=True
                ))
            
            for rule in availability_rules:
                db.add(rule)
            
            logger.info("Default calendar availability seeded")
        
        db.commit()
        
    except Exception as e:
        logger.error(f"Failed to seed initial data: {e}")
        db.rollback()
        raise
    finally:
        db.close()
