"""
Prize Scheduling Models
Daily templates, date assignments, and guaranteed wins
"""

import logging
from datetime import datetime, date
from ..database import execute_sql

logger = logging.getLogger(__name__)


class DailyPrizeTemplate:
    """Model for daily prize configuration templates"""
    
    @staticmethod
    def get_all(include_inactive=False):
        """Get all templates"""
        sql = """
            SELECT id, name, description, is_default, is_active, created_at, updated_at
            FROM daily_prize_templates
        """
        if not include_inactive:
            sql += " WHERE is_active = TRUE"
        sql += " ORDER BY is_default DESC, name ASC"
        
        return execute_sql(sql) or []
    
    @staticmethod
    def get_by_id(template_id):
        """Get template by ID with its prizes"""
        sql = """
            SELECT id, name, description, is_default, is_active, created_at, updated_at
            FROM daily_prize_templates
            WHERE id = :template_id
        """
        results = execute_sql(sql, {'template_id': template_id})
        
        if results:
            template = results[0]
            template['prizes'] = DailyPrizeTemplate.get_template_prizes(template_id)
            return template
        return None
    
    @staticmethod
    def get_default():
        """Get the default template"""
        sql = """
            SELECT id, name, description, is_default, is_active
            FROM daily_prize_templates
            WHERE is_default = TRUE AND is_active = TRUE
            LIMIT 1
        """
        results = execute_sql(sql)
        if results:
            template = results[0]
            template['prizes'] = DailyPrizeTemplate.get_template_prizes(template['id'])
            return template
        return None
    
    @staticmethod
    def get_template_prizes(template_id):
        """Get prizes for a template"""
        sql = """
            SELECT tp.id, tp.prize_id, tp.quantity, tp.daily_limit, tp.is_enabled,
                   p.name AS prize_name, p.emoji, pc.name AS category_name,
                   pc.display_name AS category_display
            FROM template_prizes tp
            JOIN prizes p ON tp.prize_id = p.id
            JOIN prize_categories pc ON p.category_id = pc.id
            WHERE tp.template_id = :template_id
            ORDER BY pc.weight ASC, p.display_order ASC
        """
        return execute_sql(sql, {'template_id': template_id}) or []
    
    @staticmethod
    def create(name, description=None, is_default=False):
        """Create a new template"""
        # If setting as default, unset current default first
        if is_default:
            execute_sql("UPDATE daily_prize_templates SET is_default = FALSE WHERE is_default = TRUE")
        
        sql = """
            INSERT INTO daily_prize_templates (name, description, is_default, is_active)
            VALUES (:name, :description, :is_default, TRUE)
            RETURNING id, name, description, is_default, is_active, created_at
        """
        results = execute_sql(sql, {
            'name': name,
            'description': description,
            'is_default': is_default
        })
        
        if results:
            logger.info(f"Created template: {name} (ID: {results[0]['id']})")
            return results[0]
        return None
    
    @staticmethod
    def update(template_id, **kwargs):
        """Update a template"""
        allowed_fields = ['name', 'description', 'is_default', 'is_active']
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields and v is not None}
        
        if not updates:
            return None
        
        # Handle setting as default
        if updates.get('is_default'):
            execute_sql("UPDATE daily_prize_templates SET is_default = FALSE WHERE is_default = TRUE")
        
        set_clauses = [f"{k} = :{k}" for k in updates.keys()]
        updates['template_id'] = template_id
        
        sql = f"""
            UPDATE daily_prize_templates
            SET {', '.join(set_clauses)}, updated_at = CURRENT_TIMESTAMP
            WHERE id = :template_id
            RETURNING id, name, description, is_default, is_active
        """
        
        results = execute_sql(sql, updates)
        return results[0] if results else None
    
    @staticmethod
    def delete(template_id):
        """Delete a template (cannot delete default)"""
        sql = """
            DELETE FROM daily_prize_templates 
            WHERE id = :template_id AND is_default = FALSE
            RETURNING id, name
        """
        results = execute_sql(sql, {'template_id': template_id})
        if results:
            logger.info(f"Deleted template: {results[0]['name']} (ID: {template_id})")
        return results[0] if results else None
    
    @staticmethod
    def clear_prizes(template_id):
        """Remove all prizes from a template"""
        sql = """
            DELETE FROM template_prizes
            WHERE template_id = :template_id
            RETURNING id
        """
        results = execute_sql(sql, {'template_id': template_id})
        count = len(results) if results else 0
        logger.info(f"Cleared {count} prizes from template {template_id}")
        return count
    
    @staticmethod
    def add_prize(template_id, prize_id, quantity=1, daily_limit=None, is_enabled=True):
        """Add a prize to a template"""
        sql = """
            INSERT INTO template_prizes (template_id, prize_id, quantity, daily_limit, is_enabled)
            VALUES (:template_id, :prize_id, :quantity, :daily_limit, :is_enabled)
            ON CONFLICT (template_id, prize_id) 
            DO UPDATE SET quantity = :quantity, daily_limit = :daily_limit, is_enabled = :is_enabled
            RETURNING id, template_id, prize_id, quantity, daily_limit, is_enabled
        """
        results = execute_sql(sql, {
            'template_id': template_id,
            'prize_id': prize_id,
            'quantity': quantity,
            'daily_limit': daily_limit,
            'is_enabled': is_enabled
        })
        return results[0] if results else None
    
    @staticmethod
    def update_prize(template_prize_id, **kwargs):
        """Update a prize in a template"""
        allowed_fields = ['quantity', 'daily_limit', 'is_enabled']
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if not updates:
            return None
        
        set_clauses = [f"{k} = :{k}" for k in updates.keys()]
        updates['id'] = template_prize_id
        
        sql = f"""
            UPDATE template_prizes
            SET {', '.join(set_clauses)}
            WHERE id = :id
            RETURNING id, template_id, prize_id, quantity, daily_limit, is_enabled
        """
        
        results = execute_sql(sql, updates)
        return results[0] if results else None
    
    @staticmethod
    def remove_prize(template_id, prize_id):
        """Remove a prize from a template"""
        sql = """
            DELETE FROM template_prizes
            WHERE template_id = :template_id AND prize_id = :prize_id
            RETURNING id
        """
        results = execute_sql(sql, {'template_id': template_id, 'prize_id': prize_id})
        return results[0] if results else None


class DateTemplateAssignment:
    """Model for assigning templates to specific dates"""
    
    @staticmethod
    def get_for_date(target_date):
        """Get template assignment for a specific date"""
        sql = """
            SELECT dta.id, dta.target_date, dta.template_id, dta.notes,
                   dpt.name AS template_name
            FROM date_template_assignments dta
            JOIN daily_prize_templates dpt ON dta.template_id = dpt.id
            WHERE dta.target_date = :target_date
        """
        results = execute_sql(sql, {'target_date': target_date})
        return results[0] if results else None
    
    @staticmethod
    def get_range(start_date, end_date):
        """Get template assignments for a date range"""
        sql = """
            SELECT dta.id, dta.target_date, dta.template_id, dta.notes,
                   dpt.name AS template_name
            FROM date_template_assignments dta
            JOIN daily_prize_templates dpt ON dta.template_id = dpt.id
            WHERE dta.target_date BETWEEN :start_date AND :end_date
            ORDER BY dta.target_date ASC
        """
        return execute_sql(sql, {'start_date': start_date, 'end_date': end_date}) or []
    
    @staticmethod
    def assign(target_date, template_id, notes=None):
        """Assign a template to a date"""
        sql = """
            INSERT INTO date_template_assignments (target_date, template_id, notes)
            VALUES (:target_date, :template_id, :notes)
            ON CONFLICT (target_date) 
            DO UPDATE SET template_id = :template_id, notes = :notes
            RETURNING id, target_date, template_id, notes
        """
        results = execute_sql(sql, {
            'target_date': target_date,
            'template_id': template_id,
            'notes': notes
        })
        if results:
            logger.info(f"Assigned template {template_id} to date {target_date}")
        return results[0] if results else None
    
    @staticmethod
    def assign_range(start_date, end_date, template_id, notes=None):
        """Assign a template to a date range"""
        from datetime import timedelta
        
        current = start_date
        results = []
        while current <= end_date:
            result = DateTemplateAssignment.assign(current, template_id, notes)
            if result:
                results.append(result)
            current += timedelta(days=1)
        
        return results
    
    @staticmethod
    def unassign(target_date):
        """Remove template assignment from a date"""
        sql = """
            DELETE FROM date_template_assignments
            WHERE target_date = :target_date
            RETURNING id, target_date, template_id
        """
        results = execute_sql(sql, {'target_date': target_date})
        return results[0] if results else None
    
    @staticmethod
    def get_effective_template(target_date):
        """Get the effective template for a date (assigned or default)"""
        sql = "SELECT get_template_for_date(:target_date) AS template_id"
        results = execute_sql(sql, {'target_date': target_date})
        
        if results and results[0]['template_id']:
            return DailyPrizeTemplate.get_by_id(results[0]['template_id'])
        return None


class GuaranteedWin:
    """Model for scheduled/guaranteed prize wins"""
    
    @staticmethod
    def get_all(status=None, limit=50):
        """Get all guaranteed wins"""
        sql = """
            SELECT gw.id, gw.prize_id, gw.scheduled_at, gw.target_identifier,
                   gw.reason, gw.status, gw.priority, gw.triggered_at,
                   gw.triggered_by_user, gw.created_by, gw.created_at,
                   gw.max_triggers, gw.triggered_count, gw.expires_at,
                   p.name AS prize_name, p.emoji AS prize_emoji,
                   pc.name AS category_name
            FROM guaranteed_wins gw
            JOIN prizes p ON gw.prize_id = p.id
            JOIN prize_categories pc ON p.category_id = pc.id
        """
        params = {}
        
        if status:
            sql += " WHERE gw.status = :status"
            params['status'] = status
        
        sql += " ORDER BY gw.status ASC, gw.priority DESC, gw.created_at DESC LIMIT :limit"
        params['limit'] = limit
        
        return execute_sql(sql, params) or []
    
    @staticmethod
    def get_pending(user_identifier=None):
        """Get pending guaranteed wins (for spin selection)"""
        sql = """
            SELECT * FROM get_pending_guaranteed_win(:user_identifier)
        """
        results = execute_sql(sql, {'user_identifier': user_identifier})
        return results[0] if results else None
    
    @staticmethod
    def get_by_id(win_id):
        """Get a guaranteed win by ID"""
        sql = """
            SELECT gw.id, gw.prize_id, gw.scheduled_at, gw.target_identifier,
                   gw.reason, gw.status, gw.priority, gw.triggered_at,
                   gw.triggered_by_user, gw.created_by, gw.created_at,
                   gw.max_triggers, gw.triggered_count, gw.expires_at,
                   p.name AS prize_name, p.emoji AS prize_emoji
            FROM guaranteed_wins gw
            JOIN prizes p ON gw.prize_id = p.id
            WHERE gw.id = :win_id
        """
        results = execute_sql(sql, {'win_id': win_id})
        return results[0] if results else None
    
    @staticmethod
    def create(prize_id, scheduled_at=None, target_identifier=None, 
               reason=None, priority=0, created_by=None,
               max_triggers=1, expires_at=None):
        """Create a guaranteed win with quantity limits"""
        sql = """
            INSERT INTO guaranteed_wins 
            (prize_id, scheduled_at, target_identifier, reason, priority, created_by, 
             max_triggers, triggered_count, expires_at, status)
            VALUES (:prize_id, :scheduled_at, :target_identifier, :reason, :priority, :created_by,
                    :max_triggers, 0, :expires_at, 'pending')
            RETURNING id, prize_id, scheduled_at, target_identifier, reason, status, priority, 
                      max_triggers, triggered_count, expires_at, created_at
        """
        results = execute_sql(sql, {
            'prize_id': prize_id,
            'scheduled_at': scheduled_at,
            'target_identifier': target_identifier,
            'reason': reason,
            'priority': priority,
            'created_by': created_by,
            'max_triggers': max_triggers,
            'expires_at': expires_at
        })
        
        if results:
            win_type = "next spin" if scheduled_at is None else f"scheduled at {scheduled_at}"
            qty_info = f"(max {max_triggers} wins)" if max_triggers else "(unlimited)"
            logger.info(f"Created guaranteed win (ID: {results[0]['id']}) - {win_type} {qty_info}")
            return results[0]
        return None
    
    @staticmethod
    def trigger(win_id, triggered_by_user=None):
        """
        Trigger a guaranteed win - increments triggered_count.
        If triggered_count >= max_triggers, marks as 'triggered' (completed).
        Otherwise, keeps status as 'pending' for future triggers.
        """
        # First, increment the triggered_count
        sql = """
            UPDATE guaranteed_wins
            SET triggered_count = triggered_count + 1,
                triggered_at = CURRENT_TIMESTAMP,
                triggered_by_user = :triggered_by,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :win_id AND status = 'pending'
            RETURNING id, prize_id, triggered_count, max_triggers, triggered_at, triggered_by_user
        """
        results = execute_sql(sql, {'win_id': win_id, 'triggered_by': triggered_by_user})
        
        if results:
            result = results[0]
            triggered_count = result.get('triggered_count', 1)
            max_triggers = result.get('max_triggers', 1)
            
            # Check if we've reached the max triggers
            if max_triggers is not None and triggered_count >= max_triggers:
                # Mark as completed (triggered)
                complete_sql = """
                    UPDATE guaranteed_wins
                    SET status = 'triggered', updated_at = CURRENT_TIMESTAMP
                    WHERE id = :win_id
                """
                execute_sql(complete_sql, {'win_id': win_id})
                logger.info(f"Guaranteed win (ID: {win_id}) completed - {triggered_count}/{max_triggers} triggers by {triggered_by_user}")
            else:
                logger.info(f"Triggered guaranteed win (ID: {win_id}) - {triggered_count}/{max_triggers or '∞'} by {triggered_by_user}")
            
            return result
        return None
    
    @staticmethod
    def cancel(win_id):
        """Cancel a guaranteed win"""
        sql = """
            UPDATE guaranteed_wins
            SET status = 'cancelled', updated_at = CURRENT_TIMESTAMP
            WHERE id = :win_id AND status = 'pending'
            RETURNING id, prize_id, status
        """
        results = execute_sql(sql, {'win_id': win_id})
        if results:
            logger.info(f"Cancelled guaranteed win (ID: {win_id})")
        return results[0] if results else None
    
    @staticmethod
    def expire_old():
        """Expire old scheduled wins that were never triggered"""
        sql = """
            UPDATE guaranteed_wins
            SET status = 'expired', updated_at = CURRENT_TIMESTAMP
            WHERE status = 'pending'
              AND scheduled_at IS NOT NULL
              AND scheduled_at < NOW() - INTERVAL '24 hours'
            RETURNING id
        """
        results = execute_sql(sql)
        count = len(results) if results else 0
        if count > 0:
            logger.info(f"Expired {count} old guaranteed wins")
        return count
    
    @staticmethod
    def update(win_id, **kwargs):
        """Update a guaranteed win (only if pending)"""
        allowed_fields = ['scheduled_at', 'target_identifier', 'reason', 'priority']
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if not updates:
            return None
        
        set_clauses = [f"{k} = :{k}" for k in updates.keys()]
        updates['win_id'] = win_id
        
        sql = f"""
            UPDATE guaranteed_wins
            SET {', '.join(set_clauses)}, updated_at = CURRENT_TIMESTAMP
            WHERE id = :win_id AND status = 'pending'
            RETURNING id, prize_id, scheduled_at, target_identifier, reason, status, priority
        """
        
        results = execute_sql(sql, updates)
        return results[0] if results else None
