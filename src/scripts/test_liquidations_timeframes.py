"""
🌙 Moon Dev: Test script to debug liquidation timeframes
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.api import MoonDevAPI
from datetime import datetime, timedelta

print("🌙 Moon Dev: Testing Liquidation Timeframes...")
print("=" * 80)

# Test different limits to see how far back the data goes
limits = [10000, 25000, 50000, 100000]

for limit in limits:
    print(f"\n{'='*80}")
    print(f"📊 Testing with limit={limit:,} liquidations")
    print(f"{'='*80}")

    # Initialize API
    api = MoonDevAPI()

    # Get liquidations
    print(f"\n📡 Fetching last {limit:,} liquidations from API...")
    df = api.get_liquidation_data(limit=limit)

    if df is None or df.empty:
        print(f"❌ No data received for limit={limit}")
        continue

    # Fix column names
    column_names = [
        'symbol', 'side', 'order_type', 'time_in_force', 'original_quantity',
        'price', 'average_price', 'order_status', 'order_last_filled_quantity',
        'order_filled_accumulated_quantity', 'order_trade_time', 'usd_size', 'datetime'
    ]
    df.columns = column_names

    # Get time range
    oldest_ts = df['order_trade_time'].min()
    newest_ts = df['order_trade_time'].max()

    oldest_dt = datetime.fromtimestamp(oldest_ts / 1000)
    newest_dt = datetime.fromtimestamp(newest_ts / 1000)

    time_span = (newest_ts - oldest_ts) / (1000 * 3600)  # Convert to hours

    print(f"\n⏰ Time Range:")
    print(f"   Oldest: {oldest_dt}")
    print(f"   Newest: {newest_dt}")
    print(f"   Time Span: {time_span:.2f} hours ({time_span/24:.2f} days)")

    # Calculate stats for each timeframe
    now = datetime.now().timestamp() * 1000

    timeframes = {
        '1h': 1,
        '4h': 4,
        '12h': 12,
        '24h': 24
    }

    print(f"\n📊 Stats by timeframe:")
    for tf_name, hours in timeframes.items():
        threshold = now - (hours * 3600 * 1000)
        recent = df[df['order_trade_time'] >= threshold]

        if len(recent) > 0:
            total_volume = recent['usd_size'].sum()
            print(f"   {tf_name:4s}: {len(recent):5,} liquidations, ${total_volume:>15,.2f} volume")
        else:
            print(f"   {tf_name:4s}: NO DATA (threshold too recent)")

    # Check if we have enough data for 24h
    if time_span >= 24:
        print(f"\n✅ This limit provides FULL 24-hour coverage!")
        print(f"   Recommended: Use limit={limit:,} or higher")
        break
    else:
        hours_missing = 24 - time_span
        print(f"\n⚠️  Only {time_span:.2f} hours of data - missing {hours_missing:.2f} hours")
        print(f"   Need to increase limit to get full 24 hours")

print(f"\n{'='*80}")
print("✅ Test complete!")
print("=" * 80)
