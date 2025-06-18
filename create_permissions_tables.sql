-- Create comprehensive permissions and restrictions system for user_service
-- This extends the existing user_service with advanced access control

-- 1. User Permissions Table (Core permissions engine)
CREATE TABLE IF NOT EXISTS tradingdb.user_permissions (
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
    
    -- Prevent duplicate permissions (allow updates via revoke/re-grant)
    UNIQUE(grantor_user_id, grantee_user_id, permission_type, resource_type, action_type, scope_type)
);

-- 2. Data Sharing Templates (Predefined sharing configurations)
CREATE TABLE IF NOT EXISTS tradingdb.data_sharing_templates (
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
    
    CONSTRAINT fk_data_sharing_templates_owner FOREIGN KEY (owner_user_id) REFERENCES tradingdb.users(id),
    UNIQUE(owner_user_id, template_name)
);

-- 3. Trading Restrictions (Advanced trading controls)
CREATE TABLE IF NOT EXISTS tradingdb.trading_restrictions (
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

-- 4. Permission Audit Log (Track all permission changes)
CREATE TABLE IF NOT EXISTS tradingdb.permission_audit_log (
    id SERIAL PRIMARY KEY,
    action_type VARCHAR(50) NOT NULL,              -- 'GRANT', 'DENY', 'REVOKE', 'MODIFY'
    permission_id INTEGER,                         -- Reference to user_permissions or trading_restrictions
    table_name VARCHAR(50) NOT NULL,               -- Which table was affected
    
    -- Who did what
    actor_user_id INTEGER NOT NULL,                -- User who made the change
    target_user_id INTEGER NOT NULL,               -- User affected by the change
    
    -- What changed
    old_values JSONB,                              -- Previous state
    new_values JSONB,                              -- New state
    change_reason TEXT,                            -- Why the change was made
    
    -- When and where
    action_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_agent TEXT,
    
    CONSTRAINT fk_permission_audit_actor FOREIGN KEY (actor_user_id) REFERENCES tradingdb.users(id),
    CONSTRAINT fk_permission_audit_target FOREIGN KEY (target_user_id) REFERENCES tradingdb.users(id)
);

-- 5. Permission Cache (For performance optimization)
CREATE TABLE IF NOT EXISTS tradingdb.permission_cache (
    id SERIAL PRIMARY KEY,
    cache_key VARCHAR(255) NOT NULL UNIQUE,        -- Hash of permission query
    user_id INTEGER NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    instrument_key VARCHAR(100),
    
    -- Cached result
    permission_allowed BOOLEAN NOT NULL,
    permission_reason VARCHAR(100) NOT NULL,
    priority_level INTEGER DEFAULT 1,
    
    -- Cache metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    access_count INTEGER DEFAULT 1,
    
    CONSTRAINT fk_permission_cache_user FOREIGN KEY (user_id) REFERENCES tradingdb.users(id)
);

-- 6. Create indexes for optimal performance
CREATE INDEX IF NOT EXISTS idx_user_permissions_grantor ON tradingdb.user_permissions(grantor_user_id);
CREATE INDEX IF NOT EXISTS idx_user_permissions_grantee ON tradingdb.user_permissions(grantee_user_id);
CREATE INDEX IF NOT EXISTS idx_user_permissions_type_resource ON tradingdb.user_permissions(permission_type, resource_type);
CREATE INDEX IF NOT EXISTS idx_user_permissions_active ON tradingdb.user_permissions(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_user_permissions_expires ON tradingdb.user_permissions(expires_at) WHERE expires_at IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_trading_restrictions_user ON tradingdb.trading_restrictions(user_id);
CREATE INDEX IF NOT EXISTS idx_trading_restrictions_restrictor ON tradingdb.trading_restrictions(restrictor_user_id);
CREATE INDEX IF NOT EXISTS idx_trading_restrictions_type ON tradingdb.trading_restrictions(restriction_type);
CREATE INDEX IF NOT EXISTS idx_trading_restrictions_priority ON tradingdb.trading_restrictions(priority_level DESC);
CREATE INDEX IF NOT EXISTS idx_trading_restrictions_active ON tradingdb.trading_restrictions(is_active) WHERE is_active = true;

CREATE INDEX IF NOT EXISTS idx_permission_audit_actor ON tradingdb.permission_audit_log(actor_user_id);
CREATE INDEX IF NOT EXISTS idx_permission_audit_target ON tradingdb.permission_audit_log(target_user_id);
CREATE INDEX IF NOT EXISTS idx_permission_audit_timestamp ON tradingdb.permission_audit_log(action_timestamp);

CREATE INDEX IF NOT EXISTS idx_permission_cache_key ON tradingdb.permission_cache(cache_key);
CREATE INDEX IF NOT EXISTS idx_permission_cache_user_resource ON tradingdb.permission_cache(user_id, resource_type, action_type);
CREATE INDEX IF NOT EXISTS idx_permission_cache_expires ON tradingdb.permission_cache(expires_at);

-- 7. Insert sample permission templates
INSERT INTO tradingdb.data_sharing_templates (template_name, description, owner_user_id, default_permissions, restricted_users) VALUES
('Conservative Sharing', 'Share basic data with close contacts only', 1, 
 '{"positions": {"default": "deny", "allowed_actions": ["view"]}, "holdings": {"default": "allow"}}',
 '{"excluded_user_ids": [], "allowed_user_ids": [2, 3]}'),
 
('Open Sharing', 'Share most data with all users except blacklisted', 1,
 '{"positions": {"default": "allow"}, "holdings": {"default": "allow"}, "orders": {"default": "allow"}}',
 '{"excluded_user_ids": [4, 5], "allowed_user_ids": []}'),
 
('Trading Team', 'Full sharing for trading team members', 1,
 '{"positions": {"default": "allow"}, "holdings": {"default": "allow"}, "orders": {"default": "allow"}, "strategies": {"default": "allow"}}',
 '{"excluded_user_ids": [], "allowed_user_ids": [10, 11, 12]}')
ON CONFLICT (owner_user_id, template_name) DO NOTHING;

-- 8. Insert sample permissions (for testing)
-- Sample: User 1 shares positions with all except users 2 and 3
INSERT INTO tradingdb.user_permissions (
    grantor_user_id, grantee_user_id, permission_type, resource_type, action_type, 
    permission_level, scope_type, granted_by, notes
) VALUES
-- Allow all users to view user 1's positions
(1, 0, 'data_sharing', 'positions', 'view', 'ALLOW', 'ALL', 1, 'Default: Share positions with everyone'),

-- Explicitly deny users 2 and 3
(1, 2, 'data_sharing', 'positions', 'view', 'DENY', 'SPECIFIC', 1, 'Privacy: Do not share with user 2'),
(1, 3, 'data_sharing', 'positions', 'view', 'DENY', 'SPECIFIC', 1, 'Privacy: Do not share with user 3'),

-- Trading permissions: User 2 can create positions but not exit HDFC
(1, 2, 'trading_action', 'positions', 'create', 'ALLOW', 'ALL', 1, 'Allow user 2 to create positions'),
(1, 2, 'trading_action', 'positions', 'modify', 'ALLOW', 'ALL', 1, 'Allow user 2 to modify positions'),
(1, 2, 'trading_action', 'positions', 'exit', 'DENY', 'SPECIFIC', 1, 'Restrict exit for sensitive instruments',
 '{"blacklist": ["NSE:HDFCBANK", "NSE:RELIANCE"]}')

ON CONFLICT (grantor_user_id, grantee_user_id, permission_type, resource_type, action_type, scope_type) 
DO UPDATE SET 
    permission_level = EXCLUDED.permission_level,
    instrument_filters = EXCLUDED.instrument_filters,
    notes = EXCLUDED.notes,
    granted_at = CURRENT_TIMESTAMP;

-- 9. Insert sample trading restrictions
INSERT INTO tradingdb.trading_restrictions (
    user_id, restrictor_user_id, restriction_type, action_type, 
    instrument_keys, priority_level, enforcement_type, notes
) VALUES
-- Restrict user 2 from trading specific instruments
(2, 1, 'instrument_blacklist', 'all', 
 '["NSE:YESBANK", "NSE:VODAFONE"]', 10, 'HARD', 
 'High-risk instruments banned'),

-- Restrict user 3 from large positions
(3, 1, 'value_limit', 'create',
 '[]', 5, 'SOFT',
 'Position size limits for junior trader'),

-- Time-based restrictions for user 4
(4, 1, 'time_restriction', 'all',
 '[]', 7, 'HARD',
 'After-hours trading prohibited')
 
ON CONFLICT DO NOTHING;

-- 10. Grant permissions to tradmin
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA tradingdb TO tradmin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA tradingdb TO tradmin;

-- Verify tables were created
SELECT 'Permissions tables created successfully!' as result;
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'tradingdb' AND table_name LIKE '%permission%' OR table_name LIKE '%restriction%' 
ORDER BY table_name;