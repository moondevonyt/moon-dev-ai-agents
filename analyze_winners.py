"""
Analyze if the 26 winners are truly unique strategies
"""

import json
import os
from collections import defaultdict

WINNERS_DIR = 'src/data/rbi_auto/winners/'

# Load all winners
winners = []
for filename in os.listdir(WINNERS_DIR):
    if filename.endswith('.json'):
        with open(os.path.join(WINNERS_DIR, filename), 'r') as f:
            winner = json.load(f)
            winners.append(winner)

print("=" * 90)
print("🔍 WINNER STRATEGY UNIQUENESS ANALYSIS")
print("=" * 90)
print(f"\nTotal winner files: {len(winners)}")

# Create unique signature for each strategy
unique_configs = {}
duplicates = defaultdict(list)

for winner in winners:
    strat = winner['strategy']

    # Create signature from key parameters
    signature = (
        strat.get('fast_ma'),
        strat.get('slow_ma'),
        strat.get('use_ema'),
        strat.get('leverage'),
        strat.get('stop_loss_pct'),
        strat.get('take_profit_pct'),
        strat.get('rsi_min'),
        strat.get('use_volume'),
        strat.get('volume_mult'),
    )

    config_str = f"MA {strat.get('fast_ma')}/{strat.get('slow_ma')} {'EMA' if strat.get('use_ema') else 'SMA'} | " \
                 f"Lev {strat.get('leverage')}x | RSI >{strat.get('rsi_min')} | " \
                 f"Vol {strat.get('volume_mult')}x" if strat.get('use_volume') else "NoVol"

    if signature in unique_configs:
        duplicates[signature].append({
            'name': strat.get('name'),
            'return': winner['results']['return'],
            'config': config_str
        })
    else:
        unique_configs[signature] = {
            'name': strat.get('name'),
            'return': winner['results']['return'],
            'max_dd': winner['results']['max_dd'],
            'sharpe': winner['results']['sharpe'],
            'config': config_str,
            'full_config': strat
        }

print(f"\n✅ Truly unique strategies: {len(unique_configs)}")
print(f"❌ Duplicate configurations: {len(duplicates)}")

if duplicates:
    print(f"\n{'='*90}")
    print("DUPLICATE CONFIGURATIONS FOUND")
    print(f"{'='*90}\n")

    for signature, dups in duplicates.items():
        config = unique_configs.get(signature)
        if config:
            print(f"Configuration: {config['config']}")
            print(f"  Original: {config['name']} - {config['return']:.2f}%")
            for dup in dups:
                print(f"  Duplicate: {dup['name']} - {dup['return']:.2f}%")
            print()

print(f"\n{'='*90}")
print("UNIQUE STRATEGIES")
print(f"{'='*90}\n")

# Sort by return
sorted_unique = sorted(unique_configs.values(), key=lambda x: x['return'], reverse=True)

print(f"{'Rank':<6} {'Return':<10} {'MaxDD':<10} {'Sharpe':<8} {'Configuration':<60}")
print("-" * 90)

for rank, strat in enumerate(sorted_unique, 1):
    print(f"#{rank:<5} {strat['return']:>7.2f}%  {strat['max_dd']:>8.2f}%  {strat['sharpe']:>6.2f}  {strat['config']}")

print(f"\n{'='*90}")
print("SUMMARY")
print(f"{'='*90}\n")

print(f"Total files: {len(winners)}")
print(f"Unique strategies: {len(unique_configs)}")
print(f"Duplicates: {len(winners) - len(unique_configs)}")

if len(unique_configs) < len(winners):
    pct_unique = (len(unique_configs) / len(winners)) * 100
    print(f"\nPercentage unique: {pct_unique:.1f}%")
    print(f"\n⚠️  The system generated variations around successful configurations,")
    print(f"   resulting in some identical parameter sets.")
else:
    print(f"\n✅ All 26 strategies are unique!")

print(f"\n{'='*90}\n")
