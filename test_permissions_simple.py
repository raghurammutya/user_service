#!/usr/bin/env python3
"""
Simple Permissions Test using the Service API
"""

import requests
import json
import time

BASE_URL = "http://localhost:8002"

def test_service_health():
    """Test if the service is running"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Service is healthy")
            return True
        else:
            print(f"❌ Service health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to service: {e}")
        return False

def create_test_user(user_data):
    """Create a test user"""
    try:
        response = requests.post(f"{BASE_URL}/users/", json=user_data)
        if response.status_code in [200, 201]:
            user = response.json()
            print(f"✅ Created user {user_data['first_name']}: ID {user.get('id', 'N/A')}")
            return user
        else:
            print(f"❌ Failed to create user {user_data['first_name']}: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error creating user {user_data['first_name']}: {e}")
        return None

def test_permissions_api():
    """Test the permissions API endpoints"""
    print("\n📊 Testing Permissions API")
    
    # Test data sharing endpoint
    print("\n🔍 Testing data sharing endpoint...")
    share_data = {
        "resource_types": ["positions"],
        "scope": "all_except", 
        "excluded_users": [2],
        "notes": "Test data sharing"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/permissions/data-sharing", json=share_data)
        print(f"Data sharing response: {response.status_code}")
        if response.status_code == 200:
            print("✅ Data sharing endpoint works")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"❌ Data sharing failed: {response.text}")
    except Exception as e:
        print(f"❌ Data sharing error: {e}")
    
    # Test trading permissions endpoint
    print("\n🔍 Testing trading permissions endpoint...")
    trading_data = {
        "grantee_user_id": 2,
        "permissions": [
            {"action": "create", "scope": "all"}
        ],
        "notes": "Test trading permission"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/permissions/trading", json=trading_data)
        print(f"Trading permissions response: {response.status_code}")
        if response.status_code == 200:
            print("✅ Trading permissions endpoint works")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"❌ Trading permissions failed: {response.text}")
    except Exception as e:
        print(f"❌ Trading permissions error: {e}")
    
    # Test permission check endpoint
    print("\n🔍 Testing permission check endpoint...")
    check_data = {
        "user_id": 2,
        "action": "create",
        "resource": "positions",
        "instrument_key": "NSE:TCS"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/permissions/trading/check", json=check_data)
        print(f"Permission check response: {response.status_code}")
        if response.status_code == 200:
            print("✅ Permission check endpoint works")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"❌ Permission check failed: {response.text}")
    except Exception as e:
        print(f"❌ Permission check error: {e}")

def main():
    print("🚀 Simple Permissions Testing")
    print("=" * 40)
    
    # Test service health
    if not test_service_health():
        print("Service is not running. Please start it first with:")
        print("cd /home/stocksadmin/stocksblitz/user_service && python app/main.py")
        return False
    
    # Create test users
    print("\n👥 Creating test users...")
    users_data = [
        {"first_name": "Alice", "last_name": "Manager", "email": "alice@test.com", "role": "ADMIN"},
        {"first_name": "Bob", "last_name": "Trader", "email": "bob@test.com", "role": "EDITOR"}
    ]
    
    created_users = []
    for user_data in users_data:
        user = create_test_user(user_data)
        if user:
            created_users.append(user)
    
    # Test permissions API
    test_permissions_api()
    
    print("\n🎯 Testing completed!")
    return True

if __name__ == "__main__":
    main()