#!/usr/bin/env python3
"""
Complete Flow Verification
Tests each step of the spin process to ensure perfect alignment
"""

import json
import subprocess
import time

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

def verify_complete_flow():
    """Verify the complete spin flow step by step"""
    print("🔍 COMPLETE FLOW VERIFICATION")
    print("=" * 60)
    
    base_url = "http://localhost:8082"
    
    # STEP 1: Get wheel display items
    print("\n📋 STEP 1: WHEEL DISPLAY ANALYSIS")
    print("-" * 40)
    
    wheel_data = run_curl(f"{base_url}/api/prizes/wheel-display")
    if not wheel_data or not wheel_data.get('success'):
        print("❌ Failed to get wheel display")
        return False
    
    wheel_items = wheel_data['prizes']
    print(f"✅ Loaded {len(wheel_items)} wheel items")
    
    # Create segment mapping
    segment_map = {}
    for i, item in enumerate(wheel_items):
        segment_map[i] = {
            'id': item['id'],
            'name': item['name'],
            'category': item['category'],
            'quantity': item.get('remaining_quantity', 0)
        }
    
    print("🗺️  Segment mapping (first 10):")
    for i in range(min(10, len(segment_map))):
        item = segment_map[i]
        print(f"   Segment {i}: {item['name']} (ID: {item['id']}) - Qty: {item['quantity']}")
    
    # STEP 2: Backend selection
    print("\n🎯 STEP 2: BACKEND SELECTION")
    print("-" * 40)
    
    prespin_data = run_curl(f"{base_url}/api/pre-spin", "POST")
    if not prespin_data or not prespin_data.get('success'):
        print("❌ Backend selection failed")
        return False
    
    selected_prize = prespin_data['selected_prize']
    target_segment = prespin_data['target_segment_index']
    
    print(f"✅ Backend selected: {selected_prize['name']} (ID: {selected_prize['id']})")
    print(f"✅ Target segment: {target_segment}")
    
    # STEP 3: Verify segment mapping
    print("\n🔗 STEP 3: SEGMENT MAPPING VERIFICATION")
    print("-" * 40)
    
    if target_segment >= len(segment_map):
        print(f"❌ Target segment {target_segment} is out of range (max: {len(segment_map)-1})")
        return False
    
    wheel_item_at_target = segment_map[target_segment]
    print(f"🎯 Target segment {target_segment} contains: {wheel_item_at_target['name']} (ID: {wheel_item_at_target['id']})")
    
    # Verify mapping
    if selected_prize['id'] != wheel_item_at_target['id']:
        print(f"❌ MAPPING MISMATCH!")
        print(f"   Backend selected: {selected_prize['name']} (ID: {selected_prize['id']})")
        print(f"   Wheel segment {target_segment}: {wheel_item_at_target['name']} (ID: {wheel_item_at_target['id']})")
        return False
    else:
        print(f"✅ Perfect mapping: Backend selection matches wheel segment")
    
    # STEP 4: Simulate rotation calculation
    print("\n🎡 STEP 4: ROTATION CALCULATION")
    print("-" * 40)
    
    total_segments = len(wheel_items)
    segment_angle = 360 / total_segments
    target_segment_center = target_segment * segment_angle + (segment_angle / 2)
    # ORIGINAL WORKING LOGIC: 360 - targetSegmentCenter
    target_final_position = 360 - target_segment_center
    
    # Normalize
    target_final_position = target_final_position % 360
    if target_final_position < 0:
        target_final_position += 360
    
    print(f"📐 Segment angle: {segment_angle:.2f}°")
    print(f"🎯 Target segment center: {target_segment_center:.2f}°")
    print(f"🎡 Target final position: {target_final_position:.2f}°")
    
    # STEP 5: Verify landing calculation
    print("\n🎯 STEP 5: LANDING VERIFICATION")
    print("-" * 40)
    
    # Simulate final wheel position using original working logic
    simulated_final_rotation = target_final_position
    wheel_position = simulated_final_rotation % 360
    segment_at_pointer = (360 - wheel_position) % 360
    calculated_segment = int(segment_at_pointer / segment_angle) % total_segments
    
    print(f"🎡 Simulated final position: {wheel_position:.2f}°")
    print(f"📍 Calculated landing segment: {calculated_segment}")
    
    if calculated_segment != target_segment:
        print(f"❌ LANDING MISMATCH!")
        print(f"   Expected segment: {target_segment}")
        print(f"   Calculated segment: {calculated_segment}")
        return False
    else:
        print(f"✅ Perfect landing calculation")
    
    # STEP 6: Backend confirmation
    print("\n🏆 STEP 6: BACKEND CONFIRMATION")
    print("-" * 40)
    
    spin_data = {
        "selected_prize_id": selected_prize['id'],
        "target_segment_index": target_segment,
        "final_rotation": 3600 + target_final_position  # Simulate 10 spins
    }
    
    spin_result = run_curl(f"{base_url}/api/spin", "POST", spin_data)
    if not spin_result or not spin_result.get('success'):
        print(f"❌ Backend confirmation failed: {spin_result.get('error') if spin_result else 'No response'}")
        return False
    
    awarded_prize = spin_result['prize']
    print(f"✅ Backend awarded: {awarded_prize['name']} (ID: {awarded_prize['id']})")
    
    # STEP 7: Final verification
    print("\n🔍 STEP 7: FINAL VERIFICATION")
    print("-" * 40)
    
    all_match = True
    
    # Check backend selection vs wheel segment
    if selected_prize['id'] != wheel_item_at_target['id']:
        print(f"❌ Backend selection doesn't match wheel segment")
        all_match = False
    else:
        print(f"✅ Backend selection matches wheel segment")
    
    # Check backend selection vs awarded prize
    if selected_prize['id'] != awarded_prize['id']:
        print(f"❌ Backend selection doesn't match awarded prize")
        all_match = False
    else:
        print(f"✅ Backend selection matches awarded prize")
    
    # Check wheel segment vs awarded prize
    if wheel_item_at_target['id'] != awarded_prize['id']:
        print(f"❌ Wheel segment doesn't match awarded prize")
        all_match = False
    else:
        print(f"✅ Wheel segment matches awarded prize")
    
    # Summary
    print(f"\n🎉 FINAL RESULT")
    print("=" * 60)
    
    if all_match:
        print("✅ PERFECT ALIGNMENT!")
        print(f"   Prize: {selected_prize['name']} (ID: {selected_prize['id']})")
        print(f"   Segment: {target_segment}")
        print(f"   All systems consistent")
        return True
    else:
        print("❌ ALIGNMENT ISSUES DETECTED!")
        print("   Check the errors above for details")
        return False

if __name__ == "__main__":
    success = verify_complete_flow()
    exit(0 if success else 1)
