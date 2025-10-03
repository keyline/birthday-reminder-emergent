#!/usr/bin/env python3
"""
Focused test script for Indian phone number validation in user profile updates.
This script tests the enhanced Indian phone number validation as requested in the review.
"""

import requests
import sys
import json
import time

class IndianPhoneValidationTester:
    def __init__(self, base_url="https://birthday-buddy-16.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")

    def setup_user(self):
        """Create a test user and get authentication token"""
        timestamp = int(time.time())
        user_data = {
            "email": f"phonetest{timestamp}@example.com",
            "password": "TestPass123!",
            "full_name": f"Phone Test User {timestamp}"
        }
        
        try:
            response = requests.post(f"{self.api_url}/auth/register", json=user_data, timeout=10)
            if response.status_code == 200:
                result = response.json()
                self.token = result.get('access_token')
                self.user_id = result.get('user', {}).get('id')
                print(f"✅ Test user created: {user_data['email']}")
                return True
            else:
                print(f"❌ Failed to create test user: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Exception creating test user: {str(e)}")
            return False

    def test_phone_update(self, phone_number, expected_status, expected_cleaned=None, description=""):
        """Test a single phone number update"""
        if not self.token:
            self.log_test(f"Phone Test: {description}", False, "No auth token available")
            return False

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }
        
        data = {"phone_number": phone_number}
        
        try:
            response = requests.put(f"{self.api_url}/user/profile", json=data, headers=headers, timeout=10)
            
            if response.status_code == expected_status:
                if expected_status == 200 and expected_cleaned is not None:
                    # Verify the phone number was cleaned correctly
                    result = response.json()
                    actual_phone = result.get('phone_number')
                    if actual_phone == expected_cleaned:
                        self.log_test(f"✅ {description}", True, f"Cleaned to: {actual_phone}")
                        return True
                    else:
                        self.log_test(f"❌ {description}", False, f"Expected: {expected_cleaned}, Got: {actual_phone}")
                        return False
                elif expected_status != 200:
                    # For error cases, just check that we got the expected error status
                    try:
                        error_data = response.json()
                        error_msg = error_data.get('detail', 'Unknown error')
                        self.log_test(f"✅ {description}", True, f"Correctly rejected: {error_msg}")
                        return True
                    except:
                        self.log_test(f"✅ {description}", True, f"Correctly rejected with status {expected_status}")
                        return True
                else:
                    self.log_test(f"✅ {description}", True, "Success")
                    return True
            else:
                try:
                    error_data = response.json()
                    self.log_test(f"❌ {description}", False, f"Status: {response.status_code}, Expected: {expected_status}, Response: {error_data}")
                except:
                    self.log_test(f"❌ {description}", False, f"Status: {response.status_code}, Expected: {expected_status}, Response: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log_test(f"❌ {description}", False, f"Exception: {str(e)}")
            return False

    def run_indian_phone_tests(self):
        """Run comprehensive Indian phone number validation tests"""
        print("🇮🇳 Testing Enhanced Indian Phone Number Validation...")
        print("=" * 80)
        
        if not self.setup_user():
            print("❌ Failed to setup test user. Exiting.")
            return False

        success = True

        # Valid Indian Phone Number Tests
        print("\n📱 Testing Valid Indian Phone Numbers...")
        valid_tests = [
            # Basic valid numbers
            ("9876543210", 200, "9876543210", "Valid 10-digit starting with 9"),
            ("8765432109", 200, "8765432109", "Valid 10-digit starting with 8"),
            ("7654321098", 200, "7654321098", "Valid 10-digit starting with 7"),
            ("6543210987", 200, "6543210987", "Valid 10-digit starting with 6"),
            
            # Numbers with +91 prefix (should be cleaned)
            ("+919876543210", 200, "9876543210", "Number with +91 prefix"),
            ("+918765432109", 200, "8765432109", "Another +91 prefix number"),
            
            # Numbers with 91 prefix (should be cleaned)
            ("919876543210", 200, "9876543210", "Number with 91 prefix (12 digits)"),
            ("918765432109", 200, "8765432109", "Another 91 prefix number"),
            
            # Numbers with spaces and formatting (should be cleaned)
            ("+91 98765 43210", 200, "9876543210", "Number with +91 and spaces"),
            ("91 8765 432 109", 200, "8765432109", "Number with 91 and spaces"),
            (" 9876543210 ", 200, "9876543210", "Number with leading/trailing spaces"),
            
            # Numbers with dashes and parentheses (should be cleaned)
            ("98765-43210", 200, "9876543210", "Number with dashes"),
            ("(987) 654-3210", 200, "9876543210", "Number with parentheses and dashes"),
            ("+91-98765-43210", 200, "9876543210", "Number with +91 and dashes"),
            ("91-(876)-543-2109", 200, "8765432109", "Number with 91, parentheses and dashes"),
        ]
        
        for phone, expected_status, expected_cleaned, description in valid_tests:
            if not self.test_phone_update(phone, expected_status, expected_cleaned, description):
                success = False

        # Invalid Indian Phone Number Tests
        print("\n❌ Testing Invalid Indian Phone Numbers...")
        invalid_tests = [
            # Numbers not starting with 6-9
            ("5876543210", 400, "Number starting with 5 (invalid)"),
            ("4876543210", 400, "Number starting with 4 (invalid)"),
            ("3876543210", 400, "Number starting with 3 (invalid)"),
            ("2876543210", 400, "Number starting with 2 (invalid)"),
            ("1876543210", 400, "Number starting with 1 (invalid)"),
            ("0876543210", 400, "Number starting with 0 (invalid)"),
            ("1234567890", 400, "Number starting with 1 (invalid)"),
            
            # Numbers with wrong length
            ("98765", 400, "Too short (5 digits)"),
            ("987654321", 400, "Too short (9 digits)"),
            ("98765432101", 400, "Too long (11 digits)"),
            ("987654321012", 400, "Too long (12 digits)"),
            ("+9198765432101", 400, "Too long with +91 prefix (13 digits total)"),
            
            # Numbers with non-digit characters
            ("98765abc10", 400, "Contains letters"),
            ("9876543@10", 400, "Contains special characters"),
            ("9876.543.210", 400, "Contains dots (not allowed)"),
            ("9876#543210", 400, "Contains hash symbol"),
            
            # Edge cases with prefixes
            ("+9198765", 400, "Too short even with +91"),
            ("9198765", 400, "Too short with 91 prefix"),
            ("+915876543210", 400, "+91 prefix with invalid starting digit 5"),
            ("915876543210", 400, "91 prefix with invalid starting digit 5"),
        ]
        
        for phone, expected_status, description in invalid_tests:
            if not self.test_phone_update(phone, expected_status, None, description):
                success = False

        # Edge Cases
        print("\n🔄 Testing Edge Cases...")
        edge_tests = [
            # Empty/null phone numbers (should be accepted and set to None)
            ("", 200, None, "Empty string"),
            ("   ", 200, None, "Whitespace only"),
            
            # Very long numbers with valid prefixes
            ("+919876543210123", 400, "Very long with +91"),
            ("919876543210123", 400, "Very long with 91"),
        ]
        
        for phone, expected_status, expected_cleaned, description in edge_tests:
            if not self.test_phone_update(phone, expected_status, expected_cleaned, description):
                success = False

        # Test null phone number explicitly
        print("\n🔄 Testing Null Phone Number...")
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }
        
        try:
            response = requests.put(f"{self.api_url}/user/profile", json={"phone_number": None}, headers=headers, timeout=10)
            if response.status_code == 400:
                self.log_test("✅ Null Phone Number", True, "Correctly rejected (no valid fields to update)")
            else:
                result = response.json() if response.status_code == 200 else {}
                self.log_test("❌ Null Phone Number", False, f"Expected 400, got {response.status_code}: {result}")
                success = False
        except Exception as e:
            self.log_test("❌ Null Phone Number", False, f"Exception: {str(e)}")
            success = False

        return success

    def run_all_tests(self):
        """Run all Indian phone number validation tests"""
        print("🚀 Starting Indian Phone Number Validation Tests...")
        print(f"Testing against: {self.base_url}")
        print("=" * 80)
        
        success = self.run_indian_phone_tests()
        
        # Print results
        print("=" * 80)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if success and self.tests_passed == self.tests_run:
            print("🎉 All Indian phone number validation tests passed!")
            return 0
        else:
            print("❌ Some tests failed. Check the details above.")
            return 1

def main():
    tester = IndianPhoneValidationTester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())