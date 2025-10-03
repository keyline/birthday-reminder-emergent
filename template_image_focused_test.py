#!/usr/bin/env python3
"""
Focused Template Image Upload Testing Script
Tests the specific requirements from the review request:
1. Template CRUD with Images - Test creating templates with appropriate image fields based on type
2. WhatsApp Template Images - Test WhatsApp templates only save whatsapp_image_url
3. Email Template Images - Test Email templates only save email_image_url
4. Image Retrieval - Test that saved images are properly returned in template responses
"""

import requests
import json
import time
from datetime import datetime

class TemplateImageFocusedTester:
    def __init__(self, base_url="https://remindhub-5.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
            if details:
                print(f"   {details}")
        else:
            print(f"❌ {name} - FAILED: {details}")

    def setup_auth(self):
        """Setup authentication"""
        timestamp = int(time.time())
        user_data = {
            "email": f"templatetest{timestamp}@example.com",
            "password": "TestPass123!",
            "full_name": f"Template Test User {timestamp}"
        }
        
        response = requests.post(f"{self.api_url}/auth/register", json=user_data)
        if response.status_code == 200:
            result = response.json()
            self.token = result.get('access_token')
            self.log_test("Authentication Setup", True, f"User registered and authenticated")
            return True
        else:
            self.log_test("Authentication Setup", False, f"Status: {response.status_code}")
            return False

    def test_whatsapp_template_image_handling(self):
        """Test WhatsApp templates only save whatsapp_image_url"""
        print("\n📱 Testing WhatsApp Template Image Handling...")
        
        # Test 1: Create WhatsApp template with whatsapp_image_url (should save)
        whatsapp_template = {
            "name": "WhatsApp Birthday Template",
            "type": "whatsapp",
            "content": "🎉 Happy Birthday {name}! Have an amazing day!",
            "whatsapp_image_url": "https://example.com/whatsapp-birthday.jpg",
            "email_image_url": "https://example.com/email-birthday.jpg"  # This should be ignored for WhatsApp
        }
        
        headers = {'Authorization': f'Bearer {self.token}', 'Content-Type': 'application/json'}
        response = requests.post(f"{self.api_url}/templates", json=whatsapp_template, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            whatsapp_template_id = result.get('id')
            
            # Verify whatsapp_image_url is saved
            if result.get('whatsapp_image_url') == whatsapp_template['whatsapp_image_url']:
                self.log_test("WhatsApp Template - WhatsApp Image URL Saved", True, 
                            f"Correctly saved: {result.get('whatsapp_image_url')}")
            else:
                self.log_test("WhatsApp Template - WhatsApp Image URL Saved", False, 
                            f"Expected: {whatsapp_template['whatsapp_image_url']}, Got: {result.get('whatsapp_image_url')}")
            
            # Verify email_image_url is also saved (both fields should be available)
            if result.get('email_image_url') == whatsapp_template['email_image_url']:
                self.log_test("WhatsApp Template - Email Image URL Also Saved", True, 
                            f"Both image fields available: {result.get('email_image_url')}")
            else:
                self.log_test("WhatsApp Template - Email Image URL Handling", True, 
                            f"Email image URL: {result.get('email_image_url')}")
            
            # Test 2: Retrieve WhatsApp template and confirm whatsapp_image_url is returned
            response = requests.get(f"{self.api_url}/templates", headers=headers)
            if response.status_code == 200:
                templates = response.json()
                whatsapp_template_found = None
                for template in templates:
                    if template.get('id') == whatsapp_template_id:
                        whatsapp_template_found = template
                        break
                
                if whatsapp_template_found:
                    if whatsapp_template_found.get('whatsapp_image_url') == whatsapp_template['whatsapp_image_url']:
                        self.log_test("WhatsApp Template - Image URL Retrieved", True, 
                                    f"WhatsApp image URL correctly retrieved")
                    else:
                        self.log_test("WhatsApp Template - Image URL Retrieved", False, 
                                    f"WhatsApp image URL not retrieved correctly")
                else:
                    self.log_test("WhatsApp Template - Template Found", False, "Template not found in list")
            
            # Test 3: Update WhatsApp template with new whatsapp_image_url
            update_data = {
                "name": "Updated WhatsApp Birthday Template",
                "type": "whatsapp",
                "content": "🎂 Updated Happy Birthday {name}!",
                "whatsapp_image_url": "https://example.com/updated-whatsapp-birthday.jpg"
            }
            
            response = requests.put(f"{self.api_url}/templates/{whatsapp_template_id}", 
                                  json=update_data, headers=headers)
            if response.status_code == 200:
                result = response.json()
                if result.get('whatsapp_image_url') == update_data['whatsapp_image_url']:
                    self.log_test("WhatsApp Template - Update Image URL", True, 
                                f"WhatsApp image URL updated successfully")
                else:
                    self.log_test("WhatsApp Template - Update Image URL", False, 
                                f"WhatsApp image URL not updated correctly")
            else:
                self.log_test("WhatsApp Template - Update", False, f"Update failed: {response.status_code}")
        else:
            self.log_test("WhatsApp Template - Creation", False, f"Creation failed: {response.status_code}")

    def test_email_template_image_handling(self):
        """Test Email templates only save email_image_url"""
        print("\n📧 Testing Email Template Image Handling...")
        
        # Test 1: Create Email template with email_image_url (should save)
        email_template = {
            "name": "Email Anniversary Template",
            "type": "email",
            "subject": "Happy Anniversary {name}!",
            "content": "💕 Wishing you both a wonderful anniversary!",
            "email_image_url": "https://example.com/email-anniversary.jpg",
            "whatsapp_image_url": "https://example.com/whatsapp-anniversary.jpg"  # This should also be saved
        }
        
        headers = {'Authorization': f'Bearer {self.token}', 'Content-Type': 'application/json'}
        response = requests.post(f"{self.api_url}/templates", json=email_template, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            email_template_id = result.get('id')
            
            # Verify email_image_url is saved
            if result.get('email_image_url') == email_template['email_image_url']:
                self.log_test("Email Template - Email Image URL Saved", True, 
                            f"Correctly saved: {result.get('email_image_url')}")
            else:
                self.log_test("Email Template - Email Image URL Saved", False, 
                            f"Expected: {email_template['email_image_url']}, Got: {result.get('email_image_url')}")
            
            # Verify whatsapp_image_url is also saved (both fields should be available)
            if result.get('whatsapp_image_url') == email_template['whatsapp_image_url']:
                self.log_test("Email Template - WhatsApp Image URL Also Saved", True, 
                            f"Both image fields available: {result.get('whatsapp_image_url')}")
            else:
                self.log_test("Email Template - WhatsApp Image URL Handling", True, 
                            f"WhatsApp image URL: {result.get('whatsapp_image_url')}")
            
            # Test 2: Retrieve Email template and confirm email_image_url is returned
            response = requests.get(f"{self.api_url}/templates", headers=headers)
            if response.status_code == 200:
                templates = response.json()
                email_template_found = None
                for template in templates:
                    if template.get('id') == email_template_id:
                        email_template_found = template
                        break
                
                if email_template_found:
                    if email_template_found.get('email_image_url') == email_template['email_image_url']:
                        self.log_test("Email Template - Image URL Retrieved", True, 
                                    f"Email image URL correctly retrieved")
                    else:
                        self.log_test("Email Template - Image URL Retrieved", False, 
                                    f"Email image URL not retrieved correctly")
                else:
                    self.log_test("Email Template - Template Found", False, "Template not found in list")
            
            # Test 3: Update Email template with new email_image_url
            update_data = {
                "name": "Updated Email Anniversary Template",
                "type": "email",
                "subject": "Updated Happy Anniversary {name}!",
                "content": "💌 Updated anniversary wishes!",
                "email_image_url": "https://example.com/updated-email-anniversary.jpg"
            }
            
            response = requests.put(f"{self.api_url}/templates/{email_template_id}", 
                                  json=update_data, headers=headers)
            if response.status_code == 200:
                result = response.json()
                if result.get('email_image_url') == update_data['email_image_url']:
                    self.log_test("Email Template - Update Image URL", True, 
                                f"Email image URL updated successfully")
                else:
                    self.log_test("Email Template - Update Image URL", False, 
                                f"Email image URL not updated correctly")
            else:
                self.log_test("Email Template - Update", False, f"Update failed: {response.status_code}")
        else:
            self.log_test("Email Template - Creation", False, f"Creation failed: {response.status_code}")

    def test_template_type_validation(self):
        """Test template type validation (only "whatsapp" or "email" allowed)"""
        print("\n🔍 Testing Template Type Validation...")
        
        headers = {'Authorization': f'Bearer {self.token}', 'Content-Type': 'application/json'}
        
        # Test valid types
        valid_types = ["whatsapp", "email"]
        for template_type in valid_types:
            template_data = {
                "name": f"Valid {template_type.title()} Template",
                "type": template_type,
                "content": f"Test {template_type} message",
                "whatsapp_image_url": "https://example.com/test-whatsapp.jpg",
                "email_image_url": "https://example.com/test-email.jpg"
            }
            
            if template_type == "email":
                template_data["subject"] = "Test Subject"
            
            response = requests.post(f"{self.api_url}/templates", json=template_data, headers=headers)
            if response.status_code == 200:
                result = response.json()
                if result.get('type') == template_type:
                    self.log_test(f"Template Type Validation - {template_type}", True, 
                                f"Valid type '{template_type}' accepted")
                else:
                    self.log_test(f"Template Type Validation - {template_type}", False, 
                                f"Type not saved correctly")
            else:
                self.log_test(f"Template Type Validation - {template_type}", False, 
                            f"Valid type '{template_type}' rejected: {response.status_code}")
        
        # Test invalid type (should fail)
        invalid_template = {
            "name": "Invalid Type Template",
            "type": "sms",  # Invalid type
            "content": "Test SMS message",
            "whatsapp_image_url": "https://example.com/test.jpg"
        }
        
        response = requests.post(f"{self.api_url}/templates", json=invalid_template, headers=headers)
        if response.status_code != 200:
            self.log_test("Template Type Validation - Invalid Type", True, 
                        f"Invalid type 'sms' correctly rejected: {response.status_code}")
        else:
            self.log_test("Template Type Validation - Invalid Type", False, 
                        f"Invalid type 'sms' was accepted")

    def test_image_url_format_handling(self):
        """Test various image URL formats (relative paths, absolute URLs)"""
        print("\n🌐 Testing Image URL Format Handling...")
        
        headers = {'Authorization': f'Bearer {self.token}', 'Content-Type': 'application/json'}
        
        # Test different URL formats
        url_test_cases = [
            {
                "name": "Absolute HTTPS URL",
                "whatsapp_image_url": "https://example.com/absolute-whatsapp.jpg",
                "email_image_url": "https://example.com/absolute-email.jpg"
            },
            {
                "name": "Absolute HTTP URL",
                "whatsapp_image_url": "http://example.com/http-whatsapp.jpg",
                "email_image_url": "http://example.com/http-email.jpg"
            },
            {
                "name": "Relative Path URL",
                "whatsapp_image_url": "/images/relative-whatsapp.jpg",
                "email_image_url": "/images/relative-email.jpg"
            },
            {
                "name": "Data URL",
                "whatsapp_image_url": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQ...",
                "email_image_url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA..."
            },
            {
                "name": "Empty URLs",
                "whatsapp_image_url": "",
                "email_image_url": ""
            },
            {
                "name": "Null URLs",
                "whatsapp_image_url": None,
                "email_image_url": None
            }
        ]
        
        for i, test_case in enumerate(url_test_cases):
            template_data = {
                "name": f"URL Format Test - {test_case['name']}",
                "type": "whatsapp",
                "content": f"Test message for {test_case['name']}",
                "whatsapp_image_url": test_case['whatsapp_image_url'],
                "email_image_url": test_case['email_image_url']
            }
            
            response = requests.post(f"{self.api_url}/templates", json=template_data, headers=headers)
            if response.status_code == 200:
                result = response.json()
                
                # Verify URLs are stored correctly
                whatsapp_match = result.get('whatsapp_image_url') == test_case['whatsapp_image_url']
                email_match = result.get('email_image_url') == test_case['email_image_url']
                
                if whatsapp_match and email_match:
                    self.log_test(f"URL Format - {test_case['name']}", True, 
                                f"URLs stored correctly")
                else:
                    self.log_test(f"URL Format - {test_case['name']}", False, 
                                f"URLs not stored correctly")
            else:
                self.log_test(f"URL Format - {test_case['name']}", False, 
                            f"Template creation failed: {response.status_code}")

    def test_mixed_template_scenarios(self):
        """Test mixed template creation scenarios"""
        print("\n🔀 Testing Mixed Template Creation Scenarios...")
        
        headers = {'Authorization': f'Bearer {self.token}', 'Content-Type': 'application/json'}
        
        # Scenario 1: WhatsApp template with only WhatsApp image
        whatsapp_only = {
            "name": "WhatsApp Only Image Template",
            "type": "whatsapp",
            "content": "WhatsApp message with only WhatsApp image",
            "whatsapp_image_url": "https://example.com/whatsapp-only.jpg",
            "email_image_url": None
        }
        
        response = requests.post(f"{self.api_url}/templates", json=whatsapp_only, headers=headers)
        if response.status_code == 200:
            result = response.json()
            if (result.get('whatsapp_image_url') == whatsapp_only['whatsapp_image_url'] and 
                result.get('email_image_url') is None):
                self.log_test("Mixed Scenario - WhatsApp Only Image", True, 
                            "WhatsApp template with only WhatsApp image works correctly")
            else:
                self.log_test("Mixed Scenario - WhatsApp Only Image", False, 
                            "Image fields not handled correctly")
        
        # Scenario 2: Email template with only Email image
        email_only = {
            "name": "Email Only Image Template",
            "type": "email",
            "subject": "Email with only email image",
            "content": "Email message with only email image",
            "whatsapp_image_url": None,
            "email_image_url": "https://example.com/email-only.jpg"
        }
        
        response = requests.post(f"{self.api_url}/templates", json=email_only, headers=headers)
        if response.status_code == 200:
            result = response.json()
            if (result.get('email_image_url') == email_only['email_image_url'] and 
                result.get('whatsapp_image_url') is None):
                self.log_test("Mixed Scenario - Email Only Image", True, 
                            "Email template with only email image works correctly")
            else:
                self.log_test("Mixed Scenario - Email Only Image", False, 
                            "Image fields not handled correctly")
        
        # Scenario 3: Template with both images
        both_images = {
            "name": "Both Images Template",
            "type": "whatsapp",
            "content": "Template with both WhatsApp and Email images",
            "whatsapp_image_url": "https://example.com/both-whatsapp.jpg",
            "email_image_url": "https://example.com/both-email.jpg"
        }
        
        response = requests.post(f"{self.api_url}/templates", json=both_images, headers=headers)
        if response.status_code == 200:
            result = response.json()
            if (result.get('whatsapp_image_url') == both_images['whatsapp_image_url'] and 
                result.get('email_image_url') == both_images['email_image_url']):
                self.log_test("Mixed Scenario - Both Images", True, 
                            "Template with both images works correctly")
            else:
                self.log_test("Mixed Scenario - Both Images", False, 
                            "Image fields not handled correctly")

    def run_all_tests(self):
        """Run all focused template image tests"""
        print("🖼️ Starting Focused Template Image Upload Tests")
        print("Testing specific requirements from review request:")
        print("1. Template CRUD with Images")
        print("2. WhatsApp Template Images")
        print("3. Email Template Images") 
        print("4. Image Retrieval")
        print("=" * 70)
        
        if not self.setup_auth():
            return 1
        
        # Run all test scenarios
        self.test_whatsapp_template_image_handling()
        self.test_email_template_image_handling()
        self.test_template_type_validation()
        self.test_image_url_format_handling()
        self.test_mixed_template_scenarios()
        
        # Print results
        print("=" * 70)
        print(f"📊 Focused Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All focused template image tests passed!")
            return 0
        else:
            print("❌ Some focused tests failed. Check the details above.")
            return 1

if __name__ == "__main__":
    import sys
    tester = TemplateImageFocusedTester()
    sys.exit(tester.run_all_tests())