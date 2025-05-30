import os
from datetime import timedelta

class Config:
    """Application configuration settings"""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SESSION_SECRET', 'evs-manager-secret-key-2024')
    DEBUG = True
    
    # Database settings
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///evs_manager.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    
    # Google API settings
    GOOGLE_CREDENTIALS_FILE = os.environ.get('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
    GOOGLE_SHEETS_ID = os.environ.get('GOOGLE_SHEETS_ID', '')
    GOOGLE_CALENDAR_ID = os.environ.get('GOOGLE_CALENDAR_ID', 'primary')
    
    # Microsoft Graph API settings
    MICROSOFT_CLIENT_ID = os.environ.get('MICROSOFT_CLIENT_ID', '')
    MICROSOFT_CLIENT_SECRET = os.environ.get('MICROSOFT_CLIENT_SECRET', '')
    MICROSOFT_TENANT_ID = os.environ.get('MICROSOFT_TENANT_ID', '')
    
    # iOS Shortcut integration
    IOS_SHORTCUT_TOKEN = os.environ.get('IOS_SHORTCUT_TOKEN', 'a1561b33-9322-4749-a93c-9265a90905da')
    
    # Message scanning settings
    SCAN_INTERVAL_MINUTES = 15
    REMINDER_INTERVAL_MINUTES = 30
    
    # Facilities configuration
    FACILITIES = [
        'Bellevue Medical Center',
        'Clinic A',
        'Clinic B', 
        'Clinic C',
        'Clinic D'
    ]
    
    # Priority keywords for message scanning
    HIGH_PRIORITY_KEYWORDS = [
        'urgent', 'asap', 'emergency', 'critical', 'immediate',
        'stat', 'priority', 'rush', 'now', 'today'
    ]
    
    MEDIUM_PRIORITY_KEYWORDS = [
        'soon', 'tomorrow', 'schedule', 'meeting', 'appointment',
        'follow up', 'followup', 'review', 'check'
    ]
