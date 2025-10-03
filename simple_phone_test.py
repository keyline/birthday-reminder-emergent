#!/usr/bin/env python3
"""
Simple focused test for Indian phone number validation
"""

import requests
import time

def test_indian_phone_validation():
    base_url = "https://birthday-buddy-16.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    # Create test user
    timestamp = int(time.time())
    user_data = {
        "email": f"simpletest{timestamp}@example.com",
        "password": "TestPass123!",
        "full_name": f"Simple Test User {timestamp}"
    }
    
    print("🔧 Creating test user...")
    response = requests.post(f"{api_url}/auth/register", json=user_data, timeout=10)
    if response.status_code != 200:
        print(f"❌ Failed to create user: {response.status_code}")
        return False
    
    token = response.json().get('access_token')
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    
    print("✅ Test user created successfully")
    
    # Test cases
    test_cases = [
        # Valid cases
        {"phone": "9876543210", "expected_status": 200, "expected_result": "9876543210", "desc": "Valid 10-digit"},
        {"phone": "+919876543210", "expected_status": 200, "expected_result": "9876543210", "desc": "With +91 prefix"},
        {"phone": "919876543210", "expected_status": 200, "expected_result": "9876543210", "desc": "With 91 prefix"},
        {"phone": "+91 98765 43210", "expected_status": 200, "expected_result": "9876543210", "desc": "With spaces"},
        {"phone": "98765-43210", "expected_status": 200, "expected_result": "9876543210", "desc": "With dashes"},
        {"phone": "", "expected_status": 200, "expected_result": None, "desc": "Empty string"},
        
        # Invalid cases
        {"phone": "5876543210", "expected_status": 400, "expected_result": None, "desc": "Starting with 5"},
        {"phone": "98765", "expected_status": 400, "expected_result": None, "desc": "Too short"},
        {"phone": "98765432101", "expected_status": 400, "expected_result": None, "desc": "Too long"},
        {"phone": "98765abc10", "expected_status": 400, "expected_result": None, "desc": "Contains letters"},
    ]
    
    passed = 0
    total = len(test_cases)
    
    print(f"\n🇮🇳 Testing {total} Indian phone number scenarios...")
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: {test['desc']} - '{test['phone']}'")
        
        data = {"phone_number": test["phone"]}
        response = requests.put(f"{api_url}/user/profile", json=data, headers=headers, timeout=10)
        
        if response.status_code == test["expected_status"]:
            if test["expected_status"] == 200:
                result = response.json()
                actual_phone = result.get('phone_number')
                if actual_phone == test["expected_result"]:
                    print(f"   ✅ PASSED - Cleaned to: {actual_phone}")
                    passed += 1
                else:
                    print(f"   ❌ FAILED - Expected: {test['expected_result']}, Got: {actual_phone}")
            else:
                error_data = response.json()
                print(f"   ✅ PASSED - Correctly rejected: {error_data.get('detail', 'Unknown error')}")
                passed += 1
        else:
            try:
                error_data = response.json()
                print(f"   ❌ FAILED - Status: {response.status_code}, Expected: {test['expected_status']}, Error: {error_data}")
            except:
                print(f"   ❌ FAILED - Status: {response.status_code}, Expected: {test['expected_status']}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed!")
        return True
    else:
        print("❌ Some tests failed.")
        return False

if __name__ == "__main__":
    success = test_indian_phone_validation()
    exit(0 if success else 1)