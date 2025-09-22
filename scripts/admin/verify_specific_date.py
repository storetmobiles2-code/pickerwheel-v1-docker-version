#!/usr/bin/env python3
"""
Verify Prize Distribution for a Specific Date

This script verifies the prize distribution for a specific date,
focusing on rare and ultra-rare items.
"""

import os
import sys
import json
import sqlite3
import subprocess
import time
from datetime import date

# Configuration
ADMIN_PASSWORD = "myTAdmin2025"
API_BASE_URL = "http://localhost:9080/api"
DB_PATH = "../../backend/pickerwheel_contest.db"
TEST_DATE = "2025-10-21"  # Date with rare and ultra-rare items
TOTAL_SPINS = 200

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

def get_available_prizes():
    """Get all available prizes for the test date"""
    cmd = [
        "curl", "-s",
        f"{API_BASE_URL}/prizes/available?date={TEST_DATE}"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(result.stdout)

def perform_spin(user_id):
    """Perform a spin without forcing any prize"""
    cmd = [
        "curl", "-s", "-X", "POST",
        f"{API_BASE_URL}/admin/test-spin",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({
            "admin_password": ADMIN_PASSWORD,
            "user_id": user_id,
            "test_date": TEST_DATE
        })
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(result.stdout)

def get_prize_stats():
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
    """, (TEST_DATE,))
    
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
    """, (TEST_DATE,))
    
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
    """, (TEST_DATE,))
    
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
    expected_rate = (total_rare_limit / TOTAL_SPINS) * 100 if TOTAL_SPINS > 0 else 0
    return total_rare_limit, expected_rate

def print_report(stats, total_spins):
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
    print(f"🔍 PRIZE DISTRIBUTION ANALYSIS FOR {TEST_DATE}")
    print("=" * 60)
    print(f"Total Spins: {total_spins}")
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
    print(f"📅 AVAILABLE RARE & ULTRA-RARE ITEMS FOR {TEST_DATE}")
    
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

def main():
    """Main function"""
    print("=== VERIFYING PRIZE DISTRIBUTION FOR SPECIFIC DATE ===")
    print()
    print(f"Test Date: {TEST_DATE}")
    print(f"Total Spins: {TOTAL_SPINS}")
    print()
    
    # Reset the inventory
    print("🔄 Resetting inventory...")
    reset_result = reset_inventory()
    print(f"Reset result: {reset_result.get('success', False)}")
    print()
    
    # Get available prizes
    available_prizes = get_available_prizes()
    print(f"Found {len(available_prizes)} available prizes for {TEST_DATE}")
    print()
    
    # Perform spins
    print(f"🔄 Performing {TOTAL_SPINS} spins...")
    for i in range(TOTAL_SPINS):
        user_id = f"verify_specific_{i}"
        result = perform_spin(user_id)
        if i % 20 == 0 and i > 0:
            print(f"  Completed {i} spins...")
    print("Spins completed")
    print()
    
    # Get statistics
    stats = get_prize_stats()
    
    # Print report
    print_report(stats, TOTAL_SPINS)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
