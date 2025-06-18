# 🔐 User Service Permissions & Restrictions Design

## 📋 **OVERVIEW**

Design a comprehensive permissions system that allows users to:
1. **Data Sharing Control**: Share positions, holdings, margins, orders, strategies with specific users
2. **Trading Restrictions**: Control what actions users can perform on specific instruments
3. **Granular Permissions**: Fine-grained control over create/modify/exit operations
4. **Conflict Resolution**: Clear hierarchy when grants and restrictions conflict

## 🏗️ **ARCHITECTURE DESIGN**

### **Permission Types**
1. **Data Sharing Permissions** - Who can see my data
2. **Trading Action Permissions** - What trading actions users can perform
3. **Instrument-Level Restrictions** - Specific instrument controls
4. **Time-Based Permissions** - Temporary access controls

### **Permission Hierarchy (Conflict Resolution)**
```
1. EXPLICIT_DENY (Highest Priority)
2. EXPLICIT_GRANT 
3. ROLE_BASED_DEFAULT
4. SYSTEM_DEFAULT (Lowest Priority)
```

## 📊 **DATABASE SCHEMA DESIGN**

### **1. User Permissions Table**
```sql
CREATE TABLE tradingdb.user_permissions (
    id SERIAL PRIMARY KEY,
    grantor_user_id INTEGER NOT NULL,              -- User granting permission
    grantee_user_id INTEGER NOT NULL,              -- User receiving permission
    permission_type VARCHAR(50) NOT NULL,          -- 'data_sharing', 'trading_action'
    resource_type VARCHAR(50) NOT NULL,            -- 'positions', 'holdings', 'orders', 'strategies', 'margins'
    action_type VARCHAR(50),                       -- 'view', 'create', 'modify', 'exit', 'all'
    permission_level VARCHAR(20) DEFAULT 'ALLOW', -- 'ALLOW', 'DENY'
    scope_type VARCHAR(20) DEFAULT 'ALL',          -- 'ALL', 'SPECIFIC', 'EXCLUDE'
    
    -- JSON fields for flexible configuration
    instrument_filters JSONB,                      -- Specific instruments to include/exclude
    additional_conditions JSONB,                   -- Time restrictions, value limits, etc.
    
    -- Metadata
    granted_by INTEGER NOT NULL,
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    revoked_at TIMESTAMP WITH TIME ZONE,
    revoked_by INTEGER,
    notes TEXT,
    
    -- Constraints
    CONSTRAINT fk_user_permissions_grantor FOREIGN KEY (grantor_user_id) REFERENCES tradingdb.users(id),
    CONSTRAINT fk_user_permissions_grantee FOREIGN KEY (grantee_user_id) REFERENCES tradingdb.users(id),
    CONSTRAINT fk_user_permissions_granted_by FOREIGN KEY (granted_by) REFERENCES tradingdb.users(id),
    CONSTRAINT fk_user_permissions_revoked_by FOREIGN KEY (revoked_by) REFERENCES tradingdb.users(id),
    
    -- Prevent duplicate permissions
    UNIQUE(grantor_user_id, grantee_user_id, permission_type, resource_type, action_type, scope_type)
);
```

### **2. Data Sharing Templates Table**
```sql
CREATE TABLE tradingdb.data_sharing_templates (
    id SERIAL PRIMARY KEY,
    template_name VARCHAR(100) NOT NULL,
    description TEXT,
    owner_user_id INTEGER NOT NULL,
    
    -- Template configuration
    default_permissions JSONB NOT NULL,            -- Default sharing rules
    restricted_users JSONB,                        -- Users explicitly denied
    allowed_users JSONB,                           -- Users explicitly allowed
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    
    CONSTRAINT fk_data_sharing_templates_owner FOREIGN KEY (owner_user_id) REFERENCES tradingdb.users(id)
);
```

### **3. Trading Restrictions Table**
```sql
CREATE TABLE tradingdb.trading_restrictions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,                      -- User being restricted
    restrictor_user_id INTEGER NOT NULL,           -- User applying restriction
    restriction_type VARCHAR(50) NOT NULL,         -- 'instrument_blacklist', 'action_limit', 'value_limit'
    action_type VARCHAR(50) NOT NULL,              -- 'create', 'modify', 'exit', 'all'
    
    -- Restriction details
    instrument_keys JSONB,                         -- Specific instruments
    value_limits JSONB,                            -- Max position size, trade value, etc.
    time_restrictions JSONB,                       -- Trading hours, days of week
    
    -- Priority and enforcement
    priority_level INTEGER DEFAULT 1,              -- Higher number = higher priority
    enforcement_type VARCHAR(20) DEFAULT 'HARD',   -- 'HARD', 'SOFT', 'WARNING'
    
    -- Metadata
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT,
    
    CONSTRAINT fk_trading_restrictions_user FOREIGN KEY (user_id) REFERENCES tradingdb.users(id),
    CONSTRAINT fk_trading_restrictions_restrictor FOREIGN KEY (restrictor_user_id) REFERENCES tradingdb.users(id)
);
```

## 📝 **PERMISSION EXAMPLES**

### **Example 1: Data Sharing - "Share with all except User1 and User2"**
```json
{
  "grantor_user_id": 5,
  "permission_type": "data_sharing",
  "resource_type": "positions",
  "action_type": "view",
  "permission_level": "ALLOW",
  "scope_type": "ALL"
}
```
Plus exclusions:
```json
[
  {
    "grantor_user_id": 5,
    "grantee_user_id": 1,
    "permission_type": "data_sharing", 
    "resource_type": "positions",
    "action_type": "view",
    "permission_level": "DENY",
    "scope_type": "SPECIFIC"
  },
  {
    "grantor_user_id": 5,
    "grantee_user_id": 2,
    "permission_type": "data_sharing",
    "resource_type": "positions", 
    "action_type": "view",
    "permission_level": "DENY",
    "scope_type": "SPECIFIC"
  }
]
```

### **Example 2: Trading Restrictions - "User1 can create/modify/exit except RELIANCE and TCS"**
```json
{
  "grantor_user_id": 5,
  "grantee_user_id": 1,
  "permission_type": "trading_action",
  "resource_type": "positions",
  "action_type": "all",
  "permission_level": "ALLOW",
  "scope_type": "ALL"
}
```
Plus restrictions:
```json
{
  "user_id": 1,
  "restrictor_user_id": 5,
  "restriction_type": "instrument_blacklist",
  "action_type": "all",
  "instrument_keys": ["NSE:RELIANCE", "NSE:TCS"],
  "enforcement_type": "HARD",
  "priority_level": 10
}
```

### **Example 3: Complex Permissions - "User1 can only create positions for NIFTY50, but not exit HDFC"**
```json
[
  {
    "grantor_user_id": 5,
    "grantee_user_id": 1,
    "permission_type": "trading_action",
    "resource_type": "positions",
    "action_type": "create",
    "permission_level": "ALLOW",
    "scope_type": "SPECIFIC",
    "instrument_filters": {"whitelist": ["NSE:NIFTY*", "NSE:BANKNIFTY*"]}
  },
  {
    "grantor_user_id": 5,
    "grantee_user_id": 1,
    "permission_type": "trading_action",
    "resource_type": "positions", 
    "action_type": "exit",
    "permission_level": "DENY",
    "scope_type": "SPECIFIC",
    "instrument_filters": {"blacklist": ["NSE:HDFCBANK"]}
  }
]
```

## 🔧 **CONFLICT RESOLUTION ALGORITHM**

### **Permission Evaluation Order**
1. **Check EXPLICIT_DENY** - If any deny rule matches, access denied
2. **Check EXPLICIT_GRANT** - If any allow rule matches, access granted  
3. **Check ROLE_BASED** - Apply default role permissions
4. **Apply SYSTEM_DEFAULT** - Fall back to system defaults

### **Example Conflict Resolution**
```python
def evaluate_permission(user_id, action, resource, instrument_key):
    # 1. Check explicit denials (highest priority)
    denials = get_explicit_denials(user_id, action, resource, instrument_key)
    if denials:
        return PermissionResult(allowed=False, reason="EXPLICIT_DENY", rule=denials[0])
    
    # 2. Check explicit grants
    grants = get_explicit_grants(user_id, action, resource, instrument_key) 
    if grants:
        return PermissionResult(allowed=True, reason="EXPLICIT_GRANT", rule=grants[0])
    
    # 3. Check role-based permissions
    role_permission = get_role_based_permission(user_id, action, resource)
    if role_permission:
        return PermissionResult(allowed=role_permission.allowed, reason="ROLE_BASED")
    
    # 4. System default (most restrictive)
    return PermissionResult(allowed=False, reason="SYSTEM_DEFAULT")
```

## 🛠️ **API DESIGN**

### **Data Sharing APIs**
```python
# Grant data sharing permission
POST /api/permissions/data-sharing
{
  "grantee_user_id": 1,
  "resource_types": ["positions", "holdings"],
  "scope": "all_except",
  "excluded_users": [2, 3],
  "expires_at": "2025-12-31T23:59:59Z"
}

# Get my data sharing settings
GET /api/permissions/data-sharing/my-settings

# Get users who can see my data
GET /api/permissions/data-sharing/viewers
```

### **Trading Permissions APIs**
```python
# Grant trading permissions
POST /api/permissions/trading
{
  "grantee_user_id": 1,
  "permissions": [
    {
      "action": "create",
      "scope": "whitelist",
      "instruments": ["NSE:RELIANCE", "NSE:TCS"]
    },
    {
      "action": "exit", 
      "scope": "blacklist",
      "instruments": ["NSE:HDFCBANK"]
    }
  ]
}

# Check if user can perform action
GET /api/permissions/trading/check?user_id=1&action=create&instrument=NSE:RELIANCE

# Apply trading restrictions  
POST /api/restrictions/trading
{
  "target_user_id": 1,
  "restrictions": [
    {
      "type": "instrument_blacklist",
      "actions": ["exit"],
      "instruments": ["NSE:HDFCBANK"],
      "enforcement": "HARD"
    }
  ]
}
```

## 📋 **IMPLEMENTATION ROADMAP**

### **Phase 1: Basic Permissions (2-3 hours)**
1. Create database tables and indexes
2. Implement basic permission models
3. Create permission evaluation logic
4. Add basic API endpoints

### **Phase 2: Data Sharing (2-3 hours)**  
1. Implement data sharing templates
2. Create "share with all except X" functionality
3. Add data filtering based on permissions
4. Test with real position/holdings data

### **Phase 3: Trading Restrictions (3-4 hours)**
1. Implement trading action permissions
2. Add instrument-level restrictions
3. Create conflict resolution engine
4. Add validation to trading endpoints

### **Phase 4: Advanced Features (2-3 hours)**
1. Time-based permissions
2. Value-based restrictions
3. Template-based permissions
4. Audit logging and monitoring

## 🔍 **TESTING SCENARIOS**

### **Data Sharing Tests**
```python
# Test 1: Share with all except specific users
user5.share_data("positions", scope="all_except", excluded_users=[1, 2])
assert can_user_view_data(user3, user5, "positions") == True
assert can_user_view_data(user1, user5, "positions") == False

# Test 2: Complex sharing rules
user5.share_data("holdings", scope="specific", allowed_users=[1, 3])
user5.deny_data("holdings", users=[1])  # Override with denial
assert can_user_view_data(user1, user5, "holdings") == False  # Denial wins
assert can_user_view_data(user3, user5, "holdings") == True
```

### **Trading Permission Tests**
```python
# Test 3: Instrument-specific permissions
user5.grant_trading_permission(user1, "create", whitelist=["NSE:RELIANCE"])
user5.deny_trading_permission(user1, "exit", instruments=["NSE:RELIANCE"])

assert can_user_trade(user1, "create", "NSE:RELIANCE") == True
assert can_user_trade(user1, "exit", "NSE:RELIANCE") == False  # Denial wins
assert can_user_trade(user1, "create", "NSE:TCS") == False     # Not in whitelist
```

This design provides a flexible, scalable permissions system that handles complex scenarios while maintaining clear conflict resolution rules. Would you like me to implement any specific part of this design?