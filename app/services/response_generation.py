"""
Response Generation Service using OpenAI GPT-4
"""

import logging
import structlog
from typing import Optional, Dict, Any
import openai
from openai import AsyncOpenAI

from app.config import settings
from app.models import IntentExtraction, ContactInfo, ChannelType, IntentType
from app.services.knowledge_base import KnowledgeBaseService

logger = structlog.get_logger()


class ResponseGenerationService:
    """Service for generating appropriate responses based on intent"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        self.knowledge_base = KnowledgeBaseService()
    
    async def generate_response(
        self,
        intent_result: IntentExtraction,
        channel: ChannelType,
        contact_info: Optional[ContactInfo] = None
    ) -> Dict[str, str]:
        """
        Generate appropriate response based on intent and context
        """
        try:
            logger.info("Generating response", intent=intent_result.intent, channel=channel)
            
            if intent_result.intent == IntentType.SCHEDULE:
                return await self._generate_scheduling_response(intent_result, channel, contact_info)
            elif intent_result.intent == IntentType.FAQ:
                return await self._generate_faq_response(intent_result, channel)
            elif intent_result.intent == IntentType.CONTACT:
                return await self._generate_contact_response(intent_result, channel, contact_info)
            elif intent_result.intent == IntentType.CANCEL:
                return await self._generate_cancellation_response(intent_result, channel)
            elif intent_result.intent == IntentType.RESCHEDULE:
                return await self._generate_rescheduling_response(intent_result, channel, contact_info)
            else:
                return await self._generate_unknown_response(intent_result, channel)
                
        except Exception as e:
            logger.error("Error generating response", error=str(e))
            return {
                "text": "I apologize, but I'm having trouble understanding your request. Could you please try again or contact us directly?",
                "channel": channel.value
            }
    
    async def _generate_scheduling_response(
        self,
        intent_result: IntentExtraction,
        channel: ChannelType,
        contact_info: Optional[ContactInfo]
    ) -> Dict[str, str]:
        """Generate response for scheduling intent"""
        try:
            if not intent_result.appointment:
                return {
                    "text": "I'd be happy to help you schedule an appointment! Could you please provide your preferred date and time?",
                    "channel": channel.value
                }
            
            # Format the appointment details
            appointment = intent_result.appointment
            date_str = self._format_date(appointment.date)
            time_str = self._format_time(appointment.time)
            
            # Generate confirmation message
            prompt = f"""
Generate a professional appointment confirmation message for {settings.business_name}.

Appointment Details:
- Date: {date_str}
- Time: {time_str}
- Contact: {contact_info.name if contact_info and contact_info.name else 'Not provided'}

The message should:
- Confirm the appointment details
- Be friendly and professional
- Include next steps
- Be appropriate for {channel.value} communication
- Be concise but complete

Generate the message:
"""
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_scheduling_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=300
            )
            
            message = response.choices[0].message.content.strip()
            
            return {
                "text": message,
                "channel": channel.value
            }
            
        except Exception as e:
            logger.error("Error generating scheduling response", error=str(e))
            return {
                "text": "I've received your appointment request. I'll check our availability and get back to you shortly with confirmation details.",
                "channel": channel.value
            }
    
    async def _generate_faq_response(
        self,
        intent_result: IntentExtraction,
        channel: ChannelType
    ) -> Dict[str, str]:
        """Generate response for FAQ intent"""
        try:
            # Search knowledge base for relevant answer
            faq_answer = await self.knowledge_base.search_faq(intent_result.raw_text)
            
            if faq_answer:
                return {
                    "text": faq_answer,
                    "channel": channel.value
                }
            
            # If no specific FAQ found, generate a helpful response
            prompt = f"""
The user asked: "{intent_result.raw_text}"

Generate a helpful response for {settings.business_name} that:
- Acknowledges their question
- Provides general helpful information
- Suggests they can schedule an appointment or contact us for more specific help
- Is appropriate for {channel.value} communication
- Is friendly and professional

Generate the response:
"""
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_faq_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=300
            )
            
            message = response.choices[0].message.content.strip()
            
            return {
                "text": message,
                "channel": channel.value
            }
            
        except Exception as e:
            logger.error("Error generating FAQ response", error=str(e))
            return {
                "text": "Thank you for your question! I'd be happy to help you with that. Could you provide a bit more detail, or would you like to schedule an appointment to discuss this in person?",
                "channel": channel.value
            }
    
    async def _generate_contact_response(
        self,
        intent_result: IntentExtraction,
        channel: ChannelType,
        contact_info: Optional[ContactInfo]
    ) -> Dict[str, str]:
        """Generate response for contact intent"""
        try:
            if contact_info and contact_info.name:
                return {
                    "text": f"Thank you for providing your contact information, {contact_info.name}! I have your details and will make sure our team gets back to you soon. Is there anything specific you'd like to discuss or schedule?",
                    "channel": channel.value
                }
            else:
                return {
                    "text": "I'd be happy to help you get in touch with our team! Could you please provide your name and contact information so we can reach you?",
                    "channel": channel.value
                }
                
        except Exception as e:
            logger.error("Error generating contact response", error=str(e))
            return {
                "text": "Thank you for reaching out! I'll make sure our team gets back to you soon. Is there anything specific I can help you with today?",
                "channel": channel.value
            }
    
    async def _generate_cancellation_response(
        self,
        intent_result: IntentExtraction,
        channel: ChannelType
    ) -> Dict[str, str]:
        """Generate response for cancellation intent"""
        return {
            "text": "I understand you'd like to cancel an appointment. I'll help you with that. Could you please provide the appointment details or reference number so I can locate it in our system?",
            "channel": channel.value
        }
    
    async def _generate_rescheduling_response(
        self,
        intent_result: IntentExtraction,
        channel: ChannelType,
        contact_info: Optional[ContactInfo]
    ) -> Dict[str, str]:
        """Generate response for rescheduling intent"""
        return {
            "text": "I'd be happy to help you reschedule your appointment. Could you please provide the current appointment details and your preferred new date and time?",
            "channel": channel.value
        }
    
    async def _generate_unknown_response(
        self,
        intent_result: IntentExtraction,
        channel: ChannelType
    ) -> Dict[str, str]:
        """Generate response for unknown intent"""
        return {
            "text": "I'm not sure I understand what you're looking for. I can help you with scheduling appointments, answering questions, or connecting you with our team. What would you like to do today?",
            "channel": channel.value
        }
    
    def _get_scheduling_system_prompt(self) -> str:
        """Get system prompt for scheduling responses"""
        return f"""
You are Sara, a professional AI receptionist for {settings.business_name}.

When confirming appointments:
- Be warm and professional
- Clearly state the appointment details
- Mention any next steps or preparation needed
- Keep the message concise but complete
- Use appropriate tone for the communication channel
- Include contact information if helpful
"""
    
    def _get_faq_system_prompt(self) -> str:
        """Get system prompt for FAQ responses"""
        return f"""
You are Sara, a helpful AI receptionist for {settings.business_name}.

When answering questions:
- Be helpful and informative
- Stay within your knowledge of the business
- If you don't know something specific, offer to connect them with the right person
- Be encouraging about scheduling appointments for detailed discussions
- Keep responses concise but complete
- Use appropriate tone for the communication channel
"""
    
    def _format_date(self, date_str: str) -> str:
        """Format date string for display"""
        try:
            from datetime import datetime
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            return date_obj.strftime("%A, %B %d, %Y")
        except:
            return date_str
    
    def _format_time(self, time_str: str) -> str:
        """Format time string for display"""
        try:
            from datetime import datetime
            time_obj = datetime.strptime(time_str, "%H:%M")
            return time_obj.strftime("%I:%M %p")
        except:
            return time_str
