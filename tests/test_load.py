# tests/test_load.py

import asyncio
import httpx
import time
import statistics
from typing import List, Dict, Any
from datetime import datetime
import json

class LoadTester:
    """Simple load testing utility for user_service"""
    
    def __init__(self, base_url: str = "http://localhost:8002"):
        self.base_url = base_url
        self.results: List[Dict[str, Any]] = []
        
    async def single_request(self, endpoint: str, method: str = "GET", data: Dict = None) -> Dict[str, Any]:
        """Make a single request and measure performance"""
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=30.0) as client:
                if method.upper() == "GET":
                    response = await client.get(endpoint)
                elif method.upper() == "POST":
                    response = await client.post(endpoint, json=data)
                else:
                    raise ValueError(f"Unsupported method: {method}")
                
                duration = (time.time() - start_time) * 1000  # Convert to milliseconds
                
                return {
                    "endpoint": endpoint,
                    "method": method,
                    "status_code": response.status_code,
                    "duration_ms": duration,
                    "success": 200 <= response.status_code < 400,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            return {
                "endpoint": endpoint,
                "method": method,
                "status_code": 0,
                "duration_ms": duration,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def concurrent_requests(self, endpoint: str, num_requests: int, method: str = "GET", data: Dict = None) -> List[Dict[str, Any]]:
        """Make multiple concurrent requests"""
        print(f"🚀 Making {num_requests} concurrent {method} requests to {endpoint}")
        
        start_time = time.time()
        
        # Create tasks for concurrent execution
        tasks = [
            self.single_request(endpoint, method, data)
            for _ in range(num_requests)
        ]
        
        # Execute all requests concurrently
        results = await asyncio.gather(*tasks)
        
        total_duration = time.time() - start_time
        
        # Calculate statistics
        successful_requests = [r for r in results if r["success"]]
        failed_requests = [r for r in results if not r["success"]]
        
        if successful_requests:
            durations = [r["duration_ms"] for r in successful_requests]
            avg_duration = statistics.mean(durations)
            median_duration = statistics.median(durations)
            min_duration = min(durations)
            max_duration = max(durations)
        else:
            avg_duration = median_duration = min_duration = max_duration = 0
        
        # Print results
        print(f"📊 Load Test Results for {endpoint}:")
        print(f"   Total requests: {num_requests}")
        print(f"   Successful: {len(successful_requests)} ({len(successful_requests)/num_requests*100:.1f}%)")
        print(f"   Failed: {len(failed_requests)} ({len(failed_requests)/num_requests*100:.1f}%)")
        print(f"   Total time: {total_duration:.2f}s")
        print(f"   Requests/sec: {num_requests/total_duration:.2f}")
        print(f"   Response times (ms):")
        print(f"     Average: {avg_duration:.2f}")
        print(f"     Median: {median_duration:.2f}")
        print(f"     Min: {min_duration:.2f}")
        print(f"     Max: {max_duration:.2f}")
        
        if failed_requests:
            print(f"   ❌ Failure details:")
            for failure in failed_requests[:3]:  # Show first 3 failures
                error = failure.get("error", f"HTTP {failure['status_code']}")
                print(f"     - {error}")
        
        return results
    
    async def gradual_load_test(self, endpoint: str, max_concurrent: int = 50, step: int = 10):
        """Gradually increase load to find breaking point"""
        print(f"\n🎯 Gradual Load Test for {endpoint}")
        print(f"   Max concurrent: {max_concurrent}, Step: {step}")
        print("=" * 50)
        
        for concurrent in range(step, max_concurrent + 1, step):
            print(f"\n📈 Testing with {concurrent} concurrent requests...")
            
            results = await self.concurrent_requests(endpoint, concurrent)
            successful = sum(1 for r in results if r["success"])
            success_rate = successful / concurrent * 100
            
            if success_rate < 95:  # Less than 95% success rate
                print(f"⚠️  Success rate dropped to {success_rate:.1f}% at {concurrent} concurrent requests")
                if success_rate < 80:  # Less than 80% success rate
                    print(f"🔴 Breaking point reached at {concurrent} concurrent requests")
                    break
            else:
                print(f"✅ {success_rate:.1f}% success rate maintained")
            
            # Wait a bit between load tests
            await asyncio.sleep(2)
    
    async def stress_test_endpoints(self):
        """Test multiple endpoints under load"""
        print("\n🔥 Stress Testing Multiple Endpoints")
        print("=" * 50)
        
        test_scenarios = [
            {
                "name": "Health Check",
                "endpoint": "/health",
                "method": "GET",
                "concurrent": 20,
                "expected": "Should handle high load for health checks"
            },
            {
                "name": "Root Endpoint",
                "endpoint": "/",
                "method": "GET", 
                "concurrent": 15,
                "expected": "Should be lightweight and fast"
            },
            {
                "name": "Trading Limits List",
                "endpoint": "/api/trading-limits",
                "method": "GET",
                "concurrent": 10,
                "expected": "May require authentication, expect 401s"
            },
            {
                "name": "Detailed Health",
                "endpoint": "/health/detailed",
                "method": "GET",
                "concurrent": 5,
                "expected": "More complex endpoint, lower concurrency"
            }
        ]
        
        for scenario in test_scenarios:
            print(f"\n🎯 {scenario['name']}")
            print(f"   Expected: {scenario['expected']}")
            
            results = await self.concurrent_requests(
                scenario["endpoint"],
                scenario["concurrent"],
                scenario["method"]
            )
            
            # Store results for later analysis
            self.results.extend(results)
    
    async def endurance_test(self, endpoint: str = "/health", duration_seconds: int = 60, requests_per_second: int = 5):
        """Run endurance test for specified duration"""
        print(f"\n⏰ Endurance Test: {endpoint} for {duration_seconds}s at {requests_per_second} req/s")
        print("=" * 50)
        
        start_time = time.time()
        request_count = 0
        interval = 1.0 / requests_per_second
        
        while time.time() - start_time < duration_seconds:
            request_start = time.time()
            
            result = await self.single_request(endpoint)
            request_count += 1
            
            if request_count % (requests_per_second * 10) == 0:  # Every 10 seconds
                elapsed = time.time() - start_time
                print(f"   {elapsed:.0f}s: {request_count} requests, last: {result['status_code']} ({result['duration_ms']:.1f}ms)")
            
            # Wait for next request
            elapsed = time.time() - request_start
            sleep_time = max(0, interval - elapsed)
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
        
        total_time = time.time() - start_time
        actual_rps = request_count / total_time
        
        print(f"✅ Endurance test completed:")
        print(f"   Duration: {total_time:.1f}s")
        print(f"   Total requests: {request_count}")
        print(f"   Actual rate: {actual_rps:.1f} req/s")
    
    def generate_report(self):
        """Generate a summary report of all tests"""
        if not self.results:
            print("No test results to report")
            return
        
        print("\n📋 Load Test Summary Report")
        print("=" * 50)
        
        total_requests = len(self.results)
        successful_requests = [r for r in self.results if r["success"]]
        failed_requests = [r for r in self.results if not r["success"]]
        
        print(f"Total requests made: {total_requests}")
        print(f"Successful: {len(successful_requests)} ({len(successful_requests)/total_requests*100:.1f}%)")
        print(f"Failed: {len(failed_requests)} ({len(failed_requests)/total_requests*100:.1f}%)")
        
        if successful_requests:
            durations = [r["duration_ms"] for r in successful_requests]
            print(f"\nResponse time statistics (ms):")
            print(f"  Average: {statistics.mean(durations):.2f}")
            print(f"  Median: {statistics.median(durations):.2f}")
            print(f"  Min: {min(durations):.2f}")
            print(f"  Max: {max(durations):.2f}")
            print(f"  95th percentile: {sorted(durations)[int(0.95 * len(durations))]:.2f}")
        
        # Endpoint breakdown
        endpoints = {}
        for result in self.results:
            endpoint = result["endpoint"]
            if endpoint not in endpoints:
                endpoints[endpoint] = {"total": 0, "success": 0, "durations": []}
            
            endpoints[endpoint]["total"] += 1
            if result["success"]:
                endpoints[endpoint]["success"] += 1
                endpoints[endpoint]["durations"].append(result["duration_ms"])
        
        print(f"\nEndpoint breakdown:")
        for endpoint, stats in endpoints.items():
            success_rate = stats["success"] / stats["total"] * 100
            avg_duration = statistics.mean(stats["durations"]) if stats["durations"] else 0
            print(f"  {endpoint}: {success_rate:.1f}% success, {avg_duration:.1f}ms avg")

async def run_load_tests():
    """Run comprehensive load tests"""
    tester = LoadTester()
    
    print("🔥 Starting Load Tests for user_service")
    print("=" * 60)
    
    try:
        # Basic concurrent load test
        await tester.stress_test_endpoints()
        
        # Gradual load test for health endpoint
        await tester.gradual_load_test("/health", max_concurrent=30, step=5)
        
        # Short endurance test
        await tester.endurance_test("/health", duration_seconds=30, requests_per_second=3)
        
        # Generate final report
        tester.generate_report()
        
        print(f"\n🎉 Load testing completed!")
        
    except Exception as e:
        print(f"\n❌ Load testing failed: {e}")

if __name__ == "__main__":
    asyncio.run(run_load_tests())