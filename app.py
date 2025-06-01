import os
import logging
import atexit
import signal
from datetime import datetime, timedelta
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from config import Config

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
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
        
        # Enhanced environment variable validation
        required_vars = Config.get_required_env_vars()
        missing_vars = []
        for var, desc in required_vars.items():
            if not os.environ.get(var) and not app.config.get(var):
                missing_vars.append(f"{var} ({desc})")
        
        if missing_vars:
            error_msg = "Missing required environment variables:\n" + "\n".join(f"- {var}" for var in missing_vars)
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        # Ensure required environment variables are set
        if not app.config.get('SECRET_KEY'):
            app.config['SECRET_KEY'] = os.environ.get("SESSION_SECRET", Config.SECRET_KEY)
            if not app.config['SECRET_KEY']:
                raise RuntimeError("No SECRET_KEY set in config or environment")
        
        app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
        
        # Enhanced configuration validation
        is_valid, errors, warnings = Config.validate_config()
        if warnings:
            for warning in warnings:
                logger.warning(f"Configuration warning: {warning}")
        if not is_valid:
            error_msg = "Configuration errors found:\n" + "\n".join(f"- {error}" for error in errors)
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        # Initialize extensions with error handling
        try:
            db.init_app(app)
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            raise
        
        # Add template context processors
        @app.context_processor
        def inject_datetime():
            return dict(
                now=datetime.now(),
                timedelta=timedelta,
                datetime=datetime
            )
        
        # Enhanced error handlers with detailed logging
        @app.errorhandler(404)
        def not_found_error(error):
            logger.warning(f"404 error: {str(error)}")
            return jsonify({'error': 'Not found', 'message': str(error)}), 404

        @app.errorhandler(500)
        def internal_error(error):
            logger.error(f"500 error: {str(error)}")
            db.session.rollback()
            return jsonify({'error': 'Internal server error', 'message': str(error)}), 500
        
        # Register routes with error handling
        try:
            from routes import register_routes
            register_routes(app)
        except Exception as e:
            logger.error(f"Failed to register routes: {str(e)}")
            raise
        
        # Create database tables with enhanced error handling
        with app.app_context():
            import models  # Import models to register them
            try:
                db.create_all()
                logger.info("Database tables created successfully")
            except Exception as e:
                logger.error(f"Error creating database tables: {str(e)}")
                raise
        
        # Initialize health check endpoint
        @app.route('/health')
        def health_check():
            try:
                # Test database connection
                db.session.execute('SELECT 1')
                return jsonify({
                    'status': 'healthy',
                    'database': 'connected',
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Health check failed: {str(e)}")
                return jsonify({
                    'status': 'unhealthy',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }), 500
        
        return app
        
    except Exception as e:
        logger.error(f"Error creating application: {str(e)}")
        raise

def cleanup_resources():
    """Cleanup function to be called on shutdown"""
    try:
        if hasattr(app, 'scheduler_service'):
            app.scheduler_service.shutdown()
        logger.info("Application resources cleaned up successfully")
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, initiating shutdown...")
    cleanup_resources()
    exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Register cleanup function
atexit.register(cleanup_resources)

# Create the app instance
try:
    app = create_app()
    
    # Initialize scheduler for message scanning
    from scheduler import init_scheduler
    scheduler_service = init_scheduler(app)
    logger.info("Application initialized successfully")
    
except Exception as e:
    logger.critical(f"Failed to initialize application: {str(e)}")
    raise

if __name__ == '__main__':
    try:
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port)
    except Exception as e:
        logger.critical(f"Failed to start application: {str(e)}")
        raise
