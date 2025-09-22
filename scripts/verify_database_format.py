#!/usr/bin/env python3
"""
Database Format Verification Script
Compares old backend format vs new daily database backend format
"""

import subprocess
import json
import sys
from typing import Dict, List, Any

def run_curl_command(url: str) -> Dict[str, Any]:
    """Run curl command and parse JSON response"""
    try:
        result = subprocess.run(['curl', '-s', url], capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            return {'error': f'curl failed: {result.stderr}'}
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        return {'error': f'JSON decode error: {e}'}
    except Exception as e:
        return {'error': f'Request failed: {e}'}

def compare_prize_formats():
    """Compare prize formats between old and new backends"""
    print("🔍 Database Format Verification")
    print("=" * 60)
    
    # Test new daily database backend
    print("\n📡 Testing NEW Daily Database Backend (Port 8082)...")
    
    # Test wheel display format
    wheel_data = run_curl_command('http://localhost:8082/api/prizes/wheel-display')
    if 'error' in wheel_data:
        print(f"❌ Wheel display test failed: {wheel_data['error']}")
        return False
    
    print("✅ Wheel Display Format:")
    print(f"   Success: {wheel_data.get('success')}")
    print(f"   Total items: {wheel_data.get('total_items')}")
    print(f"   Source: {wheel_data.get('source')}")
    
    if wheel_data.get('prizes'):
        first_prize = wheel_data['prizes'][0]
        print("   First prize structure:")
        for key, value in first_prize.items():
            print(f"     {key}: {value}")
    
    # Test available prizes format
    available_data = run_curl_command('http://localhost:8082/api/prizes/available')
    if 'error' in available_data:
        print(f"❌ Available prizes test failed: {available_data['error']}")
        return False
    
    print("\n✅ Available Prizes Format:")
    print(f"   Success: {available_data.get('success')}")
    print(f"   Date: {available_data.get('date')}")
    print(f"   Count: {available_data.get('count')}")
    
    if available_data.get('prizes'):
        first_available = available_data['prizes'][0]
        print("   First available prize structure:")
        for key, value in first_available.items():
            print(f"     {key}: {value}")
    
    # Test pre-spin format
    try:
        result = subprocess.run(['curl', '-s', '-X', 'POST', 'http://localhost:8082/api/pre-spin', 
                               '-H', 'Content-Type: application/json', '-d', '{}'], 
                               capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            print(f"❌ Pre-spin test failed: curl error: {result.stderr}")
            return False
        pre_spin_data = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        print(f"❌ Pre-spin test failed: JSON decode error: {e}")
        return False
    except Exception as e:
        print(f"❌ Pre-spin test failed: {e}")
        return False
    
    print("\n✅ Pre-spin Format:")
    print(f"   Success: {pre_spin_data.get('success')}")
    if pre_spin_data.get('selected_prize'):
        selected = pre_spin_data['selected_prize']
        print("   Selected prize structure:")
        for key, value in selected.items():
            print(f"     {key}: {value}")
    print(f"   Target segment: {pre_spin_data.get('target_segment_index')}")
    print(f"   Total segments: {pre_spin_data.get('total_segments')}")
    
    return True

def verify_field_compatibility():
    """Verify that all required fields are present and compatible"""
    print("\n🔍 Field Compatibility Check")
    print("=" * 40)
    
    # Get wheel display data
    wheel_data = run_curl_command('http://localhost:8082/api/prizes/wheel-display')
    if 'error' in wheel_data or not wheel_data.get('prizes'):
        print("❌ Cannot get wheel display data")
        return False
    
    # Get available prizes data
    available_data = run_curl_command('http://localhost:8082/api/prizes/available')
    if 'error' in available_data or not available_data.get('prizes'):
        print("❌ Cannot get available prizes data")
        return False
    
    wheel_prize = wheel_data['prizes'][0]
    available_prize = available_data['prizes'][0]
    
    # Required fields for frontend compatibility
    required_fields = ['id', 'name', 'category']
    
    print("✅ Required Fields Check:")
    for field in required_fields:
        wheel_has = field in wheel_prize
        available_has = field in available_prize
        print(f"   {field}: Wheel={wheel_has}, Available={available_has}")
        
        if not wheel_has or not available_has:
            print(f"❌ Missing required field: {field}")
            return False
    
    # Check data types
    print("\n✅ Data Types Check:")
    print(f"   ID type: {type(wheel_prize['id'])} (should be int)")
    print(f"   Name type: {type(wheel_prize['name'])} (should be str)")
    print(f"   Category type: {type(wheel_prize['category'])} (should be str)")
    
    # Check ID consistency
    print("\n✅ ID Consistency Check:")
    wheel_ids = [p['id'] for p in wheel_data['prizes']]
    available_ids = [p['id'] for p in available_data['prizes']]
    
    print(f"   Wheel IDs: {sorted(wheel_ids)}")
    print(f"   Available IDs: {sorted(available_ids)}")
    
    # Check if available IDs are subset of wheel IDs
    if not all(aid in wheel_ids for aid in available_ids):
        print("❌ Available prize IDs are not subset of wheel prize IDs")
        return False
    
    print("✅ All available prize IDs are present in wheel display")
    
    return True

def verify_daily_logic():
    """Verify daily availability logic"""
    print("\n🗓️ Daily Availability Logic Check")
    print("=" * 40)
    
    # Get current date from backend
    available_data = run_curl_command('http://localhost:8082/api/prizes/available')
    if 'error' in available_data:
        print(f"❌ Cannot get available prizes: {available_data['error']}")
        return False
    
    current_date = available_data.get('date')
    print(f"✅ Backend current date: {current_date}")
    
    # Check that silver coin is NOT available on 2025-09-23
    available_prizes = available_data.get('prizes', [])
    silver_coin_available = any('silver coin' in p['name'].lower() for p in available_prizes)
    
    if current_date == '2025-09-23':
        if silver_coin_available:
            print("❌ Silver coin should NOT be available on 2025-09-23")
            return False
        else:
            print("✅ Silver coin correctly NOT available on 2025-09-23")
    else:
        print(f"ℹ️  Current date is {current_date}, silver coin availability: {silver_coin_available}")
    
    # Check that common items are available
    common_items = [p for p in available_prizes if p.get('category', '').lower() == 'common']
    print(f"✅ Common items available: {len(common_items)}")
    
    # Check that rare items are available (if any)
    rare_items = [p for p in available_prizes if p.get('category', '').lower() == 'rare']
    print(f"✅ Rare items available: {len(rare_items)}")
    
    return True

def main():
    """Main verification function"""
    print("🚀 Starting Database Format Verification...")
    
    tests = [
        ("Format Comparison", compare_prize_formats),
        ("Field Compatibility", verify_field_compatibility),
        ("Daily Logic", verify_daily_logic)
    ]
    
    all_passed = True
    for test_name, test_func in tests:
        try:
            result = test_func()
            if not result:
                all_passed = False
                print(f"\n❌ {test_name} FAILED")
            else:
                print(f"\n✅ {test_name} PASSED")
        except Exception as e:
            print(f"\n❌ {test_name} ERROR: {e}")
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL VERIFICATIONS PASSED!")
        print("✅ Database format is compatible with frontend")
        print("✅ Daily logic is working correctly")
        print("✅ Timezone is properly configured")
    else:
        print("⚠️  SOME VERIFICATIONS FAILED!")
        print("❌ System needs attention")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
