import os
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from config import Config

logger = logging.getLogger(__name__)

class GoogleSheetsService:
    """Service for Google Sheets integration"""
    
    def __init__(self):
        self.credentials = None
        self.gc = None
        self.sheet = None
        self._initialize_credentials()
    
    def _initialize_credentials(self):
        """Initialize Google Sheets credentials"""
        try:
            # Try to get credentials from environment variable (JSON string)
            creds_json = os.environ.get('GOOGLE_CREDENTIALS_JSON')
            if creds_json:
                creds_info = json.loads(creds_json)
                self.credentials = Credentials.from_service_account_info(
                    creds_info,
                    scopes=['https://www.googleapis.com/auth/spreadsheets',
                           'https://www.googleapis.com/auth/drive']
                )
            else:
                # Try to load from file
                creds_file = Config.GOOGLE_CREDENTIALS_FILE
                if os.path.exists(creds_file):
                    self.credentials = Credentials.from_service_account_file(
                        creds_file,
                        scopes=['https://www.googleapis.com/auth/spreadsheets',
                               'https://www.googleapis.com/auth/drive']
                    )
            
            if self.credentials:
                self.gc = gspread.authorize(self.credentials)
                if Config.GOOGLE_SHEETS_ID:
                    self.sheet = self.gc.open_by_key(Config.GOOGLE_SHEETS_ID)
                else:
                    logger.warning("No Google Sheets ID configured")
            else:
                logger.warning("No Google credentials found")
                
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets: {e}")
    
    def log_message(self, sender: str, content: str, source: str, priority: str) -> bool:
        """Log a message to Google Sheets"""
        try:
            if not self.sheet:
                logger.error("Google Sheets not initialized")
                return False
            
            # Get or create the messages worksheet
            try:
                worksheet = self.sheet.worksheet("Messages")
            except gspread.WorksheetNotFound:
                worksheet = self.sheet.add_worksheet(title="Messages", rows="1000", cols="6")
                # Add headers
                worksheet.append_row(["Timestamp", "Sender", "Content", "Source", "Priority", "Processed"])
            
            # Add the message
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            worksheet.append_row([timestamp, sender, content, source, priority, "No"])
            
            logger.info(f"Logged message from {sender} to Google Sheets")
            return True
            
        except Exception as e:
            logger.error(f"Failed to log message to Google Sheets: {e}")
            return False
    
    def log_task(self, title: str, description: str, facility: str, priority: str, assigned_to: str = "") -> bool:
        """Log a task to Google Sheets"""
        try:
            if not self.sheet:
                return False
            
            try:
                worksheet = self.sheet.worksheet("Tasks")
            except gspread.WorksheetNotFound:
                worksheet = self.sheet.add_worksheet(title="Tasks", rows="1000", cols="8")
                worksheet.append_row(["Timestamp", "Title", "Description", "Facility", "Priority", "Assigned To", "Status", "Due Date"])
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            worksheet.append_row([timestamp, title, description, facility, priority, assigned_to, "Not Started", ""])
            
            logger.info(f"Logged task '{title}' to Google Sheets")
            return True
            
        except Exception as e:
            logger.error(f"Failed to log task to Google Sheets: {e}")
            return False
    
    def get_tasks(self) -> List[Dict]:
        """Retrieve tasks from Google Sheets"""
        try:
            if not self.sheet:
                return []
            
            worksheet = self.sheet.worksheet("Tasks")
            records = worksheet.get_all_records()
            return records
            
        except Exception as e:
            logger.error(f"Failed to get tasks from Google Sheets: {e}")
            return []

class GoogleCalendarService:
    """Service for Google Calendar integration"""
    
    def __init__(self):
        self.service = None
        self._initialize_service()
    
    def _initialize_service(self):
        """Initialize Google Calendar service"""
        try:
            creds_json = os.environ.get('GOOGLE_CREDENTIALS_JSON')
            if creds_json:
                creds_info = json.loads(creds_json)
                credentials = Credentials.from_service_account_info(
                    creds_info,
                    scopes=['https://www.googleapis.com/auth/calendar']
                )
            else:
                creds_file = Config.GOOGLE_CREDENTIALS_FILE
                if os.path.exists(creds_file):
                    credentials = Credentials.from_service_account_file(
                        creds_file,
                        scopes=['https://www.googleapis.com/auth/calendar']
                    )
                else:
                    logger.warning("No Google credentials found for Calendar")
                    return
            
            self.service = build('calendar', 'v3', credentials=credentials)
            logger.info("Google Calendar service initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize Google Calendar: {e}")
    
    def create_event(self, title: str, description: str, start_time: datetime, 
                    end_time: datetime, location: str = "") -> Optional[str]:
        """Create a calendar event"""
        try:
            if not self.service:
                logger.error("Google Calendar service not initialized")
                return None
            
            event = {
                'summary': title,
                'description': description,
                'location': location,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'America/Los_Angeles',  # Pacific Time for Kaiser Permanente WA
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'America/Los_Angeles',
                },
            }
            
            event_result = self.service.events().insert(
                calendarId=Config.GOOGLE_CALENDAR_ID,
                body=event
            ).execute()
            
            logger.info(f"Created calendar event: {title}")
            return event_result.get('id')
            
        except HttpError as e:
            logger.error(f"Failed to create calendar event: {e}")
            return None
    
    def get_upcoming_events(self, max_results: int = 10) -> List[Dict]:
        """Get upcoming events from calendar"""
        try:
            if not self.service:
                return []
            
            now = datetime.utcnow().isoformat() + 'Z'
            events_result = self.service.events().list(
                calendarId=Config.GOOGLE_CALENDAR_ID,
                timeMin=now,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            return events
            
        except HttpError as e:
            logger.error(f"Failed to get calendar events: {e}")
            return []

# Initialize services
sheets_service = GoogleSheetsService()
calendar_service = GoogleCalendarService()
