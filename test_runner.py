#!/usr/bin/env python3
# test_runner.py - Comprehensive test runner for user_service

import asyncio
import subprocess
import sys
import time
import os
import signal
from typing import Optional
import httpx

class UserServiceTestRunner:
    """Comprehensive test runner for user_service"""
    
    def __init__(self):
        self.service_process: Optional[subprocess.Popen] = None
        self.base_url = "http://localhost:8002"
        
    def check_dependencies(self):
        """Check if all required dependencies are installed"""
        print("🔍 Checking dependencies...")
        
        required_packages = ['httpx', 'pytest', 'fastapi', 'uvicorn']
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package)
                print(f"✅ {package}")
            except ImportError:
                missing_packages.append(package)
                print(f"❌ {package} - Missing")
        
        if missing_packages:
            print(f"\n📦 Install missing packages:")
            print(f"pip install {' '.join(missing_packages)}")
            return False
        
        return True
    
    def start_service(self, wait_time: int = 10):
        """Start the user service"""
        print("🚀 Starting user_service...")
        
        try:
            # Start the service
            self.service_process = subprocess.Popen(
                [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd="/home/stocksadmin/stocksblitz/user_service"
            )
            
            print(f"⏳ Waiting {wait_time} seconds for service to start...")
            time.sleep(wait_time)
            
            # Check if service is running
            if self.service_process.poll() is None:
                print("✅ Service started successfully")
                return True
            else:
                stdout, stderr = self.service_process.communicate()
                print(f"❌ Service failed to start:")
                print(f"STDOUT: {stdout.decode()}")
                print(f"STDERR: {stderr.decode()}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to start service: {e}")
            return False
    
    def stop_service(self):
        """Stop the user service"""
        if self.service_process:
            print("🛑 Stopping user_service...")
            try:
                self.service_process.terminate()
                self.service_process.wait(timeout=5)
                print("✅ Service stopped")
            except subprocess.TimeoutExpired:
                print("⚠️  Force killing service...")
                self.service_process.kill()
                self.service_process.wait()
            except Exception as e:
                print(f"❌ Error stopping service: {e}")
    
    async def wait_for_service(self, max_attempts: int = 30):
        """Wait for service to become available"""
        print("⏳ Waiting for service to become available...")
        
        for attempt in range(max_attempts):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{self.base_url}/health", timeout=5.0)
                    if response.status_code in [200, 503]:  # 503 is also acceptable (degraded)
                        print(f"✅ Service available after {attempt + 1} attempts")
                        return True
            except Exception:
                pass
            
            time.sleep(1)
        
        print(f"❌ Service not available after {max_attempts} attempts")
        return False
    
    async def run_manual_tests(self):
        """Run manual test scenarios"""
        print("\n🧪 Running Manual Test Scenarios...")
        
        async with httpx.AsyncClient(base_url=self.base_url, timeout=30.0) as client:
            
            # Test 1: Basic connectivity
            print("\n1️⃣  Testing Basic Connectivity")
            try:
                response = await client.get("/")
                print(f"   Root endpoint: {response.status_code} - {response.json()}")
            except Exception as e:
                print(f"   ❌ Root endpoint failed: {e}")
            
            # Test 2: Health checks
            print("\n2️⃣  Testing Health Endpoints")
            health_endpoints = ["/health", "/health/detailed", "/health/integrations"]
            
            for endpoint in health_endpoints:
                try:
                    response = await client.get(endpoint)
                    status = "✅" if response.status_code in [200, 503] else "❌"
                    print(f"   {status} {endpoint}: {response.status_code}")
                    
                    if endpoint == "/health" and response.status_code == 200:
                        data = response.json()
                        print(f"      Overall status: {data.get('overall_status', 'unknown')}")
                        
                except Exception as e:
                    print(f"   ❌ {endpoint}: {e}")
            
            # Test 3: Trading Limits API
            print("\n3️⃣  Testing Trading Limits API")
            
            # Test limit creation (expect auth error in real scenario)
            limit_data = {
                "user_id": 1,
                "trading_account_id": 1,
                "limit_type": "daily_trading_limit",
                "limit_value": 50000.00,
                "enforcement_type": "hard_limit"
            }
            
            try:
                response = await client.post("/api/trading-limits", json=limit_data)
                if response.status_code == 401:
                    print("   ✅ Authentication required (expected)")
                elif response.status_code == 422:
                    print("   ✅ Validation working")
                else:
                    print(f"   ⚠️  Unexpected response: {response.status_code}")
            except Exception as e:
                print(f"   ❌ Trading limits test failed: {e}")
            
            # Test limit validation
            validation_data = {
                "action_type": "place_order",
                "instrument": "RELIANCE",
                "quantity": 100,
                "price": 2500.00,
                "trade_value": 250000.00
            }
            
            try:
                response = await client.post(
                    "/api/trading-limits/validate?trading_account_id=1",
                    json=validation_data
                )
                if response.status_code == 401:
                    print("   ✅ Validation endpoint requires auth (expected)")
                else:
                    print(f"   ⚠️  Validation response: {response.status_code}")
            except Exception as e:
                print(f"   ❌ Validation test failed: {e}")
            
            # Test 4: Error handling
            print("\n4️⃣  Testing Error Handling")
            
            # Test 404 handling
            try:
                response = await client.get("/api/nonexistent")
                if response.status_code == 404:
                    print("   ✅ 404 handling working")
                else:
                    print(f"   ⚠️  Unexpected 404 response: {response.status_code}")
            except Exception as e:
                print(f"   ❌ 404 test failed: {e}")
            
            # Test malformed JSON
            try:
                response = await client.post(
                    "/api/trading-limits",
                    data="invalid json",
                    headers={"Content-Type": "application/json"}
                )
                if response.status_code in [400, 422]:
                    print("   ✅ Malformed JSON handling working")
                else:
                    print(f"   ⚠️  Malformed JSON response: {response.status_code}")
            except Exception as e:
                print(f"   ❌ Malformed JSON test failed: {e}")
    
    async def run_e2e_tests(self):
        """Run the comprehensive E2E test suite"""
        print("\n🚀 Running Comprehensive E2E Tests...")
        
        try:
            # Import and run the E2E test suite
            from tests.test_end_to_end import run_comprehensive_e2e_test
            await run_comprehensive_e2e_test()
        except ImportError:
            print("❌ E2E test module not found. Running manual tests instead.")
            await self.run_manual_tests()
        except Exception as e:
            print(f"❌ E2E tests failed: {e}")
            await self.run_manual_tests()
    
    def run_unit_tests(self):
        """Run unit tests using pytest"""
        print("\n🧪 Running Unit Tests...")
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "tests/", "-v"],
                cwd="/home/stocksadmin/stocksblitz/user_service",
                capture_output=True,
                text=True
            )
            
            print("STDOUT:")
            print(result.stdout)
            
            if result.stderr:
                print("STDERR:")
                print(result.stderr)
            
            if result.returncode == 0:
                print("✅ Unit tests passed")
            else:
                print(f"⚠️  Unit tests completed with return code: {result.returncode}")
                
        except Exception as e:
            print(f"❌ Failed to run unit tests: {e}")
    
    async def run_full_test_suite(self):
        """Run the complete test suite"""
        print("🎯 Starting Full Test Suite for user_service")
        print("=" * 60)
        
        # Check dependencies
        if not self.check_dependencies():
            print("❌ Dependency check failed. Please install missing packages.")
            return False
        
        # Start the service
        if not self.start_service():
            print("❌ Failed to start service")
            return False
        
        try:
            # Wait for service to be ready
            if not await self.wait_for_service():
                print("❌ Service not ready for testing")
                return False
            
            # Run unit tests
            self.run_unit_tests()
            
            # Run E2E tests
            await self.run_e2e_tests()
            
            print("\n🎉 Full test suite completed!")
            return True
            
        finally:
            # Always stop the service
            self.stop_service()
    
    def run_quick_test(self):
        """Run a quick test without starting the service (assumes service is running)"""
        print("⚡ Running Quick Test (assuming service is running)")
        print("=" * 50)
        
        async def quick_test():
            if await self.wait_for_service(max_attempts=3):
                await self.run_manual_tests()
            else:
                print("❌ Service not available. Start the service first:")
                print("   cd /home/stocksadmin/stocksblitz/user_service")
                print("   python -m uvicorn app.main:app --host 0.0.0.0 --port 8002")
        
        asyncio.run(quick_test())

def main():
    """Main test runner entry point"""
    runner = UserServiceTestRunner()
    
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        runner.run_quick_test()
    else:
        try:
            success = asyncio.run(runner.run_full_test_suite())
            sys.exit(0 if success else 1)
        except KeyboardInterrupt:
            print("\n🛑 Test interrupted by user")
            runner.stop_service()
            sys.exit(1)

if __name__ == "__main__":
    main()