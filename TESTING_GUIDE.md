# User Service - End-to-End Testing Guide

## Overview

This guide provides comprehensive testing strategies for the user_service, including unit tests, integration tests, load tests, and end-to-end testing scenarios.

## Quick Start

### 1. Run Quick Test (Service Running)
```bash
# If service is already running on port 8002
cd /home/stocksadmin/stocksblitz/user_service
python test_runner.py quick
```

### 2. Run Full Test Suite (Automated Service Start)
```bash
# Automatically starts service, runs tests, stops service
cd /home/stocksadmin/stocksblitz/user_service
python test_runner.py
```

### 3. Run Specific Test Categories
```bash
# Trading limits integration tests
python -m pytest tests/test_trading_limits_integration.py -v

# Load testing
python tests/test_load.py

# End-to-end tests
python tests/test_end_to_end.py
```

## Test Categories

### 🏥 Health Check Tests
Tests basic service availability and health endpoints:
- `/health` - Basic health status
- `/health/detailed` - Detailed service discovery info
- `/health/integrations` - Service integration status

**Expected Results:**
- Health endpoints return 200 or 503 (degraded but functional)
- Response times under 1 second
- Proper JSON structure with status information

### 💰 Trading Limits API Tests
Comprehensive testing of the trading limits functionality:

#### Limit Creation Tests
```bash
POST /api/trading-limits
```
Test scenarios:
- Daily trading limits (₹50,000)
- Single trade limits (₹10,000)
- Order count limits (20 orders/day)
- Instrument restrictions (whitelists/blacklists)
- Trading hours restrictions (9:15-15:30)

#### Limit Validation Tests
```bash
POST /api/trading-limits/validate
```
Test scenarios:
- Small trades (should pass)
- Large trades (may hit limits)
- Restricted instruments (should block)
- After-hours trading (should check time restrictions)

#### Bulk Operations Tests
```bash
POST /api/trading-limits/bulk-create
```
Test creating multiple limits simultaneously for multiple users.

### 🔐 Authentication & Authorization Tests
Tests security and access control:
- Unauthenticated requests (expect 401)
- Invalid tokens (expect 401)
- Insufficient permissions (expect 403)
- Valid authenticated requests

### 🚨 Error Handling Tests
Tests robustness and error responses:
- Invalid endpoints (404)
- Malformed JSON (400/422)
- Invalid parameters (422)
- Service unavailable scenarios

### ⚡ Performance Tests
Tests system performance and scalability:

#### Load Testing
- Concurrent requests (10-50 simultaneous)
- Gradual load increase to find breaking points
- Multiple endpoint stress testing

#### Endurance Testing
- Sustained load over time (60+ seconds)
- Memory leak detection
- Response time degradation monitoring

## Test Scenarios

### Scenario 1: Conservative Trader Setup
```json
{
  "daily_limit": 25000.00,
  "single_trade_limit": 5000.00,
  "order_count": 10,
  "allowed_instruments": "NIFTY50_STOCKS",
  "trading_hours": "09:15-15:30"
}
```

### Scenario 2: Active Day Trader Setup
```json
{
  "daily_limit": 100000.00,
  "single_trade_limit": 20000.00,
  "order_count": 50,
  "enforcement": "soft_limit"
}
```

### Scenario 3: Algorithm Trading Setup
```json
{
  "daily_limit": 500000.00,
  "order_count": 200,
  "max_positions": 20,
  "leverage_limit": 5
}
```

## Expected Behaviors

### ✅ Success Cases
1. **Service Startup**: Service starts within 10 seconds
2. **Health Checks**: All health endpoints respond successfully
3. **Authentication**: Proper 401 responses for missing tokens
4. **Validation**: Trading limits validate correctly
5. **Error Handling**: Graceful error responses with proper HTTP codes

### ⚠️ Expected Warnings
1. **Authentication Required**: Most endpoints require valid JWT tokens
2. **Service Dependencies**: Some integrations may be unavailable in test environment
3. **Database Connections**: May use mock data if database unavailable
4. **External Services**: Trade service communication may fail in isolated testing

### ❌ Failure Indicators
1. **Service Won't Start**: Check dependencies and ports
2. **All Requests Fail**: Network connectivity issues
3. **High Response Times**: Performance problems or resource constraints
4. **Memory Leaks**: Increasing memory usage over time

## Detailed Test Execution

### Manual Testing Steps

#### 1. Basic Connectivity
```bash
curl http://localhost:8002/
# Expected: {"message": "Welcome to User Service", "service": "user_service", "status": "operational"}
```

#### 2. Health Checks
```bash
curl http://localhost:8002/health
# Expected: JSON with overall_status and service details

curl http://localhost:8002/health/detailed
# Expected: Detailed service discovery information

curl http://localhost:8002/health/integrations
# Expected: Integration status for alerting, service clients, etc.
```

#### 3. Trading Limits (Requires Authentication)
```bash
# Create limit (expect 401 without auth)
curl -X POST http://localhost:8002/api/trading-limits \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "trading_account_id": 1, "limit_type": "daily_trading_limit", "limit_value": 50000.00}'

# Validate action (expect 401 without auth)
curl -X POST "http://localhost:8002/api/trading-limits/validate?trading_account_id=1" \
  -H "Content-Type: application/json" \
  -d '{"action_type": "place_order", "instrument": "RELIANCE", "quantity": 100, "price": 2500.00, "trade_value": 250000.00}'
```

### Automated Testing with Python

#### Run Complete Test Suite
```python
from test_runner import UserServiceTestRunner
import asyncio

async def run_tests():
    runner = UserServiceTestRunner()
    success = await runner.run_full_test_suite()
    return success

# Run tests
success = asyncio.run(run_tests())
```

#### Run Specific Tests
```python
# Trading limits integration
from tests.test_trading_limits_integration import run_trading_limits_integration_test
asyncio.run(run_trading_limits_integration_test())

# Load testing
from tests.test_load import run_load_tests
asyncio.run(run_load_tests())
```

## Performance Benchmarks

### Target Response Times
- Health checks: < 100ms
- Trading limit validation: < 500ms
- Limit creation: < 1000ms
- Bulk operations: < 5000ms

### Target Throughput
- Health endpoint: 100+ req/s
- Trading operations: 20+ req/s
- Concurrent users: 50+ simultaneous

### Resource Usage
- Memory: < 512MB under normal load
- CPU: < 50% under normal load
- Database connections: < 20 concurrent

## Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check if port is in use
lsof -i :8002

# Check dependencies
pip install -r requirements.txt

# Check configuration
python -c "from app.core.config import settings; print(settings)"
```

#### Database Connection Issues
```bash
# Check database connectivity
python -c "from shared_architecture.db.session import sync_engine; print(sync_engine.url)"

# Test database connection
python -c "from sqlalchemy import text; from shared_architecture.db.session import sync_engine; print(sync_engine.execute(text('SELECT 1')).scalar())"
```

#### Authentication Failures
```bash
# Check Keycloak configuration
python -c "from app.core.config import settings; print(f'Keycloak: {settings.keycloak_url}')"

# Verify JWT settings
python -c "from shared_architecture.auth.jwt_manager import get_jwt_manager; print('JWT manager available')"
```

### Debug Mode Testing
```bash
# Run with debug logging
export LOG_LEVEL=DEBUG
python test_runner.py

# Run single test with verbose output
python -m pytest tests/test_end_to_end.py::test_health_endpoints -v -s
```

## Integration with CI/CD

### GitHub Actions Integration
```yaml
name: User Service Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.10
    - name: Install dependencies
      run: pip install -r requirements.txt
    - name: Run tests
      run: python test_runner.py
```

### Local Development Workflow
```bash
# 1. Start development server
uvicorn app.main:app --reload --port 8002

# 2. In another terminal, run quick tests
python test_runner.py quick

# 3. Run specific test during development
python -m pytest tests/test_trading_limits_integration.py::test_limit_creation_scenarios -v

# 4. Run load test to check performance impact
python tests/test_load.py
```

## Monitoring and Alerting

### Test Result Monitoring
- Track test success rates over time
- Monitor response time trends
- Alert on test failures in CI/CD
- Generate test coverage reports

### Production Readiness Checklist
- [ ] All health checks pass
- [ ] Authentication works correctly
- [ ] Trading limits validate properly
- [ ] Error handling is graceful
- [ ] Performance meets benchmarks
- [ ] Load testing shows acceptable limits
- [ ] Integration with external services works

This comprehensive testing strategy ensures the user_service is robust, performant, and ready for production deployment.