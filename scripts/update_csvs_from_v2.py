#!/usr/bin/env python3
"""
[DEPRECATED] Update CSV files from itemlist_dates_v2.txt
Regenerates all daily CSV files with updated quantities and daily limits

⚠️  DEPRECATED: Please use validate_and_update_prizes.py instead
    This script is kept for backward compatibility only.
    
    Use: python3 scripts/validate_and_update_prizes.py
"""

import csv
import os
from datetime import datetime, date, timedelta
from typing import List, Dict

def parse_itemlist_v2(file_path: str) -> List[Dict]:
    """Parse the itemlist_dates_v2.txt file"""
    items = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            try:
                parts = [part.strip() for part in line.split(',')]
                if len(parts) < 6:
                    print(f"Warning: Line {line_num} has insufficient columns: {line}")
                    continue
                
                item = {
                    'id': int(parts[0]),
                    'name': parts[1],
                    'category': parts[2].lower(),
                    'quantity': int(parts[3]),
                    'daily_limit': int(parts[4]),
                    'available_dates': parts[5],
                    'emoji': parts[6] if len(parts) > 6 else '🎁',
                    'description': parts[7] if len(parts) > 7 else ''
                }
                items.append(item)
                
            except (ValueError, IndexError) as e:
                print(f"Error parsing line {line_num}: {line} - {e}")
                continue
    
    return items

def is_item_available_on_date(item: Dict, target_date: date) -> bool:
    """Check if an item is available on a specific date"""
    available_dates = item['available_dates']
    
    # If '*', available on all dates
    if available_dates == '*':
        return True
    
    # Check specific dates
    date_str = target_date.isoformat()
    return date_str in available_dates.split('|')

def generate_daily_csv(items: List[Dict], target_date: date, output_dir: str):
    """Generate a daily CSV file for a specific date"""
    date_str = target_date.isoformat()
    csv_file = os.path.join(output_dir, f'prizes_{date_str}.csv')
    
    # Filter items available on this date
    available_items = []
    for item in items:
        if is_item_available_on_date(item, target_date):
            available_items.append(item)
    
    # Write CSV file
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Write header
        writer.writerow(['Item', 'Category', 'Quantity', 'Daily Limit', 'Emoji'])
        
        # Write items
        for item in available_items:
            writer.writerow([
                item['name'],
                item['category'],
                item['quantity'],
                item['daily_limit'],
                item['emoji']
            ])
    
    print(f"Generated {csv_file} with {len(available_items)} items")

def main():
    """Main function to update all CSV files"""
    print("🔄 Updating CSV files from itemlist_dates_v2.txt")
    print("=" * 60)
    
    # Paths - handle both local and Docker environments
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    # Try multiple possible locations for itemlist_dates_v2.txt
    possible_itemlist_paths = [
        'itemlist_dates_v2.txt',  # Current directory
        os.path.join(project_root, 'itemlist_dates_v2.txt'),  # Project root
        '/app/itemlist_dates_v2.txt',  # Docker container path
        os.path.join(os.path.dirname(__file__), '..', 'itemlist_dates_v2.txt')  # Relative to script
    ]
    
    itemlist_file = None
    for path in possible_itemlist_paths:
        if os.path.exists(path):
            itemlist_file = path
            break
    
    if not itemlist_file:
        print(f"❌ Error: itemlist_dates_v2.txt not found in any of these locations:")
        for path in possible_itemlist_paths:
            print(f"   - {path}")
        return
    
    # CSV directory paths
    possible_csv_dirs = [
        'daily_csvs',
        os.path.join(project_root, 'daily_csvs'),
        '/app/daily_csvs'
    ]
    
    csv_dir = None
    for path in possible_csv_dirs:
        if os.path.exists(path) or path == '/app/daily_csvs':  # Create if it's the Docker path
            csv_dir = path
            break
    
    if not csv_dir:
        csv_dir = 'daily_csvs'  # Default fallback
    
    # Parse items
    print(f"📖 Using itemlist file: {itemlist_file}")
    print(f"📖 Using CSV directory: {csv_dir}")
    print(f"📖 Parsing {itemlist_file}...")
    items = parse_itemlist_v2(itemlist_file)
    print(f"✅ Parsed {len(items)} items")
    
    # Show updated common items
    print(f"\n📋 Updated common items:")
    common_items = [item for item in items if item['category'] == 'common']
    for item in common_items:
        print(f"  {item['name']}: quantity={item['quantity']}, daily_limit={item['daily_limit']}")
    
    # Create output directory if it doesn't exist
    os.makedirs(csv_dir, exist_ok=True)
    
    # Generate CSV files for date range (Sep 21 - Oct 30, 2025)
    start_date = date(2025, 9, 21)
    end_date = date(2025, 10, 30)
    
    print(f"\n🗓️  Generating CSV files from {start_date} to {end_date}...")
    
    current_date = start_date
    csv_count = 0
    
    while current_date <= end_date:
        generate_daily_csv(items, current_date, csv_dir)
        current_date += timedelta(days=1)
        csv_count += 1
    
    print(f"\n✅ Successfully generated {csv_count} CSV files in {csv_dir}/")
    print(f"📊 All common items now have:")
    print(f"   - Quantity: 30")
    print(f"   - Daily Limit: 5")

if __name__ == "__main__":
    main()
