"""
Service tests
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.models import IntentType, ChannelType, ContactInfo, AppointmentSlot
from app.services.intent_extraction import IntentExtractionService
from app.services.response_generation import ResponseGenerationService
from app.services.knowledge_base import KnowledgeBaseService


class TestIntentExtractionService:
    """Test IntentExtractionService"""
    
    @pytest.fixture
    def intent_service(self):
        return IntentExtractionService()
    
    @pytest.mark.asyncio
    async def test_extract_intent_schedule(self, intent_service):
        """Test extracting schedule intent"""
        with patch.object(intent_service.client.chat.completions, 'create') as mock_create:
            mock_response = MagicMock()
            mock_response.choices[0].message.content = '''
            {
                "intent": "schedule",
                "confidence": 0.95,
                "contact_info": {
                    "name": "John Doe",
                    "email": "john@example.com",
                    "phone": "+1234567890"
                },
                "appointment": {
                    "date": "2024-01-15",
                    "time": "14:30",
                    "timezone": "UTC"
                },
                "slots": {
                    "service_type": "consultation"
                }
            }
            '''
            mock_create.return_value = mock_response
            
            result = await intent_service.extract_intent(
                text="I'd like to schedule an appointment for tomorrow at 2 PM",
                channel=ChannelType.VOICE
            )
            
            assert result.intent == IntentType.SCHEDULE
            assert result.confidence == 0.95
            assert result.contact_info.name == "John Doe"
            assert result.appointment.date == "2024-01-15"
            assert result.appointment.time == "14:30"
    
    @pytest.mark.asyncio
    async def test_extract_intent_faq(self, intent_service):
        """Test extracting FAQ intent"""
        with patch.object(intent_service.client.chat.completions, 'create') as mock_create:
            mock_response = MagicMock()
            mock_response.choices[0].message.content = '''
            {
                "intent": "faq",
                "confidence": 0.88,
                "contact_info": null,
                "appointment": null,
                "slots": {
                    "question_topic": "business_hours"
                }
            }
            '''
            mock_create.return_value = mock_response
            
            result = await intent_service.extract_intent(
                text="What are your business hours?",
                channel=ChannelType.WHATSAPP
            )
            
            assert result.intent == IntentType.FAQ
            assert result.confidence == 0.88
            assert result.contact_info is None
            assert result.appointment is None
    
    @pytest.mark.asyncio
    async def test_extract_intent_error_handling(self, intent_service):
        """Test error handling in intent extraction"""
        with patch.object(intent_service.client.chat.completions, 'create') as mock_create:
            mock_create.side_effect = Exception("API Error")
            
            result = await intent_service.extract_intent(
                text="Some text",
                channel=ChannelType.VOICE
            )
            
            assert result.intent == IntentType.UNKNOWN
            assert result.confidence == 0.0
            assert result.slots == {}


class TestResponseGenerationService:
    """Test ResponseGenerationService"""
    
    @pytest.fixture
    def response_service(self):
        return ResponseGenerationService()
    
    @pytest.mark.asyncio
    async def test_generate_scheduling_response(self, response_service):
        """Test generating scheduling response"""
        from app.models import IntentExtraction
        
        intent_result = IntentExtraction(
            intent=IntentType.SCHEDULE,
            confidence=0.95,
            appointment=AppointmentSlot(
                date="2024-01-15",
                time="14:30",
                timezone="UTC"
            ),
            contact_info=ContactInfo(name="John Doe"),
            raw_text="I'd like to schedule an appointment"
        )
        
        with patch.object(response_service.client.chat.completions, 'create') as mock_create:
            mock_response = MagicMock()
            mock_response.choices[0].message.content = "Your appointment has been scheduled for Monday, January 15, 2024 at 2:30 PM. We look forward to seeing you!"
            mock_create.return_value = mock_response
            
            result = await response_service.generate_response(
                intent_result=intent_result,
                channel=ChannelType.VOICE,
                contact_info=intent_result.contact_info
            )
            
            assert "appointment" in result["text"].lower()
            assert "scheduled" in result["text"].lower()
            assert result["channel"] == "voice"
    
    @pytest.mark.asyncio
    async def test_generate_faq_response(self, response_service):
        """Test generating FAQ response"""
        from app.models import IntentExtraction
        
        intent_result = IntentExtraction(
            intent=IntentType.FAQ,
            confidence=0.88,
            raw_text="What are your business hours?"
        )
        
        with patch.object(response_service.knowledge_base, 'search_faq') as mock_search:
            mock_search.return_value = "We're open Monday through Friday from 9 AM to 5 PM."
            
            result = await response_service.generate_response(
                intent_result=intent_result,
                channel=ChannelType.WHATSAPP
            )
            
            assert "9 AM to 5 PM" in result["text"]
            assert result["channel"] == "whatsapp"
    
    @pytest.mark.asyncio
    async def test_generate_unknown_response(self, response_service):
        """Test generating response for unknown intent"""
        from app.models import IntentExtraction
        
        intent_result = IntentExtraction(
            intent=IntentType.UNKNOWN,
            confidence=0.3,
            raw_text="Some unclear message"
        )
        
        result = await response_service.generate_response(
            intent_result=intent_result,
            channel=ChannelType.SMS
        )
        
        assert "not sure" in result["text"].lower() or "understand" in result["text"].lower()
        assert result["channel"] == "sms"


class TestKnowledgeBaseService:
    """Test KnowledgeBaseService"""
    
    @pytest.fixture
    def kb_service(self):
        return KnowledgeBaseService()
    
    @pytest.mark.asyncio
    async def test_search_faq_no_results(self, kb_service):
        """Test searching FAQ with no results"""
        with patch('app.services.knowledge_base.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_db.query.return_value.filter.return_value.all.return_value = []
            mock_get_db.return_value = iter([mock_db])
            
            result = await kb_service.search_faq("some random question")
            assert result is None
    
    @pytest.mark.asyncio
    async def test_search_faq_with_results(self, kb_service):
        """Test searching FAQ with results"""
        with patch('app.services.knowledge_base.get_db') as mock_get_db:
            mock_faq = MagicMock()
            mock_faq.question = "What are your business hours?"
            mock_faq.answer = "We're open Monday through Friday from 9 AM to 5 PM."
            mock_faq.category = "general"
            
            mock_db = MagicMock()
            mock_db.query.return_value.filter.return_value.all.return_value = [mock_faq]
            mock_get_db.return_value = iter([mock_db])
            
            result = await kb_service.search_faq("business hours")
            assert result == "We're open Monday through Friday from 9 AM to 5 PM."
    
    @pytest.mark.asyncio
    async def test_create_faq(self, kb_service):
        """Test creating FAQ entry"""
        with patch('app.services.knowledge_base.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_faq = MagicMock()
            mock_faq.id = 1
            mock_faq.question = "Test question"
            mock_faq.answer = "Test answer"
            mock_db.add.return_value = None
            mock_db.commit.return_value = None
            mock_db.refresh.return_value = None
            mock_get_db.return_value = iter([mock_db])
            
            result = await kb_service.create_faq(
                question="Test question",
                answer="Test answer",
                keywords=["test"],
                category="general"
            )
            
            assert result is not None
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_faq_error(self, kb_service):
        """Test creating FAQ entry with error"""
        with patch('app.services.knowledge_base.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_db.add.side_effect = Exception("Database error")
            mock_get_db.return_value = iter([mock_db])
            
            result = await kb_service.create_faq(
                question="Test question",
                answer="Test answer",
                keywords=["test"],
                category="general"
            )
            
            assert result is None
            mock_db.rollback.assert_called_once()
