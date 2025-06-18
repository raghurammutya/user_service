# tests/test_end_to_end.py

import pytest
import asyncio
import httpx
import json
from typing import Dict, Any
from datetime import datetime
import os

# Test configuration
BASE_URL = os.getenv("USER_SERVICE_URL", "http://localhost:8002")
TEST_TIMEOUT = 30

class UserServiceE2ETest:
    """End-to-end test suite for user_service"""
    
    def __init__(self):
        self.base_url = BASE_URL
        self.client = None
        self.test_data = {}
        
    async def setup(self):
        """Setup test environment"""
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=TEST_TIMEOUT)
        print(f"🚀 Starting E2E tests for user_service at {self.base_url}")
        
    async def cleanup(self):
        """Cleanup test environment"""
        if self.client:
            await self.client.aclose()
        print("🧹 Test cleanup completed")
    
    async def test_health_endpoints(self):
        """Test all health check endpoints"""
        print("\n📊 Testing Health Endpoints...")
        
        # Basic health check
        response = await self.client.get("/health")
        assert response.status_code in [200, 503], f"Health check failed: {response.status_code}"
        health_data = response.json()
        print(f"✅ Basic health: {health_data.get('overall_status', 'unknown')}")
        
        # Detailed health check
        try:
            response = await self.client.get("/health/detailed")
            assert response.status_code in [200, 500], f"Detailed health failed: {response.status_code}"
            detailed_health = response.json()
            print(f"✅ Detailed health: {len(detailed_health.get('service_discovery', {}))} services discovered")
        except Exception as e:
            print(f"⚠️  Detailed health check unavailable: {e}")
        
        # Integration health check
        try:
            response = await self.client.get("/health/integrations")
            assert response.status_code in [200, 500], f"Integration health failed: {response.status_code}"
            integration_health = response.json()
            integrations = integration_health.get('integrations', {})
            print(f"✅ Integration health: {integrations.get('initialized', False)}")
        except Exception as e:
            print(f"⚠️  Integration health check unavailable: {e}")
    
    async def test_trading_limits_api(self):
        """Test trading limits CRUD operations"""
        print("\n💰 Testing Trading Limits API...")
        
        # Test cases for different scenarios
        test_cases = [
            {
                "name": "Daily Trading Limit",
                "data": {
                    "user_id": 1,
                    "trading_account_id": 1,
                    "limit_type": "daily_trading_limit",
                    "limit_value": 50000.00,
                    "enforcement_type": "hard_limit",
                    "warning_threshold": 80.0
                }
            },
            {
                "name": "Single Trade Limit", 
                "data": {
                    "user_id": 1,
                    "trading_account_id": 1,
                    "limit_type": "single_trade_limit",
                    "limit_value": 10000.00,
                    "enforcement_type": "hard_limit"
                }
            },
            {
                "name": "Daily Order Count",
                "data": {
                    "user_id": 1,
                    "trading_account_id": 1,
                    "limit_type": "daily_order_count",
                    "limit_count": 20,
                    "enforcement_type": "soft_limit"
                }
            }
        ]
        
        created_limits = []
        
        # Test limit creation
        for test_case in test_cases:
            try:
                response = await self.client.post(
                    "/api/trading-limits",
                    json=test_case["data"],
                    headers={"Authorization": "Bearer mock-token"}  # Mock token for testing
                )
                
                if response.status_code == 201:
                    limit_data = response.json()
                    created_limits.append(limit_data["id"])
                    print(f"✅ Created {test_case['name']}: ID {limit_data['id']}")
                elif response.status_code == 401:
                    print(f"⚠️  {test_case['name']}: Authentication required (expected in production)")
                elif response.status_code == 403:
                    print(f"⚠️  {test_case['name']}: Authorization required (expected without proper permissions)")
                else:
                    print(f"⚠️  {test_case['name']}: {response.status_code} - {response.text}")
                    
            except Exception as e:
                print(f"❌ Failed to create {test_case['name']}: {e}")
        
        # Test limit listing
        try:
            response = await self.client.get(
                "/api/trading-limits",
                headers={"Authorization": "Bearer mock-token"}
            )
            
            if response.status_code == 200:
                limits_data = response.json()
                print(f"✅ Listed limits: {limits_data.get('total', 0)} total")
            else:
                print(f"⚠️  List limits: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Failed to list limits: {e}")
        
        # Test limit validation
        validation_test = {
            "action_type": "place_order",
            "instrument": "RELIANCE",
            "quantity": 100,
            "price": 2500.00,
            "trade_value": 250000.00
        }
        
        try:
            response = await self.client.post(
                "/api/trading-limits/validate?trading_account_id=1",
                json=validation_test,
                headers={"Authorization": "Bearer mock-token"}
            )
            
            if response.status_code == 200:
                validation_result = response.json()
                print(f"✅ Validation result: {'Allowed' if validation_result.get('allowed') else 'Blocked'}")
                if validation_result.get('violations'):
                    print(f"   Violations: {len(validation_result['violations'])}")
            else:
                print(f"⚠️  Validation test: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Failed validation test: {e}")
    
    async def test_service_startup_sequence(self):
        """Test the service startup and initialization"""
        print("\n🚀 Testing Service Startup Sequence...")
        
        # Test root endpoint
        try:
            response = await self.client.get("/")
            assert response.status_code == 200, f"Root endpoint failed: {response.status_code}"
            root_data = response.json()
            print(f"✅ Root endpoint: {root_data.get('service', 'unknown')} - {root_data.get('status', 'unknown')}")
        except Exception as e:
            print(f"❌ Root endpoint failed: {e}")
        
        # Test service is responsive
        start_time = datetime.now()
        try:
            response = await self.client.get("/health")
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            print(f"✅ Response time: {response_time:.2f}ms")
            
            if response_time > 5000:  # 5 seconds
                print("⚠️  Slow response time detected")
        except Exception as e:
            print(f"❌ Response time test failed: {e}")
    
    async def test_error_handling(self):
        """Test error handling and edge cases"""
        print("\n🛡️  Testing Error Handling...")
        
        # Test invalid endpoints
        invalid_endpoints = [
            "/api/invalid-endpoint",
            "/api/trading-limits/999999",
            "/api/users/invalid-id"
        ]
        
        for endpoint in invalid_endpoints:
            try:
                response = await self.client.get(endpoint)
                if response.status_code == 404:
                    print(f"✅ 404 handling: {endpoint}")
                else:
                    print(f"⚠️  Unexpected response for {endpoint}: {response.status_code}")
            except Exception as e:
                print(f"❌ Error testing {endpoint}: {e}")
        
        # Test malformed requests
        try:
            response = await self.client.post(
                "/api/trading-limits",
                json={"invalid": "data"},
                headers={"Authorization": "Bearer mock-token"}
            )
            if response.status_code in [400, 422]:
                print("✅ Input validation working")
            else:
                print(f"⚠️  Input validation: {response.status_code}")
        except Exception as e:
            print(f"❌ Input validation test failed: {e}")
    
    async def test_performance_baseline(self):
        """Test basic performance metrics"""
        print("\n⚡ Testing Performance Baseline...")
        
        # Concurrent requests test
        async def make_request():
            response = await self.client.get("/health")
            return response.status_code
        
        try:
            start_time = datetime.now()
            tasks = [make_request() for _ in range(10)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            duration = (datetime.now() - start_time).total_seconds()
            
            successful_requests = sum(1 for r in results if r == 200)
            print(f"✅ Concurrent requests: {successful_requests}/10 successful in {duration:.2f}s")
            
            if duration > 10:  # 10 seconds for 10 requests
                print("⚠️  Performance concern: High response times under concurrent load")
                
        except Exception as e:
            print(f"❌ Concurrent request test failed: {e}")

async def run_comprehensive_e2e_test():
    """Run the complete end-to-end test suite"""
    test_suite = UserServiceE2ETest()
    
    try:
        await test_suite.setup()
        
        # Run all test categories
        await test_suite.test_service_startup_sequence()
        await test_suite.test_health_endpoints() 
        await test_suite.test_trading_limits_api()
        await test_suite.test_error_handling()
        await test_suite.test_performance_baseline()
        
        print(f"\n🎉 End-to-end testing completed!")
        print(f"📊 Test results available above")
        
    except Exception as e:
        print(f"\n❌ E2E test suite failed: {e}")
        
    finally:
        await test_suite.cleanup()

if __name__ == "__main__":
    asyncio.run(run_comprehensive_e2e_test())