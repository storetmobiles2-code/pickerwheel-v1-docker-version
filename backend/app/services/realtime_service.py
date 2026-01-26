"""
Realtime Service
WebSocket broadcasting for live updates
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Reference to socketio instance (set by websocket module)
_socketio = None


def set_socketio(socketio_instance):
    """Set the Socket.IO instance for broadcasting"""
    global _socketio
    _socketio = socketio_instance


class RealtimeService:
    """Service for real-time WebSocket broadcasting"""
    
    @staticmethod
    def get_socketio():
        """Get the Socket.IO instance"""
        global _socketio
        if _socketio is None:
            # Try to import from app
            try:
                from .. import socketio
                _socketio = socketio
            except ImportError:
                logger.warning("Socket.IO not available")
        return _socketio
    
    @staticmethod
    def broadcast_prizes_updated(prizes):
        """Broadcast updated prize list to all clients"""
        socketio = RealtimeService.get_socketio()
        if socketio:
            socketio.emit('prizes:updated', {
                'prizes': prizes,
                'timestamp': datetime.utcnow().isoformat()
            })
            logger.info(f"Broadcast prizes:updated with {len(prizes)} prizes")
    
    @staticmethod
    def broadcast_prize_update(prize_id, remaining_quantity):
        """Broadcast single prize inventory update"""
        socketio = RealtimeService.get_socketio()
        if socketio:
            socketio.emit('prize:inventory_updated', {
                'prize_id': prize_id,
                'remaining_quantity': remaining_quantity,
                'timestamp': datetime.utcnow().isoformat()
            })
            logger.debug(f"Broadcast inventory update for prize {prize_id}")
    
    @staticmethod
    def broadcast_prize_enabled_changed(prize_id, is_enabled, prize_name=None):
        """Broadcast when a prize is enabled/disabled"""
        socketio = RealtimeService.get_socketio()
        if socketio:
            socketio.emit('prize:enabled_changed', {
                'prize_id': prize_id,
                'is_enabled': is_enabled,
                'prize_name': prize_name,
                'timestamp': datetime.utcnow().isoformat()
            })
            logger.info(f"Broadcast enabled change for prize {prize_id}: {is_enabled}")
    
    @staticmethod
    def broadcast_prize_added(prize):
        """Broadcast when a new prize is added"""
        socketio = RealtimeService.get_socketio()
        if socketio:
            socketio.emit('prize:added', {
                'prize': prize,
                'timestamp': datetime.utcnow().isoformat()
            })
            logger.info(f"Broadcast prize added: {prize.get('name', prize.get('id'))}")
    
    @staticmethod
    def broadcast_prize_removed(prize_id, prize_name=None):
        """Broadcast when a prize is removed"""
        socketio = RealtimeService.get_socketio()
        if socketio:
            socketio.emit('prize:removed', {
                'prize_id': prize_id,
                'prize_name': prize_name,
                'timestamp': datetime.utcnow().isoformat()
            })
            logger.info(f"Broadcast prize removed: {prize_id}")
    
    @staticmethod
    def broadcast_transaction(transaction_data):
        """Broadcast a new transaction (win)"""
        socketio = RealtimeService.get_socketio()
        if socketio:
            socketio.emit('transaction:new', {
                **transaction_data,
                'timestamp': datetime.utcnow().isoformat()
            })
            logger.debug(f"Broadcast new transaction")
    
    @staticmethod
    def broadcast_stats_updated(stats):
        """Broadcast updated statistics"""
        socketio = RealtimeService.get_socketio()
        if socketio:
            socketio.emit('stats:updated', {
                'stats': stats,
                'timestamp': datetime.utcnow().isoformat()
            })
    
    @staticmethod
    def send_to_admin(event, data):
        """Send event only to admin room"""
        socketio = RealtimeService.get_socketio()
        if socketio:
            socketio.emit(event, data, room='admin')
    
    @staticmethod
    def notify_admin(message, level='info'):
        """Send notification to admin panel"""
        socketio = RealtimeService.get_socketio()
        if socketio:
            socketio.emit('admin:notification', {
                'message': message,
                'level': level,
                'timestamp': datetime.utcnow().isoformat()
            }, room='admin')
