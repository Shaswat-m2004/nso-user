from flask import Flask
from app.config import Config
from app.routes import bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Register all our routes from routes.py
    app.register_blueprint(bp)
    
    return app