"""
🌙 Moon Dev's ADX + VWAP Backtest Strategy
Built with love by Moon Dev 🚀

Strategy Logic:
- Uses ADX to measure trend strength
- Uses VWAP to determine price position relative to average
- LONG: Price above VWAP + Strong ADX (trending up)
- SHORT: Price below VWAP + Strong ADX (trending down)
"""

import pandas as pd
import numpy as np
import talib
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from pathlib import Path
from glob import glob

# Get the most recent HYPE data file
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "src" / "data" / "hyperliquid_data"

# Find the most recent HYPE 1d file
hype_files = glob(str(DATA_DIR / "HYPE_1d_*.csv"))
if not hype_files:
    raise FileNotFoundError("No HYPE 1d data files found! Run hyperliquid_data.py first.")

# Get the most recent file
data_path = max(hype_files, key=lambda x: Path(x).stat().st_mtime)
print(f"🌙 Moon Dev loading data from: {data_path}")

# Load the data
data = pd.read_csv(data_path, parse_dates=['timestamp'])
data.set_index('timestamp', inplace=True)

# Rename columns to match backtesting.py format (needs capitalized names)
data.columns = ['Open', 'High', 'Low', 'Close', 'Volume']

print(f"📊 Loaded {len(data)} candles")
print(f"📅 Date range: {data.index.min()} to {data.index.max()}")
print(f"💰 Price range: ${data['Close'].min():.2f} - ${data['Close'].max():.2f}")


class ADX_VWAP_Strategy(Strategy):
    """
    Moon Dev's ADX + VWAP Strategy

    Parameters:
    - adx_period: Period for ADX calculation (default: 14)
    - adx_threshold: Minimum ADX value to enter trade (default: 25)
    - take_profit: Take profit percentage (default: 10%)
    - stop_loss: Stop loss percentage (default: 5%)
    """
    adx_period = 14
    adx_threshold = 25
    take_profit = 0.10  # 10%
    stop_loss = 0.05    # 5%

    def init(self):
        """Initialize indicators"""
        # Calculate ADX using TA-Lib
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, self.adx_period)

        # Calculate VWAP manually (TA-Lib doesn't have VWAP)
        # VWAP = Cumulative(Price * Volume) / Cumulative(Volume)
        typical_price = (self.data.High + self.data.Low + self.data.Close) / 3
        self.vwap = self.I(self.calculate_vwap, typical_price, self.data.Volume)

    def calculate_vwap(self, price, volume):
        """Calculate VWAP (Volume Weighted Average Price)"""
        # For daily timeframe, we calculate rolling VWAP over a period
        # Using a 20-period rolling window for VWAP
        period = 20
        pv = price * volume

        # Calculate rolling sum
        rolling_pv = pd.Series(pv).rolling(window=period, min_periods=1).sum()
        rolling_v = pd.Series(volume).rolling(window=period, min_periods=1).sum()

        vwap = rolling_pv / rolling_v
        return vwap.values

    def next(self):
        """Execute strategy logic on each candle"""
        # Need enough data for indicators
        if len(self.data) < self.adx_period:
            return

        current_price = self.data.Close[-1]
        current_adx = self.adx[-1]
        current_vwap = self.vwap[-1]

        # Check if we have valid indicator values
        if np.isnan(current_adx) or np.isnan(current_vwap):
            return

        # LONG Setup: Price above VWAP + Strong trend (ADX > threshold)
        if current_price > current_vwap and current_adx > self.adx_threshold and not self.position:
            # Enter long
            self.buy(
                sl=current_price * (1 - self.stop_loss),
                tp=current_price * (1 + self.take_profit)
            )

        # SHORT Setup: Price below VWAP + Strong trend (ADX > threshold)
        elif current_price < current_vwap and current_adx > self.adx_threshold and not self.position:
            # Enter short
            self.sell(
                sl=current_price * (1 + self.stop_loss),
                tp=current_price * (1 - self.take_profit)
            )


# Create and configure the backtest
print("\n🚀 Moon Dev's Backtest Starting...")
bt = Backtest(data, ADX_VWAP_Strategy, cash=100000, commission=0.002)

# Run the backtest with default parameters
print("\n" + "="*80)
print("🌙 MOON DEV'S DEFAULT PARAMETERS RESULTS 🌙")
print("="*80)
stats_default = bt.run()
print(stats_default)

# Run optimization
print("\n🔍 Moon Dev's Optimization Running...")
print("This may take a few minutes...\n")

optimization_results = bt.optimize(
    adx_period=range(10, 25, 5),  # Test ADX periods: 10, 15, 20
    adx_threshold=range(20, 35, 5),  # Test ADX thresholds: 20, 25, 30
    take_profit=[i / 100 for i in range(5, 20, 5)],  # TP: 5%, 10%, 15%
    stop_loss=[i / 100 for i in range(3, 12, 3)],    # SL: 3%, 6%, 9%
    maximize='Equity Final [$]',
    constraint=lambda param: param.adx_period > 0 and param.adx_threshold > 0
)

# Print optimization results
print("\n" + "="*80)
print("🌙 MOON DEV'S OPTIMIZED RESULTS 🌙")
print("="*80)
print(optimization_results)

print("\n" + "="*80)
print("🌙 MOON DEV'S BEST PARAMETERS 🌙")
print("="*80)
print(f"ADX Period: {optimization_results._strategy.adx_period}")
print(f"ADX Threshold: {optimization_results._strategy.adx_threshold}")
print(f"Take Profit: {optimization_results._strategy.take_profit * 100:.1f}%")
print(f"Stop Loss: {optimization_results._strategy.stop_loss * 100:.1f}%")
print("="*80)

print("\n✨ Moon Dev's backtest complete! ✨")
