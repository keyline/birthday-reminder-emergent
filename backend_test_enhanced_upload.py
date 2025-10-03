import requests
import sys
import json
import io
import pandas as pd
from datetime import datetime

class EnhancedUploadTester:
    def __init__(self, base_url="https://birthday-buddy-16.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.user_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                if files:
                    # Remove Content-Type for file uploads
                    headers.pop('Content-Type', None)
                    response = requests.post(url, files=files, headers=headers)
                else:
                    response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json()
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Error: {error_detail}")
                except:
                    print(f"   Response: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def setup_test_user(self):
        """Create and login test user"""
        timestamp = datetime.now().strftime('%H%M%S')
        test_email = f"test_enhanced_{timestamp}@example.com"
        
        # Register user
        success, response = self.run_test(
            "User Registration",
            "POST",
            "auth/register",
            200,
            data={
                "email": test_email,
                "password": "TestPass123!",
                "full_name": "Enhanced Test User"
            }
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_id = response['user']['id']
            print(f"✅ Test user created: {test_email}")
            return True
        return False

    def create_excel_file(self, data, filename="test_contacts.xlsx"):
        """Create Excel file from data"""
        df = pd.DataFrame(data)
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False)
        buffer.seek(0)
        return buffer

    def test_valid_upload(self):
        """Test valid Excel upload with all validation rules"""
        print("\n📋 Testing Valid Excel Upload...")
        
        # Create valid test data
        valid_data = [
            {
                'name': 'John Doe',
                'birthday': '15-05',
                'anniversary': '',
                'email': 'john.doe@example.com',
                'whatsapp': '+1234567890'
            },
            {
                'name': 'Jane Smith',
                'birthday': '',
                'anniversary': '20-09-2018',
                'email': 'jane.smith@example.com',
                'whatsapp': ''
            },
            {
                'name': 'Bob Johnson',
                'birthday': '03-12-1985',
                'anniversary': '14-07-2010',
                'email': '',
                'whatsapp': '+9876543210'
            },
            {
                'name': 'Alice Brown',
                'birthday': '25-08',
                'anniversary': '',
                'email': 'alice.brown@example.com',
                'whatsapp': '+1122334455'
            }
        ]
        
        excel_buffer = self.create_excel_file(valid_data)
        
        success, response = self.run_test(
            "Valid Excel Upload",
            "POST",
            "contacts/bulk-upload",
            200,
            files={'file': ('test_contacts.xlsx', excel_buffer, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
        )
        
        if success:
            print(f"   Total rows: {response.get('total_rows', 0)}")
            print(f"   Successful imports: {response.get('successful_imports', 0)}")
            print(f"   Failed imports: {response.get('failed_imports', 0)}")
            print(f"   Errors: {response.get('errors', [])}")
            
            # Validate response structure
            expected_keys = ['total_rows', 'successful_imports', 'failed_imports', 'errors', 'imported_contacts']
            for key in expected_keys:
                if key not in response:
                    print(f"❌ Missing key in response: {key}")
                    return False
            
            # Should import all 4 contacts successfully
            if response.get('successful_imports') == 4 and response.get('failed_imports') == 0:
                print("✅ All valid contacts imported successfully")
                return True
            else:
                print(f"❌ Expected 4 successful imports, got {response.get('successful_imports')}")
        
        return False

    def test_validation_rules(self):
        """Test all validation rules"""
        print("\n🔍 Testing Validation Rules...")
        
        # Test data with various validation issues
        invalid_data = [
            {
                'name': '',  # Missing name
                'birthday': '15-05',
                'anniversary': '',
                'email': 'valid@example.com',
                'whatsapp': '+1234567890'
            },
            {
                'name': 'Invalid Email User',
                'birthday': '20-06',
                'anniversary': '',
                'email': 'invalid-email',  # Invalid email format
                'whatsapp': ''
            },
            {
                'name': 'Invalid Phone User',
                'birthday': '',
                'anniversary': '25-12',
                'email': '',
                'whatsapp': '123'  # Invalid phone format
            },
            {
                'name': 'No Contact Info',
                'birthday': '10-10',
                'anniversary': '',
                'email': '',  # No email or whatsapp
                'whatsapp': ''
            },
            {
                'name': 'No Dates',
                'birthday': '',  # No birthday or anniversary
                'anniversary': '',
                'email': 'nodate@example.com',
                'whatsapp': ''
            },
            {
                'name': 'Invalid Date Format',
                'birthday': '32-13',  # Invalid date
                'anniversary': '',
                'email': 'invaliddate@example.com',
                'whatsapp': ''
            }
        ]
        
        excel_buffer = self.create_excel_file(invalid_data)
        
        success, response = self.run_test(
            "Validation Rules Test",
            "POST",
            "contacts/bulk-upload",
            200,
            files={'file': ('invalid_contacts.xlsx', excel_buffer, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
        )
        
        if success:
            print(f"   Total rows: {response.get('total_rows', 0)}")
            print(f"   Successful imports: {response.get('successful_imports', 0)}")
            print(f"   Failed imports: {response.get('failed_imports', 0)}")
            
            errors = response.get('errors', [])
            print(f"   Validation errors ({len(errors)}):")
            for error in errors:
                print(f"     • {error}")
            
            # Should have 0 successful imports and 6 failed imports
            if response.get('successful_imports') == 0 and response.get('failed_imports') == 6:
                print("✅ All validation rules working correctly")
                return True
            else:
                print(f"❌ Expected 0 successful, 6 failed. Got {response.get('successful_imports')} successful, {response.get('failed_imports')} failed")
        
        return False

    def test_duplicate_checking(self):
        """Test duplicate checking against existing contacts"""
        print("\n🔄 Testing Duplicate Checking...")
        
        # First, create a contact manually
        success, _ = self.run_test(
            "Create Initial Contact",
            "POST",
            "contacts",
            200,
            data={
                "name": "Existing User",
                "email": "existing@example.com",
                "whatsapp": "+9999999999",
                "birthday": "2024-01-01"
            }
        )
        
        if not success:
            print("❌ Failed to create initial contact for duplicate test")
            return False
        
        # Now try to upload duplicates
        duplicate_data = [
            {
                'name': 'Duplicate Email User',
                'birthday': '15-05',
                'anniversary': '',
                'email': 'existing@example.com',  # Duplicate email
                'whatsapp': '+1111111111'
            },
            {
                'name': 'Duplicate Phone User',
                'birthday': '20-06',
                'anniversary': '',
                'email': 'different@example.com',
                'whatsapp': '+9999999999'  # Duplicate phone
            },
            {
                'name': 'New Valid User',
                'birthday': '25-07',
                'anniversary': '',
                'email': 'new@example.com',
                'whatsapp': '+8888888888'
            }
        ]
        
        excel_buffer = self.create_excel_file(duplicate_data)
        
        success, response = self.run_test(
            "Duplicate Checking Test",
            "POST",
            "contacts/bulk-upload",
            200,
            files={'file': ('duplicate_test.xlsx', excel_buffer, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
        )
        
        if success:
            print(f"   Total rows: {response.get('total_rows', 0)}")
            print(f"   Successful imports: {response.get('successful_imports', 0)}")
            print(f"   Failed imports: {response.get('failed_imports', 0)}")
            
            errors = response.get('errors', [])
            print(f"   Duplicate errors ({len(errors)}):")
            for error in errors:
                print(f"     • {error}")
            
            # Should have 1 successful import and 2 failed (duplicates)
            if response.get('successful_imports') == 1 and response.get('failed_imports') == 2:
                print("✅ Duplicate checking working correctly")
                return True
            else:
                print(f"❌ Expected 1 successful, 2 failed. Got {response.get('successful_imports')} successful, {response.get('failed_imports')} failed")
        
        return False

    def test_date_formats(self):
        """Test different date formats"""
        print("\n📅 Testing Date Formats...")
        
        date_format_data = [
            {
                'name': 'DD-MM Format User',
                'birthday': '15-05',  # DD-MM format
                'anniversary': '',
                'email': 'ddmm@example.com',
                'whatsapp': ''
            },
            {
                'name': 'DD-MM-YYYY Format User',
                'birthday': '20-06-1990',  # DD-MM-YYYY format
                'anniversary': '25-12-2015',
                'email': 'ddmmyyyy@example.com',
                'whatsapp': ''
            },
            {
                'name': 'Mixed Format User',
                'birthday': '10-03',  # DD-MM
                'anniversary': '14-07-2020',  # DD-MM-YYYY
                'email': 'mixed@example.com',
                'whatsapp': ''
            }
        ]
        
        excel_buffer = self.create_excel_file(date_format_data)
        
        success, response = self.run_test(
            "Date Formats Test",
            "POST",
            "contacts/bulk-upload",
            200,
            files={'file': ('date_formats.xlsx', excel_buffer, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
        )
        
        if success:
            print(f"   Total rows: {response.get('total_rows', 0)}")
            print(f"   Successful imports: {response.get('successful_imports', 0)}")
            print(f"   Failed imports: {response.get('failed_imports', 0)}")
            
            # Should import all 3 contacts successfully
            if response.get('successful_imports') == 3 and response.get('failed_imports') == 0:
                print("✅ All date formats handled correctly")
                return True
            else:
                print(f"❌ Expected 3 successful imports, got {response.get('successful_imports')}")
                errors = response.get('errors', [])
                for error in errors:
                    print(f"     • {error}")
        
        return False

    def test_file_format_validation(self):
        """Test file format validation"""
        print("\n📄 Testing File Format Validation...")
        
        # Test with non-Excel file
        text_content = "This is not an Excel file"
        
        success, response = self.run_test(
            "Invalid File Format",
            "POST",
            "contacts/bulk-upload",
            400,
            files={'file': ('test.txt', io.BytesIO(text_content.encode()), 'text/plain')}
        )
        
        if success:
            print("✅ File format validation working correctly")
            return True
        
        return False

    def test_missing_columns(self):
        """Test missing required columns"""
        print("\n📋 Testing Missing Columns...")
        
        # Create Excel with missing columns
        incomplete_data = [
            {
                'name': 'John Doe',
                'birthday': '15-05'
                # Missing anniversary, email, whatsapp columns
            }
        ]
        
        excel_buffer = self.create_excel_file(incomplete_data)
        
        success, response = self.run_test(
            "Missing Columns Test",
            "POST",
            "contacts/bulk-upload",
            400,
            files={'file': ('incomplete.xlsx', excel_buffer, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
        )
        
        if success:
            print("✅ Missing columns validation working correctly")
            return True
        
        return False

def main():
    print("🚀 Starting Enhanced Excel Upload Feature Testing...")
    print("=" * 60)
    
    tester = EnhancedUploadTester()
    
    # Setup test user
    if not tester.setup_test_user():
        print("❌ Failed to setup test user, stopping tests")
        return 1
    
    # Run all tests
    test_results = []
    
    test_results.append(tester.test_file_format_validation())
    test_results.append(tester.test_missing_columns())
    test_results.append(tester.test_valid_upload())
    test_results.append(tester.test_validation_rules())
    test_results.append(tester.test_duplicate_checking())
    test_results.append(tester.test_date_formats())
    
    # Print final results
    print("\n" + "=" * 60)
    print(f"📊 Enhanced Upload Tests Summary:")
    print(f"   Tests passed: {tester.tests_passed}/{tester.tests_run}")
    print(f"   Success rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    passed_tests = sum(test_results)
    total_feature_tests = len(test_results)
    print(f"   Feature tests passed: {passed_tests}/{total_feature_tests}")
    
    if passed_tests == total_feature_tests:
        print("✅ All enhanced upload features working correctly!")
        return 0
    else:
        print("❌ Some enhanced upload features need attention")
        return 1

if __name__ == "__main__":
    sys.exit(main())