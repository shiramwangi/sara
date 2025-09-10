"""
Twilio Voice Webhook Handler
"""

import logging
import structlog
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import VoiceWebhookRequest, ChannelType, InteractionStatus, Interaction
from app.services.intent_extraction import IntentExtractionService
from app.services.response_generation import ResponseGenerationService
from app.services.calendar_service import CalendarService
from app.services.communication_service import CommunicationService
from app.utils.idempotency import check_idempotency, mark_processed

logger = structlog.get_logger()
router = APIRouter()


@router.post("/voice")
async def handle_voice_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Handle incoming Twilio voice webhook
    """
    try:
        # Parse webhook data
        form_data = await request.form()
        
        # Extract required fields
        call_sid = form_data.get("CallSid")
        from_number = form_data.get("From")
        to_number = form_data.get("To")
        call_status = form_data.get("CallStatus")
        transcription = form_data.get("TranscriptionText", "")
        recording_url = form_data.get("RecordingUrl", "")
        
        if not call_sid:
            raise HTTPException(status_code=400, detail="Missing CallSid")
        
        # Create call_id (use CallSid as unique identifier)
        call_id = call_sid
        
        # Check idempotency
        if await check_idempotency(db, call_id):
            logger.info("Duplicate webhook received", call_id=call_id)
            return {"status": "duplicate", "message": "Request already processed"}
        
        # Create webhook request object
        webhook_request = VoiceWebhookRequest(
            call_id=call_id,
            channel=ChannelType.VOICE,
            from_number=from_number,
            to_number=to_number,
            call_sid=call_sid,
            transcription=transcription,
            recording_url=recording_url,
            raw_data=dict(form_data)
        )
        
        # Process the interaction
        await process_voice_interaction(webhook_request, db)
        
        # Mark as processed
        await mark_processed(db, call_id)
        
        return {"status": "success", "message": "Voice webhook processed"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error processing voice webhook", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


async def process_voice_interaction(
    webhook_request: VoiceWebhookRequest,
    db: Session
):
    """
    Process a voice interaction end-to-end
    """
    call_id = webhook_request.call_id
    
    try:
        # Create interaction record
        interaction = Interaction(
            call_id=call_id,
            channel=webhook_request.channel,
            status=InteractionStatus.PROCESSING,
            raw_webhook_data=webhook_request.raw_data
        )
        db.add(interaction)
        db.commit()
        
        logger.info("Processing voice interaction", call_id=call_id)
        
        # Extract intent and slots
        intent_service = IntentExtractionService()
        intent_result = await intent_service.extract_intent(
            text=webhook_request.transcription or "",
            channel=webhook_request.channel
        )
        
        # Update interaction with intent data
        interaction.intent = intent_result.intent
        interaction.intent_confidence = str(intent_result.confidence)
        interaction.extracted_slots = intent_result.slots
        interaction.contact_name = intent_result.contact_info.name if intent_result.contact_info else None
        interaction.contact_email = intent_result.contact_info.email if intent_result.contact_info else None
        interaction.contact_phone = intent_result.contact_info.phone if intent_result.contact_info else None
        
        # Generate response based on intent
        response_service = ResponseGenerationService()
        response = await response_service.generate_response(
            intent_result=intent_result,
            channel=webhook_request.channel,
            contact_info=intent_result.contact_info
        )
        
        # Handle specific intents
        if intent_result.intent.value == "schedule":
            await handle_scheduling_intent(intent_result, interaction, db)
        elif intent_result.intent.value == "faq":
            await handle_faq_intent(intent_result, interaction, db)
        
        # Update interaction with response
        interaction.response_text = response.text
        interaction.status = InteractionStatus.COMPLETED
        
        # Send response back to caller
        comm_service = CommunicationService()
        await comm_service.send_voice_response(
            to_number=webhook_request.from_number,
            response_text=response.text
        )
        
        db.commit()
        logger.info("Voice interaction completed successfully", call_id=call_id)
        
    except Exception as e:
        logger.error("Error processing voice interaction", call_id=call_id, error=str(e))
        
        # Update interaction with error
        interaction.status = InteractionStatus.FAILED
        interaction.error_message = str(e)
        db.commit()
        
        raise


async def handle_scheduling_intent(intent_result, interaction, db):
    """
    Handle scheduling intent - create calendar event
    """
    try:
        if not intent_result.appointment:
            raise ValueError("No appointment details found")
        
        calendar_service = CalendarService()
        event_id = await calendar_service.create_appointment(
            appointment=intent_result.appointment,
            contact_info=intent_result.contact_info,
            description=f"Appointment scheduled via voice call"
        )
        
        interaction.calendar_event_id = event_id
        logger.info("Calendar event created", event_id=event_id)
        
    except Exception as e:
        logger.error("Failed to create calendar event", error=str(e))
        raise


async def handle_faq_intent(intent_result, interaction, db):
    """
    Handle FAQ intent - answer from knowledge base
    """
    try:
        # FAQ handling is done in response generation
        # This is just for logging/auditing
        logger.info("FAQ intent handled", slots=intent_result.slots)
        
    except Exception as e:
        logger.error("Failed to handle FAQ intent", error=str(e))
        raise
