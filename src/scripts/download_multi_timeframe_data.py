"""
📊 Multi-Timeframe OHLCV Data Downloader
Downloads all 54 required OHLCV files (6 assets × 9 timeframes)
"""

import sys
from pathlib import Path
import pandas as pd
import ccxt
from datetime import datetime, timedelta

# Add project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
CONFIG_DIR = PROJECT_ROOT / "src/config"
sys.path.insert(0, str(CONFIG_DIR))

from multi_timeframe_config import ASSETS, PRIMARY_TIMEFRAMES, INFORMATIVE_TIMEFRAMES

# Output directory
OHLCV_DIR = PROJECT_ROOT / "src/data/ohlcv"
OHLCV_DIR.mkdir(parents=True, exist_ok=True)

# Exchange
exchange = ccxt.binance({
    'enableRateLimit': True,
    'options': {'defaultType': 'future'}
})

# Timeframe limits (how far back to fetch)
TIMEFRAME_LIMITS = {
    '1m': 7,      # 7 days
    '5m': 30,     # 30 days
    '15m': 60,    # 60 days
    '30m': 90,    # 90 days
    '1h': 180,    # 180 days
    '2h': 365,    # 1 year
    '4h': 365,    # 1 year
    '1d': 730,    # 2 years
    '1w': 1095,   # 3 years
}

def download_ohlcv(symbol, timeframe):
    """Download OHLCV data for a symbol and timeframe"""
    
    output_file = OHLCV_DIR / f"{symbol}-{timeframe}.csv"
    
    # Skip if already exists
    if output_file.exists():
        file_age_hours = (datetime.now().timestamp() - output_file.stat().st_mtime) / 3600
        if file_age_hours < 24:  # Skip if less than 24 hours old
            print(f"   ⏭️  Skipping {symbol}-{timeframe} (file exists, {file_age_hours:.1f}h old)")
            return True
    
    try:
        print(f"   📥 Downloading {symbol} {timeframe}...", end=' ', flush=True)
        
        # Convert symbol format: BTC-USDT -> BTC/USDT for ccxt
        ccxt_symbol = symbol.replace('-', '/')
        
        # Calculate since timestamp
        days_back = TIMEFRAME_LIMITS.get(timeframe, 365)
        since = exchange.parse8601((datetime.now() - timedelta(days=days_back)).isoformat())
        
        # Fetch OHLCV
        all_ohlcv = []
        current_since = since
        
        while True:
            ohlcv = exchange.fetch_ohlcv(ccxt_symbol, timeframe, since=current_since, limit=1000)
            
            if not ohlcv:
                break
            
            all_ohlcv.extend(ohlcv)
            
            # Check if we got less than requested (end of data)
            if len(ohlcv) < 1000:
                break
            
            # Update since to last timestamp
            current_since = ohlcv[-1][0] + 1
            
            # Safety: don't fetch more than 100k candles
            if len(all_ohlcv) > 100000:
                break
        
        if not all_ohlcv:
            print(f"❌ No data")
            return False
        
        # Convert to DataFrame
        df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
        df = df[['datetime', 'open', 'high', 'low', 'close', 'volume']]
        
        # Save
        df.to_csv(output_file, index=False)
        
        print(f"✅ {len(df)} candles ({df['datetime'].min().date()} to {df['datetime'].max().date()})")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Download all required OHLCV files"""
    
    print("=" * 60)
    print("📊 Multi-Timeframe OHLCV Downloader")
    print("=" * 60)
    
    # Get all unique timeframes
    all_timeframes = sorted(set(PRIMARY_TIMEFRAMES + INFORMATIVE_TIMEFRAMES))
    
    print(f"\n📋 Assets: {len(ASSETS)}")
    print(f"⏱️  Timeframes: {len(all_timeframes)}")
    print(f"💾 Total files to download: {len(ASSETS) * len(all_timeframes)}")
    print(f"📁 Output: {OHLCV_DIR}")
    print()
    
    success_count = 0
    total_count = 0
    
    for asset in ASSETS:
        print(f"\n🪙 {asset}:")
        
        for tf in all_timeframes:
            total_count += 1
            if download_ohlcv(asset, tf):
                success_count += 1
    
    print("\n" + "=" * 60)
    print(f"✅ Downloaded: {success_count}/{total_count} files")
    print(f"📁 Location: {OHLCV_DIR}")
    print("=" * 60)
    
    return 0 if success_count == total_count else 1

if __name__ == "__main__":
    sys.exit(main())
