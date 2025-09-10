"""
Communication Service for WhatsApp, SMS, and Email
"""

import logging
import structlog
from typing import Optional, Dict, Any
import httpx
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from twilio.rest import Client as TwilioClient
from twilio.twiml import VoiceResponse

from app.config import settings
from app.models import ChannelType, ResponseMessage

logger = structlog.get_logger()


class CommunicationService:
    """Service for sending messages via various channels"""
    
    def __init__(self):
        self.twilio_client = TwilioClient(settings.twilio_account_sid, settings.twilio_auth_token)
        self.whatsapp_phone_number_id = settings.whatsapp_phone_number_id
        self.whatsapp_access_token = settings.whatsapp_access_token
    
    async def send_voice_response(
        self,
        to_number: str,
        response_text: str
    ) -> bool:
        """
        Send voice response via Twilio (TTS)
        """
        try:
            # Create TwiML response for voice
            response = VoiceResponse()
            response.say(response_text, voice='alice', language='en-US')
            
            # In a real implementation, you would return this TwiML
            # For now, we'll log the response
            logger.info("Voice response generated", to_number=to_number, response_text=response_text)
            
            return True
            
        except Exception as e:
            logger.error("Error sending voice response", to_number=to_number, error=str(e))
            return False
    
    async def send_whatsapp_message(
        self,
        to_number: str,
        message_text: str,
        media_url: Optional[str] = None
    ) -> bool:
        """
        Send WhatsApp message via Meta API
        """
        try:
            url = f"https://graph.facebook.com/v18.0/{self.whatsapp_phone_number_id}/messages"
            
            headers = {
                "Authorization": f"Bearer {self.whatsapp_access_token}",
                "Content-Type": "application/json"
            }
            
            # Prepare message data
            message_data = {
                "messaging_product": "whatsapp",
                "to": to_number,
                "type": "text",
                "text": {
                    "body": message_text
                }
            }
            
            # Add media if provided
            if media_url:
                message_data["type"] = "image"
                message_data["image"] = {
                    "link": media_url
                }
                del message_data["text"]
            
            # Send message
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=message_data, headers=headers)
                response.raise_for_status()
                
                result = response.json()
                message_id = result.get("messages", [{}])[0].get("id")
                
                logger.info("WhatsApp message sent", to_number=to_number, message_id=message_id)
                return True
                
        except Exception as e:
            logger.error("Error sending WhatsApp message", to_number=to_number, error=str(e))
            return False
    
    async def send_sms(
        self,
        to_number: str,
        message_text: str
    ) -> bool:
        """
        Send SMS via Twilio
        """
        try:
            message = self.twilio_client.messages.create(
                body=message_text,
                from_=settings.twilio_phone_number,
                to=to_number
            )
            
            logger.info("SMS sent", to_number=to_number, message_sid=message.sid)
            return True
            
        except Exception as e:
            logger.error("Error sending SMS", to_number=to_number, error=str(e))
            return False
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        message_text: str,
        html_content: Optional[str] = None
    ) -> bool:
        """
        Send email via SMTP
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = settings.smtp_username
            msg['To'] = to_email
            
            # Add text content
            text_part = MIMEText(message_text, 'plain')
            msg.attach(text_part)
            
            # Add HTML content if provided
            if html_content:
                html_part = MIMEText(html_content, 'html')
                msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(settings.smtp_server, settings.smtp_port) as server:
                server.starttls()
                server.login(settings.smtp_username, settings.smtp_password)
                server.send_message(msg)
            
            logger.info("Email sent", to_email=to_email, subject=subject)
            return True
            
        except Exception as e:
            logger.error("Error sending email", to_email=to_email, error=str(e))
            return False
    
    async def send_response(
        self,
        response: ResponseMessage
    ) -> bool:
        """
        Send response via appropriate channel
        """
        try:
            if response.channel == ChannelType.VOICE:
                return await self.send_voice_response(
                    to_number=response.to_number,
                    response_text=response.text
                )
            elif response.channel == ChannelType.WHATSAPP:
                return await self.send_whatsapp_message(
                    to_number=response.to_number,
                    message_text=response.text,
                    media_url=response.media_url
                )
            elif response.channel == ChannelType.SMS:
                return await self.send_sms(
                    to_number=response.to_number,
                    message_text=response.text
                )
            elif response.channel == ChannelType.EMAIL:
                return await self.send_email(
                    to_email=response.to_number,  # Using to_number as email for simplicity
                    subject=f"Response from {settings.business_name}",
                    message_text=response.text
                )
            else:
                logger.error("Unsupported channel", channel=response.channel)
                return False
                
        except Exception as e:
            logger.error("Error sending response", error=str(e))
            return False
    
    async def send_appointment_confirmation(
        self,
        channel: ChannelType,
        to_number: str,
        appointment_details: Dict[str, Any],
        contact_info: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Send appointment confirmation message
        """
        try:
            # Build confirmation message
            message_parts = [
                f"Hello {contact_info.get('name', 'there')}!" if contact_info else "Hello!",
                "",
                "Your appointment has been confirmed:",
                f"Date: {appointment_details.get('date')}",
                f"Time: {appointment_details.get('time')}",
                f"Duration: {appointment_details.get('duration', '1 hour')}",
                "",
                "We look forward to seeing you!",
                "",
                f"Best regards,\n{settings.business_name}"
            ]
            
            message_text = "\n".join(message_parts)
            
            # Send via appropriate channel
            if channel == ChannelType.VOICE:
                return await self.send_voice_response(to_number, message_text)
            elif channel == ChannelType.WHATSAPP:
                return await self.send_whatsapp_message(to_number, message_text)
            elif channel == ChannelType.SMS:
                return await self.send_sms(to_number, message_text)
            elif channel == ChannelType.EMAIL:
                subject = f"Appointment Confirmation - {appointment_details.get('date')}"
                return await self.send_email(to_number, subject, message_text)
            else:
                logger.error("Unsupported channel for confirmation", channel=channel)
                return False
                
        except Exception as e:
            logger.error("Error sending appointment confirmation", error=str(e))
            return False
    
    async def send_appointment_reminder(
        self,
        channel: ChannelType,
        to_number: str,
        appointment_details: Dict[str, Any],
        hours_before: int = 24
    ) -> bool:
        """
        Send appointment reminder
        """
        try:
            message_parts = [
                "Appointment Reminder",
                "",
                f"Your appointment is scheduled for:",
                f"Date: {appointment_details.get('date')}",
                f"Time: {appointment_details.get('time')}",
                "",
                f"This is a reminder {hours_before} hours before your appointment.",
                "",
                "If you need to reschedule or cancel, please contact us.",
                "",
                f"Best regards,\n{settings.business_name}"
            ]
            
            message_text = "\n".join(message_parts)
            
            # Send via appropriate channel
            if channel == ChannelType.VOICE:
                return await self.send_voice_response(to_number, message_text)
            elif channel == ChannelType.WHATSAPP:
                return await self.send_whatsapp_message(to_number, message_text)
            elif channel == ChannelType.SMS:
                return await self.send_sms(to_number, message_text)
            elif channel == ChannelType.EMAIL:
                subject = f"Appointment Reminder - {appointment_details.get('date')}"
                return await self.send_email(to_number, subject, message_text)
            else:
                logger.error("Unsupported channel for reminder", channel=channel)
                return False
                
        except Exception as e:
            logger.error("Error sending appointment reminder", error=str(e))
            return False
    
    def generate_twiml_response(self, message_text: str) -> str:
        """
        Generate TwiML response for voice calls
        """
        try:
            response = VoiceResponse()
            response.say(message_text, voice='alice', language='en-US')
            response.hangup()
            
            return str(response)
            
        except Exception as e:
            logger.error("Error generating TwiML response", error=str(e))
            # Return basic TwiML on error
            response = VoiceResponse()
            response.say("Thank you for calling. We'll get back to you soon.", voice='alice')
            response.hangup()
            return str(response)
