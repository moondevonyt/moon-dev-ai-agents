-- Moon Dev EDA Database Schema
-- TimescaleDB with Event Sourcing
-- Maps to T-1.3: TimescaleDB Setup
--
-- This schema creates:
-- 1. Events hypertable (main audit log)
-- 2. Positions table (open positions)
-- 3. Trades table (executed trades)
-- 4. Users table (user configuration)
-- 5. Necessary indices for query performance

-- ============================================================================
-- USERS TABLE
-- ============================================================================
-- Stores user accounts and configuration

CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    initial_balance NUMERIC(20, 2) NOT NULL DEFAULT 50000,
    max_leverage NUMERIC(5, 2) NOT NULL DEFAULT 10.0,
    max_daily_loss_pct NUMERIC(5, 2) NOT NULL DEFAULT 2.0,
    trading_enabled BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT positive_balance CHECK (initial_balance > 0),
    CONSTRAINT valid_leverage CHECK (max_leverage > 0 AND max_leverage <= 100)
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);

-- ============================================================================
-- EVENTS TABLE (HYPERTABLE)
-- ============================================================================
-- Event sourcing store - immutable log of all events
-- Maps to T-2.3: Event Store Persistence (FR-4.2)

CREATE TABLE IF NOT EXISTS events (
    event_id UUID PRIMARY KEY NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    token VARCHAR(20),
    user_id UUID,
    source VARCHAR(100) NOT NULL,
    data JSONB NOT NULL,
    correlation_id VARCHAR(100),
    version INT NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    CONSTRAINT valid_event_type CHECK (event_type != '')
);

-- Convert to TimescaleDB hypertable with automatic partitioning
-- T-1.3.2: Create hypertable
SELECT create_hypertable(
    'events',
    'timestamp',
    if_not_exists => TRUE,
    chunk_time_interval => INTERVAL '1 day'
);

-- Compression policy: compress chunks older than 7 days
-- T-1.3.3: Configure compression
ALTER TABLE events SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'token,event_type,source',
    timescaledb.compress_orderby = 'timestamp DESC'
);

SELECT add_compression_policy(
    'events',
    INTERVAL '7 days',
    if_not_exists => TRUE
);

-- Retention policy: keep data for 1 year (compliance requirement)
SELECT add_retention_policy(
    'events',
    INTERVAL '365 days',
    if_not_exists => TRUE
);

-- T-2.3.3: Indices for query optimization
-- Query patterns:
-- 1. Get events by date range and token
-- 2. Get events by type
-- 3. Get events by source (agent name)

CREATE INDEX IF NOT EXISTS idx_events_timestamp_token 
    ON events (timestamp DESC, token) 
    WHERE token IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_events_timestamp_type 
    ON events (timestamp DESC, event_type);

CREATE INDEX IF NOT EXISTS idx_events_timestamp_source 
    ON events (timestamp DESC, source);

CREATE INDEX IF NOT EXISTS idx_events_correlation 
    ON events (correlation_id) 
    WHERE correlation_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_events_user 
    ON events (user_id, timestamp DESC) 
    WHERE user_id IS NOT NULL;

-- ============================================================================
-- POSITIONS TABLE
-- ============================================================================
-- Current open positions
-- Maps to FR-4.1: State Management

CREATE TABLE IF NOT EXISTS positions (
    position_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    token VARCHAR(20) NOT NULL,
    direction VARCHAR(10) NOT NULL, -- LONG or SHORT
    size NUMERIC(20, 8) NOT NULL,
    entry_price NUMERIC(20, 8) NOT NULL,
    current_price NUMERIC(20, 8) NOT NULL,
    unrealized_pnl NUMERIC(20, 2),
    leverage NUMERIC(5, 2),
    opened_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    CONSTRAINT valid_direction CHECK (direction IN ('LONG', 'SHORT')),
    CONSTRAINT positive_size CHECK (size > 0),
    CONSTRAINT positive_price CHECK (entry_price > 0 AND current_price > 0)
);

CREATE INDEX IF NOT EXISTS idx_positions_user_token 
    ON positions(user_id, token);

CREATE INDEX IF NOT EXISTS idx_positions_user_opened 
    ON positions(user_id, opened_at DESC);

-- ============================================================================
-- TRADES TABLE
-- ============================================================================
-- Executed trades (permanent record)
-- Maps to FR-3.3: Trade Execution Recording

CREATE TABLE IF NOT EXISTS trades (
    trade_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    token VARCHAR(20) NOT NULL,
    direction VARCHAR(10) NOT NULL, -- LONG or SHORT
    entry_price NUMERIC(20, 8) NOT NULL,
    entry_amount NUMERIC(20, 8) NOT NULL,
    exit_price NUMERIC(20, 8),
    exit_amount NUMERIC(20, 8),
    realized_pnl NUMERIC(20, 2),
    pnl_pct NUMERIC(8, 4),
    fee_paid NUMERIC(20, 2) NOT NULL DEFAULT 0,
    duration_seconds INT,
    source VARCHAR(100), -- e.g., "trading_agent", "manual"
    status VARCHAR(20) NOT NULL DEFAULT 'OPEN', -- OPEN, CLOSED, CANCELLED
    entered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    exited_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    CONSTRAINT valid_direction CHECK (direction IN ('LONG', 'SHORT')),
    CONSTRAINT valid_status CHECK (status IN ('OPEN', 'CLOSED', 'CANCELLED')),
    CONSTRAINT positive_prices CHECK (entry_price > 0 AND (exit_price IS NULL OR exit_price > 0))
);

-- T-1.3.2: Convert trades to hypertable for time-series optimization
SELECT create_hypertable(
    'trades',
    'entered_at',
    if_not_exists => TRUE,
    chunk_time_interval => INTERVAL '1 day'
);

CREATE INDEX IF NOT EXISTS idx_trades_user_token 
    ON trades(user_id, token, entered_at DESC);

CREATE INDEX IF NOT EXISTS idx_trades_user_status 
    ON trades(user_id, status, entered_at DESC);

CREATE INDEX IF NOT EXISTS idx_trades_closed 
    ON trades(user_id, entered_at DESC) 
    WHERE status = 'CLOSED';

-- ============================================================================
-- PORTFOLIO SNAPSHOT TABLE
-- ============================================================================
-- Periodic snapshots for consistency checking
-- Maps to FR-4.3: State Snapshots

CREATE TABLE IF NOT EXISTS portfolio_snapshots (
    snapshot_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    balance NUMERIC(20, 2) NOT NULL,
    portfolio_value NUMERIC(20, 2) NOT NULL,
    leverage_ratio NUMERIC(8, 4),
    daily_pnl NUMERIC(20, 2),
    positions_count INT,
    snapshot_data JSONB, -- Complete portfolio state
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    CONSTRAINT positive_balance CHECK (balance >= 0)
);

-- Convert to hypertable
SELECT create_hypertable(
    'portfolio_snapshots',
    'timestamp',
    if_not_exists => TRUE,
    chunk_time_interval => INTERVAL '1 day'
);

CREATE INDEX IF NOT EXISTS idx_snapshots_user_timestamp 
    ON portfolio_snapshots(user_id, timestamp DESC);

-- ============================================================================
-- BACKTEST RESULTS TABLE
-- ============================================================================
-- Stores backtest results for analysis
-- Maps to DESIGN.md User Story 3: Event Replay for Backtesting

CREATE TABLE IF NOT EXISTS backtest_results (
    backtest_id UUID PRIMARY KEY,
    user_id UUID,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    initial_balance NUMERIC(20, 2) NOT NULL,
    final_balance NUMERIC(20, 2) NOT NULL,
    total_return_pct NUMERIC(8, 4),
    sharpe_ratio NUMERIC(8, 4),
    sortino_ratio NUMERIC(8, 4),
    max_drawdown_pct NUMERIC(8, 4),
    win_rate_pct NUMERIC(5, 2),
    profit_factor NUMERIC(8, 4),
    trade_count INT,
    events_processed INT,
    backtest_time_seconds NUMERIC(10, 2),
    results_json JSONB, -- Complete backtest results
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_backtest_user 
    ON backtest_results(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_backtest_dates 
    ON backtest_results(start_date, end_date);

-- ============================================================================
-- ALERTS TABLE
-- ============================================================================
-- User alerts and notifications
-- Maps to Story 1: Real-Time Price Alert Detection

CREATE TABLE IF NOT EXISTS alerts (
    alert_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    token VARCHAR(20),
    alert_type VARCHAR(50) NOT NULL, -- "price_spike", "liquidation_risk", etc.
    severity VARCHAR(20) NOT NULL, -- "INFO", "WARNING", "CRITICAL"
    message TEXT,
    read BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    read_at TIMESTAMPTZ,
    
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    CONSTRAINT valid_severity CHECK (severity IN ('INFO', 'WARNING', 'CRITICAL'))
);

CREATE INDEX IF NOT EXISTS idx_alerts_user_unread 
    ON alerts(user_id, created_at DESC) 
    WHERE read = false;

-- ============================================================================
-- MATERIALIZED VIEW: Daily Statistics
-- ============================================================================
-- Pre-computed daily stats for dashboard performance

CREATE MATERIALIZED VIEW IF NOT EXISTS daily_user_stats AS
SELECT 
    user_id,
    DATE(entered_at) as trade_date,
    COUNT(*) as trade_count,
    SUM(CASE WHEN realized_pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
    SUM(CASE WHEN realized_pnl < 0 THEN 1 ELSE 0 END) as losing_trades,
    SUM(realized_pnl) as daily_pnl,
    AVG(pnl_pct) as avg_pnl_pct,
    MAX(pnl_pct) as best_trade_pct,
    MIN(pnl_pct) as worst_trade_pct
FROM trades
WHERE status = 'CLOSED'
GROUP BY user_id, DATE(entered_at);

CREATE UNIQUE INDEX IF NOT EXISTS idx_daily_stats_unique 
    ON daily_user_stats(user_id, trade_date);

-- ============================================================================
-- GRANT PERMISSIONS
-- ============================================================================
-- Application user (read/write trades, events, positions)
DO $$
BEGIN
    CREATE USER trading_app WITH PASSWORD 'change-me';
EXCEPTION WHEN DUPLICATE_OBJECT THEN
    NULL;
END
$$;

GRANT CONNECT ON DATABASE moon_dev TO trading_app;
GRANT USAGE ON SCHEMA public TO trading_app;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO trading_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO trading_app;

-- Read-only user (for analytics)
DO $$
BEGIN
    CREATE USER analytics_user WITH PASSWORD 'change-me';
EXCEPTION WHEN DUPLICATE_OBJECT THEN
    NULL;
END
$$;

GRANT CONNECT ON DATABASE moon_dev TO analytics_user;
GRANT USAGE ON SCHEMA public TO analytics_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO analytics_user;

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================
-- Run these after schema creation to verify setup

-- SELECT 'Events hypertable created' as status
-- UNION ALL SELECT tablename || ' table created' FROM pg_tables WHERE tablename IN ('users', 'positions', 'trades', 'portfolio_snapshots', 'backtest_results', 'alerts');
-- UNION ALL SELECT 'TimescaleDB hypertable: events' FROM timescaledb_information.hypertables WHERE hypertable_name = 'events';

-- ============================================================================
-- SCHEMA COMPLETE
-- ============================================================================
-- Database schema ready for Moon Dev EDA system
-- Maps to T-1.3: TimescaleDB Setup
-- 
-- Table Summary:
-- - events: Main event log (hypertable) - immutable audit trail
-- - positions: Current open positions
-- - trades: Executed trades with P&L
-- - portfolio_snapshots: Portfolio state snapshots
-- - backtest_results: Backtest run results
-- - alerts: User notifications
-- - users: User accounts and configuration
--
-- All tables have appropriate indices for query performance
-- Compression and retention policies configured for events table
-- Foreign key constraints maintain data integrity
