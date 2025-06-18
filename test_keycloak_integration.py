#!/usr/bin/env python3
"""
Test Keycloak integration and get real JWT tokens
"""

import asyncio
import httpx
import json
from typing import Dict, Any

class KeycloakTester:
    """Test Keycloak integration with user_service"""
    
    def __init__(self):
        self.keycloak_url = "http://localhost:8080"
        self.user_service_url = "http://localhost:8002"
        self.realm = "master"
        self.client_id = "admin-cli"
        self.admin_username = "admin"
        self.admin_password = "admin"
        
    async def test_keycloak_accessibility(self):
        """Test if Keycloak is accessible"""
        print("🔍 Testing Keycloak accessibility...")
        
        async with httpx.AsyncClient() as client:
            try:
                # Test realm info
                response = await client.get(f"{self.keycloak_url}/realms/{self.realm}")
                if response.status_code == 200:
                    realm_info = response.json()
                    print(f"✅ Keycloak realm '{self.realm}' accessible")
                    print(f"   Issuer: {realm_info.get('issuer', 'N/A')}")
                    return True
                else:
                    print(f"❌ Keycloak realm not accessible: {response.status_code}")
                    return False
            except Exception as e:
                print(f"❌ Keycloak connection failed: {e}")
                return False
    
    async def get_admin_token(self):
        """Get admin access token from Keycloak"""
        print("🔑 Getting admin token from Keycloak...")
        
        token_url = f"{self.keycloak_url}/realms/{self.realm}/protocol/openid-connect/token"
        
        data = {
            "grant_type": "password",
            "client_id": self.client_id,
            "username": self.admin_username,
            "password": self.admin_password
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(token_url, data=data)
                if response.status_code == 200:
                    token_data = response.json()
                    access_token = token_data.get("access_token")
                    print(f"✅ Got admin access token (length: {len(access_token)})")
                    print(f"   Token type: {token_data.get('token_type')}")
                    print(f"   Expires in: {token_data.get('expires_in')} seconds")
                    return access_token
                else:
                    print(f"❌ Failed to get token: {response.status_code}")
                    print(f"   Response: {response.text}")
                    return None
            except Exception as e:
                print(f"❌ Token request failed: {e}")
                return None
    
    async def test_user_service_with_token(self, token: str):
        """Test user_service endpoints with real JWT token"""
        print("\n🧪 Testing user_service with real JWT token...")
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Test endpoints that require authentication
        test_cases = [
            {
                "name": "Create trading limit",
                "method": "POST",
                "endpoint": "/api/trading-limits",
                "data": {
                    "user_id": 1,
                    "trading_account_id": 1,
                    "limit_type": "daily_trading_limit",
                    "limit_value": 50000.00,
                    "currency": "INR",
                    "enforcement_type": "hard_limit"
                }
            },
            {
                "name": "List trading limits",
                "method": "GET", 
                "endpoint": "/api/trading-limits",
                "data": None
            },
            {
                "name": "Validate trade",
                "method": "POST",
                "endpoint": "/api/trading-limits/validate?trading_account_id=1",
                "data": {
                    "action_type": "place_order",
                    "instrument": "RELIANCE",
                    "quantity": 10,
                    "price": 2500.00,
                    "trade_value": 25000.00
                }
            },
            {
                "name": "Create user",
                "method": "POST",
                "endpoint": "/users/",
                "data": {
                    "first_name": "Test",
                    "last_name": "User",
                    "email": "test.user@example.com",
                    "phone_number": "+1234567890",
                    "role": "VIEWER"  # Use enum value that matches UserRole
                }
            }
        ]
        
        async with httpx.AsyncClient() as client:
            for test_case in test_cases:
                try:
                    print(f"\n   🔸 {test_case['name']}...")
                    
                    if test_case['method'] == 'POST':
                        response = await client.post(
                            f"{self.user_service_url}{test_case['endpoint']}", 
                            headers=headers,
                            json=test_case['data']
                        )
                    else:
                        response = await client.get(
                            f"{self.user_service_url}{test_case['endpoint']}", 
                            headers=headers
                        )
                    
                    print(f"      Status: {response.status_code}")
                    
                    if response.status_code == 200:
                        print(f"      ✅ SUCCESS: {response.json()}")
                    elif response.status_code == 401:
                        print(f"      🔒 AUTHENTICATION REQUIRED (token not working)")
                    elif response.status_code == 422:
                        print(f"      ⚠️  VALIDATION ERROR: {response.json()}")
                    elif response.status_code == 500:
                        print(f"      ❌ SERVER ERROR: {response.text}")
                    else:
                        print(f"      ❓ UNEXPECTED: {response.status_code} - {response.text}")
                        
                except Exception as e:
                    print(f"      ❌ REQUEST FAILED: {e}")
    
    async def test_user_service_auth_endpoint(self, token: str):
        """Test user_service Keycloak login endpoint"""
        print("\n🔐 Testing user_service Keycloak authentication...")
        
        async with httpx.AsyncClient() as client:
            try:
                # Test Keycloak login endpoint
                response = await client.post(
                    f"{self.user_service_url}/auth/keycloak-login",
                    params={
                        "username": self.admin_username,
                        "password": self.admin_password
                    }
                )
                
                print(f"   Keycloak login status: {response.status_code}")
                if response.status_code == 200:
                    result = response.json()
                    print(f"   ✅ Keycloak login successful")
                    print(f"   User: {result.get('user', {}).get('email', 'N/A')}")
                    print(f"   Token: {result.get('access_token', 'N/A')[:50]}...")
                    return result.get('access_token')
                else:
                    print(f"   ❌ Keycloak login failed: {response.text}")
                    return None
                    
            except Exception as e:
                print(f"   ❌ Keycloak login error: {e}")
                return None
    
    async def run_full_test(self):
        """Run complete Keycloak integration test"""
        print("=" * 80)
        print("🔐 KEYCLOAK INTEGRATION TESTING")
        print("=" * 80)
        
        # Test 1: Keycloak accessibility
        if not await self.test_keycloak_accessibility():
            print("\n❌ Keycloak not accessible. Cannot proceed.")
            return False
        
        # Test 2: Get admin token
        admin_token = await self.get_admin_token()
        if not admin_token:
            print("\n❌ Cannot get admin token. Cannot proceed.")
            return False
        
        # Test 3: Test user_service with token
        await self.test_user_service_with_token(admin_token)
        
        # Test 4: Test user_service auth endpoint
        service_token = await self.test_user_service_auth_endpoint(admin_token)
        
        print("\n" + "=" * 80)
        print("📋 KEYCLOAK INTEGRATION SUMMARY")
        print("=" * 80)
        print("✅ WORKING:")
        print("   - Keycloak server accessible")
        print("   - Admin token generation")
        print("   - JWT token format")
        
        print("\n❓ NEEDS VERIFICATION:")
        print("   - JWT token validation in user_service")
        print("   - User provisioning from Keycloak")
        print("   - Role-based access control")
        print("   - Database operations with authentication")
        
        return True

async def main():
    """Main test execution"""
    tester = KeycloakTester()
    await tester.run_full_test()

if __name__ == "__main__":
    print("🚀 Starting Keycloak integration testing...")
    asyncio.run(main())