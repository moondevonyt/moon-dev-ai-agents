
import pandas as pd
import requests
from datetime import datetime, timedelta
import numpy as np
import time
from pathlib import Path


# Define symbol and timeframe
symbol = 'HYPE'
timeframe = '1d'

# Get project root and set up data directory
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "src" / "data" / "hyperliquid_data"

# Create data directory if it doesn't exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
print(f"📁 Moon Dev's data directory: {DATA_DIR}")


# Constants
BATCH_SIZE = 5000 # MAX IS 5000 FOR HYPERLIQUID IF YOU NEED MORE USE COINBASE
MAX_RETRIES = 3
MAX_ROWS = 5000  # New constant to limit the number of rows


# Global variable to store timestamp offset
timestamp_offset = None


def adjust_timestamp(dt):
    """Adjust API timestamps by subtracting the timestamp offset."""
    if timestamp_offset is not None:
        corrected_dt = dt - timestamp_offset
        return corrected_dt
    else:
        return dt  # No adjustment needed if offset is not set


def get_ohlcv2(symbol, interval, start_time, end_time, batch_size=BATCH_SIZE):
    global timestamp_offset
    print(f'\n🔍 Requesting data:')
    print(f'📊 Batch Size: {batch_size}')
    print(f'🚀 Start: {start_time.strftime("%Y-%m-%d %H:%M:%S")} UTC')
    print(f'🎯 End: {end_time.strftime("%Y-%m-%d %H:%M:%S")} UTC')


    start_ts = int(start_time.timestamp() * 1000)
    end_ts = int(end_time.timestamp() * 1000)


    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(
                'https://api.hyperliquid.xyz/info',
                headers={'Content-Type': 'application/json'},
                json={
                    "type": "candleSnapshot",
                    "req": {
                        "coin": symbol,
                        "interval": interval,
                        "startTime": start_ts,
                        "endTime": end_ts,
                        "limit": batch_size
                    }
                },
                timeout=10
            )


            if response.status_code == 200:
                snapshot_data = response.json()
                if snapshot_data:
                    # Manually calculate timestamp offset if not already done
                    if timestamp_offset is None:
                        latest_api_timestamp = datetime.utcfromtimestamp(snapshot_data[-1]['t'] / 1000)
                        # Your system's current date (adjust to your actual current date)
                        system_current_date = datetime.utcnow()
                        # Manually set the expected latest timestamp (e.g., now)
                        expected_latest_timestamp = system_current_date
                        # Calculate offset
                        timestamp_offset = latest_api_timestamp - expected_latest_timestamp
                        print(f"⏱️ Calculated timestamp offset: {timestamp_offset}")
                    # Adjust timestamps due to API bug
                    for candle in snapshot_data:
                        dt = datetime.utcfromtimestamp(candle['t'] / 1000)
                        # Adjust date
                        adjusted_dt = adjust_timestamp(dt)
                        candle['t'] = int(adjusted_dt.timestamp() * 1000)
                    first_time = datetime.utcfromtimestamp(snapshot_data[0]['t'] / 1000)
                    last_time = datetime.utcfromtimestamp(snapshot_data[-1]['t'] / 1000)
                    print(f'✨ Received {len(snapshot_data)} candles')
                    print(f'📈 First: {first_time}')
                    print(f'📉 Last: {last_time}')
                    return snapshot_data
                else:
                    print('❌ No data returned by API')
                    return None
            else:
                print(f'⚠️ HTTP Error {response.status_code}: {response.text}')
        except requests.exceptions.RequestException as e:
            print(f'⚠️ Request failed (attempt {attempt + 1}): {e}')
            time.sleep(1)
    return None


def process_data_to_df(snapshot_data):
    if snapshot_data:
        columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        data = []
        for snapshot in snapshot_data:
            timestamp = datetime.utcfromtimestamp(snapshot['t'] / 1000)
            open_price = snapshot['o']
            high_price = snapshot['h']
            low_price = snapshot['l']
            close_price = snapshot['c']
            volume = snapshot['v']
            data.append([timestamp, open_price, high_price, low_price, close_price, volume])


        df = pd.DataFrame(data, columns=columns)
        return df
    else:
        return pd.DataFrame()


def fetch_historical_data(symbol, timeframe):
    """Fetch 5000 rows of historical data."""
    print("\n🌙 MoonDev's Historical Data Fetcher")
    print(f"🎯 Symbol: {symbol}")
    print(f"⏰ Timeframe: {timeframe}")


    # Just fetch the most recent 5000 candles
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=60)  # Setting a wide enough window


    print("\n🔄 Fetching data:")
    print(f"📅 From: {start_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print(f"📅 To: {end_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")


    data = get_ohlcv2(symbol, timeframe, start_time, end_time, batch_size=5000)
    
    if not data:
        print("❌ No data available.")
        return pd.DataFrame()


    df = process_data_to_df(data)


    if not df.empty:
        # Sort by timestamp and take the most recent 5000 rows
        df = df.sort_values('timestamp', ascending=False).head(5000).sort_values('timestamp')
        df = df.reset_index(drop=True)


        print("\n📊 Final data summary:")
        print(f"📈 Total candles: {len(df)}")
        print(f"📅 Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        print("✨ Thanks for using MoonDev's Data Fetcher! ✨")


    return df


# Use the function
all_data = fetch_historical_data(symbol, timeframe)


# Save the data
if not all_data.empty:
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    file_path = DATA_DIR / f'{symbol}_{timeframe}_{timestamp}_historical.csv'
    all_data.to_csv(file_path, index=False)
    print(f'\n💾 Moon Dev saved data to: {file_path}')

    # Print the DataFrame
    print("\n" + "="*80)
    print("🌙 MOON DEV'S DATA PREVIEW 🌙")
    print("="*80)
    print(f"\n📊 First 10 rows:")
    print(all_data.head(10).to_string(index=False))
    print(f"\n📊 Last 10 rows:")
    print(all_data.tail(10).to_string(index=False))
    print("\n" + "="*80)
    print(f"📈 Total rows: {len(all_data)}")
    print(f"📊 Columns: {', '.join(all_data.columns)}")
    print("="*80 + "\n")
else:
    print('❌ No data to save.')
