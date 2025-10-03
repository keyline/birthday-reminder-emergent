import requests
import sys
import json
from datetime import datetime, date
import time

class BirthdayReminderAPITester:
    def __init__(self, base_url="https://birthday-buddy-16.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.admin_token = None
        self.admin_user_id = None

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        self.test_results.append({
            "test_name": name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=10)

            success = response.status_code == expected_status
            details = f"Status: {response.status_code}"
            
            if not success:
                details += f", Expected: {expected_status}"
                try:
                    error_data = response.json()
                    details += f", Response: {error_data}"
                except:
                    details += f", Response: {response.text[:200]}"

            self.log_test(name, success, details)
            
            if success:
                try:
                    return response.json()
                except:
                    return {"status": "success"}
            return None

        except Exception as e:
            self.log_test(name, False, f"Exception: {str(e)}")
            return None

    def test_health_check(self):
        """Test health endpoint"""
        return self.run_test("Health Check", "GET", "health", 200)

    def test_user_registration(self):
        """Test user registration"""
        timestamp = int(time.time())
        user_data = {
            "email": f"testuser{timestamp}@example.com",
            "password": "TestPass123!",
            "full_name": f"Test User {timestamp}"
        }
        
        result = self.run_test("User Registration", "POST", "auth/register", 200, user_data)
        if result:
            self.token = result.get('access_token')
            self.user_id = result.get('user', {}).get('id')
            return True
        return False

    def test_user_login(self):
        """Test user login with existing credentials"""
        # First register a user
        timestamp = int(time.time())
        email = f"logintest{timestamp}@example.com"
        password = "TestPass123!"
        
        register_data = {
            "email": email,
            "password": password,
            "full_name": f"Login Test User {timestamp}"
        }
        
        # Register user
        register_result = self.run_test("Register for Login Test", "POST", "auth/register", 200, register_data)
        if not register_result:
            return False
        
        # Now test login
        login_data = {
            "email": email,
            "password": password
        }
        
        result = self.run_test("User Login", "POST", "auth/login", 200, login_data)
        if result:
            # Store login token for further tests
            self.token = result.get('access_token')
            self.user_id = result.get('user', {}).get('id')
            return True
        return False

    def test_get_current_user(self):
        """Test getting current user info"""
        if not self.token:
            self.log_test("Get Current User", False, "No auth token available")
            return False
        
        result = self.run_test("Get Current User", "GET", "auth/me", 200)
        return result is not None

    def test_create_contact(self):
        """Test creating a contact"""
        if not self.token:
            self.log_test("Create Contact", False, "No auth token available")
            return False
        
        contact_data = {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "whatsapp": "+1234567890",
            "birthday": "1990-05-15",
            "anniversary_date": "2020-06-20"
        }
        
        result = self.run_test("Create Contact", "POST", "contacts", 200, contact_data)
        if result:
            self.contact_id = result.get('id')
            return True
        return False

    def test_get_contacts(self):
        """Test getting all contacts"""
        if not self.token:
            self.log_test("Get Contacts", False, "No auth token available")
            return False
        
        result = self.run_test("Get Contacts", "GET", "contacts", 200)
        return result is not None

    def test_get_single_contact(self):
        """Test getting a single contact"""
        if not self.token or not hasattr(self, 'contact_id'):
            self.log_test("Get Single Contact", False, "No auth token or contact ID available")
            return False
        
        result = self.run_test("Get Single Contact", "GET", f"contacts/{self.contact_id}", 200)
        return result is not None

    def test_update_contact(self):
        """Test updating a contact"""
        if not self.token or not hasattr(self, 'contact_id'):
            self.log_test("Update Contact", False, "No auth token or contact ID available")
            return False
        
        update_data = {
            "name": "John Doe Updated",
            "email": "john.updated@example.com",
            "whatsapp": "+1234567891",
            "birthday": "1990-05-16",
            "anniversary_date": "2020-06-21"
        }
        
        result = self.run_test("Update Contact", "PUT", f"contacts/{self.contact_id}", 200, update_data)
        return result is not None

    def test_create_template(self):
        """Test creating a template"""
        if not self.token:
            self.log_test("Create Template", False, "No auth token available")
            return False
        
        template_data = {
            "name": "Birthday Template",
            "type": "email",
            "subject": "Happy Birthday {name}!",
            "content": "Dear {name},\n\nWishing you a very happy birthday!\n\nBest regards",
            "is_default": False
        }
        
        result = self.run_test("Create Template", "POST", "templates", 200, template_data)
        if result:
            self.template_id = result.get('id')
            return True
        return False

    def test_get_templates(self):
        """Test getting all templates"""
        if not self.token:
            self.log_test("Get Templates", False, "No auth token available")
            return False
        
        result = self.run_test("Get Templates", "GET", "templates", 200)
        return result is not None

    def test_update_template(self):
        """Test updating a template"""
        if not self.token or not hasattr(self, 'template_id'):
            self.log_test("Update Template", False, "No auth token or template ID available")
            return False
        
        update_data = {
            "name": "Updated Birthday Template",
            "type": "email",
            "subject": "Happy Birthday {name}! Updated",
            "content": "Dear {name},\n\nWishing you a very happy birthday! Updated message.\n\nBest regards",
            "is_default": True
        }
        
        result = self.run_test("Update Template", "PUT", f"templates/{self.template_id}", 200, update_data)
        return result is not None

    def test_generate_message(self):
        """Test AI message generation"""
        if not self.token:
            self.log_test("Generate AI Message", False, "No auth token available")
            return False
        
        message_data = {
            "contact_name": "John Doe",
            "occasion": "birthday",
            "relationship": "friend",
            "tone": "warm"
        }
        
        result = self.run_test("Generate AI Message", "POST", "generate-message", 200, message_data)
        if result and result.get('message'):
            print(f"   Generated message: {result['message'][:100]}...")
            return True
        return False

    def test_dashboard_stats(self):
        """Test dashboard statistics"""
        if not self.token:
            self.log_test("Dashboard Stats", False, "No auth token available")
            return False
        
        result = self.run_test("Dashboard Stats", "GET", "dashboard/stats", 200)
        if result:
            print(f"   Stats: {result.get('total_contacts', 0)} contacts, {result.get('total_templates', 0)} templates")
            return True
        return False

    def test_admin_functionality(self):
        """Test admin functionality"""
        # First create an admin user
        timestamp = int(time.time())
        admin_data = {
            "email": f"admin{timestamp}@example.com",
            "password": "AdminPass123!",
            "full_name": f"Admin User {timestamp}"
        }
        
        # Register admin user
        result = self.run_test("Register Admin User", "POST", "auth/register", 200, admin_data)
        if not result:
            return False
        
        admin_token = result.get('access_token')
        admin_user_id = result.get('user', {}).get('id')
        
        # Manually set admin status (in real app, this would be done through database)
        # For testing, we'll try to access admin endpoints and expect 403
        
        # Store current token
        original_token = self.token
        self.token = admin_token
        
        # Try to access admin endpoints (should fail since user is not admin)
        result = self.run_test("Admin Get Users (Should Fail)", "GET", "admin/users", 403)
        
        # Restore original token
        self.token = original_token
        
        return result is None  # Should fail, so None is expected

    def test_custom_message_crud(self):
        """Test custom message CRUD operations"""
        if not self.token or not hasattr(self, 'contact_id'):
            self.log_test("Custom Message CRUD", False, "No auth token or contact ID available")
            return False
        
        success = True
        
        # Test 1: Create custom WhatsApp birthday message
        whatsapp_message_data = {
            "contact_id": self.contact_id,
            "occasion": "birthday",
            "message_type": "whatsapp",
            "custom_message": "🎉 Happy Birthday! Hope you have an amazing day filled with joy and celebration!",
            "image_url": "/default-birthday.jpg"
        }
        
        result = self.run_test("Create Custom WhatsApp Birthday Message", "POST", "custom-messages", 200, whatsapp_message_data)
        if not result:
            success = False
        
        # Test 2: Create custom Email anniversary message
        email_message_data = {
            "contact_id": self.contact_id,
            "occasion": "anniversary",
            "message_type": "email",
            "custom_message": "💕 Happy Anniversary! Wishing you both continued happiness and love.",
            "image_url": "/default-anniversary.jpg"
        }
        
        result = self.run_test("Create Custom Email Anniversary Message", "POST", "custom-messages", 200, email_message_data)
        if not result:
            success = False
        
        # Test 3: Get all custom messages for contact
        result = self.run_test("Get All Custom Messages for Contact", "GET", f"custom-messages/{self.contact_id}", 200)
        if not result:
            success = False
        elif isinstance(result, list) and len(result) >= 2:
            print(f"   Found {len(result)} custom messages for contact")
        
        # Test 4: Get specific custom message (WhatsApp birthday)
        result = self.run_test("Get Specific Custom Message", "GET", f"custom-messages/{self.contact_id}/birthday/whatsapp", 200)
        if not result:
            success = False
        elif result.get('custom_message'):
            print(f"   Retrieved message: {result['custom_message'][:50]}...")
        
        # Test 5: Get non-existent custom message (should return AI-generated default)
        result = self.run_test("Get Default AI Message", "GET", f"custom-messages/{self.contact_id}/birthday/email", 200)
        if not result:
            success = False
        elif result.get('is_default'):
            print(f"   AI-generated default message: {result.get('custom_message', '')[:50]}...")
        
        # Test 6: Update existing custom message
        updated_message_data = {
            "contact_id": self.contact_id,
            "occasion": "birthday",
            "message_type": "whatsapp",
            "custom_message": "🎂 Updated Birthday Message! Have a fantastic celebration!",
            "image_url": "/updated-birthday.jpg"
        }
        
        result = self.run_test("Update Custom Message", "POST", "custom-messages", 200, updated_message_data)
        if not result:
            success = False
        
        # Test 7: Delete custom message
        result = self.run_test("Delete Custom Message", "DELETE", f"custom-messages/{self.contact_id}/anniversary/email", 200)
        if not result:
            success = False
        
        # Test 8: Try to delete non-existent message (should return 404)
        result = self.run_test("Delete Non-existent Message", "DELETE", f"custom-messages/{self.contact_id}/nonexistent/whatsapp", 404)
        if result is not None:  # Should fail with 404
            success = False
        
        return success
    
    def test_send_test_message(self):
        """Test sending test messages"""
        if not self.token or not hasattr(self, 'contact_id'):
            self.log_test("Send Test Message", False, "No auth token or contact ID available")
            return False
        
        # Test sending test message for birthday
        test_message_data = {
            "contact_id": self.contact_id,
            "occasion": "birthday"
        }
        
        result = self.run_test("Send Test Birthday Message", "POST", "send-test-message", 200, test_message_data)
        if result:
            print(f"   Test message results: WhatsApp: {result.get('results', {}).get('whatsapp', {}).get('status', 'N/A')}, Email: {result.get('results', {}).get('email', {}).get('status', 'N/A')}")
            return True
        return False
    
    def test_custom_message_error_handling(self):
        """Test custom message error handling"""
        if not self.token:
            self.log_test("Custom Message Error Handling", False, "No auth token available")
            return False
        
        success = True
        
        # Test 1: Create custom message with invalid contact ID
        invalid_message_data = {
            "contact_id": "invalid-contact-id",
            "occasion": "birthday",
            "message_type": "whatsapp",
            "custom_message": "Test message"
        }
        
        result = self.run_test("Custom Message Invalid Contact", "POST", "custom-messages", 404, invalid_message_data)
        if result is not None:  # Should fail with 404
            success = False
        
        # Test 2: Get custom messages for invalid contact
        result = self.run_test("Get Messages Invalid Contact", "GET", "custom-messages/invalid-contact-id", 404)
        if result is not None:  # Should fail with 404
            success = False
        
        # Test 3: Send test message with invalid contact
        invalid_test_data = {
            "contact_id": "invalid-contact-id",
            "occasion": "birthday"
        }
        
        result = self.run_test("Test Message Invalid Contact", "POST", "send-test-message", 404, invalid_test_data)
        if result is not None:  # Should fail with 404
            success = False
        
        return success
    
    def test_custom_message_integration(self):
        """Test custom message integration with existing systems"""
        if not self.token or not hasattr(self, 'contact_id'):
            self.log_test("Custom Message Integration", False, "No auth token or contact ID available")
            return False
        
        success = True
        
        # Test 1: Create custom messages for different occasions and types
        test_scenarios = [
            {"occasion": "birthday", "message_type": "whatsapp", "message": "🎉 WhatsApp Birthday Wishes!"},
            {"occasion": "birthday", "message_type": "email", "message": "📧 Email Birthday Greetings!"},
            {"occasion": "anniversary", "message_type": "whatsapp", "message": "💕 WhatsApp Anniversary Love!"},
            {"occasion": "anniversary", "message_type": "email", "message": "💌 Email Anniversary Wishes!"}
        ]
        
        for scenario in test_scenarios:
            message_data = {
                "contact_id": self.contact_id,
                "occasion": scenario["occasion"],
                "message_type": scenario["message_type"],
                "custom_message": scenario["message"],
                "image_url": f"/test-{scenario['occasion']}-{scenario['message_type']}.jpg"
            }
            
            result = self.run_test(f"Create {scenario['occasion'].title()} {scenario['message_type'].title()} Message", 
                                 "POST", "custom-messages", 200, message_data)
            if not result:
                success = False
        
        # Test 2: Verify all messages were created
        result = self.run_test("Verify All Custom Messages Created", "GET", f"custom-messages/{self.contact_id}", 200)
        if result and isinstance(result, list):
            print(f"   Total custom messages created: {len(result)}")
            if len(result) < 4:  # Should have at least 4 messages from scenarios above
                success = False
        else:
            success = False
        
        # Test 3: Test message generation integration with contact tone
        # First update contact with different tone
        contact_update = {
            "name": "John Doe Updated",
            "email": "john.updated@example.com",
            "whatsapp": "+1234567891",
            "birthday": "1990-05-16",
            "anniversary_date": "2020-06-21",
            "message_tone": "funny"
        }
        
        update_result = self.run_test("Update Contact Tone for Integration Test", "PUT", f"contacts/{self.contact_id}", 200, contact_update)
        if update_result:
            # Now test getting default message with funny tone
            result = self.run_test("Get AI Message with Funny Tone", "GET", f"custom-messages/{self.contact_id}/birthday/sms", 200)
            if result and result.get('is_default'):
                print(f"   AI message with funny tone: {result.get('custom_message', '')[:50]}...")
            elif not result:
                success = False
        
        return success

    def test_delete_operations(self):
        """Test delete operations"""
        if not self.token:
            self.log_test("Delete Operations", False, "No auth token available")
            return False
        
        success = True
        
        # Delete custom messages first (cleanup)
        if hasattr(self, 'contact_id'):
            # Try to delete some custom messages (may not exist, that's ok)
            self.run_test("Cleanup Custom Messages 1", "DELETE", f"custom-messages/{self.contact_id}/birthday/whatsapp", 200)
            self.run_test("Cleanup Custom Messages 2", "DELETE", f"custom-messages/{self.contact_id}/anniversary/email", 200)
        
        # Delete template
        if hasattr(self, 'template_id'):
            result = self.run_test("Delete Template", "DELETE", f"templates/{self.template_id}", 200)
            if not result:
                success = False
        
        # Delete contact
        if hasattr(self, 'contact_id'):
            result = self.run_test("Delete Contact", "DELETE", f"contacts/{self.contact_id}", 200)
            if not result:
                success = False
        
        return success

    def test_error_handling(self):
        """Test error handling"""
        success = True
        
        # Test invalid login
        invalid_login = {
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        }
        result = self.run_test("Invalid Login", "POST", "auth/login", 401, invalid_login)
        if result is not None:  # Should fail
            success = False
        
        # Test accessing protected endpoint without token
        original_token = self.token
        self.token = None
        result = self.run_test("Unauthorized Access", "GET", "contacts", 401)
        if result is not None:  # Should fail
            success = False
        self.token = original_token
        
        # Test invalid contact creation
        if self.token:
            invalid_contact = {
                "name": "",  # Empty name should fail
                "email": "invalid-email"  # Invalid email format
            }
            result = self.run_test("Invalid Contact Creation", "POST", "contacts", 422, invalid_contact)
            if result is not None:  # Should fail
                success = False
        
        return success

    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 Starting Birthday Reminder API Tests...")
        print(f"Testing against: {self.base_url}")
        print("=" * 60)
        
        # Basic tests
        self.test_health_check()
        
        # Authentication tests
        if self.test_user_registration():
            self.test_get_current_user()
        
        # Test login separately
        self.test_user_login()
        
        # Contact management tests
        if self.test_create_contact():
            self.test_get_contacts()
            self.test_get_single_contact()
            self.test_update_contact()
        
        # Template management tests
        if self.test_create_template():
            self.test_get_templates()
            self.test_update_template()
        
        # AI and dashboard tests
        self.test_generate_message()
        self.test_dashboard_stats()
        
        # Custom Message tests (NEW)
        print("\n🔧 Testing Custom Message Functionality...")
        self.test_custom_message_crud()
        self.test_send_test_message()
        self.test_custom_message_error_handling()
        self.test_custom_message_integration()
        
        # Admin tests
        self.test_admin_functionality()
        
        # Error handling tests
        self.test_error_handling()
        
        # Cleanup tests
        self.test_delete_operations()
        
        # Print results
        print("=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return 0
        else:
            print("❌ Some tests failed. Check the details above.")
            return 1

def main():
    tester = BirthdayReminderAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())