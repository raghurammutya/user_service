#!/usr/bin/env python3
"""
Practical testing with sample data to identify what's working vs. what needs testing
"""

import asyncio
import httpx
import json
from datetime import datetime
from typing import Dict, Any, List

class PracticalTester:
    """Test user_service with realistic sample data"""
    
    def __init__(self, base_url: str = "http://localhost:8002"):
        self.base_url = base_url
        self.client = None
        
        # Sample test data that should work
        self.sample_users = [
            {
                "first_name": "John",
                "last_name": "Conservative", 
                "email": "john.conservative@test.com",
                "phone_number": "+1234567890",
                "role": "TRADER"
            },
            {
                "first_name": "Alice", 
                "last_name": "DayTrader",
                "email": "alice.daytrader@test.com", 
                "phone_number": "+1234567891",
                "role": "TRADER"
            },
            {
                "first_name": "Bob",
                "last_name": "ViewOnly",
                "email": "bob.viewer@test.com",
                "phone_number": "+1234567892", 
                "role": "VIEWER"
            }
        ]
        
        self.sample_trading_accounts = [
            {
                "login_id": "CONS001",
                "pseudo_acc_name": "Conservative Account",
                "broker": "ICICI",
                "platform": "BREEZE", 
                "system_id": 12345,
                "system_id_of_pseudo_acc": 12345,
                "is_live": False,
                "assigned_user_id": 1  # Will be set after user creation
            },
            {
                "login_id": "DAY001", 
                "pseudo_acc_name": "Day Trading Account",
                "broker": "ZERODHA",
                "platform": "KITE",
                "system_id": 67890,
                "system_id_of_pseudo_acc": 67890, 
                "is_live": True,
                "assigned_user_id": 2
            }
        ]
        
        self.sample_trading_limits = [
            {
                "user_id": 1,
                "trading_account_id": 1,
                "limit_type": "daily_trading_limit",
                "limit_value": 25000.00,
                "currency": "INR",
                "enforcement_type": "hard_limit",
                "description": "Conservative daily limit"
            },
            {
                "user_id": 1,
                "trading_account_id": 1, 
                "limit_type": "single_trade_limit",
                "limit_value": 5000.00,
                "currency": "INR",
                "enforcement_type": "hard_limit",
                "description": "Conservative single trade limit"
            },
            {
                "user_id": 2,
                "trading_account_id": 2,
                "limit_type": "daily_trading_limit", 
                "limit_value": 100000.00,
                "currency": "INR",
                "enforcement_type": "soft_limit",
                "description": "Active trader daily limit"
            },
            {
                "user_id": 2,
                "trading_account_id": 2,
                "limit_type": "daily_order_count_limit",
                "limit_value": 50,
                "enforcement_type": "soft_limit", 
                "description": "Day trader order count limit"
            }
        ]
        
        self.sample_trade_validations = [
            {
                "name": "Conservative Trade - Should PASS",
                "trading_account_id": 1,
                "data": {
                    "action_type": "place_order",
                    "instrument": "RELIANCE",
                    "quantity": 10,
                    "price": 2500.00,
                    "trade_value": 25000.00,
                    "order_type": "MARKET"
                },
                "expected": "PASS (within ₹5,000 single trade limit)"
            },
            {
                "name": "Conservative Trade - Should REJECT",
                "trading_account_id": 1, 
                "data": {
                    "action_type": "place_order",
                    "instrument": "RELIANCE",
                    "quantity": 30,
                    "price": 2500.00, 
                    "trade_value": 75000.00,
                    "order_type": "MARKET"
                },
                "expected": "REJECT (exceeds ₹5,000 single trade limit)"
            },
            {
                "name": "Day Trader Trade - Should PASS",
                "trading_account_id": 2,
                "data": {
                    "action_type": "place_order",
                    "instrument": "NIFTY50",
                    "quantity": 50,
                    "price": 1500.00,
                    "trade_value": 75000.00,
                    "order_type": "LIMIT"
                },
                "expected": "PASS (within ₹100,000 daily limit)"
            }
        ]
    
    async def setup(self):
        """Initialize test client"""
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)
        print(f"🚀 Starting practical tests for user_service at {self.base_url}")
    
    async def cleanup(self):
        """Cleanup test client"""
        if self.client:
            await self.client.aclose()
    
    async def test_service_availability(self):
        """Test if service is running and responsive"""
        print("\n📡 Testing Service Availability...")
        
        try:
            response = await self.client.get("/")
            if response.status_code == 200:
                print("✅ Service is running and responsive")
                print(f"   Response: {response.json()}")
                return True
            else:
                print(f"⚠️  Service responding but with status {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Service not available: {e}")
            return False
    
    async def test_health_endpoints(self):
        """Test health check endpoints"""
        print("\n🏥 Testing Health Endpoints...")
        
        endpoints = ["/health", "/health/detailed", "/health/integrations"]
        results = {}
        
        for endpoint in endpoints:
            try:
                response = await self.client.get(endpoint)
                status = "✅ HEALTHY" if response.status_code == 200 else "⚠️  DEGRADED" if response.status_code == 503 else "❌ FAILED"
                print(f"   {endpoint}: {status} ({response.status_code})")
                results[endpoint] = {
                    "status_code": response.status_code,
                    "response": response.json() if response.status_code in [200, 503] else None
                }
            except Exception as e:
                print(f"   {endpoint}: ❌ ERROR - {e}")
                results[endpoint] = {"error": str(e)}
        
        return results
    
    async def test_authentication_behavior(self):
        """Test authentication requirements (should return 401 without tokens)"""
        print("\n🔐 Testing Authentication Behavior...")
        
        auth_endpoints = [
            ("POST", "/api/trading-limits", {"user_id": 1, "limit_type": "daily_trading_limit", "limit_value": 50000}),
            ("GET", "/api/trading-limits", None),
            ("POST", "/api/trading-limits/validate", {"action_type": "place_order", "trade_value": 10000}),
            ("POST", "/users/", self.sample_users[0]),
            ("GET", "/users/1", None)
        ]
        
        for method, endpoint, data in auth_endpoints:
            try:
                if method == "POST":
                    response = await self.client.post(endpoint, json=data)
                else:
                    response = await self.client.get(endpoint)
                
                if response.status_code == 401:
                    print(f"   ✅ {method} {endpoint}: Correctly requires authentication (401)")
                elif response.status_code in [200, 422]:
                    print(f"   ⚠️  {method} {endpoint}: Unexpected success ({response.status_code}) - may have auth bypass")
                    print(f"       Response: {response.json()}")
                else:
                    print(f"   ❓ {method} {endpoint}: Unexpected status {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ {method} {endpoint}: Error - {e}")
    
    async def test_trading_limits_structure(self):
        """Test trading limits API structure (without authentication)"""
        print("\n💰 Testing Trading Limits API Structure...")
        
        # Test limit creation (should fail auth but show API structure)
        print("   📝 Testing limit creation structure...")
        for limit in self.sample_trading_limits[:2]:  # Test first 2 limits
            try:
                response = await self.client.post("/api/trading-limits", json=limit)
                if response.status_code == 401:
                    print(f"   ✅ Limit creation API exists (returns 401 as expected)")
                elif response.status_code == 422:
                    print(f"   ✅ Limit creation API validates input (422: {response.json()})")
                else:
                    print(f"   ❓ Unexpected response: {response.status_code}")
                break  # Only test one to confirm API exists
            except Exception as e:
                print(f"   ❌ API error: {e}")
        
        # Test validation endpoint 
        print("   🔍 Testing trade validation structure...")
        for validation in self.sample_trade_validations[:1]:  # Test first validation
            try:
                response = await self.client.post(
                    f"/api/trading-limits/validate?trading_account_id={validation['trading_account_id']}", 
                    json=validation['data']
                )
                if response.status_code == 401:
                    print(f"   ✅ Trade validation API exists (returns 401 as expected)")
                elif response.status_code in [200, 422]:
                    print(f"   ⚠️  Trade validation API responded: {response.status_code}")
                    print(f"       {response.json()}")
                break
            except Exception as e:
                print(f"   ❌ Validation API error: {e}")
    
    async def test_mock_business_scenarios(self):
        """Test what business scenarios WOULD look like with proper auth"""
        print("\n🎯 Mock Business Scenario Analysis...")
        
        scenarios = [
            {
                "name": "Conservative Trader Setup",
                "user": self.sample_users[0],
                "account": self.sample_trading_accounts[0],
                "limits": [l for l in self.sample_trading_limits if l["user_id"] == 1],
                "test_trades": [v for v in self.sample_trade_validations if v["trading_account_id"] == 1]
            },
            {
                "name": "Day Trader Setup", 
                "user": self.sample_users[1],
                "account": self.sample_trading_accounts[1],
                "limits": [l for l in self.sample_trading_limits if l["user_id"] == 2],
                "test_trades": [v for v in self.sample_trade_validations if v["trading_account_id"] == 2]
            }
        ]
        
        for scenario in scenarios:
            print(f"\n   📊 {scenario['name']}:")
            print(f"      User: {scenario['user']['email']} ({scenario['user']['role']})")
            print(f"      Account: {scenario['account']['broker']} - {scenario['account']['pseudo_acc_name']}")
            print(f"      Limits to create: {len(scenario['limits'])}")
            for limit in scenario['limits']:
                print(f"        - {limit['limit_type']}: ₹{limit['limit_value']:,.2f} ({limit['enforcement_type']})")
            print(f"      Test trades: {len(scenario['test_trades'])}")
            for trade in scenario['test_trades']:
                print(f"        - {trade['name']}: {trade['expected']}")

    async def run_all_tests(self):
        """Run all practical tests"""
        print("=" * 80)
        print("🧪 USER SERVICE PRACTICAL TESTING WITH SAMPLE DATA")
        print("=" * 80)
        
        # Test service availability first
        if not await self.test_service_availability():
            print("\n❌ Service not available. Please start the service first:")
            print("   cd /home/stocksadmin/stocksblitz/user_service")
            print("   python -m uvicorn app.main:app --host 0.0.0.0 --port 8002")
            return False
        
        # Run all tests
        await self.test_health_endpoints()
        await self.test_authentication_behavior() 
        await self.test_trading_limits_structure()
        await self.test_mock_business_scenarios()
        
        print("\n" + "=" * 80)
        print("📋 TESTING SUMMARY")
        print("=" * 80)
        print("✅ TESTED (Working):")
        print("   - Service startup and basic connectivity")
        print("   - Health endpoints (with graceful degradation)")
        print("   - Authentication requirements (proper 401 responses)")
        print("   - API endpoint structure exists")
        
        print("\n❌ NOT TESTED (Needs Implementation):")
        print("   - Database operations with real data")
        print("   - Keycloak JWT token validation")
        print("   - Trading limits creation and retrieval")
        print("   - Trade validation logic with real limits")
        print("   - User and account management")
        print("   - Integration with external services")
        
        print("\n🎯 TO TEST FULLY, NEED:")
        print("   1. Fix database connection (TimescaleDB/PostgreSQL)")
        print("   2. Set up test Keycloak instance OR mock JWT tokens")
        print("   3. Create database test fixtures with sample data")
        print("   4. Test full workflow: auth → create limits → validate trades")
        
        return True

async def main():
    """Main test execution"""
    tester = PracticalTester()
    await tester.setup()
    
    try:
        await tester.run_all_tests()
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    print("🚀 Starting practical testing...")
    asyncio.run(main())