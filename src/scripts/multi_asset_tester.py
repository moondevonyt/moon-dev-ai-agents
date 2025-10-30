"""
🌍 BB1151's Multi-Asset Strategy Tester
Tests existing strategies on all 6 assets × 4 timeframes = 24 backtests per strategy

Usage:
    python3 src/scripts/multi_asset_tester.py --top 5
"""

import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime
import argparse

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backtesting import Backtest

# Paths
DATA_DIR = PROJECT_ROOT / "src/data/rbi_pp_multi"
OHLCV_DIR = PROJECT_ROOT / "src/data/ohlcv"
STATS_CSV = DATA_DIR / "backtest_stats.csv"

# 6 Assets × 4 Timeframes = 24 combinations
TEST_ASSETS = [
    # BTC
    {'symbol': 'BTC-USDT', 'timeframe': '5m', 'file': 'BTC-USDT-5m.csv'},
    {'symbol': 'BTC-USDT', 'timeframe': '15m', 'file': 'BTC-USDT-15m.csv'},
    {'symbol': 'BTC-USDT', 'timeframe': '30m', 'file': 'BTC-USDT-30m.csv'},
    {'symbol': 'BTC-USDT', 'timeframe': '1h', 'file': 'BTC-USDT-1h.csv'},
    # ETH
    {'symbol': 'ETH-USDT', 'timeframe': '5m', 'file': 'ETH-USDT-5m.csv'},
    {'symbol': 'ETH-USDT', 'timeframe': '15m', 'file': 'ETH-USDT-15m.csv'},
    {'symbol': 'ETH-USDT', 'timeframe': '30m', 'file': 'ETH-USDT-30m.csv'},
    {'symbol': 'ETH-USDT', 'timeframe': '1h', 'file': 'ETH-USDT-1h.csv'},
    # SOL
    {'symbol': 'SOL-USDT', 'timeframe': '5m', 'file': 'SOL-USDT-5m.csv'},
    {'symbol': 'SOL-USDT', 'timeframe': '15m', 'file': 'SOL-USDT-15m.csv'},
    {'symbol': 'SOL-USDT', 'timeframe': '30m', 'file': 'SOL-USDT-30m.csv'},
    {'symbol': 'SOL-USDT', 'timeframe': '1h', 'file': 'SOL-USDT-1h.csv'},
    # ADA
    {'symbol': 'ADA-USDT', 'timeframe': '5m', 'file': 'ADA-USDT-5m.csv'},
    {'symbol': 'ADA-USDT', 'timeframe': '15m', 'file': 'ADA-USDT-15m.csv'},
    {'symbol': 'ADA-USDT', 'timeframe': '30m', 'file': 'ADA-USDT-30m.csv'},
    {'symbol': 'ADA-USDT', 'timeframe': '1h', 'file': 'ADA-USDT-1h.csv'},
    # XRP
    {'symbol': 'XRP-USDT', 'timeframe': '5m', 'file': 'XRP-USDT-5m.csv'},
    {'symbol': 'XRP-USDT', 'timeframe': '15m', 'file': 'XRP-USDT-15m.csv'},
    {'symbol': 'XRP-USDT', 'timeframe': '30m', 'file': 'XRP-USDT-30m.csv'},
    {'symbol': 'XRP-USDT', 'timeframe': '1h', 'file': 'XRP-USDT-1h.csv'},
    # SUI
    {'symbol': 'SUI-USDT', 'timeframe': '5m', 'file': 'SUI-USDT-5m.csv'},
    {'symbol': 'SUI-USDT', 'timeframe': '15m', 'file': 'SUI-USDT-15m.csv'},
    {'symbol': 'SUI-USDT', 'timeframe': '30m', 'file': 'SUI-USDT-30m.csv'},
    {'symbol': 'SUI-USDT', 'timeframe': '1h', 'file': 'SUI-USDT-1h.csv'},
]

def load_top_strategies(n=5):
    """Load top N strategies from backtest_stats.csv"""
    print(f"\n📊 Loading top {n} strategies...")
    
    if not STATS_CSV.exists():
        print(f"❌ Stats CSV not found: {STATS_CSV}")
        return []
    
    df = pd.read_csv(STATS_CSV)
    
    # Group by strategy name, get best return for each
    best_per_strategy = df.loc[df.groupby('Strategy Name')['Return %'].idxmax()]
    
    # Sort by return and take top N
    top_strategies = best_per_strategy.sort_values('Return %', ascending=False).head(n)
    
    print(f"✅ Found {len(top_strategies)} strategies:\n")
    for idx, row in top_strategies.iterrows():
        print(f"   {row['Strategy Name']:30s} → {row['Return %']:7.2f}% on {row['Data']}")
    
    return top_strategies

def load_strategy_class(strategy_file):
    """Dynamically load strategy class from Python file"""
    import importlib.util
    
    spec = importlib.util.spec_from_file_location("strategy", strategy_file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    # Find Strategy class
    for name in dir(module):
        obj = getattr(module, name)
        if isinstance(obj, type) and name != 'Strategy':
            try:
                from backtesting import Strategy
                if issubclass(obj, Strategy) and obj != Strategy:
                    return obj
            except:
                continue
    
    return None

def run_backtest_on_asset(strategy_class, asset_config):
    """Run backtest on specific asset"""
    try:
        # Load OHLCV data
        data_file = OHLCV_DIR / asset_config['file']
        
        if not data_file.exists():
            return None, f"Data file not found: {asset_config['file']}"
        
        # Load and prepare data
        df = pd.read_csv(data_file)
        df['datetime'] = pd.to_datetime(df['datetime'])
        df = df.set_index('datetime')
        df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        
        # Run backtest
        bt = Backtest(df, strategy_class, cash=1_000_000, commission=0.002)
        stats = bt.run()
        
        # Extract stats
        result = {
            'Return %': float(stats['Return [%]']) if 'Return [%]' in stats else 0.0,
            'Buy & Hold %': float(stats['Buy & Hold Return [%]']) if 'Buy & Hold Return [%]' in stats else 0.0,
            'Max Drawdown %': float(stats['Max. Drawdown [%]']) if 'Max. Drawdown [%]' in stats else 0.0,
            'Sharpe Ratio': float(stats['Sharpe Ratio']) if 'Sharpe Ratio' in stats else 0.0,
            'Sortino Ratio': float(stats['Sortino Ratio']) if 'Sortino Ratio' in stats else 0.0,
            'Trades': int(stats['# Trades']) if '# Trades' in stats else 0,
        }
        
        # Calculate EV
        if result['Trades'] > 0:
            result['EV %'] = result['Return %'] / result['Trades']
        else:
            result['EV %'] = 0.0
        
        return result, None
        
    except Exception as e:
        return None, str(e)

def test_strategy_on_all_assets(strategy_info):
    """Test a strategy on all 24 asset/timeframe combinations"""
    strategy_name = strategy_info['Strategy Name']
    strategy_file = Path(strategy_info['File Path'])
    
    print(f"\n{'='*60}")
    print(f"🧪 Testing: {strategy_name}")
    print(f"{'='*60}")
    
    if not strategy_file.exists():
        print(f"❌ Strategy file not found: {strategy_file}")
        return []
    
    # Load strategy class
    print(f"📥 Loading strategy class...")
    strategy_class = load_strategy_class(strategy_file)
    
    if not strategy_class:
        print(f"❌ Could not load strategy class from {strategy_file}")
        return []
    
    print(f"✅ Loaded: {strategy_class.__name__}")
    
    # Test on all assets
    results = []
    total = len(TEST_ASSETS)
    
    print(f"\n🌍 Testing on {total} asset/timeframe combinations...")
    print()
    
    for idx, asset_config in enumerate(TEST_ASSETS, 1):
        symbol = asset_config['symbol']
        timeframe = asset_config['timeframe']
        
        print(f"[{idx:2d}/{total}] {symbol:12s} {timeframe:4s} ... ", end='', flush=True)
        
        stats, error = run_backtest_on_asset(strategy_class, asset_config)
        
        if error:
            print(f"❌ {error}")
            continue
        
        if stats:
            ret = stats['Return %']
            color = '✅' if ret > 0 else '⚠️'
            print(f"{color} Return: {ret:7.2f}%")
            
            # Create result row
            result = {
                'Strategy Name': strategy_name,
                'Thread ID': 'MULTI',
                'Return %': stats['Return %'],
                'Buy & Hold %': stats['Buy & Hold %'],
                'Max Drawdown %': stats['Max Drawdown %'],
                'Sharpe Ratio': stats['Sharpe Ratio'],
                'Sortino Ratio': stats['Sortino Ratio'],
                'EV %': stats['EV %'],
                'Trades': stats['Trades'],
                'File Path': str(strategy_file),
                'Data': asset_config['file'],
                'Time': datetime.now().strftime("%m/%d %H:%M")
            }
            results.append(result)
    
    print(f"\n✅ Completed {len(results)}/{total} backtests")
    
    if results:
        df = pd.DataFrame(results)
        avg_return = df['Return %'].mean()
        max_return = df['Return %'].max()
        positive = (df['Return %'] > 0).sum()
        
        print(f"\n📊 SUMMARY:")
        print(f"   Avg Return: {avg_return:7.2f}%")
        print(f"   Max Return: {max_return:7.2f}%")
        print(f"   Positive: {positive}/{len(results)}")
    
    return results

def save_results(all_results):
    """Append results to backtest_stats.csv"""
    if not all_results:
        print("\n⚠️ No results to save")
        return
    
    print(f"\n💾 Saving {len(all_results)} results to CSV...")
    
    # Create DataFrame
    df_new = pd.DataFrame(all_results)
    
    # Append to existing CSV
    if STATS_CSV.exists():
        df_existing = pd.read_csv(STATS_CSV)
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
    else:
        df_combined = df_new
    
    # Save
    df_combined.to_csv(STATS_CSV, index=False)
    
    print(f"✅ Saved! Total backtests in CSV: {len(df_combined)}")

def main():
    parser = argparse.ArgumentParser(description='Test strategies on multiple assets')
    parser.add_argument('--top', type=int, default=5, help='Number of top strategies to test (default: 5)')
    args = parser.parse_args()
    
    print("="*60)
    print("🌍 BB1151's Multi-Asset Strategy Tester")
    print("="*60)
    print(f"\n📊 Assets: BTC, ETH, SOL, ADA, XRP, SUI")
    print(f"⏱️  Timeframes: 5m, 15m, 30m, 1h")
    print(f"🧪 Total tests per strategy: 24")
    print(f"🎯 Testing top {args.top} strategies")
    
    # Load top strategies
    top_strategies = load_top_strategies(args.top)
    
    if not top_strategies.empty:
        all_results = []
        
        # Test each strategy
        for idx, strategy_info in top_strategies.iterrows():
            results = test_strategy_on_all_assets(strategy_info)
            all_results.extend(results)
        
        # Save all results
        save_results(all_results)
        
        print("\n" + "="*60)
        print(f"🎉 COMPLETE! Tested {len(top_strategies)} strategies")
        print(f"📊 Total new backtests: {len(all_results)}")
        print(f"💾 Results saved to: {STATS_CSV}")
        print("="*60)
        
        return 0
    else:
        print("\n❌ No strategies found to test")
        return 1

if __name__ == "__main__":
    sys.exit(main())
