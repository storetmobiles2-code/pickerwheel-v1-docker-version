#!/usr/bin/env python3
"""
Test script for Daily Database Backend
Tests the daily CSV loading, inventory tracking, and transactional history
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from daily_database_backend import DatabaseManager, DailyPrizeManager
from datetime import date, datetime

def test_daily_backend():
    """Test the daily backend functionality"""
    print("🧪 Testing Daily Database Backend")
    print("=" * 50)
    
    # Initialize managers
    db_manager = DatabaseManager('test_pickerwheel.db')
    prize_manager = DailyPrizeManager('daily_csvs', db_manager)
    
    # Test date
    test_date = date(2025, 10, 2)  # A date with many prizes
    print(f"📅 Testing with date: {test_date}")
    
    # Test 1: Load daily prizes from CSV
    print("\n1️⃣ Testing CSV loading...")
    csv_prizes = prize_manager.load_daily_prizes_from_csv(test_date)
    print(f"   Loaded {len(csv_prizes)} prizes from CSV")
    
    if csv_prizes:
        print("   Sample prizes:")
        for i, prize in enumerate(csv_prizes[:3]):
            print(f"     {i+1}. {prize['name']} ({prize['category']}) - Qty: {prize['quantity']}, Limit: {prize['daily_limit']}")
    
    # Test 2: Sync to database
    print("\n2️⃣ Testing database sync...")
    success = prize_manager.sync_daily_prizes_to_database(test_date)
    print(f"   Database sync: {'✅ Success' if success else '❌ Failed'}")
    
    # Test 3: Get available prizes
    print("\n3️⃣ Testing available prizes...")
    available_prizes = prize_manager.get_available_prizes(test_date)
    print(f"   Available prizes: {len(available_prizes)}")
    
    # Show category breakdown
    categories = {}
    for prize in available_prizes:
        cat = prize['category']
        categories[cat] = categories.get(cat, 0) + 1
    
    print("   Category breakdown:")
    for cat, count in categories.items():
        print(f"     {cat}: {count}")
    
    # Test 4: Test prize selection with priority
    print("\n4️⃣ Testing prize selection with priority...")
    test_users = ['user1', 'user2', 'user3', 'user4', 'user5']
    selected_prizes = []
    
    for user in test_users:
        selected = prize_manager.select_prize_with_priority(test_date, user)
        if selected:
            selected_prizes.append(selected['name'])
            print(f"   {user} selected: {selected['name']} ({selected['category']})")
            
            # Consume the prize
            success = prize_manager.consume_prize(selected['name'], test_date, user)
            print(f"     Prize consumed: {'✅' if success else '❌'}")
        else:
            print(f"   {user} selected: No prize available")
    
    # Test 5: Check inventory after consumption
    print("\n5️⃣ Testing inventory after consumption...")
    remaining_prizes = prize_manager.get_available_prizes(test_date)
    print(f"   Remaining available prizes: {len(remaining_prizes)}")
    
    # Test 6: Get daily stats
    print("\n6️⃣ Testing daily statistics...")
    stats = prize_manager.get_daily_stats(test_date)
    print(f"   Daily stats:")
    print(f"     Total prizes: {stats['total_prizes']}")
    print(f"     Available prizes: {stats['available_prizes']}")
    print(f"     Total wins: {stats['total_wins_today']}")
    print(f"     Unique users: {stats['unique_users']}")
    print(f"     Category breakdown: {stats['category_breakdown']}")
    
    # Test 7: Test transaction history
    print("\n7️⃣ Testing transaction history...")
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT * FROM daily_transactions
            WHERE date = ?
            ORDER BY timestamp DESC
        ''', (test_date.isoformat(),))
        
        transactions = cursor.fetchall()
        print(f"   Total transactions: {len(transactions)}")
        
        for i, tx in enumerate(transactions[:3]):
            print(f"     {i+1}. {tx['user_identifier']} won {tx['prize_name']} at {tx['timestamp']}")
    
    finally:
        conn.close()
    
    print("\n✅ Daily backend test completed!")
    
    # Cleanup
    if os.path.exists('test_pickerwheel.db'):
        os.remove('test_pickerwheel.db')
        print("🧹 Cleaned up test database")

if __name__ == "__main__":
    test_daily_backend()
