"""
API endpoint tests
"""

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoints:
    """Test health check endpoints"""
    
    def test_health_check(self, client: TestClient):
        """Test health check endpoint"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] in ["healthy", "unhealthy"]
        assert "timestamp" in data
        assert "version" in data
        assert "database_connected" in data
    
    def test_readiness_check(self, client: TestClient):
        """Test readiness check endpoint"""
        response = client.get("/api/v1/health/ready")
        assert response.status_code in [200, 503]
    
    def test_liveness_check(self, client: TestClient):
        """Test liveness check endpoint"""
        response = client.get("/api/v1/health/live")
        assert response.status_code == 200
        assert response.json()["status"] == "alive"


class TestLogsEndpoints:
    """Test logs endpoints"""
    
    def test_get_interaction_log_not_found(self, client: TestClient):
        """Test getting non-existent interaction log"""
        response = client.get("/api/v1/logs/non_existent_call_id")
        assert response.status_code == 404
    
    def test_list_interactions_empty(self, client: TestClient):
        """Test listing interactions when none exist"""
        response = client.get("/api/v1/logs")
        assert response.status_code == 200
        
        data = response.json()
        assert "interactions" in data
        assert "total_count" in data
        assert data["total_count"] == 0
    
    def test_list_interactions_with_filters(self, client: TestClient):
        """Test listing interactions with filters"""
        response = client.get("/api/v1/logs?channel=voice&limit=10")
        assert response.status_code == 200
    
    def test_get_interaction_stats(self, client: TestClient):
        """Test getting interaction statistics"""
        response = client.get("/api/v1/logs/stats/summary?days=7")
        assert response.status_code == 200
        
        data = response.json()
        assert "period_days" in data
        assert "total_interactions" in data
        assert "by_channel" in data
        assert "by_status" in data
        assert "by_intent" in data


class TestAdminEndpoints:
    """Test admin endpoints"""
    
    def test_get_system_stats(self, client: TestClient):
        """Test getting system statistics"""
        response = client.get("/api/v1/admin/stats?days=7")
        assert response.status_code == 200
        
        data = response.json()
        assert "interactions" in data
        assert "performance" in data
        assert "knowledge_base" in data
        assert "calendar" in data
    
    def test_list_knowledge_base_empty(self, client: TestClient):
        """Test listing knowledge base when empty"""
        response = client.get("/api/v1/admin/knowledge-base")
        assert response.status_code == 200
        
        data = response.json()
        assert "faqs" in data
        assert "total_count" in data
        assert data["total_count"] == 0
    
    def test_create_faq(self, client: TestClient, sample_faq_data):
        """Test creating FAQ entry"""
        response = client.post(
            "/api/v1/admin/knowledge-base",
            json={
                "question": sample_faq_data["question"],
                "answer": sample_faq_data["answer"],
                "keywords": sample_faq_data["keywords"],
                "category": sample_faq_data["category"]
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["question"] == sample_faq_data["question"]
        assert data["answer"] == sample_faq_data["answer"]
        assert data["keywords"] == sample_faq_data["keywords"]
        assert data["category"] == sample_faq_data["category"]
        assert data["is_active"] is True


class TestWebhookEndpoints:
    """Test webhook endpoints"""
    
    def test_voice_webhook_missing_call_sid(self, client: TestClient):
        """Test voice webhook with missing CallSid"""
        response = client.post("/webhook/voice", data={})
        assert response.status_code == 400
    
    def test_voice_webhook_success(self, client: TestClient, sample_webhook_data):
        """Test successful voice webhook"""
        response = client.post("/webhook/voice", data=sample_webhook_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
    
    def test_whatsapp_webhook_invalid_object(self, client: TestClient):
        """Test WhatsApp webhook with invalid object"""
        response = client.post("/webhook/whatsapp", json={"object": "invalid"})
        assert response.status_code == 400
    
    def test_whatsapp_webhook_success(self, client: TestClient):
        """Test successful WhatsApp webhook"""
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
                                "body": "Hello, I'd like to schedule an appointment"
                            }
                        }]
                    }
                }]
            }]
        }
        
        response = client.post("/webhook/whatsapp", json=webhook_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
    
    def test_sms_webhook_missing_message_sid(self, client: TestClient):
        """Test SMS webhook with missing MessageSid"""
        response = client.post("/webhook/sms", data={})
        assert response.status_code == 400
    
    def test_sms_webhook_success(self, client: TestClient):
        """Test successful SMS webhook"""
        sms_data = {
            "MessageSid": "test_message_123",
            "From": "+1234567890",
            "To": "+0987654321",
            "Body": "I'd like to schedule an appointment"
        }
        
        response = client.post("/webhook/sms", data=sms_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"


class TestRootEndpoint:
    """Test root endpoint"""
    
    def test_root_endpoint(self, client: TestClient):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "Sara AI Receptionist"
        assert data["version"] == "1.0.0"
        assert data["status"] == "running"
