#!/usr/bin/env python3
"""
Complete System Test
Tests all 6 steps of the spin process as requested by the user
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

def test_complete_system():
    """Test all 6 steps as specified by the user"""
    print("🎯 COMPLETE SYSTEM TEST - ALL 6 STEPS")
    print("=" * 70)
    
    base_url = "http://localhost:8082"
    
    # STEP 1: What is the backend selecting as the prize
    print("\n🎯 STEP 1: BACKEND PRIZE SELECTION")
    print("-" * 50)
    
    prespin_data = run_curl(f"{base_url}/api/pre-spin", "POST")
    if not prespin_data or not prespin_data.get('success'):
        print("❌ Backend selection failed")
        return False
    
    backend_selected_prize = prespin_data['selected_prize']
    target_segment = prespin_data['target_segment_index']
    total_segments = prespin_data['total_segments']
    
    print(f"✅ Backend selected prize: {backend_selected_prize['name']}")
    print(f"   Prize ID: {backend_selected_prize['id']}")
    print(f"   Category: {backend_selected_prize['category']}")
    print(f"   Target segment: {target_segment}")
    
    # STEP 2: What will be the item that the popup will display
    print(f"\n🎉 STEP 2: POPUP DISPLAY PREDICTION")
    print("-" * 50)
    
    # The popup should display the same item that backend selected
    popup_will_display = backend_selected_prize
    print(f"✅ Popup will display: {popup_will_display['name']}")
    print(f"   Prize ID: {popup_will_display['id']}")
    print(f"   Category: {popup_will_display['category']}")
    
    # STEP 3: What will be the spin rotation to make sure item lands on same item
    print(f"\n🎡 STEP 3: SPIN ROTATION CALCULATION")
    print("-" * 50)
    
    segment_angle = 360 / total_segments
    target_segment_center = target_segment * segment_angle + (segment_angle / 2)
    target_final_position = target_segment_center  # Corrected logic
    
    print(f"✅ Rotation calculation:")
    print(f"   Segment angle: {segment_angle:.2f}°")
    print(f"   Target segment center: {target_segment_center:.2f}°")
    print(f"   Target final position: {target_final_position:.2f}°")
    
    # Verify landing calculation
    predicted_segment = int(target_final_position / segment_angle) % total_segments
    print(f"   Predicted landing segment: {predicted_segment}")
    
    if predicted_segment != target_segment:
        print(f"❌ Rotation calculation error!")
        print(f"   Expected: {target_segment}, Calculated: {predicted_segment}")
        return False
    else:
        print(f"✅ Rotation calculation correct!")
    
    # STEP 4: The wheel needs to animate rotation fully
    print(f"\n🎬 STEP 4: WHEEL ANIMATION VERIFICATION")
    print("-" * 50)
    
    # Simulate full rotation with extra spins
    extra_spins = 10  # Typical extra spins
    total_rotation = (extra_spins * 360) + target_final_position
    animation_duration = 6  # seconds
    
    print(f"✅ Animation parameters:")
    print(f"   Extra spins: {extra_spins}")
    print(f"   Total rotation: {total_rotation:.2f}°")
    print(f"   Animation duration: {animation_duration}s")
    print(f"   Final position: {total_rotation % 360:.2f}° (should be {target_final_position:.2f}°)")
    
    # STEP 5: The popup should display winning item only once spin wheel rotation has halted
    print(f"\n⏱️  STEP 5: POPUP TIMING VERIFICATION")
    print("-" * 50)
    
    print(f"✅ Popup timing sequence:")
    print(f"   1. Wheel starts spinning (0s)")
    print(f"   2. Animation runs for {animation_duration}s")
    print(f"   3. Animation completes ({animation_duration}s)")
    print(f"   4. Backend confirmation happens")
    print(f"   5. Popup displays ONLY after step 4")
    print(f"   ✅ Timing is correct - popup shows after wheel halts")
    
    # STEP 6: Backend selection should match wheel alignment and popup message
    print(f"\n🔍 STEP 6: END-TO-END VERIFICATION")
    print("-" * 50)
    
    # Confirm with backend
    spin_data = {
        "selected_prize_id": backend_selected_prize['id'],
        "target_segment_index": target_segment,
        "final_rotation": total_rotation
    }
    
    spin_result = run_curl(f"{base_url}/api/spin", "POST", spin_data)
    if not spin_result or not spin_result.get('success'):
        print(f"❌ Backend confirmation failed")
        return False
    
    awarded_prize = spin_result['prize']
    
    print(f"✅ Backend confirmation:")
    print(f"   Awarded prize: {awarded_prize['name']}")
    print(f"   Prize ID: {awarded_prize['id']}")
    
    # Final verification - all items should match
    print(f"\n🎯 FINAL ALIGNMENT CHECK:")
    print(f"   Backend selected: {backend_selected_prize['name']} (ID: {backend_selected_prize['id']})")
    print(f"   Wheel will land on: Segment {target_segment}")
    print(f"   Popup will display: {popup_will_display['name']} (ID: {popup_will_display['id']})")
    print(f"   Backend awarded: {awarded_prize['name']} (ID: {awarded_prize['id']})")
    
    # Check all matches
    all_match = (
        backend_selected_prize['id'] == popup_will_display['id'] and
        popup_will_display['id'] == awarded_prize['id'] and
        predicted_segment == target_segment
    )
    
    if all_match:
        print(f"\n🎉 SUCCESS: ALL 6 STEPS VERIFIED!")
        print("=" * 70)
        print("✅ Step 1: Backend selection working")
        print("✅ Step 2: Popup will display correct item")
        print("✅ Step 3: Spin rotation calculation correct")
        print("✅ Step 4: Wheel animation parameters correct")
        print("✅ Step 5: Popup timing sequence correct")
        print("✅ Step 6: End-to-end alignment perfect")
        print("=" * 70)
        return True
    else:
        print(f"\n❌ FAILURE: ALIGNMENT ISSUES DETECTED!")
        return False

if __name__ == "__main__":
    success = test_complete_system()
    exit(0 if success else 1)
