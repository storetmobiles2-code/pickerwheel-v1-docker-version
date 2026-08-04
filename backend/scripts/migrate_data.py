#!/usr/bin/env python3
"""
PickerWheel Data Migration Script
Migrates prize data from itemlist_dates_v2.txt to PostgreSQL database
"""

import os
import sys
import psycopg2
from psycopg2.extras import execute_values
from datetime import date, timedelta

# Database connection settings
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': os.environ.get('DB_PORT', '5432'),
    'dbname': os.environ.get('DB_NAME', 'pickerwheel'),
    'user': os.environ.get('DB_USER', 'pickerwheel'),
    'password': os.environ.get('DB_PASSWORD', 'pickerwheel123')
}

# Category mapping
CATEGORY_MAP = {
    'ultra_rare': 1,
    'rare': 2,
    'common': 3
}

# Emoji mapping based on item names
EMOJI_MAP = {
    'tv': '📺',
    'smart tv': '📺',
    'phone': '📱',
    'mobile': '📱',
    'tab': '📱',
    'tablet': '📱',
    'watch': '⌚',
    'smartwatch': '⌚',
    'speaker': '🔊',
    'soundbar': '🔊',
    'theatre': '🎭',
    'theater': '🎭',
    'refrigerator': '🧊',
    'fridge': '🧊',
    'washing': '🧺',
    'machine': '🧺',
    'cooler': '❄️',
    'air cooler': '❄️',
    'coin': '🪙',
    'silver': '🪙',
    'stove': '🔥',
    'gas': '🔥',
    'grinder': '🥤',
    'mixer': '🥤',
    'luggage': '🧳',
    'bag': '🧳',
    'cooker': '🍲',
    'pressure': '🍲',
    'pouch': '📱',
    'screen': '📱',
    'dinner': '🍽️',
    'set': '🍽️',
    'earbuds': '🎧',
    'buds': '🎧',
    'earphones': '🎧',
    'power': '🔋',
    'bank': '🔋',
    'neckband': '🎵',
    'trimmer': '✂️',
    'massage': '💆',
    'gun': '💆',
}


def get_emoji(name):
    """Get emoji for a prize based on its name"""
    name_lower = name.lower()
    for keyword, emoji in EMOJI_MAP.items():
        if keyword in name_lower:
            return emoji
    return '🎁'


def get_category_id(name, category_str):
    """Determine category based on name and original category"""
    name_lower = name.lower()
    
    # Override based on item rarity
    rare_items = ['jio tab', 'home theatre', 'smart speaker', 'gas stove', 'mixer grinder']
    ultra_rare_items = ['smart tv', 'silver coin', 'refrigerator', 'washing machine', 
                        'air cooler', 'soundbar']
    
    for item in ultra_rare_items:
        if item in name_lower:
            return CATEGORY_MAP['ultra_rare']
    
    for item in rare_items:
        if item in name_lower:
            return CATEGORY_MAP['rare']
    
    return CATEGORY_MAP['common']


def parse_itemlist(filepath):
    """Parse itemlist_dates_v2.txt and return prize data"""
    prizes = []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    display_order = 1
    for line in lines:
        line = line.strip()
        
        # Skip empty lines and comments
        if not line or line.startswith('#'):
            continue
        
        # Skip header
        if line.lower().startswith('item,'):
            continue
        
        parts = [p.strip() for p in line.split(',')]
        if len(parts) < 5:
            continue
        
        name = parts[0]
        category_str = parts[1]
        quantity = int(parts[2]) if parts[2].isdigit() else 10
        daily_limit = int(parts[3]) if parts[3].isdigit() else 1
        available_dates = parts[4]
        
        prize = {
            'name': name,
            'category_id': get_category_id(name, category_str),
            'emoji': get_emoji(name),
            'description': f'{name} prize',
            'display_order': display_order,
            'quantity': quantity,
            'daily_limit': daily_limit,
            'available_dates': available_dates
        }
        prizes.append(prize)
        display_order += 1
    
    return prizes


def run_migration():
    """Run the migration"""
    print("🚀 Starting PickerWheel data migration...")
    
    # Find itemlist file
    itemlist_paths = [
        '../itemlist_dates_v2.txt',
        '../../itemlist_dates_v2.txt',
        '/app/itemlist_dates_v2.txt',
        'itemlist_dates_v2.txt'
    ]
    
    itemlist_path = None
    for path in itemlist_paths:
        if os.path.exists(path):
            itemlist_path = path
            break
    
    if not itemlist_path:
        print("❌ Could not find itemlist_dates_v2.txt")
        sys.exit(1)
    
    print(f"📄 Found itemlist at: {itemlist_path}")
    
    # Parse prizes
    prizes = parse_itemlist(itemlist_path)
    print(f"📦 Parsed {len(prizes)} prizes from itemlist")
    
    # Connect to database
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print("✅ Connected to PostgreSQL database")
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        sys.exit(1)
    
    try:
        # Clear existing data (optional - for clean migration)
        cursor.execute("DELETE FROM prize_inventory")
        cursor.execute("DELETE FROM prizes WHERE id > 0")
        print("🧹 Cleared existing prize data")
        
        # Insert prizes
        for prize in prizes:
            cursor.execute("""
                INSERT INTO prizes (name, category_id, emoji, description, display_order, is_active, is_enabled)
                VALUES (%s, %s, %s, %s, %s, TRUE, TRUE)
                RETURNING id
            """, (
                prize['name'],
                prize['category_id'],
                prize['emoji'],
                prize['description'],
                prize['display_order']
            ))
            prize['id'] = cursor.fetchone()[0]
            print(f"  ➕ Added prize: {prize['name']} (ID: {prize['id']})")
        
        # Create inventory for next 60 days
        event_id = 1
        start_date = date.today()
        end_date = start_date + timedelta(days=60)
        
        print(f"\n📊 Creating inventory from {start_date} to {end_date}...")
        
        inventory_data = []
        current_date = start_date
        
        while current_date <= end_date:
            date_str = current_date.isoformat()
            
            for prize in prizes:
                # Check if prize is available on this date
                available_dates = prize['available_dates']
                
                if available_dates == '*':
                    is_available = True
                else:
                    available_list = [d.strip() for d in available_dates.split('|')]
                    is_available = date_str in available_list
                
                # Set quantity based on availability
                if is_available:
                    quantity = prize['quantity']
                else:
                    quantity = 0
                
                inventory_data.append((
                    prize['id'],
                    event_id,
                    current_date,
                    quantity,
                    quantity,
                    prize['daily_limit']
                ))
            
            current_date += timedelta(days=1)
        
        # Bulk insert inventory
        execute_values(cursor, """
            INSERT INTO prize_inventory (prize_id, event_id, available_date, initial_quantity, remaining_quantity, daily_limit)
            VALUES %s
            ON CONFLICT (prize_id, event_id, available_date) DO NOTHING
        """, inventory_data)
        
        print(f"✅ Created {len(inventory_data)} inventory records")
        
        # Commit transaction
        conn.commit()
        print("\n🎉 Migration completed successfully!")
        
        # Print summary
        cursor.execute("SELECT COUNT(*) FROM prizes WHERE is_active = TRUE")
        prize_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM prize_inventory")
        inventory_count = cursor.fetchone()[0]
        
        print(f"\n📊 Summary:")
        print(f"   • Total prizes: {prize_count}")
        print(f"   • Total inventory records: {inventory_count}")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    run_migration()
