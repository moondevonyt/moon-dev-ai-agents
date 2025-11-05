"""
🌙 Moon Dev - FINAL COMPREHENSIVE COMPARISON
Vergelijking van ALLE geteste strategieën

Optie 1: Golden Cross Optimalisatie (5 configuraties)
Optie 2: AI-Style Strategies (4 strategieën)
Optie 3: Multi-Timeframe (3 timeframes)
"""

import pandas as pd
import numpy as np

print("\n" + "=" * 100)
print("🏆 MOON DEV'S COMPREHENSIVE BACKTEST RESULTS")
print("=" * 100)

# ============================================================================
# OPTIE 1: Golden Cross Optimization Results
# ============================================================================
print("\n📊 OPTIE 1: GOLDEN CROSS OPTIMIZATION")
print("-" * 100)

gc_results = pd.read_csv('golden_cross_optimization_results.csv')
gc_results = gc_results.sort_values('return', ascending=False)

print(f"{'Config':<15} {'Description':<20} {'Return':<10} {'Trades':<8} {'Win%':<8} {'MaxDD':<10} {'Sharpe':<8}")
print("-" * 100)

for _, r in gc_results.iterrows():
    status = "🏆" if _ == gc_results.index[0] else "✅" if r['return'] > 0 else "❌"
    print(f"{status} {r['config']:<13} {r['description']:<20} {r['return']:>7.2f}%  {int(r['trades']):>6}  {r['win_rate']:>6.1f}%  {r['max_dd']:>8.2f}%  {r['sharpe']:>6.2f}")

best_gc = gc_results.iloc[0]
print(f"\n🏆 Winner: {best_gc['config']} with {best_gc['return']:.2f}% return")

# ============================================================================
# OPTIE 2: AI Strategies Results
# ============================================================================
print("\n\n📊 OPTIE 2: AI-STYLE STRATEGIES")
print("-" * 100)

ai_results = pd.read_csv('ai_strategies_results.csv')
ai_results = ai_results.sort_values('return', ascending=False)

print(f"{'Strategy':<30} {'Return':<10} {'Trades':<8} {'Win%':<8} {'MaxDD':<10} {'Sharpe':<8}")
print("-" * 100)

for _, r in ai_results.iterrows():
    status = "🏆" if _ == ai_results.index[0] else "✅" if r['return'] > 0 else "❌"
    print(f"{status} {r['name']:<28} {r['return']:>7.2f}%  {int(r['trades']):>6}  {r['win_rate']:>6.1f}%  {r['max_dd']:>8.2f}%  {r['sharpe']:>6.2f}")

best_ai = ai_results.iloc[0]
print(f"\n🏆 Winner: {best_ai['name']} with {best_ai['return']:.2f}% return")

# ============================================================================
# OPTIE 3: Multi-Timeframe Results
# ============================================================================
print("\n\n📊 OPTIE 3: MULTI-TIMEFRAME TESTING (30/150 Golden Cross)")
print("-" * 100)

tf_results = pd.read_csv('multi_timeframe_results.csv')
tf_results = tf_results.sort_values('return', ascending=False)

print(f"{'Timeframe':<15} {'Bars':<8} {'Return':<10} {'Trades':<8} {'Win%':<8} {'MaxDD':<10} {'Sharpe':<8}")
print("-" * 100)

for _, r in tf_results.iterrows():
    status = "🏆" if _ == tf_results.index[0] else "✅" if r['return'] > 0 else "❌"
    win_rate_str = f"{r['win_rate']:.1f}%" if not pd.isna(r['win_rate']) else "N/A"
    print(f"{status} {r['timeframe']:<13} {int(r['bars']):>6}  {r['return']:>7.2f}%  {int(r['trades']):>6}  {win_rate_str:>6}  {r['max_dd']:>8.2f}%  {r['sharpe']:>6.2f}")

best_tf = tf_results.iloc[0]
print(f"\n🏆 Winner: {best_tf['timeframe']} with {best_tf['return']:.2f}% return")

# ============================================================================
# OVERALL CHAMPION
# ============================================================================
print("\n\n" + "=" * 100)
print("🏆 OVERALL CHAMPION - TOP 5 STRATEGIES")
print("=" * 100)

# Combine all results
all_strategies = []

# Golden Cross configs
for _, r in gc_results.iterrows():
    all_strategies.append({
        'strategy': f"Golden Cross {r['config']}",
        'category': 'Optimized MA',
        'return': r['return'],
        'trades': r['trades'],
        'win_rate': r['win_rate'],
        'max_dd': r['max_dd'],
        'sharpe': r['sharpe'],
        'profit': r['final_equity'] - 100000
    })

# AI strategies
for _, r in ai_results.iterrows():
    all_strategies.append({
        'strategy': r['name'],
        'category': 'AI-Style',
        'return': r['return'],
        'trades': r['trades'],
        'win_rate': r['win_rate'],
        'max_dd': r['max_dd'],
        'sharpe': r['sharpe'],
        'profit': r['final_equity'] - 100000
    })

# Multi-timeframe
for _, r in tf_results.iterrows():
    all_strategies.append({
        'strategy': f"GC 30/150 ({r['timeframe']})",
        'category': 'Multi-TF',
        'return': r['return'],
        'trades': r['trades'],
        'win_rate': r['win_rate'] if not pd.isna(r['win_rate']) else 0,
        'max_dd': r['max_dd'],
        'sharpe': r['sharpe'],
        'profit': r['final_equity'] - 100000
    })

# Sort by return
df_all = pd.DataFrame(all_strategies)
df_all = df_all.sort_values('return', ascending=False)

print(f"{'#':<4} {'Strategy':<35} {'Category':<15} {'Return':<10} {'Profit':<12} {'Trades':<8} {'Sharpe':<8}")
print("-" * 100)

for i, (_, r) in enumerate(df_all.head(5).iterrows(), 1):
    medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "  "
    print(f"{medal} #{i}  {r['strategy']:<33} {r['category']:<15} {r['return']:>7.2f}%  ${r['profit']:>10,.0f}  {int(r['trades']):>6}  {r['sharpe']:>6.2f}")

# ============================================================================
# INSIGHTS & RECOMMENDATIONS
# ============================================================================
champion = df_all.iloc[0]

print("\n\n" + "=" * 100)
print("💡 KEY INSIGHTS & RECOMMENDATIONS")
print("=" * 100)

print(f"\n🏆 OVERALL CHAMPION:")
print(f"   Strategy:  {champion['strategy']}")
print(f"   Return:    {champion['return']:.2f}%")
print(f"   Profit:    ${champion['profit']:,.2f}")
print(f"   Category:  {champion['category']}")

print(f"\n📊 PERFORMANCE ANALYSIS:")
winners = df_all[df_all['return'] > 0]
print(f"   • {len(winners)}/{len(df_all)} strategies profitable ({len(winners)/len(df_all)*100:.1f}%)")
print(f"   • Average return (all): {df_all['return'].mean():.2f}%")
print(f"   • Average return (winners only): {winners['return'].mean():.2f}%")
print(f"   • Best Sharpe: {df_all['sharpe'].max():.2f}")

print(f"\n🎯 CATEGORY COMPARISON:")
for cat in df_all['category'].unique():
    cat_data = df_all[df_all['category'] == cat]
    avg_return = cat_data['return'].mean()
    best_return = cat_data['return'].max()
    print(f"   • {cat:15} - Avg: {avg_return:>6.2f}% | Best: {best_return:>6.2f}%")

print(f"\n💰 TOP RECOMMENDATIONS:")
print(f"   1. 🏆 Best Overall:      {df_all.iloc[0]['strategy']}")
print(f"   2. 📈 Best Risk-Adj:     {df_all.sort_values('sharpe', ascending=False).iloc[0]['strategy']}")
print(f"   3. ⚡ Least Trades:       {df_all.sort_values('trades').iloc[0]['strategy']}")
print(f"   4. 🎯 Best Win Rate:     {df_all.sort_values('win_rate', ascending=False).iloc[0]['strategy']}")

print(f"\n🚨 KEY LESSONS:")
print(f"   • Simpler is better: MA crossovers outperform complex indicators")
print(f"   • Timeframe matters: 1H provided best balance")
print(f"   • MA period optimization: 30/150 >> 50/200 (classic)")
print(f"   • Buy & Hold: {best_gc['buy_hold']:.2f}% (hard to beat in bull market!)")

print(f"\n✅ NEXT STEPS:")
print(f"   1. Live test {champion['strategy']} on paper trading")
print(f"   2. Optimize position sizing and risk management")
print(f"   3. Add portfolio management (multiple positions)")
print(f"   4. Test on other assets (ETH, SOL, etc.)")

print("\n" + "=" * 100)
print(f"📁 All results saved to CSV files in current directory")
print("=" * 100 + "\n")

# Save combined results
df_all.to_csv('final_combined_results.csv', index=False)
print("✅ Final combined results saved to: final_combined_results.csv")
