import requests
import sys
import json
from datetime import datetime, date
import time

class BirthdayReminderAPITester:
    def __init__(self, base_url="https://birthday-alert-4.preview.emergentagent.com"):
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

    def test_delete_operations(self):
        """Test delete operations"""
        if not self.token:
            self.log_test("Delete Operations", False, "No auth token available")
            return False
        
        success = True
        
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