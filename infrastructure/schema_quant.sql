-- ═══════════════════════════════════════════════════════════════════════════
-- 🌙 Moon Dev's Quantitative Trading Schema Extensions
-- TimescaleDB schema for Jim Simons-style quantitative trading system
-- ═══════════════════════════════════════════════════════════════════════════

-- Signal Weights Table
-- Tracks historical weights for each signal source in aggregation
CREATE TABLE IF NOT EXISTS signal_weights (
    time TIMESTAMPTZ NOT NULL,
    signal_source VARCHAR(255) NOT NULL,
    weight DOUBLE PRECISION NOT NULL,
    accuracy DOUBLE PRECISION,
    observations INTEGER DEFAULT 0,
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (time, signal_source)
);

-- Convert to hypertable with 1-day chunks
SELECT create_hypertable('signal_weights', 'time', 
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- Create indices for common queries
CREATE INDEX IF NOT EXISTS idx_signal_weights_source ON signal_weights (signal_source, time DESC);
CREATE INDEX IF NOT EXISTS idx_signal_weights_time ON signal_weights (time DESC);


-- Strategy Capacity Table
-- Tracks capacity metrics and slippage for each strategy
CREATE TABLE IF NOT EXISTS strategy_capacity (
    time TIMESTAMPTZ NOT NULL,
    strategy_id VARCHAR(255) NOT NULL,
    position_size DOUBLE PRECISION NOT NULL,
    slippage_pct DOUBLE PRECISION NOT NULL,
    market_impact_coefficient DOUBLE PRECISION,
    estimated_capacity DOUBLE PRECISION,
    utilization_pct DOUBLE PRECISION,
    PRIMARY KEY (time, strategy_id)
);

-- Convert to hypertable with 1-day chunks
SELECT create_hypertable('strategy_capacity', 'time',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- Create indices
CREATE INDEX IF NOT EXISTS idx_strategy_capacity_id ON strategy_capacity (strategy_id, time DESC);
CREATE INDEX IF NOT EXISTS idx_strategy_capacity_time ON strategy_capacity (time DESC);


-- Signal Performance Table
-- Tracks performance metrics for each signal source
CREATE TABLE IF NOT EXISTS signal_performance (
    time TIMESTAMPTZ NOT NULL,
    signal_source VARCHAR(255) NOT NULL,
    returns DOUBLE PRECISION NOT NULL,
    sharpe_ratio DOUBLE PRECISION,
    win_rate DOUBLE PRECISION,
    profit_factor DOUBLE PRECISION,
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'active', -- active, degraded, retired
    PRIMARY KEY (time, signal_source)
);

-- Convert to hypertable with 1-day chunks
SELECT create_hypertable('signal_performance', 'time',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- Create indices
CREATE INDEX IF NOT EXISTS idx_signal_performance_source ON signal_performance (signal_source, time DESC);
CREATE INDEX IF NOT EXISTS idx_signal_performance_status ON signal_performance (status, time DESC);
CREATE INDEX IF NOT EXISTS idx_signal_performance_time ON signal_performance (time DESC);


-- Regime History Table
-- Tracks market regime changes over time
CREATE TABLE IF NOT EXISTS regime_history (
    time TIMESTAMPTZ NOT NULL,
    token VARCHAR(100) NOT NULL,
    regime_type VARCHAR(50) NOT NULL, -- volatility, trend, liquidity
    regime_value VARCHAR(50) NOT NULL, -- high/low, trending/mean-reverting, liquid/illiquid
    confidence DOUBLE PRECISION,
    duration_hours DOUBLE PRECISION,
    metrics JSONB, -- Additional regime-specific metrics
    PRIMARY KEY (time, token, regime_type)
);

-- Convert to hypertable with 1-day chunks
SELECT create_hypertable('regime_history', 'time',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- Create indices
CREATE INDEX IF NOT EXISTS idx_regime_history_token ON regime_history (token, time DESC);
CREATE INDEX IF NOT EXISTS idx_regime_history_type ON regime_history (regime_type, time DESC);
CREATE INDEX IF NOT EXISTS idx_regime_history_time ON regime_history (time DESC);
CREATE INDEX IF NOT EXISTS idx_regime_history_metrics ON regime_history USING GIN (metrics);


-- Correlation Matrix Table
-- Stores correlation coefficients between token pairs
CREATE TABLE IF NOT EXISTS correlation_matrix (
    time TIMESTAMPTZ NOT NULL,
    token_1 VARCHAR(100) NOT NULL,
    token_2 VARCHAR(100) NOT NULL,
    window_days INTEGER NOT NULL,
    correlation DOUBLE PRECISION NOT NULL,
    p_value DOUBLE PRECISION,
    mutual_information DOUBLE PRECISION,
    lag_minutes INTEGER DEFAULT 0, -- For time-lagged correlations
    PRIMARY KEY (time, token_1, token_2, window_days, lag_minutes)
);

-- Convert to hypertable with 1-day chunks
SELECT create_hypertable('correlation_matrix', 'time',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- Create indices
CREATE INDEX IF NOT EXISTS idx_correlation_matrix_tokens ON correlation_matrix (token_1, token_2, time DESC);
CREATE INDEX IF NOT EXISTS idx_correlation_matrix_window ON correlation_matrix (window_days, time DESC);
CREATE INDEX IF NOT EXISTS idx_correlation_matrix_time ON correlation_matrix (time DESC);


-- Alternative Data Table
-- Stores alternative data metrics (social, on-chain, GitHub)
CREATE TABLE IF NOT EXISTS alternative_data (
    time TIMESTAMPTZ NOT NULL,
    token VARCHAR(100) NOT NULL,
    source VARCHAR(100) NOT NULL, -- twitter, github, onchain
    metric_type VARCHAR(100) NOT NULL, -- mention_velocity, commit_frequency, tx_velocity
    raw_value DOUBLE PRECISION NOT NULL,
    z_score DOUBLE PRECISION,
    percentile DOUBLE PRECISION,
    metadata JSONB, -- Additional source-specific data
    PRIMARY KEY (time, token, source, metric_type)
);

-- Convert to hypertable with 1-day chunks
SELECT create_hypertable('alternative_data', 'time',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- Create indices
CREATE INDEX IF NOT EXISTS idx_alternative_data_token ON alternative_data (token, time DESC);
CREATE INDEX IF NOT EXISTS idx_alternative_data_source ON alternative_data (source, time DESC);
CREATE INDEX IF NOT EXISTS idx_alternative_data_metric ON alternative_data (metric_type, time DESC);
CREATE INDEX IF NOT EXISTS idx_alternative_data_time ON alternative_data (time DESC);
CREATE INDEX IF NOT EXISTS idx_alternative_data_metadata ON alternative_data USING GIN (metadata);


-- Backtest Results Table
-- Stores detailed backtest validation results
CREATE TABLE IF NOT EXISTS backtest_results (
    time TIMESTAMPTZ NOT NULL,
    strategy_id VARCHAR(255) NOT NULL,
    backtest_id UUID NOT NULL,
    start_date TIMESTAMPTZ NOT NULL,
    end_date TIMESTAMPTZ NOT NULL,
    sharpe_ratio DOUBLE PRECISION,
    max_drawdown_pct DOUBLE PRECISION,
    win_rate_pct DOUBLE PRECISION,
    profit_factor DOUBLE PRECISION,
    total_trades INTEGER,
    p_value DOUBLE PRECISION,
    validation_status VARCHAR(50), -- validated, rejected
    rejection_reason TEXT,
    metrics JSONB, -- Additional performance metrics
    PRIMARY KEY (time, strategy_id, backtest_id)
);

-- Convert to hypertable with 7-day chunks (less frequent data)
SELECT create_hypertable('backtest_results', 'time',
    chunk_time_interval => INTERVAL '7 days',
    if_not_exists => TRUE
);

-- Create indices
CREATE INDEX IF NOT EXISTS idx_backtest_results_strategy ON backtest_results (strategy_id, time DESC);
CREATE INDEX IF NOT EXISTS idx_backtest_results_status ON backtest_results (validation_status, time DESC);
CREATE INDEX IF NOT EXISTS idx_backtest_results_time ON backtest_results (time DESC);
CREATE INDEX IF NOT EXISTS idx_backtest_results_metrics ON backtest_results USING GIN (metrics);


-- Transaction Cost Analysis Table
-- Tracks estimated vs actual transaction costs
CREATE TABLE IF NOT EXISTS transaction_costs (
    time TIMESTAMPTZ NOT NULL,
    trade_id VARCHAR(255) NOT NULL,
    token VARCHAR(100) NOT NULL,
    estimated_slippage_pct DOUBLE PRECISION,
    actual_slippage_pct DOUBLE PRECISION,
    estimated_fee DOUBLE PRECISION,
    actual_fee DOUBLE PRECISION,
    total_cost_pct DOUBLE PRECISION,
    order_size DOUBLE PRECISION,
    avg_volume DOUBLE PRECISION,
    market_impact_coefficient DOUBLE PRECISION,
    PRIMARY KEY (time, trade_id)
);

-- Convert to hypertable with 1-day chunks
SELECT create_hypertable('transaction_costs', 'time',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- Create indices
CREATE INDEX IF NOT EXISTS idx_transaction_costs_token ON transaction_costs (token, time DESC);
CREATE INDEX IF NOT EXISTS idx_transaction_costs_time ON transaction_costs (time DESC);


-- Portfolio Allocations Table
-- Tracks portfolio allocation changes over time
CREATE TABLE IF NOT EXISTS portfolio_allocations (
    time TIMESTAMPTZ NOT NULL,
    portfolio_id VARCHAR(255) NOT NULL,
    token VARCHAR(100) NOT NULL,
    target_weight DOUBLE PRECISION NOT NULL,
    current_weight DOUBLE PRECISION NOT NULL,
    rebalance_amount DOUBLE PRECISION,
    allocation_method VARCHAR(50), -- mpt, kelly, risk_parity
    risk_contribution DOUBLE PRECISION,
    PRIMARY KEY (time, portfolio_id, token)
);

-- Convert to hypertable with 1-day chunks
SELECT create_hypertable('portfolio_allocations', 'time',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- Create indices
CREATE INDEX IF NOT EXISTS idx_portfolio_allocations_id ON portfolio_allocations (portfolio_id, time DESC);
CREATE INDEX IF NOT EXISTS idx_portfolio_allocations_token ON portfolio_allocations (token, time DESC);
CREATE INDEX IF NOT EXISTS idx_portfolio_allocations_time ON portfolio_allocations (time DESC);


-- ═══════════════════════════════════════════════════════════════════════════
-- Continuous Aggregates for Performance Optimization
-- ═══════════════════════════════════════════════════════════════════════════

-- Daily Signal Performance Aggregate
CREATE MATERIALIZED VIEW IF NOT EXISTS signal_performance_daily
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', time) AS bucket,
    signal_source,
    AVG(sharpe_ratio) AS avg_sharpe_ratio,
    AVG(win_rate) AS avg_win_rate,
    SUM(total_trades) AS total_trades,
    MAX(status) AS latest_status
FROM signal_performance
GROUP BY bucket, signal_source;

-- Refresh policy: refresh last 7 days every hour
SELECT add_continuous_aggregate_policy('signal_performance_daily',
    start_offset => INTERVAL '7 days',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);


-- Hourly Regime Summary
CREATE MATERIALIZED VIEW IF NOT EXISTS regime_summary_hourly
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', time) AS bucket,
    token,
    regime_type,
    regime_value,
    AVG(confidence) AS avg_confidence,
    COUNT(*) AS regime_count
FROM regime_history
GROUP BY bucket, token, regime_type, regime_value;

-- Refresh policy
SELECT add_continuous_aggregate_policy('regime_summary_hourly',
    start_offset => INTERVAL '2 days',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);


-- ═══════════════════════════════════════════════════════════════════════════
-- Data Retention Policies
-- ═══════════════════════════════════════════════════════════════════════════

-- Keep raw data for 1 year, then drop
SELECT add_retention_policy('signal_weights', INTERVAL '1 year', if_not_exists => TRUE);
SELECT add_retention_policy('strategy_capacity', INTERVAL '1 year', if_not_exists => TRUE);
SELECT add_retention_policy('signal_performance', INTERVAL '1 year', if_not_exists => TRUE);
SELECT add_retention_policy('regime_history', INTERVAL '1 year', if_not_exists => TRUE);
SELECT add_retention_policy('correlation_matrix', INTERVAL '1 year', if_not_exists => TRUE);
SELECT add_retention_policy('alternative_data', INTERVAL '1 year', if_not_exists => TRUE);
SELECT add_retention_policy('transaction_costs', INTERVAL '1 year', if_not_exists => TRUE);
SELECT add_retention_policy('portfolio_allocations', INTERVAL '1 year', if_not_exists => TRUE);

-- Keep backtest results for 2 years (less frequent, more valuable)
SELECT add_retention_policy('backtest_results', INTERVAL '2 years', if_not_exists => TRUE);


-- ═══════════════════════════════════════════════════════════════════════════
-- Grants and Permissions
-- ═══════════════════════════════════════════════════════════════════════════

-- Grant permissions to application user (adjust username as needed)
-- GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO moondev_app;
-- GRANT USAGE ON SCHEMA public TO moondev_app;

-- ═══════════════════════════════════════════════════════════════════════════
-- Schema Complete
-- ═══════════════════════════════════════════════════════════════════════════
