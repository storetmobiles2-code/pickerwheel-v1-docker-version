#!/usr/bin/env python3
"""
Validate itemlist_dates.txt, check for duplicates, generate CSVs, and update database
"""

import csv
import os
import sqlite3
from datetime import date, timedelta
from typing import List, Dict, Set
from collections import defaultdict

# Configuration
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ITEMLIST_FILE = os.path.join(PROJECT_ROOT, 'itemlist_dates.txt')
CSV_DIR = os.path.join(PROJECT_ROOT, 'daily_csvs')
DB_PATH = os.path.join(PROJECT_ROOT, 'backend', 'pickerwheel_contest.db')

# Emoji mapping for prizes
EMOJI_MAP = {
    'tv': '📺',
    'television': '📺',
    'phone': '📱',
    'mobile': '📱',
    'smartphone': '📱',
    'tab': '📱',
    'tablet': '📱',
    'watch': '⌚',
    'smartwatch': '⌚',
    'speaker': '🔊',
    'soundbar': '🔊',
    'theatre': '🎭',
    'theater': '🎭',
    'earphone': '🎧',
    'earbud': '🎧',
    'headphone': '🎧',
    'bag': '🧳',
    'luggage': '🧳',
    'power bank': '🔋',
    'battery': '🔋',
    'cooker': '🍳',
    'stove': '🔥',
    'gas': '🔥',
    'mixer': '🥤',
    'grinder': '🥤',
    'dinner set': '🍽️',
    'plate': '🍽️',
    'refrigerator': '🧊',
    'fridge': '🧊',
    'washing machine': '🧺',
    'washer': '🧺',
    'cooler': '❄️',
    'air cooler': '❄️',
    'coin': '🪙',
    'silver': '🪙',
    'gold': '🪙',
    'screen guard': '📱',
    'pouch': '👝',
    'stick': '🤳',
    'selfie': '🤳',
}

def get_emoji_for_prize(name: str) -> str:
    """Get appropriate emoji for prize based on name"""
    name_lower = name.lower()
    for keyword, emoji in EMOJI_MAP.items():
        if keyword in name_lower:
            return emoji
    return '🎁'  # Default gift emoji


def parse_itemlist(file_path: str) -> Dict[str, List[Dict]]:
    """Parse itemlist_dates.txt and return items by category"""
    items = {
        'common': [],
        'rare': []
    }
    
    current_section = None
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            
            # Skip header line
            if line.startswith('Item,Category'):
                continue
            
            # Skip empty lines
            if not line:
                continue
            
            # Detect section headers
            if line.startswith('#'):
                if 'Common' in line:
                    current_section = 'common'
                elif 'Rare' in line:
                    current_section = 'rare'
                continue
            
            # Parse item line
            parts = [part.strip() for part in line.split(',')]
            if len(parts) < 5:
                continue
            
            item = {
                'name': parts[0],
                'category': parts[1].lower(),
                'quantity': int(parts[2]) if parts[2].isdigit() else 0,
                'daily_limit': int(parts[3]) if parts[3].isdigit() else 1,
                'available_dates': parts[4],
                'line_num': line_num
            }
            
            if current_section:
                items[current_section].append(item)
    
    return items


def check_duplicates(items: Dict[str, List[Dict]]) -> Dict[str, List[str]]:
    """Check for duplicate items - returns items that appear in both common and rare"""
    dual_items = defaultdict(list)
    
    # Collect all item names (case-insensitive)
    all_items = {}
    
    for category, item_list in items.items():
        for item in item_list:
            name_lower = item['name'].lower()
            if name_lower in all_items:
                dual_items[name_lower].append({
                    'name': item['name'],
                    'category': category,
                    'line': item['line_num'],
                    'dates': item['available_dates']
                })
                # Add the original item too if it's the first duplicate
                if len(dual_items[name_lower]) == 1:
                    orig = all_items[name_lower]
                    dual_items[name_lower].insert(0, {
                        'name': orig['name'],
                        'category': orig['category'],
                        'line': orig['line_num'],
                        'dates': orig['dates']
                    })
            else:
                all_items[name_lower] = {
                    'name': item['name'],
                    'category': category,
                    'line_num': item['line_num'],
                    'dates': item['available_dates']
                }
    
    return dual_items


def get_deduplicated_count(items: Dict[str, List[Dict]]) -> int:
    """Get the count of unique items after deduplication (as shown on wheel)"""
    seen_names = set()
    
    # Add common items first
    for item in items['common']:
        seen_names.add(item['name'].lower().strip())
    
    # Add rare items only if not already present
    for item in items['rare']:
        seen_names.add(item['name'].lower().strip())
    
    return len(seen_names)


def list_all_unique_items(items: Dict[str, List[Dict]]) -> List[str]:
    """Get all unique items (case-insensitive)"""
    unique = set()
    for category, item_list in items.items():
        for item in item_list:
            unique.add(item['name'].lower())
    return sorted(list(unique))


def is_item_available_on_date(item: Dict, target_date: date) -> bool:
    """Check if an item is available on a specific date"""
    available_dates = item['available_dates']
    
    # If '*', available on all dates
    if available_dates == '*':
        return True
    
    # Check specific dates
    date_str = target_date.isoformat()
    return date_str in available_dates.split('|')


def generate_daily_csv(items: Dict[str, List[Dict]], target_date: date, output_dir: str):
    """Generate a daily CSV file for a specific date"""
    date_str = target_date.isoformat()
    csv_file = os.path.join(output_dir, f'prizes_{date_str}.csv')
    
    # Include ALL items in the CSV (for display on wheel)
    # Backend will enforce date restrictions for rare items
    available_items = []
    
    for category in ['common', 'rare']:
        for item in items[category]:
            # Add all items to display on wheel
            item_data = {
                **item,
                'emoji': get_emoji_for_prize(item['name']),
                'available_today': is_item_available_on_date(item, target_date)
            }
            available_items.append(item_data)
    
    # Write CSV file
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Write header - include available_date for backend validation
        writer.writerow(['Item', 'Category', 'Quantity', 'Daily Limit', 'Emoji', 'Available_Dates'])
        
        # Write items
        for item in available_items:
            writer.writerow([
                item['name'],
                item['category'],
                item['quantity'],
                item['daily_limit'],
                item['emoji'],
                item['available_dates']
            ])
    
    return len(available_items)


def cleanup_old_csvs(csv_dir: str, cutoff_date: date):
    """Remove CSV files older than cutoff date"""
    removed = []
    
    if not os.path.exists(csv_dir):
        return removed
    
    for filename in os.listdir(csv_dir):
        if filename.startswith('prizes_') and filename.endswith('.csv'):
            try:
                # Extract date from filename
                date_str = filename.replace('prizes_', '').replace('.csv', '')
                file_date = date.fromisoformat(date_str)
                
                if file_date < cutoff_date:
                    file_path = os.path.join(csv_dir, filename)
                    os.remove(file_path)
                    removed.append(filename)
            except Exception as e:
                print(f"⚠️  Error processing {filename}: {e}")
    
    return removed


def update_database(items: Dict[str, List[Dict]], db_path: str):
    """Update the database with new prizes"""
    if not os.path.exists(db_path):
        print(f"⚠️  Database not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get category IDs
        cursor.execute("SELECT id, name FROM prize_categories")
        categories = {row[1]: row[0] for row in cursor.fetchall()}
        
        # Common = category_id 3, Rare = category_id 2
        common_cat_id = categories.get('common', 3)
        rare_cat_id = categories.get('rare', 2)
        
        # Clear existing data
        cursor.execute("DELETE FROM prize_inventory")
        cursor.execute("DELETE FROM combo_items")
        cursor.execute("DELETE FROM prizes")
        
        # Reset auto-increment
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='prizes'")
        
        # Insert prizes
        prize_id = 1
        
        # Insert common items
        for item in items['common']:
            cursor.execute("""
                INSERT INTO prizes (id, name, category_id, type, emoji, is_premium, is_active)
                VALUES (?, ?, ?, 'single', ?, 0, 1)
            """, (
                prize_id,
                item['name'],
                common_cat_id,
                get_emoji_for_prize(item['name'])
            ))
            prize_id += 1
        
        # Insert rare items
        for item in items['rare']:
            cursor.execute("""
                INSERT INTO prizes (id, name, category_id, type, emoji, is_premium, is_active)
                VALUES (?, ?, ?, 'single', ?, 1, 1)
            """, (
                prize_id,
                item['name'],
                rare_cat_id,
                get_emoji_for_prize(item['name'])
            ))
            
            # Add to prize_inventory for the specific date
            if item['available_dates'] != '*':
                dates = item['available_dates'].split('|')
                for date_str in dates:
                    cursor.execute("""
                        INSERT INTO prize_inventory 
                        (prize_id, event_id, available_date, initial_quantity, remaining_quantity, per_day_limit)
                        VALUES (?, 1, ?, ?, ?, ?)
                    """, (
                        prize_id,
                        date_str,
                        item['quantity'],
                        item['quantity'],
                        item['daily_limit']
                    ))
            
            prize_id += 1
        
        conn.commit()
        conn.close()
        
        print(f"   ✅ Database updated with {prize_id - 1} prizes")
        return True
        
    except Exception as e:
        print(f"❌ Error updating database: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main validation and update process"""
    print("=" * 80)
    print("🔍 PICKERWHEEL PRIZE VALIDATION & UPDATE")
    print("=" * 80)
    
    # Step 1: Parse itemlist
    print("\n📖 Step 1: Parsing itemlist_dates.txt...")
    items = parse_itemlist(ITEMLIST_FILE)
    
    common_count = len(items['common'])
    rare_count = len(items['rare'])
    total_count = common_count + rare_count
    
    print(f"   ✅ Found {total_count} total items:")
    print(f"      - {common_count} common items")
    print(f"      - {rare_count} rare items")
    
    # Step 2: Check for dual-availability items
    print("\n🔍 Step 2: Checking for dual-availability items...")
    dual_items = check_duplicates(items)
    deduplicated_count = get_deduplicated_count(items)
    
    if dual_items:
        print(f"   📊 Found {len(dual_items)} items with dual availability (Common + Rare):")
        for item_name, occurrences in dual_items.items():
            print(f"\n   📌 '{item_name}' appears as:")
            for occ in occurrences:
                dates_info = "all dates (*)" if occ['dates'] == '*' else f"specific date: {occ['dates']}"
                print(f"      - {occ['category'].upper()}: {dates_info}")
        print(f"\n   ℹ️  These items appear in both categories:")
        print(f"      - CSV files: {total_count} items (with duplicates)")
        print(f"      - Wheel display: {deduplicated_count} unique items (deduplicated by backend)")
        print(f"      - Common items prioritized, rare shown only if unique")
    else:
        print("   ✅ All items have single category assignment")
        print(f"   📊 Wheel will display: {deduplicated_count} unique items")
    
    # Step 3: List all unique items
    print("\n📋 Step 3: All unique items (alphabetically):")
    unique_items = list_all_unique_items(items)
    for i, item in enumerate(unique_items, 1):
        print(f"   {i:2d}. {item}")
    print(f"\n   Total unique items: {len(unique_items)}")
    
    # Step 4: Show common items (always available)
    print("\n📋 Step 4: Common items (available daily):")
    for i, item in enumerate(items['common'], 1):
        print(f"   {i:2d}. {item['name']}")
        print(f"       Quantity: {item['quantity']}, Daily Limit: {item['daily_limit']}")
    
    # Step 5: Show rare items with dates
    print("\n🌟 Step 5: Rare items (date-specific):")
    for i, item in enumerate(items['rare'], 1):
        dates = item['available_dates']
        if dates != '*':
            print(f"   {i:2d}. {item['name']}")
            print(f"       Date: {dates}")
            print(f"       Quantity: {item['quantity']}, Daily Limit: {item['daily_limit']}")
    
    # Step 6: Cleanup old CSVs
    print("\n🧹 Step 6: Cleaning up old CSV files...")
    today = date.today()
    removed = cleanup_old_csvs(CSV_DIR, today)
    if removed:
        print(f"   🗑️  Removed {len(removed)} old CSV files:")
        for filename in removed:
            print(f"      - {filename}")
    else:
        print("   ✅ No old CSV files to remove")
    
    # Step 7: Generate new CSVs
    print("\n📝 Step 7: Generating daily CSV files...")
    os.makedirs(CSV_DIR, exist_ok=True)
    
    # Generate from today to Nov 5, 2025
    start_date = today
    end_date = date(2025, 11, 5)
    
    current_date = start_date
    csv_count = 0
    
    while current_date <= end_date:
        item_count = generate_daily_csv(items, current_date, CSV_DIR)
        print(f"   ✅ {current_date.isoformat()}: {item_count} items")
        current_date += timedelta(days=1)
        csv_count += 1
    
    print(f"\n   📊 Generated {csv_count} CSV files")
    
    # Step 8: Update database
    print("\n💾 Step 8: Updating database...")
    if update_database(items, DB_PATH):
        print("   ✅ Database updated successfully")
    else:
        print("   ⚠️  Database update skipped or failed")
    
    # Final summary
    print("\n" + "=" * 80)
    print("✅ VALIDATION & UPDATE COMPLETE")
    print("=" * 80)
    print(f"📊 Summary:")
    print(f"   - Total items in config: {total_count} (9 common + {rare_count} rare)")
    print(f"   - Unique items (deduplicated): {deduplicated_count}")
    print(f"   - Dual-availability items: {len(dual_items)}")
    print(f"   - CSV files: {csv_count} files with {total_count} items each")
    print(f"   - Wheel display: {deduplicated_count} unique segments")
    print(f"   - Old CSV files removed: {len(removed)}")
    print(f"\n   📌 Note: Backend automatically deduplicates {total_count} → {deduplicated_count} for wheel display")
    
    return 0


if __name__ == "__main__":
    exit(main())

