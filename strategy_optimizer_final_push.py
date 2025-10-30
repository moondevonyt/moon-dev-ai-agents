"""
🌙 Moon Dev - FINAL PUSH TO 60%+
Fine-tuning the 5x Leverage EXTREME strategy

Best so far: 54.18% with EMA 20/100, 5x leverage, RSI >70
Now testing variations to push over 60%
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

# Load data
print("📊 Loading BTC data...")
data = pd.read_csv('src/data/rbi/BTC-USD-15m.csv')
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data = data.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'})
data['datetime'] = pd.to_datetime(data['datetime'])
data = data.set_index('datetime')

data = data.resample('1h').agg({
    'Open': 'first',
    'High': 'max',
    'Low': 'min',
    'Close': 'last',
    'Volume': 'sum'
}).dropna()

print(f"✅ Data loaded: {len(data)} bars (1H)")

# Fine-tuned configurations around the winner
configs = [
    # Original winner
    {
        'name': '5x EMA 20/100 RSI>70 Vol2x (ORIGINAL)',
        'fast': 20, 'slow': 100, 'ema': True, 'lev': 5.0,
        'sl': 0.01, 'tp': 0.06, 'rsi': 70, 'vol': True, 'vol_mult': 2.0,
    },

    # Variations - slightly more aggressive entries
    {
        'name': '5x EMA 20/100 RSI>68 Vol2x',
        'fast': 20, 'slow': 100, 'ema': True, 'lev': 5.0,
        'sl': 0.01, 'tp': 0.06, 'rsi': 68, 'vol': True, 'vol_mult': 2.0,
    },

    {
        'name': '5x EMA 20/100 RSI>65 Vol1.8x',
        'fast': 20, 'slow': 100, 'ema': True, 'lev': 5.0,
        'sl': 0.01, 'tp': 0.06, 'rsi': 65, 'vol': True, 'vol_mult': 1.8,
    },

    # Higher take profit
    {
        'name': '5x EMA 20/100 RSI>70 TP7%',
        'fast': 20, 'slow': 100, 'ema': True, 'lev': 5.0,
        'sl': 0.01, 'tp': 0.07, 'rsi': 70, 'vol': True, 'vol_mult': 2.0,
    },

    # Different MA periods
    {
        'name': '5x EMA 18/90 RSI>70 Vol2x',
        'fast': 18, 'slow': 90, 'ema': True, 'lev': 5.0,
        'sl': 0.01, 'tp': 0.06, 'rsi': 70, 'vol': True, 'vol_mult': 2.0,
    },

    {
        'name': '5x EMA 22/110 RSI>70 Vol2x',
        'fast': 22, 'slow': 110, 'ema': True, 'lev': 5.0,
        'sl': 0.01, 'tp': 0.06, 'rsi': 70, 'vol': True, 'vol_mult': 2.0,
    },

    # 6x leverage (more aggressive)
    {
        'name': '6x EMA 20/100 RSI>70 Vol2x',
        'fast': 20, 'slow': 100, 'ema': True, 'lev': 6.0,
        'sl': 0.008, 'tp': 0.05, 'rsi': 70, 'vol': True, 'vol_mult': 2.0,
    },

    # Tighter SL, higher TP
    {
        'name': '5x EMA 20/100 RSI>70 SL0.8% TP8%',
        'fast': 20, 'slow': 100, 'ema': True, 'lev': 5.0,
        'sl': 0.008, 'tp': 0.08, 'rsi': 70, 'vol': True, 'vol_mult': 2.0,
    },

    # Combo: lower RSI + higher vol
    {
        'name': '5x EMA 20/100 RSI>65 Vol2.5x',
        'fast': 20, 'slow': 100, 'ema': True, 'lev': 5.0,
        'sl': 0.01, 'tp': 0.06, 'rsi': 65, 'vol': True, 'vol_mult': 2.5,
    },

    # 5.5x leverage sweet spot
    {
        'name': '5.5x EMA 20/100 RSI>68 Vol2x',
        'fast': 20, 'slow': 100, 'ema': True, 'lev': 5.5,
        'sl': 0.009, 'tp': 0.055, 'rsi': 68, 'vol': True, 'vol_mult': 2.0,
    },

    # Without volume filter (more trades)
    {
        'name': '5x EMA 20/100 RSI>70 NoVol',
        'fast': 20, 'slow': 100, 'ema': True, 'lev': 5.0,
        'sl': 0.01, 'tp': 0.06, 'rsi': 70, 'vol': False, 'vol_mult': None,
    },

    # RSI 72 (ultra selective)
    {
        'name': '5x EMA 20/100 RSI>72 Vol2x',
        'fast': 20, 'slow': 100, 'ema': True, 'lev': 5.0,
        'sl': 0.01, 'tp': 0.06, 'rsi': 72, 'vol': True, 'vol_mult': 2.0,
    },
]

results = []
best_return = 0
best_config = None
target_hit = False

print("\n" + "=" * 90)
print("🎯 FINAL PUSH TO 60%+ RETURN")
print("=" * 90)
print(f"\nFine-tuning {len(configs)} variations of the 54.18% winner\n")

for i, cfg in enumerate(configs, 1):
    print(f"\n{'='*90}")
    print(f"📊 Test {i}/{len(configs)}: {cfg['name']}")
    print(f"{'='*90}")

    class FinalStrategy(Strategy):
        def init(self):
            close = self.data.Close

            if cfg['ema']:
                self.ma_fast = self.I(calculate_ema, close, cfg['fast'])
                self.ma_slow = self.I(calculate_ema, close, cfg['slow'])
            else:
                self.ma_fast = self.I(calculate_sma, close, cfg['fast'])
                self.ma_slow = self.I(calculate_sma, close, cfg['slow'])

            self.rsi = self.I(calculate_rsi, close, 14)

            if cfg['vol']:
                vol = self.data.Volume
                self.vol_avg = self.I(lambda: pd.Series(vol).rolling(20).mean().values)

        def next(self):
            if np.isnan(self.ma_slow[-1]) or np.isnan(self.rsi[-1]):
                return

            price = self.data.Close[-1]

            if not self.position:
                entry_ok = False

                # MA condition
                if crossover(self.ma_fast, self.ma_slow) or self.ma_fast[-1] > self.ma_slow[-1]:
                    entry_ok = True

                # RSI
                if self.rsi[-1] < cfg['rsi']:
                    entry_ok = False

                # Volume
                if cfg['vol'] and hasattr(self, 'vol_avg'):
                    if self.data.Volume[-1] < (self.vol_avg[-1] * cfg['vol_mult']):
                        entry_ok = False

                if entry_ok:
                    sl = price * (1 - cfg['sl'])
                    tp = price * (1 + cfg['tp'])
                    self.buy(size=cfg['lev'], sl=sl, tp=tp)

            else:
                if crossover(self.ma_slow, self.ma_fast):
                    self.position.close()

    try:
        bt = Backtest(data, FinalStrategy, cash=100000, commission=.002)
        stats = bt.run()

        result = {
            'name': cfg['name'],
            'return': stats['Return [%]'],
            'buy_hold': stats['Buy & Hold Return [%]'],
            'trades': stats['# Trades'],
            'win_rate': stats['Win Rate [%]'],
            'max_dd': stats['Max. Drawdown [%]'],
            'sharpe': stats['Sharpe Ratio'],
            'final_equity': stats['Equity Final [$]'],
            'avg_trade': stats['Avg. Trade [%]'],
            'leverage': cfg['lev'],
        }
        results.append(result)

        profit = result['final_equity'] - 100000

        print(f"\n   📈 Return:        {result['return']:.2f}%")
        print(f"      Profit:        ${profit:,.2f}")
        print(f"      # Trades:      {result['trades']}")
        print(f"      Win Rate:      {result['win_rate']:.2f}%")
        print(f"      Max DD:        {result['max_dd']:.2f}%")
        print(f"      Sharpe:        {result['sharpe']:.2f}")

        if result['return'] > best_return:
            best_return = result['return']
            best_config = result

        if result['return'] >= 60.0:
            print(f"\n   🎉🎉🎉 TARGET ACHIEVED! {result['return']:.2f}% >= 60%")
            target_hit = True
            break

    except Exception as e:
        print(f"   ❌ Error: {str(e)}")

    time.sleep(0.1)

# Results
print("\n\n" + "=" * 90)
print("🏁 FINAL OPTIMIZATION COMPLETE")
print("=" * 90)

results.sort(key=lambda x: x['return'], reverse=True)

print(f"\n{'Rank':<6} {'Strategy':<45} {'Return':<12} {'MaxDD':<10} {'Sharpe':<8}")
print("-" * 90)

for rank, r in enumerate(results, 1):
    medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else "  "
    target = "🎯" if r['return'] >= 60 else ""
    print(f"{medal} #{rank:<4} {r['name']:<43} {r['return']:>9.2f}%  {r['max_dd']:>8.2f}%  {r['sharpe']:>6.2f} {target}")

if best_config:
    print("\n" + "=" * 90)
    print("🏆 BEST STRATEGY")
    print("=" * 90)
    print(f"\nName:          {best_config['name']}")
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
    else:
        print(f"\n⚠️  Closest: {best_config['return']:.2f}% (target: 60%)")
        gap = 60.0 - best_config['return']
        print(f"    Gap: {gap:.2f}% remaining")

# Save
df = pd.DataFrame(results)
df.to_csv('final_push_results.csv', index=False)
print(f"\n✅ Results saved to: final_push_results.csv")

print("\n" + "=" * 90 + "\n")
