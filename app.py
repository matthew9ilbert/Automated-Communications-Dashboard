import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from config import Config

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(Config)
    app.secret_key = os.environ.get("SESSION_SECRET", Config.SECRET_KEY)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Initialize extensions
    db.init_app(app)
    
    # Register routes
    from routes import register_routes
    register_routes(app)
    
    # Create database tables
    with app.app_context():
        import models  # Import models to register them
        db.create_all()
    
    return app

# Create the app instance
app = create_app()

# Initialize scheduler for message scanning
from scheduler import init_scheduler
init_scheduler(app)
