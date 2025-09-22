#!/usr/bin/env python3
"""
Wheel Alignment Test Script
Performs multiple spins and verifies wheel lands on backend-selected prize
"""

import subprocess
import json
import time
import sys
from typing import Dict, List, Tuple, Any

class WheelAlignmentTester:
    def __init__(self, base_url: str = "http://localhost:8082"):
        self.base_url = base_url
        self.test_results = []
        self.alignment_stats = {
            'total_spins': 0,
            'perfect_alignments': 0,
            'misalignments': 0,
            'alignment_rate': 0.0
        }
        
    def run_curl_command(self, url: str, method: str = "GET", data: str = None) -> Dict[str, Any]:
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
    
    def get_wheel_display_prizes(self) -> List[Dict]:
        """Get all wheel display prizes"""
        response = self.run_curl_command(f"{self.base_url}/api/prizes/wheel-display")
        if 'error' in response:
            print(f"❌ Failed to get wheel display prizes: {response['error']}")
            return []
        return response.get('prizes', [])
    
    def perform_pre_spin(self) -> Dict[str, Any]:
        """Perform pre-spin to get backend selection"""
        response = self.run_curl_command(f"{self.base_url}/api/pre-spin", "POST", "{}")
        if 'error' in response:
            return {'error': response['error']}
        return response
    
    def simulate_wheel_rotation(self, target_segment: int, total_segments: int) -> Tuple[float, int]:
        """Simulate wheel rotation and calculate final position"""
        segment_angle = 360 / total_segments
        target_segment_center = target_segment * segment_angle + (segment_angle / 2)
        target_final_rotation = 360 - target_segment_center
        
        # Normalize to 0-360 range
        target_final_rotation = target_final_rotation % 360
        if target_final_rotation < 0:
            target_final_rotation += 360
        
        # Add exciting full rotations (8-12 spins)
        import random
        extra_spins = 8 + random.random() * 4
        total_rotation = (extra_spins * 360) + target_final_rotation
        
        # Calculate final position
        final_position = total_rotation % 360
        
        # Calculate which segment the wheel actually lands on
        actual_landed_segment = int(final_position / segment_angle) % total_segments
        
        return final_position, actual_landed_segment
    
    def verify_alignment(self, expected_segment: int, actual_segment: int, 
                        expected_prize: str, actual_prize: str) -> bool:
        """Verify if wheel alignment is correct"""
        is_aligned = expected_segment == actual_segment
        
        result = {
            'expected_segment': expected_segment,
            'actual_segment': actual_segment,
            'expected_prize': expected_prize,
            'actual_prize': actual_prize,
            'is_aligned': is_aligned
        }
        
        self.test_results.append(result)
        return is_aligned
    
    def perform_single_spin_test(self, spin_number: int) -> bool:
        """Perform a single spin test"""
        print(f"🎯 Spin #{spin_number:2d}: ", end="", flush=True)
        
        # Step 1: Get wheel display prizes
        wheel_prizes = self.get_wheel_display_prizes()
        if not wheel_prizes:
            print("❌ Failed to get wheel prizes")
            return False
        
        # Step 2: Perform pre-spin
        pre_spin_data = self.perform_pre_spin()
        if 'error' in pre_spin_data:
            print(f"❌ Pre-spin failed: {pre_spin_data['error']}")
            return False
        
        if not pre_spin_data.get('success'):
            print("❌ Pre-spin returned success=false")
            return False
        
        # Step 3: Extract backend selection
        selected_prize = pre_spin_data.get('selected_prize', {})
        target_segment = pre_spin_data.get('target_segment_index')
        total_segments = pre_spin_data.get('total_segments')
        
        if target_segment is None or total_segments is None:
            print("❌ Missing target segment or total segments")
            return False
        
        # Step 4: Simulate wheel rotation
        final_position, actual_landed_segment = self.simulate_wheel_rotation(target_segment, total_segments)
        
        # Step 5: Get expected and actual prizes
        expected_prize = selected_prize.get('name', 'Unknown')
        actual_prize = wheel_prizes[actual_landed_segment].get('name', 'Unknown') if actual_landed_segment < len(wheel_prizes) else 'Unknown'
        
        # Step 6: Verify alignment
        is_aligned = self.verify_alignment(target_segment, actual_landed_segment, expected_prize, actual_prize)
        
        # Step 7: Update stats
        self.alignment_stats['total_spins'] += 1
        if is_aligned:
            self.alignment_stats['perfect_alignments'] += 1
            print(f"✅ {expected_prize} → Segment {target_segment} (Perfect!)")
        else:
            self.alignment_stats['misalignments'] += 1
            print(f"❌ Expected: {expected_prize} → Segment {target_segment}, Got: {actual_prize} → Segment {actual_landed_segment}")
        
        return is_aligned
    
    def run_alignment_test(self, num_spins: int = 50) -> bool:
        """Run comprehensive alignment test"""
        print(f"🎡 Starting Wheel Alignment Test ({num_spins} spins)")
        print("=" * 80)
        
        successful_spins = 0
        
        for i in range(1, num_spins + 1):
            try:
                if self.perform_single_spin_test(i):
                    successful_spins += 1
                
                # Small delay to avoid overwhelming the server
                time.sleep(0.1)
                
            except Exception as e:
                print(f"❌ Spin #{i} failed with exception: {e}")
                continue
        
        # Calculate final statistics
        self.alignment_stats['alignment_rate'] = (self.alignment_stats['perfect_alignments'] / self.alignment_stats['total_spins']) * 100
        
        print("\n" + "=" * 80)
        print("📊 ALIGNMENT TEST RESULTS")
        print("=" * 80)
        print(f"Total Spins: {self.alignment_stats['total_spins']}")
        print(f"Perfect Alignments: {self.alignment_stats['perfect_alignments']}")
        print(f"Misalignments: {self.alignment_stats['misalignments']}")
        print(f"Alignment Rate: {self.alignment_stats['alignment_rate']:.1f}%")
        
        # Determine if test passed
        success_threshold = 95.0  # 95% alignment rate required
        test_passed = self.alignment_stats['alignment_rate'] >= success_threshold
        
        if test_passed:
            print(f"🎉 TEST PASSED! Alignment rate ({self.alignment_stats['alignment_rate']:.1f}%) meets threshold ({success_threshold}%)")
        else:
            print(f"❌ TEST FAILED! Alignment rate ({self.alignment_stats['alignment_rate']:.1f}%) below threshold ({success_threshold}%)")
        
        return test_passed
    
    def analyze_misalignments(self):
        """Analyze misalignment patterns"""
        if not self.test_results:
            return
        
        misalignments = [r for r in self.test_results if not r['is_aligned']]
        
        if not misalignments:
            print("\n🎯 No misalignments to analyze!")
            return
        
        print(f"\n🔍 MISALIGNMENT ANALYSIS ({len(misalignments)} cases)")
        print("-" * 60)
        
        # Group by expected segment
        segment_misalignments = {}
        for mis in misalignments:
            expected = mis['expected_segment']
            if expected not in segment_misalignments:
                segment_misalignments[expected] = []
            segment_misalignments[expected].append(mis)
        
        for expected_segment, mis_list in segment_misalignments.items():
            print(f"\nExpected Segment {expected_segment}:")
            actual_segments = [m['actual_segment'] for m in mis_list]
            segment_counts = {}
            for seg in actual_segments:
                segment_counts[seg] = segment_counts.get(seg, 0) + 1
            
            for actual_seg, count in sorted(segment_counts.items()):
                print(f"  → Actually landed on segment {actual_seg}: {count} times")
    
    def print_detailed_results(self):
        """Print detailed results for each spin"""
        print(f"\n📋 DETAILED RESULTS ({len(self.test_results)} spins)")
        print("-" * 80)
        
        for i, result in enumerate(self.test_results, 1):
            status = "✅" if result['is_aligned'] else "❌"
            print(f"{i:2d}. {status} Expected: Segment {result['expected_segment']} ({result['expected_prize']}) "
                  f"→ Got: Segment {result['actual_segment']} ({result['actual_prize']})")

def main():
    """Main function"""
    print("🚀 Wheel Alignment Test Suite")
    print("Testing backend selection vs wheel landing accuracy")
    print()
    
    tester = WheelAlignmentTester()
    
    # Check if backend is running
    test_response = tester.run_curl_command("http://localhost:8082/api/prizes/wheel-display")
    if 'error' in test_response:
        print("❌ Backend is not running or not accessible at http://localhost:8082")
        print("Please start the backend with: ./scripts/docker.sh start")
        sys.exit(1)
    
    # Run the alignment test
    success = tester.run_alignment_test(50)
    
    # Analyze results
    tester.analyze_misalignments()
    
    # Print detailed results (first 10 and last 10)
    if len(tester.test_results) > 20:
        print(f"\n📋 DETAILED RESULTS (First 10 and Last 10 of {len(tester.test_results)} spins)")
        print("-" * 80)
        
        # First 10
        for i, result in enumerate(tester.test_results[:10], 1):
            status = "✅" if result['is_aligned'] else "❌"
            print(f"{i:2d}. {status} Expected: Segment {result['expected_segment']} ({result['expected_prize']}) "
                  f"→ Got: Segment {result['actual_segment']} ({result['actual_prize']})")
        
        print("... (middle results omitted) ...")
        
        # Last 10
        for i, result in enumerate(tester.test_results[-10:], len(tester.test_results)-9):
            status = "✅" if result['is_aligned'] else "❌"
            print(f"{i:2d}. {status} Expected: Segment {result['expected_segment']} ({result['expected_prize']}) "
                  f"→ Got: Segment {result['actual_segment']} ({result['actual_prize']})")
    else:
        tester.print_detailed_results()
    
    print("\n" + "=" * 80)
    if success:
        print("🎉 WHEEL ALIGNMENT TEST PASSED!")
        print("✅ Backend selection and wheel landing are properly synchronized")
    else:
        print("❌ WHEEL ALIGNMENT TEST FAILED!")
        print("⚠️  Backend selection and wheel landing are not synchronized")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
