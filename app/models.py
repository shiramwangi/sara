"""
Data models and contracts for Sara AI Receptionist
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class IntentType(str, Enum):
    """Supported intent types"""
    SCHEDULE = "schedule"
    FAQ = "faq"
    CONTACT = "contact"
    CANCEL = "cancel"
    RESCHEDULE = "reschedule"
    UNKNOWN = "unknown"


class ChannelType(str, Enum):
    """Communication channels"""
    VOICE = "voice"
    WHATSAPP = "whatsapp"
    SMS = "sms"
    EMAIL = "email"


class InteractionStatus(str, Enum):
    """Interaction processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# Pydantic Models for API contracts
class ContactInfo(BaseModel):
    """Contact information extracted from conversation"""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


class AppointmentSlot(BaseModel):
    """Appointment time slot"""
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    time: str = Field(..., description="Time in HH:MM format")
    timezone: str = Field(default="UTC", description="Timezone")


class IntentExtraction(BaseModel):
    """AI intent extraction result"""
    intent: IntentType
    confidence: float = Field(..., ge=0.0, le=1.0)
    slots: Dict[str, Any] = Field(default_factory=dict)
    contact_info: Optional[ContactInfo] = None
    appointment: Optional[AppointmentSlot] = None
    raw_text: str


class WebhookRequest(BaseModel):
    """Base webhook request"""
    call_id: str = Field(..., description="Unique identifier for this interaction")
    channel: ChannelType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    raw_data: Dict[str, Any] = Field(default_factory=dict)


class VoiceWebhookRequest(WebhookRequest):
    """Twilio voice webhook request"""
    channel: ChannelType = ChannelType.VOICE
    from_number: str
    to_number: str
    call_sid: str
    transcription: Optional[str] = None
    recording_url: Optional[str] = None


class WhatsAppWebhookRequest(WebhookRequest):
    """WhatsApp webhook request"""
    channel: ChannelType = ChannelType.WHATSAPP
    from_number: str
    to_number: str
    message_id: str
    message_text: str
    message_type: str = "text"


class SMSWebhookRequest(WebhookRequest):
    """SMS webhook request"""
    channel: ChannelType = ChannelType.SMS
    from_number: str
    to_number: str
    message_sid: str
    message_text: str


class ResponseMessage(BaseModel):
    """Response message to send back to user"""
    text: str
    channel: ChannelType
    to_number: str
    media_url: Optional[str] = None


class CalendarEvent(BaseModel):
    """Google Calendar event data"""
    title: str
    start_time: datetime
    end_time: datetime
    description: Optional[str] = None
    attendees: List[str] = Field(default_factory=list)
    location: Optional[str] = None


class InteractionLog(BaseModel):
    """Complete interaction log entry"""
    call_id: str
    channel: ChannelType
    status: InteractionStatus
    intent: Optional[IntentType] = None
    intent_confidence: Optional[float] = None
    extracted_slots: Dict[str, Any] = Field(default_factory=dict)
    contact_info: Optional[ContactInfo] = None
    response_text: Optional[str] = None
    calendar_event_id: Optional[str] = None
    error_message: Optional[str] = None
    processing_time_ms: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# SQLAlchemy Models for database
class Interaction(Base):
    """Database model for interactions"""
    __tablename__ = "interactions"
    
    id = Column(Integer, primary_key=True, index=True)
    call_id = Column(String(255), unique=True, index=True, nullable=False)
    channel = Column(SQLEnum(ChannelType), nullable=False)
    status = Column(SQLEnum(InteractionStatus), default=InteractionStatus.PENDING)
    
    # Intent data
    intent = Column(SQLEnum(IntentType))
    intent_confidence = Column(String(10))  # Store as string to avoid precision issues
    extracted_slots = Column(JSON)
    
    # Contact info
    contact_name = Column(String(255))
    contact_email = Column(String(255))
    contact_phone = Column(String(255))
    
    # Response data
    response_text = Column(Text)
    calendar_event_id = Column(String(255))
    error_message = Column(Text)
    
    # Metadata
    processing_time_ms = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Raw webhook data
    raw_webhook_data = Column(JSON)


class KnowledgeBase(Base):
    """Database model for FAQ knowledge base"""
    __tablename__ = "knowledge_base"
    
    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    keywords = Column(JSON)  # List of keywords for matching
    category = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class CalendarAvailability(Base):
    """Database model for calendar availability rules"""
    __tablename__ = "calendar_availability"
    
    id = Column(Integer, primary_key=True, index=True)
    day_of_week = Column(Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time = Column(String(5), nullable=False)  # HH:MM format
    end_time = Column(String(5), nullable=False)    # HH:MM format
    is_available = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# API Response Models
class HealthResponse(BaseModel):
    """Health check response"""
    status: str = "healthy"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = "1.0.0"
    database_connected: bool = True


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    message: str
    call_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
