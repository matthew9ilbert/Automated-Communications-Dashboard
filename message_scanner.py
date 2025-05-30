import logging
import re
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from models import Message, Task, CalendarEvent, db
from google_services import sheets_service
from microsoft_services import graph_service
from config import Config

logger = logging.getLogger(__name__)

class MessageScanner:
    """Service for scanning and processing messages"""
    
    def __init__(self):
        self.high_priority_keywords = [keyword.lower() for keyword in Config.HIGH_PRIORITY_KEYWORDS]
        self.medium_priority_keywords = [keyword.lower() for keyword in Config.MEDIUM_PRIORITY_KEYWORDS]
    
    def determine_priority(self, content: str) -> str:
        """Determine message priority based on keywords"""
        content_lower = content.lower()
        
        # Check for high priority keywords
        for keyword in self.high_priority_keywords:
            if keyword in content_lower:
                return 'High'
        
        # Check for medium priority keywords
        for keyword in self.medium_priority_keywords:
            if keyword in content_lower:
                return 'Medium'
        
        return 'Low'
    
    def extract_datetime_info(self, content: str) -> Optional[datetime]:
        """Extract datetime information from message content"""
        try:
            # Common date/time patterns
            patterns = [
                r'(\d{1,2})/(\d{1,2})/(\d{4})\s+(\d{1,2}):(\d{2})\s*(AM|PM)?',  # MM/DD/YYYY HH:MM AM/PM
                r'(\d{1,2})-(\d{1,2})-(\d{4})\s+(\d{1,2}):(\d{2})',  # MM-DD-YYYY HH:MM
                r'(today|tomorrow)\s+(\d{1,2}):(\d{2})\s*(AM|PM)?',  # today/tomorrow HH:MM
                r'(\d{1,2}):(\d{2})\s*(AM|PM)',  # HH:MM AM/PM (assumes today)
            ]
            
            content_lower = content.lower()
            
            for pattern in patterns:
                match = re.search(pattern, content_lower)
                if match:
                    try:
                        groups = match.groups()
                        
                        if 'today' in groups[0] if groups else False:
                            date_part = datetime.now().date()
                            hour = int(groups[1])
                            minute = int(groups[2])
                            if len(groups) > 3 and groups[3] and 'pm' in groups[3].lower() and hour != 12:
                                hour += 12
                            elif len(groups) > 3 and groups[3] and 'am' in groups[3].lower() and hour == 12:
                                hour = 0
                            return datetime.combine(date_part, datetime.min.time().replace(hour=hour, minute=minute))
                        
                        elif 'tomorrow' in groups[0] if groups else False:
                            date_part = (datetime.now() + timedelta(days=1)).date()
                            hour = int(groups[1])
                            minute = int(groups[2])
                            if len(groups) > 3 and groups[3] and 'pm' in groups[3].lower() and hour != 12:
                                hour += 12
                            elif len(groups) > 3 and groups[3] and 'am' in groups[3].lower() and hour == 12:
                                hour = 0
                            return datetime.combine(date_part, datetime.min.time().replace(hour=hour, minute=minute))
                        
                        elif len(groups) >= 5:  # Full date pattern
                            month, day, year = int(groups[0]), int(groups[1]), int(groups[2])
                            hour, minute = int(groups[3]), int(groups[4])
                            if len(groups) > 5 and groups[5] and 'pm' in groups[5].lower() and hour != 12:
                                hour += 12
                            elif len(groups) > 5 and groups[5] and 'am' in groups[5].lower() and hour == 12:
                                hour = 0
                            return datetime(year, month, day, hour, minute)
                        
                        elif len(groups) >= 2:  # Time only pattern
                            hour = int(groups[0])
                            minute = int(groups[1])
                            if len(groups) > 2 and groups[2] and 'pm' in groups[2].lower() and hour != 12:
                                hour += 12
                            elif len(groups) > 2 and groups[2] and 'am' in groups[2].lower() and hour == 12:
                                hour = 0
                            today = datetime.now().date()
                            return datetime.combine(today, datetime.min.time().replace(hour=hour, minute=minute))
                    
                    except (ValueError, IndexError):
                        continue
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting datetime from content: {e}")
            return None
    
    def extract_facility_info(self, content: str) -> str:
        """Extract facility information from message content"""
        content_lower = content.lower()
        
        for facility in Config.FACILITIES:
            if facility.lower() in content_lower:
                return facility
        
        # Look for common facility indicators
        facility_keywords = {
            'bellevue': 'Bellevue Medical Center',
            'clinic a': 'Clinic A',
            'clinic b': 'Clinic B', 
            'clinic c': 'Clinic C',
            'clinic d': 'Clinic D',
            'main': 'Bellevue Medical Center'
        }
        
        for keyword, facility in facility_keywords.items():
            if keyword in content_lower:
                return facility
        
        return 'Bellevue Medical Center'  # Default facility
    
    def is_task_related(self, content: str) -> bool:
        """Determine if message content indicates a task"""
        task_indicators = [
            'need', 'needs', 'required', 'please', 'can you', 'could you',
            'assign', 'schedule', 'clean', 'cleaning', 'maintenance',
            'repair', 'fix', 'check', 'inspection', 'audit', 'coverage',
            'staff', 'help', 'assist', 'complete', 'finish', 'do'
        ]
        
        content_lower = content.lower()
        return any(indicator in content_lower for indicator in task_indicators)
    
    def is_event_related(self, content: str) -> bool:
        """Determine if message content indicates a calendar event"""
        event_indicators = [
            'meeting', 'appointment', 'schedule', 'audit', 'inspection',
            'training', 'conference', 'call', 'visit', 'at', 'on',
            'deadline', 'due', 'reminder'
        ]
        
        content_lower = content.lower()
        return any(indicator in content_lower for indicator in event_indicators)
    
    def process_message(self, message: Message) -> Dict[str, any]:
        """Process a message and determine appropriate actions"""
        try:
            result = {
                'message_id': message.id,
                'actions': [],
                'suggestions': []
            }
            
            # Check if it's task-related
            if self.is_task_related(message.content):
                task_title = self._extract_task_title(message.content)
                facility = self.extract_facility_info(message.content)
                
                result['actions'].append({
                    'type': 'task',
                    'title': task_title,
                    'description': message.content[:200] + '...' if len(message.content) > 200 else message.content,
                    'facility': facility,
                    'priority': message.priority
                })
            
            # Check if it's event-related
            if self.is_event_related(message.content):
                event_time = self.extract_datetime_info(message.content)
                if event_time:
                    event_title = self._extract_event_title(message.content)
                    location = self.extract_facility_info(message.content)
                    
                    result['actions'].append({
                        'type': 'event',
                        'title': event_title,
                        'description': message.content[:200] + '...' if len(message.content) > 200 else message.content,
                        'start_time': event_time,
                        'end_time': event_time + timedelta(hours=1),  # Default 1 hour duration
                        'location': location
                    })
            
            # Add suggestions based on content analysis
            if message.priority == 'High':
                result['suggestions'].append('Consider immediate response required')
            
            if any(keyword in message.content.lower() for keyword in ['coverage', 'staff', 'assign']):
                result['suggestions'].append('May require staff assignment')
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing message {message.id}: {e}")
            return {'message_id': message.id, 'actions': [], 'suggestions': []}
    
    def _extract_task_title(self, content: str) -> str:
        """Extract a meaningful task title from content"""
        # Split content into sentences and find the most relevant one
        sentences = re.split(r'[.!?]+', content)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if any(word in sentence.lower() for word in ['need', 'clean', 'fix', 'check', 'repair']):
                return sentence[:100] + '...' if len(sentence) > 100 else sentence
        
        # Fallback: use first sentence or truncated content
        first_sentence = sentences[0].strip() if sentences else content
        return first_sentence[:100] + '...' if len(first_sentence) > 100 else first_sentence
    
    def _extract_event_title(self, content: str) -> str:
        """Extract a meaningful event title from content"""
        # Look for meeting/event related phrases
        patterns = [
            r'(meeting|appointment|audit|inspection|training|conference).{0,50}',
            r'(schedule|plan).{0,30}(meeting|appointment|audit|inspection)',
        ]
        
        content_lower = content.lower()
        for pattern in patterns:
            match = re.search(pattern, content_lower)
            if match:
                return match.group(0).strip().title()
        
        # Fallback: use first part of content
        first_part = content.split('.')[0].strip()
        return first_part[:100] + '...' if len(first_part) > 100 else first_part
    
    def scan_incoming_messages(self) -> List[Dict]:
        """Scan for new incoming messages from various sources"""
        results = []
        
        try:
            # Scan emails from Microsoft Graph
            emails = graph_service.get_recent_emails(max_results=5)
            for email in emails:
                # Check if we've already processed this email
                existing = Message.query.filter_by(
                    source='email',
                    content=email.get('bodyPreview', '')[:500]
                ).first()
                
                if not existing:
                    sender = email.get('from', {}).get('emailAddress', {}).get('address', 'Unknown')
                    content = email.get('bodyPreview', '')
                    priority = self.determine_priority(content)
                    
                    # Create message record
                    message = Message(
                        sender=sender,
                        content=content,
                        source='email',
                        priority=priority
                    )
                    db.session.add(message)
                    db.session.commit()
                    
                    # Log to Google Sheets
                    sheets_service.log_message(sender, content, 'email', priority)
                    
                    # Process for actions
                    processing_result = self.process_message(message)
                    results.append(processing_result)
            
            # Note: Teams messages would require additional configuration and permissions
            # This is a placeholder for when those are available
            
            logger.info(f"Scanned and processed {len(results)} new messages")
            return results
            
        except Exception as e:
            logger.error(f"Error scanning incoming messages: {e}")
            return results

# Initialize scanner
message_scanner = MessageScanner()
