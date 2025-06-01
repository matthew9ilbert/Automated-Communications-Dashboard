import subprocess
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def install_spacy_model():
    """Install the required spaCy model"""
    try:
        logger.info("Installing spaCy model: en_core_web_sm")
        subprocess.check_call([
            sys.executable, 
            "-m", 
            "spacy", 
            "download", 
            "en_core_web_sm"
        ])
        logger.info("Successfully installed spaCy model")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install spaCy model: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error installing spaCy model: {str(e)}")
        return False

if __name__ == '__main__':
    success = install_spacy_model()
    if not success:
        sys.exit(1) 