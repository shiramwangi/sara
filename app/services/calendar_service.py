"""
Google Calendar Integration Service
"""

import logging
import structlog
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from google.oauth2.credentials import Credentials
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os
import json

from app.config import settings
from app.models import AppointmentSlot, ContactInfo, CalendarEvent

logger = structlog.get_logger()

# Google Calendar API scopes
SCOPES = ['https://www.googleapis.com/auth/calendar']


class CalendarService:
    """Service for Google Calendar integration"""
    
    def __init__(self):
        self.service = None
        self.calendar_id = settings.google_calendar_id
        # In debug mode, skip external auth to avoid network/browser interaction
        if not settings.debug:
            self._authenticate()
        else:
            logger.info("DEBUG mode: Skipping Google Calendar authentication (simulated)")
    
    def _authenticate(self):
        """Authenticate with Google Calendar API"""
        try:
            creds = None
            
            # Prefer service account if provided (server-friendly)
            if settings.google_service_account_file or settings.google_service_account_info:
                try:
                    if settings.google_service_account_info:
                        service_account_info = json.loads(settings.google_service_account_info)
                        creds = ServiceAccountCredentials.from_service_account_info(
                            service_account_info,
                            scopes=SCOPES
                        )
                    else:
                        creds = ServiceAccountCredentials.from_service_account_file(
                            settings.google_service_account_file,
                            scopes=SCOPES
                        )
                    # Optional domain-wide delegation / user impersonation
                    if settings.google_calendar_delegated_user:
                        creds = creds.with_subject(settings.google_calendar_delegated_user)
                    logger.info("Google Calendar authenticated via service account")
                except Exception as e:
                    logger.error("Service account auth failed, falling back to OAuth client flow", error=str(e))
                    creds = None

            if creds is None:
                token_file = 'token.json'
                # Load existing user credentials
                if os.path.exists(token_file):
                    creds = Credentials.from_authorized_user_file(token_file, SCOPES)
                
                # If no valid credentials, run OAuth client flow (interactive; not for production pods)
                if not creds or not creds.valid:
                    if creds and creds.expired and creds.refresh_token:
                        creds.refresh(Request())
                    else:
                        flow = InstalledAppFlow.from_client_secrets_file(
                            settings.google_calendar_credentials_file, SCOPES)
                        # Note: This opens a local server; use only for local/dev
                        creds = flow.run_local_server(port=0)
                    # Save credentials for next run
                    with open(token_file, 'w') as token:
                        token.write(creds.to_json())

            self.service = build('calendar', 'v3', credentials=creds)
            logger.info("Google Calendar authentication successful")
            
        except Exception as e:
            logger.error("Google Calendar authentication failed", error=str(e))
            raise
    
    async def create_appointment(
        self,
        appointment: AppointmentSlot,
        contact_info: Optional[ContactInfo] = None,
        description: str = ""
    ) -> str:
        """
        Create a new appointment in Google Calendar
        """
        try:
            if settings.debug:
                fake_id = f"debug_event_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                logger.info("DEBUG mode: Simulating calendar event creation", event_id=fake_id)
                return fake_id
            if not self.service:
                raise Exception("Google Calendar service not initialized")
            
            # Parse appointment date and time
            start_datetime = self._parse_appointment_datetime(appointment)
            end_datetime = start_datetime + timedelta(hours=1)  # Default 1-hour appointment
            
            # Create event
            event = {
                'summary': f"Appointment with {contact_info.name if contact_info and contact_info.name else 'Client'}",
                'description': self._build_event_description(contact_info, description),
                'start': {
                    'dateTime': start_datetime.isoformat(),
                    'timeZone': appointment.timezone,
                },
                'end': {
                    'dateTime': end_datetime.isoformat(),
                    'timeZone': appointment.timezone,
                },
                'attendees': self._build_attendees(contact_info),
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},  # 1 day before
                        {'method': 'popup', 'minutes': 30},       # 30 minutes before
                    ],
                },
                'conferenceData': {
                    'createRequest': {
                        'requestId': f"appointment_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        'conferenceSolutionKey': {
                            'type': 'hangoutsMeet'
                        }
                    }
                }
            }
            
            # Create the event
            created_event = self.service.events().insert(
                calendarId=self.calendar_id,
                body=event,
                conferenceDataVersion=1
            ).execute()
            
            event_id = created_event['id']
            logger.info("Calendar event created", event_id=event_id, start_time=start_datetime)
            
            return event_id
            
        except HttpError as e:
            logger.error("Google Calendar API error", error=str(e))
            raise Exception(f"Failed to create calendar event: {e}")
        except Exception as e:
            logger.error("Error creating appointment", error=str(e))
            raise
    
    async def check_availability(
        self,
        appointment: AppointmentSlot,
        duration_minutes: int = 60
    ) -> bool:
        """
        Check if the requested time slot is available
        """
        try:
            if settings.debug:
                logger.info("DEBUG mode: Simulating availability check", available=True)
                return True
            if not self.service:
                raise Exception("Google Calendar service not initialized")
            
            start_datetime = self._parse_appointment_datetime(appointment)
            end_datetime = start_datetime + timedelta(minutes=duration_minutes)
            
            # Check for conflicts
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=start_datetime.isoformat() + 'Z',
                timeMax=end_datetime.isoformat() + 'Z',
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Filter out declined events
            conflicting_events = [
                event for event in events
                if event.get('status') != 'cancelled'
                and not self._is_event_declined(event)
            ]
            
            is_available = len(conflicting_events) == 0
            
            logger.info(
                "Availability checked",
                start_time=start_datetime,
                duration_minutes=duration_minutes,
                is_available=is_available,
                conflicting_events=len(conflicting_events)
            )
            
            return is_available
            
        except Exception as e:
            logger.error("Error checking availability", error=str(e))
            return False
    
    async def get_available_slots(
        self,
        date: str,
        duration_minutes: int = 60,
        start_hour: int = 9,
        end_hour: int = 17
    ) -> List[str]:
        """
        Get available time slots for a given date
        """
        try:
            if settings.debug:
                logger.info("DEBUG mode: Simulating available slots", date=date)
                return ["09:00", "09:30", "10:00", "14:00", "14:30"]
            if not self.service:
                raise Exception("Google Calendar service not initialized")
            
            # Parse date
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            start_datetime = date_obj.replace(hour=start_hour, minute=0, second=0)
            end_datetime = date_obj.replace(hour=end_hour, minute=0, second=0)
            
            # Get existing events for the day
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=start_datetime.isoformat() + 'Z',
                timeMax=end_datetime.isoformat() + 'Z',
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Generate available slots
            available_slots = []
            current_time = start_datetime
            
            while current_time + timedelta(minutes=duration_minutes) <= end_datetime:
                slot_end = current_time + timedelta(minutes=duration_minutes)
                
                # Check if this slot conflicts with any events
                has_conflict = False
                for event in events:
                    if event.get('status') == 'cancelled' or self._is_event_declined(event):
                        continue
                    
                    event_start = datetime.fromisoformat(event['start']['dateTime'].replace('Z', '+00:00'))
                    event_end = datetime.fromisoformat(event['end']['dateTime'].replace('Z', '+00:00'))
                    
                    if (current_time < event_end and slot_end > event_start):
                        has_conflict = True
                        break
                
                if not has_conflict:
                    available_slots.append(current_time.strftime("%H:%M"))
                
                current_time += timedelta(minutes=30)  # Check every 30 minutes
            
            logger.info("Available slots generated", date=date, slots_count=len(available_slots))
            return available_slots
            
        except Exception as e:
            logger.error("Error getting available slots", error=str(e))
            return []
    
    async def cancel_appointment(self, event_id: str) -> bool:
        """
        Cancel an appointment
        """
        try:
            if settings.debug:
                logger.info("DEBUG mode: Simulating appointment cancellation", event_id=event_id)
                return True
            if not self.service:
                raise Exception("Google Calendar service not initialized")
            
            self.service.events().delete(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            
            logger.info("Appointment cancelled", event_id=event_id)
            return True
            
        except HttpError as e:
            if e.resp.status == 404:
                logger.warning("Event not found for cancellation", event_id=event_id)
                return True  # Consider it cancelled if not found
            logger.error("Error cancelling appointment", event_id=event_id, error=str(e))
            return False
        except Exception as e:
            logger.error("Error cancelling appointment", event_id=event_id, error=str(e))
            return False
    
    async def update_appointment(
        self,
        event_id: str,
        new_appointment: AppointmentSlot,
        contact_info: Optional[ContactInfo] = None
    ) -> bool:
        """
        Update an existing appointment
        """
        try:
            if settings.debug:
                logger.info("DEBUG mode: Simulating appointment update", event_id=event_id)
                return True
            if not self.service:
                raise Exception("Google Calendar service not initialized")
            
            # Get existing event
            event = self.service.events().get(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            
            # Update event details
            start_datetime = self._parse_appointment_datetime(new_appointment)
            end_datetime = start_datetime + timedelta(hours=1)
            
            event['summary'] = f"Appointment with {contact_info.name if contact_info and contact_info.name else 'Client'}"
            event['start']['dateTime'] = start_datetime.isoformat()
            event['end']['dateTime'] = end_datetime.isoformat()
            event['attendees'] = self._build_attendees(contact_info)
            
            # Update the event
            updated_event = self.service.events().update(
                calendarId=self.calendar_id,
                eventId=event_id,
                body=event
            ).execute()
            
            logger.info("Appointment updated", event_id=event_id, new_start_time=start_datetime)
            return True
            
        except Exception as e:
            logger.error("Error updating appointment", event_id=event_id, error=str(e))
            return False
    
    def _parse_appointment_datetime(self, appointment: AppointmentSlot) -> datetime:
        """Parse appointment date and time into datetime object"""
        try:
            date_str = appointment.date
            time_str = appointment.time
            
            # Combine date and time
            datetime_str = f"{date_str} {time_str}"
            dt = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
            
            return dt
        except Exception as e:
            logger.error("Error parsing appointment datetime", error=str(e))
            raise ValueError(f"Invalid appointment datetime: {appointment.date} {appointment.time}")
    
    def _build_event_description(
        self,
        contact_info: Optional[ContactInfo],
        additional_description: str = ""
    ) -> str:
        """Build event description with contact information"""
        description_parts = []
        
        if contact_info:
            if contact_info.name:
                description_parts.append(f"Client: {contact_info.name}")
            if contact_info.email:
                description_parts.append(f"Email: {contact_info.email}")
            if contact_info.phone:
                description_parts.append(f"Phone: {contact_info.phone}")
        
        if additional_description:
            description_parts.append(f"Notes: {additional_description}")
        
        description_parts.append("Scheduled via Sara AI Receptionist")
        
        return "\n".join(description_parts)
    
    def _build_attendees(self, contact_info: Optional[ContactInfo]) -> List[Dict[str, str]]:
        """Build attendees list for calendar event"""
        attendees = []
        
        if contact_info and contact_info.email:
            attendees.append({
                'email': contact_info.email,
                'displayName': contact_info.name or 'Client',
                'responseStatus': 'needsAction'
            })
        
        return attendees
    
    def _is_event_declined(self, event: Dict[str, Any]) -> bool:
        """Check if an event is declined by the attendee"""
        attendees = event.get('attendees', [])
        for attendee in attendees:
            if attendee.get('responseStatus') == 'declined':
                return True
        return False
