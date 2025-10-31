"""
🌙 Moon Dev - Multi-Timeframe Testing
Test de beste strategie (30/150 Golden Cross) op verschillende timeframes

Timeframes:
- 1H (baseline)
- 4H (swing trading)
- 1D (position trading)
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

print(f"✅ Original data: {len(data)} rows (15m)")

class GoldenCross(Strategy):
    fast_period = 30
    slow_period = 150

    def init(self):
        close = self.data.Close
        self.sma_fast = self.I(calculate_sma, close, self.fast_period)
        self.sma_slow = self.I(calculate_sma, close, self.slow_period)

    def next(self):
        if np.isnan(self.sma_slow[-1]):
            return

        # Golden Cross: Buy
        if crossover(self.sma_fast, self.sma_slow):
            if not self.position:
                self.buy()

        # Death Cross: Sell
        elif crossover(self.sma_slow, self.sma_fast):
            if self.position:
                self.position.close()

# Timeframes to test
timeframes = [
    ('1h', '1H'),
    ('4h', '4H'),
    ('1D', 'Daily')
]

results = []

print("\n" + "=" * 80)
print("📊 MULTI-TIMEFRAME TESTING - 30/150 Golden Cross")
print("=" * 80)

for tf_code, tf_name in timeframes:
    print(f"\n📊 Testing {tf_name} Timeframe...")
    print("-" * 80)

    try:
        # Resample data
        data_resampled = data.resample(tf_code).agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        }).dropna()

        print(f"   Resampled: {len(data_resampled)} bars")
        print(f"   Period: {data_resampled.index[0]} to {data_resampled.index[-1]}")

        # Run backtest
        bt = Backtest(data_resampled, GoldenCross, cash=100000, commission=.002)
        stats = bt.run()

        result = {
            'timeframe': tf_name,
            'bars': len(data_resampled),
            'return': stats['Return [%]'],
            'buy_hold': stats['Buy & Hold Return [%]'],
            'trades': stats['# Trades'],
            'win_rate': stats['Win Rate [%]'],
            'max_dd': stats['Max. Drawdown [%]'],
            'sharpe': stats['Sharpe Ratio'],
            'avg_trade': stats['Avg. Trade [%]'],
            'final_equity': stats['Equity Final [$]'],
            'avg_duration': str(stats['Avg. Trade Duration'])
        }
        results.append(result)

        profit = result['final_equity'] - 100000
        alpha = result['return'] - result['buy_hold']

        print(f"   ✅ Return:           {result['return']:.2f}%")
        print(f"      Profit:           ${profit:,.2f}")
        print(f"      # Trades:         {result['trades']}")
        print(f"      Win Rate:         {result['win_rate']:.2f}%")
        print(f"      Max DD:           {result['max_dd']:.2f}%")
        print(f"      Sharpe:           {result['sharpe']:.2f}")
        print(f"      Avg Duration:     {result['avg_duration']}")
        print(f"      Alpha vs B&H:     {alpha:.2f}%")

    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        continue

# Sort by return
results.sort(key=lambda x: x['return'], reverse=True)

# Display comparison table
print("\n\n" + "=" * 80)
print("📊 TIMEFRAME COMPARISON - 30/150 Golden Cross")
print("=" * 80)
print(f"{'Timeframe':<12} {'Bars':<8} {'Return':<10} {'Trades':<8} {'Win%':<8} {'MaxDD':<10} {'Sharpe':<8}")
print("-" * 80)

for r in results:
    status = "🏆" if r == results[0] else "✅" if r['return'] > 0 else "❌"
    print(f"{status} {r['timeframe']:<10} {r['bars']:>6}  {r['return']:>7.2f}%  {r['trades']:>6}  {r['win_rate']:>6.1f}%  {r['max_dd']:>8.2f}%  {r['sharpe']:>6.2f}")

# Best timeframe
if results:
    best = results[0]
    print("\n" + "=" * 80)
    print("🏆 BEST TIMEFRAME")
    print("=" * 80)
    print(f"Timeframe:        {best['timeframe']}")
    print(f"# Bars:           {best['bars']}")
    print(f"Return:           {best['return']:.2f}%")
    print(f"Final Capital:    ${best['final_equity']:,.2f}")
    print(f"Profit:           ${best['final_equity'] - 100000:,.2f}")
    print(f"# Trades:         {best['trades']}")
    print(f"Win Rate:         {best['win_rate']:.2f}%")
    print(f"Avg Trade:        {best['avg_trade']:.2f}%")
    print(f"Avg Duration:     {best['avg_duration']}")
    print(f"Max Drawdown:     {best['max_dd']:.2f}%")
    print(f"Sharpe Ratio:     {best['sharpe']:.2f}")

# Key insights
print("\n" + "=" * 80)
print("💡 TIMEFRAME INSIGHTS")
print("=" * 80)

# Analysis by timeframe characteristics
for r in results:
    print(f"\n{r['timeframe']} Timeframe:")
    print(f"  • {r['bars']} bars, {r['trades']} trades")
    print(f"  • Avg hold: {r['avg_duration']}")

    if r['return'] > 10:
        print(f"  ✅ Strong performance ({r['return']:.2f}%)")
    elif r['return'] > 0:
        print(f"  ⚠️  Modest gains ({r['return']:.2f}%)")
    else:
        print(f"  ❌ Losing ({r['return']:.2f}%)")

    if r['trades'] < 10:
        print(f"  • Low frequency (long-term trend following)")
    elif r['trades'] < 30:
        print(f"  • Medium frequency (swing trading)")
    else:
        print(f"  • High frequency (active trading)")

# Save results
df_results = pd.DataFrame(results)
df_results.to_csv('multi_timeframe_results.csv', index=False)
print(f"\n✅ Results saved to: multi_timeframe_results.csv")
