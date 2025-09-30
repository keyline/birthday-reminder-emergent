import requests
import pandas as pd
import io
from datetime import datetime

# Test with the provided CSV file after fix
BACKEND_URL = "https://birthday-alert-4.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

# Register and login with unique email
timestamp = datetime.now().strftime('%H%M%S')
register_data = {
    "email": f"csv_test_fixed_{timestamp}@example.com",
    "password": "TestPass123!",
    "full_name": "CSV Test Fixed User"
}

print("Registering user...")
response = requests.post(f"{API_URL}/auth/register", json=register_data)
print(f"Register response: {response.status_code}")

if response.status_code == 200:
    token = response.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    
    # Read the provided CSV file and convert to Excel
    print("\nReading provided CSV file...")
    df = pd.read_csv('/tmp/enhanced_test_contacts.csv', dtype={'whatsapp': str})
    print("CSV content after dtype fix:")
    print(df)
    print("\nWhatsApp column values:")
    for i, val in enumerate(df['whatsapp']):
        print(f"  Row {i+1}: '{val}' (type: {type(val)})")
    
    # Convert to Excel format
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False)
    buffer.seek(0)
    
    print("\nUploading provided CSV as Excel...")
    files = {'file': ('enhanced_test_contacts.xlsx', buffer, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
    response = requests.post(f"{API_URL}/contacts/bulk-upload", files=files, headers=headers)
    
    print(f"Upload response: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"\n📊 Upload Results:")
        print(f"   Total rows: {result.get('total_rows', 0)}")
        print(f"   Successful imports: {result.get('successful_imports', 0)}")
        print(f"   Failed imports: {result.get('failed_imports', 0)}")
        print(f"   Errors ({len(result.get('errors', []))}):")
        for error in result.get('errors', []):
            print(f"     • {error}")
            
        print(f"\n✅ Successfully imported contacts:")
        for contact in result.get('imported_contacts', []):
            print(f"   • {contact['name']} - Email: {contact.get('email', 'N/A')} - WhatsApp: {contact.get('whatsapp', 'N/A')}")
    else:
        print(f"Error: {response.text}")
else:
    print(f"Registration failed: {response.text}")