#!/usr/bin/env python3
"""
Debug test to understand the 404 User not found issue
"""

import requests
import time
import json

def debug_phone_test():
    base_url = "https://remindhub-5.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    # Create test user
    timestamp = int(time.time())
    user_data = {
        "email": f"debugtest{timestamp}@example.com",
        "password": "TestPass123!",
        "full_name": f"Debug Test User {timestamp}"
    }
    
    print("🔧 Creating test user...")
    response = requests.post(f"{api_url}/auth/register", json=user_data, timeout=10)
    if response.status_code != 200:
        print(f"❌ Failed to create user: {response.status_code}")
        return False
    
    result = response.json()
    token = result.get('access_token')
    user_id = result.get('user', {}).get('id')
    
    print(f"✅ Test user created: {user_data['email']}")
    print(f"   User ID: {user_id}")
    print(f"   Token: {token[:20]}...")
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    
    # First, test a simple case that should work
    print("\n1. Testing simple case (9876543210)...")
    data = {"phone_number": "9876543210"}
    response = requests.put(f"{api_url}/user/profile", json=data, headers=headers, timeout=10)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"   Result: {result.get('phone_number')}")
    else:
        print(f"   Error: {response.text}")
    
    # Test the problematic case
    print("\n2. Testing problematic case (+919876543210)...")
    data = {"phone_number": "+919876543210"}
    print(f"   Request data: {json.dumps(data)}")
    print(f"   Headers: {headers}")
    
    response = requests.put(f"{api_url}/user/profile", json=data, headers=headers, timeout=10)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text}")
    
    # Check if user still exists
    print("\n3. Checking if user still exists...")
    response = requests.get(f"{api_url}/auth/me", headers=headers, timeout=10)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"   User exists: {result.get('email')}")
    else:
        print(f"   Error: {response.text}")
    
    # Try getting profile directly
    print("\n4. Getting user profile...")
    response = requests.get(f"{api_url}/user/profile", headers=headers, timeout=10)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"   Profile: {result}")
    else:
        print(f"   Error: {response.text}")

if __name__ == "__main__":
    debug_phone_test()