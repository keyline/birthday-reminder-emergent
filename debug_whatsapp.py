import requests
import pandas as pd
import io

# Test with a single valid contact
BACKEND_URL = "https://birthday-alert-4.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

# First register and login
register_data = {
    "email": "debug_test@example.com",
    "password": "TestPass123!",
    "full_name": "Debug Test User"
}

print("Registering user...")
response = requests.post(f"{API_URL}/auth/register", json=register_data)
print(f"Register response: {response.status_code}")

if response.status_code == 200:
    token = response.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    
    # Test single contact with WhatsApp
    test_data = [{
        'name': 'Test User',
        'birthday': '15-05',
        'anniversary': '',
        'email': 'test@example.com',
        'whatsapp': '+1234567890'
    }]
    
    df = pd.DataFrame(test_data)
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False)
    buffer.seek(0)
    
    print("\nUploading single contact...")
    files = {'file': ('test.xlsx', buffer, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
    response = requests.post(f"{API_URL}/contacts/bulk-upload", files=files, headers=headers)
    
    print(f"Upload response: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Result: {result}")
    else:
        print(f"Error: {response.text}")
else:
    print(f"Registration failed: {response.text}")