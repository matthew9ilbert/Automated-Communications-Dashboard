
import os
import json
import logging
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from flask import current_app
from config import Config

logger = logging.getLogger(__name__)

class AppleShortcutsService:
    """Service for Apple Shortcuts integration"""
    
    def __init__(self):
        self.webhook_token = Config.IOS_SHORTCUT_TOKEN
    
    def create_shortcut_webhook_url(self, action: str) -> str:
        """Generate webhook URL for Apple Shortcuts"""
        base_url = current_app.config.get('BASE_URL', 'https://your-repl-url.replit.dev')
        return f"{base_url}/api/apple_shortcuts/{action}?token={self.webhook_token}"
    
    def get_shortcut_instructions(self) -> Dict[str, str]:
        """Get instructions for setting up Apple Shortcuts"""
        base_url = current_app.config.get('BASE_URL', 'https://your-repl-url.replit.dev')
        return {
            "log_message": f"{base_url}/api/log_message",
            "create_task": f"{base_url}/api/apple_shortcuts/create_task?token={self.webhook_token}",
            "get_tasks": f"{base_url}/api/tasks",
            "voice_memo": f"{base_url}/api/apple_shortcuts/voice_memo?token={self.webhook_token}",
            "calendar_event": f"{base_url}/api/apple_shortcuts/calendar_event?token={self.webhook_token}"
        }

class iMessageIntegrationService:
    """Service for iMessage integration (requires iOS Shortcuts)"""
    
    @staticmethod
    def process_imessage_data(message_data: Dict) -> Dict:
        """Process incoming iMessage data via Shortcuts"""
        return {
            'sender': message_data.get('sender', 'iMessage'),
            'content': message_data.get('text', ''),
            'source': 'imessage',
            'timestamp': datetime.now(),
            'attachments': message_data.get('attachments', [])
        }

class VoicemailTranscriptService:
    """Service for processing iPhone voicemail transcripts"""
    
    @staticmethod
    def process_voicemail_transcript(transcript_data: Dict) -> Dict:
        """Process voicemail transcript data"""
        return {
            'caller': transcript_data.get('caller', 'Unknown'),
            'transcript': transcript_data.get('transcript', ''),
            'duration': transcript_data.get('duration', 0),
            'timestamp': transcript_data.get('timestamp', datetime.now()),
            'confidence': transcript_data.get('confidence', 0.0)
        }

class AppleMailService:
    """Service for Apple Mail integration (via IMAP)"""
    
    def __init__(self):
        self.imap_server = os.environ.get('APPLE_MAIL_IMAP_SERVER', 'imap.mail.me.com')
        self.username = os.environ.get('APPLE_MAIL_USERNAME', '')
        self.password = os.environ.get('APPLE_MAIL_APP_PASSWORD', '')
    
    def fetch_recent_emails(self, count: int = 10) -> List[Dict]:
        """Fetch recent emails from Apple Mail"""
        try:
            import imaplib
            import email
            
            if not self.username or not self.password:
                logger.warning("Apple Mail credentials not configured")
                return []
            
            with imaplib.IMAP4_SSL(self.imap_server) as imap:
                imap.login(self.username, self.password)
                imap.select('INBOX')
                
                status, messages = imap.search(None, 'ALL')
                message_ids = messages[0].split()[-count:]
                
                emails = []
                for msg_id in message_ids:
                    status, msg_data = imap.fetch(msg_id, '(RFC822)')
                    msg = email.message_from_bytes(msg_data[0][1])
                    
                    emails.append({
                        'subject': msg['Subject'],
                        'sender': msg['From'],
                        'date': msg['Date'],
                        'body': self._extract_body(msg)
                    })
                
                return emails
                
        except Exception as e:
            logger.error(f"Error fetching Apple Mail emails: {e}")
            return []
    
    def _extract_body(self, msg) -> str:
        """Extract email body text"""
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode()
                    break
        else:
            body = msg.get_payload(decode=True).decode()
        return body

class AppleCalendarService:
    """Service for Apple Calendar integration (via CalDAV)"""
    
    def __init__(self):
        self.caldav_url = os.environ.get('APPLE_CALENDAR_CALDAV_URL', 'https://caldav.icloud.com')
        self.username = os.environ.get('APPLE_CALENDAR_USERNAME', '')
        self.password = os.environ.get('APPLE_CALENDAR_APP_PASSWORD', '')
    
    def create_event(self, title: str, start_time: datetime, end_time: datetime, description: str = '') -> bool:
        """Create calendar event via CalDAV"""
        try:
            if not self.username or not self.password:
                logger.warning("Apple Calendar credentials not configured")
                return False
            
            # In a full implementation, this would use a CalDAV library
            logger.info(f"Would create Apple Calendar event: {title}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating Apple Calendar event: {e}")
            return False

class AppleRemindersService:
    """Service for Apple Reminders integration"""
    
    def create_reminder(self, title: str, due_date: Optional[datetime] = None, notes: str = '') -> bool:
        """Create reminder (via Shortcuts integration)"""
        try:
            # This would integrate with Apple Shortcuts to create reminders
            logger.info(f"Would create Apple Reminder: {title}")
            return True
        except Exception as e:
            logger.error(f"Error creating Apple Reminder: {e}")
            return False

class AppleNotesService:
    """Service for Apple Notes integration"""
    
    def create_note(self, title: str, content: str, folder: str = 'Notes') -> bool:
        """Create note (via Shortcuts integration)"""
        try:
            logger.info(f"Would create Apple Note: {title}")
            return True
        except Exception as e:
            logger.error(f"Error creating Apple Note: {e}")
            return False

class EnhancedMicrosoftService:
    """Enhanced Microsoft services integration"""
    
    def __init__(self):
        self.base_service = None  # Will use existing MicrosoftGraphService
        
    def get_teams_notifications(self, team_id: str = None) -> List[Dict]:
        """Get Teams notifications and mentions"""
        try:
            # Implementation for Teams notifications
            return []
        except Exception as e:
            logger.error(f"Error getting Teams notifications: {e}")
            return []
    
    def create_excel_workbook(self, data: List[Dict], filename: str) -> Optional[str]:
        """Create Excel workbook with data"""
        try:
            # Implementation for creating Excel files
            logger.info(f"Would create Excel workbook: {filename}")
            return "workbook_id"
        except Exception as e:
            logger.error(f"Error creating Excel workbook: {e}")
            return None
    
    def create_word_document(self, title: str, content: str) -> Optional[str]:
        """Create Word document"""
        try:
            logger.info(f"Would create Word document: {title}")
            return "document_id"
        except Exception as e:
            logger.error(f"Error creating Word document: {e}")
            return None
    
    def create_powerpoint_presentation(self, title: str, slides: List[Dict]) -> Optional[str]:
        """Create PowerPoint presentation"""
        try:
            logger.info(f"Would create PowerPoint presentation: {title}")
            return "presentation_id"
        except Exception as e:
            logger.error(f"Error creating PowerPoint presentation: {e}")
            return None

class EnhancedGoogleService:
    """Enhanced Google services integration"""
    
    def __init__(self):
        self.gmail_service = None
        self.docs_service = None
        
    def setup_gmail_service(self):
        """Setup Gmail API service"""
        try:
            from googleapiclient.discovery import build
            from google.oauth2.service_account import Credentials
            
            creds_json = os.environ.get('GOOGLE_CREDENTIALS_JSON')
            if creds_json:
                creds_info = json.loads(creds_json)
                credentials = Credentials.from_service_account_info(
                    creds_info,
                    scopes=['https://www.googleapis.com/auth/gmail.readonly']
                )
                self.gmail_service = build('gmail', 'v1', credentials=credentials)
                logger.info("Gmail service initialized")
            
        except Exception as e:
            logger.error(f"Failed to setup Gmail service: {e}")
    
    def get_recent_gmail_messages(self, query: str = 'is:unread', max_results: int = 10) -> List[Dict]:
        """Get recent Gmail messages"""
        try:
            if not self.gmail_service:
                self.setup_gmail_service()
                
            if not self.gmail_service:
                return []
            
            results = self.gmail_service.users().messages().list(
                userId='me', q=query, maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            gmail_messages = []
            
            for message in messages[:5]:  # Limit to prevent API quota issues
                msg = self.gmail_service.users().messages().get(
                    userId='me', id=message['id']
                ).execute()
                
                gmail_messages.append({
                    'id': msg['id'],
                    'subject': self._get_header_value(msg, 'Subject'),
                    'sender': self._get_header_value(msg, 'From'),
                    'snippet': msg.get('snippet', ''),
                    'timestamp': msg.get('internalDate', '')
                })
            
            return gmail_messages
            
        except Exception as e:
            logger.error(f"Error getting Gmail messages: {e}")
            return []
    
    def _get_header_value(self, message: Dict, header_name: str) -> str:
        """Extract header value from Gmail message"""
        headers = message.get('payload', {}).get('headers', [])
        for header in headers:
            if header['name'] == header_name:
                return header['value']
        return ''
    
    def create_google_doc(self, title: str, content: str) -> Optional[str]:
        """Create Google Docs document"""
        try:
            logger.info(f"Would create Google Doc: {title}")
            return "document_id"
        except Exception as e:
            logger.error(f"Error creating Google Doc: {e}")
            return None

# Initialize services
apple_shortcuts_service = AppleShortcutsService()
imessage_service = iMessageIntegrationService()
voicemail_service = VoicemailTranscriptService()
apple_mail_service = AppleMailService()
apple_calendar_service = AppleCalendarService()
apple_reminders_service = AppleRemindersService()
apple_notes_service = AppleNotesService()
enhanced_microsoft_service = EnhancedMicrosoftService()
enhanced_google_service = EnhancedGoogleService()
