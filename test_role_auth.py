"""
Test script for staff creation API
Run this after starting your Django server
"""

import os
import requests
import json

# Configuration
BASE_URL = os.getenv("TEST_BASE_URL", "http://localhost:8000")
CREATE_STAFF_URL = f"{BASE_URL}/api/create-staff/"
LOGIN_URL = f"{BASE_URL}/api/login/"

# Test data for creating a staff member
staff_data = {
    "student_id": "STAFF001",
    "email": "teststaff@example.com",
    "first_name": "Test",
    "middle_name": "S",
    "last_name": "Staff",
    "gender": "Male",
    "age": 30,
    "course": "Computer Science",
    "year_graduate": 2015,
    "password": "testpassword123",
    "role": "staff"
}

# Test data for creating an admin
admin_data = {
    "student_id": "ADMIN001",
    "email": "testadmin@example.com",
    "first_name": "Test",
    "middle_name": "A",
    "last_name": "Admin",
    "gender": "Female",
    "age": 35,
    "course": "Information Technology",
    "year_graduate": 2010,
    "password": "adminpassword123",
    "role": "admin"
}

def test_create_staff():
    """Test creating a staff account"""
    print("\n=== Testing Staff Creation ===")
    try:
        response = requests.post(CREATE_STAFF_URL, json=staff_data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 201:
            print("✅ Staff account created successfully!")
            return True
        else:
            print("❌ Failed to create staff account")
            return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_create_admin():
    """Test creating an admin account"""
    print("\n=== Testing Admin Creation ===")
    try:
        response = requests.post(CREATE_STAFF_URL, json=admin_data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 201:
            print("✅ Admin account created successfully!")
            return True
        else:
            print("❌ Failed to create admin account")
            return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_login(email, password, expected_role):
    """Test login with created account"""
    print(f"\n=== Testing Login for {expected_role} ===")
    try:
        login_data = {"email": email, "password": password}
        response = requests.post(LOGIN_URL, json=login_data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            if data.get('role') == expected_role:
                print(f"✅ Login successful! Role is correctly set to '{expected_role}'")
                return True
            else:
                print(f"❌ Role mismatch! Expected '{expected_role}', got '{data.get('role')}'")
                return False
        else:
            print(f"❌ Login failed: {response.json()}")
            return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def run_all_tests():
    """Run all tests"""
    print("=" * 50)
    print("ROLE-BASED AUTHENTICATION TEST SUITE")
    print("=" * 50)
    
    results = []
    
    # Test 1: Create staff account
    results.append(("Create Staff", test_create_staff()))
    
    # Test 2: Create admin account
    results.append(("Create Admin", test_create_admin()))
    
    # Test 3: Login as staff
    results.append(("Login as Staff", test_login(staff_data["email"], staff_data["password"], "staff")))
    
    # Test 4: Login as admin
    results.append(("Login as Admin", test_login(admin_data["email"], admin_data["password"], "admin")))
    
    # Print summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")
    print("=" * 50)

if __name__ == "__main__":
    print("\n⚠️  Make sure your Django server is running before running this test!")
    print("⚠️  This will create test accounts in your database.")
    input("\nPress Enter to continue or Ctrl+C to cancel...")
    
    run_all_tests()
    
    print("\n📝 Note: You can now login with these test accounts:")
    print(f"   Staff: {staff_data['email']} / {staff_data['password']}")
    print(f"   Admin: {admin_data['email']} / {admin_data['password']}")
