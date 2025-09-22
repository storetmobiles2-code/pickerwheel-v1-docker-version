#!/usr/bin/env python3
"""
Test Alignment Precision
Tests wheel alignment with precise mathematical verification
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

def test_alignment_precision(num_tests=10):
    """Test alignment precision with multiple spins"""
    print(f"🎯 TESTING ALIGNMENT PRECISION ({num_tests} tests)")
    print("=" * 60)
    
    base_url = "http://localhost:8082"
    current_wheel_rotation = 0
    perfect_alignments = 0
    
    for test_num in range(1, num_tests + 1):
        print(f"\n🎲 TEST #{test_num}")
        print("-" * 30)
        
        # Step 1: Get backend selection
        prespin_data = run_curl(f"{base_url}/api/pre-spin", "POST")
        if not prespin_data or not prespin_data.get('success'):
            print(f"❌ Backend selection failed")
            continue
        
        selected_prize = prespin_data['selected_prize']
        target_segment = prespin_data['target_segment_index']
        total_segments = prespin_data['total_segments']
        
        print(f"Backend selected: {selected_prize['name']} (ID: {selected_prize['id']})")
        print(f"Target segment: {target_segment}")
        
        # Step 2: Calculate expected rotation
        segment_angle = 360 / total_segments
        target_segment_center = target_segment * segment_angle + (segment_angle / 2)
        target_final_position = target_segment_center
        
        # Calculate rotation from current position
        current_position = current_wheel_rotation % 360
        rotation_needed = target_final_position - current_position
        if rotation_needed <= 0:
            rotation_needed += 360
        
        # Add whole number extra spins (8-11)
        extra_spins = 8 + (test_num % 4)  # Deterministic for testing
        total_rotation_increment = rotation_needed + (extra_spins * 360)
        final_absolute_rotation = current_wheel_rotation + total_rotation_increment
        
        print(f"Expected calculation:")
        print(f"  Current position: {current_position:.2f}°")
        print(f"  Target final position: {target_final_position:.2f}°")
        print(f"  Rotation needed: {rotation_needed:.2f}°")
        print(f"  Extra spins: {extra_spins}")
        print(f"  Final absolute rotation: {final_absolute_rotation:.2f}°")
        
        # Step 3: Verify math
        predicted_final_position = final_absolute_rotation % 360
        predicted_segment = int(predicted_final_position / segment_angle) % total_segments
        
        print(f"Math verification:")
        print(f"  Predicted final position: {predicted_final_position:.2f}°")
        print(f"  Predicted segment: {predicted_segment}")
        
        # Step 4: Test with backend
        spin_data = {
            "selected_prize_id": selected_prize['id'],
            "target_segment_index": target_segment,
            "final_rotation": final_absolute_rotation
        }
        
        spin_result = run_curl(f"{base_url}/api/spin", "POST", spin_data)
        if not spin_result or not spin_result.get('success'):
            print(f"❌ Backend confirmation failed")
            continue
        
        awarded_prize = spin_result['prize']
        
        # Step 5: Verify alignment
        math_error = abs(predicted_final_position - target_final_position)
        segment_match = predicted_segment == target_segment
        prize_match = selected_prize['id'] == awarded_prize['id']
        
        print(f"Results:")
        print(f"  Math error: {math_error:.6f}° (should be 0)")
        print(f"  Segment match: {'✅' if segment_match else '❌'} ({predicted_segment} vs {target_segment})")
        print(f"  Prize match: {'✅' if prize_match else '❌'} ({selected_prize['name']} vs {awarded_prize['name']})")
        
        if math_error < 0.001 and segment_match and prize_match:
            print(f"  ✅ PERFECT ALIGNMENT!")
            perfect_alignments += 1
        else:
            print(f"  ❌ ALIGNMENT ISSUE!")
        
        # Update wheel position for next test
        current_wheel_rotation = final_absolute_rotation
        
        time.sleep(0.2)  # Brief pause
    
    # Summary
    print(f"\n🎉 ALIGNMENT PRECISION SUMMARY")
    print("=" * 60)
    print(f"Total tests: {num_tests}")
    print(f"Perfect alignments: {perfect_alignments}")
    print(f"Success rate: {(perfect_alignments / num_tests * 100):.1f}%")
    
    if perfect_alignments == num_tests:
        print("🎯 PERFECT! All alignments are mathematically precise!")
        return True
    else:
        print(f"⚠️  {num_tests - perfect_alignments} alignment issues detected")
        return False

if __name__ == "__main__":
    success = test_alignment_precision(10)
    exit(0 if success else 1)
