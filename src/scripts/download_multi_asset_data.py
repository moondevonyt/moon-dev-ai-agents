"""
🌙 BB1151's Multi-Asset Data Downloader
Downloads OHLCV data for 6 cryptocurrencies across 4 timeframes

Assets: BTC, ETH, SOL, ADA, XRP, SUI
Timeframes: 5m, 15m, 30m, 1h
Total: 24 CSV files (6 assets × 4 timeframes)
"""
import ccxt
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import time

# Configuration
EXCHANGE = ccxt.binance()
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "ohlcv"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Assets to download (Binance format)
ASSETS = [
    'BTC/USDT',
    'ETH/USDT', 
    'SOL/USDT',
    'ADA/USDT',
    'XRP/USDT',
    'SUI/USDT'
]

# Timeframes
TIMEFRAMES = {
    '5m': '5m',
    '15m': '15m',
    '30m': '30m',
    '1h': '1h'
}

# Download last 90 days of data
DAYS_BACK = 90

def download_ohlcv(symbol: str, timeframe: str) -> pd.DataFrame:
    """Download OHLCV data from Binance"""
    print(f"📥 Downloading {symbol} {timeframe}...")
    
    # Calculate start time (90 days ago)
    since = int((datetime.now() - timedelta(days=DAYS_BACK)).timestamp() * 1000)
    
    all_candles = []
    
    while True:
        try:
            candles = EXCHANGE.fetch_ohlcv(symbol, timeframe, since=since, limit=1000)
            
            if not candles:
                break
            
            all_candles.extend(candles)
            since = candles[-1][0] + 1  # Next timestamp
            
            # Check if we've reached current time
            if candles[-1][0] >= int(datetime.now().timestamp() * 1000):
                break
            
            time.sleep(0.5)  # Rate limiting
            
        except Exception as e:
            print(f"❌ Error downloading {symbol} {timeframe}: {e}")
            time.sleep(2)
            continue
    
    # Convert to DataFrame
    df = pd.DataFrame(all_candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
    df = df[['datetime', 'open', 'high', 'low', 'close', 'volume']]
    
    print(f"✅ Downloaded {len(df)} candles for {symbol} {timeframe}")
    return df

def main():
    """Download all assets and timeframes"""
    print("🌙 BB1151's Multi-Asset Data Downloader")
    print("="*60)
    print(f"📊 Downloading {len(ASSETS)} assets × {len(TIMEFRAMES)} timeframes")
    print(f"📅 Last {DAYS_BACK} days of data")
    print(f"💾 Output: {OUTPUT_DIR}")
    print("="*60 + "\n")
    
    total = len(ASSETS) * len(TIMEFRAMES)
    completed = 0
    
    for asset in ASSETS:
        for tf_name, tf_value in TIMEFRAMES.items():
            try:
                # Download data
                df = download_ohlcv(asset, tf_value)
                
                # Save to CSV
                symbol_clean = asset.replace('/', '-')
                filename = f"{symbol_clean}-{tf_name}.csv"
                filepath = OUTPUT_DIR / filename
                
                df.to_csv(filepath, index=False)
                print(f"💾 Saved: {filename} ({len(df)} rows)\n")
                
                completed += 1
                print(f"Progress: {completed}/{total} ({completed/total*100:.1f}%)\n")
                
            except Exception as e:
                print(f"❌ Failed to download {asset} {tf_name}: {e}\n")
                continue
    
    print("\n" + "="*60)
    print(f"✅ Download complete! {completed}/{total} files")
    print(f"📁 Files saved to: {OUTPUT_DIR}")
    print("="*60)
    
    # Show summary
    print("\n📊 Downloaded files:")
    for csv_file in sorted(OUTPUT_DIR.glob("*.csv")):
        size_kb = csv_file.stat().st_size / 1024
        print(f"  - {csv_file.name} ({size_kb:.1f} KB)")

if __name__ == "__main__":
    main()
