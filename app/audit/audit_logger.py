"""
Audit logging system for compliance and monitoring
"""

import json
import logging
import structlog
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum

logger = structlog.get_logger()


class AuditEventType(str, Enum):
    """Types of audit events"""
    INTERACTION_STARTED = "interaction_started"
    INTERACTION_COMPLETED = "interaction_completed"
    INTERACTION_FAILED = "interaction_failed"
    INTENT_EXTRACTED = "intent_extracted"
    CALENDAR_EVENT_CREATED = "calendar_event_created"
    CALENDAR_EVENT_CANCELLED = "calendar_event_cancelled"
    MESSAGE_SENT = "message_sent"
    FAQ_ACCESSED = "faq_accessed"
    ERROR_OCCURRED = "error_occurred"
    SECURITY_EVENT = "security_event"


class AuditLogger:
    """Centralized audit logging system"""
    
    def __init__(self):
        self.logger = structlog.get_logger("audit")
    
    def log_interaction_started(
        self,
        call_id: str,
        channel: str,
        user_input: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log when an interaction starts"""
        self._log_event(
            event_type=AuditEventType.INTERACTION_STARTED,
            call_id=call_id,
            data={
                "channel": channel,
                "user_input": user_input,
                "metadata": metadata or {}
            }
        )
    
    def log_interaction_completed(
        self,
        call_id: str,
        intent: str,
        confidence: float,
        response: str,
        processing_time_ms: int,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log when an interaction completes successfully"""
        self._log_event(
            event_type=AuditEventType.INTERACTION_COMPLETED,
            call_id=call_id,
            data={
                "intent": intent,
                "confidence": confidence,
                "response": response,
                "processing_time_ms": processing_time_ms,
                "metadata": metadata or {}
            }
        )
    
    def log_interaction_failed(
        self,
        call_id: str,
        error: str,
        processing_time_ms: int,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log when an interaction fails"""
        self._log_event(
            event_type=AuditEventType.INTERACTION_FAILED,
            call_id=call_id,
            data={
                "error": error,
                "processing_time_ms": processing_time_ms,
                "metadata": metadata or {}
            }
        )
    
    def log_intent_extracted(
        self,
        call_id: str,
        intent: str,
        confidence: float,
        slots: Dict[str, Any],
        contact_info: Optional[Dict[str, str]] = None
    ):
        """Log intent extraction results"""
        self._log_event(
            event_type=AuditEventType.INTENT_EXTRACTED,
            call_id=call_id,
            data={
                "intent": intent,
                "confidence": confidence,
                "slots": slots,
                "contact_info": contact_info or {}
            }
        )
    
    def log_calendar_event_created(
        self,
        call_id: str,
        event_id: str,
        appointment_date: str,
        appointment_time: str,
        contact_name: Optional[str] = None
    ):
        """Log calendar event creation"""
        self._log_event(
            event_type=AuditEventType.CALENDAR_EVENT_CREATED,
            call_id=call_id,
            data={
                "event_id": event_id,
                "appointment_date": appointment_date,
                "appointment_time": appointment_time,
                "contact_name": contact_name
            }
        )
    
    def log_calendar_event_cancelled(
        self,
        call_id: str,
        event_id: str,
        reason: Optional[str] = None
    ):
        """Log calendar event cancellation"""
        self._log_event(
            event_type=AuditEventType.CALENDAR_EVENT_CANCELLED,
            call_id=call_id,
            data={
                "event_id": event_id,
                "reason": reason
            }
        )
    
    def log_message_sent(
        self,
        call_id: str,
        channel: str,
        to_number: str,
        message: str,
        success: bool
    ):
        """Log message sending"""
        self._log_event(
            event_type=AuditEventType.MESSAGE_SENT,
            call_id=call_id,
            data={
                "channel": channel,
                "to_number": to_number,
                "message": message,
                "success": success
            }
        )
    
    def log_faq_accessed(
        self,
        call_id: str,
        question: str,
        answer: str,
        faq_id: Optional[int] = None
    ):
        """Log FAQ access"""
        self._log_event(
            event_type=AuditEventType.FAQ_ACCESSED,
            call_id=call_id,
            data={
                "question": question,
                "answer": answer,
                "faq_id": faq_id
            }
        )
    
    def log_error(
        self,
        call_id: str,
        error_type: str,
        error_message: str,
        stack_trace: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """Log error events"""
        self._log_event(
            event_type=AuditEventType.ERROR_OCCURRED,
            call_id=call_id,
            data={
                "error_type": error_type,
                "error_message": error_message,
                "stack_trace": stack_trace,
                "context": context or {}
            }
        )
    
    def log_security_event(
        self,
        event_type: str,
        description: str,
        severity: str = "medium",
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log security events"""
        self._log_event(
            event_type=AuditEventType.SECURITY_EVENT,
            call_id="security",
            data={
                "security_event_type": event_type,
                "description": description,
                "severity": severity,
                "client_ip": client_ip,
                "user_agent": user_agent,
                "metadata": metadata or {}
            }
        )
    
    def _log_event(
        self,
        event_type: AuditEventType,
        call_id: str,
        data: Dict[str, Any]
    ):
        """Log an audit event"""
        try:
            audit_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "event_type": event_type.value,
                "call_id": call_id,
                "data": data
            }
            
            # Log to structured logger
            self.logger.info(
                "audit_event",
                **audit_entry
            )
            
            # In production, also send to external audit system
            # self._send_to_audit_system(audit_entry)
            
        except Exception as e:
            # Don't let audit logging break the main flow
            logger.error("Failed to log audit event", error=str(e))
    
    def _send_to_audit_system(self, audit_entry: Dict[str, Any]):
        """Send audit entry to external audit system (e.g., SIEM)"""
        # Implementation would depend on the specific audit system
        # This could be sending to Splunk, ELK, or another SIEM
        pass


# Global audit logger instance
audit_logger = AuditLogger()
