"""
Special Event Model
For festival/promotional prize activations with date-time criteria
"""

import logging
from datetime import datetime
from ..database import execute_sql

logger = logging.getLogger(__name__)


class SpecialEvent:
    """Model for time-bound promotional events like festivals"""
    
    @staticmethod
    def create(name, start_datetime, end_datetime, event_type='promotion', description=None):
        """Create a new special event"""
        sql = """
            INSERT INTO special_events (name, description, event_type, start_datetime, end_datetime)
            VALUES (:name, :description, :event_type, :start_dt, :end_dt)
            RETURNING id, name, description, event_type, start_datetime, end_datetime, is_active, created_at
        """
        results = execute_sql(sql, {
            'name': name,
            'description': description,
            'event_type': event_type,
            'start_dt': start_datetime,
            'end_dt': end_datetime
        })
        
        if results:
            logger.info(f"Special event created: {name} (ID: {results[0]['id']})")
            return results[0]
        return None
    
    @staticmethod
    def get_by_id(event_id):
        """Get special event by ID with associated prizes"""
        sql = """
            SELECT se.id, se.name, se.description, se.event_type,
                   se.start_datetime, se.end_datetime, se.is_active, 
                   se.theme_config, se.created_at
            FROM special_events se
            WHERE se.id = :event_id
        """
        results = execute_sql(sql, {'event_id': event_id})
        
        if results:
            event = results[0]
            event['prizes'] = SpecialEvent.get_event_prizes(event_id)
            return event
        return None
    
    @staticmethod
    def get_all(include_inactive=False):
        """Get all special events"""
        sql = """
            SELECT se.id, se.name, se.description, se.event_type,
                   se.start_datetime, se.end_datetime, se.is_active, 
                   se.theme_config, se.created_at
            FROM special_events se
        """
        
        if not include_inactive:
            sql += " WHERE se.is_active = TRUE"
        
        sql += " ORDER BY se.start_datetime DESC"
        
        return execute_sql(sql) or []
    
    @staticmethod
    def get_active_now():
        """Get currently active special events (within datetime range)"""
        sql = """
            SELECT se.id, se.name, se.description, se.event_type,
                   se.start_datetime, se.end_datetime, se.is_active,
                   se.theme_config
            FROM special_events se
            WHERE se.is_active = TRUE
              AND se.start_datetime <= NOW()
              AND se.end_datetime >= NOW()
            ORDER BY se.start_datetime ASC
        """
        events = execute_sql(sql) or []
        
        # Load prizes for each active event
        for event in events:
            event['prizes'] = SpecialEvent.get_event_prizes(event['id'])
        
        return events
    
    @staticmethod
    def get_event_prizes(event_id):
        """Get prizes associated with a special event"""
        sql = """
            SELECT sep.id, sep.prize_id, sep.boost_enabled, sep.weight_multiplier,
                   sep.quantity_override, p.name as prize_name, p.emoji,
                   pc.name as category_name, pc.display_name as category_display
            FROM special_event_prizes sep
            JOIN prizes p ON sep.prize_id = p.id
            JOIN prize_categories pc ON p.category_id = pc.id
            WHERE sep.special_event_id = :event_id
            ORDER BY pc.weight ASC, p.display_order ASC
        """
        return execute_sql(sql, {'event_id': event_id}) or []
    
    @staticmethod
    def add_prize(event_id, prize_id, boost_enabled=True, weight_multiplier=1.5, quantity_override=None):
        """Add a prize to a special event"""
        sql = """
            INSERT INTO special_event_prizes (special_event_id, prize_id, boost_enabled, weight_multiplier, quantity_override)
            VALUES (:event_id, :prize_id, :boost_enabled, :multiplier, :qty_override)
            ON CONFLICT (special_event_id, prize_id) 
            DO UPDATE SET boost_enabled = :boost_enabled, 
                          weight_multiplier = :multiplier,
                          quantity_override = :qty_override
            RETURNING id, special_event_id, prize_id, boost_enabled, weight_multiplier, quantity_override
        """
        results = execute_sql(sql, {
            'event_id': event_id,
            'prize_id': prize_id,
            'boost_enabled': boost_enabled,
            'multiplier': weight_multiplier,
            'qty_override': quantity_override
        })
        
        if results:
            logger.info(f"Prize {prize_id} added to special event {event_id}")
        return results[0] if results else None
    
    @staticmethod
    def remove_prize(event_id, prize_id):
        """Remove a prize from a special event"""
        sql = """
            DELETE FROM special_event_prizes
            WHERE special_event_id = :event_id AND prize_id = :prize_id
            RETURNING id
        """
        results = execute_sql(sql, {'event_id': event_id, 'prize_id': prize_id})
        
        if results:
            logger.info(f"Prize {prize_id} removed from special event {event_id}")
        return results[0] if results else None
    
    @staticmethod
    def update(event_id, **kwargs):
        """Update a special event"""
        allowed_fields = ['name', 'description', 'event_type', 'start_datetime', 
                          'end_datetime', 'is_active', 'theme_config']
        
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields and v is not None}
        
        if not updates:
            return None
        
        set_clauses = [f"{k} = :{k}" for k in updates.keys()]
        updates['event_id'] = event_id
        updates['now'] = datetime.now()
        
        sql = f"""
            UPDATE special_events
            SET {', '.join(set_clauses)}, updated_at = :now
            WHERE id = :event_id
            RETURNING id, name, description, event_type, start_datetime, end_datetime, is_active, theme_config
        """
        
        results = execute_sql(sql, updates)
        return results[0] if results else None
    
    @staticmethod
    def update_theme_config(event_id, theme_config):
        """Update theme configuration for an event"""
        import json
        sql = """
            UPDATE special_events
            SET theme_config = :theme_config, updated_at = :now
            WHERE id = :event_id
            RETURNING id, name, theme_config
        """
        results = execute_sql(sql, {
            'event_id': event_id,
            'theme_config': json.dumps(theme_config) if isinstance(theme_config, dict) else theme_config,
            'now': datetime.now()
        })
        
        if results:
            logger.info(f"Theme config updated for event {event_id}")
        return results[0] if results else None
    
    @staticmethod
    def delete(event_id):
        """Delete a special event (and all associated prize links)"""
        sql = """
            DELETE FROM special_events WHERE id = :event_id
            RETURNING id, name
        """
        results = execute_sql(sql, {'event_id': event_id})
        
        if results:
            logger.info(f"Special event deleted: {results[0]['name']} (ID: {event_id})")
        return results[0] if results else None
    
    @staticmethod
    def toggle_active(event_id, is_active):
        """Toggle active status of a special event"""
        return SpecialEvent.update(event_id, is_active=is_active)
    
    @staticmethod
    def get_boosted_prize_ids():
        """Get list of prize IDs with active boosts right now"""
        sql = """
            SELECT DISTINCT sep.prize_id, sep.weight_multiplier
            FROM special_event_prizes sep
            JOIN special_events se ON sep.special_event_id = se.id
            WHERE se.is_active = TRUE
              AND se.start_datetime <= NOW()
              AND se.end_datetime >= NOW()
              AND sep.boost_enabled = TRUE
        """
        return execute_sql(sql) or []
