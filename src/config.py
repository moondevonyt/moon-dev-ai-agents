"""
🌙 Moon Dev's Configuration File
Built with love by Moon Dev 🚀
"""

# 🔄 Exchange Selection
EXCHANGE = 'solana'  # Options: 'solana', 'hyperliquid'

# 💰 Trading Configuration
USDC_ADDRESS = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"  # Never trade or close
SOL_ADDRESS = "So11111111111111111111111111111111111111111"   # Never trade or close

# Create a list of addresses to exclude from trading/closing
EXCLUDED_TOKENS = [USDC_ADDRESS, SOL_ADDRESS]

# Token List for Trading 📋
# NOTE: Trading Agent now has its own token list - see src/agents/trading_agent.py lines 101-104
MONITORED_TOKENS = [
    # '9BB6NFEcjBCtnNLFko2FqVQBq8HHM13kCyYcdQbgpump',    # 🌬️ FART
    # 'DitHyRMQiSDhn5cnKMJV2CDDt6sVct96YrECiM49pump'     # housecoin
]

# Moon Dev's Token Trading List 🚀
# Each token is carefully selected by Moon Dev for maximum moon potential! 🌙
tokens_to_trade = MONITORED_TOKENS  # Using the same list for trading

# ⚡ HyperLiquid Configuration
HYPERLIQUID_SYMBOLS = ['BTC', 'ETH', 'SOL']  # Symbols to trade on HyperLiquid perps
HYPERLIQUID_LEVERAGE = 5  # Default leverage for HyperLiquid trades (1-50)

# 🔄 Exchange-Specific Token Lists
# Use this to determine which tokens/symbols to trade based on active exchange
def get_active_tokens():
    """Returns the appropriate token/symbol list based on active exchange"""
    if EXCHANGE == 'hyperliquid':
        return HYPERLIQUID_SYMBOLS
    else:
        return MONITORED_TOKENS

# Token to Exchange Mapping (for future hybrid trading)
TOKEN_EXCHANGE_MAP = {
    'BTC': 'hyperliquid',
    'ETH': 'hyperliquid',
    'SOL': 'hyperliquid',
    # All other tokens default to Solana
}

# Token and wallet settings
symbol = '9BB6NFEcjBCtnNLFko2FqVQBq8HHM13kCyYcdQbgpump'
address = '4wgfCBf2WwLSRKLef9iW7JXZ2AfkxUxGM4XcKpHm3Sin' # YOUR WALLET ADDRESS HERE

# Position sizing 🎯
usd_size = 25  # Size of position to hold
max_usd_order_size = 3  # Max order size
tx_sleep = 30  # Sleep between transactions
slippage = 199  # Slippage settings

# Risk Management Settings 🛡️
CASH_PERCENTAGE = 20  # Minimum % to keep in USDC as safety buffer (0-100)
MAX_POSITION_PERCENTAGE = 30  # Maximum % allocation per position (0-100)
STOPLOSS_PRICE = 1 # NOT USED YET 1/5/25    
BREAKOUT_PRICE = .0001 # NOT USED YET 1/5/25
SLEEP_AFTER_CLOSE = 600  # Prevent overtrading

MAX_LOSS_GAIN_CHECK_HOURS = 12  # How far back to check for max loss/gain limits (in hours)
SLEEP_BETWEEN_RUNS_MINUTES = 15  # How long to sleep between agent runs 🕒


# Max Loss/Gain Settings FOR RISK AGENT 1/5/25
USE_PERCENTAGE = False  # If True, use percentage-based limits. If False, use USD-based limits

# USD-based limits (used if USE_PERCENTAGE is False)
MAX_LOSS_USD = 25  # Maximum loss in USD before stopping trading
MAX_GAIN_USD = 25 # Maximum gain in USD before stopping trading

# USD MINIMUM BALANCE RISK CONTROL
MINIMUM_BALANCE_USD = 50  # If balance falls below this, risk agent will consider closing all positions
USE_AI_CONFIRMATION = True  # If True, consult AI before closing positions. If False, close immediately on breach

# Percentage-based limits (used if USE_PERCENTAGE is True)
MAX_LOSS_PERCENT = 5  # Maximum loss as percentage (e.g., 20 = 20% loss)
MAX_GAIN_PERCENT = 5  # Maximum gain as percentage (e.g., 50 = 50% gain)

# Transaction settings ⚡
slippage = 199  # 500 = 5% and 50 = .5% slippage
PRIORITY_FEE = 100000  # ~0.02 USD at current SOL prices
orders_per_open = 3  # Multiple orders for better fill rates

# Market maker settings 📊
buy_under = .0946
sell_over = 1

# Data collection settings 📈
DAYSBACK_4_DATA = 3
DATA_TIMEFRAME = '1H'  # 1m, 3m, 5m, 15m, 30m, 1H, 2H, 4H, 6H, 8H, 12H, 1D, 3D, 1W, 1M
SAVE_OHLCV_DATA = False  # 🌙 Set to True to save data permanently, False will only use temp data during run

# AI Model Settings 🤖
AI_MODEL = "claude-3-haiku-20240307"  # Model Options:
                                     # - claude-3-haiku-20240307 (Fast, efficient Claude model)
                                     # - claude-3-sonnet-20240229 (Balanced Claude model)
                                     # - claude-3-opus-20240229 (Most powerful Claude model)
AI_MAX_TOKENS = 1024  # Max tokens for response
AI_TEMPERATURE = 0.7  # Creativity vs precision (0-1)

# Trading Strategy Agent Settings - MAY NOT BE USED YET 1/5/25
ENABLE_STRATEGIES = True  # Set this to True to use strategies
STRATEGY_MIN_CONFIDENCE = 0.7  # Minimum confidence to act on strategy signals

# Sleep time between main agent runs
SLEEP_BETWEEN_RUNS_MINUTES = 15  # How long to sleep between agent runs 🕒

# in our nice_funcs in token over view we look for minimum trades last hour
MIN_TRADES_LAST_HOUR = 2


# Real-Time Clips Agent Settings 🎬
REALTIME_CLIPS_ENABLED = True
REALTIME_CLIPS_OBS_FOLDER = '/Volumes/Moon 26/OBS'  # Your OBS recording folder
REALTIME_CLIPS_AUTO_INTERVAL = 120  # Check every N seconds (120 = 2 minutes)
REALTIME_CLIPS_LENGTH = 2  # Minutes to analyze per check
REALTIME_CLIPS_AI_MODEL = 'groq'  # Model type: groq, openai, claude, deepseek, xai, ollama
REALTIME_CLIPS_AI_MODEL_NAME = None  # None = use default for model type
REALTIME_CLIPS_TWITTER = True  # Auto-open Twitter compose after clip

# Future variables (not active yet) 🔮
sell_at_multiple = 3
USDC_SIZE = 1
limit = 49
timeframe = '15m'
stop_loss_perctentage = -.24
EXIT_ALL_POSITIONS = False
DO_NOT_TRADE_LIST = ['777']
CLOSED_POSITIONS_TXT = '777'
minimum_trades_in_last_hour = 777

# ═══════════════════════════════════════════════════════════════════════════
# 📊 QUANTITATIVE TRADING AGENT CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

# Anomaly Detection Settings
ANOMALY_DETECTION_WINDOW_DAYS = 30  # Rolling window for mean reversion
ANOMALY_DETECTION_SIGMA_THRESHOLD = 2.0  # Standard deviations for anomaly
ANOMALY_DETECTION_P_VALUE_THRESHOLD = 0.05  # Statistical significance
ANOMALY_CORRELATION_CHANGE_THRESHOLD = 0.3  # Correlation change threshold
ANOMALY_CORRELATION_WINDOW_DAYS = 7  # Window for correlation changes

# Signal Aggregation Settings
SIGNAL_AGGREGATION_WINDOW_SECONDS = 5  # Time window to collect signals
SIGNAL_AGGREGATION_MIN_SOURCES = 3  # Minimum signal sources for consensus
SIGNAL_AGGREGATION_CONSENSUS_THRESHOLD = 70  # Consensus threshold percentage
SIGNAL_AGGREGATION_WEIGHT_ALPHA = 0.1  # EMA alpha for weight updates
SIGNAL_AGGREGATION_MIN_OBSERVATIONS = 10  # Min observations before full weight

# Transaction Cost Settings
MAX_TRANSACTION_COST_PCT = 0.3  # Maximum transaction cost percentage
MARKET_IMPACT_COEFFICIENT = 0.01  # Initial market impact coefficient (k)
SLIPPAGE_CALIBRATION_DAYS = 7  # Days of data for cost model calibration

# Backtesting Validation Settings
BACKTEST_MIN_YEARS = 3  # Minimum years of historical data
BACKTEST_P_VALUE_THRESHOLD = 0.05  # Statistical significance threshold
BACKTEST_MIN_SHARPE_RATIO = 1.5  # Minimum Sharpe ratio for validation
BACKTEST_MAX_DRAWDOWN_PCT = 20  # Maximum drawdown percentage
BACKTEST_MIN_WIN_RATE_PCT = 45  # Minimum win rate percentage
BACKTEST_WALK_FORWARD_WINDOWS = 12  # Number of rolling windows

# Capacity Monitoring Settings
CAPACITY_SLIPPAGE_THRESHOLD_PCT = 0.5  # Slippage threshold for capacity
CAPACITY_WARNING_UTILIZATION_PCT = 80  # Warning at 80% capacity
CAPACITY_EXCEEDED_UTILIZATION_PCT = 100  # Exceeded at 100% capacity
CAPACITY_POSITION_REDUCTION_PCT = 50  # Reduce position by 50% when exceeded
CAPACITY_CALIBRATION_DAYS = 30  # Days of data for capacity estimation
CAPACITY_UPDATE_FREQUENCY_DAYS = 7  # Update capacity estimates weekly

# Signal Decay Monitoring Settings
SIGNAL_DECAY_WINDOW_DAYS = 30  # Rolling window for performance tracking
SIGNAL_DECAY_SHARPE_THRESHOLD = 0.5  # Sharpe threshold for degradation
SIGNAL_DECAY_DEGRADED_DAYS = 14  # Days before marking as degraded
SIGNAL_DECAY_RETIREMENT_DAYS = 30  # Days before retirement
SIGNAL_DECAY_MIN_WIN_RATE_PCT = 40  # Minimum win rate before retirement
SIGNAL_DECAY_WEIGHT_REDUCTION_PCT = 50  # Weight reduction when degraded

# Regime Detection Settings
REGIME_VOLATILITY_HIGH_MULTIPLIER = 1.5  # High volatility threshold
REGIME_VOLATILITY_LOW_MULTIPLIER = 0.7  # Low volatility threshold
REGIME_VOLATILITY_WINDOW_DAYS = 30  # Rolling window for volatility
REGIME_TREND_ADX_TRENDING_THRESHOLD = 25  # ADX threshold for trending
REGIME_TREND_ADX_MEANREV_THRESHOLD = 20  # ADX threshold for mean reversion
REGIME_LIQUIDITY_LIQUID_SPREAD_PCT = 0.1  # Liquid spread threshold
REGIME_LIQUIDITY_ILLIQUID_SPREAD_PCT = 0.5  # Illiquid spread threshold
REGIME_MIN_PERSISTENCE_HOURS = 4  # Minimum hours before regime change

# Correlation Matrix Settings
CORRELATION_WINDOWS_DAYS = [30, 90, 180]  # Multiple correlation windows
CORRELATION_CHANGE_THRESHOLD = 0.4  # Significant correlation change
CORRELATION_CHANGE_LOOKBACK_DAYS = 14  # Lookback for change detection
CORRELATION_LAG_MIN_MINUTES = 1  # Minimum lag to test
CORRELATION_LAG_MAX_HOURS = 24  # Maximum lag to test
CORRELATION_LAG_INCREMENT_MINUTES = 15  # Lag increment
CORRELATION_DIVERSIFICATION_THRESHOLD = 0.7  # Max correlation for diversification

# Portfolio Optimization Settings
PORTFOLIO_MAX_POSITION_PCT = 20  # Maximum position size percentage
PORTFOLIO_KELLY_FRACTION = 0.25  # Fractional Kelly (25% for safety)
PORTFOLIO_REBALANCE_FREQUENCY_HOURS = 4  # Rebalance every 4 hours
PORTFOLIO_MIN_EXPECTED_RETURN = 0.0  # Minimum expected return constraint
PORTFOLIO_RISK_PARITY_ENABLED = True  # Enable risk parity allocation

# Alternative Data Settings
ALT_DATA_SOCIAL_INTERVAL_SECONDS = 60  # Social media check interval
ALT_DATA_ONCHAIN_INTERVAL_SECONDS = 300  # On-chain check interval (5 min)
ALT_DATA_GITHUB_INTERVAL_SECONDS = 3600  # GitHub check interval (1 hour)
ALT_DATA_NORMALIZATION_WINDOW_DAYS = 30  # Window for z-score normalization

# General Quant Agent Settings
QUANT_AGENTS_ENABLED = True  # Master switch for quant agents
QUANT_AGENTS_LOG_LEVEL = 'INFO'  # Logging level: DEBUG, INFO, WARNING, ERROR
QUANT_AGENTS_METRICS_ENABLED = True  # Enable Prometheus metrics
QUANT_AGENTS_HEALTH_CHECK_INTERVAL = 60  # Health check interval in seconds
