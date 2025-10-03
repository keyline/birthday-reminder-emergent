#!/usr/bin/env python3
"""
Quick script to check what template types are actually created
"""

import requests
import time

def check_template_types():
    base_url = "https://remindhub-5.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    # Register user
    timestamp = int(time.time())
    user_data = {
        "email": f"typecheck{timestamp}@example.com",
        "password": "TestPass123!",
        "full_name": f"Type Check User {timestamp}"
    }
    
    response = requests.post(f"{api_url}/auth/register", json=user_data)
    if response.status_code != 200:
        print("Failed to register user")
        return
    
    token = response.json().get('access_token')
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    
    # Test creating template with invalid type
    invalid_template = {
        "name": "Invalid Type Template",
        "type": "sms",  # Invalid type
        "content": "Test SMS message",
        "whatsapp_image_url": "https://example.com/test.jpg"
    }
    
    response = requests.post(f"{api_url}/templates", json=invalid_template, headers=headers)
    print(f"Creating template with type 'sms': Status {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Template created successfully with type: {result.get('type')}")
        print(f"Template ID: {result.get('id')}")
        print("This indicates the backend accepts any template type (flexible design)")
    else:
        print(f"Template creation failed: {response.text}")
        print("This indicates the backend validates template types")

if __name__ == "__main__":
    check_template_types()