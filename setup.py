import subprocess
import sys
import os
import secrets
from pathlib import Path
import logging
from typing import Tuple, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_python_version() -> bool:
    """Check if Python version meets requirements."""
    required_version = (3, 8)
    current_version = sys.version_info[:2]
    if current_version < required_version:
        logger.error(f"Python {required_version[0]}.{required_version[1]} or higher is required")
        return False
    return True

def check_disk_space() -> bool:
    """Check if there's enough disk space for installation."""
    try:
        free_space = os.statvfs('.').f_frsize * os.statvfs('.').f_bavail
        required_space = 500 * 1024 * 1024  # 500MB
        if free_space < required_space:
            logger.error(f"Insufficient disk space. Required: 500MB, Available: {free_space/1024/1024:.2f}MB")
            return False
        return True
    except Exception as e:
        logger.warning(f"Could not check disk space: {e}")
        return True

def generate_secret_key() -> str:
    """Generate a secure secret key."""
    return secrets.token_hex(32)

def setup_environment() -> Tuple[bool, List[str]]:
    """Set up the Python environment and install dependencies."""
    errors = []
    
    try:
        logger.info("Setting up Automated Communications Dashboard environment...")
        
        # Create virtual environment if it doesn't exist
        if not Path(".venv").exists():
            logger.info("Creating virtual environment...")
            subprocess.run([sys.executable, "-m", "venv", ".venv"], check=True)
        
        # Determine the pip path
        if sys.platform == "win32":
            pip_path = ".venv/Scripts/pip"
            python_path = ".venv/Scripts/python"
        else:
            pip_path = ".venv/bin/pip"
            python_path = ".venv/bin/python"
        
        # Upgrade pip
        logger.info("Upgrading pip...")
        subprocess.run([pip_path, "install", "--upgrade", "pip"], check=True)
        
        # Install requirements
        logger.info("Installing dependencies...")
        subprocess.run([pip_path, "install", "-r", "requirements.txt"], check=True)
        
        # Install spaCy model
        logger.info("Installing spaCy language model...")
        subprocess.run([pip_path, "install", "https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl"], check=True)
        
        # Verify installation
        logger.info("Verifying installation...")
        subprocess.run([python_path, "-c", "import flask; import spacy; import sqlalchemy"], check=True)
        
        logger.info("Environment setup complete!")
        return True, []
        
    except subprocess.CalledProcessError as e:
        error_msg = f"Error during environment setup: {str(e)}"
        logger.error(error_msg)
        errors.append(error_msg)
        return False, errors
    except Exception as e:
        error_msg = f"Unexpected error during setup: {str(e)}"
        logger.error(error_msg)
        errors.append(error_msg)
        return False, errors

def create_env_file() -> Tuple[bool, List[str]]:
    """Create a .env file with default configuration if it doesn't exist."""
    errors = []
    
    try:
        if not Path(".env").exists():
            logger.info("Creating .env file with default configuration...")
            env_content = f"""# Flask Configuration
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY={generate_secret_key()}

# Database Configuration
DATABASE_URL=sqlite:///instance/app.db

# API Keys (Replace with your actual keys)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
MICROSOFT_CLIENT_ID=your-microsoft-client-id
MICROSOFT_CLIENT_SECRET=your-microsoft-client-secret

# Application Settings
DEBUG=True
LOG_LEVEL=INFO
MAX_CONTENT_LENGTH=16777216  # 16MB max upload size
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
PERMANENT_SESSION_LIFETIME=3600  # 1 hour

# Security Settings
PASSWORD_SALT={secrets.token_hex(16)}
"""
            with open(".env", "w") as f:
                f.write(env_content)
            logger.info("Created .env file. Please update it with your actual configuration values.")
            return True, []
    except Exception as e:
        error_msg = f"Error creating .env file: {str(e)}"
        logger.error(error_msg)
        errors.append(error_msg)
        return False, errors

def create_instance_folder() -> Tuple[bool, List[str]]:
    """Create instance folder for application data."""
    errors = []
    try:
        instance_path = Path("instance")
        if not instance_path.exists():
            instance_path.mkdir(parents=True)
            logger.info("Created instance directory")
        return True, []
    except Exception as e:
        error_msg = f"Error creating instance directory: {str(e)}"
        logger.error(error_msg)
        errors.append(error_msg)
        return False, errors

if __name__ == "__main__":
    all_errors = []
    
    # Check prerequisites
    if not check_python_version():
        sys.exit(1)
    if not check_disk_space():
        sys.exit(1)
    
    # Run setup steps
    success, errors = setup_environment()
    all_errors.extend(errors)
    
    if success:
        success, errors = create_env_file()
        all_errors.extend(errors)
        
        success, errors = create_instance_folder()
        all_errors.extend(errors)
    
    if all_errors:
        logger.error("\nSetup completed with errors:")
        for error in all_errors:
            logger.error(f"- {error}")
        sys.exit(1)
    else:
        logger.info("\nSetup completed successfully!")
        logger.info("\nNext steps:")
        logger.info("1. Update the .env file with your actual configuration values")
        logger.info("2. Run 'python app.py' to start the application") 