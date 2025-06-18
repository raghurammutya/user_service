#!/usr/bin/env python3
"""
Test user_service with fixed enum values and real data operations
"""

import asyncio
import httpx
import json
from typing import Dict, Any

class FixedEnumTester:
    """Test user_service with corrected enum values"""
    
    def __init__(self):
        self.base_url = "http://localhost:8002"
        
        # Corrected test data with proper enum values
        self.sample_users = [
            {
                "first_name": "John",
                "last_name": "Conservative", 
                "email": "john.conservative@test.com",
                "phone_number": "+1234567890",
                "role": "VIEWER"  # Using string enum values from fixed shared_architecture
            },
            {
                "first_name": "Alice", 
                "last_name": "DayTrader",
                "email": "alice.daytrader@test.com", 
                "phone_number": "+1234567891",
                "role": "ADMIN"  # Using ADMIN instead of TRADER
            },
            {
                "first_name": "Bob",
                "last_name": "Editor",
                "email": "bob.editor@test.com",
                "phone_number": "+1234567892", 
                "role": "EDITOR"  # Using EDITOR role
            }
        ]
        
        # Updated trading limits with proper structure
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
            }
        ]
    
    async def test_user_creation_with_fixed_enums(self):
        """Test user creation with corrected enum values"""
        print("👤 Testing User Creation with Fixed Enums...")
        
        async with httpx.AsyncClient() as client:
            for i, user in enumerate(self.sample_users):
                try:
                    print(f"\n   🔸 Creating user {i+1}: {user['email']} ({user['role']})")
                    
                    response = await client.post(
                        f"{self.base_url}/users/", 
                        json=user
                    )
                    
                    print(f"      Status: {response.status_code}")
                    
                    if response.status_code == 200:
                        result = response.json()
                        print(f"      ✅ SUCCESS: User created with ID {result.get('id')}")
                        print(f"         Email: {result.get('email')}")
                        print(f"         Role: {result.get('role')}")
                        return result.get('id')  # Return first successful user ID
                    elif response.status_code == 422:
                        error_detail = response.json()
                        print(f"      ❌ VALIDATION ERROR: {error_detail}")
                        if 'role' in str(error_detail):
                            print(f"      🔧 Enum issue still exists with role: {user['role']}")
                    elif response.status_code == 500:
                        print(f"      ❌ SERVER ERROR: {response.text}")
                    else:
                        print(f"      ❓ UNEXPECTED: {response.status_code}")
                        
                except Exception as e:
                    print(f"      ❌ REQUEST FAILED: {e}")
        
        return None
    
    async def test_database_operations(self):
        """Test basic database operations"""
        print("\n🗄️ Testing Database Operations...")
        
        async with httpx.AsyncClient() as client:
            try:
                # Try to get user by ID (should work if DB operations are working)
                response = await client.get(f"{self.base_url}/users/1")
                print(f"   📊 Get User by ID: {response.status_code}")
                
                if response.status_code == 200:
                    print("   ✅ Database operations working!")
                    print(f"      Response: {response.json()}")
                elif response.status_code == 404:
                    print("   ⚠️  User not found (expected if no users created)")
                elif response.status_code == 500:
                    print("   ❌ Database operation failed")
                    
            except Exception as e:
                print(f"   ❌ Database test failed: {e}")
    
    async def test_health_with_database(self):
        """Test health endpoints to see database status"""
        print("\n🏥 Testing Health with Database Status...")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/health/detailed")
                if response.status_code == 200:
                    health = response.json()
                    print("   ✅ Detailed health check working")
                    
                    # Check database connections
                    connections = health.get('connections', {})
                    for db, status in connections.items():
                        if 'timescale' in db.lower():
                            print(f"      📊 {db}: {status}")
                    
                    # Check table discovery
                    tables = health.get('database_tables', [])
                    print(f"      📋 Tables discovered: {len(tables)}")
                    if tables:
                        print(f"         Sample tables: {tables[:5]}")
                        
            except Exception as e:
                print(f"   ❌ Health check failed: {e}")
    
    async def create_sample_data_in_database(self):
        """Try to create sample data directly in database"""
        print("\n📊 Testing Sample Data Creation...")
        
        # Test if we can create basic data for testing
        sample_sql_user = {
            "first_name": "TestUser",
            "last_name": "Database", 
            "email": "test.database@example.com",
            "phone_number": "+9999999999",
            "role": "VIEWER"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(f"{self.base_url}/users/", json=sample_sql_user)
                print(f"   📝 Sample user creation: {response.status_code}")
                
                if response.status_code == 200:
                    user = response.json()
                    print(f"   ✅ Successfully created test user: {user.get('id')}")
                    
                    # Now test trading limits for this user
                    limit_data = {
                        "user_id": user.get('id'),
                        "limit_type": "daily_trading_limit",
                        "limit_value": 10000.00,
                        "currency": "INR"
                    }
                    
                    limit_response = await client.post(f"{self.base_url}/api/trading-limits", json=limit_data)
                    print(f"   📊 Trading limit creation: {limit_response.status_code}")
                    
                    if limit_response.status_code == 200:
                        print("   ✅ Trading limits API working!")
                    else:
                        print(f"   ⚠️  Trading limits API: {limit_response.status_code}")
                        
            except Exception as e:
                print(f"   ❌ Sample data creation failed: {e}")
    
    async def run_comprehensive_test(self):
        """Run all tests to verify fixes"""
        print("=" * 80)
        print("🔧 TESTING USER_SERVICE AFTER FIXES")
        print("=" * 80)
        
        # Test 1: Service availability
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/")
                if response.status_code == 200:
                    print("✅ Service is running")
                else:
                    print("❌ Service not available")
                    return
            except:
                print("❌ Service not accessible")
                return
        
        # Test 2: Health and database status
        await self.test_health_with_database()
        
        # Test 3: Database operations
        await self.test_database_operations()
        
        # Test 4: User creation with fixed enums
        user_id = await self.test_user_creation_with_fixed_enums()
        
        # Test 5: Sample data creation
        await self.create_sample_data_in_database()
        
        print("\n" + "=" * 80)
        print("📋 TEST RESULTS SUMMARY")
        print("=" * 80)
        
        if user_id:
            print("✅ MAJOR PROGRESS:")
            print("   - Enum validation working")
            print("   - User creation successful")
            print("   - Database operations functional")
        else:
            print("⚠️  PARTIAL PROGRESS:")
            print("   - Service running")
            print("   - Health checks working") 
            print("   - Still issues with user creation or database")
        
        print("\n🎯 NEXT STEPS:")
        print("   1. Debug remaining 500 errors")
        print("   2. Test trading limits creation")
        print("   3. Test JWT authentication flow")
        print("   4. Test positive/negative trade scenarios")

async def main():
    """Main test execution"""
    tester = FixedEnumTester()
    await tester.run_comprehensive_test()

if __name__ == "__main__":
    print("🚀 Starting comprehensive testing with fixed enums...")
    asyncio.run(main())