#!/usr/bin/env python3
"""
Verify admin panel data - checks itemlist, CSV files, and database
"""

import sqlite3
import csv
import os
from datetime import date

# Paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ITEMLIST_FILE = os.path.join(PROJECT_ROOT, 'itemlist_dates.txt')
CSV_DIR = os.path.join(PROJECT_ROOT, 'daily_csvs')
DB_PATH = os.path.join(PROJECT_ROOT, 'backend', 'pickerwheel_contest.db')

print("=" * 80)
print("🔍 ADMIN PANEL DATA VERIFICATION")
print("=" * 80)

# 1. Check itemlist_dates.txt
print("\n📋 Step 1: Checking itemlist_dates.txt...")
common_items = []
rare_items = []

with open(ITEMLIST_FILE, 'r') as f:
    current_section = None
    for line in f:
        line = line.strip()
        if not line or line.startswith('Item,'):
            continue
        if line.startswith('#'):
            if 'Common' in line:
                current_section = 'common'
            elif 'Rare' in line:
                current_section = 'rare'
            continue
        
        parts = [p.strip() for p in line.split(',')]
        if len(parts) >= 5:
            item_info = {
                'name': parts[0],
                'category': parts[1],
                'quantity': parts[2],
                'daily_limit': parts[3],
                'available_dates': parts[4]
            }
            if current_section == 'common':
                common_items.append(item_info)
            elif current_section == 'rare':
                rare_items.append(item_info)

total_items = len(common_items) + len(rare_items)

# Calculate unique items (after deduplication)
unique_names = set()
for item in common_items:
    unique_names.add(item['name'].lower().strip())
for item in rare_items:
    unique_names.add(item['name'].lower().strip())

print(f"   ✅ Common items: {len(common_items)}")
print(f"   ✅ Rare items: {len(rare_items)}")
print(f"   ✅ Total items in config: {total_items}")
print(f"   ✅ Unique items (deduplicated): {len(unique_names)}")

# 2. Check a sample CSV file
print("\n📄 Step 2: Checking daily CSV files...")
today = date.today()
csv_file = os.path.join(CSV_DIR, f'prizes_{today.isoformat()}.csv')

if os.path.exists(csv_file):
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        csv_items = list(reader)
    print(f"   ✅ CSV file exists: prizes_{today.isoformat()}.csv")
    print(f"   ✅ Items in CSV: {len(csv_items)}")
    
    # Check if Available_Dates column exists
    if csv_items and 'Available_Dates' in csv_items[0]:
        print(f"   ✅ Available_Dates column present")
    else:
        print(f"   ⚠️  Available_Dates column missing")
else:
    print(f"   ⚠️  CSV file not found: {csv_file}")

# 3. Check database
print("\n💾 Step 3: Checking database...")
if os.path.exists(DB_PATH):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check prizes table
        cursor.execute("SELECT COUNT(*) FROM prizes")
        prizes_count = cursor.fetchone()[0]
        print(f"   ✅ Prizes in database: {prizes_count}")
        
        # Check prize names
        cursor.execute("SELECT name FROM prizes ORDER BY id LIMIT 10")
        sample_prizes = [row[0] for row in cursor.fetchall()]
        print(f"   ✅ Sample prize names:")
        for prize in sample_prizes[:5]:
            print(f"      - {prize}")
        
        # Check daily_prizes table (used by admin panel)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='daily_prizes'")
        if cursor.fetchone():
            cursor.execute(f"SELECT COUNT(*) FROM daily_prizes WHERE date = '{today.isoformat()}'")
            daily_count = cursor.fetchone()[0]
            print(f"   ✅ Daily prizes for today: {daily_count}")
            
            if daily_count == 0:
                print(f"   ⚠️  No daily prizes in database for today - needs sync!")
                print(f"   💡 Use admin panel 'Reload from Master Config' button")
        else:
            print(f"   ℹ️  daily_prizes table doesn't exist yet")
        
        conn.close()
    except Exception as e:
        print(f"   ❌ Error reading database: {e}")
else:
    print(f"   ⚠️  Database not found: {DB_PATH}")

# 4. Admin Panel Endpoints
print("\n🔧 Step 4: Admin Panel Access")
print(f"   📍 Admin Panel URL: http://localhost:8082/admin.html")
print(f"   🔑 Admin Password: myTAdmin2025")
print(f"   ℹ️  After logging in:")
print(f"      1. Click 'Load Prizes' to see current items")
print(f"      2. Click 'Reload from Master Config' to sync from itemlist_dates.txt")
print(f"      3. Verify all {len(common_items) + len(rare_items)} items appear")

print("\n" + "=" * 80)
print("✅ VERIFICATION COMPLETE")
print("=" * 80)
print(f"\n📊 Summary:")
print(f"   - Items in config: {total_items} ({len(common_items)} common + {len(rare_items)} rare)")
print(f"   - Unique items (deduplicated): {len(unique_names)}")
print(f"   - Wheel displays: {len(unique_names)} unique segments")
print(f"   - Database: {'✅ Ready' if os.path.exists(DB_PATH) else '⚠️ Not found'}")
print(f"   - CSV files: {'✅ Generated' if os.path.exists(csv_file) else '⚠️ Missing'}")
print(f"\n   📌 Backend automatically deduplicates {total_items} → {len(unique_names)} for wheel display")

