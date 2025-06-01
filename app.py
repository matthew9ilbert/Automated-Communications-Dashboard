import os
import logging
from datetime import datetime, timedelta
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from config import Config

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

def create_app():
    """Application factory pattern"""
    try:
        app = Flask(__name__)
        app.config.from_object(Config)
        
        # Ensure required environment variables are set
        if not app.config.get('SECRET_KEY'):
            app.config['SECRET_KEY'] = os.environ.get("SESSION_SECRET", Config.SECRET_KEY)
            if not app.config['SECRET_KEY']:
                raise RuntimeError("No SECRET_KEY set in config or environment")
        
        app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
        
        # Validate configuration
        is_valid, errors, warnings = Config.validate_config()
        if warnings:
            logger.warning(f"Configuration warnings: {', '.join(warnings)}")
        if not is_valid:
            raise RuntimeError(f"Configuration errors found: {', '.join(errors)}")
        
        # Initialize extensions
        db.init_app(app)
        
        # Add template context processors
        @app.context_processor
        def inject_datetime():
            return dict(
                now=datetime.now(),
                timedelta=timedelta,
                datetime=datetime
            )
        
        # Register routes
        from routes import register_routes
        register_routes(app)
        
        # Create database tables
        with app.app_context():
            import models  # Import models to register them
            try:
                db.create_all()
                logger.info("Database tables created successfully")
            except Exception as e:
                logger.error(f"Error creating database tables: {str(e)}")
                raise
        
        return app
        
    except Exception as e:
        logger.error(f"Error creating application: {str(e)}")
        raise

# Create the app instance
try:
    app = create_app()
    
    # Initialize scheduler for message scanning
    from scheduler import init_scheduler
    init_scheduler(app)
    logger.info("Application initialized successfully")
    
except Exception as e:
    logger.critical(f"Failed to initialize application: {str(e)}")
    raise
