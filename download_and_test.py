"""
🌙 Download Crypto Data & Test AdaptiveVolatility Strategy
Downloads BTC, ETH, SOL data in 15m and 30m timeframes, then runs backtests
"""
import ccxt
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import time

def download_ohlcv(exchange_id='binance', symbol='BTC/USDT', timeframe='15m', days=90):
    """Download OHLCV data from exchange"""
    print(f"📥 Downloading {symbol} {timeframe} data ({days} days)...")
    
    try:
        exchange = getattr(ccxt, exchange_id)()
        
        # Calculate start time
        since = exchange.parse8601((datetime.now() - timedelta(days=days)).isoformat())
        
        # Download data
        all_ohlcv = []
        while True:
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=1000)
            if not ohlcv:
                break
            all_ohlcv.extend(ohlcv)
            since = ohlcv[-1][0] + 1
            
            # Check if we've reached present
            if ohlcv[-1][0] >= exchange.milliseconds() - exchange.parse_timeframe(timeframe) * 1000:
                break
            
            time.sleep(exchange.rateLimit / 1000)  # Respect rate limits
        
        # Convert to DataFrame
        df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
        df = df[['datetime', 'open', 'high', 'low', 'close', 'volume']]
        
        print(f"✅ Downloaded {len(df)} candles for {symbol} {timeframe}")
        return df
        
    except Exception as e:
        print(f"❌ Error downloading {symbol}: {str(e)}")
        return None

def main():
    # Setup
    project_root = Path(__file__).parent
    data_dir = project_root / "src" / "data" / "ohlcv"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Download configs
    configs = [
        {'symbol': 'BTC/USDT', 'file': 'BTC-USD-15m.csv', 'timeframe': '15m'},
        {'symbol': 'BTC/USDT', 'file': 'BTC-USD-30m.csv', 'timeframe': '30m'},
        {'symbol': 'ETH/USDT', 'file': 'ETH-USD-15m.csv', 'timeframe': '15m'},
        {'symbol': 'ETH/USDT', 'file': 'ETH-USD-30m.csv', 'timeframe': '30m'},
        {'symbol': 'SOL/USDT', 'file': 'SOL-USD-15m.csv', 'timeframe': '15m'},
        {'symbol': 'SOL/USDT', 'file': 'SOL-USD-30m.csv', 'timeframe': '30m'},
    ]
    
    print("\n" + "="*80)
    print("🌙 Moon Dev's Data Downloader & Backtest Runner 🌙")
    print("="*80 + "\n")
    
    # Download all data
    for config in configs:
        file_path = data_dir / config['file']
        
        # Skip if already exists
        if file_path.exists():
            print(f"⏭️  {config['file']} already exists, skipping...")
            continue
        
        df = download_ohlcv(symbol=config['symbol'], timeframe=config['timeframe'], days=90)
        
        if df is not None:
            df.to_csv(file_path, index=False)
            print(f"💾 Saved to {file_path}\n")
    
    print("\n" + "="*80)
    print("✅ Data download complete! Now running backtests...")
    print("="*80 + "\n")
    
    # Run the multi-asset test
    import subprocess
    result = subprocess.run(['/usr/bin/python3', 'test_adaptive_volatility_multi.py'], 
                          capture_output=False, text=True)
    
    if result.returncode == 0:
        print("\n✅ Backtest complete!")
    else:
        print(f"\n❌ Backtest failed with code {result.returncode}")

if __name__ == "__main__":
    main()
