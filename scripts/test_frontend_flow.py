#!/usr/bin/env python3
"""
Test Frontend Flow
Simulates the frontend JavaScript flow to identify issues
"""

import requests
import json
import time

BASE_URL = "http://localhost:8082"

def test_frontend_flow():
    """Test the complete frontend flow"""
    print("🧪 Testing Frontend Flow")
    print("=" * 50)
    
    try:
        # Step 1: Load wheel display
        print("1. Loading wheel display...")
        response = requests.get(f"{BASE_URL}/api/prizes/wheel-display")
        if response.status_code != 200:
            print(f"❌ Wheel display failed: {response.status_code}")
            return False
        
        wheel_data = response.json()
        print(f"✅ Loaded {wheel_data.get('total_items')} prizes for wheel")
        
        # Step 2: Pre-spin (backend selects prize)
        print("\n2. Pre-spin (backend selection)...")
        response = requests.post(f"{BASE_URL}/api/pre-spin", json={})
        if response.status_code != 200:
            print(f"❌ Pre-spin failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        prespin_data = response.json()
        if not prespin_data.get('success'):
            print(f"❌ Pre-spin unsuccessful: {prespin_data.get('error')}")
            return False
        
        selected_prize = prespin_data['selected_prize']
        target_segment = prespin_data['target_segment_index']
        
        print(f"✅ Backend selected: {selected_prize['name']} (ID: {selected_prize['id']})")
        print(f"   Target segment: {target_segment}")
        
        # Step 3: Simulate wheel animation (frontend would do this)
        print(f"\n3. Simulating wheel animation...")
        print(f"   Wheel would rotate to segment {target_segment}")
        time.sleep(1)  # Simulate animation time
        
        # Step 4: Confirm spin (backend awards prize)
        print(f"\n4. Confirming spin with backend...")
        spin_data = {
            "selected_prize_id": selected_prize['id'],
            "target_segment_index": target_segment,
            "final_rotation": 360 * 10 + (target_segment * (360 / wheel_data['total_items']))  # Simulate rotation
        }
        
        response = requests.post(f"{BASE_URL}/api/spin", json=spin_data)
        if response.status_code != 200:
            print(f"❌ Spin confirmation failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        spin_result = response.json()
        if not spin_result.get('success'):
            print(f"❌ Spin confirmation unsuccessful: {spin_result.get('error')}")
            return False
        
        awarded_prize = spin_result['prize']
        print(f"✅ Prize awarded: {awarded_prize['name']} (ID: {awarded_prize['id']})")
        
        # Step 5: Verify data consistency
        print(f"\n5. Verifying data consistency...")
        if selected_prize['id'] != awarded_prize['id']:
            print(f"⚠️  Prize ID mismatch: Selected {selected_prize['id']}, Awarded {awarded_prize['id']}")
        else:
            print(f"✅ Prize IDs match: {selected_prize['id']}")
        
        if selected_prize['name'] != awarded_prize['name']:
            print(f"⚠️  Prize name mismatch: Selected '{selected_prize['name']}', Awarded '{awarded_prize['name']}'")
        else:
            print(f"✅ Prize names match: '{selected_prize['name']}'")
        
        print(f"\n🎉 Frontend flow test completed successfully!")
        print(f"📊 Final result: {awarded_prize['name']} ({awarded_prize['category']})")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False

if __name__ == "__main__":
    success = test_frontend_flow()
    exit(0 if success else 1)
