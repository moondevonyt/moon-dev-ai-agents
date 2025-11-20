#!/usr/bin/env python3
"""
Simple Strategy Performance Test
Tests strategies without optimization to get baseline performance
"""

import pandas as pd
import numpy as np
from backtesting import Backtest, Strategy
import warnings
import sys
import os
warnings.filterwarnings('ignore')

# Add paths for imports
sys.path.append('/home/user/moon-dev-ai-agents/src/data/rbi/FINAL_WINNING_STRATEGIES')
sys.path.append('/home/user/moon-dev-ai-agents/src/data/rbi/AI_GENERATED_STRATEGIES')

# Data path
data_path = '/home/user/moon-dev-ai-agents/src/data/rbi/BTC-USD-15m.csv'

def load_btc_data(file_path):
    """Load and prepare BTC data"""
    df = pd.read_csv(file_path)
    df.columns = df.columns.str.strip().str.lower()
    df = df.drop(columns=[col for col in df.columns if 'unnamed' in col.lower()], errors='ignore')

    column_mapping = {
        'datetime': 'datetime',
        'timestamp': 'datetime',
        'date': 'datetime',
        'time': 'datetime',
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume'
    }

    for old_col, new_col in column_mapping.items():
        if old_col in df.columns:
            df = df.rename(columns={old_col: new_col})

    if 'datetime' in df.columns:
        df['datetime'] = pd.to_datetime(df['datetime'])
        df = df.set_index('datetime')

    required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
    df = df[required_cols].dropna()
    df = df[df > 0]

    return df

def test_strategy_file(strategy_file, strategy_name):
    """Test a strategy by importing and running it"""
    try:
        # Import the module
        module_name = strategy_file.replace('.py', '')
        if 'FINAL_WINNING_STRATEGIES' in strategy_file:
            module = __import__(f'src.data.rbi.FINAL_WINNING_STRATEGIES.{module_name}', fromlist=[strategy_name])
        elif 'AI_GENERATED_STRATEGIES' in strategy_file:
            module = __import__(f'src.data.rbi.AI_GENERATED_STRATEGIES.{module_name}', fromlist=[strategy_name])
        else:
            return None

        strategy_class = getattr(module, strategy_name)

        # Load data
        data = load_btc_data(data_path)

        # Run backtest
        bt = Backtest(data, strategy_class, cash=1000000, commission=0.002)
        stats = bt.run()

        return {
            'name': strategy_name,
            'trades': stats['# Trades'],
            'return': stats['Return [%]'],
            'sharpe': stats['Sharpe Ratio'],
            'max_dd': stats['Max. Drawdown [%]'],
            'win_rate': stats['Win Rate [%]']
        }
    except Exception as e:
        print(f"Error testing {strategy_name}: {e}")
        return None

# List of strategies to test
strategies_to_test = [
    # FINAL_WINNING_STRATEGIES (top 3)
    ('DivergenceVolatilityEnhanced_BT', 'DivergenceVolatilityEnhanced'),
    ('SelectiveMomentumSwing_BT', 'SelectiveMomentumSwing'),
    ('TrendCapturePro_BT', 'TrendCapturePro'),

    # AI_GENERATED_STRATEGIES
    ('MomentumVolatilityFusion_BT', 'MomentumVolatilityFusion'),
    ('AdaptiveMeanReversionBreakout_BT', 'AdaptiveMeanReversionBreakout'),
    ('VolumeBreakoutConvergence_BT', 'VolumeBreakoutConvergence'),
]

print("=" * 80)
print("STRATEGY PERFORMANCE TEST - Finding Strategies Better Than 1.84 Sharpe")
print("=" * 80)
print()

results = []

for file_name, strategy_name in strategies_to_test:
    print(f"Testing {strategy_name}...")
    result = test_strategy_file(file_name, strategy_name)
    if result:
        results.append(result)
        print(f"  ✓ Trades: {result['trades']}, Return: {result['return']:.2f}%, Sharpe: {result['sharpe']:.2f}")
    print()

# Sort by Sharpe ratio
results.sort(key=lambda x: x['sharpe'] if not pd.isna(x['sharpe']) else -999, reverse=True)

print("=" * 80)
print("RESULTS RANKED BY SHARPE RATIO")
print("=" * 80)
print(f"{'Rank':<6} {'Strategy':<40} {'Trades':<8} {'Return %':<12} {'Sharpe':<10} {'Max DD %':<12} {'Win Rate %':<12}")
print("-" * 120)

for i, result in enumerate(results, 1):
    sharpe_display = f"{result['sharpe']:.2f}" if not pd.isna(result['sharpe']) else "N/A"
    win_rate_display = f"{result['win_rate']:.2f}" if not pd.isna(result['win_rate']) else "N/A"
    max_dd_display = f"{result['max_dd']:.2f}" if not pd.isna(result['max_dd']) else "N/A"

    marker = "🏆" if result['sharpe'] > 1.84 else "  "
    print(f"{marker} {i:<4} {result['name']:<40} {result['trades']:<8} {result['return']:<12.2f} {sharpe_display:<10} {max_dd_display:<12} {win_rate_display:<12}")

print()
print("🏆 = Better than DivergenceVolatility (1.84 Sharpe)")
