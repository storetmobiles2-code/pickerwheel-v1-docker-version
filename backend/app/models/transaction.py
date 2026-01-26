"""
Transaction Model
Records all prize wins and adjustments
"""

import logging
from datetime import date, datetime
from ..database import execute_sql

logger = logging.getLogger(__name__)


class Transaction:
    """Transaction model for recording wins and adjustments"""
    
    @staticmethod
    def create(prize_id, user_identifier=None, transaction_type='win', 
               quantity=1, metadata=None):
        """Create a new transaction"""
        sql = """
            INSERT INTO transactions (prize_id, user_identifier, transaction_type, quantity, metadata)
            VALUES (:prize_id, :user_id, :type, :qty, :metadata::jsonb)
            RETURNING id, prize_id, user_identifier, transaction_type, quantity, created_at
        """
        results = execute_sql(sql, {
            'prize_id': prize_id,
            'user_id': user_identifier,
            'type': transaction_type,
            'qty': quantity,
            'metadata': metadata or '{}'
        })
        
        if results:
            logger.info(f"Transaction created: {transaction_type} for prize {prize_id}")
        
        return results[0] if results else None
    
    @staticmethod
    def get_by_id(transaction_id):
        """Get transaction by ID"""
        sql = """
            SELECT t.id, t.prize_id, t.user_identifier, t.transaction_type,
                   t.quantity, t.metadata, t.created_at,
                   p.name as prize_name, p.emoji, pc.name as category_name
            FROM transactions t
            JOIN prizes p ON t.prize_id = p.id
            JOIN prize_categories pc ON p.category_id = pc.id
            WHERE t.id = :id
        """
        results = execute_sql(sql, {'id': transaction_id})
        return results[0] if results else None
    
    @staticmethod
    def get_for_date(target_date=None, transaction_type=None, limit=100):
        """Get transactions for a specific date"""
        if target_date is None:
            target_date = date.today()
        
        sql = """
            SELECT t.id, t.prize_id, t.user_identifier, t.transaction_type,
                   t.quantity, t.metadata, t.created_at,
                   p.name as prize_name, p.emoji, pc.name as category_name,
                   pc.display_name as category_display
            FROM transactions t
            JOIN prizes p ON t.prize_id = p.id
            JOIN prize_categories pc ON p.category_id = pc.id
            WHERE DATE(t.created_at) = :date
        """
        params = {'date': target_date, 'limit': limit}
        
        if transaction_type:
            sql += " AND t.transaction_type = :type"
            params['type'] = transaction_type
        
        sql += " ORDER BY t.created_at DESC LIMIT :limit"
        
        return execute_sql(sql, params) or []
    
    @staticmethod
    def get_wins_for_date(target_date=None, limit=100):
        """Get win transactions for a specific date"""
        return Transaction.get_for_date(target_date, 'win', limit)
    
    @staticmethod
    def get_recent(limit=50):
        """Get most recent transactions"""
        sql = """
            SELECT t.id, t.prize_id, t.user_identifier, t.transaction_type,
                   t.quantity, t.metadata, t.created_at,
                   p.name as prize_name, p.emoji, pc.name as category_name
            FROM transactions t
            JOIN prizes p ON t.prize_id = p.id
            JOIN prize_categories pc ON p.category_id = pc.id
            ORDER BY t.created_at DESC
            LIMIT :limit
        """
        return execute_sql(sql, {'limit': limit}) or []
    
    @staticmethod
    def get_stats_for_date(target_date=None):
        """Get transaction statistics for a date"""
        if target_date is None:
            target_date = date.today()
        
        sql = """
            SELECT 
                COUNT(*) as total_transactions,
                COUNT(*) FILTER (WHERE t.transaction_type = 'win') as total_wins,
                COUNT(DISTINCT t.user_identifier) as unique_users
            FROM transactions t
            WHERE DATE(t.created_at) = :date
        """
        results = execute_sql(sql, {'date': target_date})
        return results[0] if results else {'total_transactions': 0, 'total_wins': 0, 'unique_users': 0}
    
    @staticmethod
    def get_wins_by_category(target_date=None):
        """Get win counts by category for a date"""
        if target_date is None:
            target_date = date.today()
        
        sql = """
            SELECT pc.name as category_name, pc.display_name, COUNT(*) as win_count
            FROM transactions t
            JOIN prizes p ON t.prize_id = p.id
            JOIN prize_categories pc ON p.category_id = pc.id
            WHERE t.transaction_type = 'win'
              AND DATE(t.created_at) = :date
            GROUP BY pc.id, pc.name, pc.display_name
            ORDER BY pc.weight ASC
        """
        return execute_sql(sql, {'date': target_date}) or []
    
    @staticmethod
    def get_wins_today_for_prize(prize_id, target_date=None):
        """Get number of wins today for a specific prize"""
        if target_date is None:
            target_date = date.today()
        
        sql = """
            SELECT COUNT(*) as wins_today
            FROM transactions
            WHERE prize_id = :prize_id
              AND transaction_type = 'win'
              AND DATE(created_at) = :date
        """
        results = execute_sql(sql, {'prize_id': prize_id, 'date': target_date})
        return results[0]['wins_today'] if results else 0
    
    @staticmethod
    def get_user_wins(user_identifier, target_date=None, limit=10):
        """Get wins for a specific user"""
        sql = """
            SELECT t.id, t.prize_id, t.created_at,
                   p.name as prize_name, p.emoji, pc.name as category_name
            FROM transactions t
            JOIN prizes p ON t.prize_id = p.id
            JOIN prize_categories pc ON p.category_id = pc.id
            WHERE t.user_identifier = :user_id
              AND t.transaction_type = 'win'
        """
        params = {'user_id': user_identifier, 'limit': limit}
        
        if target_date:
            sql += " AND DATE(t.created_at) = :date"
            params['date'] = target_date
        
        sql += " ORDER BY t.created_at DESC LIMIT :limit"
        
        return execute_sql(sql, params) or []
    
    @staticmethod
    def get_today_wins(target_date=None, limit=100):
        """Get today's wins formatted for display"""
        if target_date is None:
            target_date = date.today()
        
        sql = """
            SELECT t.id, t.prize_id, t.user_identifier, t.created_at,
                   p.name, p.emoji, pc.name as category,
                   TO_CHAR(t.created_at, 'HH24:MI:SS') as formatted_time
            FROM transactions t
            JOIN prizes p ON t.prize_id = p.id
            JOIN prize_categories pc ON p.category_id = pc.id
            WHERE t.transaction_type = 'win'
              AND DATE(t.created_at) = :date
            ORDER BY t.created_at DESC
            LIMIT :limit
        """
        return execute_sql(sql, {'date': target_date, 'limit': limit}) or []
