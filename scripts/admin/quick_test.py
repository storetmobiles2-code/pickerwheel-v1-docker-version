#!/usr/bin/env python3
"""
Quick Test for Prize Distribution

This script performs 100 spins and checks if rare and ultra-rare items are being selected.
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
TEST_DATE = "2025-10-01"
TOTAL_SPINS = 200  # Increased from 100 to 200

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
    
    conn.close()
    
    return {
        'category_stats': category_stats,
        'prize_stats': prize_stats
    }

def main():
    """Main function"""
    print("=== QUICK TEST FOR PRIZE DISTRIBUTION ===")
    print()
    
    # Reset the inventory
    print("🔄 Resetting inventory...")
    reset_result = reset_inventory()
    print(f"Reset result: {reset_result.get('success', False)}")
    print()
    
    # Perform spins
    print(f"🔄 Performing {TOTAL_SPINS} spins...")
    for i in range(TOTAL_SPINS):
        user_id = f"quick_test_{i}"
        result = perform_spin(user_id)
        if i % 10 == 0:
            print(f"  Completed {i} spins...")
    print("Spins completed")
    print()
    
    # Get statistics
    stats = get_prize_stats()
    category_stats = stats['category_stats']
    prize_stats = stats['prize_stats']
    
    # Calculate percentages
    total_wins = sum(category_stats.values())
    rare_wins = category_stats.get('rare', 0)
    ultra_rare_wins = category_stats.get('ultra_rare', 0)
    common_wins = category_stats.get('common', 0)
    
    rare_pct = (rare_wins / total_wins) * 100 if total_wins > 0 else 0
    ultra_rare_pct = (ultra_rare_wins / total_wins) * 100 if total_wins > 0 else 0
    combined_rare_pct = ((rare_wins + ultra_rare_wins) / total_wins) * 100 if total_wins > 0 else 0
    
    # Print report
    print("=" * 60)
    print(f"🔍 PRIZE DISTRIBUTION ANALYSIS")
    print("=" * 60)
    print(f"Test Date: {TEST_DATE}")
    print(f"Total Spins: {TOTAL_SPINS}")
    print(f"Total Wins: {total_wins}")
    print()
    
    print("🎯 CATEGORY DISTRIBUTION:")
    print(f"• Common: {common_wins} ({common_wins/total_wins*100:.1f}%)")
    print(f"• Rare: {rare_wins} ({rare_pct:.1f}%)")
    print(f"• Ultra Rare: {ultra_rare_wins} ({ultra_rare_pct:.1f}%)")
    print(f"• Combined Rare Rate: {combined_rare_pct:.1f}%")
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
    
    # Overall assessment
    print("📊 OVERALL ASSESSMENT:")
    if ultra_rare_wins > 0:
        print("✅ Ultra Rare items are being awarded")
    else:
        print("❌ No Ultra Rare items were awarded")
    
    if rare_wins > 0:
        print("✅ Rare items are being awarded")
    else:
        print("❌ No Rare items were awarded")
    
    if combined_rare_pct >= 5:
        print(f"✅ Combined rare rate ({combined_rare_pct:.1f}%) is good")
    else:
        print(f"❌ Combined rare rate ({combined_rare_pct:.1f}%) is too low")
    print("=" * 60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
