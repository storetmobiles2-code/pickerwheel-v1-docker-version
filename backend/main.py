#!/usr/bin/env python3
"""
PickerWheel Backend - Main Entry Point
PostgreSQL-based backend with real-time WebSocket support
"""

import os
import sys
import logging

# Add app directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, socketio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create application
app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 9080))
    debug = os.environ.get('FLASK_ENV', 'development') == 'development'
    
    logger.info(f"Starting PickerWheel Backend on port {port}")
    logger.info(f"Debug mode: {debug}")
    logger.info(f"Database: {app.config['DATABASE_URL'].split('@')[1] if '@' in app.config['DATABASE_URL'] else 'configured'}")
    
    # Run with Socket.IO support
    socketio.run(
        app,
        host='0.0.0.0',
        port=port,
        debug=debug,
        allow_unsafe_werkzeug=True
    )
