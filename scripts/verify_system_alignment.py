#!/usr/bin/env python3
"""
Comprehensive System Verification Script
Tests wheel alignment, backend logic, and daily item list integration
"""

import requests
import json
import sys
import time
from datetime import date, datetime
from typing import Dict, List, Tuple

class SystemVerifier:
    def __init__(self, base_url: str = "http://localhost:8082"):
        self.base_url = base_url
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        self.test_results.append({
            'test': test_name,
            'success': success,
            'details': details
        })
        
    def test_backend_connectivity(self) -> bool:
        """Test if backend is responding"""
        try:
            response = requests.get(f"{self.base_url}/api/prizes/wheel-display", timeout=5)
            return response.status_code == 200
        except Exception as e:
            self.log_test("Backend Connectivity", False, f"Error: {e}")
            return False
            
    def test_wheel_display_consistency(self) -> bool:
        """Test wheel display prizes consistency"""
        try:
            response = requests.get(f"{self.base_url}/api/prizes/wheel-display")
            data = response.json()
            
            if not data.get('success'):
                self.log_test("Wheel Display API", False, "API returned success=false")
                return False
                
            prizes = data.get('prizes', [])
            if len(prizes) != 21:
                self.log_test("Wheel Display Count", False, f"Expected 21 prizes, got {len(prizes)}")
                return False
                
            # Check ID consistency
            for i, prize in enumerate(prizes):
                expected_id = i + 1
                if prize.get('id') != expected_id:
                    self.log_test("Wheel Display ID Consistency", False, 
                                f"Prize {i}: Expected ID {expected_id}, got {prize.get('id')}")
                    return False
                    
            self.log_test("Wheel Display Consistency", True, f"All {len(prizes)} prizes have correct IDs")
            return True
            
        except Exception as e:
            self.log_test("Wheel Display API", False, f"Error: {e}")
            return False
            
    def test_available_prizes_logic(self) -> bool:
        """Test available prizes logic"""
        try:
            response = requests.get(f"{self.base_url}/api/prizes/available")
            data = response.json()
            
            if not data.get('success'):
                self.log_test("Available Prizes API", False, "API returned success=false")
                return False
                
            available_prizes = data.get('prizes', [])
            if len(available_prizes) == 0:
                self.log_test("Available Prizes", False, "No prizes available today")
                return False
                
            # Check that all available prizes have valid data
            for prize in available_prizes:
                required_fields = ['id', 'name', 'category', 'daily_limit', 'available_dates']
                for field in required_fields:
                    if field not in prize:
                        self.log_test("Available Prizes Data", False, f"Missing field: {field}")
                        return False
                        
            self.log_test("Available Prizes Logic", True, f"{len(available_prizes)} prizes available today")
            return True
            
        except Exception as e:
            self.log_test("Available Prizes API", False, f"Error: {e}")
            return False
            
    def test_pre_spin_mapping(self) -> bool:
        """Test pre-spin selection and mapping"""
        try:
            response = requests.post(f"{self.base_url}/api/pre-spin", 
                                   json={}, 
                                   headers={'Content-Type': 'application/json'})
            data = response.json()
            
            if not data.get('success'):
                self.log_test("Pre-spin API", False, f"API error: {data.get('error', 'Unknown')}")
                return False
                
            selected_prize = data.get('selected_prize', {})
            target_segment = data.get('target_segment_index')
            total_segments = data.get('total_segments')
            
            if target_segment is None or total_segments is None:
                self.log_test("Pre-spin Mapping", False, "Missing target_segment_index or total_segments")
                return False
                
            if target_segment >= total_segments:
                self.log_test("Pre-spin Mapping", False, 
                            f"Target segment {target_segment} >= total segments {total_segments}")
                return False
                
            # Get wheel display prizes to verify mapping
            wheel_response = requests.get(f"{self.base_url}/api/prizes/wheel-display")
            wheel_data = wheel_response.json()
            wheel_prizes = wheel_data.get('prizes', [])
            
            if target_segment >= len(wheel_prizes):
                self.log_test("Pre-spin Mapping", False, 
                            f"Target segment {target_segment} >= wheel prizes {len(wheel_prizes)}")
                return False
                
            wheel_prize_at_segment = wheel_prizes[target_segment]
            
            # Verify name mapping
            if selected_prize.get('name') != wheel_prize_at_segment.get('name'):
                self.log_test("Pre-spin Name Mapping", False, 
                            f"Selected: {selected_prize.get('name')}, "
                            f"Wheel segment {target_segment}: {wheel_prize_at_segment.get('name')}")
                return False
                
            self.log_test("Pre-spin Mapping", True, 
                        f"Selected: {selected_prize.get('name')} → Segment {target_segment}")
            return True
            
        except Exception as e:
            self.log_test("Pre-spin API", False, f"Error: {e}")
            return False
            
    def test_rotation_calculation(self, target_segment: int, total_segments: int) -> Tuple[float, float]:
        """Test rotation calculation logic"""
        segment_angle = 360 / total_segments
        target_segment_center = target_segment * segment_angle + (segment_angle / 2)
        target_final_rotation = 360 - target_segment_center
        
        # Normalize to 0-360 range
        target_final_rotation = target_final_rotation % 360
        if target_final_rotation < 0:
            target_final_rotation += 360
            
        return target_final_rotation, target_segment_center
        
    def test_verification_logic(self, final_rotation: float, total_segments: int) -> int:
        """Test verification logic"""
        segment_angle = 360 / total_segments
        wheel_position = final_rotation % 360
        actual_landed_segment = int(wheel_position / segment_angle) % total_segments
        return actual_landed_segment
        
    def test_full_spin_cycle(self) -> bool:
        """Test complete spin cycle"""
        try:
            # Step 1: Pre-spin selection
            pre_spin_response = requests.post(f"{self.base_url}/api/pre-spin", 
                                            json={}, 
                                            headers={'Content-Type': 'application/json'})
            pre_spin_data = pre_spin_response.json()
            
            if not pre_spin_data.get('success'):
                self.log_test("Full Spin Cycle", False, "Pre-spin failed")
                return False
                
            selected_prize = pre_spin_data.get('selected_prize', {})
            target_segment = pre_spin_data.get('target_segment_index')
            total_segments = pre_spin_data.get('total_segments')
            
            # Step 2: Calculate rotation
            target_final_rotation, segment_center = self.test_rotation_calculation(target_segment, total_segments)
            
            # Step 3: Simulate wheel landing (add some extra spins)
            extra_spins = 10
            total_rotation = extra_spins * 360 + target_final_rotation
            
            # Step 4: Verify alignment
            actual_landed_segment = self.test_verification_logic(total_rotation, total_segments)
            
            # Step 5: Check if alignment is correct
            if actual_landed_segment == target_segment:
                self.log_test("Full Spin Cycle", True, 
                            f"Perfect alignment: {selected_prize.get('name')} → Segment {target_segment}")
                return True
            else:
                self.log_test("Full Spin Cycle", False, 
                            f"Misalignment: Expected segment {target_segment}, got {actual_landed_segment}")
                return False
                
        except Exception as e:
            self.log_test("Full Spin Cycle", False, f"Error: {e}")
            return False
            
    def test_daily_item_list_integration(self) -> bool:
        """Test daily item list integration"""
        try:
            # Test that wheel display shows all items from itemlist_dates.txt
            wheel_response = requests.get(f"{self.base_url}/api/prizes/wheel-display")
            wheel_data = wheel_response.json()
            wheel_prizes = wheel_data.get('prizes', [])
            
            # Expected items from itemlist_dates.txt (first 10 for brevity)
            expected_items = [
                "smartwatch + mini cooler",
                "power bank + neckband", 
                "luggage bags",
                "Free pouch and screen guard",
                "Dinner Set",
                "Earbuds and G.Speaker",
                "jio tab",
                "intex home theatre",
                "zebronics home theatre",
                "Mi smart speaker"
            ]
            
            # Check that expected items are in wheel display
            wheel_names = [prize.get('name') for prize in wheel_prizes]
            for expected_item in expected_items:
                if expected_item not in wheel_names:
                    self.log_test("Daily Item List Integration", False, 
                                f"Expected item '{expected_item}' not found in wheel display")
                    return False
                    
            self.log_test("Daily Item List Integration", True, 
                        f"All expected items found in wheel display ({len(wheel_prizes)} total)")
            return True
            
        except Exception as e:
            self.log_test("Daily Item List Integration", False, f"Error: {e}")
            return False
            
    def test_multiple_spins(self, num_spins: int = 5) -> bool:
        """Test multiple spins to ensure consistency"""
        successful_spins = 0
        
        for i in range(num_spins):
            try:
                # Pre-spin
                pre_spin_response = requests.post(f"{self.base_url}/api/pre-spin", 
                                                json={}, 
                                                headers={'Content-Type': 'application/json'})
                pre_spin_data = pre_spin_response.json()
                
                if not pre_spin_data.get('success'):
                    continue
                    
                selected_prize = pre_spin_data.get('selected_prize', {})
                target_segment = pre_spin_data.get('target_segment_index')
                total_segments = pre_spin_data.get('total_segments')
                
                # Calculate and verify
                target_final_rotation, _ = self.test_rotation_calculation(target_segment, total_segments)
                total_rotation = 10 * 360 + target_final_rotation
                actual_landed_segment = self.test_verification_logic(total_rotation, total_segments)
                
                if actual_landed_segment == target_segment:
                    successful_spins += 1
                    
            except Exception:
                continue
                
        success_rate = successful_spins / num_spins
        if success_rate >= 0.8:  # 80% success rate
            self.log_test("Multiple Spins Consistency", True, 
                        f"{successful_spins}/{num_spins} spins aligned correctly ({success_rate:.1%})")
            return True
        else:
            self.log_test("Multiple Spins Consistency", False, 
                        f"Only {successful_spins}/{num_spins} spins aligned correctly ({success_rate:.1%})")
            return False
            
    def run_all_tests(self) -> bool:
        """Run all verification tests"""
        print("🔍 Starting Comprehensive System Verification...")
        print("=" * 60)
        
        tests = [
            ("Backend Connectivity", self.test_backend_connectivity),
            ("Wheel Display Consistency", self.test_wheel_display_consistency),
            ("Available Prizes Logic", self.test_available_prizes_logic),
            ("Pre-spin Mapping", self.test_pre_spin_mapping),
            ("Full Spin Cycle", self.test_full_spin_cycle),
            ("Daily Item List Integration", self.test_daily_item_list_integration),
            ("Multiple Spins Consistency", lambda: self.test_multiple_spins(5))
        ]
        
        all_passed = True
        for test_name, test_func in tests:
            try:
                result = test_func()
                if not result:
                    all_passed = False
            except Exception as e:
                self.log_test(test_name, False, f"Exception: {e}")
                all_passed = False
                
        print("=" * 60)
        if all_passed:
            print("🎉 ALL TESTS PASSED! System is working perfectly!")
        else:
            print("⚠️  SOME TESTS FAILED! System needs attention.")
            
        return all_passed
        
    def print_summary(self):
        """Print test summary"""
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"\n📊 Test Summary: {passed}/{total} tests passed")
        
        if passed < total:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['details']}")

def main():
    """Main function"""
    verifier = SystemVerifier()
    
    # Check if backend is running
    if not verifier.test_backend_connectivity():
        print("❌ Backend is not running or not accessible at http://localhost:8082")
        print("Please start the backend with: ./scripts/docker.sh start")
        sys.exit(1)
        
    # Run all tests
    success = verifier.run_all_tests()
    verifier.print_summary()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
