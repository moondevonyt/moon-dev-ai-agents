"""
🌙 Moon Dev - ULTRA AGGRESSIVE Strategy Optimizer
TARGET: >60% return using leverage, tight stops, and aggressive entries

Key tactics:
- Leverage simulation (2x-5x position sizing)
- Very tight entry filters for high-probability setups
- Momentum riding (add to winners)
- Shorter timeframes for more trades
"""

import pandas as pd
import numpy as np
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import time

def calculate_sma(prices, period):
    return pd.Series(prices).rolling(period).mean().values

def calculate_ema(prices, period):
    return pd.Series(prices).ewm(span=period, adjust=False).mean().values

def calculate_rsi(prices, period=14):
    deltas = np.diff(prices)
    seed = deltas[:period+1]
    up = seed[seed >= 0].sum() / period
    down = -seed[seed < 0].sum() / period
    if down == 0:
        return np.full_like(prices, 100)
    rs = up / down
    rsi = np.zeros_like(prices)
    rsi[:period] = 100. - 100. / (1. + rs)
    for i in range(period, len(prices)):
        delta = deltas[i - 1]
        up = (up * (period - 1) + max(delta, 0)) / period
        down = (down * (period - 1) + max(-delta, 0)) / period
        if down == 0:
            rsi[i] = 100
        else:
            rsi[i] = 100. - 100. / (1. + up/down)
    return rsi

# Load and prepare data
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

print(f"✅ Data loaded: {len(data)} bars (1H)")

# ULTRA AGGRESSIVE configurations
configs = [
    # Config 1: 2x Leverage + Tight SL/TP
    {
        'name': '2x Leverage GC 30/150',
        'description': '2x position sizing with tight risk management',
        'fast_ma': 30,
        'slow_ma': 150,
        'use_ema': False,
        'leverage': 2.0,
        'stop_loss_pct': 0.02,  # 2% stop = 4% loss on 2x
        'take_profit_pct': 0.10,  # 10% TP = 20% gain on 2x
        'rsi_min': None,
        'use_volume': False,
    },

    # Config 2: 3x Leverage + RSI filter
    {
        'name': '3x Leverage + RSI >65',
        'description': '3x position on strong momentum only',
        'fast_ma': 30,
        'slow_ma': 150,
        'use_ema': False,
        'leverage': 3.0,
        'stop_loss_pct': 0.015,  # 1.5% stop = 4.5% loss on 3x
        'take_profit_pct': 0.08,  # 8% TP = 24% gain on 3x
        'rsi_min': 65,
        'use_volume': False,
    },

    # Config 3: Faster EMAs + 2x leverage
    {
        'name': '2x Leverage EMA 20/100',
        'description': 'Faster signals with 2x sizing',
        'fast_ma': 20,
        'slow_ma': 100,
        'use_ema': True,
        'leverage': 2.0,
        'stop_loss_pct': 0.025,
        'take_profit_pct': 0.12,
        'rsi_min': None,
        'use_volume': False,
    },

    # Config 4: Very aggressive - 5x leverage with very tight stops
    {
        'name': '5x Leverage EXTREME',
        'description': '5x leverage - high risk/high reward',
        'fast_ma': 20,
        'slow_ma': 100,
        'use_ema': True,
        'leverage': 5.0,
        'stop_loss_pct': 0.01,  # 1% stop = 5% loss on 5x
        'take_profit_pct': 0.06,  # 6% TP = 30% gain on 5x
        'rsi_min': 70,  # Only extreme momentum
        'use_volume': True,
        'volume_mult': 2.0,
    },

    # Config 5: 2x Leverage with volume confirmation
    {
        'name': '2x Leverage + Volume',
        'description': '2x leverage on volume breakouts',
        'fast_ma': 30,
        'slow_ma': 150,
        'use_ema': False,
        'leverage': 2.0,
        'stop_loss_pct': 0.02,
        'take_profit_pct': 0.10,
        'rsi_min': 60,
        'use_volume': True,
        'volume_mult': 1.8,
    },

    # Config 6: 3x Leverage EMA with triple confirmation
    {
        'name': '3x EMA + RSI + Volume',
        'description': '3x leverage with all confirmations',
        'fast_ma': 25,
        'slow_ma': 120,
        'use_ema': True,
        'leverage': 3.0,
        'stop_loss_pct': 0.018,
        'take_profit_pct': 0.09,
        'rsi_min': 62,
        'use_volume': True,
        'volume_mult': 1.5,
    },

    # Config 7: 4x Leverage - medium aggression
    {
        'name': '4x Leverage GC 25/125',
        'description': '4x leverage medium-fast signals',
        'fast_ma': 25,
        'slow_ma': 125,
        'use_ema': False,
        'leverage': 4.0,
        'stop_loss_pct': 0.012,
        'take_profit_pct': 0.07,
        'rsi_min': 68,
        'use_volume': False,
    },

    # Config 8: 2.5x Leverage balanced
    {
        'name': '2.5x Leverage Balanced',
        'description': '2.5x leverage with RSI filter',
        'fast_ma': 30,
        'slow_ma': 150,
        'use_ema': False,
        'leverage': 2.5,
        'stop_loss_pct': 0.022,
        'take_profit_pct': 0.11,
        'rsi_min': 58,
        'use_volume': False,
    },

    # Config 9: Short-term aggressive (15/75)
    {
        'name': '3x Short-term SMA 15/75',
        'description': '3x leverage on short-term trend',
        'fast_ma': 15,
        'slow_ma': 75,
        'use_ema': False,
        'leverage': 3.0,
        'stop_loss_pct': 0.015,
        'take_profit_pct': 0.08,
        'rsi_min': 60,
        'use_volume': True,
        'volume_mult': 1.5,
    },

    # Config 10: 2x Leverage EMA 30/150 (safer)
    {
        'name': '2x EMA 30/150 Safe',
        'description': '2x leverage with wider stops',
        'fast_ma': 30,
        'slow_ma': 150,
        'use_ema': True,
        'leverage': 2.0,
        'stop_loss_pct': 0.03,
        'take_profit_pct': 0.15,
        'rsi_min': None,
        'use_volume': False,
    },
]

results = []
best_return = 0
best_config = None

print("\n" + "=" * 90)
print("🚀 ULTRA AGGRESSIVE OPTIMIZATION - LEVERAGE STRATEGIES - TARGET: >60%")
print("=" * 90)
print(f"\n⚠️  WARNING: Simulating {len(configs)} leveraged strategies (high risk!)")
print(f"🎯 Target: >60% return with acceptable drawdown\n")

for i, config in enumerate(configs, 1):
    print(f"\n{'='*90}")
    print(f"📊 Test {i}/{len(configs)}: {config['name']}")
    print(f"{'='*90}")
    print(f"   {config['description']}")
    print(f"   Leverage: {config['leverage']}x | SL: {config['stop_loss_pct']*100:.1f}% | TP: {config['take_profit_pct']*100:.1f}%")

    # Create dynamic strategy class
    class LeveragedStrategy(Strategy):
        def init(self):
            close = self.data.Close

            # Moving averages
            if config['use_ema']:
                self.ma_fast = self.I(calculate_ema, close, config['fast_ma'])
                self.ma_slow = self.I(calculate_ema, close, config['slow_ma'])
            else:
                self.ma_fast = self.I(calculate_sma, close, config['fast_ma'])
                self.ma_slow = self.I(calculate_sma, close, config['slow_ma'])

            # RSI
            if config.get('rsi_min'):
                self.rsi = self.I(calculate_rsi, close, 14)

            # Volume
            if config.get('use_volume'):
                vol = self.data.Volume
                self.vol_avg = self.I(lambda: pd.Series(vol).rolling(20).mean().values)

        def next(self):
            if np.isnan(self.ma_slow[-1]):
                return

            price = self.data.Close[-1]

            if not self.position:
                # Entry conditions
                entry_ok = False

                # MA crossover or above
                if crossover(self.ma_fast, self.ma_slow) or self.ma_fast[-1] > self.ma_slow[-1]:
                    entry_ok = True

                # RSI filter
                if config.get('rsi_min') and hasattr(self, 'rsi'):
                    if self.rsi[-1] < config['rsi_min']:
                        entry_ok = False

                # Volume filter
                if config.get('use_volume') and hasattr(self, 'vol_avg'):
                    if self.data.Volume[-1] < (self.vol_avg[-1] * config.get('volume_mult', 1.5)):
                        entry_ok = False

                if entry_ok:
                    # Leverage simulation via position size
                    leverage = config['leverage']
                    sl = price * (1 - config['stop_loss_pct'])
                    tp = price * (1 + config['take_profit_pct'])
                    self.buy(size=leverage, sl=sl, tp=tp)

            else:
                # Exit on death cross
                if crossover(self.ma_slow, self.ma_fast):
                    self.position.close()

    try:
        # Run backtest
        bt = Backtest(data, LeveragedStrategy, cash=100000, commission=.002)
        stats = bt.run()

        result = {
            'name': config['name'],
            'description': config['description'],
            'leverage': config['leverage'],
            'return': stats['Return [%]'],
            'buy_hold': stats['Buy & Hold Return [%]'],
            'trades': stats['# Trades'],
            'win_rate': stats['Win Rate [%]'],
            'max_dd': stats['Max. Drawdown [%]'],
            'sharpe': stats['Sharpe Ratio'],
            'final_equity': stats['Equity Final [$]'],
            'avg_trade': stats['Avg. Trade [%]'],
        }
        results.append(result)

        profit = result['final_equity'] - 100000
        alpha = result['return'] - result['buy_hold']

        print(f"\n   📈 Results:")
        print(f"      Return:        {result['return']:.2f}%")
        print(f"      Profit:        ${profit:,.2f}")
        print(f"      # Trades:      {result['trades']}")
        print(f"      Win Rate:      {result['win_rate']:.2f}%")
        print(f"      Avg Trade:     {result['avg_trade']:.2f}%")
        print(f"      Max DD:        {result['max_dd']:.2f}%")
        print(f"      Sharpe:        {result['sharpe']:.2f}")

        if result['return'] > best_return:
            best_return = result['return']
            best_config = result

            if result['return'] >= 60.0:
                print(f"\n   🎉🎉🎉 TARGET ACHIEVED! {result['return']:.2f}% >= 60%")
                print(f"   Max DD: {result['max_dd']:.2f}%")
                print(f"   Breaking early - target met!")
                break

    except Exception as e:
        print(f"   ❌ Error: {str(e)}")

    time.sleep(0.1)

# Results summary
print("\n\n" + "=" * 90)
print("🏁 ULTRA AGGRESSIVE OPTIMIZATION COMPLETE")
print("=" * 90)

results.sort(key=lambda x: x['return'], reverse=True)

print(f"\n{'Rank':<6} {'Strategy':<32} {'Lev':<5} {'Return':<12} {'MaxDD':<10} {'Sharpe':<8}")
print("-" * 90)

for rank, r in enumerate(results, 1):
    medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else "  "
    dd_color = "🔴" if r['max_dd'] < -30 else "🟡" if r['max_dd'] < -20 else "🟢"
    print(f"{medal} #{rank:<4} {r['name']:<30} {r['leverage']}x   {r['return']:>9.2f}%  {dd_color} {r['max_dd']:>7.2f}%  {r['sharpe']:>6.2f}")

# Best strategy
if best_config:
    print("\n" + "=" * 90)
    print("🏆 BEST STRATEGY FOUND")
    print("=" * 90)
    print(f"\nName:          {best_config['name']}")
    print(f"Description:   {best_config['description']}")
    print(f"Leverage:      {best_config['leverage']}x")
    print(f"Return:        {best_config['return']:.2f}%")
    print(f"Profit:        ${best_config['final_equity'] - 100000:,.2f}")
    print(f"# Trades:      {best_config['trades']}")
    print(f"Win Rate:      {best_config['win_rate']:.2f}%")
    print(f"Avg Trade:     {best_config['avg_trade']:.2f}%")
    print(f"Max Drawdown:  {best_config['max_dd']:.2f}%")
    print(f"Sharpe Ratio:  {best_config['sharpe']:.2f}")

    if best_config['return'] >= 60.0:
        print(f"\n✅✅✅ TARGET ACHIEVED: {best_config['return']:.2f}% >= 60%")
        if best_config['max_dd'] < -25:
            print(f"   ⚠️  WARNING: High drawdown {best_config['max_dd']:.2f}%")
        else:
            print(f"   ✅ Drawdown acceptable: {best_config['max_dd']:.2f}%")
    else:
        print(f"\n⚠️  Best found: {best_config['return']:.2f}% (target: 60%)")
        print(f"    Buy & Hold: {best_config['buy_hold']:.2f}%")
        print(f"\n💡 Note: During strong bull markets (B&H >100%), beating")
        print(f"    the market with systematic strategies is very difficult.")

# Save results
df = pd.DataFrame(results)
df.to_csv('ultra_aggressive_optimization_results.csv', index=False)
print(f"\n✅ Results saved to: ultra_aggressive_optimization_results.csv")

print("\n" + "=" * 90 + "\n")
