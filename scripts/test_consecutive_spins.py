#!/usr/bin/env python3
"""
Test Consecutive Spins
Simulates multiple consecutive spins to verify wheel rotation works correctly
"""

import json
import time
import subprocess

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

def simulate_wheel_rotation(current_rotation, target_segment, total_segments):
    """Simulate the frontend wheel rotation calculation"""
    segment_angle = 360 / total_segments
    target_segment_center = target_segment * segment_angle + (segment_angle / 2)
    target_final_position = 360 - target_segment_center
    
    # Normalize to 0-360 range
    target_final_position = target_final_position % 360
    if target_final_position < 0:
        target_final_position += 360
    
    # Get current position (normalized)
    current_position = current_rotation % 360
    
    # Calculate rotation needed
    rotation_needed = target_final_position - current_position
    if rotation_needed <= 0:
        rotation_needed += 360
    
    # Add extra spins (simulate 10 spins for testing)
    extra_spins = 10
    total_rotation_increment = rotation_needed + (extra_spins * 360)
    final_absolute_rotation = current_rotation + total_rotation_increment
    
    return final_absolute_rotation, target_final_position

def test_consecutive_spins(num_spins=5):
    """Test multiple consecutive spins"""
    print(f"🧪 Testing {num_spins} Consecutive Spins")
    print("=" * 60)
    
    base_url = "http://localhost:8082"
    current_wheel_rotation = 0  # Track simulated wheel position
    
    for spin_num in range(1, num_spins + 1):
        print(f"\n🎯 SPIN #{spin_num}")
        print("-" * 30)
        
        # Step 1: Pre-spin
        print("1. Getting backend selection...")
        prespin_data = run_curl(f"{base_url}/api/pre-spin", "POST")
        
        if not prespin_data or not prespin_data.get('success'):
            print(f"❌ Pre-spin failed: {prespin_data.get('error') if prespin_data else 'No response'}")
            continue
        
        selected_prize = prespin_data['selected_prize']
        target_segment = prespin_data['target_segment_index']
        total_segments = prespin_data['total_segments']
        
        print(f"   Backend selected: {selected_prize['name']} (ID: {selected_prize['id']})")
        print(f"   Target segment: {target_segment}")
        
        # Step 2: Simulate frontend rotation calculation
        print("2. Simulating wheel rotation...")
        final_rotation, target_position = simulate_wheel_rotation(
            current_wheel_rotation, target_segment, total_segments
        )
        
        rotation_increment = final_rotation - current_wheel_rotation
        
        print(f"   Current wheel position: {current_wheel_rotation % 360:.1f}° (absolute: {current_wheel_rotation:.1f}°)")
        print(f"   Target final position: {target_position:.1f}°")
        print(f"   Rotation increment: {rotation_increment:.1f}°")
        print(f"   Final absolute rotation: {final_rotation:.1f}°")
        
        # Step 3: Verify the math
        predicted_final = final_rotation % 360
        print(f"   Predicted landing: {predicted_final:.1f}° (should be ~{target_position:.1f}°)")
        
        math_error = abs(predicted_final - target_position)
        if math_error > 1.0:  # Allow 1 degree tolerance
            print(f"   ⚠️  Math error: {math_error:.1f}° difference")
        else:
            print(f"   ✅ Math correct: {math_error:.1f}° difference")
        
        # Step 4: Confirm with backend
        print("3. Confirming with backend...")
        spin_data = {
            "selected_prize_id": selected_prize['id'],
            "target_segment_index": target_segment,
            "final_rotation": final_rotation
        }
        
        spin_result = run_curl(f"{base_url}/api/spin", "POST", spin_data)
        
        if not spin_result or not spin_result.get('success'):
            print(f"❌ Spin confirmation failed: {spin_result.get('error') if spin_result else 'No response'}")
            continue
        
        awarded_prize = spin_result['prize']
        print(f"   ✅ Prize awarded: {awarded_prize['name']} (ID: {awarded_prize['id']})")
        
        # Step 5: Verify consistency
        if selected_prize['id'] != awarded_prize['id']:
            print(f"   ⚠️  Prize mismatch: Selected {selected_prize['id']}, Awarded {awarded_prize['id']}")
        else:
            print(f"   ✅ Prize consistent: {selected_prize['name']}")
        
        # Update wheel position for next spin
        current_wheel_rotation = final_rotation
        
        # Brief pause between spins
        time.sleep(0.5)
    
    print(f"\n🎉 Completed {num_spins} consecutive spins!")
    print(f"📊 Final wheel position: {current_wheel_rotation % 360:.1f}° (absolute: {current_wheel_rotation:.1f}°)")

if __name__ == "__main__":
    test_consecutive_spins(5)
