# User Service - End-to-End Testing Complete Guide

## 🎯 Quick Testing Options

### Option 1: Automated Full Test Suite
```bash
cd /home/stocksadmin/stocksblitz/user_service
python test_runner.py
```
**What it does:**
- ✅ Starts the service automatically
- ✅ Runs comprehensive health checks
- ✅ Tests all API endpoints
- ✅ Performs load testing
- ✅ Stops service automatically
- ✅ Generates detailed report

### Option 2: Manual Service + Quick Tests
```bash
# Terminal 1: Start service
cd /home/stocksadmin/stocksblitz/user_service
python start_service.py

# Terminal 2: Run tests
python test_runner.py quick
```

### Option 3: Specific Test Categories
```bash
# Trading limits integration testing
python tests/test_trading_limits_integration.py

# Load testing only
python tests/test_load.py

# End-to-end scenarios
python tests/test_end_to_end.py
```

## 📊 Test Coverage

### ✅ What We Test

#### 1. **Service Health & Startup**
- Service starts within 10 seconds
- All health endpoints respond correctly
- Integration status is properly reported
- Response times are acceptable

#### 2. **Trading Limits API** (Core Feature)
- **Limit Creation**: 15+ different limit types
  - Daily trading limits (₹50,000)
  - Single trade limits (₹10,000) 
  - Order count limits (20 orders/day)
  - Instrument restrictions (RELIANCE,TCS,INFY)
  - Trading hours (9:15-15:30, weekdays only)
- **Limit Validation**: Real-time trade validation
- **Bulk Operations**: Create multiple limits simultaneously
- **Query Operations**: Filter and paginate limits

#### 3. **Authentication & Security**
- Proper 401 responses for missing authentication
- JWT token validation (when tokens provided)
- Authorization checks for different user roles
- Input validation and sanitization

#### 4. **Error Handling & Resilience**
- 404 handling for invalid endpoints
- 422 handling for malformed requests
- Service degradation scenarios
- Circuit breaker behavior
- Fallback mechanisms

#### 5. **Performance & Load Testing**
- Concurrent request handling (10-50 users)
- Response time benchmarks (< 500ms for critical APIs)
- Memory and CPU usage monitoring
- Breaking point identification
- Endurance testing (sustained load)

## 🧪 Test Scenarios

### Scenario A: Conservative Trader
```json
{
  "profile": "Conservative Individual Trader",
  "limits": {
    "daily_trading_limit": 25000.00,
    "single_trade_limit": 5000.00,
    "daily_order_count": 10,
    "allowed_instruments": "NIFTY50_STOCKS",
    "trading_hours": "09:15-15:30",
    "enforcement": "hard_limit"
  },
  "expected_behavior": "Strict limits prevent over-trading"
}
```

### Scenario B: Active Day Trader
```json
{
  "profile": "Active Day Trader",
  "limits": {
    "daily_trading_limit": 100000.00,
    "single_trade_limit": 20000.00,
    "daily_order_count": 50,
    "enforcement": "soft_limit"
  },
  "expected_behavior": "Warnings but allows higher volume"
}
```

### Scenario C: Algorithm Trading
```json
{
  "profile": "Algorithmic Trading System",
  "limits": {
    "daily_trading_limit": 500000.00,
    "daily_order_count": 200,
    "max_open_positions": 20,
    "single_order_quantity": 1000,
    "enforcement": "advisory"
  },
  "expected_behavior": "High volume with monitoring only"
}
```

## 📈 Performance Benchmarks

### Target Response Times
| Endpoint | Target | Acceptable | Critical |
|----------|--------|------------|----------|
| `/health` | < 50ms | < 200ms | < 500ms |
| `/api/trading-limits/validate` | < 100ms | < 500ms | < 1000ms |
| `/api/trading-limits` (POST) | < 200ms | < 1000ms | < 2000ms |
| `/api/trading-limits` (GET) | < 100ms | < 500ms | < 1000ms |

### Throughput Targets
| Operation | Target | Acceptable | Minimum |
|-----------|--------|------------|---------|
| Health checks | 100 req/s | 50 req/s | 20 req/s |
| Limit validation | 50 req/s | 25 req/s | 10 req/s |
| Concurrent users | 100 users | 50 users | 20 users |

## 🔍 Detailed Test Results

### Expected Output Examples

#### ✅ Successful Health Check
```json
{
  "overall_status": "healthy",
  "service": "user_service",
  "connections": {
    "timescaledb": {"status": "healthy", "response_time": "45ms"},
    "redis": {"status": "healthy", "connections": "5/100"}
  },
  "integrations": {
    "initialized": true,
    "services": {
      "user_service_client": {"initialized": true, "circuit_breaker_state": "CLOSED"},
      "trade_service_client": {"initialized": true, "circuit_breaker_state": "CLOSED"}
    },
    "alerting": {
      "initialized": true, 
      "channels": ["email", "slack", "websocket"],
      "queue_size": 0
    }
  }
}
```

#### ✅ Successful Limit Validation
```json
{
  "allowed": false,
  "violations": [
    {
      "limit_type": "daily_trading_limit",
      "limit_value": 50000.0,
      "current_usage": 30000.0,
      "attempted_value": 25000.0,
      "projected_usage": 55000.0,
      "breach_amount": 5000.0,
      "message": "Daily trading limit of ₹50,000.00 would be exceeded"
    }
  ],
  "warnings": [],
  "actions_required": ["WARNING", "NOTIFY_ADMIN"],
  "override_possible": false
}
```

#### ⚠️ Expected Authentication Responses
```json
{
  "detail": "Not authenticated"
}
```
*Status: 401 - This is expected behavior when testing without proper JWT tokens*

## 🛠️ Troubleshooting Guide

### Common Issues & Solutions

#### Issue: Service Won't Start
```bash
# Check port availability
lsof -i :8002

# Kill existing process if needed
pkill -f "uvicorn.*8002"

# Check dependencies
pip install -r requirements.txt

# Verify Python path
export PYTHONPATH=/home/stocksadmin/stocksblitz:$PYTHONPATH
```

#### Issue: Database Connection Errors
```bash
# Check database status
docker ps | grep postgres
# or
systemctl status postgresql

# Verify database configuration
python -c "from shared_architecture.db.session import sync_engine; print(sync_engine.url)"
```

#### Issue: Test Timeouts
```bash
# Increase timeout for slow systems
export TEST_TIMEOUT=60

# Run tests with verbose output
python test_runner.py quick --verbose
```

#### Issue: Import Errors
```bash
# Ensure proper Python path
cd /home/stocksadmin/stocksblitz/user_service
export PYTHONPATH=/home/stocksadmin/stocksblitz:$PYTHONPATH

# Install missing dependencies
pip install httpx pytest fastapi uvicorn
```

## 📋 Test Execution Checklist

### Pre-Test Setup
- [ ] Navigate to user_service directory
- [ ] Verify Python environment and dependencies
- [ ] Check port 8002 is available
- [ ] Ensure database connectivity (if required)
- [ ] Set up proper environment variables

### Test Execution
- [ ] Run automated test suite OR start service manually
- [ ] Verify all health checks pass
- [ ] Test trading limits API responses
- [ ] Check authentication behavior
- [ ] Validate error handling
- [ ] Monitor performance metrics

### Post-Test Verification
- [ ] Review test results and metrics
- [ ] Check for any error logs
- [ ] Verify service stops cleanly
- [ ] Document any issues or performance concerns

## 🚀 Production Readiness Indicators

### ✅ Ready for Production
- All health checks return 200 or 503 (degraded but functional)
- Trading limits API responds with proper authentication requirements
- Error handling returns appropriate HTTP status codes
- Response times meet performance benchmarks
- Load testing shows acceptable concurrency limits
- No memory leaks during endurance testing

### ⚠️ Needs Investigation
- Slow response times (> 1 second for simple endpoints)
- High error rates (> 5% failures)
- Memory usage continuously increasing
- Service crashes under moderate load
- Database connection issues

### ❌ Not Ready
- Service fails to start
- Health checks consistently fail
- Critical endpoints return 500 errors
- Performance significantly below benchmarks
- Security vulnerabilities detected

## 🔗 Integration Testing

### With Trade Service
```bash
# Test inter-service communication
python tests/test_service_integration.py

# Expected: Circuit breaker behavior when trade service unavailable
# Expected: Proper fallback to emergency limits
```

### With External Dependencies
```bash
# Test Keycloak integration
curl -X POST http://localhost:8002/api/trading-limits \
  -H "Authorization: Bearer <real-jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "limit_type": "daily_trading_limit", "limit_value": 50000}'

# Expected: Proper JWT validation and user context extraction
```

This comprehensive testing framework ensures the user_service is robust, performant, and ready for production deployment with full trading limits functionality.