import os
from dotenv import load_dotenv
import logging

def load_environment():
    """
    Load environment variables and set up basic configuration.
    Returns True if successful, False otherwise.
    """
    try:
        # Load environment variables from .env file if it exists
        load_dotenv()
        
        # Required environment variables
        required_vars = [
            'SECRET_KEY',
            'SECURITY_PASSWORD_SALT',
            'LOG_LEVEL',
            'CACHE_TYPE',
            'RATELIMIT_STORAGE_URL'
        ]
        
        # Check if all required variables are set
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            logging.error(f"Missing required environment variables: {', '.join(missing_vars)}")
            return False
            
        # Set up logging
        log_level = os.getenv('LOG_LEVEL', 'INFO')
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        logging.info("Environment variables loaded successfully")
        return True
        
    except Exception as e:
        logging.error(f"Error loading environment variables: {str(e)}")
        return False

if __name__ == "__main__":
    # Test the environment loading
    success = load_environment()
    if success:
        print("Environment variables loaded successfully!")
        print(f"SECRET_KEY: {os.getenv('SECRET_KEY')[:10]}...")
        print(f"SECURITY_PASSWORD_SALT: {os.getenv('SECURITY_PASSWORD_SALT')[:10]}...")
        print(f"LOG_LEVEL: {os.getenv('LOG_LEVEL')}")
        print(f"CACHE_TYPE: {os.getenv('CACHE_TYPE')}")
        print(f"RATELIMIT_STORAGE_URL: {os.getenv('RATELIMIT_STORAGE_URL')}")
    else:
        print("Failed to load environment variables. Please check the setup.") 