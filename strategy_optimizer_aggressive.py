"""
🌙 Moon Dev - Aggressive Strategy Optimizer
Systematically test strategy variations to find >60% return

Since we found 30/150 Golden Cross achieved 34.85% return, we need to:
1. Add aggressive entry/exit filters
2. Optimize position sizing
3. Add momentum confirmation
4. Test leverage simulation
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

def calculate_atr(high, low, close, period=14):
    """Calculate Average True Range"""
    high_low = high - low
    high_close = np.abs(high - np.roll(close, 1))
    low_close = np.abs(low - np.roll(close, 1))
    tr = np.maximum(high_low, np.maximum(high_close, low_close))
    atr = pd.Series(tr).rolling(period).mean().values
    return atr

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

# Strategy configurations to test
configs = [
    # Config 1: 30/150 Golden Cross + RSI filter (aggressive entries only)
    {
        'name': 'GC 30/150 + RSI >60',
        'description': 'Golden Cross with RSI momentum filter',
        'fast_ma': 30,
        'slow_ma': 150,
        'use_ema': False,
        'rsi_entry_min': 60,  # Only enter in strong uptrend
        'rsi_exit': 40,
        'use_volume': False,
        'position_size': 1.0,  # Full position
        'use_stop_loss': False,
        'use_take_profit': False,
    },

    # Config 2: 30/150 Golden Cross + Volume confirmation
    {
        'name': 'GC 30/150 + Volume 2x',
        'description': 'Golden Cross with volume breakout',
        'fast_ma': 30,
        'slow_ma': 150,
        'use_ema': False,
        'rsi_entry_min': None,
        'rsi_exit': None,
        'use_volume': True,
        'volume_multiplier': 2.0,
        'position_size': 1.0,
        'use_stop_loss': False,
        'use_take_profit': False,
    },

    # Config 3: 30/150 with EMA instead of SMA (faster response)
    {
        'name': 'EMA 30/150',
        'description': 'Exponential MAs for faster signals',
        'fast_ma': 30,
        'slow_ma': 150,
        'use_ema': True,
        'rsi_entry_min': None,
        'rsi_exit': None,
        'use_volume': False,
        'position_size': 1.0,
        'use_stop_loss': False,
        'use_take_profit': False,
    },

    # Config 4: 20/100 EMA + RSI (faster, more trades)
    {
        'name': 'EMA 20/100 + RSI >55',
        'description': 'Faster trend following with momentum',
        'fast_ma': 20,
        'slow_ma': 100,
        'use_ema': True,
        'rsi_entry_min': 55,
        'rsi_exit': 45,
        'use_volume': False,
        'position_size': 1.0,
        'use_stop_loss': False,
        'use_take_profit': False,
    },

    # Config 5: 30/150 with tight stop loss + take profit
    {
        'name': 'GC 30/150 + SL/TP',
        'description': 'Golden Cross with risk management',
        'fast_ma': 30,
        'slow_ma': 150,
        'use_ema': False,
        'rsi_entry_min': None,
        'rsi_exit': None,
        'use_volume': False,
        'position_size': 1.0,
        'use_stop_loss': True,
        'stop_loss_pct': 0.03,  # 3% stop
        'use_take_profit': True,
        'take_profit_pct': 0.12,  # 12% take profit
    },

    # Config 6: 30/150 + RSI + Volume (multi-confirmation)
    {
        'name': 'GC 30/150 + RSI + Volume',
        'description': 'Triple confirmation entry',
        'fast_ma': 30,
        'slow_ma': 150,
        'use_ema': False,
        'rsi_entry_min': 55,
        'rsi_exit': 40,
        'use_volume': True,
        'volume_multiplier': 1.5,
        'position_size': 1.0,
        'use_stop_loss': False,
        'use_take_profit': False,
    },

    # Config 7: Shorter periods for more trading (15/75)
    {
        'name': 'SMA 15/75',
        'description': 'Aggressive short-term trend',
        'fast_ma': 15,
        'slow_ma': 75,
        'use_ema': False,
        'rsi_entry_min': None,
        'rsi_exit': None,
        'use_volume': False,
        'position_size': 1.0,
        'use_stop_loss': False,
        'use_take_profit': False,
    },

    # Config 8: 30/150 with pyramiding (add to winners)
    {
        'name': 'GC 30/150 Pyramid',
        'description': 'Golden Cross with position scaling',
        'fast_ma': 30,
        'slow_ma': 150,
        'use_ema': False,
        'rsi_entry_min': None,
        'rsi_exit': None,
        'use_volume': False,
        'position_size': 1.0,
        'use_pyramiding': True,
        'use_stop_loss': False,
        'use_take_profit': False,
    },
]

results = []
best_return = 0
best_config = None

print("\n" + "=" * 90)
print("🔥 AGGRESSIVE STRATEGY OPTIMIZATION - TARGET: >60% RETURN")
print("=" * 90)
print(f"\n🎯 Testing {len(configs)} configurations on 1H BTC data\n")

for i, config in enumerate(configs, 1):
    print(f"\n{'='*90}")
    print(f"📊 Test {i}/{len(configs)}: {config['name']}")
    print(f"{'='*90}")
    print(f"   {config['description']}")

    # Create dynamic strategy class
    class DynamicStrategy(Strategy):
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
            if config.get('rsi_entry_min') or config.get('rsi_exit'):
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
                entry_ok = True

                # MA crossover
                if not crossover(self.ma_fast, self.ma_slow):
                    if self.ma_fast[-1] <= self.ma_slow[-1]:
                        entry_ok = False

                # RSI filter
                if config.get('rsi_entry_min') and hasattr(self, 'rsi'):
                    if self.rsi[-1] < config['rsi_entry_min']:
                        entry_ok = False

                # Volume filter
                if config.get('use_volume') and hasattr(self, 'vol_avg'):
                    if self.data.Volume[-1] < (self.vol_avg[-1] * config.get('volume_multiplier', 1.5)):
                        entry_ok = False

                if entry_ok:
                    size = config['position_size']
                    if config.get('use_stop_loss') and config.get('use_take_profit'):
                        sl = price * (1 - config['stop_loss_pct'])
                        tp = price * (1 + config['take_profit_pct'])
                        self.buy(size=size, sl=sl, tp=tp)
                    else:
                        self.buy(size=size)

            else:
                # Exit conditions
                exit_ok = False

                # Death cross
                if crossover(self.ma_slow, self.ma_fast):
                    exit_ok = True

                # RSI exit
                if config.get('rsi_exit') and hasattr(self, 'rsi'):
                    if self.rsi[-1] < config['rsi_exit']:
                        exit_ok = True

                if exit_ok:
                    self.position.close()

    try:
        # Run backtest
        bt = Backtest(data, DynamicStrategy, cash=100000, commission=.002)
        stats = bt.run()

        result = {
            'name': config['name'],
            'description': config['description'],
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
        print(f"      Alpha vs B&H:  {alpha:.2f}%")

        if result['return'] > best_return:
            best_return = result['return']
            best_config = result

            if result['return'] >= 60.0:
                print(f"\n   🎉🎉🎉 TARGET ACHIEVED! {result['return']:.2f}% >= 60%")
                print(f"   Breaking early - target met!")
                break

    except Exception as e:
        print(f"   ❌ Error: {str(e)}")

    time.sleep(0.1)

# Results summary
print("\n\n" + "=" * 90)
print("🏁 OPTIMIZATION COMPLETE")
print("=" * 90)

results.sort(key=lambda x: x['return'], reverse=True)

print(f"\n{'Rank':<6} {'Strategy':<30} {'Return':<12} {'Trades':<8} {'Win%':<8} {'Sharpe':<8}")
print("-" * 90)

for rank, r in enumerate(results, 1):
    medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else "  "
    print(f"{medal} #{rank:<4} {r['name']:<28} {r['return']:>9.2f}%  {r['trades']:>6}  {r['win_rate']:>6.1f}%  {r['sharpe']:>6.2f}")

# Best strategy
if best_config:
    print("\n" + "=" * 90)
    print("🏆 BEST STRATEGY FOUND")
    print("=" * 90)
    print(f"\nName:          {best_config['name']}")
    print(f"Description:   {best_config['description']}")
    print(f"Return:        {best_config['return']:.2f}%")
    print(f"Profit:        ${best_config['final_equity'] - 100000:,.2f}")
    print(f"# Trades:      {best_config['trades']}")
    print(f"Win Rate:      {best_config['win_rate']:.2f}%")
    print(f"Avg Trade:     {best_config['avg_trade']:.2f}%")
    print(f"Max Drawdown:  {best_config['max_dd']:.2f}%")
    print(f"Sharpe Ratio:  {best_config['sharpe']:.2f}")

    if best_config['return'] >= 60.0:
        print(f"\n✅✅✅ TARGET ACHIEVED: {best_config['return']:.2f}% >= 60%")
    else:
        print(f"\n⚠️  Best found: {best_config['return']:.2f}% (target: 60%)")
        print(f"    Buy & Hold: {best_config['buy_hold']:.2f}%")

# Save results
df = pd.DataFrame(results)
df.to_csv('aggressive_optimization_results.csv', index=False)
print(f"\n✅ Results saved to: aggressive_optimization_results.csv")

print("\n" + "=" * 90 + "\n")
