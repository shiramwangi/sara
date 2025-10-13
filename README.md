# Sara - AI Receptionist

[![CI/CD Pipeline](https://github.com/shiramwangi/sara/actions/workflows/ci.yml/badge.svg)](https://github.com/shiramwangi/sara/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.116+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Sara** is an intelligent AI receptionist that handles inbound voice calls, WhatsApp messages, and SMS through advanced intent extraction and automated response generation. Built with FastAPI and powered by OpenAI GPT-4.

## 🎯 Vision & Success Criteria

**Vision**: Sara is an AI receptionist that answers inbound voice & message requests, handles FAQs, and performs actionable requests (bookings/emails/follow-ups) reliably through Google Calendar, Email, and WhatsApp/SMS. All interactions are logged and auditable.

**Success Criteria**:
- ✅ Incoming call or WhatsApp message → transcript received by backend
- ✅ AI extracts intent and slots (appointment date/time, name, email, phone) with >90% structure accuracy
- ✅ If intent = schedule: verifies availability, creates Google Calendar event, returns confirmation
- ✅ If intent = FAQ: answers from knowledge base and logs interaction
- ✅ All runs are idempotent: repeated webhook with same callId is ignored/deduplicated
- ✅ Easy to deploy: repo contains Dockerfile and deploy instructions

## 🚀 Quick Start

```bash
# Clone and setup
git clone https://github.com/shiramwangi/sara.git
cd sara
cp env.example .env
# Edit .env with your API keys

# Run with Docker
docker-compose up -d

# Or run locally
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app/main.py
```

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Voice Calls   │    │   WhatsApp      │    │   SMS/Email     │
│   (Twilio)      │    │   (API)         │    │   (Twilio)      │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │      Sara Backend         │
                    │   (FastAPI + AI Engine)   │
                    └─────────────┬─────────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │    External Services      │
                    │  Google Calendar + Email  │
                    └───────────────────────────┘
```

## API Endpoints

- `POST /webhook/voice` - Twilio voice webhook
- `POST /webhook/whatsapp` - WhatsApp message webhook  
- `POST /webhook/sms` - SMS webhook
- `GET /health` - Health check
- `GET /logs/{call_id}` - Retrieve interaction logs

## Environment Variables

See `.env.example` for required configuration.

## Development

See `DEVELOPMENT.md` for detailed setup and development instructions.

## Example output

<img width="663" height="161" alt="image" src="https://github.com/user-attachments/assets/79eb064a-3221-4c60-bd16-42c417b2b1fa" />

contributors are me, and fatma

