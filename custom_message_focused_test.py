#!/usr/bin/env python3
"""
Focused test for Custom Message functionality as requested in the review.
Tests the specific scenarios mentioned in the review request.
"""

import requests
import json
import time
from datetime import datetime

class CustomMessageTester:
    def __init__(self, base_url="https://remindhub-5.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.contact_id = None
        self.tests_run = 0
        self.tests_passed = 0

    def log_result(self, test_name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {test_name}")
            if details:
                print(f"   {details}")
        else:
            print(f"❌ {test_name} - FAILED: {details}")

    def setup_test_user_and_contact(self):
        """Setup test user and contact for testing"""
        print("🔧 Setting up test user and contact...")
        
        # Register user
        timestamp = int(time.time())
        user_data = {
            "email": f"customtest{timestamp}@example.com",
            "password": "TestPass123!",
            "full_name": f"Custom Message Test User {timestamp}"
        }
        
        response = requests.post(f"{self.api_url}/auth/register", json=user_data)
        if response.status_code == 200:
            result = response.json()
            self.token = result.get('access_token')
            self.user_id = result.get('user', {}).get('id')
            print(f"   User created: {user_data['email']}")
        else:
            print(f"   Failed to create user: {response.text}")
            return False
        
        # Create contact
        contact_data = {
            "name": "Sarah Johnson",
            "email": "sarah.johnson@example.com",
            "whatsapp": "+1234567890",
            "birthday": "1985-03-15",
            "anniversary_date": "2018-07-20",
            "message_tone": "normal"
        }
        
        headers = {'Authorization': f'Bearer {self.token}', 'Content-Type': 'application/json'}
        response = requests.post(f"{self.api_url}/contacts", json=contact_data, headers=headers)
        if response.status_code == 200:
            result = response.json()
            self.contact_id = result.get('id')
            print(f"   Contact created: {contact_data['name']}")
            return True
        else:
            print(f"   Failed to create contact: {response.text}")
            return False

    def test_custom_message_crud_operations(self):
        """Test all CRUD operations for custom messages"""
        print("\n📝 Testing Custom Message CRUD Operations...")
        
        headers = {'Authorization': f'Bearer {self.token}', 'Content-Type': 'application/json'}
        
        # Test 1: Create custom WhatsApp birthday message
        whatsapp_birthday_data = {
            "contact_id": self.contact_id,
            "occasion": "birthday",
            "message_type": "whatsapp",
            "custom_message": "🎉 Happy Birthday Sarah! Hope your special day is filled with joy, laughter, and all your favorite things!",
            "image_url": "/uploads/birthday-celebration.jpg"
        }
        
        response = requests.post(f"{self.api_url}/custom-messages", json=whatsapp_birthday_data, headers=headers)
        success = response.status_code == 200
        self.log_result("Create WhatsApp Birthday Message", success, 
                       f"Message: {whatsapp_birthday_data['custom_message'][:50]}..." if success else response.text)
        
        # Test 2: Create custom Email anniversary message
        email_anniversary_data = {
            "contact_id": self.contact_id,
            "occasion": "anniversary",
            "message_type": "email",
            "custom_message": "💕 Happy Anniversary Sarah! Wishing you and your partner continued happiness and many more wonderful years together.",
            "image_url": "/uploads/anniversary-hearts.jpg"
        }
        
        response = requests.post(f"{self.api_url}/custom-messages", json=email_anniversary_data, headers=headers)
        success = response.status_code == 200
        self.log_result("Create Email Anniversary Message", success,
                       f"Message: {email_anniversary_data['custom_message'][:50]}..." if success else response.text)
        
        # Test 3: Get all custom messages for contact
        response = requests.get(f"{self.api_url}/custom-messages/{self.contact_id}", headers=headers)
        success = response.status_code == 200
        if success:
            messages = response.json()
            self.log_result("Get All Custom Messages", success, f"Found {len(messages)} custom messages")
        else:
            self.log_result("Get All Custom Messages", success, response.text)
        
        # Test 4: Get specific custom message (WhatsApp birthday)
        response = requests.get(f"{self.api_url}/custom-messages/{self.contact_id}/birthday/whatsapp", headers=headers)
        success = response.status_code == 200
        if success:
            message = response.json()
            self.log_result("Get Specific Custom Message", success, 
                           f"Retrieved: {message.get('custom_message', '')[:50]}...")
        else:
            self.log_result("Get Specific Custom Message", success, response.text)
        
        # Test 5: Get default AI-generated message (for non-existent custom message)
        response = requests.get(f"{self.api_url}/custom-messages/{self.contact_id}/birthday/email", headers=headers)
        success = response.status_code == 200
        if success:
            message = response.json()
            is_default = message.get('is_default', False)
            self.log_result("Get Default AI Message", success, 
                           f"AI Generated ({'Default' if is_default else 'Custom'}): {message.get('custom_message', '')[:50]}...")
        else:
            self.log_result("Get Default AI Message", success, response.text)
        
        # Test 6: Update existing custom message
        updated_whatsapp_data = {
            "contact_id": self.contact_id,
            "occasion": "birthday",
            "message_type": "whatsapp",
            "custom_message": "🎂 Updated Birthday Message! Sarah, hope you have the most amazing celebration ever!",
            "image_url": "/uploads/updated-birthday.jpg"
        }
        
        response = requests.post(f"{self.api_url}/custom-messages", json=updated_whatsapp_data, headers=headers)
        success = response.status_code == 200
        self.log_result("Update Custom Message", success,
                       f"Updated to: {updated_whatsapp_data['custom_message'][:50]}..." if success else response.text)
        
        # Test 7: Delete custom message
        response = requests.delete(f"{self.api_url}/custom-messages/{self.contact_id}/anniversary/email", headers=headers)
        success = response.status_code == 200
        self.log_result("Delete Custom Message", success, "Anniversary email message deleted" if success else response.text)

    def test_message_sending(self):
        """Test the send-test-message functionality"""
        print("\n📤 Testing Message Sending...")
        
        headers = {'Authorization': f'Bearer {self.token}', 'Content-Type': 'application/json'}
        
        # Test sending test message for birthday
        test_data = {
            "contact_id": self.contact_id,
            "occasion": "birthday"
        }
        
        response = requests.post(f"{self.api_url}/send-test-message", json=test_data, headers=headers)
        success = response.status_code == 200
        if success:
            result = response.json()
            whatsapp_status = result.get('results', {}).get('whatsapp', {}).get('status', 'N/A')
            email_status = result.get('results', {}).get('email', {}).get('status', 'N/A')
            self.log_result("Send Test Birthday Message", success, 
                           f"WhatsApp: {whatsapp_status}, Email: {email_status}")
        else:
            self.log_result("Send Test Birthday Message", success, response.text)
        
        # Test sending test message for anniversary
        test_data = {
            "contact_id": self.contact_id,
            "occasion": "anniversary"
        }
        
        response = requests.post(f"{self.api_url}/send-test-message", json=test_data, headers=headers)
        success = response.status_code == 200
        if success:
            result = response.json()
            whatsapp_status = result.get('results', {}).get('whatsapp', {}).get('status', 'N/A')
            email_status = result.get('results', {}).get('email', {}).get('status', 'N/A')
            self.log_result("Send Test Anniversary Message", success,
                           f"WhatsApp: {whatsapp_status}, Email: {email_status}")
        else:
            self.log_result("Send Test Anniversary Message", success, response.text)

    def test_integration_scenarios(self):
        """Test integration with existing systems"""
        print("\n🔗 Testing Integration Scenarios...")
        
        headers = {'Authorization': f'Bearer {self.token}', 'Content-Type': 'application/json'}
        
        # Test 1: Create messages for both WhatsApp and Email for different occasions
        test_scenarios = [
            {
                "occasion": "birthday",
                "message_type": "whatsapp",
                "message": "🎉 WhatsApp Birthday: Have an absolutely wonderful day Sarah!",
                "image": "/uploads/whatsapp-birthday.jpg"
            },
            {
                "occasion": "birthday", 
                "message_type": "email",
                "message": "📧 Email Birthday: Wishing you joy, happiness, and all the best on your special day!",
                "image": "/uploads/email-birthday.jpg"
            },
            {
                "occasion": "anniversary",
                "message_type": "whatsapp", 
                "message": "💕 WhatsApp Anniversary: Celebrating your love story today!",
                "image": "/uploads/whatsapp-anniversary.jpg"
            },
            {
                "occasion": "anniversary",
                "message_type": "email",
                "message": "💌 Email Anniversary: Here's to many more years of happiness together!",
                "image": "/uploads/email-anniversary.jpg"
            }
        ]
        
        for scenario in test_scenarios:
            message_data = {
                "contact_id": self.contact_id,
                "occasion": scenario["occasion"],
                "message_type": scenario["message_type"],
                "custom_message": scenario["message"],
                "image_url": scenario["image"]
            }
            
            response = requests.post(f"{self.api_url}/custom-messages", json=message_data, headers=headers)
            success = response.status_code == 200
            self.log_result(f"Create {scenario['occasion'].title()} {scenario['message_type'].title()}", 
                           success, f"{scenario['message'][:40]}..." if success else response.text)
        
        # Test 2: Verify all messages were created
        response = requests.get(f"{self.api_url}/custom-messages/{self.contact_id}", headers=headers)
        if response.status_code == 200:
            messages = response.json()
            self.log_result("Verify All Messages Created", True, f"Total: {len(messages)} custom messages")
        else:
            self.log_result("Verify All Messages Created", False, response.text)
        
        # Test 3: Test with different contact tones
        contact_update = {
            "name": "Sarah Johnson",
            "email": "sarah.johnson@example.com", 
            "whatsapp": "+1234567890",
            "birthday": "1985-03-15",
            "anniversary_date": "2018-07-20",
            "message_tone": "funny"
        }
        
        response = requests.put(f"{self.api_url}/contacts/{self.contact_id}", json=contact_update, headers=headers)
        if response.status_code == 200:
            # Test AI generation with funny tone
            response = requests.get(f"{self.api_url}/custom-messages/{self.contact_id}/birthday/sms", headers=headers)
            if response.status_code == 200:
                message = response.json()
                self.log_result("AI Message with Funny Tone", True,
                               f"Generated: {message.get('custom_message', '')[:50]}...")
            else:
                self.log_result("AI Message with Funny Tone", False, response.text)
        else:
            self.log_result("Update Contact Tone", False, response.text)

    def test_error_handling(self):
        """Test error handling scenarios"""
        print("\n⚠️  Testing Error Handling...")
        
        headers = {'Authorization': f'Bearer {self.token}', 'Content-Type': 'application/json'}
        
        # Test 1: Invalid contact ID
        invalid_data = {
            "contact_id": "invalid-contact-id",
            "occasion": "birthday",
            "message_type": "whatsapp",
            "custom_message": "Test message"
        }
        
        response = requests.post(f"{self.api_url}/custom-messages", json=invalid_data, headers=headers)
        success = response.status_code == 404
        self.log_result("Invalid Contact ID (404 Expected)", success, 
                       "Correctly returned 404" if success else f"Got {response.status_code}")
        
        # Test 2: Get messages for invalid contact
        response = requests.get(f"{self.api_url}/custom-messages/invalid-contact-id", headers=headers)
        success = response.status_code == 404
        self.log_result("Get Messages Invalid Contact (404 Expected)", success,
                       "Correctly returned 404" if success else f"Got {response.status_code}")
        
        # Test 3: Send test message with invalid contact
        invalid_test_data = {
            "contact_id": "invalid-contact-id",
            "occasion": "birthday"
        }
        
        response = requests.post(f"{self.api_url}/send-test-message", json=invalid_test_data, headers=headers)
        success = response.status_code == 404
        self.log_result("Test Message Invalid Contact (404 Expected)", success,
                       "Correctly returned 404" if success else f"Got {response.status_code}")

    def run_all_tests(self):
        """Run all focused custom message tests"""
        print("🚀 Starting Custom Message Focused Tests...")
        print(f"Testing against: {self.base_url}")
        print("=" * 60)
        
        # Setup
        if not self.setup_test_user_and_contact():
            print("❌ Failed to setup test environment")
            return 1
        
        # Run tests
        self.test_custom_message_crud_operations()
        self.test_message_sending()
        self.test_integration_scenarios()
        self.test_error_handling()
        
        # Results
        print("=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All custom message tests passed!")
            return 0
        else:
            print("❌ Some tests failed. Check the details above.")
            return 1

def main():
    tester = CustomMessageTester()
    return tester.run_all_tests()

if __name__ == "__main__":
    exit(main())