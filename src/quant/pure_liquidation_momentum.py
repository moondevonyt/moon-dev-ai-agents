"""
Pure Liquidation Momentum Strategy (Continuation/Follow the Liquidations)
=========================================================================

This strategy uses ONLY liquidation data - no OHLCV data.
It trades WITH liquidations (momentum/continuation):
- When long positions are liquidated → SELL (continue the down move)
- When short positions are liquidated → BUY (continue the up move)

The theory: Liquidations represent the start of cascading moves that continue in the same direction.

Total Trades: 1495
Win Rate: 53.38%
Return: 299.74%
Sharpe: 0.82
Max Drawdown: -45.35%


--- 5 MIN TEST....WORKS WELL! 500 

📈 FULL BASELINE STATS:
======================================================================
Start                     2024-06-04 12:50:00
End                       2025-09-22 14:25:00
Duration                    475 days 01:35:00
Exposure Time [%]                   30.256541
Equity Final [$]                 3997444.3498
Equity Peak [$]                 4154532.83245
Return [%]                         299.744435
Buy & Hold Return [%]               65.820151
Return (Ann.) [%]                  191.827748
Volatility (Ann.) [%]              233.801738
Sharpe Ratio                         0.820472
Sortino Ratio                        5.806576
Calmar Ratio                         4.229883
Max. Drawdown [%]                  -45.350603
Avg. Drawdown [%]                   -1.604503
Max. Drawdown Duration      167 days 11:40:00
Avg. Drawdown Duration        1 days 15:52:00
# Trades                                 1495
Win Rate [%]                        53.377926
Best Trade [%]                      53.026756
Worst Trade [%]                    -16.621365
Avg. Trade [%]                       0.098485
Max. Trade Duration           0 days 12:45:00
Avg. Trade Duration           0 days 02:14:00
Profit Factor                        1.219186
Expectancy [%]                       0.118977
SQN                                     2.107
_strategy                 PureLiquidationM...
_equity_curve                             ...
_trades                         Size  Entr...
dtype: object

======================================================================
RUNNING OPTIMIZATION
======================================================================
🔄 Optimizing parameters... This may take a few minutes...
                                                                                                                                                                      
✨ OPTIMIZED RESULTS:
======================================================================
Start                     2024-06-04 12:50:00
End                       2025-09-22 14:25:00
Duration                    475 days 01:35:00
Exposure Time [%]                    5.141792
Equity Final [$]                5946758.17419
Equity Peak [$]                 6079904.89419
Return [%]                         494.675817
Buy & Hold Return [%]               65.820151
Return (Ann.) [%]                  289.621294
Volatility (Ann.) [%]               71.321572
Sharpe Ratio                         4.060781
Sortino Ratio                       30.850515
Calmar Ratio                        43.365552
Max. Drawdown [%]                   -6.678603
Avg. Drawdown [%]                   -1.054539
Max. Drawdown Duration       21 days 21:55:00
Avg. Drawdown Duration        0 days 19:56:00
# Trades                                  701
Win Rate [%]                        66.191155
Best Trade [%]                       2.278101
Worst Trade [%]                     -4.815867
Avg. Trade [%]                        0.27305
Max. Trade Duration           0 days 06:25:00
Avg. Trade Duration           0 days 00:46:00
Profit Factor                         1.94185
Expectancy [%]                       0.277744
SQN                                  7.206844
_strategy                 PureLiquidationM...
_equity_curve                             ...
_trades                        Size  Entry...
dtype: object

🎯 OPTIMIZED PARAMETERS:
--------------------------------------------------
Liquidation Threshold: $900,000
Take Profit: 1.0%
Stop Loss: 1.5%
Max Hold Hours: 6

📊 IMPROVEMENT SUMMARY:
--------------------------------------------------
Baseline Return: 299.74%
Optimized Return: 494.68%
Improvement: 194.93%

=======================================================
RUNNING OPTIMIZATION
======================================================================
🔄 Optimizing parameters... This may take a few minutes...
                                                                                
✨ OPTIMIZED RESULTS:
======================================================================
Start                     2024-06-04 12:51:00
End                       2025-09-22 14:29:00
Duration                    475 days 01:38:00
Exposure Time [%]                    2.627544
Equity Final [$]                6975624.41629
Equity Peak [$]                 7074383.72489
Return [%]                         597.562442
Buy & Hold Return [%]               65.820151
Return (Ann.) [%]                  343.470958
Volatility (Ann.) [%]              108.513458
Sharpe Ratio                         3.165238
Sortino Ratio                       19.819296
Calmar Ratio                        17.557738
Max. Drawdown [%]                  -19.562369
Avg. Drawdown [%]                   -0.872776
Max. Drawdown Duration       42 days 05:01:00
Avg. Drawdown Duration        0 days 15:04:00
# Trades                                  478
Win Rate [%]                        77.405858
Best Trade [%]                       3.170871
Worst Trade [%]                    -20.234605
Avg. Trade [%]                       0.437188
Max. Trade Duration           0 days 03:00:00
Avg. Trade Duration           0 days 00:37:00
Profit Factor                        2.744819
Expectancy [%]                       0.446761
SQN                                  7.592419
_strategy                 PureLiquidationM...
_equity_curve                             ...
_trades                        Size  Entry...
dtype: object

🎯 OPTIMIZED PARAMETERS:
--------------------------------------------------
Liquidation Threshold: $975,000
Take Profit: 1.0%
Stop Loss: 2.0%
Max Hold Hours: 2

📊 IMPROVEMENT SUMMARY:
--------------------------------------------------
Baseline Return: -100.00%
Optimized Return: 597.56%

"""

import pandas as pd
import numpy as np
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

print("🚀 Moon Dev's Pure Liquidation MOMENTUM Strategy 🌙")
print("Theory: Sell when longs are liquidated, Buy when shorts are liquidated")
print("=" * 70)

# # Load liquidation data
# LIQUIDATION_PATH = '/Users/md/Dropbox/dev/github/moon-dev-trading-bots/backtests/liquidations/results/all_liquidations.csv'
# 
# # Try to load all liquidations first, fall back to 90-day data if not available
# try:
#     liq_data = pd.read_csv(LIQUIDATION_PATH)
#     print(f"✅ Loaded ALL liquidation data from: {LIQUIDATION_PATH}")
# except:
#     LIQUIDATION_PATH = '/Users/md/Dropbox/dev/github/moon-dev-trading-bots/backtests/liquidations/data/liquidations_90days.csv'
#     liq_data = pd.read_csv(LIQUIDATION_PATH)
#     print(f"📊 Loaded 90-day liquidation data from: {LIQUIDATION_PATH}")
# 
# # Process liquidation data
# if len(liq_data.columns) >= 13:
#     column_names = ['symbol', 'side', 'order_type', 'time_in_force', 'quantity',
#                    'price', 'avg_price', 'status', 'filled_qty', 'total_qty',
#                    'timestamp_ms', 'usd_value', 'datetime']
#     liq_data.columns = column_names[:len(liq_data.columns)]
# 
# # Convert to proper types
# liq_data['datetime'] = pd.to_datetime(liq_data['datetime'])
# liq_data['usd_value'] = pd.to_numeric(liq_data['usd_value'], errors='coerce')
# liq_data['price'] = pd.to_numeric(liq_data['price'], errors='coerce')
# 
# # Sort by datetime
# liq_data = liq_data.sort_values('datetime')
# 
# print(f"📊 Total liquidations: {len(liq_data):,}")
# print(f"📅 Date range: {liq_data['datetime'].min()} → {liq_data['datetime'].max()}")
# 
# # Create hourly aggregated data for backtesting
# print("\n🔧 Creating hourly aggregated liquidation data...")
# 
# # Group by hour and aggregate liquidations
# liq_data['hour'] = liq_data['datetime'].dt.floor('H')
# 
# # Aggregate by hour
# hourly_data = []
# 
# for hour in pd.date_range(start=liq_data['hour'].min(), end=liq_data['hour'].max(), freq='H'):
#     hour_liqs = liq_data[liq_data['hour'] == hour]
# 
#     if len(hour_liqs) > 0:
#         # Calculate liquidation metrics
#         long_liqs = hour_liqs[hour_liqs['side'].str.upper() == 'BUY']
#         short_liqs = hour_liqs[hour_liqs['side'].str.upper() == 'SELL']
# 
#         long_volume = long_liqs['usd_value'].sum()
#         short_volume = short_liqs['usd_value'].sum()
#         total_volume = long_volume + short_volume
# 
#         # Use average price from liquidations as proxy for market price
#         avg_price = hour_liqs['price'].mean()
# 
#         # Create OHLCV-like data from liquidations
#         hourly_data.append({
#             'datetime': hour,
#             'Open': avg_price,
#             'High': hour_liqs['price'].max(),
#             'Low': hour_liqs['price'].min(),
#             'Close': avg_price,
#             'Volume': total_volume,
#             'long_liq_volume': long_volume,
#             'short_liq_volume': short_volume,
#             'net_liq_volume': short_volume - long_volume,  # Positive = more shorts liquidated
#             'total_liq_count': len(hour_liqs),
#             'long_liq_count': len(long_liqs),
#             'short_liq_count': len(short_liqs)
#         })
# 
# # Convert to DataFrame
# data = pd.DataFrame(hourly_data)
# data = data.set_index('datetime')
# 
# # Fill missing hours with forward fill
# full_range = pd.date_range(start=data.index.min(), end=data.index.max(), freq='H')
# data = data.reindex(full_range)
# data[['Open', 'High', 'Low', 'Close']] = data[['Open', 'High', 'Low', 'Close']].ffill()
# data[['Volume', 'long_liq_volume', 'short_liq_volume', 'net_liq_volume']] = data[['Volume', 'long_liq_volume', 'short_liq_volume', 'net_liq_volume']].fillna(0)
# data[['total_liq_count', 'long_liq_count', 'short_liq_count']] = data[['total_liq_count', 'long_liq_count', 'short_liq_count']].fillna(0)
# 
# print(f"✅ Created {len(data)} hourly data points")

# Data configuration
# Load preprocessed BTC data - choose between 1-minute and 5-minute
# Just comment/uncomment to switch between timeframes

# Option 1: 1-minute data
# data_path = '/Users/md/Dropbox/dev/github/moon-dev-trading-bots/data/moondev_api/liq_data_BTC_1m_ohlcv.csv'
# timeframe = '1-minute'

# # Option 2: 5-minute data (currently active)
data_path = '/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/quant/liq_data_BTC_5m_ohlcv.csv'
timeframe = '5-minute'

print(f"📊 Loading preprocessed {timeframe} BTC liquidation data...")
data = pd.read_csv(data_path, index_col='datetime', parse_dates=True)

# Data already has proper columns from preprocessing
print(f"✅ Loaded {len(data):,} {timeframe} bars")
print(f"📊 Data columns: {list(data.columns)}")

# Map liquidation columns to match strategy expectations
if 'long_liquidations' in data.columns and 'short_liquidations' in data.columns:
    data['long_liq_volume'] = data['long_liquidations']
    data['short_liq_volume'] = data['short_liquidations']
    data['net_liq_volume'] = data['short_liquidations'] - data['long_liquidations']
    data['total_liq_count'] = data['liquidation_count'] if 'liquidation_count' in data.columns else 0
    data['long_liq_count'] = (data['long_liquidations'] > 0).astype(int)
    data['short_liq_count'] = (data['short_liquidations'] > 0).astype(int)
else:
    # Create empty liquidation columns if they don't exist
    print("⚠️ Warning: Liquidation columns not found, creating empty columns")
    data['long_liq_volume'] = 0
    data['short_liq_volume'] = 0
    data['net_liq_volume'] = 0
    data['total_liq_count'] = 0
    data['long_liq_count'] = 0
    data['short_liq_count'] = 0

class PureLiquidationMomentumStrategy(Strategy):
    """
    Pure Liquidation MOMENTUM Strategy

    Entry Logic:
    - SELL when long liquidation volume exceeds threshold (follow the cascade down)
    - BUY when short liquidation volume exceeds threshold (follow the cascade up)

    Exit Logic:
    - Take profit at X%
    - Stop loss at Y%
    - Time-based exit after max_hold_hours
    """

    # Optimizable parameters
    liquidation_threshold = 925_000  # Minimum USD liquidation volume to trigger trade
    take_profit = 0.01  # 1.5% take profit
    stop_loss = 0.015     # 1% stop loss
    max_hold_hours = 2  # Maximum holding period

    # Position sizing
    position_size = 0.95  # Use 95% of available capital

    def init(self):
        """Initialize strategy indicators"""
        #print("🔧 Initializing Pure Liquidation Momentum Strategy...")

        # Store liquidation volumes as indicators
        self.long_liq_volume = self.I(lambda: self.data.long_liq_volume)
        self.short_liq_volume = self.I(lambda: self.data.short_liq_volume)
        self.net_liq_volume = self.I(lambda: self.data.net_liq_volume)

        # Calculate rolling averages for context
        self.avg_long_liq = self.I(lambda x: pd.Series(x).rolling(24).mean(), self.long_liq_volume)
        self.avg_short_liq = self.I(lambda x: pd.Series(x).rolling(24).mean(), self.short_liq_volume)

        #print("✅ Strategy initialized!")

    def next(self):
        """Main strategy logic - MOMENTUM approach"""

        # Get current liquidation volumes
        current_long_liq = self.long_liq_volume[-1]
        current_short_liq = self.short_liq_volume[-1]
        current_price = self.data.Close[-1]

        # Skip if no liquidations
        if current_long_liq == 0 and current_short_liq == 0:
            return

        # Entry logic - MOMENTUM (INVERSE of contrarian)
        if not self.position:

            # SELL when longs are liquidated (follow the cascade down)
            if current_long_liq >= self.liquidation_threshold:
                sl_price = current_price * (1 + self.stop_loss)
                tp_price = current_price * (1 - self.take_profit)

                self.sell(size=self.position_size, sl=sl_price, tp=tp_price)

            # BUY when shorts are liquidated (follow the cascade up)
            elif current_short_liq >= self.liquidation_threshold:
                sl_price = current_price * (1 - self.stop_loss)
                tp_price = current_price * (1 + self.take_profit)

                self.buy(size=self.position_size, sl=sl_price, tp=tp_price)

        # Exit logic - time-based exit
        else:
            if len(self.trades) > 0:
                entry_time = self.trades[-1].entry_time
                current_time = self.data.index[-1]
                hours_held = (current_time - entry_time).total_seconds() / 3600

                if hours_held >= self.max_hold_hours:
                    self.position.close()


# Run backtest with baseline parameters
print("\n" + "="*70)
print("RUNNING BASELINE BACKTEST (Non-Optimized)")
print("="*70)

if len(data) > 100:
    bt = Backtest(
        data[['Open', 'High', 'Low', 'Close', 'Volume', 'long_liq_volume', 'short_liq_volume', 'net_liq_volume']],
        PureLiquidationMomentumStrategy,
        cash=1000000,
        commission=0.001
    )

    # Run baseline
    baseline_stats = bt.run()

    print(f"\n📊 BASELINE RESULTS (MOMENTUM):")
    print(f"Liquidation Threshold: ${PureLiquidationMomentumStrategy.liquidation_threshold:,}")
    print(f"Take Profit: {PureLiquidationMomentumStrategy.take_profit*100:.1f}%")
    print(f"Stop Loss: {PureLiquidationMomentumStrategy.stop_loss*100:.1f}%")
    print(f"Max Hold: {PureLiquidationMomentumStrategy.max_hold_hours} hours")
    print("-" * 50)
    print(f"Total Trades: {baseline_stats['# Trades']}")
    print(f"Win Rate: {baseline_stats['Win Rate [%]']:.2f}%")
    print(f"Return: {baseline_stats['Return [%]']:.2f}%")
    print(f"Sharpe: {baseline_stats['Sharpe Ratio']:.2f}")
    print(f"Max Drawdown: {baseline_stats['Max. Drawdown [%]']:.2f}%")

    print("\n📈 FULL BASELINE STATS:")
    print("="*70)
    print(baseline_stats)

    # Run optimization automatically
    print("\n" + "="*70)
    print("RUNNING OPTIMIZATION")
    print("="*70)
    print("🔄 Optimizing parameters... This may take a few minutes...")

    # Run the optimizer with error handling
    try:
        optimization_results = bt.optimize(
            liquidation_threshold=range(100000, 1000000, 25_000),  # $100k to $2M in $100k steps
            take_profit=[0.01, 0.015, 0.02],  # 1% to 3%
            stop_loss=[0.01, 0.015, 0.02],  # 0.5% to 2%
            max_hold_hours=[2,4],  # 6 to 48 hours
            maximize='Sharpe Ratio',
            # Remove constraint to allow all parameter combinations
            return_heatmap=False  # Disable heatmap to avoid potential issues
        )

        print("\n✨ OPTIMIZED RESULTS:")
        print("="*70)
        print(optimization_results)

        # Extract and display optimized parameters
        print("\n🎯 OPTIMIZED PARAMETERS:")
        print("-" * 50)
        print(f"Liquidation Threshold: ${optimization_results._strategy.liquidation_threshold:,}")
        print(f"Take Profit: {optimization_results._strategy.take_profit*100:.1f}%")
        print(f"Stop Loss: {optimization_results._strategy.stop_loss*100:.1f}%")
        print(f"Max Hold Hours: {optimization_results._strategy.max_hold_hours}")

        # Compare baseline vs optimized
        print("\n📊 IMPROVEMENT SUMMARY:")
        print("-" * 50)
        baseline_return = baseline_stats['Return [%]']
        optimized_return = optimization_results['Return [%]']
        print(f"Baseline Return: {baseline_return:.2f}%")
        print(f"Optimized Return: {optimized_return:.2f}%")
        print(f"Improvement: {optimized_return - baseline_return:.2f}%")

    except Exception as e:
        print(f"\n⚠️ Optimization failed: {str(e)}")
        print("This may happen if there aren't enough trades with the current parameter ranges.")
        print("Try adjusting the parameter ranges or using more data.")

else:
    print("❌ Insufficient data for backtesting")