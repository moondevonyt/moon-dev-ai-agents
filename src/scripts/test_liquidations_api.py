"""
🌙 Moon Dev: Test script to fetch and analyze liquidation data
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.api import MoonDevAPI
from datetime import datetime

print("🌙 Moon Dev: Testing Liquidation API...")

# Initialize API
api = MoonDevAPI()

# Get last 10,000 liquidations
print("\n📡 Fetching last 10,000 liquidations from API...")
df = api.get_liquidation_data(limit=10000)

if df is None or df.empty:
    print("❌ No data received!")
    sys.exit(1)

print(f"\n✅ Received {len(df)} liquidations")
print(f"\n📊 Columns (first row used as headers): {list(df.columns)}")
print(f"\n🔍 First few rows:")
print(df.head())

# The columns are actually: symbol, side, order_type, time_in_force, original_quantity,
# price, average_price, order_status, order_last_filled_quantity,
# order_filled_accumulated_quantity, order_trade_time, usd_size

# Rename columns properly
column_names = [
    'symbol', 'side', 'order_type', 'time_in_force', 'original_quantity',
    'price', 'average_price', 'order_status', 'order_last_filled_quantity',
    'order_filled_accumulated_quantity', 'order_trade_time', 'usd_size', 'datetime'
]

# Check if we need to add the first row back (it's being used as headers)
print(f"\n🔧 Fixing column names...")
df.columns = column_names

print(f"\n✅ Renamed columns: {list(df.columns)}")
print(f"\n🔍 Fixed data:")
print(df.head())

# Check timestamp
print(f"\n⏰ Timestamp column:")
print(f"   Type: {df['order_trade_time'].dtype}")
print(f"   Sample: {df['order_trade_time'].iloc[0]}")

# Check USD size
print(f"\n💰 USD Size column:")
print(f"   Type: {df['usd_size'].dtype}")
print(f"   Min: ${df['usd_size'].min():,.2f}")
print(f"   Max: ${df['usd_size'].max():,.2f}")
print(f"   Mean: ${df['usd_size'].mean():,.2f}")

# Calculate timeframe stats
print("\n⏱️ Calculating timeframe stats...")
now = datetime.now().timestamp() * 1000  # Convert to milliseconds

stats = {
    "1h": {"count": 0, "volume": 0},
    "4h": {"count": 0, "volume": 0},
    "12h": {"count": 0, "volume": 0},
    "24h": {"count": 0, "volume": 0}
}

for _, row in df.iterrows():
    ts = int(row['order_trade_time'])
    usd = float(row['usd_size'])

    # 1 hour
    if ts >= now - (1 * 3600 * 1000):
        stats['1h']['count'] += 1
        stats['1h']['volume'] += usd

    # 4 hours
    if ts >= now - (4 * 3600 * 1000):
        stats['4h']['count'] += 1
        stats['4h']['volume'] += usd

    # 12 hours
    if ts >= now - (12 * 3600 * 1000):
        stats['12h']['count'] += 1
        stats['12h']['volume'] += usd

    # 24 hours
    if ts >= now - (24 * 3600 * 1000):
        stats['24h']['count'] += 1
        stats['24h']['volume'] += usd

print("\n📊 Stats by timeframe:")
for tf, data in stats.items():
    print(f"   {tf}: {data['count']} liquidations, ${data['volume']:,.2f} volume")

# Show categorization
print("\n🔖 Categorizing liquidations...")
mini = df[df['usd_size'].between(3000, 25000)]
big = df[df['usd_size'].between(25000, 100000)]
major = df[df['usd_size'] > 100000]

print(f"   💧 Mini ($3k-$25k): {len(mini)}")
print(f"   🔶 Big ($25k-$100k): {len(big)}")
print(f"   💎 Major (>$100k): {len(major)}")

print("\n✅ Test complete!")
