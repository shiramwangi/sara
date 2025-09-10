# Sara AI Receptionist - Development Guide

## Quick Start

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- Git
- OpenAI API key
- Twilio account
- WhatsApp Business API access
- Google Calendar API credentials

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd sara
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your API keys and configuration
   ```

5. **Set up Google Calendar credentials**
   - Download credentials.json from Google Cloud Console
   - Place it in the project root

6. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

7. **Start the development server**
   ```bash
   python app/main.py
   ```

### Docker Development

1. **Build and run with Docker Compose**
   ```bash
   docker-compose up -d
   ```

2. **View logs**
   ```bash
   docker-compose logs -f sara
   ```

3. **Stop services**
   ```bash
   docker-compose down
   ```

## Project Structure

```
sara/
├── app/                    # Main application code
│   ├── __init__.py
│   ├── main.py            # FastAPI application entry point
│   ├── config.py          # Configuration management
│   ├── models.py          # Pydantic and SQLAlchemy models
│   ├── database.py        # Database configuration
│   ├── api/               # API endpoints
│   │   ├── health.py      # Health check endpoints
│   │   ├── logs.py        # Logs and audit endpoints
│   │   └── admin.py       # Admin endpoints
│   ├── webhooks/          # Webhook handlers
│   │   ├── voice.py       # Twilio voice webhooks
│   │   ├── whatsapp.py    # WhatsApp webhooks
│   │   └── sms.py         # SMS webhooks
│   ├── services/          # Business logic services
│   │   ├── intent_extraction.py    # AI intent extraction
│   │   ├── response_generation.py  # Response generation
│   │   ├── calendar_service.py     # Google Calendar integration
│   │   ├── communication_service.py # Communication channels
│   │   └── knowledge_base.py       # FAQ management
│   ├── middleware/        # Custom middleware
│   │   ├── logging.py     # Request/response logging
│   │   └── rate_limiting.py # Rate limiting
│   ├── audit/             # Audit and compliance
│   │   └── audit_logger.py # Audit logging system
│   └── utils/             # Utility functions
│       └── idempotency.py # Idempotency handling
├── tests/                 # Test suite
│   ├── conftest.py        # Pytest configuration
│   ├── test_api.py        # API endpoint tests
│   ├── test_models.py     # Model tests
│   ├── test_services.py   # Service tests
│   └── test_integration.py # Integration tests
├── k8s/                   # Kubernetes manifests
├── alembic/               # Database migrations
├── scripts/               # Deployment scripts
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker configuration
├── docker-compose.yml    # Docker Compose configuration
└── README.md             # Project overview
```

## Development Workflow

### 1. Feature Development

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Follow the existing code structure
   - Add tests for new functionality
   - Update documentation as needed

3. **Run tests**
   ```bash
   pytest
   ```

4. **Run linting**
   ```bash
   flake8 app/
   black app/
   mypy app/
   ```

5. **Commit your changes**
   ```bash
   git add .
   git commit -m "Add your feature description"
   ```

### 2. Database Changes

1. **Create a migration**
   ```bash
   alembic revision --autogenerate -m "Description of changes"
   ```

2. **Review the generated migration**
   - Check `alembic/versions/` for the new migration file
   - Verify the changes are correct

3. **Apply the migration**
   ```bash
   alembic upgrade head
   ```

### 3. Testing

#### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_api.py

# Run with coverage
pytest --cov=app

# Run integration tests only
pytest -m integration

# Run unit tests only
pytest -m unit
```

#### Test Categories

- **Unit Tests**: Test individual functions and classes
- **Integration Tests**: Test component interactions
- **API Tests**: Test HTTP endpoints
- **Model Tests**: Test data models and validation

### 4. Code Quality

#### Linting

```bash
# Run flake8 for style checking
flake8 app/

# Run black for code formatting
black app/

# Run mypy for type checking
mypy app/
```

#### Pre-commit Hooks

Set up pre-commit hooks to automatically run linting:

```bash
pip install pre-commit
pre-commit install
```

## API Development

### Adding New Endpoints

1. **Create endpoint in appropriate module**
   ```python
   # app/api/your_module.py
   from fastapi import APIRouter
   
   router = APIRouter()
   
   @router.get("/your-endpoint")
   async def your_endpoint():
       return {"message": "Hello World"}
   ```

2. **Register router in main.py**
   ```python
   from app.api.your_module import router
   app.include_router(router, prefix="/api/v1", tags=["your-tag"])
   ```

3. **Add tests**
   ```python
   def test_your_endpoint(client):
       response = client.get("/api/v1/your-endpoint")
       assert response.status_code == 200
   ```

### Adding New Services

1. **Create service class**
   ```python
   # app/services/your_service.py
   class YourService:
       def __init__(self):
           pass
       
       async def your_method(self):
           pass
   ```

2. **Add to dependency injection if needed**
   ```python
   # app/main.py
   from app.services.your_service import YourService
   
   def get_your_service():
       return YourService()
   ```

## Configuration

### Environment Variables

All configuration is managed through environment variables. See `env.example` for the complete list.

### Key Configuration Areas

- **OpenAI**: API key and model settings
- **Twilio**: Account credentials and phone numbers
- **WhatsApp**: Business API credentials
- **Google Calendar**: API credentials and calendar ID
- **Database**: Connection string and settings
- **Security**: Encryption keys and secrets

## Debugging

### Local Debugging

1. **Enable debug mode**
   ```bash
   export DEBUG=true
   python app/main.py
   ```

2. **Use debugger**
   ```python
   import pdb; pdb.set_trace()
   ```

3. **Check logs**
   ```bash
   tail -f logs/sara.log
   ```

### Docker Debugging

1. **View container logs**
   ```bash
   docker-compose logs -f sara
   ```

2. **Execute commands in container**
   ```bash
   docker-compose exec sara bash
   ```

3. **Debug with VS Code**
   - Install Remote-Containers extension
   - Open project in container

## Performance Optimization

### Database Optimization

1. **Add indexes for frequently queried fields**
   ```python
   # In models.py
   class Interaction(Base):
       __tablename__ = "interactions"
       
       call_id = Column(String(255), unique=True, index=True)
       created_at = Column(DateTime(timezone=True), index=True)
   ```

2. **Use connection pooling**
   ```python
   # In database.py
   engine = create_engine(
       DATABASE_URL,
       pool_size=20,
       max_overflow=30
   )
   ```

### Caching

1. **Add Redis caching**
   ```python
   import redis
   
   redis_client = redis.Redis(host='localhost', port=6379, db=0)
   
   def get_cached_data(key):
       return redis_client.get(key)
   ```

### Async Operations

1. **Use async/await for I/O operations**
   ```python
   async def process_data():
       result = await some_async_operation()
       return result
   ```

## Security Considerations

### Input Validation

1. **Validate all inputs**
   ```python
   from pydantic import BaseModel, validator
   
   class YourModel(BaseModel):
       field: str
       
       @validator('field')
       def validate_field(cls, v):
           if not v:
               raise ValueError('Field cannot be empty')
           return v
   ```

### Authentication

1. **Verify webhook signatures**
   ```python
   from twilio.request_validator import RequestValidator
   
   validator = RequestValidator(auth_token)
   is_valid = validator.validate(url, params, signature)
   ```

### Rate Limiting

1. **Implement rate limiting**
   ```python
   from app.middleware.rate_limiting import RateLimitingMiddleware
   
   app.add_middleware(RateLimitingMiddleware, calls_per_minute=60)
   ```

## Monitoring and Observability

### Logging

1. **Use structured logging**
   ```python
   import structlog
   
   logger = structlog.get_logger()
   logger.info("Processing request", call_id=call_id, user_id=user_id)
   ```

2. **Add correlation IDs**
   ```python
   # In middleware
   request_id = f"req_{int(time.time() * 1000)}"
   logger.info("Request started", request_id=request_id)
   ```

### Metrics

1. **Add custom metrics**
   ```python
   from prometheus_client import Counter, Histogram
   
   request_count = Counter('requests_total', 'Total requests')
   request_duration = Histogram('request_duration_seconds', 'Request duration')
   ```

### Health Checks

1. **Implement health checks**
   ```python
   @app.get("/health")
   async def health_check():
       # Check database connection
       # Check external services
       return {"status": "healthy"}
   ```

## Deployment

### Local Deployment

1. **Using Docker Compose**
   ```bash
   docker-compose up -d
   ```

2. **Using Kubernetes**
   ```bash
   kubectl apply -f k8s/
   ```

### Production Deployment

1. **Build production image**
   ```bash
   ./scripts/build.sh v1.0.0 your-registry.com
   ```

2. **Deploy to Kubernetes**
   ```bash
   ./scripts/deploy.sh v1.0.0 your-registry.com
   ```

## Troubleshooting

### Common Issues

1. **Database connection errors**
   - Check DATABASE_URL
   - Verify database is running
   - Check network connectivity

2. **API key errors**
   - Verify API keys in .env
   - Check API key permissions
   - Verify rate limits

3. **Webhook errors**
   - Check webhook URLs
   - Verify webhook signatures
   - Check request format

### Getting Help

1. **Check logs**
   ```bash
   docker-compose logs sara
   ```

2. **Run tests**
   ```bash
   pytest -v
   ```

3. **Check health endpoint**
   ```bash
   curl http://localhost:8000/health
   ```

## Contributing

1. **Follow the coding standards**
2. **Write tests for new features**
3. **Update documentation**
4. **Submit pull requests**
5. **Respond to code review feedback**
