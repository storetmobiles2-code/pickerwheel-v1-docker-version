"""
PickerWheel Backend Application
Flask app factory with Socket.IO for real-time updates
"""

import os
import logging
from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO

# Initialize Socket.IO globally for access from other modules
socketio = SocketIO()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app(config_name=None):
    """Create and configure the Flask application"""
    app = Flask(__name__, 
                static_folder='../../frontend',
                static_url_path='')
    
    # Load configuration
    from .config import config
    config_name = config_name or os.environ.get('FLASK_ENV', 'development')
    app.config.from_object(config[config_name])
    
    # Enable CORS
    CORS(app, resources={
        r"/api/*": {"origins": "*"},
        r"/socket.io/*": {"origins": "*"}
    })
    
    # Initialize Socket.IO
    socketio.init_app(app, 
                      cors_allowed_origins="*",
                      async_mode='threading',
                      logger=True,
                      engineio_logger=True)
    
    # Initialize database
    from .database import init_db
    init_db(app)
    
    # Register blueprints
    from .routes.api import api_bp
    from .routes.admin import admin_bp
    
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    
    # Register WebSocket handlers
    from .routes import websocket
    websocket.register_handlers(socketio)
    
    # Register static file routes
    @app.route('/')
    def serve_index():
        return app.send_static_file('index.html')
    
    @app.route('/admin')
    def serve_admin():
        return app.send_static_file('admin.html')
    
    @app.route('/<path:filename>')
    def serve_static(filename):
        return app.send_static_file(filename)
    
    logger.info(f"PickerWheel app created with config: {config_name}")
    
    return app
