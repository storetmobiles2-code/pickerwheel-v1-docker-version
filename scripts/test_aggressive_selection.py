#!/usr/bin/env python3
"""
Test the aggressive rare/ultra-rare selection logic
Verifies that rare items are won within 3-5 spins as expected
"""

import requests
import json
import time
from datetime import datetime

def test_aggressive_selection():
    """Test the aggressive selection logic with multiple simulation runs"""
    base_url = "http://localhost:8082"
    
    print("🚀 TESTING AGGRESSIVE RARE/ULTRA-RARE SELECTION")
    print("=" * 60)
    print("📋 Expected behavior:")
    print("   • Ultra-rare items: 80% chance in first 3 spins")
    print("   • Rare items: Guaranteed by spin 5 if no rare/ultra-rare won")
    print("   • Weighted selection favors scarce items")
    print()
    
    # Test multiple simulation runs
    simulation_runs = 10
    results = {
        'ultra_rare_in_first_3': 0,
        'rare_in_first_5': 0,
        'total_runs': simulation_runs,
        'spin_details': []
    }
    
    for run in range(1, simulation_runs + 1):
        print(f"🎯 SIMULATION RUN #{run}")
        print("-" * 40)
        
        # Reset database for clean test
        try:
            reset_response = requests.post(f"{base_url}/api/admin/reset-database", 
                                         json={"confirm": True},
                                         timeout=10)
            if reset_response.status_code == 200:
                print("✅ Database reset for clean test")
            else:
                print(f"⚠️  Database reset failed: {reset_response.status_code}")
        except Exception as e:
            print(f"⚠️  Database reset error: {e}")
        
        time.sleep(1)  # Allow reset to complete
        
        # Perform up to 5 spins to test the guarantee
        run_results = {
            'run': run,
            'spins': [],
            'first_rare_spin': None,
            'first_ultra_rare_spin': None
        }
        
        for spin_num in range(1, 6):  # Test first 5 spins
            try:
                print(f"  🎲 Spin #{spin_num}:")
                
                # Call pre-spin to get selected prize
                pre_spin_response = requests.post(f"{base_url}/api/pre-spin", 
                                                json={"user": f"test_user_run{run}"},
                                                timeout=10)
                
                if pre_spin_response.status_code == 200:
                    pre_spin_data = pre_spin_response.json()
                    selected_prize = pre_spin_data.get('selected_prize', {})
                    prize_name = selected_prize.get('name', 'Unknown')
                    prize_category = selected_prize.get('category', 'unknown')
                    
                    print(f"    Selected: {prize_name} ({prize_category})")
                    
                    # Confirm the spin
                    spin_response = requests.post(f"{base_url}/api/spin",
                                                json={"user": f"test_user_run{run}"},
                                                timeout=10)
                    
                    if spin_response.status_code == 200:
                        spin_data = spin_response.json()
                        confirmed_prize = spin_data.get('prize', {})
                        confirmed_name = confirmed_prize.get('name', prize_name)
                        confirmed_category = confirmed_prize.get('category', prize_category)
                        
                        print(f"    Confirmed: {confirmed_name} ({confirmed_category})")
                        
                        # Record the spin
                        spin_result = {
                            'spin_number': spin_num,
                            'prize_name': confirmed_name,
                            'category': confirmed_category
                        }
                        run_results['spins'].append(spin_result)
                        
                        # Track first rare/ultra-rare wins
                        if confirmed_category.lower() == 'ultra_rare' and run_results['first_ultra_rare_spin'] is None:
                            run_results['first_ultra_rare_spin'] = spin_num
                            print(f"    🌟 FIRST ULTRA-RARE WON ON SPIN #{spin_num}")
                        elif confirmed_category.lower() == 'rare' and run_results['first_rare_spin'] is None:
                            run_results['first_rare_spin'] = spin_num
                            print(f"    ⭐ FIRST RARE WON ON SPIN #{spin_num}")
                        
                        # Stop if we got a rare/ultra-rare item (success case)
                        if confirmed_category.lower() in ['rare', 'ultra_rare']:
                            print(f"    ✅ Rare/Ultra-rare achieved on spin #{spin_num}")
                            break
                    else:
                        print(f"    ❌ Spin confirmation failed: {spin_response.status_code}")
                        break
                else:
                    print(f"    ❌ Pre-spin failed: {pre_spin_response.status_code}")
                    break
                    
            except Exception as e:
                print(f"    ❌ Error on spin #{spin_num}: {e}")
                break
        
        # Analyze run results
        results['spin_details'].append(run_results)
        
        if run_results['first_ultra_rare_spin'] and run_results['first_ultra_rare_spin'] <= 3:
            results['ultra_rare_in_first_3'] += 1
        
        if (run_results['first_rare_spin'] and run_results['first_rare_spin'] <= 5) or \
           (run_results['first_ultra_rare_spin'] and run_results['first_ultra_rare_spin'] <= 5):
            results['rare_in_first_5'] += 1
        
        print(f"  📊 Run #{run} Summary:")
        if run_results['first_ultra_rare_spin']:
            print(f"    Ultra-rare won on spin #{run_results['first_ultra_rare_spin']}")
        if run_results['first_rare_spin']:
            print(f"    Rare won on spin #{run_results['first_rare_spin']}")
        if not run_results['first_rare_spin'] and not run_results['first_ultra_rare_spin']:
            print(f"    ⚠️  No rare/ultra-rare won in 5 spins")
        print()
        
        time.sleep(2)  # Brief pause between runs
    
    # Final analysis
    print("📊 FINAL RESULTS ANALYSIS")
    print("=" * 60)
    
    ultra_rare_success_rate = (results['ultra_rare_in_first_3'] / results['total_runs']) * 100
    rare_guarantee_rate = (results['rare_in_first_5'] / results['total_runs']) * 100
    
    print(f"🌟 Ultra-rare in first 3 spins: {results['ultra_rare_in_first_3']}/{results['total_runs']} ({ultra_rare_success_rate:.1f}%)")
    print(f"   Expected: ~80% | Actual: {ultra_rare_success_rate:.1f}%")
    
    print(f"⭐ Rare/Ultra-rare in first 5 spins: {results['rare_in_first_5']}/{results['total_runs']} ({rare_guarantee_rate:.1f}%)")
    print(f"   Expected: ~95-100% | Actual: {rare_guarantee_rate:.1f}%")
    
    print(f"\n📋 Detailed Results:")
    for run_detail in results['spin_details']:
        run_num = run_detail['run']
        first_rare = run_detail['first_rare_spin'] or "None"
        first_ultra = run_detail['first_ultra_rare_spin'] or "None"
        print(f"  Run #{run_num}: First rare={first_rare}, First ultra-rare={first_ultra}")
    
    # Success criteria
    print(f"\n🎯 SUCCESS CRITERIA:")
    ultra_rare_success = ultra_rare_success_rate >= 60  # Allow some variance
    rare_guarantee_success = rare_guarantee_rate >= 80  # Should be very high
    
    print(f"  ✅ Ultra-rare boost working: {'PASS' if ultra_rare_success else 'FAIL'}")
    print(f"  ✅ Rare guarantee working: {'PASS' if rare_guarantee_success else 'FAIL'}")
    
    overall_success = ultra_rare_success and rare_guarantee_success
    print(f"\n🏆 OVERALL TEST: {'✅ PASS' if overall_success else '❌ FAIL'}")
    
    if overall_success:
        print("🎉 Aggressive selection logic is working as expected!")
        print("   Rare and ultra-rare items will be won within 3-5 spins.")
    else:
        print("⚠️  Aggressive selection needs adjustment.")
        print("   Consider increasing boost percentages or weights.")

if __name__ == "__main__":
    test_aggressive_selection()
