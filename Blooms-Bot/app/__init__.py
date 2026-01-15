from flask import Flask
from app.app import app as app_blueprint  # Import the Blueprint

def create_app():
    app = Flask(__name__)
    app.register_blueprint(app_blueprint)  # Register the Blueprint
    return app