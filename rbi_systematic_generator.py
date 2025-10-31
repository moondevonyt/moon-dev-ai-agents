"""
🌙 Moon Dev - RBI Systematic Strategy Generator
Generates and tests trading strategies systematically (no API needed!)

Benefits:
- No API costs
- Reproducible results
- Exhaustive parameter exploration
- Can run continuously

Strategy Space Explored:
- MA periods: 10-150
- Leverage: 1x-6x
- RSI thresholds: 50-75
- Volume multipliers: 1.2x-3x
- Stop loss: 0.5%-3%
- Take profit: 3%-15%
"""

import pandas as pd
import numpy as np
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import time
import os
from datetime import datetime
import json
import itertools

# Configuration
TARGET_RETURN = 60.0
MAX_DRAWDOWN = -25.0
DATA_PATH = 'src/data/rbi/BTC-USD-15m.csv'
RESULTS_DIR = 'src/data/rbi_auto/'
WINNERS_DIR = 'src/data/rbi_auto/winners/'

os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(WINNERS_DIR, exist_ok=True)

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

# Define parameter space
PARAMETER_SPACE = {
    'fast_ma': [15, 20, 25, 30],
    'slow_ma': [75, 100, 120, 150],
    'use_ema': [True, False],
    'leverage': [3.0, 4.0, 5.0, 6.0],
    'stop_loss_pct': [0.008, 0.01, 0.012, 0.015],
    'take_profit_pct': [0.05, 0.06, 0.07, 0.08],
    'rsi_min': [65, 68, 70, 72],
    'use_volume': [True, False],
    'volume_mult': [1.5, 2.0, 2.5],
}

def generate_strategy_combinations(max_combinations=100):
    """Generate smart strategy combinations"""

    strategies = []

    # Method 1: Random sampling from parameter space
    import random
    keys = list(PARAMETER_SPACE.keys())

    for i in range(max_combinations // 2):
        strategy = {}
        for key in keys:
            strategy[key] = random.choice(PARAMETER_SPACE[key])

        # Ensure slow_ma > fast_ma
        if strategy['slow_ma'] <= strategy['fast_ma']:
            strategy['slow_ma'] = strategy['fast_ma'] * 4

        # Generate unique name
        ma_type = "EMA" if strategy['use_ema'] else "SMA"
        vol_suffix = f"Vol{strategy['volume_mult']}x" if strategy['use_volume'] else "NoVol"
        strategy['name'] = f"{strategy['leverage']}x{ma_type}{strategy['fast_ma']}/{strategy['slow_ma']}_RSI{strategy['rsi_min']}_{vol_suffix}"
        strategy['description'] = f"{strategy['leverage']}x leverage {ma_type} crossover with RSI and volume filters"

        strategies.append(strategy)

    # Method 2: Variations around known winner (5x EMA 20/100 RSI>68)
    base_winner = {
        'fast_ma': 20,
        'slow_ma': 100,
        'use_ema': True,
        'leverage': 5.0,
        'stop_loss_pct': 0.01,
        'take_profit_pct': 0.06,
        'rsi_min': 68,
        'use_volume': True,
        'volume_mult': 2.0,
    }

    # Variations
    for variation in range(max_combinations // 2):
        strategy = base_winner.copy()

        # Randomly tweak 1-2 parameters
        params_to_tweak = random.sample(list(PARAMETER_SPACE.keys()), random.randint(1, 2))

        for param in params_to_tweak:
            strategy[param] = random.choice(PARAMETER_SPACE[param])

        # Ensure slow_ma > fast_ma
        if strategy['slow_ma'] <= strategy['fast_ma']:
            strategy['slow_ma'] = strategy['fast_ma'] * 4

        # Generate unique name
        ma_type = "EMA" if strategy['use_ema'] else "SMA"
        vol_suffix = f"Vol{strategy['volume_mult']}x" if strategy['use_volume'] else "NoVol"
        strategy['name'] = f"{strategy['leverage']}x{ma_type}{strategy['fast_ma']}/{strategy['slow_ma']}_RSI{strategy['rsi_min']}_{vol_suffix}_v{variation}"
        strategy['description'] = f"Variation of winner strategy #{variation}"

        strategies.append(strategy)

    return strategies

def test_strategy(strategy_config, data):
    """Backtest a strategy"""

    class GeneratedStrategy(Strategy):
        def init(self):
            close = self.data.Close

            if strategy_config.get('use_ema', False):
                self.ma_fast = self.I(calculate_ema, close, strategy_config['fast_ma'])
                self.ma_slow = self.I(calculate_ema, close, strategy_config['slow_ma'])
            else:
                self.ma_fast = self.I(calculate_sma, close, strategy_config['fast_ma'])
                self.ma_slow = self.I(calculate_sma, close, strategy_config['slow_ma'])

            self.rsi = self.I(calculate_rsi, close, 14)

            if strategy_config.get('use_volume', False):
                vol = self.data.Volume
                self.vol_avg = self.I(lambda: pd.Series(vol).rolling(20).mean().values)

        def next(self):
            if np.isnan(self.ma_slow[-1]) or np.isnan(self.rsi[-1]):
                return

            price = self.data.Close[-1]

            if not self.position:
                entry_ok = False

                if crossover(self.ma_fast, self.ma_slow) or self.ma_fast[-1] > self.ma_slow[-1]:
                    entry_ok = True

                if self.rsi[-1] < strategy_config['rsi_min']:
                    entry_ok = False

                if strategy_config.get('use_volume') and hasattr(self, 'vol_avg'):
                    if self.data.Volume[-1] < (self.vol_avg[-1] * strategy_config['volume_mult']):
                        entry_ok = False

                if entry_ok:
                    sl = price * (1 - strategy_config['stop_loss_pct'])
                    tp = price * (1 + strategy_config['take_profit_pct'])
                    self.buy(size=strategy_config['leverage'], sl=sl, tp=tp)

            else:
                if crossover(self.ma_slow, self.ma_fast):
                    self.position.close()

    try:
        bt = Backtest(data, GeneratedStrategy, cash=100000, commission=.002)
        stats = bt.run()

        return {
            'success': True,
            'return': stats['Return [%]'],
            'buy_hold': stats['Buy & Hold Return [%]'],
            'trades': stats['# Trades'],
            'win_rate': stats['Win Rate [%]'],
            'max_dd': stats['Max. Drawdown [%]'],
            'sharpe': stats['Sharpe Ratio'],
            'final_equity': stats['Equity Final [$]'],
            'avg_trade': stats['Avg. Trade [%]'],
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def save_winner(strategy_config, results, iteration):
    """Save winning strategy"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{WINNERS_DIR}winner_{iteration}_{timestamp}_{results['return']:.1f}pct.json"

    winner_data = {
        'timestamp': timestamp,
        'iteration': iteration,
        'strategy': strategy_config,
        'results': results,
    }

    with open(filename, 'w') as f:
        json.dump(winner_data, f, indent=2)

    return filename

def main():
    print("=" * 90)
    print("🌙 MOON DEV - RBI SYSTEMATIC STRATEGY GENERATOR")
    print("=" * 90)
    print(f"\n🎯 Target: >{TARGET_RETURN}% return with max DD {MAX_DRAWDOWN}%")
    print(f"🔬 Method: Systematic parameter space exploration")
    print(f"💰 Cost: $0 (no API calls)")

    # Load data
    print(f"\n📈 Loading BTC data from {DATA_PATH}...")
    data = pd.read_csv(DATA_PATH)
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

    # Generate strategies
    print(f"\n🧬 Generating strategy combinations...")
    strategies = generate_strategy_combinations(max_combinations=100)
    print(f"✅ Generated {len(strategies)} unique strategies")

    # Test strategies
    all_results = []
    winners_found = 0

    print(f"\n{'='*90}")
    print("🚀 STARTING SYSTEMATIC TESTING")
    print(f"{'='*90}\n")

    for i, strategy in enumerate(strategies, 1):
        print(f"\r🔬 Testing {i}/{len(strategies)}: {strategy['name'][:60]:<60}", end='', flush=True)

        results = test_strategy(strategy, data)

        if not results['success']:
            continue

        # Check if winner
        is_winner = (results['return'] >= TARGET_RETURN and
                    results['max_dd'] >= MAX_DRAWDOWN)

        if is_winner:
            print(f"\n   🎉 WINNER! {results['return']:.2f}% (DD: {results['max_dd']:.2f}%)")
            filename = save_winner(strategy, results, i)
            winners_found += 1

        all_results.append({
            'iteration': i,
            'name': strategy['name'],
            'strategy': strategy,
            'results': results,
            'is_winner': is_winner,
        })

    print(f"\n\n{'='*90}")
    print("🏁 SYSTEMATIC TESTING COMPLETE")
    print(f"{'='*90}\n")

    # Sort and display top 20
    all_results.sort(key=lambda x: x['results']['return'] if x['results']['success'] else -999, reverse=True)

    print(f"{'Rank':<6} {'Strategy':<50} {'Return':<12} {'MaxDD':<10} {'Sharpe':<8} {'Status':<5}")
    print("-" * 90)

    for rank, r in enumerate(all_results[:20], 1):
        if not r['results']['success']:
            continue

        medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else "  "
        status = "🎯" if r['is_winner'] else ""

        print(f"{medal} #{rank:<4} {r['name'][:48]:<48} "
              f"{r['results']['return']:>9.2f}%  {r['results']['max_dd']:>8.2f}%  "
              f"{r['results']['sharpe']:>6.2f}  {status}")

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"{RESULTS_DIR}systematic_{timestamp}.json"
    with open(results_file, 'w') as f:
        json.dump(all_results, f, indent=2)

    print(f"\n✅ Results saved to: {results_file}")
    print(f"🏆 Winners found: {winners_found}")

    if winners_found > 0:
        print(f"💾 Winners saved to: {WINNERS_DIR}")
        print(f"\n🚀 Run rbi_auto_deployer.py to deploy winning strategies!")
    else:
        best = all_results[0] if all_results and all_results[0]['results']['success'] else None
        if best:
            print(f"\n📊 Best strategy: {best['name']}")
            print(f"   Return: {best['results']['return']:.2f}%")
            print(f"   Max DD: {best['results']['max_dd']:.2f}%")
            gap = TARGET_RETURN - best['results']['return']
            if gap > 0:
                print(f"   Gap to target: {gap:.2f}%")

    print(f"\n{'='*90}\n")

if __name__ == "__main__":
    main()
