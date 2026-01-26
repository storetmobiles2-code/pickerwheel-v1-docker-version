"""
Inventory Service
Business logic for inventory management
"""

import logging
from datetime import date, timedelta
from ..models import Inventory, Prize

logger = logging.getLogger(__name__)


class InventoryService:
    """Service for managing prize inventory"""
    
    @staticmethod
    def get_inventory_status(event_id=1, target_date=None):
        """Get complete inventory status for a date"""
        if target_date is None:
            target_date = date.today()
        
        inventory = Inventory.get_all_for_date(event_id, target_date)
        
        # Calculate summary
        total_prizes = len(inventory)
        available = sum(1 for i in inventory if i['remaining_quantity'] > 0 and i['is_enabled'])
        out_of_stock = sum(1 for i in inventory if i['remaining_quantity'] == 0)
        disabled = sum(1 for i in inventory if not i['is_enabled'])
        
        return {
            'date': target_date.isoformat(),
            'inventory': inventory,
            'summary': {
                'total_prizes': total_prizes,
                'available': available,
                'out_of_stock': out_of_stock,
                'disabled': disabled
            }
        }
    
    @staticmethod
    def initialize_inventory_for_prize(prize_id, category_id, event_id=1, 
                                       start_date=None, days=30):
        """Initialize inventory for a new prize based on category"""
        if start_date is None:
            start_date = date.today()
        
        # Set quantities based on category
        if category_id == 1:  # ultra_rare
            initial_quantity = 2
            daily_limit = 1
        elif category_id == 2:  # rare
            initial_quantity = 5
            daily_limit = 2
        else:  # common
            initial_quantity = 10
            daily_limit = 5
        
        results = Inventory.create_for_prize_range(
            prize_id, event_id, start_date, days,
            initial_quantity, daily_limit
        )
        
        logger.info(f"Initialized inventory for prize {prize_id}: {len(results)} days")
        return results
    
    @staticmethod
    def replenish_all(event_id=1, target_date=None):
        """Replenish all inventory for a date to initial quantities"""
        if target_date is None:
            target_date = date.today()
        
        inventory = Inventory.get_all_for_date(event_id, target_date)
        
        replenished = []
        for item in inventory:
            result = Inventory.replenish(item['prize_id'], event_id, target_date)
            if result:
                replenished.append(result)
        
        logger.info(f"Replenished {len(replenished)} inventory items for {target_date}")
        return replenished
    
    @staticmethod
    def adjust_quantity(prize_id, adjustment, event_id=1, target_date=None):
        """Adjust inventory quantity by a delta"""
        if target_date is None:
            target_date = date.today()
        
        current = Inventory.get_for_prize(prize_id, event_id, target_date)
        
        if not current:
            logger.warning(f"No inventory found for prize {prize_id}")
            return None
        
        new_quantity = max(0, current['remaining_quantity'] + adjustment)
        
        return Inventory.update_quantity(
            prize_id, event_id, target_date,
            remaining_quantity=new_quantity
        )
    
    @staticmethod
    def set_quantity(prize_id, quantity, event_id=1, target_date=None):
        """Set inventory quantity to a specific value"""
        if target_date is None:
            target_date = date.today()
        
        return Inventory.update_quantity(
            prize_id, event_id, target_date,
            remaining_quantity=max(0, quantity)
        )
    
    @staticmethod
    def get_low_stock_alerts(event_id=1, target_date=None, threshold=2):
        """Get prizes with low stock"""
        if target_date is None:
            target_date = date.today()
        
        inventory = Inventory.get_all_for_date(event_id, target_date)
        
        low_stock = [
            item for item in inventory 
            if item['remaining_quantity'] <= threshold 
            and item['remaining_quantity'] > 0
            and item['is_enabled']
        ]
        
        return low_stock
