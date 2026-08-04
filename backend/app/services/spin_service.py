"""
Spin Service
ACID-compliant spin logic with disabled item exclusion
Supports guaranteed wins and template-based prize selection
"""

import logging
import random
from datetime import date
from ..database import execute_sql, session_scope, execute_function
from ..models import Prize, Inventory, Transaction, GuaranteedWin, DateTemplateAssignment
from .realtime_service import RealtimeService

logger = logging.getLogger(__name__)


class SpinService:
    """Service for handling wheel spins with ACID transactions"""
    
    @staticmethod
    def get_available_prizes(event_id=1, target_date=None):
        """Get prizes available for winning (enabled + has inventory)"""
        if target_date is None:
            target_date = date.today()
        
        return Prize.get_available_for_spin(event_id, target_date)
    
    @staticmethod
    def get_wheel_prizes(event_id=1, target_date=None):
        """Get all prizes for wheel display (including disabled)"""
        if target_date is None:
            target_date = date.today()
        
        return Prize.get_for_wheel_display(event_id, target_date)
    
    @staticmethod
    def select_winning_prize(event_id=1, target_date=None, user_identifier=None):
        """
        Select a winning prize using the following priority:
        1. Check for guaranteed wins (next spin or scheduled)
        2. Get prizes from date-specific template (if assigned)
        3. Fall back to default weighted random selection
        
        Only selects from ENABLED prizes with remaining inventory.
        """
        if target_date is None:
            target_date = date.today()
        
        # Priority 1: Check for guaranteed win
        guaranteed_win = GuaranteedWin.get_pending(user_identifier)
        if guaranteed_win:
            logger.info(f"Guaranteed win found: {guaranteed_win['prize_name']} (Win ID: {guaranteed_win['win_id']})")
            # Get full prize details
            prize = Prize.get_by_id(guaranteed_win['prize_id'])
            if prize:
                # Return in the same format as regular prizes
                return {
                    'prize_id': prize['id'],
                    'name': prize['name'],
                    'emoji': prize['emoji'],
                    'category_name': prize['category_name'],
                    'category_display': prize.get('category_display', prize['category_name']),
                    'remaining_quantity': 1,  # Guaranteed, so always 1
                    'is_guaranteed': True,
                    'guaranteed_win_id': guaranteed_win['win_id']
                }
        
        # Priority 2: Get available prizes (could be from template or default)
        available_prizes = SpinService.get_available_prizes(event_id, target_date)
        
        if not available_prizes:
            logger.warning("No available prizes for selection")
            return None
        
        # Separate by category for weighted selection
        ultra_rare = [p for p in available_prizes if p['category_name'] == 'ultra_rare']
        rare = [p for p in available_prizes if p['category_name'] == 'rare']
        common = [p for p in available_prizes if p['category_name'] == 'common']
        
        logger.info(f"Available: {len(ultra_rare)} ultra_rare, {len(rare)} rare, {len(common)} common")
        
        # Weighted category selection
        # Higher chance for rare items to make the game exciting
        category_weights = []
        categories = []
        
        if ultra_rare:
            categories.append(ultra_rare)
            category_weights.append(15)  # 15% for ultra_rare
        if rare:
            categories.append(rare)
            category_weights.append(35)  # 35% for rare
        if common:
            categories.append(common)
            category_weights.append(50)  # 50% for common
        
        if not categories:
            return None
        
        # Select category
        selected_category = random.choices(categories, weights=category_weights, k=1)[0]
        
        # Select prize from category (weighted by remaining quantity)
        weights = [max(1, p['remaining_quantity']) for p in selected_category]
        selected_prize = random.choices(selected_category, weights=weights, k=1)[0]
        
        logger.info(f"Selected prize: {selected_prize['name']} ({selected_prize['category_name']})")
        
        return selected_prize
    
    @staticmethod
    def pre_spin(user_identifier, event_id=1, target_date=None):
        """
        Pre-spin selection - select the winning prize before animation.
        Returns the prize and its wheel segment index.
        Checks for guaranteed wins first.
        """
        if target_date is None:
            target_date = date.today()
        
        # Select winning prize (handles guaranteed wins internally)
        selected_prize = SpinService.select_winning_prize(event_id, target_date, user_identifier)
        
        if not selected_prize:
            return {
                'success': False,
                'error': 'No prizes available'
            }
        
        # Get all wheel prizes to find segment index
        wheel_prizes = SpinService.get_wheel_prizes(event_id, target_date)
        
        # Find the segment index for the selected prize
        target_segment_index = next(
            (i for i, p in enumerate(wheel_prizes) if p['prize_id'] == selected_prize['prize_id']),
            0
        )
        
        result = {
            'success': True,
            'selected_prize': {
                'id': selected_prize['prize_id'],
                'name': selected_prize['name'],
                'category': selected_prize['category_name'],
                'category_display': selected_prize['category_display'],
                'emoji': selected_prize['emoji'],
                'remaining_quantity': selected_prize['remaining_quantity']
            },
            'target_segment_index': target_segment_index,
            'total_segments': len(wheel_prizes)
        }
        
        # Include guaranteed win info if applicable
        if selected_prize.get('is_guaranteed'):
            result['is_guaranteed'] = True
            result['guaranteed_win_id'] = selected_prize['guaranteed_win_id']
        
        return result
    
    @staticmethod
    def execute_spin(prize_id, user_identifier, event_id=1, target_date=None, guaranteed_win_id=None):
        """
        Execute the spin - consume prize and record transaction.
        Uses PostgreSQL function for ACID compliance.
        Handles guaranteed wins specially.
        """
        if target_date is None:
            target_date = date.today()
        
        # If this is a guaranteed win, mark it as triggered
        if guaranteed_win_id:
            GuaranteedWin.trigger(guaranteed_win_id, user_identifier)
            logger.info(f"Triggered guaranteed win (ID: {guaranteed_win_id}) for user {user_identifier}")
        
        # Use the consume_prize function for atomic operation
        results = execute_function('consume_prize', prize_id, event_id, user_identifier, '{}')
        
        if not results or not results[0]['success']:
            logger.warning(f"Failed to consume prize {prize_id}")
            return {
                'success': False,
                'error': 'Prize no longer available'
            }
        
        result = results[0]
        
        # Get prize details
        prize = Prize.get_by_id(prize_id)
        
        # Broadcast update to all connected clients
        RealtimeService.broadcast_prize_update(prize_id, result['remaining'])
        RealtimeService.broadcast_transaction({
            'prize_id': prize_id,
            'prize_name': prize['name'] if prize else 'Unknown',
            'category': prize['category_name'] if prize else 'Unknown',
            'user': user_identifier[:8] + '...' if len(user_identifier) > 8 else user_identifier,
            'is_guaranteed': guaranteed_win_id is not None
        })
        
        logger.info(f"Spin executed: {prize['name'] if prize else prize_id} won by {user_identifier}" + 
                   (" (Guaranteed)" if guaranteed_win_id else ""))
        
        return {
            'success': True,
            'prize': prize,
            'transaction_id': result['transaction_id'],
            'remaining_quantity': result['remaining'],
            'was_guaranteed': guaranteed_win_id is not None
        }
    
    @staticmethod
    def get_daily_stats(event_id=1, target_date=None):
        """Get statistics for the day"""
        if target_date is None:
            target_date = date.today()
        
        stats = Transaction.get_stats_for_date(target_date)
        wins_by_category = Transaction.get_wins_by_category(target_date)
        
        return {
            'date': target_date.isoformat(),
            'total_spins': stats.get('total_transactions', 0),
            'total_wins': stats.get('total_wins', 0),
            'unique_users': stats.get('unique_users', 0),
            'wins_by_category': {w['category_name']: w['win_count'] for w in wins_by_category}
        }
