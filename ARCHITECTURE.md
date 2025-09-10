# Sara AI Receptionist - System Architecture

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

## Component Details

### 1. Webhook Handlers (`app/webhooks/`)
- **Voice Handler**: Processes Twilio voice calls and transcriptions
- **WhatsApp Handler**: Handles WhatsApp message webhooks
- **SMS Handler**: Processes SMS messages via Twilio
- **Idempotency**: Ensures duplicate webhooks are handled gracefully

### 2. AI Engine (`app/ai/`)
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

## Data Flow

### 1. Incoming Request Flow
```
External Channel → Webhook Handler → Intent Extraction → Business Logic → Response Generation → External Channel
```

### 2. Intent Processing Flow
```
Raw Text → OpenAI GPT-4 → Intent Classification → Slot Extraction → Validation → Action Execution
```

### 3. Scheduling Flow
```
Schedule Intent → Availability Check → Calendar Creation → Confirmation Response → Logging
```

## Security Architecture

### 1. Authentication & Authorization
- **Webhook Verification**: Twilio/WhatsApp signature verification
- **API Keys**: Secure storage of external service credentials
- **Rate Limiting**: Per-IP and per-phone number limits

### 2. Data Protection
- **Encryption**: Sensitive data encrypted at rest
- **PII Handling**: Contact information properly secured
- **Audit Logging**: Complete interaction audit trail

### 3. Infrastructure Security
- **HTTPS Only**: All communications encrypted
- **Environment Isolation**: Production/staging separation
- **Secret Management**: Environment variables for secrets

## Scalability Considerations

### 1. Horizontal Scaling
- **Stateless Design**: No server-side session storage
- **Load Balancing**: Multiple backend instances
- **Database Connection Pooling**: Efficient database connections

### 2. Performance Optimization
- **Caching**: Redis for frequently accessed data
- **Async Processing**: Non-blocking I/O operations
- **Connection Reuse**: HTTP client connection pooling

### 3. Monitoring & Observability
- **Health Checks**: Endpoint monitoring
- **Metrics**: Request rates, response times, error rates
- **Logging**: Structured logs with correlation IDs
- **Alerting**: Automated alerts for failures

## Deployment Architecture

### 1. Containerization
- **Docker**: Application containerization
- **Docker Compose**: Local development environment
- **Multi-stage Builds**: Optimized production images

### 2. Infrastructure
- **Cloud Provider**: AWS/GCP/Azure deployment
- **Container Orchestration**: Kubernetes or Docker Swarm
- **Database**: Managed PostgreSQL service
- **Cache**: Managed Redis service

### 3. CI/CD Pipeline
- **Source Control**: Git-based workflow
- **Automated Testing**: Unit, integration, and E2E tests
- **Deployment**: Automated deployment to staging/production
- **Rollback**: Quick rollback capabilities

## Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Cache**: Redis
- **AI**: OpenAI GPT-4 API
- **Task Queue**: Celery (for async processing)

### External Integrations
- **Voice/SMS**: Twilio API
- **WhatsApp**: Meta WhatsApp Business API
- **Calendar**: Google Calendar API
- **Email**: SMTP (Gmail/SendGrid)

### DevOps
- **Containerization**: Docker
- **Orchestration**: Docker Compose / Kubernetes
- **Monitoring**: Prometheus + Grafana
- **Logging**: ELK Stack or similar
- **CI/CD**: GitHub Actions or GitLab CI

## API Design

### RESTful Endpoints
- `POST /webhook/voice` - Twilio voice webhook
- `POST /webhook/whatsapp` - WhatsApp message webhook
- `POST /webhook/sms` - SMS webhook
- `GET /health` - Health check
- `GET /logs/{call_id}` - Retrieve interaction logs
- `GET /admin/stats` - System statistics

### Webhook Security
- **Signature Verification**: All webhooks verified
- **Idempotency**: Duplicate request handling
- **Rate Limiting**: Per-source rate limits
- **Error Handling**: Graceful error responses

## Error Handling Strategy

### 1. Graceful Degradation
- **Fallback Responses**: Default responses when AI fails
- **Circuit Breakers**: Prevent cascade failures
- **Retry Logic**: Exponential backoff for transient failures

### 2. Error Classification
- **Client Errors**: 4xx responses with clear messages
- **Server Errors**: 5xx responses with logging
- **External Service Errors**: Proper error propagation

### 3. Monitoring & Alerting
- **Error Tracking**: Centralized error logging
- **Alert Thresholds**: Automated alerts for error spikes
- **Recovery Procedures**: Documented recovery steps
