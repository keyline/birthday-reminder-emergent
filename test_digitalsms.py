#!/usr/bin/env python3

import requests
import json

def test_digitalsms_api():
    """Test DigitalSMS API with minimal parameters"""
    
    # Test with minimal parameters (no real API key for now)
    url = "https://demo.digitalsms.biz/api"
    
    # Test parameters
    params = {
        "apikey": "test_key",  # This will likely fail, but let's see the error
        "mobile": "9876543210",
        "msg": "Test message from ReminderAI"
    }
    
    print("Testing DigitalSMS API...")
    print(f"URL: {url}")
    print(f"Params: {params}")
    print()
    
    try:
        response = requests.get(url, params=params, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Text: {response.text}")
        
        if response.status_code == 200:
            try:
                json_data = response.json()
                print(f"JSON Response: {json.dumps(json_data, indent=2)}")
            except:
                print("Response is not JSON")
        
        print("\n" + "="*50)
        
        # Test with image parameter
        params_with_image = params.copy()
        params_with_image["img1"] = "https://images.unsplash.com/photo-1530103862676-de8c9debad1d?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Njl8MHwxfHNlYXJjaHwxfHxiaXJ0aGRheSUyMGNlbGVicmF0aW9ufGVufDB8fHx8MTc1OTQ4ODk0Nnww&ixlib=rb-4.1.0&q=85&w=400&h=400&fit=crop"
        
        print("Testing with image parameter...")
        print(f"Params with image: {params_with_image}")
        
        response2 = requests.get(url, params=params_with_image, timeout=30)
        
        print(f"Status Code (with image): {response2.status_code}")
        print(f"Response Text (with image): {response2.text}")
        
        if response2.status_code == 200:
            try:
                json_data2 = response2.json()
                print(f"JSON Response (with image): {json.dumps(json_data2, indent=2)}")
            except:
                print("Response with image is not JSON")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_digitalsms_api()