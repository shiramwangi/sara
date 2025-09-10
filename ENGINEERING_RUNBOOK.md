# Sara AI Receptionist - Engineering Runbook

## Executive Summary

This runbook provides complete engineering specifications for Sara, an AI receptionist that handles inbound voice calls, WhatsApp messages, and SMS through intelligent intent extraction and automated response generation.

## Vision & Success Criteria

**Vision**: Sara is an AI receptionist that answers inbound voice & message requests, handles FAQs, and performs actionable requests (bookings/emails/follow-ups) reliably through Google Calendar, Email, and WhatsApp/SMS. All interactions are logged and auditable.

**Success Criteria**:
- ✅ Incoming call or WhatsApp message → transcript received by backend
- ✅ AI extracts intent and slots (appointment date/time, name, email, phone) with >90% structure accuracy
- ✅ If intent = schedule: verifies availability, creates Google Calendar event, returns confirmation
- ✅ If intent = FAQ: answers from knowledge base and logs interaction
- ✅ All runs are idempotent: repeated webhook with same callId is ignored/deduplicated
- ✅ Easy to deploy: repo contains Dockerfile and deploy instructions

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        External Channels                        │
├─────────────────┬─────────────────┬─────────────────┬───────────┤
│   Voice Calls   │   WhatsApp      │   SMS/Email     │   Web     │
│   (Twilio)      │   (Meta API)    │   (Twilio)      │   (Admin) │
└─────────┬───────┴─────────┬───────┴─────────┬───────┴───────────┘
          │                 │                 │
          └─────────────────┼─────────────────┘
                            │
              ┌─────────────▼─────────────┐
              │      Load Balancer        │
              │      (Nginx/CloudFlare)   │
              └─────────────┬─────────────┘
                            │
              ┌─────────────▼─────────────┐
              │      Sara Backend         │
              │   (FastAPI + AI Engine)   │
              ├───────────────────────────┤
              │  • Webhook Handlers      │
              │  • Intent Extraction     │
              │  • Response Generation   │
              │  • Business Logic        │
              └─────────────┬─────────────┘
                            │
              ┌─────────────▼─────────────┐
              │      Data Layer           │
              ├───────────────────────────┤
              │  • PostgreSQL Database   │
              │  • Redis Cache           │
              │  • File Storage          │
              └─────────────┬─────────────┘
                            │
              ┌─────────────▼─────────────┐
              │    External Services      │
              ├───────────────────────────┤
              │  • Google Calendar API   │
              │  • OpenAI API            │
              │  • Twilio API            │
              │  • WhatsApp API          │
              │  • SMTP Server           │
              └───────────────────────────┘
```

## Canonical Data Models (JSON Contracts)

### Intent Extraction Response
```json
{
  "intent": "schedule|faq|contact|cancel|reschedule|unknown",
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
    "service_type": "consultation",
    "urgency": "normal",
    "notes": "any additional notes"
  }
}
```

### Webhook Request (Voice)
```json
{
  "call_id": "call_123",
  "channel": "voice",
  "from_number": "+1234567890",
  "to_number": "+0987654321",
  "call_sid": "CA1234567890",
  "transcription": "I'd like to schedule an appointment",
  "recording_url": "https://api.twilio.com/recording.mp3"
}
```

### Webhook Request (WhatsApp)
```json
{
  "call_id": "whatsapp_123",
  "channel": "whatsapp",
  "from_number": "1234567890",
  "to_number": "0987654321",
  "message_id": "msg_123",
  "message_text": "Hello, I'd like to schedule an appointment",
  "message_type": "text"
}
```

### Calendar Event
```json
{
  "title": "Appointment with John Doe",
  "start_time": "2024-01-15T14:30:00Z",
  "end_time": "2024-01-15T15:30:00Z",
  "description": "Consultation appointment",
  "attendees": ["john@example.com"],
  "location": "Office"
}
```

## System Components

### 1. Webhook Handlers (`app/webhooks/`)
- **Voice Handler**: Processes Twilio voice calls and transcriptions
- **WhatsApp Handler**: Handles WhatsApp message webhooks
- **SMS Handler**: Processes SMS messages via Twilio
- **Idempotency**: Ensures duplicate webhooks are handled gracefully

### 2. AI Engine (`app/services/`)
- **Intent Extraction**: Uses OpenAI GPT-4 to extract intents and slots
- **Response Generation**: Generates appropriate responses based on intent
- **Knowledge Base**: FAQ system with semantic search
- **Slot Filling**: Extracts structured data (dates, times, contact info)

### 3. Business Logic (`app/services/`)
- **Calendar Service**: Google Calendar integration for scheduling
- **Communication Service**: Handles responses via multiple channels
- **Validation Service**: Validates appointments and availability
- **Notification Service**: Sends confirmations and reminders

### 4. Data Layer (`app/database/`)
- **Models**: SQLAlchemy models for data persistence
- **Migrations**: Alembic for database schema management
- **Cache**: Redis for session management and rate limiting
- **Logging**: Structured logging with audit trails

## Exact Developer Tasks

### Task 1: Environment Setup
```bash
# Clone repository
git clone <repository-url>
cd sara

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp env.example .env
# Edit .env with your API keys

# Set up Google Calendar credentials
# Download credentials.json from Google Cloud Console
# Place in project root

# Run database migrations
alembic upgrade head
```

### Task 2: Local Development
```bash
# Start development server
python app/main.py

# Or use Docker Compose
docker-compose up -d

# Run tests
pytest

# Run linting
flake8 app/
black app/
mypy app/
```

### Task 3: Database Setup
```bash
# Create initial migration
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head

# Seed initial data
python -c "from app.database import seed_initial_data; seed_initial_data()"
```

### Task 4: External Service Configuration

#### OpenAI Setup
1. Get API key from OpenAI
2. Add to `.env`: `OPENAI_API_KEY=your_key_here`
3. Test with: `curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models`

#### Twilio Setup
1. Create Twilio account
2. Get Account SID and Auth Token
3. Purchase phone number
4. Add to `.env`:
   ```
   TWILIO_ACCOUNT_SID=your_sid
   TWILIO_AUTH_TOKEN=your_token
   TWILIO_PHONE_NUMBER=+1234567890
   ```

#### WhatsApp Business API Setup
1. Create Meta Business account
2. Set up WhatsApp Business API
3. Get access token and phone number ID
4. Add to `.env`:
   ```
   WHATSAPP_ACCESS_TOKEN=your_token
   WHATSAPP_PHONE_NUMBER_ID=your_phone_id
   WHATSAPP_VERIFY_TOKEN=your_verify_token
   ```

#### Google Calendar Setup
1. Create Google Cloud project
2. Enable Calendar API
3. Create service account
4. Download credentials.json
5. Add to `.env`:
   ```
   GOOGLE_CALENDAR_ID=your_calendar@gmail.com
   ```

### Task 5: Testing
```bash
# Run all tests
pytest

# Run specific test categories
pytest -m unit
pytest -m integration

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_api.py -v
```

### Task 6: Deployment
```bash
# Build Docker image
./scripts/build.sh v1.0.0 your-registry.com

# Deploy to Kubernetes
./scripts/deploy.sh v1.0.0 your-registry.com

# Or use Docker Compose
docker-compose up -d
```

## Prompt Engineering & AI Templates

### Intent Extraction Prompt
```
Analyze the following {channel} message and extract the intent and relevant information:

Message: "{text}"

Please extract:
1. Intent (schedule, faq, contact, cancel, reschedule, or unknown)
2. Confidence score (0.0 to 1.0)
3. Contact information (name, email, phone if mentioned)
4. Appointment details (date, time if scheduling)
5. Any other relevant slots

Respond with a JSON object in this exact format:
{
    "intent": "schedule|faq|contact|cancel|reschedule|unknown",
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
        "service_type": "consultation",
        "urgency": "normal",
        "notes": "any additional notes"
    }
}
```

### Response Generation Prompt
```
Generate a professional appointment confirmation message for {business_name}.

Appointment Details:
- Date: {date}
- Time: {time}
- Contact: {contact_name}

The message should:
- Confirm the appointment details
- Be friendly and professional
- Include next steps
- Be appropriate for {channel} communication
- Be concise but complete

Generate the message:
```

### FAQ Response Prompt
```
The user asked: "{question}"

Generate a helpful response for {business_name} that:
- Acknowledges their question
- Provides general helpful information
- Suggests they can schedule an appointment or contact us for more specific help
- Is appropriate for {channel} communication
- Is friendly and professional

Generate the response:
```

## Testing, Verification and Acceptance Criteria

### Unit Tests
- ✅ All service methods have unit tests
- ✅ All API endpoints have tests
- ✅ All models have validation tests
- ✅ Test coverage > 80%

### Integration Tests
- ✅ End-to-end webhook processing
- ✅ Database operations
- ✅ External API integrations
- ✅ Error handling scenarios

### Performance Tests
- ✅ Response time < 2 seconds for 95% of requests
- ✅ Can handle 100 concurrent requests
- ✅ Database queries optimized
- ✅ Memory usage within limits

### Security Tests
- ✅ Input validation
- ✅ SQL injection prevention
- ✅ XSS prevention
- ✅ Rate limiting
- ✅ Authentication/authorization

### Acceptance Criteria
- ✅ Voice calls are transcribed and processed
- ✅ WhatsApp messages are received and responded to
- ✅ SMS messages are handled correctly
- ✅ Appointments are created in Google Calendar
- ✅ FAQ responses are generated from knowledge base
- ✅ All interactions are logged and auditable
- ✅ System is idempotent (duplicate webhooks ignored)
- ✅ Error handling is graceful
- ✅ System is deployable with Docker

## Deployment, Monitoring & Production Hardening

### Deployment Checklist
- [ ] Docker image built and tested
- [ ] Kubernetes manifests configured
- [ ] Secrets and configmaps created
- [ ] Database migrations applied
- [ ] Health checks configured
- [ ] Monitoring and alerting set up
- [ ] SSL certificates configured
- [ ] Load balancer configured
- [ ] Backup strategy implemented

### Monitoring Setup
- [ ] Prometheus metrics collection
- [ ] Grafana dashboards configured
- [ ] Alerting rules defined
- [ ] Log aggregation (ELK stack)
- [ ] Health check endpoints
- [ ] Performance monitoring
- [ ] Error tracking

### Security Hardening
- [ ] Secrets management (Kubernetes secrets)
- [ ] Network policies configured
- [ ] RBAC permissions set
- [ ] Pod security standards enforced
- [ ] SSL/TLS encryption
- [ ] Input validation
- [ ] Rate limiting
- [ ] Audit logging

### Production Configuration
- [ ] Resource limits set
- [ ] Horizontal pod autoscaling
- [ ] Pod disruption budgets
- [ ] Rolling update strategy
- [ ] Database connection pooling
- [ ] Redis caching
- [ ] CDN configuration

## Next Steps & Feature Roadmap

### Phase 1: Core Functionality (Current)
- ✅ Voice call handling
- ✅ WhatsApp message processing
- ✅ SMS handling
- ✅ Intent extraction
- ✅ Calendar integration
- ✅ FAQ system
- ✅ Basic logging and audit

### Phase 2: Enhanced Features
- [ ] Multi-language support
- [ ] Advanced scheduling (recurring appointments)
- [ ] Email integration
- [ ] Advanced analytics dashboard
- [ ] Custom business rules
- [ ] Integration with CRM systems

### Phase 3: Advanced AI Features
- [ ] Sentiment analysis
- [ ] Conversation context
- [ ] Personalized responses
- [ ] Learning from interactions
- [ ] Advanced NLP capabilities
- [ ] Voice synthesis (TTS)

### Phase 4: Enterprise Features
- [ ] Multi-tenant support
- [ ] Advanced security features
- [ ] Compliance reporting
- [ ] Advanced monitoring
- [ ] Custom integrations
- [ ] White-label solution

## Maintenance & Support

### Daily Operations
- Monitor system health
- Check error logs
- Verify external service status
- Review performance metrics
- Check backup status

### Weekly Operations
- Review audit logs
- Update knowledge base
- Performance optimization
- Security review
- Capacity planning

### Monthly Operations
- Security updates
- Dependency updates
- Performance analysis
- Cost optimization
- Feature planning

## Troubleshooting Guide

### Common Issues
1. **Webhook not receiving calls**
   - Check Twilio webhook URL configuration
   - Verify SSL certificate
   - Check firewall rules

2. **Intent extraction failing**
   - Verify OpenAI API key
   - Check API rate limits
   - Review prompt engineering

3. **Calendar events not creating**
   - Check Google Calendar API credentials
   - Verify calendar permissions
   - Check timezone settings

4. **Database connection issues**
   - Verify database URL
   - Check network connectivity
   - Review connection pool settings

### Emergency Procedures
1. **System down**
   - Check pod status
   - Review logs
   - Restart services
   - Escalate if needed

2. **Data corruption**
   - Stop writes
   - Restore from backup
   - Verify data integrity
   - Resume operations

3. **Security incident**
   - Isolate affected systems
   - Review logs
   - Notify security team
   - Document incident

## Conclusion

This runbook provides complete engineering specifications for Sara AI Receptionist. The system is designed to be scalable, maintainable, and production-ready with comprehensive monitoring, security, and operational procedures.

The implementation includes all required features and meets the success criteria outlined in the vision. The system is ready for deployment and can be extended with additional features as outlined in the roadmap.
