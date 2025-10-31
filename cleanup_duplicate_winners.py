"""
🌙 Moon Dev - Cleanup Duplicate Winner Strategies
Removes duplicate strategies, keeping only the 11 unique ones
"""

import json
import os
from collections import defaultdict
import shutil

WINNERS_DIR = 'src/data/rbi_auto/winners/'
STRATEGIES_DIR = 'src/strategies/auto_generated/'
BACKUP_DIR = 'src/data/rbi_auto/duplicates_backup/'

# Create backup directory
os.makedirs(BACKUP_DIR, exist_ok=True)
os.makedirs(os.path.join(BACKUP_DIR, 'winners'), exist_ok=True)
os.makedirs(os.path.join(BACKUP_DIR, 'strategies'), exist_ok=True)

print("=" * 90)
print("🧹 CLEANUP DUPLICATE WINNER STRATEGIES")
print("=" * 90)

# Load all winners
winners = []
for filename in os.listdir(WINNERS_DIR):
    if filename.endswith('.json'):
        filepath = os.path.join(WINNERS_DIR, filename)
        with open(filepath, 'r') as f:
            winner = json.load(f)
            winner['filename'] = filename
            winner['filepath'] = filepath
            winners.append(winner)

print(f"\n📊 Found {len(winners)} winner files")

# Group by unique signature
unique_groups = defaultdict(list)

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

    unique_groups[signature].append(winner)

print(f"✅ Found {len(unique_groups)} unique configurations")
print(f"❌ Duplicates to remove: {len(winners) - len(unique_groups)}")

# Track what we'll keep and remove
to_keep = []
to_remove = []

print(f"\n{'='*90}")
print("PROCESSING EACH UNIQUE CONFIGURATION")
print(f"{'='*90}\n")

for signature, group in unique_groups.items():
    if len(group) == 1:
        # No duplicates, keep it
        to_keep.append(group[0])
        config = group[0]['strategy']['name']
        print(f"✅ Unique: {config}")
    else:
        # Multiple duplicates - keep the best performing one
        # Sort by return (descending)
        group_sorted = sorted(group, key=lambda x: x['results']['return'], reverse=True)
        best = group_sorted[0]
        duplicates = group_sorted[1:]

        to_keep.append(best)
        to_remove.extend(duplicates)

        config = best['strategy']['name']
        print(f"🔍 Found {len(group)} duplicates of: {config}")
        print(f"   ✅ Keeping best: {best['filename']} ({best['results']['return']:.2f}%)")
        print(f"   ❌ Removing {len(duplicates)} duplicates:")
        for dup in duplicates:
            print(f"      - {dup['filename']}")

# Perform cleanup
print(f"\n{'='*90}")
print("CLEANUP ACTIONS")
print(f"{'='*90}\n")

print(f"Backing up {len(to_remove)} duplicate files...")

removed_count = 0
for winner in to_remove:
    # Backup winner JSON
    src_json = winner['filepath']
    dst_json = os.path.join(BACKUP_DIR, 'winners', winner['filename'])

    if os.path.exists(src_json):
        shutil.move(src_json, dst_json)
        print(f"  📦 Backed up: {winner['filename']}")
        removed_count += 1

    # Find and remove corresponding strategy file(s)
    strategy_name = winner['strategy']['name'].replace(' ', '').replace('-', '').replace('/', '_').replace('.', '_')

    # Strategy files might have different rank numbers and timestamps
    for strategy_file in os.listdir(STRATEGIES_DIR):
        if strategy_file.startswith(strategy_name):
            src_strategy = os.path.join(STRATEGIES_DIR, strategy_file)
            dst_strategy = os.path.join(BACKUP_DIR, 'strategies', strategy_file)

            if os.path.exists(src_strategy):
                shutil.move(src_strategy, dst_strategy)
                print(f"     ↳ Removed strategy: {strategy_file}")

print(f"\n✅ Removed {removed_count} duplicate winner files")

# Verify final state
remaining_winners = len([f for f in os.listdir(WINNERS_DIR) if f.endswith('.json')])
remaining_strategies = len([f for f in os.listdir(STRATEGIES_DIR) if f.endswith('.py')])

print(f"\n{'='*90}")
print("FINAL STATE")
print(f"{'='*90}\n")

print(f"📁 Winners remaining: {remaining_winners}/{len(winners)}")
print(f"📁 Strategies remaining: {remaining_strategies}")
print(f"💾 Backups saved to: {BACKUP_DIR}")

print(f"\n{'='*90}")
print("UNIQUE WINNERS (sorted by return)")
print(f"{'='*90}\n")

# Display final unique list
to_keep_sorted = sorted(to_keep, key=lambda x: x['results']['return'], reverse=True)

print(f"{'Rank':<6} {'Strategy':<45} {'Return':<12} {'MaxDD':<10} {'Sharpe':<8}")
print("-" * 90)

for rank, winner in enumerate(to_keep_sorted, 1):
    strat = winner['strategy']
    results = winner['results']

    config = f"{strat.get('leverage')}x {'EMA' if strat.get('use_ema') else 'SMA'} {strat.get('fast_ma')}/{strat.get('slow_ma')} RSI>{strat.get('rsi_min')}"

    medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else "  "

    print(f"{medal} #{rank:<4} {config:<43} {results['return']:>9.2f}%  {results['max_dd']:>8.2f}%  {results['sharpe']:>6.2f}")

print(f"\n{'='*90}")
print("CLEANUP COMPLETE")
print(f"{'='*90}\n")

print(f"✅ {len(to_keep)} unique strategies remain")
print(f"❌ {len(to_remove)} duplicates moved to backup")
print(f"\n💡 To restore backups if needed:")
print(f"   cp {BACKUP_DIR}winners/*.json {WINNERS_DIR}")
print(f"   cp {BACKUP_DIR}strategies/*.py {STRATEGIES_DIR}")

print(f"\n{'='*90}\n")
