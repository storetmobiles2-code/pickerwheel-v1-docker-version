#!/usr/bin/env python3
"""
Test Daily Limits Enforcement
Verifies that daily limits are properly enforced for rare and ultra-rare items
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

def test_daily_limits(num_spins=20):
    """Test daily limit enforcement with multiple spins"""
    print(f"🧪 TESTING DAILY LIMITS ENFORCEMENT ({num_spins} spins)")
    print("=" * 70)
    
    base_url = "http://localhost:8082"
    wins_by_prize = defaultdict(int)
    wins_by_category = defaultdict(int)
    
    print("🎯 Expected daily limits from itemlist_dates.txt:")
    print("   Rare items: 1 per day")
    print("   Ultra-rare items: 1 per day") 
    print("   Common items: varies (5-100 per day)")
    print()
    
    for spin_num in range(1, num_spins + 1):
        print(f"🎲 SPIN #{spin_num}")
        print("-" * 30)
        
        # Step 1: Pre-spin
        prespin_data = run_curl(f"{base_url}/api/pre-spin", "POST")
        if not prespin_data or not prespin_data.get('success'):
            print(f"❌ Pre-spin failed: {prespin_data.get('error') if prespin_data else 'No response'}")
            continue
        
        selected_prize = prespin_data['selected_prize']
        target_segment = prespin_data['target_segment_index']
        
        print(f"Backend selected: {selected_prize['name']} ({selected_prize['category']})")
        
        # Step 2: Confirm spin
        spin_data = {
            "selected_prize_id": selected_prize['id'],
            "target_segment_index": target_segment,
            "final_rotation": 3600  # Dummy rotation
        }
        
        spin_result = run_curl(f"{base_url}/api/spin", "POST", spin_data)
        if not spin_result or not spin_result.get('success'):
            print(f"❌ Spin confirmation failed: {spin_result.get('error') if spin_result else 'No response'}")
            continue
        
        awarded_prize = spin_result['prize']
        prize_name = awarded_prize['name']
        category = awarded_prize['category']
        
        # Track wins
        wins_by_prize[prize_name] += 1
        wins_by_category[category] += 1
        
        print(f"✅ Awarded: {prize_name} ({category})")
        print(f"   Total wins for this prize: {wins_by_prize[prize_name]}")
        
        # Check for daily limit violations
        if category.lower() in ['rare', 'ultra_rare'] and wins_by_prize[prize_name] > 1:
            print(f"⚠️  DAILY LIMIT VIOLATION: {prize_name} won {wins_by_prize[prize_name]} times!")
        
        time.sleep(0.1)  # Brief pause
    
    # Summary
    print(f"\n📊 DAILY LIMITS SUMMARY")
    print("=" * 70)
    
    print(f"Total spins: {num_spins}")
    print(f"Category distribution:")
    for category, count in wins_by_category.items():
        percentage = (count / num_spins) * 100
        print(f"  {category}: {count} wins ({percentage:.1f}%)")
    
    print(f"\nPrize-by-prize breakdown:")
    violations = 0
    
    for prize_name, count in sorted(wins_by_prize.items()):
        # Determine expected daily limit based on itemlist_dates.txt
        if any(keyword in prize_name.lower() for keyword in ['gas stove', 'intex', 'zebronics', 'jio', 'mi', 'boult', 'mixer']):
            expected_limit = 1  # Rare items
            category_type = "rare"
        elif any(keyword in prize_name.lower() for keyword in ['smart tv', 'silver coin', 'refrigerator', 'washing', 'aircooler', 'smartphone']):
            expected_limit = 1  # Ultra-rare items  
            category_type = "ultra-rare"
        else:
            expected_limit = 100  # Common items (high limit)
            category_type = "common"
        
        status = "✅ OK" if count <= expected_limit else "❌ VIOLATION"
        if count > expected_limit:
            violations += 1
        
        print(f"  {prize_name}: {count} wins (limit: {expected_limit}) - {status}")
    
    print(f"\n🎯 DAILY LIMITS ENFORCEMENT RESULTS:")
    if violations == 0:
        print("✅ PERFECT! All daily limits respected")
        return True
    else:
        print(f"❌ {violations} daily limit violations detected")
        return False

if __name__ == "__main__":
    success = test_daily_limits(20)
    exit(0 if success else 1)
