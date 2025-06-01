import os
import secrets
from datetime import timedelta
from typing import Tuple, List, Dict, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class Config:
    """Application configuration settings"""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY', secrets.token_hex(32))
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    TESTING = os.environ.get('TESTING', 'False').lower() == 'true'
    
    # Enhanced security settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload size
    SECURITY_PASSWORD_SALT = os.environ.get('SECURITY_PASSWORD_SALT', secrets.token_hex(16))
    SECURITY_PASSWORD_HASH = 'bcrypt'
    SECURITY_PASSWORD_LENGTH_MIN = 8
    
    # Enhanced database settings
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///instance/app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
        "pool_size": 10,
        "max_overflow": 20,
        "pool_timeout": 30,
        "echo": DEBUG,
        "echo_pool": DEBUG,
    }
    
    # Rate limiting settings
    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URL = os.environ.get('RATELIMIT_STORAGE_URL', 'memory://')
    RATELIMIT_STRATEGY = 'fixed-window'
    RATELIMIT_DEFAULT = "200 per day;50 per hour;10 per minute"
    
    # Caching settings
    CACHE_TYPE = os.environ.get('CACHE_TYPE', 'simple')
    CACHE_DEFAULT_TIMEOUT = 300
    CACHE_KEY_PREFIX = 'app_cache_'
    
    # Logging settings
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    LOG_FILE = os.environ.get('LOG_FILE', 'app.log')
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5
    
    # Performance settings
    JSON_SORT_KEYS = False
    JSONIFY_PRETTYPRINT_REGULAR = DEBUG
    SEND_FILE_MAX_AGE_DEFAULT = 31536000  # 1 year
    
    # Google API settings
    GOOGLE_CREDENTIALS_FILE = os.environ.get('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
    GOOGLE_SHEETS_ID = os.environ.get('GOOGLE_SHEETS_ID', '')
    GOOGLE_CALENDAR_ID = os.environ.get('GOOGLE_CALENDAR_ID', 'primary')
    
    # Microsoft Graph API settings
    MICROSOFT_CLIENT_ID = os.environ.get('MICROSOFT_CLIENT_ID', '')
    MICROSOFT_CLIENT_SECRET = os.environ.get('MICROSOFT_CLIENT_SECRET', '')
    MICROSOFT_TENANT_ID = os.environ.get('MICROSOFT_TENANT_ID', '')
    
    # iOS Shortcut integration
    IOS_SHORTCUT_TOKEN = os.environ.get('IOS_SHORTCUT_TOKEN', '')
    
    # Apple Mail/Calendar integration
    APPLE_MAIL_USERNAME = os.environ.get('APPLE_MAIL_USERNAME', '')
    APPLE_MAIL_APP_PASSWORD = os.environ.get('APPLE_MAIL_APP_PASSWORD', '')
    APPLE_CALENDAR_USERNAME = os.environ.get('APPLE_CALENDAR_USERNAME', '')
    APPLE_CALENDAR_APP_PASSWORD = os.environ.get('APPLE_CALENDAR_APP_PASSWORD', '')
    
    # Application base URL for webhooks
    BASE_URL = os.environ.get('BASE_URL', 'http://localhost:5000')
    
    # Message scanning settings
    SCAN_INTERVAL_MINUTES = int(os.environ.get('SCAN_INTERVAL_MINUTES', '15'))
    REMINDER_INTERVAL_MINUTES = int(os.environ.get('REMINDER_INTERVAL_MINUTES', '30'))
    
    # Facilities configuration
    FACILITIES = [
        facility.strip() 
        for facility in os.environ.get('FACILITIES', 'Bellevue Medical Center,Clinic A,Clinic B,Clinic C,Clinic D').split(',')
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
    
    # AI Service settings
    AI_FEATURES_ENABLED = os.environ.get('AI_FEATURES_ENABLED', 'True').lower() == 'true'
    AI_SETTINGS = {
        'priority': {
            'high_threshold': float(os.environ.get('AI_PRIORITY_HIGH_THRESHOLD', '0.5')),
            'medium_threshold': float(os.environ.get('AI_PRIORITY_MEDIUM_THRESHOLD', '0.3')),
            'urgent_terms_weight': float(os.environ.get('AI_PRIORITY_URGENT_WEIGHT', '0.4')),
            'deadline_terms_weight': float(os.environ.get('AI_PRIORITY_DEADLINE_WEIGHT', '0.2')),
            'action_terms_weight': float(os.environ.get('AI_PRIORITY_ACTION_WEIGHT', '0.2')),
            'date_weight': float(os.environ.get('AI_PRIORITY_DATE_WEIGHT', '0.1')),
            'sentiment_weight': float(os.environ.get('AI_PRIORITY_SENTIMENT_WEIGHT', '0.1'))
        },
        'similarity': {
            'threshold': float(os.environ.get('AI_SIMILARITY_THRESHOLD', '0.3')),
            'max_messages': int(os.environ.get('AI_SIMILARITY_MAX_MESSAGES', '100')),
            'min_similarity_score': float(os.environ.get('AI_SIMILARITY_MIN_SCORE', '0.3'))
        },
        'summarization': {
            'max_length': int(os.environ.get('AI_SUMMARY_MAX_LENGTH', '150')),
            'min_sentences': int(os.environ.get('AI_SUMMARY_MIN_SENTENCES', '3')),
            'max_clusters': int(os.environ.get('AI_SUMMARY_MAX_CLUSTERS', '3'))
        },
        'task_dependencies': {
            'similarity_threshold': float(os.environ.get('AI_TASK_SIMILARITY_THRESHOLD', '0.8')),
            'title_match_weight': float(os.environ.get('AI_TASK_TITLE_WEIGHT', '0.6')),
            'semantic_match_weight': float(os.environ.get('AI_TASK_SEMANTIC_WEIGHT', '0.4'))
        }
    }
    
    @classmethod
    def validate_config(cls) -> Tuple[bool, List[str], List[str]]:
        """Validate configuration settings"""
        errors = []
        warnings = []
        
        # Enhanced database validation
        if not cls.SQLALCHEMY_DATABASE_URI:
            errors.append("SQLALCHEMY_DATABASE_URI is not configured")
        elif cls.SQLALCHEMY_DATABASE_URI.startswith('sqlite:///'):
            db_path = Path(cls.SQLALCHEMY_DATABASE_URI.replace('sqlite:///', ''))
            if not db_path.parent.exists():
                try:
                    db_path.parent.mkdir(parents=True)
                except Exception as e:
                    errors.append(f"Cannot create database directory: {str(e)}")
            # Check if directory is writable
            if not os.access(db_path.parent, os.W_OK):
                errors.append(f"Database directory is not writable: {db_path.parent}")
        
        # Enhanced security validation
        if not cls.SECRET_KEY or len(cls.SECRET_KEY) < 32:
            errors.append("SECRET_KEY must be at least 32 characters long")
        if not cls.SECURITY_PASSWORD_SALT or len(cls.SECURITY_PASSWORD_SALT) < 16:
            errors.append("SECURITY_PASSWORD_SALT must be at least 16 characters long")
        
        # Validate logging configuration
        if cls.LOG_FILE:
            log_path = Path(cls.LOG_FILE)
            if not log_path.parent.exists():
                try:
                    log_path.parent.mkdir(parents=True)
                except Exception as e:
                    errors.append(f"Cannot create log directory: {str(e)}")
            if not os.access(log_path.parent, os.W_OK):
                errors.append(f"Log directory is not writable: {log_path.parent}")
        
        # Validate cache configuration
        if cls.CACHE_TYPE not in ['simple', 'filesystem', 'redis', 'memcached']:
            warnings.append(f"Unsupported cache type: {cls.CACHE_TYPE}")
        
        # Validate rate limiting configuration
        if cls.RATELIMIT_ENABLED:
            if not cls.RATELIMIT_STORAGE_URL:
                warnings.append("RATELIMIT_STORAGE_URL is not configured")
            if cls.RATELIMIT_STRATEGY not in ['fixed-window', 'moving-window']:
                warnings.append(f"Unsupported rate limit strategy: {cls.RATELIMIT_STRATEGY}")
        
        # Check iOS shortcut token
        if not cls.IOS_SHORTCUT_TOKEN:
            warnings.append("IOS_SHORTCUT_TOKEN is not configured - API endpoints will not work")
        
        # Check facilities configuration
        if not cls.FACILITIES:
            errors.append("No facilities configured")
        
        # Validate Microsoft integration
        ms_config_complete = all([
            cls.MICROSOFT_CLIENT_ID,
            cls.MICROSOFT_CLIENT_SECRET,
            cls.MICROSOFT_TENANT_ID
        ])
        if not ms_config_complete:
            warnings.append('Microsoft Graph API configuration incomplete')
        
        # Validate Google integration
        if not os.path.exists(cls.GOOGLE_CREDENTIALS_FILE):
            warnings.append('Google credentials file not found')
        
        # Validate AI settings
        if cls.AI_FEATURES_ENABLED:
            for category, settings in cls.AI_SETTINGS.items():
                for key, value in settings.items():
                    if isinstance(value, (int, float)) and value < 0:
                        errors.append(f"Invalid AI setting: {category}.{key} must be non-negative")
        
        # Validate intervals
        if cls.SCAN_INTERVAL_MINUTES < 1:
            errors.append("SCAN_INTERVAL_MINUTES must be at least 1")
        if cls.REMINDER_INTERVAL_MINUTES < 1:
            errors.append("REMINDER_INTERVAL_MINUTES must be at least 1")
        
        # Check base URL
        if not cls.BASE_URL.startswith(('http://', 'https://')):
            warnings.append("BASE_URL should start with http:// or https://")
        
        return len(errors) == 0, errors, warnings
    
    @classmethod
    def get_required_env_vars(cls) -> Dict[str, str]:
        """Get a dictionary of required environment variables and their descriptions."""
        return {
            'SECRET_KEY': 'Secret key for session security',
            'DATABASE_URL': 'Database connection URL',
            'MICROSOFT_CLIENT_ID': 'Microsoft Graph API client ID',
            'MICROSOFT_CLIENT_SECRET': 'Microsoft Graph API client secret',
            'MICROSOFT_TENANT_ID': 'Microsoft Graph API tenant ID',
            'GOOGLE_CREDENTIALS_FILE': 'Path to Google API credentials file',
            'BASE_URL': 'Base URL for webhooks and callbacks',
            'SECURITY_PASSWORD_SALT': 'Salt for password hashing',
            'LOG_LEVEL': 'Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)',
            'CACHE_TYPE': 'Cache type (simple, filesystem, redis, memcached)',
            'RATELIMIT_STORAGE_URL': 'Rate limiting storage URL'
        }
