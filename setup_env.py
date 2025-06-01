import os
import secrets
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_environment():
    """Set up required environment variables"""
    # Create .env file if it doesn't exist
    env_file = Path('.env')
    if not env_file.exists():
        logger.info("Creating .env file...")
        
        # Generate secure keys
        secret_key = secrets.token_hex(32)
        password_salt = secrets.token_hex(16)
        
        # Default configuration
        env_content = f"""# Flask settings
SECRET_KEY={secret_key}
DEBUG=False
TESTING=False

# Security settings
SECURITY_PASSWORD_SALT={password_salt}

# Database settings
DATABASE_URL=sqlite:///instance/app.db

# Application settings
BASE_URL=http://localhost:5000
LOG_LEVEL=INFO
CACHE_TYPE=simple
RATELIMIT_STORAGE_URL=memory://

# Google API settings (update these with your credentials)
GOOGLE_CREDENTIALS_FILE=credentials.json
GOOGLE_SHEETS_ID=
GOOGLE_CALENDAR_ID=primary

# Microsoft Graph API settings (update these with your credentials)
MICROSOFT_CLIENT_ID=
MICROSOFT_CLIENT_SECRET=
MICROSOFT_TENANT_ID=

# iOS Shortcut integration
IOS_SHORTCUT_TOKEN=

# Apple Mail/Calendar integration
APPLE_MAIL_USERNAME=
APPLE_MAIL_APP_PASSWORD=
APPLE_CALENDAR_USERNAME=
APPLE_CALENDAR_APP_PASSWORD=
"""
        
        try:
            with open(env_file, 'w') as f:
                f.write(env_content)
            logger.info("Created .env file with default configuration")
        except Exception as e:
            logger.error(f"Failed to create .env file: {str(e)}")
            return False
    
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
        logger.info("Loaded environment variables from .env file")
        return True
    except Exception as e:
        logger.error(f"Failed to load environment variables: {str(e)}")
        return False

if __name__ == '__main__':
    success = setup_environment()
    if not success:
        exit(1) 