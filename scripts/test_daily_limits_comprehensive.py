#!/usr/bin/env python3
"""
Comprehensive Daily Limits Test
Tests daily limits enforcement by attempting to exceed known limits
"""

import json
import subprocess
import time
from collections import defaultdict

def run_curl(url, method="GET", data=None):
    """Run curl command and return parsed JSON response"""
    cmd = ["curl", "-s"]
    
    if method == "POST":
        cmd.extend(["-X", "POST", "-H", "Content-Type: application/json"])
        if data:
            cmd.extend(["-d", json.dumps(data)])
        else:
            cmd.extend(["-d", "{}"])
    
    cmd.append(url)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            print(f"❌ Curl failed: {result.stderr}")
            return None
        
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
        print(f"Raw response: {result.stdout}")
        return None
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return None

def test_daily_limits_comprehensive():
    """Test daily limits with many spins to try to exceed limits"""
    print("🧪 COMPREHENSIVE DAILY LIMITS TEST")
    print("=" * 70)
    
    # Expected daily limits from itemlist_dates.txt
    expected_limits = {
        # Common items
        'smartwatch + mini cooler': 100,
        'power bank + neckband': 100, 
        'luggage bags': 100,
        'Free pouch and screen guard': 5,
        'Dinner Set': 5,
        'Earbuds and G.Speaker': 3,
        'pressure cooker': 1,
        
        # Rare items (all have daily limit = 1)
        'jio tab': 1,
        'intex home theatre': 1,
        'zebronics home theatre': 1,
        'Mi smart speaker': 1,
        'zebronics astra BT speaker': 1,
        'boult 60w soundbar': 1,
        'gas stove': 1,
        'Mixer Grinder': 1,
        
        # Ultra rare items (all have daily limit = 1)
        'Smart Tv 32 inches': 1,
        'silver coin': 1,
        'refrigerator': 1,
        'washing machine': 1,
        'aircooler': 1,
        'Budget Smartphone': 1
    }
    
    base_url = "http://localhost:8082"
    wins_by_prize = defaultdict(int)
    wins_by_category = defaultdict(int)
    
    # Try many spins to test limits
    num_spins = 50
    violations = 0
    
    print(f"🎯 Testing with {num_spins} spins to verify daily limits...")
    print()
    
    for spin_num in range(1, num_spins + 1):
        if spin_num % 10 == 0:
            print(f"🎲 Completed {spin_num} spins...")
        
        # Pre-spin
        prespin_data = run_curl(f"{base_url}/api/pre-spin", "POST")
        if not prespin_data or not prespin_data.get('success'):
            print(f"❌ Pre-spin failed at spin {spin_num}: {prespin_data.get('error') if prespin_data else 'No response'}")
            continue
        
        selected_prize = prespin_data['selected_prize']
        target_segment = prespin_data['target_segment_index']
        
        # Confirm spin
        spin_data = {
            "selected_prize_id": selected_prize['id'],
            "target_segment_index": target_segment,
            "final_rotation": 3600
        }
        
        spin_result = run_curl(f"{base_url}/api/spin", "POST", spin_data)
        if not spin_result or not spin_result.get('success'):
            print(f"❌ Spin confirmation failed at spin {spin_num}: {spin_result.get('error') if spin_result else 'No response'}")
            continue
        
        awarded_prize = spin_result['prize']
        prize_name = awarded_prize['name']
        category = awarded_prize['category']
        
        # Track wins
        wins_by_prize[prize_name] += 1
        wins_by_category[category] += 1
        
        # Check for violations immediately
        expected_limit = expected_limits.get(prize_name, 1)
        if wins_by_prize[prize_name] > expected_limit:
            print(f"⚠️  VIOLATION at spin {spin_num}: {prize_name} won {wins_by_prize[prize_name]} times (limit: {expected_limit})")
            violations += 1
        
        time.sleep(0.05)  # Brief pause
    
    # Final analysis
    print(f"\n📊 COMPREHENSIVE DAILY LIMITS ANALYSIS")
    print("=" * 70)
    
    print(f"Total spins attempted: {num_spins}")
    print(f"Category distribution:")
    for category, count in wins_by_category.items():
        percentage = (count / sum(wins_by_category.values())) * 100
        print(f"  {category}: {count} wins ({percentage:.1f}%)")
    
    print(f"\n🔍 Prize-by-prize analysis:")
    
    all_good = True
    for prize_name in sorted(expected_limits.keys()):
        actual_wins = wins_by_prize.get(prize_name, 0)
        expected_limit = expected_limits[prize_name]
        
        if actual_wins > expected_limit:
            status = f"❌ VIOLATION ({actual_wins - expected_limit} over limit)"
            all_good = False
        elif actual_wins == expected_limit:
            status = "✅ AT LIMIT"
        else:
            status = "✅ OK"
        
        print(f"  {prize_name}: {actual_wins}/{expected_limit} - {status}")
    
    # Check for any unexpected prizes
    for prize_name, count in wins_by_prize.items():
        if prize_name not in expected_limits:
            print(f"  ⚠️  UNEXPECTED PRIZE: {prize_name} won {count} times")
            all_good = False
    
    print(f"\n🎯 FINAL RESULT:")
    if all_good and violations == 0:
        print("✅ PERFECT! All daily limits properly enforced")
        return True
    else:
        print(f"❌ Daily limit enforcement issues detected ({violations} violations)")
        return False

if __name__ == "__main__":
    success = test_daily_limits_comprehensive()
    exit(0 if success else 1)
