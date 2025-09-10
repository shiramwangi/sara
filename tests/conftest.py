"""
Pytest configuration and fixtures
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import get_db, Base
from app.models import Interaction, KnowledgeBase, CalendarAvailability

# Test database URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

# Create test engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def db_session():
    """Create a test database session"""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        # Drop tables
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    """Create a test client"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_interaction_data():
    """Sample interaction data for testing"""
    return {
        "call_id": "test_call_123",
        "channel": "voice",
        "status": "pending",
        "intent": "schedule",
        "intent_confidence": "0.95",
        "extracted_slots": {"service_type": "consultation"},
        "contact_name": "John Doe",
        "contact_email": "john@example.com",
        "contact_phone": "+1234567890",
        "response_text": "Your appointment has been scheduled.",
        "calendar_event_id": "cal_event_123"
    }


@pytest.fixture
def sample_faq_data():
    """Sample FAQ data for testing"""
    return {
        "question": "What are your business hours?",
        "answer": "We're open Monday through Friday from 9 AM to 5 PM.",
        "keywords": ["hours", "business hours", "open"],
        "category": "general",
        "is_active": True
    }


@pytest.fixture
def sample_webhook_data():
    """Sample webhook data for testing"""
    return {
        "CallSid": "test_call_123",
        "From": "+1234567890",
        "To": "+0987654321",
        "CallStatus": "completed",
        "TranscriptionText": "I'd like to schedule an appointment for tomorrow at 2 PM",
        "RecordingUrl": "https://api.twilio.com/recording.mp3"
    }
