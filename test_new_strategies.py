#!/usr/bin/env python3
"""
Test untested strategies - run each without optimization to get baseline results
"""

import subprocess
import sys
import time

strategies_to_test = [
    ('src/data/rbi/FINAL_WINNING_STRATEGIES/DivergenceVolatilityEnhanced_BT.py', 'DivergenceVolatilityEnhanced'),
    ('src/data/rbi/FINAL_WINNING_STRATEGIES/SelectiveMomentumSwing_BT.py', 'SelectiveMomentumSwing'),
    ('src/data/rbi/FINAL_WINNING_STRATEGIES/TrendCapturePro_BT.py', 'TrendCapturePro'),
    ('src/data/rbi/AI_GENERATED_STRATEGIES/MomentumVolatilityFusion_BT.py', 'MomentumVolatilityFusion'),
    ('src/data/rbi/AI_GENERATED_STRATEGIES/AdaptiveMeanReversionBreakout_BT.py', 'AdaptiveMeanReversionBreakout'),
    ('src/data/rbi/AI_GENERATED_STRATEGIES/VolumeBreakoutConvergence_BT.py', 'VolumeBreakoutConvergence'),
]

print("=" * 100)
print("TESTING UNTESTED STRATEGIES FOR SHARPE > 1.84")
print("=" * 100)
print()

results = []

for file_path, strategy_name in strategies_to_test:
    print(f"\n{'='*80}")
    print(f"Testing: {strategy_name}")
    print(f"File: {file_path}")
    print('='*80)

    try:
        # Run the strategy with a 60 second timeout
        result = subprocess.run(
            ['timeout', '60', 'python', file_path],
            capture_output=True,
            text=True,
            cwd='/home/user/moon-dev-ai-agents'
        )

        output = result.stdout + result.stderr

        # Parse output for KEY METRICS
        if 'KEY METRICS' in output or 'Sharpe Ratio' in output:
            lines = output.split('\n')
            trades = None
            return_pct = None
            sharpe = None
            max_dd = None
            win_rate = None

            for i, line in enumerate(lines):
                if 'Total Trades:' in line:
                    try:
                        trades = int(line.split(':')[-1].strip())
                    except:
                        pass
                elif 'Total Return:' in line:
                    try:
                        return_pct = float(line.split(':')[-1].strip().replace('%', ''))
                    except:
                        pass
                elif 'Sharpe Ratio:' in line:
                    try:
                        sharpe = float(line.split(':')[-1].strip())
                    except:
                        pass
                elif 'Max Drawdown:' in line:
                    try:
                        max_dd = float(line.split(':')[-1].strip().replace('%', ''))
                    except:
                        pass
                elif 'Win Rate:' in line:
                    try:
                        win_rate = float(line.split(':')[-1].strip().replace('%', ''))
                    except:
                        pass

            if sharpe is not None:
                results.append({
                    'name': strategy_name,
                    'trades': trades or 0,
                    'return': return_pct or 0.0,
                    'sharpe': sharpe,
                    'max_dd': max_dd or 0.0,
                    'win_rate': win_rate or 0.0
                })
                print(f"✓ Results: Trades={trades}, Return={return_pct}%, Sharpe={sharpe:.2f}")
            else:
                print(f"⚠ No metrics found in output - Strategy may have generated 0 trades")
                print(f"Output preview: {output[:500]}")
        else:
            print(f"⚠ Strategy timed out or produced no metrics")

    except Exception as e:
        print(f"❌ Error testing {strategy_name}: {e}")

print("\n" + "="*100)
print("RESULTS SUMMARY")
print("="*100)

if results:
    results.sort(key=lambda x: x['sharpe'], reverse=True)

    print(f"\n{'Strategy':<45} {'Sharpe':<10} {'Return %':<12} {'Trades':<8} {'Max DD %':<12} {'Win Rate %':<12}")
    print("-" * 120)

    for r in results:
        marker = "🏆" if r['sharpe'] > 1.84 else "  "
        print(f"{marker} {r['name']:<45} {r['sharpe']:<10.2f} {r['return']:<12.2f} {r['trades']:<8} {r['max_dd']:<12.2f} {r['win_rate']:<12.2f}")

    winners = [r for r in results if r['sharpe'] > 1.84]
    if winners:
        print(f"\n🎉 FOUND {len(winners)} STRATEGIES BEATING 1.84 SHARPE!")
        for w in winners:
            print(f"   🏆 {w['name']}: Sharpe {w['sharpe']:.2f}")
    else:
        print("\n❌ None of the tested strategies beat DivergenceVolatility_AI6 (1.84 Sharpe)")
else:
    print("\n⚠ No strategies produced measurable results")
    print("All strategies likely generated 0 trades with default parameters")
