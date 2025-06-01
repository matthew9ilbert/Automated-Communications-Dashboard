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
    
    # Apple Mail/Calendar integration (requires app-specific passwords)
    APPLE_MAIL_USERNAME = os.environ.get('APPLE_MAIL_USERNAME', '')
    APPLE_MAIL_APP_PASSWORD = os.environ.get('APPLE_MAIL_APP_PASSWORD', '')
    APPLE_CALENDAR_USERNAME = os.environ.get('APPLE_CALENDAR_USERNAME', '')
    APPLE_CALENDAR_APP_PASSWORD = os.environ.get('APPLE_CALENDAR_APP_PASSWORD', '')
    
    # Application base URL for webhooks
    BASE_URL = os.environ.get('BASE_URL', 'https://your-repl-url.replit.dev')
    
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
    
    @classmethod
    def validate_config(cls):
        """Validate configuration settings"""
        errors = []
        warnings = []
        
        # Check database URL
        if not cls.SQLALCHEMY_DATABASE_URI:
            errors.append("SQLALCHEMY_DATABASE_URI is not configured")
        
        # Check secret key
        if not cls.SECRET_KEY or cls.SECRET_KEY == 'dev-secret-key':
            warnings.append("SECRET_KEY should be changed from default in production")
        
        # Check iOS shortcut token
        if not cls.IOS_SHORTCUT_TOKEN:
            warnings.append("IOS_SHORTCUT_TOKEN is not configured - API endpoints will not work")
        
        # Check facilities configuration
        if not cls.FACILITIES:
            warnings.append("No facilities configured")
        
        # Print validation results
        if errors:
            print("Configuration ERRORS:")
            for error in errors:
                print(f"  - {error}")
        
        if warnings:
            print("Configuration WARNINGS:")
            for warning in warnings:
                print(f"  - {warning}")
        
        return len(errors) == 0, errors, warnings
