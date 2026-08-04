"""
Prize Model
Handles prize CRUD operations with is_enabled support
"""

import logging
from datetime import date
from ..database import execute_sql, session_scope, execute_function
from sqlalchemy import text

logger = logging.getLogger(__name__)


class PrizeCategory:
    """Prize category model"""
    
    @staticmethod
    def get_all():
        """Get all prize categories"""
        sql = """
            SELECT id, name, display_name, weight, color, text_color, description
            FROM prize_categories
            ORDER BY weight ASC
        """
        return execute_sql(sql) or []
    
    @staticmethod
    def get_by_id(category_id):
        """Get category by ID"""
        sql = "SELECT * FROM prize_categories WHERE id = :id"
        results = execute_sql(sql, {'id': category_id})
        return results[0] if results else None


class Prize:
    """Prize model with is_enabled support"""
    
    @staticmethod
    def get_all(include_inactive=False):
        """Get all prizes"""
        sql = """
            SELECT p.id, p.name, p.category_id, pc.name as category_name,
                   pc.display_name as category_display, p.type, p.emoji,
                   p.description, p.is_active, p.is_enabled, p.display_order,
                   pc.color, pc.text_color
            FROM prizes p
            JOIN prize_categories pc ON p.category_id = pc.id
        """
        if not include_inactive:
            sql += " WHERE p.is_active = TRUE"
        sql += " ORDER BY p.display_order ASC, p.id ASC"
        
        return execute_sql(sql) or []
    
    @staticmethod
    def get_by_id(prize_id):
        """Get prize by ID"""
        sql = """
            SELECT p.id, p.name, p.category_id, pc.name as category_name,
                   pc.display_name as category_display, p.type, p.emoji,
                   p.description, p.is_active, p.is_enabled, p.display_order,
                   pc.color, pc.text_color
            FROM prizes p
            JOIN prize_categories pc ON p.category_id = pc.id
            WHERE p.id = :id
        """
        results = execute_sql(sql, {'id': prize_id})
        return results[0] if results else None
    
    @staticmethod
    def get_for_wheel_display(event_id=1, target_date=None):
        """Get all active prizes for wheel display (including disabled)"""
        if target_date is None:
            target_date = date.today()
        
        results = execute_function('get_wheel_display_prizes', event_id, target_date)
        return results or []
    
    @staticmethod
    def get_available_for_spin(event_id=1, target_date=None):
        """Get prizes that can be won (enabled + has inventory)"""
        if target_date is None:
            target_date = date.today()
        
        results = execute_function('get_available_prizes', event_id, target_date)
        return results or []
    
    @staticmethod
    def create(name, category_id, emoji='🎁', description=None, display_order=0):
        """Create a new prize"""
        sql = """
            INSERT INTO prizes (name, category_id, emoji, description, display_order, is_active, is_enabled)
            VALUES (:name, :category_id, :emoji, :description, :display_order, TRUE, TRUE)
            RETURNING id, name, category_id, emoji, description, is_active, is_enabled, display_order
        """
        results = execute_sql(sql, {
            'name': name,
            'category_id': category_id,
            'emoji': emoji,
            'description': description,
            'display_order': display_order
        })
        
        if results:
            logger.info(f"Created prize: {name} (ID: {results[0]['id']})")
            
            # Log to audit
            execute_sql("""
                INSERT INTO audit_log (action, entity_type, entity_id, new_value, performed_by)
                VALUES ('create', 'prize', :id, :data, 'admin')
            """, {
                'id': results[0]['id'],
                'data': f'{{"name": "{name}", "category_id": {category_id}}}'
            })
            
            return results[0]
        return None
    
    @staticmethod
    def update(prize_id, **kwargs):
        """Update a prize"""
        allowed_fields = ['name', 'category_id', 'emoji', 'description', 'display_order', 'is_enabled']
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if not updates:
            return None
        
        set_clause = ', '.join([f"{k} = :{k}" for k in updates.keys()])
        updates['id'] = prize_id
        
        sql = f"""
            UPDATE prizes SET {set_clause}, updated_at = CURRENT_TIMESTAMP
            WHERE id = :id
            RETURNING id, name, category_id, emoji, description, is_active, is_enabled, display_order
        """
        
        results = execute_sql(sql, updates)
        if results:
            logger.info(f"Updated prize {prize_id}: {updates}")
        return results[0] if results else None
    
    @staticmethod
    def toggle_enabled(prize_id, is_enabled):
        """Toggle the is_enabled flag for a prize"""
        sql = """
            UPDATE prizes SET is_enabled = :is_enabled, updated_at = CURRENT_TIMESTAMP
            WHERE id = :id AND is_active = TRUE
            RETURNING id, name, is_enabled
        """
        results = execute_sql(sql, {'id': prize_id, 'is_enabled': is_enabled})
        
        if results:
            logger.info(f"Prize {prize_id} enabled={is_enabled}")
            
            # Log to audit
            execute_sql("""
                INSERT INTO audit_log (action, entity_type, entity_id, new_value, performed_by)
                VALUES ('toggle_enabled', 'prize', :id, :data, 'admin')
            """, {
                'id': prize_id,
                'data': f'{{"is_enabled": {str(is_enabled).lower()}}}'
            })
        
        return results[0] if results else None
    
    @staticmethod
    def delete(prize_id):
        """Soft delete a prize (set is_active = FALSE)"""
        sql = """
            UPDATE prizes SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP
            WHERE id = :id
            RETURNING id, name
        """
        results = execute_sql(sql, {'id': prize_id})
        
        if results:
            logger.info(f"Deleted prize: {results[0]['name']} (ID: {prize_id})")
            
            # Log to audit
            execute_sql("""
                INSERT INTO audit_log (action, entity_type, entity_id, old_value, performed_by)
                VALUES ('delete', 'prize', :id, :data, 'admin')
            """, {
                'id': prize_id,
                'data': f'{{"name": "{results[0]["name"]}"}}'
            })
        
        return results[0] if results else None
    
    @staticmethod
    def hard_delete(prize_id):
        """Permanently delete a prize (use with caution)"""
        # First delete related inventory
        execute_sql("DELETE FROM prize_inventory WHERE prize_id = :id", {'id': prize_id})
        
        sql = "DELETE FROM prizes WHERE id = :id RETURNING id, name"
        results = execute_sql(sql, {'id': prize_id})
        
        if results:
            logger.info(f"Hard deleted prize: {results[0]['name']} (ID: {prize_id})")
        
        return results[0] if results else None
