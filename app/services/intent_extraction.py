"""
AI Intent Extraction Service using OpenAI GPT-4
"""

import json
import logging
import structlog
from datetime import datetime
from typing import Optional, Dict, Any
import asyncio
import openai
from openai import AsyncOpenAI

from app.config import settings
from app.models import (
    IntentExtraction,
    IntentType,
    ContactInfo,
    AppointmentSlot,
    ChannelType,
)

logger = structlog.get_logger()


class IntentExtractionService:
    """Service for extracting intents and slots from user input using OpenAI"""

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model

    async def extract_intent(self, text: str, channel: ChannelType) -> IntentExtraction:
        """
        Extract intent and slots from user input text
        """
        try:
            logger.info("Extracting intent", text_length=len(text), channel=channel)

            # Prepare the prompt for intent extraction
            prompt = self._build_intent_extraction_prompt(text, channel)

            # Call OpenAI API (support both async client and test MagicMock)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt},
                ],
                temperature=settings.temperature,
                max_tokens=settings.max_tokens,
                response_format={"type": "json_object"},
            )
            if asyncio.iscoroutine(response):
                response = await response

            # Parse the response
            result = json.loads(response.choices[0].message.content)

            # Create IntentExtraction object
            intent_extraction = self._parse_intent_result(result, text)

            logger.info(
                "Intent extracted successfully",
                intent=intent_extraction.intent,
                confidence=intent_extraction.confidence,
                slots_count=len(intent_extraction.slots),
            )

            return intent_extraction

        except Exception as e:
            logger.error("Error extracting intent", error=str(e), exc_info=True)
            # Return fallback intent
            return IntentExtraction(
                intent=IntentType.UNKNOWN, confidence=0.0, slots={}, raw_text=text
            )

    def _build_intent_extraction_prompt(self, text: str, channel: ChannelType) -> str:
        """Build the prompt for intent extraction"""
        return f"""
Analyze the following {channel.value} message and extract the intent and relevant information:

Message: "{text}"

Please extract:
1. Intent (schedule, faq, contact, cancel, reschedule, or unknown)
2. Confidence score (0.0 to 1.0)
3. Contact information (name, email, phone if mentioned)
4. Appointment details (date, time if scheduling)
5. Any other relevant slots

Respond with a JSON object in this exact format:
{{
    "intent": "schedule|faq|contact|cancel|reschedule|unknown",
    "confidence": 0.95,
    "contact_info": {{
        "name": "John Doe",
        "email": "john@example.com", 
        "phone": "+1234567890"
    }},
    "appointment": {{
        "date": "2024-01-15",
        "time": "14:30",
        "timezone": "UTC"
    }},
    "slots": {{
        "service_type": "consultation",
        "urgency": "normal",
        "notes": "any additional notes"
    }}
}}

Guidelines:
- For scheduling: extract date/time, contact info, and service type
- For FAQ: identify the question topic and keywords
- For contact: extract name, email, phone
- For cancel/reschedule: extract appointment reference and new details
- Use null for missing information
- Be conservative with confidence scores
- Extract dates in YYYY-MM-DD format
- Extract times in HH:MM format (24-hour)
"""

    def _get_system_prompt(self) -> str:
        """Get the system prompt for intent extraction"""
        return f"""
You are Sara, an AI receptionist for {settings.business_name}. 

Your job is to analyze incoming messages and extract:
1. What the person wants (intent)
2. Their contact information 
3. Appointment details if they're scheduling
4. Any other relevant information

You work for a business that offers appointments and answers common questions.
Be accurate and conservative with confidence scores.
Extract information only if it's clearly stated or strongly implied.
"""

    def _parse_intent_result(
        self, result: Dict[str, Any], raw_text: str
    ) -> IntentExtraction:
        """Parse the OpenAI response into IntentExtraction object"""
        try:
            # Extract intent
            intent_str = result.get("intent", "unknown").lower()
            intent = IntentType.UNKNOWN
            for intent_type in IntentType:
                if intent_type.value == intent_str:
                    intent = intent_type
                    break

            # Extract confidence
            confidence = float(result.get("confidence", 0.0))
            confidence = max(0.0, min(1.0, confidence))  # Clamp between 0 and 1

            # Extract contact info
            contact_info = None
            contact_data = result.get("contact_info") or {}
            if any(contact_data.values()):
                contact_info = ContactInfo(
                    name=contact_data.get("name"),
                    email=contact_data.get("email"),
                    phone=contact_data.get("phone"),
                )

            # Extract appointment details
            appointment = None
            appointment_data = result.get("appointment") or {}
            if appointment_data.get("date") and appointment_data.get("time"):
                appointment = AppointmentSlot(
                    date=appointment_data["date"],
                    time=appointment_data["time"],
                    timezone=appointment_data.get("timezone", "UTC"),
                )

            # Extract other slots
            slots = result.get("slots") or {}

            return IntentExtraction(
                intent=intent,
                confidence=confidence,
                slots=slots,
                contact_info=contact_info,
                appointment=appointment,
                raw_text=raw_text,
            )

        except Exception as e:
            logger.error("Error parsing intent result", error=str(e))
            return IntentExtraction(
                intent=IntentType.UNKNOWN, confidence=0.0, slots={}, raw_text=raw_text
            )

    async def extract_contact_info(self, text: str) -> Optional[ContactInfo]:
        """Extract contact information from text"""
        try:
            prompt = f"""
Extract contact information from this text: "{text}"

Look for:
- Name (first and last name)
- Email address
- Phone number

Respond with JSON:
{{
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+1234567890"
}}

Use null for missing information.
"""

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at extracting contact information from text.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=200,
                response_format={"type": "json_object"},
            )

            result = json.loads(response.choices[0].message.content)

            if any(result.values()):
                return ContactInfo(
                    name=result.get("name"),
                    email=result.get("email"),
                    phone=result.get("phone"),
                )

            return None

        except Exception as e:
            logger.error("Error extracting contact info", error=str(e))
            return None

    async def extract_appointment_details(self, text: str) -> Optional[AppointmentSlot]:
        """Extract appointment details from text"""
        try:
            prompt = f"""
Extract appointment details from this text: "{text}"

Look for:
- Date (convert to YYYY-MM-DD format)
- Time (convert to HH:MM format, 24-hour)
- Timezone (if mentioned)

Respond with JSON:
{{
    "date": "2024-01-15",
    "time": "14:30",
    "timezone": "UTC"
}}

Use null for missing information.
If no clear appointment details, return null.
"""

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at extracting appointment details from text.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=200,
                response_format={"type": "json_object"},
            )

            result = json.loads(response.choices[0].message.content)

            if result.get("date") and result.get("time"):
                return AppointmentSlot(
                    date=result["date"],
                    time=result["time"],
                    timezone=result.get("timezone", "UTC"),
                )

            return None

        except Exception as e:
            logger.error("Error extracting appointment details", error=str(e))
            return None
