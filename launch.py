import os
import sys
import time
import logging
import traceback
from datetime import datetime
from pathlib import Path

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('launch.log')
    ]
)
logger = logging.getLogger('launch')

def check_environment():
    """Check environment setup and dependencies"""
    logger.info("Checking environment setup...")
    issues = []
    
    # Check Python version
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        issues.append(f"Python version {python_version.major}.{python_version.minor} is not supported. Please use Python 3.8 or higher.")
    
    # Check required directories
    required_dirs = ['instance', 'logs', 'static', 'templates']
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            try:
                dir_path.mkdir(parents=True)
                logger.info(f"Created directory: {dir_name}")
            except Exception as e:
                issues.append(f"Failed to create directory {dir_name}: {str(e)}")
    
    # Check environment variables
    required_vars = [
        'SECRET_KEY',
        'DATABASE_URL',
        'BASE_URL'
    ]
    for var in required_vars:
        if not os.environ.get(var):
            issues.append(f"Required environment variable {var} is not set")
    
    return issues

def check_dependencies():
    """Check if all required packages are installed"""
    logger.info("Checking dependencies...")
    issues = []
    
    try:
        import flask
        import sqlalchemy
        import werkzeug
        import requests
        import google.auth
        import msal
        import redis
        import gunicorn
        import sentry_sdk
        import prometheus_client
        import structlog
        import spacy
        
        # Check spaCy model
        try:
            nlp = spacy.load("en_core_web_sm")
        except OSError:
            issues.append("spaCy model 'en_core_web_sm' is not installed")
            
    except ImportError as e:
        issues.append(f"Missing dependency: {str(e)}")
    
    return issues

def check_database():
    """Check database connection and setup"""
    logger.info("Checking database connection...")
    issues = []
    
    try:
        from app import create_app, db
        app = create_app()
        with app.app_context():
            # Test database connection
            db.session.execute('SELECT 1')
            logger.info("Database connection successful")
            
            # Check if tables exist
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            if not tables:
                issues.append("No database tables found")
            else:
                logger.info(f"Found {len(tables)} database tables")
                
    except Exception as e:
        issues.append(f"Database check failed: {str(e)}")
    
    return issues

def main():
    """Main launch function with detailed analysis"""
    start_time = time.time()
    logger.info("Starting application launch analysis...")
    
    # Track all issues
    all_issues = []
    
    # Stage 1: Environment Check
    logger.info("Stage 1: Environment Check")
    env_issues = check_environment()
    if env_issues:
        all_issues.extend(env_issues)
        logger.error("Environment check failed")
    else:
        logger.info("Environment check passed")
    
    # Stage 2: Dependencies Check
    logger.info("Stage 2: Dependencies Check")
    dep_issues = check_dependencies()
    if dep_issues:
        all_issues.extend(dep_issues)
        logger.error("Dependencies check failed")
    else:
        logger.info("Dependencies check passed")
    
    # Stage 3: Database Check
    logger.info("Stage 3: Database Check")
    db_issues = check_database()
    if db_issues:
        all_issues.extend(db_issues)
        logger.error("Database check failed")
    else:
        logger.info("Database check passed")
    
    # Summary
    end_time = time.time()
    duration = end_time - start_time
    
    if all_issues:
        logger.error("Launch analysis completed with issues:")
        for issue in all_issues:
            logger.error(f"- {issue}")
        logger.error(f"Total issues found: {len(all_issues)}")
        return False
    else:
        logger.info("Launch analysis completed successfully")
        logger.info(f"Total time: {duration:.2f} seconds")
        return True

if __name__ == '__main__':
    success = main()
    if not success:
        sys.exit(1) 