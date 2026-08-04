"""
Inventory Model
Handles prize inventory with atomic updates
"""

import logging
from datetime import date, timedelta
from ..database import execute_sql, session_scope
from sqlalchemy import text

logger = logging.getLogger(__name__)


class Inventory:
    """Prize inventory model"""
    
    @staticmethod
    def get_for_prize(prize_id, event_id=1, target_date=None):
        """Get inventory for a specific prize"""
        if target_date is None:
            target_date = date.today()
        
        sql = """
            SELECT pi.id, pi.prize_id, pi.event_id, pi.available_date,
                   pi.initial_quantity, pi.remaining_quantity, pi.daily_limit,
                   p.name as prize_name, pc.name as category_name
            FROM prize_inventory pi
            JOIN prizes p ON pi.prize_id = p.id
            JOIN prize_categories pc ON p.category_id = pc.id
            WHERE pi.prize_id = :prize_id
              AND pi.event_id = :event_id
              AND pi.available_date = :date
        """
        results = execute_sql(sql, {
            'prize_id': prize_id,
            'event_id': event_id,
            'date': target_date
        })
        return results[0] if results else None
    
    @staticmethod
    def get_all_for_date(event_id=1, target_date=None):
        """Get all inventory for a specific date"""
        if target_date is None:
            target_date = date.today()
        
        sql = """
            SELECT pi.id, pi.prize_id, pi.event_id, pi.available_date,
                   pi.initial_quantity, pi.remaining_quantity, pi.daily_limit,
                   p.name as prize_name, p.emoji, p.is_enabled, p.is_active,
                   pc.name as category_name, pc.display_name as category_display,
                   COALESCE(tw.wins_today, 0) as wins_today
            FROM prize_inventory pi
            JOIN prizes p ON pi.prize_id = p.id
            JOIN prize_categories pc ON p.category_id = pc.id
            LEFT JOIN (
                SELECT prize_id, COUNT(*) as wins_today
                FROM transactions
                WHERE transaction_type = 'win'
                  AND DATE(created_at) = :date
                GROUP BY prize_id
            ) tw ON pi.prize_id = tw.prize_id
            WHERE pi.event_id = :event_id
              AND pi.available_date = :date
              AND p.is_active = TRUE
            ORDER BY p.display_order ASC, p.id ASC
        """
        return execute_sql(sql, {'event_id': event_id, 'date': target_date}) or []
    
    @staticmethod
    def create_for_prize(prize_id, event_id=1, target_date=None, 
                         initial_quantity=10, daily_limit=5):
        """Create inventory entry for a prize"""
        if target_date is None:
            target_date = date.today()
        
        sql = """
            INSERT INTO prize_inventory (prize_id, event_id, available_date, 
                                         initial_quantity, remaining_quantity, daily_limit)
            VALUES (:prize_id, :event_id, :date, :qty, :qty, :limit)
            ON CONFLICT (prize_id, event_id, available_date) 
            DO UPDATE SET initial_quantity = :qty, remaining_quantity = :qty, daily_limit = :limit
            RETURNING *
        """
        results = execute_sql(sql, {
            'prize_id': prize_id,
            'event_id': event_id,
            'date': target_date,
            'qty': initial_quantity,
            'limit': daily_limit
        })
        return results[0] if results else None
    
    @staticmethod
    def create_for_prize_range(prize_id, event_id=1, start_date=None, days=30,
                               initial_quantity=10, daily_limit=5):
        """Create inventory entries for a prize for multiple days"""
        if start_date is None:
            start_date = date.today()
        
        results = []
        for i in range(days):
            target_date = start_date + timedelta(days=i)
            result = Inventory.create_for_prize(
                prize_id, event_id, target_date, initial_quantity, daily_limit
            )
            if result:
                results.append(result)
        
        logger.info(f"Created {len(results)} inventory entries for prize {prize_id}")
        return results
    
    @staticmethod
    def update_quantity(prize_id, event_id=1, target_date=None, 
                        remaining_quantity=None, daily_limit=None):
        """Update inventory quantity"""
        if target_date is None:
            target_date = date.today()
        
        updates = []
        params = {'prize_id': prize_id, 'event_id': event_id, 'date': target_date}
        
        if remaining_quantity is not None:
            updates.append("remaining_quantity = :qty")
            params['qty'] = remaining_quantity
        
        if daily_limit is not None:
            updates.append("daily_limit = :limit")
            params['limit'] = daily_limit
        
        if not updates:
            return None
        
        sql = f"""
            UPDATE prize_inventory 
            SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP
            WHERE prize_id = :prize_id AND event_id = :event_id AND available_date = :date
            RETURNING *
        """
        results = execute_sql(sql, params)
        return results[0] if results else None
    
    @staticmethod
    def decrement(prize_id, event_id=1, target_date=None):
        """Atomically decrement inventory (used by consume_prize function)"""
        if target_date is None:
            target_date = date.today()
        
        sql = """
            UPDATE prize_inventory 
            SET remaining_quantity = remaining_quantity - 1,
                updated_at = CURRENT_TIMESTAMP
            WHERE prize_id = :prize_id 
              AND event_id = :event_id 
              AND available_date = :date
              AND remaining_quantity > 0
            RETURNING remaining_quantity
        """
        results = execute_sql(sql, {
            'prize_id': prize_id,
            'event_id': event_id,
            'date': target_date
        })
        
        if results:
            logger.info(f"Decremented inventory for prize {prize_id}: {results[0]['remaining_quantity']} remaining")
            return results[0]['remaining_quantity']
        return None
    
    @staticmethod
    def check_daily_limit(prize_id, target_date=None):
        """Check if daily limit has been reached"""
        if target_date is None:
            target_date = date.today()
        
        sql = """
            SELECT pi.daily_limit,
                   COALESCE(tw.wins_today, 0) as wins_today
            FROM prize_inventory pi
            LEFT JOIN (
                SELECT prize_id, COUNT(*) as wins_today
                FROM transactions
                WHERE transaction_type = 'win'
                  AND DATE(created_at) = :date
                GROUP BY prize_id
            ) tw ON pi.prize_id = tw.prize_id
            WHERE pi.prize_id = :prize_id
              AND pi.available_date = :date
        """
        results = execute_sql(sql, {'prize_id': prize_id, 'date': target_date})
        
        if results:
            return results[0]['wins_today'] < results[0]['daily_limit']
        return False
    
    @staticmethod
    def replenish(prize_id, event_id=1, target_date=None, quantity=None):
        """Replenish inventory to initial quantity or specified amount"""
        if target_date is None:
            target_date = date.today()
        
        if quantity is not None:
            sql = """
                UPDATE prize_inventory 
                SET remaining_quantity = :qty, updated_at = CURRENT_TIMESTAMP
                WHERE prize_id = :prize_id AND event_id = :event_id AND available_date = :date
                RETURNING *
            """
            params = {'qty': quantity, 'prize_id': prize_id, 'event_id': event_id, 'date': target_date}
        else:
            sql = """
                UPDATE prize_inventory 
                SET remaining_quantity = initial_quantity, updated_at = CURRENT_TIMESTAMP
                WHERE prize_id = :prize_id AND event_id = :event_id AND available_date = :date
                RETURNING *
            """
            params = {'prize_id': prize_id, 'event_id': event_id, 'date': target_date}
        
        results = execute_sql(sql, params)
        
        if results:
            logger.info(f"Replenished inventory for prize {prize_id} to {results[0]['remaining_quantity']}")
        
        return results[0] if results else None
