"""
Model tests
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from app.models import (
    ContactInfo, AppointmentSlot, IntentExtraction, IntentType,
    VoiceWebhookRequest, WhatsAppWebhookRequest, SMSWebhookRequest,
    ChannelType, InteractionStatus, CalendarEvent, ResponseMessage
)


class TestContactInfo:
    """Test ContactInfo model"""
    
    def test_contact_info_valid(self):
        """Test valid ContactInfo creation"""
        contact = ContactInfo(
            name="John Doe",
            email="john@example.com",
            phone="+1234567890"
        )
        assert contact.name == "John Doe"
        assert contact.email == "john@example.com"
        assert contact.phone == "+1234567890"
    
    def test_contact_info_partial(self):
        """Test ContactInfo with partial data"""
        contact = ContactInfo(name="John Doe")
        assert contact.name == "John Doe"
        assert contact.email is None
        assert contact.phone is None
    
    def test_contact_info_empty(self):
        """Test ContactInfo with no data"""
        contact = ContactInfo()
        assert contact.name is None
        assert contact.email is None
        assert contact.phone is None


class TestAppointmentSlot:
    """Test AppointmentSlot model"""
    
    def test_appointment_slot_valid(self):
        """Test valid AppointmentSlot creation"""
        appointment = AppointmentSlot(
            date="2024-01-15",
            time="14:30",
            timezone="UTC"
        )
        assert appointment.date == "2024-01-15"
        assert appointment.time == "14:30"
        assert appointment.timezone == "UTC"
    
    def test_appointment_slot_default_timezone(self):
        """Test AppointmentSlot with default timezone"""
        appointment = AppointmentSlot(
            date="2024-01-15",
            time="14:30"
        )
        assert appointment.timezone == "UTC"


class TestIntentExtraction:
    """Test IntentExtraction model"""
    
    def test_intent_extraction_valid(self):
        """Test valid IntentExtraction creation"""
        intent = IntentExtraction(
            intent=IntentType.SCHEDULE,
            confidence=0.95,
            slots={"service_type": "consultation"},
            raw_text="I'd like to schedule an appointment"
        )
        assert intent.intent == IntentType.SCHEDULE
        assert intent.confidence == 0.95
        assert intent.slots == {"service_type": "consultation"}
        assert intent.raw_text == "I'd like to schedule an appointment"
    
    def test_intent_extraction_with_contact_info(self):
        """Test IntentExtraction with contact info"""
        contact = ContactInfo(name="John Doe", email="john@example.com")
        intent = IntentExtraction(
            intent=IntentType.SCHEDULE,
            confidence=0.95,
            contact_info=contact,
            raw_text="I'd like to schedule an appointment"
        )
        assert intent.contact_info.name == "John Doe"
        assert intent.contact_info.email == "john@example.com"
    
    def test_intent_extraction_with_appointment(self):
        """Test IntentExtraction with appointment"""
        appointment = AppointmentSlot(
            date="2024-01-15",
            time="14:30"
        )
        intent = IntentExtraction(
            intent=IntentType.SCHEDULE,
            confidence=0.95,
            appointment=appointment,
            raw_text="I'd like to schedule an appointment"
        )
        assert intent.appointment.date == "2024-01-15"
        assert intent.appointment.time == "14:30"


class TestWebhookRequests:
    """Test webhook request models"""
    
    def test_voice_webhook_request(self):
        """Test VoiceWebhookRequest creation"""
        webhook = VoiceWebhookRequest(
            call_id="test_call_123",
            channel=ChannelType.VOICE,
            from_number="+1234567890",
            to_number="+0987654321",
            call_sid="call_sid_123",
            transcription="Hello, I'd like to schedule an appointment"
        )
        assert webhook.call_id == "test_call_123"
        assert webhook.channel == ChannelType.VOICE
        assert webhook.from_number == "+1234567890"
        assert webhook.transcription == "Hello, I'd like to schedule an appointment"
    
    def test_whatsapp_webhook_request(self):
        """Test WhatsAppWebhookRequest creation"""
        webhook = WhatsAppWebhookRequest(
            call_id="whatsapp_123",
            channel=ChannelType.WHATSAPP,
            from_number="1234567890",
            to_number="0987654321",
            message_id="msg_123",
            message_text="Hello, I'd like to schedule an appointment"
        )
        assert webhook.call_id == "whatsapp_123"
        assert webhook.channel == ChannelType.WHATSAPP
        assert webhook.message_text == "Hello, I'd like to schedule an appointment"
    
    def test_sms_webhook_request(self):
        """Test SMSWebhookRequest creation"""
        webhook = SMSWebhookRequest(
            call_id="sms_123",
            channel=ChannelType.SMS,
            from_number="+1234567890",
            to_number="+0987654321",
            message_sid="msg_123",
            message_text="Hello, I'd like to schedule an appointment"
        )
        assert webhook.call_id == "sms_123"
        assert webhook.channel == ChannelType.SMS
        assert webhook.message_text == "Hello, I'd like to schedule an appointment"


class TestCalendarEvent:
    """Test CalendarEvent model"""
    
    def test_calendar_event_valid(self):
        """Test valid CalendarEvent creation"""
        start_time = datetime(2024, 1, 15, 14, 30)
        end_time = datetime(2024, 1, 15, 15, 30)
        
        event = CalendarEvent(
            title="Appointment with John Doe",
            start_time=start_time,
            end_time=end_time,
            description="Consultation appointment",
            attendees=["john@example.com"],
            location="Office"
        )
        assert event.title == "Appointment with John Doe"
        assert event.start_time == start_time
        assert event.end_time == end_time
        assert event.description == "Consultation appointment"
        assert event.attendees == ["john@example.com"]
        assert event.location == "Office"


class TestResponseMessage:
    """Test ResponseMessage model"""
    
    def test_response_message_valid(self):
        """Test valid ResponseMessage creation"""
        response = ResponseMessage(
            text="Your appointment has been scheduled for tomorrow at 2 PM.",
            channel=ChannelType.VOICE,
            to_number="+1234567890"
        )
        assert response.text == "Your appointment has been scheduled for tomorrow at 2 PM."
        assert response.channel == ChannelType.VOICE
        assert response.to_number == "+1234567890"
        assert response.media_url is None
    
    def test_response_message_with_media(self):
        """Test ResponseMessage with media URL"""
        response = ResponseMessage(
            text="Here's your appointment confirmation.",
            channel=ChannelType.WHATSAPP,
            to_number="1234567890",
            media_url="https://example.com/confirmation.pdf"
        )
        assert response.media_url == "https://example.com/confirmation.pdf"


class TestEnums:
    """Test enum models"""
    
    def test_intent_type_enum(self):
        """Test IntentType enum values"""
        assert IntentType.SCHEDULE == "schedule"
        assert IntentType.FAQ == "faq"
        assert IntentType.CONTACT == "contact"
        assert IntentType.CANCEL == "cancel"
        assert IntentType.RESCHEDULE == "reschedule"
        assert IntentType.UNKNOWN == "unknown"
    
    def test_channel_type_enum(self):
        """Test ChannelType enum values"""
        assert ChannelType.VOICE == "voice"
        assert ChannelType.WHATSAPP == "whatsapp"
        assert ChannelType.SMS == "sms"
        assert ChannelType.EMAIL == "email"
    
    def test_interaction_status_enum(self):
        """Test InteractionStatus enum values"""
        assert InteractionStatus.PENDING == "pending"
        assert InteractionStatus.PROCESSING == "processing"
        assert InteractionStatus.COMPLETED == "completed"
        assert InteractionStatus.FAILED == "failed"
        assert InteractionStatus.CANCELLED == "cancelled"
