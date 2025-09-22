#!/usr/bin/env python3
"""
Debug Segment Mapping Script
Verifies segment mapping between frontend and backend
"""

import subprocess
import json
import sys

def run_curl_command(url: str, method: str = "GET", data: str = None) -> dict:
    """Run curl command and parse JSON response"""
    try:
        cmd = ['curl', '-s']
        if method == "POST":
            cmd.extend(['-X', 'POST', '-H', 'Content-Type: application/json'])
            if data:
                cmd.extend(['-d', data])
        cmd.append(url)
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            return {'error': f'curl failed: {result.stderr}'}
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        return {'error': f'JSON decode error: {e}'}
    except Exception as e:
        return {'error': f'Request failed: {e}'}

def debug_segment_mapping():
    """Debug segment mapping between frontend and backend"""
    print("🔍 Debugging Segment Mapping")
    print("=" * 60)
    
    # Get wheel display prizes
    wheel_response = run_curl_command("http://localhost:8082/api/prizes/wheel-display")
    if 'error' in wheel_response:
        print(f"❌ Failed to get wheel display: {wheel_response['error']}")
        return
    
    wheel_prizes = wheel_response.get('prizes', [])
    print(f"✅ Got {len(wheel_prizes)} wheel display prizes")
    
    # Print segment mapping
    print("\n📋 Wheel Segment Mapping:")
    print("-" * 60)
    for i, prize in enumerate(wheel_prizes):
        print(f"Segment {i:2d}: {prize['name']} (ID: {prize['id']})")
    
    # Test pre-spin multiple times
    print(f"\n🎯 Testing Pre-spin Selection (10 times):")
    print("-" * 60)
    
    segment_counts = {}
    for i in range(10):
        pre_spin_response = run_curl_command("http://localhost:8082/api/pre-spin", "POST", "{}")
        if 'error' in pre_spin_response:
            print(f"❌ Pre-spin {i+1} failed: {pre_spin_response['error']}")
            continue
        
        selected_prize = pre_spin_response.get('selected_prize', {})
        target_segment = pre_spin_response.get('target_segment_index')
        total_segments = pre_spin_response.get('total_segments')
        
        if target_segment is not None:
            segment_counts[target_segment] = segment_counts.get(target_segment, 0) + 1
            prize_name = selected_prize.get('name', 'Unknown')
            print(f"Spin {i+1:2d}: Selected {prize_name} → Segment {target_segment}")
    
    print(f"\n📊 Segment Selection Distribution:")
    print("-" * 60)
    for segment, count in sorted(segment_counts.items()):
        prize_name = wheel_prizes[segment]['name'] if segment < len(wheel_prizes) else 'Unknown'
        print(f"Segment {segment:2d} ({prize_name}): {count} times")
    
    # Test rotation calculation for each segment
    print(f"\n🔄 Testing Rotation Calculation:")
    print("-" * 60)
    
    total_segments = len(wheel_prizes)
    segment_angle = 360 / total_segments
    
    for target_segment in range(min(5, total_segments)):  # Test first 5 segments
        # Calculate rotation using segment CENTER (not start)
        target_segment_center = target_segment * segment_angle + (segment_angle / 2)
        target_final_rotation = 360 - target_segment_center
        target_final_rotation = target_final_rotation % 360
        if target_final_rotation < 0:
            target_final_rotation += 360
        
        # Add extra spins
        extra_spins = 10
        total_rotation = (extra_spins * 360) + target_final_rotation
        final_position = total_rotation % 360
        
        # Calculate which segment this lands on
        # The wheel rotates clockwise, so we need to account for the rotation direction
        # When the wheel rotates by X degrees, the segment that was at position X is now at the pointer (0°)
        actual_landed_segment = int(final_position / segment_angle) % total_segments
        
        prize_name = wheel_prizes[target_segment]['name']
        actual_prize_name = wheel_prizes[actual_landed_segment]['name'] if actual_landed_segment < len(wheel_prizes) else 'Unknown'
        
        is_correct = target_segment == actual_landed_segment
        status = "✅" if is_correct else "❌"
        
        print(f"{status} Target Segment {target_segment:2d} ({prize_name}):")
        print(f"    Center angle: {target_segment_center:.2f}°")
        print(f"    Target rotation: {target_final_rotation:.2f}°")
        print(f"    Final position: {final_position:.2f}°")
        print(f"    Lands on: Segment {actual_landed_segment} ({actual_prize_name})")
        print()

def main():
    """Main function"""
    debug_segment_mapping()

if __name__ == "__main__":
    main()
