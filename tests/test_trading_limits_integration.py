# tests/test_trading_limits_integration.py

import pytest
import asyncio
import httpx
from datetime import datetime
from typing import Dict, Any, List

class TradingLimitsIntegrationTest:
    """Integration tests specifically for trading limits functionality"""
    
    def __init__(self, base_url: str = "http://localhost:8002"):
        self.base_url = base_url
        self.client = None
        self.created_limits: List[int] = []
        
    async def setup(self):
        """Setup test client"""
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)
        
    async def cleanup(self):
        """Cleanup test data and client"""
        # Try to clean up created test data
        for limit_id in self.created_limits:
            try:
                await self.client.delete(
                    f"/api/trading-limits/{limit_id}",
                    headers={"Authorization": "Bearer test-token"}
                )
            except:
                pass  # Ignore cleanup errors
                
        if self.client:
            await self.client.aclose()
    
    async def test_limit_creation_scenarios(self):
        """Test various limit creation scenarios"""
        print("\n💰 Testing Trading Limit Creation Scenarios...")
        
        # Test cases covering different limit types
        test_scenarios = [
            {
                "name": "Daily Trading Limit - Conservative",
                "data": {
                    "user_id": 1,
                    "trading_account_id": 1,
                    "limit_type": "daily_trading_limit",
                    "limit_value": 25000.00,
                    "enforcement_type": "hard_limit",
                    "warning_threshold": 80.0,
                    "usage_reset_frequency": "daily"
                },
                "expected_behavior": "Should create conservative daily limit"
            },
            {
                "name": "Single Trade Limit - Aggressive",
                "data": {
                    "user_id": 1, 
                    "trading_account_id": 1,
                    "limit_type": "single_trade_limit",
                    "limit_value": 50000.00,
                    "enforcement_type": "soft_limit"
                },
                "expected_behavior": "Should create high single trade limit with warning"
            },
            {
                "name": "Order Count Limit",
                "data": {
                    "user_id": 1,
                    "trading_account_id": 1,
                    "limit_type": "daily_order_count",
                    "limit_count": 50,
                    "enforcement_type": "hard_limit"
                },
                "expected_behavior": "Should limit daily order count"
            },
            {
                "name": "Instrument Whitelist",
                "data": {
                    "user_id": 1,
                    "trading_account_id": 1,
                    "limit_type": "allowed_instruments",
                    "limit_text": "RELIANCE,TCS,INFY,HDFCBANK,ICICIBANK",
                    "enforcement_type": "hard_limit"
                },
                "expected_behavior": "Should restrict to blue-chip stocks only"
            },
            {
                "name": "Trading Hours Restriction",
                "data": {
                    "user_id": 1,
                    "trading_account_id": 1,
                    "limit_type": "trading_hours",
                    "start_time": "09:15:00",
                    "end_time": "15:30:00",
                    "allowed_days": "MONDAY,TUESDAY,WEDNESDAY,THURSDAY,FRIDAY",
                    "enforcement_type": "hard_limit"
                },
                "expected_behavior": "Should restrict trading to market hours only"
            }
        ]
        
        for scenario in test_scenarios:
            print(f"\n  📝 Testing: {scenario['name']}")
            print(f"     Expected: {scenario['expected_behavior']}")
            
            try:
                response = await self.client.post(
                    "/api/trading-limits",
                    json=scenario["data"],
                    headers={"Authorization": "Bearer test-token"}
                )
                
                print(f"     Status: {response.status_code}")
                
                if response.status_code == 201:
                    limit_data = response.json()
                    self.created_limits.append(limit_data["id"])
                    print(f"     ✅ Created limit ID: {limit_data['id']}")
                    print(f"     Details: {limit_data.get('limit_type')} = {limit_data.get('limit_value', limit_data.get('limit_count', 'N/A'))}")
                    
                elif response.status_code == 401:
                    print(f"     ⚠️  Authentication required (expected in production)")
                    
                elif response.status_code == 422:
                    print(f"     ⚠️  Validation error: {response.text}")
                    
                else:
                    print(f"     ❌ Unexpected response: {response.text}")
                    
            except Exception as e:
                print(f"     ❌ Request failed: {e}")
    
    async def test_limit_validation_scenarios(self):
        """Test trading action validation against limits"""
        print("\n🔍 Testing Trading Action Validation...")
        
        validation_scenarios = [
            {
                "name": "Small Trade - Should Pass",
                "data": {
                    "action_type": "place_order",
                    "instrument": "RELIANCE",
                    "quantity": 10,
                    "price": 2500.00,
                    "trade_value": 25000.00,
                    "order_type": "LIMIT"
                },
                "expected": "Should be allowed under most limits"
            },
            {
                "name": "Large Trade - May Hit Limits",
                "data": {
                    "action_type": "place_order",
                    "instrument": "RELIANCE", 
                    "quantity": 1000,
                    "price": 2500.00,
                    "trade_value": 2500000.00,
                    "order_type": "MARKET"
                },
                "expected": "Likely to exceed daily/single trade limits"
            },
            {
                "name": "Restricted Instrument",
                "data": {
                    "action_type": "place_order",
                    "instrument": "PENNY_STOCK_XYZ",
                    "quantity": 1000,
                    "price": 1.50,
                    "trade_value": 1500.00,
                    "order_type": "LIMIT"
                },
                "expected": "Should be blocked if instrument restrictions exist"
            },
            {
                "name": "After Hours Trading",
                "data": {
                    "action_type": "place_order",
                    "instrument": "TCS",
                    "quantity": 50,
                    "price": 3000.00,
                    "trade_value": 150000.00,
                    "order_type": "LIMIT"
                },
                "expected": "Should check trading hours restrictions"
            }
        ]
        
        for scenario in validation_scenarios:
            print(f"\n  🧪 Testing: {scenario['name']}")
            print(f"     Expected: {scenario['expected']}")
            
            try:
                response = await self.client.post(
                    "/api/trading-limits/validate?trading_account_id=1",
                    json=scenario["data"],
                    headers={"Authorization": "Bearer test-token"}
                )
                
                print(f"     Status: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    allowed = result.get("allowed", False)
                    violations = result.get("violations", [])
                    warnings = result.get("warnings", [])
                    
                    status_icon = "✅" if allowed else "🚫"
                    print(f"     {status_icon} Result: {'ALLOWED' if allowed else 'BLOCKED'}")
                    
                    if violations:
                        print(f"     Violations: {len(violations)}")
                        for violation in violations[:2]:  # Show first 2
                            print(f"       - {violation.get('message', 'Unknown violation')}")
                    
                    if warnings:
                        print(f"     Warnings: {len(warnings)}")
                        for warning in warnings[:2]:  # Show first 2
                            print(f"       - {warning.get('message', 'Unknown warning')}")
                            
                elif response.status_code == 401:
                    print(f"     ⚠️  Authentication required")
                    
                else:
                    print(f"     ❌ Validation failed: {response.text}")
                    
            except Exception as e:
                print(f"     ❌ Validation request failed: {e}")
    
    async def test_bulk_operations(self):
        """Test bulk limit operations"""
        print("\n📦 Testing Bulk Operations...")
        
        # Test bulk limit creation
        bulk_data = {
            "apply_to_all_users": True,
            "user_ids": [1, 2, 3],
            "limits": [
                {
                    "user_id": 1,
                    "trading_account_id": 1,
                    "limit_type": "daily_trading_limit",
                    "limit_value": 100000.00,
                    "enforcement_type": "hard_limit"
                },
                {
                    "user_id": 1,
                    "trading_account_id": 1,
                    "limit_type": "single_trade_limit",
                    "limit_value": 20000.00,
                    "enforcement_type": "hard_limit"
                }
            ]
        }
        
        try:
            response = await self.client.post(
                "/api/trading-limits/bulk-create",
                json=bulk_data,
                headers={"Authorization": "Bearer test-token"}
            )
            
            print(f"  Bulk creation status: {response.status_code}")
            
            if response.status_code == 200:
                results = response.json()
                print(f"  ✅ Created {len(results)} limits in bulk")
                for result in results:
                    self.created_limits.append(result["id"])
            elif response.status_code == 401:
                print(f"  ⚠️  Authentication required for bulk operations")
            else:
                print(f"  ❌ Bulk creation failed: {response.text}")
                
        except Exception as e:
            print(f"  ❌ Bulk creation request failed: {e}")
    
    async def test_limit_querying(self):
        """Test various limit querying scenarios"""
        print("\n🔎 Testing Limit Querying...")
        
        query_scenarios = [
            {
                "name": "List all limits",
                "params": {},
                "expected": "Should return paginated list of all limits"
            },
            {
                "name": "Filter by user",
                "params": {"user_id": 1},
                "expected": "Should return limits for specific user"
            },
            {
                "name": "Filter by account",
                "params": {"trading_account_id": 1},
                "expected": "Should return limits for specific trading account"
            },
            {
                "name": "Filter by limit type",
                "params": {"limit_type": "daily_trading_limit"},
                "expected": "Should return only daily trading limits"
            },
            {
                "name": "Filter active limits",
                "params": {"is_active": True},
                "expected": "Should return only active limits"
            },
            {
                "name": "Pagination test",
                "params": {"skip": 0, "limit": 5},
                "expected": "Should return first 5 limits"
            }
        ]
        
        for scenario in query_scenarios:
            print(f"\n  🔍 Testing: {scenario['name']}")
            print(f"     Expected: {scenario['expected']}")
            
            try:
                response = await self.client.get(
                    "/api/trading-limits",
                    params=scenario["params"],
                    headers={"Authorization": "Bearer test-token"}
                )
                
                print(f"     Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    total = data.get("total", 0)
                    limits = data.get("limits", [])
                    active_count = data.get("active_count", 0)
                    breached_count = data.get("breached_count", 0)
                    
                    print(f"     ✅ Found {len(limits)} limits (total: {total})")
                    print(f"     Active: {active_count}, Breached: {breached_count}")
                    
                elif response.status_code == 401:
                    print(f"     ⚠️  Authentication required")
                    
                else:
                    print(f"     ❌ Query failed: {response.text}")
                    
            except Exception as e:
                print(f"     ❌ Query request failed: {e}")

async def run_trading_limits_integration_test():
    """Run the complete trading limits integration test"""
    test_suite = TradingLimitsIntegrationTest()
    
    try:
        await test_suite.setup()
        
        print("🎯 Starting Trading Limits Integration Tests")
        print("=" * 60)
        
        await test_suite.test_limit_creation_scenarios()
        await test_suite.test_limit_validation_scenarios()
        await test_suite.test_bulk_operations()
        await test_suite.test_limit_querying()
        
        print(f"\n🎉 Trading Limits Integration Tests Completed!")
        
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        
    finally:
        await test_suite.cleanup()

if __name__ == "__main__":
    asyncio.run(run_trading_limits_integration_test())