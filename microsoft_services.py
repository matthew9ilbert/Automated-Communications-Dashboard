import os
import logging
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from config import Config

logger = logging.getLogger(__name__)

class MicrosoftGraphService:
    """Service for Microsoft Graph API integration (Outlook/Teams)"""
    
    def __init__(self):
        self.access_token = None
        self.token_expires = None
        self._get_access_token()
    
    def _get_access_token(self):
        """Get access token for Microsoft Graph API"""
        try:
            if not all([Config.MICROSOFT_CLIENT_ID, Config.MICROSOFT_CLIENT_SECRET, Config.MICROSOFT_TENANT_ID]):
                logger.warning("Microsoft Graph credentials not configured")
                return
            
            url = f"https://login.microsoftonline.com/{Config.MICROSOFT_TENANT_ID}/oauth2/v2.0/token"
            
            data = {
                'client_id': Config.MICROSOFT_CLIENT_ID,
                'client_secret': Config.MICROSOFT_CLIENT_SECRET,
                'scope': 'https://graph.microsoft.com/.default',
                'grant_type': 'client_credentials'
            }
            
            response = requests.post(url, data=data)
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data['access_token']
                expires_in = token_data.get('expires_in', 3600)
                self.token_expires = datetime.now() + timedelta(seconds=expires_in - 300)  # 5 min buffer
                logger.info("Microsoft Graph access token obtained")
            else:
                logger.error(f"Failed to get Microsoft Graph token: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error getting Microsoft Graph token: {e}")
    
    def _ensure_valid_token(self):
        """Ensure we have a valid access token"""
        if not self.access_token or (self.token_expires and datetime.now() >= self.token_expires):
            self._get_access_token()
    
    def _make_graph_request(self, endpoint: str, method: str = 'GET', data: Dict = None) -> Optional[Dict]:
        """Make a request to Microsoft Graph API"""
        try:
            self._ensure_valid_token()
            
            if not self.access_token:
                logger.error("No valid Microsoft Graph token available")
                return None
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            url = f"https://graph.microsoft.com/v1.0{endpoint}"
            
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data)
            else:
                logger.error(f"Unsupported HTTP method: {method}")
                return None
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                logger.error(f"Microsoft Graph API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error making Microsoft Graph request: {e}")
            return None
    
    def get_recent_emails(self, user_id: str = 'me', max_results: int = 10) -> List[Dict]:
        """Get recent emails from Outlook"""
        try:
            endpoint = f"/users/{user_id}/messages"
            params = f"?$top={max_results}&$select=id,subject,bodyPreview,from,receivedDateTime&$orderby=receivedDateTime desc"
            
            result = self._make_graph_request(endpoint + params)
            
            if result and 'value' in result:
                return result['value']
            return []
            
        except Exception as e:
            logger.error(f"Error getting emails: {e}")
            return []
    
    def get_teams_messages(self, team_id: str = None) -> List[Dict]:
        """Get recent Teams messages (requires team access)"""
        try:
            if not team_id:
                logger.warning("No team ID provided for Teams messages")
                return []
            
            endpoint = f"/teams/{team_id}/channels"
            result = self._make_graph_request(endpoint)
            
            if result and 'value' in result:
                channels = result['value']
                messages = []
                
                for channel in channels[:3]:  # Limit to first 3 channels
                    channel_id = channel['id']
                    messages_endpoint = f"/teams/{team_id}/channels/{channel_id}/messages"
                    channel_messages = self._make_graph_request(messages_endpoint + "?$top=5")
                    
                    if channel_messages and 'value' in channel_messages:
                        messages.extend(channel_messages['value'])
                
                return messages
            return []
            
        except Exception as e:
            logger.error(f"Error getting Teams messages: {e}")
            return []
    
    def create_calendar_event(self, user_id: str, title: str, description: str, 
                            start_time: datetime, end_time: datetime, location: str = "") -> Optional[str]:
        """Create a calendar event in Outlook"""
        try:
            endpoint = f"/users/{user_id}/events"
            
            event_data = {
                "subject": title,
                "body": {
                    "contentType": "text",
                    "content": description
                },
                "start": {
                    "dateTime": start_time.isoformat(),
                    "timeZone": "Pacific Standard Time"
                },
                "end": {
                    "dateTime": end_time.isoformat(),
                    "timeZone": "Pacific Standard Time"
                },
                "location": {
                    "displayName": location
                }
            }
            
            result = self._make_graph_request(endpoint, 'POST', event_data)
            
            if result and 'id' in result:
                logger.info(f"Created Outlook calendar event: {title}")
                return result['id']
            return None
            
        except Exception as e:
            logger.error(f"Error creating Outlook event: {e}")
            return None
    
    def send_email(self, to_email: str, subject: str, body: str, user_id: str = 'me') -> bool:
        """Send an email via Outlook"""
        try:
            endpoint = f"/users/{user_id}/sendMail"
            
            email_data = {
                "message": {
                    "subject": subject,
                    "body": {
                        "contentType": "text",
                        "content": body
                    },
                    "toRecipients": [
                        {
                            "emailAddress": {
                                "address": to_email
                            }
                        }
                    ]
                }
            }
            
            result = self._make_graph_request(endpoint, 'POST', email_data)
            
            if result is not None:
                logger.info(f"Sent email to {to_email}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False

# Initialize service
graph_service = MicrosoftGraphService()
