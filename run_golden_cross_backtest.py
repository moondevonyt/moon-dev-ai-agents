"""
🌙 Moon Dev - Golden Cross Backtest
KLASSIEKE BEWEZEN STRATEGIE

Strategie:
- Buy: 50 SMA kruist boven 200 SMA (Golden Cross)
- Sell: 50 SMA kruist onder 200 SMA (Death Cross)
- 100% position sizing voor long-term holding
- Geen stop loss (trend following)

Deze strategie is simpel maar effectief voor Bitcoin bull markets.
"""

from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import pandas as pd
import numpy as np

def calculate_sma(prices, period):
    """Calculate Simple Moving Average"""
    return pd.Series(prices).rolling(period).mean().values

# Load data
print("📊 Loading BTC data...")
data = pd.read_csv('src/data/rbi/BTC-USD-15m.csv')
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data = data.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'})
data['datetime'] = pd.to_datetime(data['datetime'])
data = data.set_index('datetime')

print(f"✅ Loaded: {len(data)} rows")

# Resample to 1H for cleaner signals
print("🔄 Resampling to 1H timeframe...")
data = data.resample('1h').agg({
    'Open': 'first',
    'High': 'max',
    'Low': 'min',
    'Close': 'last',
    'Volume': 'sum'
}).dropna()

print(f"✅ After resampling: {len(data)} rows")
print(f"📅 Period: {data.index[0]} to {data.index[-1]}\n")

class GoldenCross(Strategy):
    # Parameters
    fast_period = 50
    slow_period = 200

    def init(self):
        close = self.data.Close

        # Moving averages
        self.sma_fast = self.I(calculate_sma, close, self.fast_period)
        self.sma_slow = self.I(calculate_sma, close, self.slow_period)

        print("🌙 Golden Cross Strategy Initialized! ✨")
        print(f"   Fast SMA: {self.fast_period}")
        print(f"   Slow SMA: {self.slow_period}")
        print(f"   Strategy: Buy on Golden Cross, Sell on Death Cross\n")

    def next(self):
        # Skip if not enough data
        if np.isnan(self.sma_slow[-1]):
            return

        # Golden Cross: Buy signal
        if crossover(self.sma_fast, self.sma_slow):
            if not self.position:
                self.buy()  # Buy with all available capital
                print(f"✅ GOLDEN CROSS! Buying at ${self.data.Close[-1]:.2f}")

        # Death Cross: Sell signal
        elif crossover(self.sma_slow, self.sma_fast):
            if self.position:
                self.position.close()
                print(f"❌ DEATH CROSS! Selling at ${self.data.Close[-1]:.2f}")

# Run backtest
print("🚀 Running Golden Cross Backtest...\n")
bt = Backtest(data, GoldenCross, cash=100000, commission=.002)
stats = bt.run()

print("\n" + "=" * 70)
print("📊 GOLDEN CROSS BACKTEST RESULTS (1H)")
print("=" * 70)
print(f"Strategy:            50/200 SMA Crossover")
print(f"Initial Capital:     ${100000:,.2f}")
print(f"Final Portfolio:     ${stats['Equity Final [$]']:,.2f}")
print(f"Return:              {stats['Return [%]']:.2f}%")
print(f"Buy & Hold Return:   {stats['Buy & Hold Return [%]']:.2f}%")
print(f"Max Drawdown:        {stats['Max. Drawdown [%]']:.2f}%")
print(f"Sharpe Ratio:        {stats['Sharpe Ratio']:.2f}")
print(f"# Trades:            {stats['# Trades']}")
print(f"Win Rate:            {stats['Win Rate [%]']:.2f}%")
print(f"Avg Trade:           {stats['Avg. Trade [%]']:.2f}%")
print(f"Max Trade Duration:  {stats['Max. Trade Duration']}")
print("=" * 70)

profit = stats['Equity Final [$]'] - 100000
alpha = stats['Return [%]'] - stats['Buy & Hold Return [%]']

if stats['Return [%]'] > 0:
    print(f"\n✅ WINNENDE STRATEGIE!")
    print(f"   💰 Profit: ${profit:,.2f}")
    print(f"   📈 Total Return: {stats['Return [%]']:.2f}%")
else:
    print(f"\n❌ Verliezende strategie")
    print(f"   💸 Loss: ${profit:,.2f}")

print(f"\n📊 Performance vs Buy & Hold:")
if alpha > 0:
    print(f"   ✅ Outperformance: +{alpha:.2f}%")
elif alpha > -10:
    print(f"   ⚠️  Slightly underperforming: {alpha:.2f}%")
else:
    print(f"   ❌ Significantly underperforming: {alpha:.2f}%")

print(f"\n💡 Analysis:")
print(f"   • Number of Golden Crosses: {stats['# Trades'] // 2 if stats['# Trades'] > 0 else 0}")
print(f"   • Average holding period: {stats['Avg. Trade Duration']}")
print(f"   • Max drawdown: {stats['Max. Drawdown [%]']:.2f}%")

if stats['# Trades'] <= 5:
    print(f"\n✨ Low trade frequency = trend following strategy")
    print(f"   This is normal for Golden Cross - few but high-conviction trades")
