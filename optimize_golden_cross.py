"""
🌙 Moon Dev - Golden Cross Optimization
Test meerdere MA combinaties om de beste te vinden

MA Combinaties:
- 10/50: Zeer responsive, meer trades
- 20/100: Responsive, moderate trades
- 30/150: Balanced
- 50/200: Klassieke Golden Cross (baseline)
- 100/300: Conservatief, minder trades
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

# Resample to 1H
data = data.resample('1h').agg({
    'Open': 'first',
    'High': 'max',
    'Low': 'min',
    'Close': 'last',
    'Volume': 'sum'
}).dropna()

print(f"✅ Data: {len(data)} rows, {data.index[0]} to {data.index[-1]}\n")

class GoldenCrossOptimized(Strategy):
    # Parameters that will be optimized
    fast_period = 50
    slow_period = 200

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

# Test configurations
configs = [
    (10, 50, "Zeer Responsive"),
    (20, 100, "Responsive"),
    (30, 150, "Balanced"),
    (50, 200, "Klassiek (Baseline)"),
    (100, 300, "Conservatief")
]

results = []

print("=" * 80)
print("🔬 GOLDEN CROSS OPTIMIZATION - TESTING MULTIPLE CONFIGURATIONS")
print("=" * 80)

for fast, slow, description in configs:
    print(f"\n📊 Testing {fast}/{slow} SMA ({description})...")
    print("-" * 80)

    try:
        bt = Backtest(data, GoldenCrossOptimized, cash=100000, commission=.002)
        stats = bt.run(fast_period=fast, slow_period=slow)

        result = {
            'config': f"{fast}/{slow}",
            'description': description,
            'fast': fast,
            'slow': slow,
            'return': stats['Return [%]'],
            'buy_hold': stats['Buy & Hold Return [%]'],
            'trades': stats['# Trades'],
            'win_rate': stats['Win Rate [%]'],
            'max_dd': stats['Max. Drawdown [%]'],
            'sharpe': stats['Sharpe Ratio'],
            'avg_trade': stats['Avg. Trade [%]'],
            'final_equity': stats['Equity Final [$]']
        }
        results.append(result)

        profit = result['final_equity'] - 100000
        alpha = result['return'] - result['buy_hold']

        print(f"✅ Return:        {result['return']:.2f}%")
        print(f"   Profit:        ${profit:,.2f}")
        print(f"   # Trades:      {result['trades']}")
        print(f"   Win Rate:      {result['win_rate']:.2f}%")
        print(f"   Max DD:        {result['max_dd']:.2f}%")
        print(f"   Sharpe:        {result['sharpe']:.2f}")
        print(f"   Alpha vs B&H:  {alpha:.2f}%")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        continue

# Sort by return
results.sort(key=lambda x: x['return'], reverse=True)

# Display comparison table
print("\n\n" + "=" * 80)
print("📊 OPTIMIZATION RESULTS COMPARISON")
print("=" * 80)
print(f"{'Config':<12} {'Description':<20} {'Return':<10} {'Trades':<8} {'Win%':<8} {'MaxDD':<10} {'Sharpe':<8}")
print("-" * 80)

for r in results:
    status = "🏆" if r == results[0] else "✅" if r['return'] > 0 else "❌"
    print(f"{status} {r['config']:<10} {r['description']:<20} {r['return']:>7.2f}%  {r['trades']:>6}  {r['win_rate']:>6.1f}%  {r['max_dd']:>8.2f}%  {r['sharpe']:>6.2f}")

# Best strategy
best = results[0]
print("\n" + "=" * 80)
print("🏆 BEST STRATEGY")
print("=" * 80)
print(f"Configuration:    {best['config']} SMA ({best['description']})")
print(f"Return:           {best['return']:.2f}%")
print(f"Final Capital:    ${best['final_equity']:,.2f}")
print(f"Profit:           ${best['final_equity'] - 100000:,.2f}")
print(f"# Trades:         {best['trades']}")
print(f"Win Rate:         {best['win_rate']:.2f}%")
print(f"Max Drawdown:     {best['max_dd']:.2f}%")
print(f"Sharpe Ratio:     {best['sharpe']:.2f}")
print(f"Avg Trade:        {best['avg_trade']:.2f}%")

# Key insights
print("\n" + "=" * 80)
print("💡 KEY INSIGHTS")
print("=" * 80)

# Find best by different metrics
best_return = max(results, key=lambda x: x['return'])
best_sharpe = max(results, key=lambda x: x['sharpe'])
least_trades = min(results, key=lambda x: x['trades'])
best_winrate = max(results, key=lambda x: x['win_rate'])

print(f"• Highest Return:     {best_return['config']} ({best_return['return']:.2f}%)")
print(f"• Best Sharpe Ratio:  {best_sharpe['config']} ({best_sharpe['sharpe']:.2f})")
print(f"• Fewest Trades:      {least_trades['config']} ({least_trades['trades']} trades)")
print(f"• Best Win Rate:      {best_winrate['config']} ({best_winrate['win_rate']:.2f}%)")

# Save results to CSV
df_results = pd.DataFrame(results)
df_results.to_csv('golden_cross_optimization_results.csv', index=False)
print(f"\n✅ Results saved to: golden_cross_optimization_results.csv")
