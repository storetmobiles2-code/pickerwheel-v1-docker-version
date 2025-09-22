#!/usr/bin/env python3
"""
Comprehensive Verification of Rare and Ultra-Rare Items

This script verifies the winning probability of rare and ultra-rare items
for all days in the event period, honoring the daily limits.
"""

import os
import sys
import json
import sqlite3
import subprocess
import time
from datetime import date, datetime, timedelta

# Configuration
ADMIN_PASSWORD = "myTAdmin2025"
API_BASE_URL = "http://localhost:9080/api"
DB_PATH = "../../backend/pickerwheel_contest.db"
SPINS_PER_DAY = 100
START_DATE = "2025-09-21"
END_DATE = "2025-11-21"

def reset_inventory():
    """Reset the inventory"""
    cmd = [
        "curl", "-s", "-X", "POST",
        f"{API_BASE_URL}/admin/reset-inventory",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({"admin_password": ADMIN_PASSWORD})
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(result.stdout)

def get_available_prizes(test_date):
    """Get all available prizes for the test date"""
    cmd = [
        "curl", "-s",
        f"{API_BASE_URL}/prizes/available?date={test_date}"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(result.stdout)

def perform_spin(user_id, test_date):
    """Perform a spin for a specific date"""
    cmd = [
        "curl", "-s", "-X", "POST",
        f"{API_BASE_URL}/admin/test-spin",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({
            "admin_password": ADMIN_PASSWORD,
            "user_id": user_id,
            "test_date": test_date
        })
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(result.stdout)

def get_prize_stats(test_date):
    """Get statistics about prizes won"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get total wins by category
    cursor.execute("""
        SELECT pc.name as category, COUNT(*) as wins
        FROM prize_wins pw
        JOIN prizes p ON pw.prize_id = p.id
        JOIN prize_categories pc ON p.category_id = pc.id
        WHERE pw.win_date = ?
        GROUP BY pc.name
    """, (test_date,))
    
    category_stats = {row['category']: row['wins'] for row in cursor.fetchall()}
    
    # Get wins by prize
    cursor.execute("""
        SELECT p.id, p.name, pc.name as category, COUNT(*) as wins
        FROM prize_wins pw
        JOIN prizes p ON pw.prize_id = p.id
        JOIN prize_categories pc ON p.category_id = pc.id
        WHERE pw.win_date = ?
        GROUP BY p.id
        ORDER BY pc.name, wins DESC
    """, (test_date,))
    
    prize_stats = [dict(row) for row in cursor.fetchall()]
    
    # Get available rare and ultra-rare prizes
    cursor.execute("""
        SELECT p.id, p.name, pc.name as category, pi.per_day_limit, pi.remaining_quantity
        FROM prizes p
        JOIN prize_categories pc ON p.category_id = pc.id
        JOIN prize_inventory pi ON p.id = pi.prize_id
        WHERE (pc.name = 'rare' OR pc.name = 'ultra_rare')
          AND pi.available_date = ?
        ORDER BY pc.name, p.name
    """, (test_date,))
    
    available_rare = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        'category_stats': category_stats,
        'prize_stats': prize_stats,
        'available_rare': available_rare
    }

def get_expected_rare_rate(available_rare):
    """Calculate the expected rare rate based on available prizes and their daily limits"""
    total_rare_limit = 0
    for prize in available_rare:
        total_rare_limit += prize.get('per_day_limit', 1)
    
    # Calculate expected percentage
    expected_rate = (total_rare_limit / SPINS_PER_DAY) * 100 if SPINS_PER_DAY > 0 else 0
    return total_rare_limit, expected_rate

def print_report(test_date, stats, spins_performed):
    """Print a report of the test results"""
    category_stats = stats['category_stats']
    prize_stats = stats['prize_stats']
    available_rare = stats['available_rare']
    
    # Calculate percentages
    total_wins = sum(category_stats.values())
    rare_wins = category_stats.get('rare', 0)
    ultra_rare_wins = category_stats.get('ultra_rare', 0)
    common_wins = category_stats.get('common', 0)
    
    rare_pct = (rare_wins / total_wins) * 100 if total_wins > 0 else 0
    ultra_rare_pct = (ultra_rare_wins / total_wins) * 100 if total_wins > 0 else 0
    combined_rare_pct = ((rare_wins + ultra_rare_wins) / total_wins) * 100 if total_wins > 0 else 0
    
    # Calculate expected rare rate
    total_rare_limit, expected_rate = get_expected_rare_rate(available_rare)
    
    # Print report
    print("=" * 60)
    print(f"🔍 PRIZE DISTRIBUTION FOR {test_date}")
    print("=" * 60)
    print(f"Spins Performed: {spins_performed}")
    print(f"Total Wins: {total_wins}")
    print()
    
    print("🎯 CATEGORY DISTRIBUTION:")
    print(f"• Common: {common_wins} ({common_wins/total_wins*100:.1f}%)")
    print(f"• Rare: {rare_wins} ({rare_pct:.1f}%)")
    print(f"• Ultra Rare: {ultra_rare_wins} ({ultra_rare_pct:.1f}%)")
    print(f"• Combined Rare Rate: {combined_rare_pct:.1f}%")
    print(f"• Expected Rare Rate: {expected_rate:.1f}% (based on {total_rare_limit} daily limit)")
    print()
    
    print("🏆 PRIZE DISTRIBUTION:")
    
    # Print ultra-rare wins
    print("🔥 Ultra Rare Items Won:")
    ultra_rare_prizes = [p for p in prize_stats if p['category'] == 'ultra_rare']
    if ultra_rare_prizes:
        for prize in ultra_rare_prizes:
            print(f"• {prize['name']}: {prize['wins']} wins")
    else:
        print("No Ultra Rare items won")
    print()
    
    # Print rare wins
    print("⭐ Rare Items Won:")
    rare_prizes = [p for p in prize_stats if p['category'] == 'rare']
    if rare_prizes:
        for prize in rare_prizes:
            print(f"• {prize['name']}: {prize['wins']} wins")
    else:
        print("No Rare items won")
    print()
    
    # Print available rare and ultra-rare items
    print(f"📅 AVAILABLE RARE & ULTRA-RARE ITEMS FOR {test_date}")
    
    # Rare items
    rare_items = [p for p in available_rare if p['category'] == 'rare']
    if rare_items:
        print(f"⭐ Rare Items Available Today ({len(rare_items)})")
        print(f"{'Item Name':<20}{'Daily Limit':<15}{'Remaining':<10}")
        for item in rare_items:
            print(f"{item['name']:<20}{item['per_day_limit']:<15}{item['remaining_quantity']:<10}")
    else:
        print("No Rare items available today")
    print()
    
    # Ultra-rare items
    ultra_rare_items = [p for p in available_rare if p['category'] == 'ultra_rare']
    if ultra_rare_items:
        print(f"🔥 Ultra Rare Items Available Today ({len(ultra_rare_items)})")
        print(f"{'Item Name':<20}{'Daily Limit':<15}{'Remaining':<10}")
        for item in ultra_rare_items:
            print(f"{item['name']:<20}{item['per_day_limit']:<15}{item['remaining_quantity']:<10}")
    else:
        print("No Ultra Rare items available today")
    print()
    
    # Overall assessment
    print("📊 OVERALL ASSESSMENT:")
    if ultra_rare_wins > 0:
        print("✅ Ultra Rare items are being awarded")
    else:
        if len(ultra_rare_items) > 0:
            print("❌ No Ultra Rare items were awarded despite being available")
        else:
            print("⚠️ No Ultra Rare items available today")
    
    if rare_wins > 0:
        print("✅ Rare items are being awarded")
    else:
        if len(rare_items) > 0:
            print("❌ No Rare items were awarded despite being available")
        else:
            print("⚠️ No Rare items available today")
    
    # Check if we're close to the expected rate
    if total_rare_limit > 0:
        if combined_rare_pct >= expected_rate * 0.8:  # Within 80% of expected
            print(f"✅ Combined rare rate ({combined_rare_pct:.1f}%) is close to expected ({expected_rate:.1f}%)")
        else:
            print(f"❌ Combined rare rate ({combined_rare_pct:.1f}%) is too low (expected: {expected_rate:.1f}%)")
    else:
        print("⚠️ No rare or ultra-rare items available today")
    print("=" * 60)
    
    return {
        'date': test_date,
        'total_wins': total_wins,
        'rare_wins': rare_wins,
        'ultra_rare_wins': ultra_rare_wins,
        'combined_rare_pct': combined_rare_pct,
        'expected_rate': expected_rate,
        'total_rare_limit': total_rare_limit,
        'rare_items_available': len(rare_items),
        'ultra_rare_items_available': len(ultra_rare_items)
    }

def test_date_range(start_date_str, end_date_str, days_to_test=10):
    """Test a range of dates, sampling evenly across the range"""
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    
    # Calculate the total number of days
    total_days = (end_date - start_date).days + 1
    
    # Calculate the step size to sample evenly
    step = max(1, total_days // days_to_test)
    
    # Generate the dates to test
    test_dates = []
    current_date = start_date
    while current_date <= end_date:
        test_dates.append(current_date.isoformat())
        current_date += timedelta(days=step)
    
    # Make sure we include the end date
    if test_dates[-1] != end_date.isoformat():
        test_dates.append(end_date.isoformat())
    
    # Test each date
    results = []
    for test_date in test_dates:
        print(f"\n\n🔍 TESTING DATE: {test_date}")
        
        # Reset the inventory
        print("🔄 Resetting inventory...")
        reset_result = reset_inventory()
        
        # Get available prizes
        available_prizes = get_available_prizes(test_date)
        print(f"Found {len(available_prizes)} available prizes for {test_date}")
        
        # Perform spins
        print(f"🔄 Performing {SPINS_PER_DAY} spins...")
        for i in range(SPINS_PER_DAY):
            user_id = f"verify_{test_date}_{i}"
            result = perform_spin(user_id, test_date)
            if i % 10 == 0 and i > 0:
                print(f"  Completed {i} spins...")
        print("Spins completed")
        
        # Get statistics
        stats = get_prize_stats(test_date)
        
        # Print report
        result = print_report(test_date, stats, SPINS_PER_DAY)
        results.append(result)
    
    # Print summary
    print("\n\n" + "=" * 60)
    print("📊 OVERALL SUMMARY")
    print("=" * 60)
    print(f"Tested {len(test_dates)} dates from {start_date_str} to {end_date_str}")
    print(f"Spins per day: {SPINS_PER_DAY}")
    print()
    
    print("📅 DATE SUMMARY:")
    print(f"{'Date':<12}{'Rare Items':<12}{'Ultra Rare':<12}{'Combined %':<12}{'Expected %':<12}{'Assessment'}")
    print("-" * 70)
    
    for result in results:
        date = result['date']
        rare_wins = result['rare_wins']
        ultra_rare_wins = result['ultra_rare_wins']
        combined_pct = result['combined_rare_pct']
        expected_rate = result['expected_rate']
        
        # Determine assessment
        if result['total_rare_limit'] == 0:
            assessment = "N/A"
        elif combined_pct >= expected_rate * 0.8:
            assessment = "✅ Good"
        else:
            assessment = "❌ Low"
        
        print(f"{date:<12}{rare_wins:<12}{ultra_rare_wins:<12}{combined_pct:.1f}%{' ':<8}{expected_rate:.1f}%{' ':<8}{assessment}")
    
    print("=" * 60)

def main():
    """Main function"""
    print("=== COMPREHENSIVE VERIFICATION OF RARE AND ULTRA-RARE ITEMS ===")
    print()
    print(f"Start Date: {START_DATE}")
    print(f"End Date: {END_DATE}")
    print(f"Spins per Day: {SPINS_PER_DAY}")
    print()
    
    # Test a range of dates
    test_date_range(START_DATE, END_DATE, days_to_test=10)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
