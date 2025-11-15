#!/usr/bin/env python3
"""
Comprehensive Strategy Performance Test
Find all strategies beating DivergenceVolatility's 1.84 Sharpe ratio
"""

import pandas as pd
import numpy as np
import warnings
import glob
import re
warnings.filterwarnings('ignore')

# Collect all documented results
results = []

# 1. Add the known best performer
results.append({
    'name': 'DivergenceVolatility_AI6',
    'trades': 125,
    'return': 2.61,
    'sharpe': 1.84,
    'max_dd': -0.87,
    'win_rate': 44.00,
    'location': 'src/data/rbi/03_14_2025/AI_BACKTEST_RESULTS/'
})

# 2. Add other known performers
results.append({
    'name': 'AccumulationManipulation',
    'trades': 71,
    'return': 3.47,
    'sharpe': 0.73,
    'max_dd': -2.69,
    'win_rate': 32.39,
    'location': 'src/data/rbi/backtests/'
})

results.append({
    'name': 'RSIDivergence',
    'trades': 4,
    'return': 1.17,
    'sharpe': 0.25,
    'max_dd': -5.87,
    'win_rate': 50.00,
    'location': 'src/data/rbi/backtests/'
})

results.append({
    'name': 'DivergenceBand_AI6',
    'trades': 10,
    'return': 1.05,
    'sharpe': 0.21,
    'max_dd': -4.89,
    'win_rate': 40.00,
    'location': 'src/data/rbi/03_14_2025/AI_BACKTEST_RESULTS/'
})

results.append({
    'name': 'DivergenceAnchor_AI6',
    'trades': 17,
    'return': -9.28,
    'sharpe': -0.81,
    'max_dd': -9.32,
    'win_rate': 29.41,
    'location': 'src/data/rbi/03_14_2025/AI_BACKTEST_RESULTS/'
})

results.append({
    'name': 'SimpleMomentumCross',
    'trades': 834,
    'return': -92.43,
    'sharpe': -47.31,
    'max_dd': np.nan,
    'win_rate': 22.06,
    'location': 'src/data/rbi/FINAL_WINNING_STRATEGIES/'
})

results.append({
    'name': 'RSIMeanReversion',
    'trades': 834,
    'return': -92.58,
    'sharpe': -77.63,
    'max_dd': np.nan,
    'win_rate': 69.18,
    'location': 'src/data/rbi/FINAL_WINNING_STRATEGIES/'
})

# Now try to find and test the untested strategies
print("=" * 100)
print("COMPREHENSIVE STRATEGY PERFORMANCE ANALYSIS")
print("Finding All Strategies Better Than DivergenceVolatility (1.84 Sharpe)")
print("=" * 100)
print()

# Check for additional stat files
stat_files = glob.glob('/home/user/moon-dev-ai-agents/src/data/rbi/backtests/stats/*_stats*.txt')

for stat_file in stat_files:
    try:
        with open(stat_file, 'r') as f:
            content = f.read()

        # Extract strategy name from filename or content
        strategy_name = stat_file.split('/')[-1].replace('_stats', '').replace('.txt', '')
        strategy_name = re.sub(r'_\d{8}_\d{6}', '', strategy_name)  # Remove timestamps

        # Parse stats
        sharpe = None
        trades = None
        return_pct = None
        max_dd = None
        win_rate = None

        for line in content.split('\n'):
            if 'Sharpe Ratio' in line and 'Sharpe Ratio' not in line.split()[-1]:
                try:
                    sharpe = float(line.split()[-1])
                except:
                    pass
            elif '# Trades' in line:
                try:
                    trades = int(line.split()[-1])
                except:
                    pass
            elif 'Return [%]' in line and 'Ann' not in line:
                try:
                    return_pct = float(line.split()[-1])
                except:
                    pass
            elif 'Max. Drawdown [%]' in line:
                try:
                    max_dd = float(line.split()[-1])
                except:
                    pass
            elif 'Win Rate [%]' in line:
                try:
                    win_rate = float(line.split()[-1])
                except:
                    pass

        # Only add if we have sharpe ratio
        if sharpe is not None and not any(r['name'] == strategy_name for r in results):
            results.append({
                'name': strategy_name,
                'trades': trades or 0,
                'return': return_pct or 0.0,
                'sharpe': sharpe,
                'max_dd': max_dd or 0.0,
                'win_rate': win_rate or 0.0,
                'location': 'src/data/rbi/backtests/stats/'
            })
    except Exception as e:
        pass

# Sort by Sharpe ratio
results.sort(key=lambda x: x['sharpe'] if not pd.isna(x['sharpe']) else -999, reverse=True)

# Print results
print(f"{'Rank':<6} {'Strategy':<45} {'Sharpe':<10} {'Return %':<12} {'Trades':<8} {'Max DD %':<12} {'Win Rate %':<12}")
print("-" * 125)

winners = []
for i, result in enumerate(results, 1):
    sharpe_display = f"{result['sharpe']:.2f}" if not pd.isna(result['sharpe']) else "N/A"
    win_rate_display = f"{result['win_rate']:.2f}" if not pd.isna(result['win_rate']) else "N/A"
    max_dd_display = f"{result['max_dd']:.2f}" if not pd.isna(result['max_dd']) else "N/A"

    marker = "🏆" if result['sharpe'] > 1.84 else ("  " if i <= 10 else "")

    if result['sharpe'] > 1.84:
        winners.append(result)

    if i <= 20:  # Show top 20
        print(f"{marker} {i:<4} {result['name']:<45} {sharpe_display:<10} {result['return']:<12.2f} {result['trades']:<8} {max_dd_display:<12} {win_rate_display:<12}")

print()
print("=" * 100)
print(f"SUMMARY: Found {len(winners)} strategies beating DivergenceVolatility's 1.84 Sharpe ratio")
print("=" * 100)

if winners:
    print()
    print("🏆 WINNERS (Sharpe > 1.84):")
    for w in winners:
        print(f"   {w['name']}: Sharpe {w['sharpe']:.2f}, Return {w['return']:.2f}%, Trades {w['trades']}, Location: {w['location']}")
else:
    print()
    print("❌ No strategies found that beat DivergenceVolatility's 1.84 Sharpe ratio")
    print("   DivergenceVolatility_AI6 remains the best strategy in the repository.")

print()
print("=" * 100)
print("TOP 10 MOST PROFITABLE STRATEGIES (By Sharpe Ratio)")
print("=" * 100)
for i in range(min(10, len(results))):
    r = results[i]
    print(f"{i+1}. {r['name']}")
    print(f"   Sharpe: {r['sharpe']:.2f} | Return: {r['return']:.2f}% | Trades: {r['trades']} | Max DD: {r['max_dd']:.2f}% | Win Rate: {r['win_rate']:.2f}%")
    print(f"   Location: {r['location']}")
    print()
