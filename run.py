import os
import sys
import time
import logging
import subprocess
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('run.log')
    ]
)
logger = logging.getLogger('run')

def run_command(command, description):
    """Run a command and log its output"""
    logger.info(f"Running: {description}")
    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True
        )
        if result.stdout:
            logger.info(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {description}")
        if e.stdout:
            logger.error(f"Output: {e.stdout}")
        if e.stderr:
            logger.error(f"Error: {e.stderr}")
        return False

def main():
    """Main function to run all setup and launch steps"""
    start_time = time.time()
    logger.info("Starting application setup and launch...")
    
    # Step 1: Set up environment
    logger.info("Step 1: Setting up environment")
    if not run_command([sys.executable, 'setup_env.py'], "Environment setup"):
        return False
    
    # Step 2: Install spaCy model
    logger.info("Step 2: Installing spaCy model")
    if not run_command([sys.executable, 'install_spacy.py'], "SpaCy model installation"):
        return False
    
    # Step 3: Run launch analysis
    logger.info("Step 3: Running launch analysis")
    if not run_command([sys.executable, 'launch.py'], "Launch analysis"):
        return False
    
    # Step 4: Start the application
    logger.info("Step 4: Starting the application")
    try:
        # Use gunicorn in production, Flask development server in development
        if os.environ.get('FLASK_ENV') == 'production':
            run_command([
                'gunicorn',
                '--bind', '0.0.0.0:5000',
                '--workers', '4',
                '--timeout', '120',
                '--access-logfile', '-',
                '--error-logfile', '-',
                'app:app'
            ], "Starting Gunicorn server")
        else:
            run_command([
                sys.executable,
                'app.py'
            ], "Starting Flask development server")
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        return False
    
    end_time = time.time()
    duration = end_time - start_time
    logger.info(f"Total setup and launch time: {duration:.2f} seconds")
    return True

if __name__ == '__main__':
    success = main()
    if not success:
        sys.exit(1) 