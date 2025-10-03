#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend_test import BirthdayReminderAPITester

def main():
    """Run focused image upload tests"""
    tester = BirthdayReminderAPITester()
    
    print("🚀 Starting Image Upload URL Tests...")
    print(f"Testing against: {tester.base_url}")
    print("=" * 60)
    
    # Register user and get token
    if not tester.test_user_registration():
        print("❌ User registration failed - stopping tests")
        return 1
    
    # Create a contact for testing
    if not tester.test_create_contact():
        print("❌ Contact creation failed - stopping tests")
        return 1
    
    # Run image upload tests
    print("\n📸 Testing Image Upload URL Functionality...")
    success1 = tester.test_image_upload_functionality()
    
    print("\n🎨 Testing Template Image Integration...")
    success2 = tester.test_template_image_integration()
    
    print("\n🔍 Testing Image Upload Validation...")
    success3 = tester.test_image_upload_validation()
    
    # Print summary
    print("\n" + "=" * 60)
    print("🏁 IMAGE UPLOAD TEST SUMMARY")
    print("=" * 60)
    print(f"Total tests run: {tester.tests_run}")
    print(f"Tests passed: {tester.tests_passed}")
    print(f"Tests failed: {tester.tests_run - tester.tests_passed}")
    print(f"Success rate: {(tester.tests_passed / tester.tests_run * 100):.1f}%")
    
    if success1 and success2 and success3:
        print("🎉 All image upload tests passed!")
        return 0
    else:
        print("⚠️ Some image upload tests failed. Check the logs above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())