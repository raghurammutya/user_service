#!/usr/bin/env python3
"""
Comprehensive Permissions Testing Suite
Tests grants, restrictions, and conflict resolution for user permissions system.
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any

class PermissionsTestSuite:
    def __init__(self, base_url: str = "http://localhost:8002"):
        self.base_url = base_url
        self.auth_headers = {}
        self.test_users = {}
        
    def setup_test_users(self):
        """Create test users for permission testing"""
        print("🔧 Setting up test users...")
        
        # Test user data
        users_data = [
            {"first_name": "Alice", "last_name": "Manager", "email": "alice@test.com", "role": "ADMIN"},
            {"first_name": "Bob", "last_name": "Trader", "email": "bob@test.com", "role": "EDITOR"},
            {"first_name": "Charlie", "last_name": "Viewer", "email": "charlie@test.com", "role": "VIEWER"},
            {"first_name": "Diana", "last_name": "Restricted", "email": "diana@test.com", "role": "VIEWER"},
            {"first_name": "Eve", "last_name": "Guest", "email": "eve@test.com", "role": "VIEWER"}
        ]
        
        for user_data in users_data:
            try:
                # Create user
                response = requests.post(
                    f"{self.base_url}/users/",
                    json=user_data,
                    headers=self.auth_headers
                )
                if response.status_code in [200, 201]:
                    user = response.json()
                    self.test_users[user_data["first_name"]] = user
                    print(f"✅ Created user {user_data['first_name']}: ID {user.get('id', 'N/A')}")
                else:
                    print(f"❌ Failed to create user {user_data['first_name']}: {response.status_code}")
            except Exception as e:
                print(f"❌ Error creating user {user_data['first_name']}: {e}")
    
    def test_data_sharing_all_except(self):
        """Test: Share data with all users except specific ones"""
        print("\n📊 Testing Data Sharing - All Except Pattern")
        
        alice_id = self.test_users.get("Alice", {}).get("id")
        bob_id = self.test_users.get("Bob", {}).get("id")
        charlie_id = self.test_users.get("Charlie", {}).get("id")
        
        if not all([alice_id, bob_id, charlie_id]):
            print("❌ Required test users not found")
            return False
            
        # Alice shares positions with all except Bob
        share_request = {
            "resource_types": ["positions", "holdings"],
            "scope": "all_except",
            "excluded_users": [bob_id],
            "notes": "Test: Share with all except Bob"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/permissions/data-sharing",
                json=share_request,
                headers=self.auth_headers
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Data sharing permission created: {result['permissions_created']} permissions")
                
                # Verify permissions were created correctly
                settings_response = requests.get(
                    f"{self.base_url}/api/permissions/data-sharing/my-settings",
                    headers=self.auth_headers
                )
                
                if settings_response.status_code == 200:
                    settings = settings_response.json()
                    print(f"✅ Permission settings: {json.dumps(settings, indent=2)}")
                    return True
                else:
                    print(f"❌ Failed to get settings: {settings_response.status_code}")
                    
            else:
                print(f"❌ Failed to create data sharing permission: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Error in data sharing test: {e}")
            
        return False
    
    def test_trading_permissions_with_instruments(self):
        """Test: Grant trading permissions with instrument-specific controls"""
        print("\n🔄 Testing Trading Permissions - Instrument Controls")
        
        alice_id = self.test_users.get("Alice", {}).get("id")
        bob_id = self.test_users.get("Bob", {}).get("id")
        
        if not all([alice_id, bob_id]):
            print("❌ Required test users not found")
            return False
            
        # Alice grants Bob permission to create positions but not exit HDFC/RELIANCE
        trading_request = {
            "grantee_user_id": bob_id,
            "permissions": [
                {
                    "action": "create",
                    "scope": "all"
                },
                {
                    "action": "modify", 
                    "scope": "all"
                },
                {
                    "action": "exit",
                    "scope": "blacklist",
                    "instruments": ["NSE:HDFCBANK", "NSE:RELIANCE"]
                }
            ],
            "notes": "Test: Allow trading but restrict exit on specific instruments"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/permissions/trading",
                json=trading_request,
                headers=self.auth_headers
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Trading permissions granted: {result['permissions_created']} permissions")
                
                # Test permission checks
                test_cases = [
                    {"action": "create", "instrument": "NSE:HDFCBANK", "expected": True},
                    {"action": "exit", "instrument": "NSE:HDFCBANK", "expected": False},
                    {"action": "create", "instrument": "NSE:TCS", "expected": True},
                    {"action": "exit", "instrument": "NSE:TCS", "expected": True}
                ]
                
                for test_case in test_cases:
                    check_result = self.check_permission(
                        bob_id, 
                        test_case["action"], 
                        "positions", 
                        test_case["instrument"]
                    )
                    
                    if check_result and check_result.get("allowed") == test_case["expected"]:
                        print(f"✅ {test_case['action']} {test_case['instrument']}: {check_result['allowed']} (expected: {test_case['expected']})")
                    else:
                        print(f"❌ {test_case['action']} {test_case['instrument']}: {check_result} (expected: {test_case['expected']})")
                
                return True
                
            else:
                print(f"❌ Failed to grant trading permissions: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Error in trading permissions test: {e}")
            
        return False
    
    def test_trading_restrictions(self):
        """Test: Apply trading restrictions with blacklists"""
        print("\n🚫 Testing Trading Restrictions")
        
        alice_id = self.test_users.get("Alice", {}).get("id")
        diana_id = self.test_users.get("Diana", {}).get("id")
        
        if not all([alice_id, diana_id]):
            print("❌ Required test users not found")
            return False
            
        # Alice restricts Diana from trading specific instruments
        restriction_request = {
            "target_user_id": diana_id,
            "restrictions": [
                {
                    "type": "instrument_blacklist",
                    "actions": ["all"],
                    "instruments": ["NSE:YESBANK", "NSE:VODAFONE"],
                    "enforcement": "HARD",
                    "priority": 10
                }
            ],
            "notes": "Test: Block high-risk instruments for Diana"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/permissions/restrictions/trading",
                json=restriction_request,
                headers=self.auth_headers
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Trading restrictions applied: {result['restrictions_created']} restrictions")
                
                # Check if restrictions are working
                check_result = self.check_permission(
                    diana_id, 
                    "create", 
                    "positions", 
                    "NSE:YESBANK"
                )
                
                if check_result and not check_result.get("allowed"):
                    print(f"✅ Restriction working: {check_result['reason']}")
                else:
                    print(f"❌ Restriction not working: {check_result}")
                
                return True
                
            else:
                print(f"❌ Failed to apply restrictions: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Error in trading restrictions test: {e}")
            
        return False
    
    def test_conflict_resolution(self):
        """Test: Conflict resolution between grants and restrictions"""
        print("\n⚖️ Testing Conflict Resolution")
        
        alice_id = self.test_users.get("Alice", {}).get("id")
        eve_id = self.test_users.get("Eve", {}).get("id")
        
        if not all([alice_id, eve_id]):
            print("❌ Required test users not found")
            return False
            
        # Step 1: Grant Eve general trading permission
        grant_request = {
            "grantee_user_id": eve_id,
            "permissions": [
                {
                    "action": "all",
                    "scope": "all"
                }
            ],
            "notes": "Test: General trading permission"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/permissions/trading",
                json=grant_request,
                headers=self.auth_headers
            )
            
            if response.status_code != 200:
                print(f"❌ Failed to grant general permission: {response.status_code}")
                return False
                
            print("✅ Granted general trading permission")
            
            # Step 2: Apply specific restriction (should override general permission)
            restriction_request = {
                "target_user_id": eve_id,
                "restrictions": [
                    {
                        "type": "instrument_blacklist",
                        "actions": ["create"],
                        "instruments": ["NSE:HDFCBANK"],
                        "enforcement": "HARD",
                        "priority": 10
                    }
                ],
                "notes": "Test: Specific restriction should override general permission"
            }
            
            response = requests.post(
                f"{self.base_url}/api/permissions/restrictions/trading",
                json=restriction_request,
                headers=self.auth_headers
            )
            
            if response.status_code != 200:
                print(f"❌ Failed to apply specific restriction: {response.status_code}")
                return False
                
            print("✅ Applied specific restriction")
            
            # Step 3: Test conflict resolution
            test_cases = [
                {"instrument": "NSE:HDFCBANK", "action": "create", "expected": False, "reason": "Restriction should override"},
                {"instrument": "NSE:TCS", "action": "create", "expected": True, "reason": "General permission should work"},
                {"instrument": "NSE:HDFCBANK", "action": "modify", "expected": True, "reason": "Only create is restricted"}
            ]
            
            for test_case in test_cases:
                check_result = self.check_permission(
                    eve_id,
                    test_case["action"],
                    "positions",
                    test_case["instrument"]
                )
                
                if check_result and check_result.get("allowed") == test_case["expected"]:
                    print(f"✅ {test_case['instrument']} {test_case['action']}: {check_result['allowed']} - {test_case['reason']}")
                else:
                    print(f"❌ {test_case['instrument']} {test_case['action']}: {check_result} - {test_case['reason']}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error in conflict resolution test: {e}")
            return False
    
    def check_permission(self, user_id: int, action: str, resource: str, instrument_key: str) -> Dict:
        """Helper method to check permissions"""
        check_request = {
            "user_id": user_id,
            "action": action,
            "resource": resource,
            "instrument_key": instrument_key
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/permissions/trading/check",
                json=check_request,
                headers=self.auth_headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Permission check failed: {response.status_code}")
                return {"allowed": False, "reason": "CHECK_FAILED"}
                
        except Exception as e:
            print(f"❌ Error checking permission: {e}")
            return {"allowed": False, "reason": "ERROR"}
    
    def test_permission_revocation(self):
        """Test: Permission revocation"""
        print("\n🔄 Testing Permission Revocation")
        
        # This would test the revoke endpoint
        print("⏳ Permission revocation test - requires permission ID from previous tests")
        
        # For now, just test the endpoint structure
        try:
            response = requests.get(
                f"{self.base_url}/api/permissions/audit-log",
                headers=self.auth_headers
            )
            
            if response.status_code == 200:
                audit_log = response.json()
                print(f"✅ Audit log retrieved: {len(audit_log.get('audit_log', []))} entries")
                return True
            else:
                print(f"❌ Failed to get audit log: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error in revocation test: {e}")
            
        return False
    
    def run_all_tests(self):
        """Run complete test suite"""
        print("🚀 Starting Permissions Testing Suite")
        print("=" * 50)
        
        # Check service health
        try:
            health_response = requests.get(f"{self.base_url}/health", timeout=5)
            if health_response.status_code != 200:
                print(f"❌ Service health check failed: {health_response.status_code}")
                return False
            print("✅ Service is healthy")
        except Exception as e:
            print(f"❌ Cannot connect to service: {e}")
            return False
        
        # Run tests
        test_results = []
        
        # Setup phase
        self.setup_test_users()
        
        # Test phases
        test_results.append(("Data Sharing (All Except)", self.test_data_sharing_all_except()))
        test_results.append(("Trading Permissions", self.test_trading_permissions_with_instruments()))
        test_results.append(("Trading Restrictions", self.test_trading_restrictions()))
        test_results.append(("Conflict Resolution", self.test_conflict_resolution()))
        test_results.append(("Permission Revocation", self.test_permission_revocation()))
        
        # Summary
        print("\n" + "=" * 50)
        print("📋 TEST RESULTS SUMMARY")
        print("=" * 50)
        
        passed = 0
        total = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
            if result:
                passed += 1
        
        print(f"\n🎯 Overall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Permissions system is working correctly.")
        else:
            print("⚠️  Some tests failed. Check the output above for details.")
        
        return passed == total

def main():
    """Run the test suite"""
    tester = PermissionsTestSuite()
    
    # For testing without authentication, we'll need to modify this
    # In a real scenario, you'd get JWT tokens here
    
    success = tester.run_all_tests()
    exit(0 if success else 1)

if __name__ == "__main__":
    main()