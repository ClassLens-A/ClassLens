"""
Test Script for Student Mobile API Endpoints
Run this after starting your Django server to verify the new endpoints work correctly.

Usage: python test_student_mobile_apis.py
"""

import requests
import json
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:8000/api"
# Replace with an actual student ID from your database
TEST_STUDENT_ID = 1
# Replace with an actual subject ID from your database
TEST_SUBJECT_ID = 1

def print_response(response, endpoint_name):
    """Pretty print API response"""
    print(f"\n{'='*60}")
    print(f"Testing: {endpoint_name}")
    print(f"{'='*60}")
    print(f"Status Code: {response.status_code}")
    print(f"Response:")
    print(json.dumps(response.json(), indent=2))
    print(f"{'='*60}\n")

def test_student_profile():
    """Test 1: Student Profile Endpoint"""
    url = f"{BASE_URL}/student/profile/"
    payload = {"student_id": TEST_STUDENT_ID}
    
    response = requests.post(url, json=payload)
    print_response(response, "GET STUDENT PROFILE")
    
    # Verify expected fields
    if response.status_code == 200:
        data = response.json()
        required_fields = ["email", "department", "semester", "attendance_percentage", "total_classes"]
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            print(f"⚠️  WARNING: Missing fields: {missing_fields}")
        else:
            print("✅ All required fields present!")
            print(f"   - Email: {data['email']}")
            print(f"   - Department: {data['department']}")
            print(f"   - Semester: {data['semester']}")
            print(f"   - Attendance: {data['attendance_percentage']}%")
            print(f"   - Total Classes: {data['total_classes']}")

def test_attendance_history():
    """Test 2: Attendance History Endpoint"""
    url = f"{BASE_URL}/student/attendance/history/"
    
    # Test with date range (last 30 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    payload = {
        "student_id": TEST_STUDENT_ID,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat()
    }
    
    response = requests.post(url, json=payload)
    print_response(response, "GET ATTENDANCE HISTORY")
    
    # Verify expected fields
    if response.status_code == 200:
        data = response.json()
        if "attendance_records" in data:
            records = data["attendance_records"]
            print(f"✅ Found {len(records)} attendance records")
            
            if records:
                print("\n📋 Sample record:")
                sample = records[0]
                print(f"   - Date: {sample.get('date')}")
                print(f"   - Subject: {sample.get('subject_name')}")
                print(f"   - Status: {sample.get('status')}")
                print(f"   - Time: {sample.get('time')}")
                
                # Verify status format
                statuses = set(r.get('status') for r in records)
                if statuses.issubset({'Present', 'Absent'}):
                    print("✅ Status format correct (Present/Absent)")
                else:
                    print(f"⚠️  WARNING: Unexpected statuses: {statuses}")
        else:
            print("⚠️  WARNING: Missing 'attendance_records' field")

def test_subject_attendance_details():
    """Test 3: Subject Attendance Details Endpoint"""
    url = f"{BASE_URL}/student/subject/attendance/"
    payload = {
        "student_id": TEST_STUDENT_ID,
        "subject_id": TEST_SUBJECT_ID
    }
    
    response = requests.post(url, json=payload)
    print_response(response, "GET SUBJECT ATTENDANCE DETAILS")
    
    # Verify expected fields
    if response.status_code == 200:
        data = response.json()
        if "attendance_records" in data:
            records = data["attendance_records"]
            print(f"✅ Found {len(records)} subject attendance records")
            
            if records:
                print("\n📋 Sample record:")
                sample = records[0]
                print(f"   - Date: {sample.get('date')}")
                print(f"   - Status: {sample.get('status')}")
                
                # Verify date format (ISO 8601)
                try:
                    datetime.fromisoformat(sample.get('date').replace('Z', '+00:00'))
                    print("✅ Date format correct (ISO 8601)")
                except:
                    print(f"⚠️  WARNING: Invalid date format: {sample.get('date')}")
        else:
            print("⚠️  WARNING: Missing 'attendance_records' field")

def test_error_handling():
    """Test 4: Error Handling"""
    print(f"\n{'='*60}")
    print("Testing: ERROR HANDLING")
    print(f"{'='*60}")
    
    # Test missing student_id
    url = f"{BASE_URL}/student/profile/"
    response = requests.post(url, json={})
    print(f"\n1. Missing student_id: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    # Test invalid student_id
    response = requests.post(url, json={"student_id": 999999})
    print(f"\n2. Invalid student_id: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    # Test missing subject_id in subject details
    url = f"{BASE_URL}/student/subject/attendance/"
    response = requests.post(url, json={"student_id": TEST_STUDENT_ID})
    print(f"\n3. Missing subject_id: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    print(f"\n{'='*60}\n")

if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════╗
║     Student Mobile API Endpoints - Test Suite             ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    print(f"Testing against: {BASE_URL}")
    print(f"Test Student ID: {TEST_STUDENT_ID}")
    print(f"Test Subject ID: {TEST_SUBJECT_ID}")
    print("\n⚠️  Update TEST_STUDENT_ID and TEST_SUBJECT_ID with actual IDs from your database!\n")
    
    try:
        # Run all tests
        test_student_profile()
        test_attendance_history()
        test_subject_attendance_details()
        test_error_handling()
        
        print("\n" + "="*60)
        print("✅ All tests completed!")
        print("="*60)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to server.")
        print("   Make sure Django server is running at:", BASE_URL)
        print("   Run: cd ClassLens_DB && python manage.py runserver")
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
