#!/usr/bin/env python3
"""
🌙 Moon Dev's Live Backtest Monitor
Shows real-time updates of multi-asset backtesting
"""

import pandas as pd
from datetime import datetime, timedelta
import time
import os

def clear_screen():
    os.system('clear' if os.name != 'nt' else 'cls')

def monitor():
    last_count = 0
    
    while True:
        try:
            # Read CSV
            df = pd.read_csv('src/data/rbi_pp_multi/backtest_stats.csv')
            df['Time'] = pd.to_datetime(df['Time'], errors='coerce')
            
            clear_screen()
            
            print("=" * 80)
            print("🌙 MOON DEV'S LIVE BACKTEST MONITOR")
            print("=" * 80)
            print(f"\n⏰ Last Update: {datetime.now().strftime('%H:%M:%S')}")
            print(f"📊 Total Entries in CSV: {len(df)}")
            
            # Check for new entries
            if len(df) > last_count:
                new_count = len(df) - last_count
                print(f"\n🆕 NEW ENTRIES: +{new_count} since last check!")
                last_count = len(df)
            else:
                print(f"\n⏳ Waiting for new backtests...")
            
            # Get last 5 minutes
            five_min_ago = datetime.now() - timedelta(minutes=5)
            recent = df[df['Time'] > five_min_ago]
            
            if len(recent) > 0:
                print(f"\n📈 LAST 5 MINUTES: {len(recent)} entries")
                
                # Group by strategy
                recent_strategies = recent.groupby('Strategy Name').agg({
                    'Data': 'nunique',
                    'Return %': 'mean',
                    'Realistic': lambda x: (x == 'Yes').sum()
                }).reset_index()
                
                recent_strategies.columns = ['Strategy', 'Assets Tested', 'Avg Return', 'Realistic Count']
                recent_strategies = recent_strategies.sort_values('Assets Tested', ascending=False)
                
                print("\n🎯 RECENT STRATEGIES:")
                print("-" * 80)
                for idx, row in recent_strategies.head(10).iterrows():
                    strat = row['Strategy']
                    assets = int(row['Assets Tested'])
                    avg_ret = row['Avg Return']
                    realistic_cnt = int(row['Realistic Count'])
                    
                    multi_badge = "🌍" if assets > 1 else "🪙"
                    realistic_badge = "✅" if realistic_cnt > assets/2 else "⚠️" if realistic_cnt > 0 else "❌"
                    
                    print(f"{multi_badge} {realistic_badge} {strat:30s} | {assets:2d} assets | Avg: {avg_ret:+7.2f}%")
                
            else:
                print(f"\n⏳ No entries in last 5 minutes")
                print("   Agents are processing... check RBI log for activity")
            
            # Show most recent entries (last 10)
            print("\n📝 MOST RECENT ENTRIES (Last 10):")
            print("-" * 80)
            last_10 = df.sort_values('Time', ascending=False).head(10)
            for idx, row in last_10.iterrows():
                strat = row['Strategy Name'][:25]
                data = row['Data'][:30]
                ret = row['Return %']
                realistic = row['Realistic']
                
                real_icon = "✅" if realistic == 'Yes' else "⚠️" if realistic == 'No' else "❓"
                
                print(f"{real_icon} {strat:25s} | {data:30s} | {ret:+7.2f}%")
            
            # Multi-asset summary
            print("\n🌍 MULTI-ASSET SUMMARY:")
            print("-" * 80)
            strategy_asset_counts = df.groupby('Strategy Name')['Data'].nunique()
            multi_asset = strategy_asset_counts[strategy_asset_counts > 1]
            single_asset = strategy_asset_counts[strategy_asset_counts == 1]
            
            print(f"   Multi-Asset Strategies:  {len(multi_asset):3d}")
            print(f"   Single-Asset Strategies: {len(single_asset):3d}")
            
            if len(multi_asset) > 0:
                avg_assets = multi_asset.mean()
                max_assets = multi_asset.max()
                print(f"   Avg Assets per Strategy: {avg_assets:.1f}")
                print(f"   Max Assets per Strategy: {int(max_assets)}")
            
            print("\n" + "=" * 80)
            print("🔄 Auto-refresh in 10 seconds... (Ctrl+C to stop)")
            print("=" * 80)
            
            time.sleep(10)
            
        except KeyboardInterrupt:
            print("\n\n👋 Monitoring stopped!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    print("🌙 Starting Live Backtest Monitor...")
    print("   Press Ctrl+C to stop\n")
    time.sleep(2)
    monitor()
