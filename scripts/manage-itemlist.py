#!/usr/bin/env python3
"""
Item List Manager for PickerWheel Contest
Helps users manage the itemlist_dates.txt file
"""

import os
import sys
import csv
from datetime import datetime, date
from typing import List, Dict

class ItemListManager:
    def __init__(self, itemlist_path: str = None):
        if itemlist_path is None:
            # Try to find the itemlist file
            possible_paths = [
                'itemlist_dates.txt',
                '../itemlist_dates.txt',
                '/app/itemlist_dates.txt'
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    itemlist_path = path
                    break
        
        if not itemlist_path or not os.path.exists(itemlist_path):
            raise FileNotFoundError(f"Itemlist file not found. Tried: {possible_paths}")
        
        self.itemlist_path = itemlist_path
        self.items = []
        self.load_items()
    
    def load_items(self):
        """Load items from itemlist_dates.txt"""
        self.items = []
        
        with open(self.itemlist_path, 'r', encoding='utf-8') as file:
            lines = [line.strip() for line in file if line.strip() and not line.strip().startswith('#')]
            
            # Skip header line
            if lines and lines[0].startswith('Item,'):
                lines = lines[1:]
            
            for i, line in enumerate(lines):
                if not line:
                    continue
                    
                parts = line.split(',')
                if len(parts) >= 5:
                    item_name = parts[0].strip()
                    category = parts[1].strip()
                    quantity = parts[2].strip()
                    daily_limit = parts[3].strip()
                    available_dates = parts[4].strip()
                    
                    self.items.append({
                        'id': i + 1,
                        'name': item_name,
                        'category': category,
                        'quantity': quantity,
                        'daily_limit': daily_limit,
                        'available_dates': available_dates
                    })
    
    def save_items(self):
        """Save items back to itemlist_dates.txt"""
        with open(self.itemlist_path, 'w', encoding='utf-8') as file:
            file.write('Item,Category,Quantity,Daily Limit,Available Dates\n\n')
            
            # Group items by category
            categories = {}
            for item in self.items:
                cat = item['category']
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(item)
            
            # Write items grouped by category
            for category, items in categories.items():
                file.write(f'# {category} Items\n')
                for item in items:
                    file.write(f"{item['name']},{item['category']},{item['quantity']},{item['daily_limit']},{item['available_dates']}\n")
                file.write('\n')
    
    def list_items(self):
        """List all items"""
        print(f"📋 Items in {self.itemlist_path}")
        print("=" * 50)
        
        categories = {}
        for item in self.items:
            cat = item['category']
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(item)
        
        for category, items in categories.items():
            print(f"\n{category} Items ({len(items)}):")
            for item in items:
                print(f"  {item['id']:2d}. {item['name']}")
                print(f"      Quantity: {item['quantity']}, Daily Limit: {item['daily_limit']}")
                print(f"      Available: {item['available_dates']}")
    
    def add_item(self, name: str, category: str, quantity: str, daily_limit: str, available_dates: str = "*"):
        """Add a new item"""
        new_item = {
            'id': len(self.items) + 1,
            'name': name,
            'category': category,
            'quantity': quantity,
            'daily_limit': daily_limit,
            'available_dates': available_dates
        }
        self.items.append(new_item)
        print(f"✅ Added item: {name}")
    
    def update_item(self, item_id: int, **kwargs):
        """Update an existing item"""
        if item_id < 1 or item_id > len(self.items):
            print(f"❌ Invalid item ID: {item_id}")
            return
        
        item = self.items[item_id - 1]
        for key, value in kwargs.items():
            if key in item:
                old_value = item[key]
                item[key] = value
                print(f"✅ Updated {key}: '{old_value}' → '{value}'")
    
    def delete_item(self, item_id: int):
        """Delete an item"""
        if item_id < 1 or item_id > len(self.items):
            print(f"❌ Invalid item ID: {item_id}")
            return
        
        item = self.items.pop(item_id - 1)
        print(f"✅ Deleted item: {item['name']}")
        
        # Update IDs
        for i, remaining_item in enumerate(self.items):
            remaining_item['id'] = i + 1
    
    def check_availability(self, target_date: str = None):
        """Check which items are available on a specific date"""
        if target_date is None:
            target_date = date.today().isoformat()
        
        print(f"📅 Items available on {target_date}")
        print("=" * 40)
        
        available_items = []
        for item in self.items:
            if self.is_item_available_on_date(item, target_date):
                available_items.append(item)
        
        if not available_items:
            print("❌ No items available on this date")
            return
        
        categories = {}
        for item in available_items:
            cat = item['category']
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(item)
        
        for category, items in categories.items():
            print(f"\n{category} ({len(items)}):")
            for item in items:
                print(f"  • {item['name']} (Limit: {item['daily_limit']}/day)")
    
    def is_item_available_on_date(self, item: Dict, target_date: str) -> bool:
        """Check if an item is available on a specific date"""
        available_dates = item['available_dates']
        
        # If "*", item is available on all days
        if available_dates == '*':
            return True
        
        # Check if target date is in the available dates list
        available_date_list = [d.strip() for d in available_dates.split('|')]
        return target_date in available_date_list
    
    def validate_itemlist(self):
        """Validate the itemlist for common issues"""
        print("🔍 Validating itemlist...")
        print("=" * 30)
        
        issues = []
        
        # Check for duplicate names
        names = [item['name'] for item in self.items]
        duplicates = set([name for name in names if names.count(name) > 1])
        if duplicates:
            issues.append(f"Duplicate item names: {', '.join(duplicates)}")
        
        # Check for invalid quantities
        for item in self.items:
            if not item['quantity'].isdigit():
                issues.append(f"Invalid quantity for '{item['name']}': {item['quantity']}")
            if not item['daily_limit'].isdigit():
                issues.append(f"Invalid daily limit for '{item['name']}': {item['daily_limit']}")
        
        # Check for empty names
        for item in self.items:
            if not item['name'].strip():
                issues.append(f"Empty item name at ID {item['id']}")
        
        if issues:
            print("❌ Issues found:")
            for issue in issues:
                print(f"  • {issue}")
        else:
            print("✅ No issues found")
        
        return len(issues) == 0

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 manage-itemlist.py [command] [options]")
        print("")
        print("Commands:")
        print("  list                    - List all items")
        print("  add <name> <category> <quantity> <daily_limit> [dates] - Add new item")
        print("  update <id> <field> <value> - Update item field")
        print("  delete <id>             - Delete item")
        print("  check [date]            - Check availability for date")
        print("  validate                - Validate itemlist")
        print("  backup                  - Create backup of itemlist")
        print("")
        print("Examples:")
        print("  python3 manage-itemlist.py list")
        print("  python3 manage-itemlist.py add 'New Prize' 'Common' '50' '10' '*'")
        print("  python3 manage-itemlist.py update 1 name 'Updated Prize'")
        print("  python3 manage-itemlist.py check 2025-10-02")
        return
    
    try:
        manager = ItemListManager()
        command = sys.argv[1].lower()
        
        if command == 'list':
            manager.list_items()
        
        elif command == 'add':
            if len(sys.argv) < 6:
                print("❌ Usage: add <name> <category> <quantity> <daily_limit> [dates]")
                return
            
            name = sys.argv[2]
            category = sys.argv[3]
            quantity = sys.argv[4]
            daily_limit = sys.argv[5]
            available_dates = sys.argv[6] if len(sys.argv) > 6 else "*"
            
            manager.add_item(name, category, quantity, daily_limit, available_dates)
            manager.save_items()
        
        elif command == 'update':
            if len(sys.argv) < 5:
                print("❌ Usage: update <id> <field> <value>")
                return
            
            item_id = int(sys.argv[2])
            field = sys.argv[3]
            value = sys.argv[4]
            
            manager.update_item(item_id, **{field: value})
            manager.save_items()
        
        elif command == 'delete':
            if len(sys.argv) < 3:
                print("❌ Usage: delete <id>")
                return
            
            item_id = int(sys.argv[2])
            manager.delete_item(item_id)
            manager.save_items()
        
        elif command == 'check':
            target_date = sys.argv[2] if len(sys.argv) > 2 else None
            manager.check_availability(target_date)
        
        elif command == 'validate':
            manager.validate_itemlist()
        
        elif command == 'backup':
            backup_path = f"{manager.itemlist_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            import shutil
            shutil.copy2(manager.itemlist_path, backup_path)
            print(f"✅ Backup created: {backup_path}")
        
        else:
            print(f"❌ Unknown command: {command}")
    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
