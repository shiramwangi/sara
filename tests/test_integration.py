"""
Integration tests for Sara AI Receptionist
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.models import IntentType, ChannelType, ContactInfo, AppointmentSlot


class TestVoiceWebhookIntegration:
    """Test voice webhook integration"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_voice_webhook_complete_flow(self, client: TestClient):
        """Test complete voice webhook flow"""
        webhook_data = {
            "CallSid": "test_call_123",
            "From": "+1234567890",
            "To": "+0987654321",
            "CallStatus": "completed",
            "TranscriptionText": "I'd like to schedule an appointment for tomorrow at 2 PM with John Doe"
        }
        
        with patch('app.services.intent_extraction.IntentExtractionService.extract_intent') as mock_extract, \
             patch('app.services.calendar_service.CalendarService.create_appointment') as mock_calendar, \
             patch('app.services.communication_service.CommunicationService.send_voice_response') as mock_send:
            
            # Mock intent extraction
            from app.models import IntentExtraction
            mock_extract.return_value = IntentExtraction(
                intent=IntentType.SCHEDULE,
                confidence=0.95,
                appointment=AppointmentSlot(
                    date="2024-01-16",
                    time="14:00",
                    timezone="UTC"
                ),
                contact_info=ContactInfo(name="John Doe"),
                raw_text=webhook_data["TranscriptionText"]
            )
            
            # Mock calendar service
            mock_calendar.return_value = "cal_event_123"
            
            # Mock communication service
            mock_send.return_value = True
            
            response = client.post("/webhook/voice", data=webhook_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            
            # Verify mocks were called
            mock_extract.assert_called_once()
            mock_calendar.assert_called_once()
            mock_send.assert_called_once()


class TestWhatsAppWebhookIntegration:
    """Test WhatsApp webhook integration"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_whatsapp_webhook_complete_flow(self, client: TestClient):
        """Test complete WhatsApp webhook flow"""
        webhook_data = {
            "object": "whatsapp_business_account",
            "entry": [{
                "changes": [{
                    "field": "messages",
                    "value": {
                        "messages": [{
                            "id": "test_message_123",
                            "from": "1234567890",
                            "to": "0987654321",
                            "timestamp": "1234567890",
                            "type": "text",
                            "text": {
                                "body": "What are your business hours?"
                            }
                        }]
                    }
                }]
            }]
        }
        
        with patch('app.services.intent_extraction.IntentExtractionService.extract_intent') as mock_extract, \
             patch('app.services.knowledge_base.KnowledgeBaseService.search_faq') as mock_faq, \
             patch('app.services.communication_service.CommunicationService.send_whatsapp_message') as mock_send:
            
            # Mock intent extraction
            from app.models import IntentExtraction
            mock_extract.return_value = IntentExtraction(
                intent=IntentType.FAQ,
                confidence=0.88,
                raw_text="What are your business hours?"
            )
            
            # Mock FAQ search
            mock_faq.return_value = "We're open Monday through Friday from 9 AM to 5 PM."
            
            # Mock communication service
            mock_send.return_value = True
            
            response = client.post("/webhook/whatsapp", json=webhook_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            
            # Verify mocks were called
            mock_extract.assert_called_once()
            mock_faq.assert_called_once()
            mock_send.assert_called_once()


class TestSMSWebhookIntegration:
    """Test SMS webhook integration"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_sms_webhook_complete_flow(self, client: TestClient):
        """Test complete SMS webhook flow"""
        webhook_data = {
            "MessageSid": "test_message_123",
            "From": "+1234567890",
            "To": "+0987654321",
            "Body": "I need to cancel my appointment"
        }
        
        with patch('app.services.intent_extraction.IntentExtractionService.extract_intent') as mock_extract, \
             patch('app.services.communication_service.CommunicationService.send_sms') as mock_send:
            
            # Mock intent extraction
            from app.models import IntentExtraction
            mock_extract.return_value = IntentExtraction(
                intent=IntentType.CANCEL,
                confidence=0.92,
                raw_text="I need to cancel my appointment"
            )
            
            # Mock communication service
            mock_send.return_value = True
            
            response = client.post("/webhook/sms", data=webhook_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            
            # Verify mocks were called
            mock_extract.assert_called_once()
            mock_send.assert_called_once()


class TestDatabaseIntegration:
    """Test database integration"""
    
    @pytest.mark.integration
    def test_interaction_creation(self, client: TestClient, db_session):
        """Test creating interaction in database"""
        from app.models import Interaction, InteractionStatus, ChannelType
        
        # Create interaction
        interaction = Interaction(
            call_id="test_call_123",
            channel=ChannelType.VOICE,
            status=InteractionStatus.PROCESSING,
            intent=IntentType.SCHEDULE,
            intent_confidence="0.95",
            extracted_slots={"service_type": "consultation"},
            contact_name="John Doe",
            contact_email="john@example.com",
            response_text="Your appointment has been scheduled."
        )
        
        db_session.add(interaction)
        db_session.commit()
        db_session.refresh(interaction)
        
        # Verify interaction was created
        assert interaction.id is not None
        assert interaction.call_id == "test_call_123"
        assert interaction.channel == ChannelType.VOICE
        assert interaction.intent == IntentType.SCHEDULE
    
    @pytest.mark.integration
    def test_knowledge_base_creation(self, client: TestClient, db_session):
        """Test creating FAQ in database"""
        from app.models import KnowledgeBase
        
        # Create FAQ
        faq = KnowledgeBase(
            question="What are your business hours?",
            answer="We're open Monday through Friday from 9 AM to 5 PM.",
            keywords=["hours", "business hours", "open"],
            category="general",
            is_active=True
        )
        
        db_session.add(faq)
        db_session.commit()
        db_session.refresh(faq)
        
        # Verify FAQ was created
        assert faq.id is not None
        assert faq.question == "What are your business hours?"
        assert faq.is_active is True


class TestAPIIntegration:
    """Test API integration"""
    
    @pytest.mark.integration
    def test_health_check_integration(self, client: TestClient):
        """Test health check with database"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "database_connected" in data
        assert "timestamp" in data
    
    @pytest.mark.integration
    def test_logs_endpoint_integration(self, client: TestClient, db_session):
        """Test logs endpoint with database"""
        from app.models import Interaction, InteractionStatus, ChannelType
        
        # Create test interaction
        interaction = Interaction(
            call_id="test_call_123",
            channel=ChannelType.VOICE,
            status=InteractionStatus.COMPLETED,
            intent=IntentType.SCHEDULE,
            intent_confidence="0.95"
        )
        
        db_session.add(interaction)
        db_session.commit()
        
        # Test logs endpoint
        response = client.get("/api/v1/logs")
        assert response.status_code == 200
        
        data = response.json()
        assert "interactions" in data
        assert "total_count" in data
        assert data["total_count"] >= 1
    
    @pytest.mark.integration
    def test_admin_stats_integration(self, client: TestClient, db_session):
        """Test admin stats with database"""
        from app.models import Interaction, InteractionStatus, ChannelType, KnowledgeBase
        
        # Create test data
        interaction = Interaction(
            call_id="test_call_123",
            channel=ChannelType.VOICE,
            status=InteractionStatus.COMPLETED,
            intent=IntentType.SCHEDULE,
            intent_confidence="0.95",
            processing_time_ms=1500
        )
        
        faq = KnowledgeBase(
            question="Test question",
            answer="Test answer",
            keywords=["test"],
            category="general",
            is_active=True
        )
        
        db_session.add(interaction)
        db_session.add(faq)
        db_session.commit()
        
        # Test admin stats
        response = client.get("/api/v1/admin/stats?days=7")
        assert response.status_code == 200
        
        data = response.json()
        assert "interactions" in data
        assert "knowledge_base" in data
        assert data["interactions"]["total"] >= 1
        assert data["knowledge_base"]["total_faqs"] >= 1
