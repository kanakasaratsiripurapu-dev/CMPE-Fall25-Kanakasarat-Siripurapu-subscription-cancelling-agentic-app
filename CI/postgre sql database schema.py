-- PostgreSQL Schema for SubScout

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    gmail_refresh_token TEXT NOT NULL, -- Encrypted with user-specific key
    gmail_token_encrypted_at TIMESTAMP,
    profile_picture_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP,
    last_scan_at TIMESTAMP,
    subscription_count INTEGER DEFAULT 0,
    total_monthly_spend DECIMAL(10, 2) DEFAULT 0.00,
    is_active BOOLEAN DEFAULT TRUE,
    deleted_at TIMESTAMP NULL  -- Soft delete
);

-- Indexes for users
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_active ON users(is_active) WHERE is_active = TRUE;

-- Email import sessions (tracks scanning progress)
CREATE TABLE email_import_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(50) DEFAULT 'running', -- running, completed, failed, cancelled
    total_emails_found INTEGER DEFAULT 0,
    emails_processed INTEGER DEFAULT 0,
    subscriptions_found INTEGER DEFAULT 0,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    scan_params JSONB, -- Store search filters, date range, etc.
    CONSTRAINT fk_session_user FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Indexes for sessions
CREATE INDEX idx_sessions_user ON email_import_sessions(user_id);
CREATE INDEX idx_sessions_status ON email_import_sessions(status);
CREATE INDEX idx_sessions_started ON email_import_sessions(started_at DESC);

-- Subscriptions table (main data)
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Core subscription data
    service_name VARCHAR(255) NOT NULL,
    service_domain VARCHAR(255), -- e.g., netflix.com
    service_logo_url TEXT,
    service_category VARCHAR(100), -- Streaming, SaaS, News, Fitness, etc.
    
    -- Pricing
    price DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    billing_period VARCHAR(50) NOT NULL, -- monthly, annually, quarterly, one-time
    
    -- Dates
    first_detected_date DATE,
    next_renewal_date DATE,
    last_verified_date TIMESTAMP,
    
    -- Links & metadata
    unsubscribe_link TEXT,
    manage_account_link TEXT,
    payment_method_last4 VARCHAR(4),
    subscription_tier VARCHAR(100), -- Premium, Pro, Basic, etc.
    
    -- Status
    status VARCHAR(50) DEFAULT 'active', -- active, cancelled, pending_cancellation, expired
    
    -- Detection metadata
    source_email_ids TEXT[], -- Array of Gmail message IDs
    detection_confidence DECIMAL(3, 2), -- 0.00 to 1.00
    detected_by VARCHAR(50), -- 'rule_based', 'llm', 'manual'
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    cancelled_at TIMESTAMP,
    
    CONSTRAINT fk_subscription_user FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Indexes for subscriptions
CREATE INDEX idx_subs_user ON subscriptions(user_id);
CREATE INDEX idx_subs_status ON subscriptions(status);
CREATE INDEX idx_subs_renewal ON subscriptions(next_renewal_date) WHERE next_renewal_date IS NOT NULL;
CREATE INDEX idx_subs_service ON subscriptions(service_name);
CREATE INDEX idx_subs_created ON subscriptions(created_at DESC);
CREATE UNIQUE INDEX idx_subs_user_service ON subscriptions(user_id, service_name) WHERE status = 'active';

-- Subscription events (audit trail)
CREATE TABLE subscription_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    subscription_id UUID NOT NULL REFERENCES subscriptions(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    event_type VARCHAR(100) NOT NULL, -- detected, updated, renewal_reminder, price_change, cancelled
    event_description TEXT,
    event_metadata JSONB, -- Flexible storage for event-specific data
    
    -- Agent info
    triggered_by VARCHAR(100), -- 'system', 'user', 'agent_name'
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_event_subscription FOREIGN KEY (subscription_id) REFERENCES subscriptions(id),
    CONSTRAINT fk_event_user FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Indexes for events
CREATE INDEX idx_events_subscription ON subscription_events(subscription_id);
CREATE INDEX idx_events_user ON subscription_events(user_id);
CREATE INDEX idx_events_type ON subscription_events(event_type);
CREATE INDEX idx_events_created ON subscription_events(created_at DESC);

-- Unsubscribe actions (tracks cancellation attempts)
CREATE TABLE unsubscribe_actions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    subscription_id UUID NOT NULL REFERENCES subscriptions(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Action details
    action_type VARCHAR(50) NOT NULL, -- automated, manual_link, manual_phone, email_required
    status VARCHAR(50) DEFAULT 'pending', -- pending, in_progress, awaiting_confirmation, confirmed, failed
    
    -- Execution details
    unsubscribe_url TEXT,
    http_method VARCHAR(10), -- GET, POST
    form_data JSONB, -- If POST required
    
    -- Response tracking
    http_status_code INTEGER,
    response_body_snippet TEXT,
    
    -- Confirmation monitoring
    confirmation_email_id VARCHAR(255), -- Gmail message ID of confirmation email
    confirmation_detected_at TIMESTAMP,
    
    -- Retry logic
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    
    -- Error handling
    error_message TEXT,
    requires_manual_action BOOLEAN DEFAULT FALSE,
    manual_instructions TEXT,
    
    -- Timestamps
    initiated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    monitoring_until TIMESTAMP, -- End of 7-day monitoring window
    
    CONSTRAINT fk_action_subscription FOREIGN KEY (subscription_id) REFERENCES subscriptions(id),
    CONSTRAINT fk_action_user FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Indexes for unsubscribe actions
CREATE INDEX idx_actions_subscription ON unsubscribe_actions(subscription_id);
CREATE INDEX idx_actions_user ON unsubscribe_actions(user_id);
CREATE INDEX idx_actions_status ON unsubscribe_actions(status);
CREATE INDEX idx_actions_monitoring ON unsubscribe_actions(monitoring_until) WHERE status = 'awaiting_confirmation';

-- Activity log (unified view of all user-agent interactions)
CREATE TABLE activity_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    activity_type VARCHAR(100) NOT NULL, -- scan_started, scan_completed, subscription_detected, cancellation_initiated, etc.
    activity_description TEXT NOT NULL,
    
    -- Related entities
    related_subscription_id UUID,
    related_session_id UUID,
    related_action_id UUID,
    
    -- Metadata
    activity_metadata JSONB,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_log_user FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Indexes for activity log
CREATE INDEX idx_log_user ON activity_log(user_id);
CREATE INDEX idx_log_type ON activity_log(activity_type);
CREATE INDEX idx_log_created ON activity_log(created_at DESC);

-- Service catalog (optional: pre-populated known services)
CREATE TABLE service_catalog (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_name VARCHAR(255) UNIQUE NOT NULL,
    service_domain VARCHAR(255),
    logo_url TEXT,
    category VARCHAR(100),
    
    -- Known patterns for detection
    email_domains TEXT[], -- e.g., ['netflix.com', 'account.netflix.com']
    keywords TEXT[],
    
    -- Stats
    times_detected INTEGER DEFAULT 0,
    avg_price DECIMAL(10, 2),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for service catalog
CREATE INDEX idx_catalog_name ON service_catalog(service_name);
CREATE INDEX idx_catalog_domain ON service_catalog(service_domain);
CREATE INDEX idx_catalog_category ON service_catalog(category);

-- Triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_subscriptions_updated_at
    BEFORE UPDATE ON subscriptions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_service_catalog_updated_at
    BEFORE UPDATE ON service_catalog
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Views for common queries

-- Active subscriptions summary per user
CREATE VIEW user_subscription_summary AS
SELECT 
    u.id AS user_id,
    u.email,
    COUNT(s.id) AS total_subscriptions,
    SUM(CASE 
        WHEN s.billing_period = 'monthly' THEN s.price
        WHEN s.billing_period = 'annually' THEN s.price / 12
        WHEN s.billing_period = 'quarterly' THEN s.price / 3
        ELSE 0
    END) AS estimated_monthly_spend,
    SUM(CASE 
        WHEN s.billing_period = 'annually' THEN s.price
        WHEN s.billing_period = 'monthly' THEN s.price * 12
        WHEN s.billing_period = 'quarterly' THEN s.price * 4
        ELSE 0
    END) AS estimated_annual_spend
FROM users u
LEFT JOIN subscriptions s ON u.id = s.user_id AND s.status = 'active'
GROUP BY u.id, u.email;

-- Recent activity per user (last 30 days)
CREATE VIEW recent_user_activity AS
SELECT 
    user_id,
    activity_type,
    activity_description,
    created_at
FROM activity_log
WHERE created_at > CURRENT_TIMESTAMP - INTERVAL '30 days'
ORDER BY created_at DESC;

-- Comments for documentation
COMMENT ON TABLE users IS 'User accounts with encrypted Gmail credentials';
COMMENT ON TABLE subscriptions IS 'Detected subscriptions with extracted metadata';
COMMENT ON TABLE unsubscribe_actions IS 'Tracks automated and manual cancellation attempts';
COMMENT ON TABLE activity_log IS 'Unified audit trail of all system actions';
COMMENT ON COLUMN subscriptions.detection_confidence IS 'LLM confidence score (0.00 to 1.00)';
COMMENT ON COLUMN unsubscribe_actions.monitoring_until IS 'End of confirmation monitoring period (initiated_at + 7 days)';
