"""
🌙 Moon Dev's API Handler
Built with love by Moon Dev 🚀

disclaimer: this is not financial advice and there is no guarantee of any kind. use at your own risk.

Quick Start Guide:
-----------------
1. Install required packages:
   ```
   pip install requests pandas python-dotenv
   ```

2. Create a .env file in your project root:
   ```
   MOONDEV_API_KEY=your_api_key_here
   ```

3. Basic Usage:
   ```python
   from agents.api import MoonDevAPI

   # Initialize with env variable (recommended)
   api = MoonDevAPI()

   # Or initialize with direct key
   api = MoonDevAPI(api_key="your_key_here")

   # Get limited liquidation data (recommended for testing)
   liquidations = api.get_liquidation_data(limit=50000)  # Last 50,000 rows

   # Get ALL liquidation data (full 1.5GB dataset - takes longer)
   all_liquidations = api.get_liquidation_data()  # All data (~17M records)

   # Other data endpoints
   funding = api.get_funding_data()
   oi = api.get_oi_data()
   ```

Available Methods:
----------------
- get_liquidation_data(limit=None): Get historical liquidation data
  * limit=50000: Gets last 50,000 records (recommended for testing) - fast download
  * limit=None: Gets ALL data (~17M records, 1.5GB dataset) - full historical data
  * Data is sorted chronologically (oldest first, like OHLCV data)
  * Recent data is downloaded first, then filtered/sorted as needed
- get_funding_data(): Get current funding rate data for various tokens
- get_token_addresses(): Get new Solana token launches and their addresses
- get_oi_data(): Get detailed open interest data for ETH or BTC individually
- get_oi_total(): Get total open interest data for ETH & BTC combined
- get_copybot_follow_list(): Get Moon Dev's personal copy trading follow list (for reference only - DYOR!)
- get_copybot_recent_transactions(): Get recent transactions from the followed wallets above
- get_agg_positions_hlp(): Get aggregated positions on HLP data
- get_positions_hlp(): Get detailed positions on HLP data
- get_whale_addresses(): Get list of whale addresses

Data Details:
------------
- Liquidation Data: Historical liquidation events with timestamps and amounts
- Funding Rates: Current funding rates across different tokens
- Token Addresses: New token launches on Solana with contract addresses
- Open Interest: Both detailed (per-token) and combined OI metrics
- CopyBot Data: Moon Dev's personal trading signals (use as reference only, always DYOR!)

Rate Limits:
-----------
- 100 requests per minute per API key
- Larger datasets (like liquidations) recommended to use limit parameter

⚠️ Important Notes:
-----------------
1. This is not financial advice
2. There are no guarantees of any kind
3. Use at your own risk
4. Always do your own research (DYOR)
5. The copybot follow list is Moon Dev's personal list and should not be used alone

Need an API key? for a limited time, bootcamp members get free api keys for claude, openai, helius, birdeye & quant elite gets access to the moon dev api. join here: https://algotradecamp.com
"""

import os
import pandas as pd
import requests
from datetime import datetime
import time
from pathlib import Path
import numpy as np
import traceback
import json
import io
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent

class MoonDevAPI:
    def __init__(self, api_key=None, base_url="http://api.moondev.com:8000"):
        """Initialize the API handler"""
        # Simplified data directory path
        self.base_dir = PROJECT_ROOT / "src" / "agents" / "api_data"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.api_key = api_key or os.getenv('MOONDEV_API_KEY')
        self.base_url = base_url
        self.headers = {'X-API-Key': self.api_key} if self.api_key else {}
        self.session = requests.Session()
        self.max_retries = 3
        self.chunk_size = 8192  # Smaller chunk size for more reliable downloads

        # Chunked download configuration
        self.chunk_size_mb = 2  # Download in 2MB chunks
        self.column_names = [
            'order_trade_time', 'symbol', 'side', 'size', 'price', 'tick_direction',
            'timestamp', 'cross_seq', 'position_idx', 'order_id'
        ]

    def _fetch_csv(self, filename, limit=None):
        """Fetch CSV data from the API with retry logic"""
        max_retries = 3
        retry_delay = 2  # seconds

        for attempt in range(max_retries):
            try:
                url = f'{self.base_url}/files/{filename}'
                if limit:
                    url += f'?limit={limit}'

                # Use stream=True for better handling of large files
                response = self.session.get(url, headers=self.headers, stream=True)
                response.raise_for_status()

                # Save streamed content to a temporary file first
                temp_file = self.base_dir / f"temp_{filename}"
                with open(temp_file, 'wb') as f:
                    # Use a larger chunk size for better performance
                    for chunk in response.iter_content(chunk_size=8192*16):
                        if chunk:
                            f.write(chunk)

                # Once download is complete, read the file
                df = pd.read_csv(temp_file)

                # Move temp file to final location
                final_file = self.base_dir / filename
                temp_file.rename(final_file)

                return df

            except (requests.exceptions.ChunkedEncodingError,
                    requests.exceptions.ConnectionError,
                    requests.exceptions.RequestException) as e:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    print(f"💥 Error fetching {filename} after {max_retries} attempts: {str(e)}")
                    print(f"📋 Stack trace:\n{traceback.format_exc()}")
                    return None

            except Exception as e:
                print(f"💥 Unexpected error fetching {filename}: {str(e)}")
                print(f"📋 Stack trace:\n{traceback.format_exc()}")
                return None

    def _fetch_liquidation_chunked(self, limit=None):
        """
        🌙 Moon Dev Enhanced Liquidation Data Download

        Downloads liquidation data efficiently. For limited requests, uses existing API.
        For full data, downloads and sorts chronologically like OHLCV data.
        """
        try:
            if limit is not None:
                # For limited requests, use the existing efficient API
                print(f"🎯 Moon Dev: Getting last {limit:,} liquidation records...")
                df = self._fetch_csv("liq_data.csv", limit=limit)

                if df is not None:
                    # Find timestamp column (usually the largest numeric column that looks like epoch time)
                    timestamp_col = None
                    for col in df.columns:
                        try:
                            # Check if column name contains timestamp-like numbers or if values look like timestamps
                            if str(col).isdigit() and len(str(col)) == 13:  # Column name itself is 13-digit timestamp
                                timestamp_col = col
                                break
                            elif pd.api.types.is_numeric_dtype(df[col]):
                                sample_val = df[col].iloc[0]
                                if isinstance(sample_val, (int, float)) and sample_val > 1000000000000:  # Epoch milliseconds
                                    timestamp_col = col
                                    break
                        except:
                            continue

                    if timestamp_col:
                        df['datetime'] = pd.to_datetime(df[timestamp_col], unit='ms')
                        # Sort oldest first (like OHLCV data)
                        df = df.sort_values('datetime', ascending=True)
                        print(f"✅ Moon Dev: Got {len(df):,} records")
                        print(f"📅 Date range: {df['datetime'].min()} → {df['datetime'].max()}")
                        print(f"🎯 Data sorted chronologically (oldest→newest like OHLCV)")
                    else:
                        print(f"✅ Moon Dev: Got {len(df):,} records (timestamp column not identified)")

                return df

            else:
                # For unlimited requests, use proven CHUNKED download approach
                print("🌙 Moon Dev: Downloading FULL liquidation dataset (1.5GB+)...")
                print("🚀 Using proven chunked download approach from file END")

                return self._download_complete_chunked_dataset()

        except Exception as e:
            print(f"💥 Error in liquidation data download: {str(e)}")
            print(f"📋 Stack trace:\n{traceback.format_exc()}")
            return None

    def _get_file_size(self, url):
        """Get total file size using range request"""
        try:
            headers = self.headers.copy()
            headers['Range'] = 'bytes=0-1'

            response = self.session.get(url, headers=headers, timeout=30)

            if response.status_code == 206:  # Partial Content
                content_range = response.headers.get('content-range')
                if content_range:
                    total_size = int(content_range.split('/')[-1])
                    return total_size

            return None

        except Exception as e:
            print(f"💥 Moon Dev error getting file size: {e}")
            return None

    def _download_chunk_range(self, url, start_byte, end_byte, chunk_number):
        """Download a specific byte range"""
        try:
            headers = self.headers.copy()
            headers['Range'] = f'bytes={start_byte}-{end_byte}'

            response = self.session.get(url, headers=headers, timeout=(30, 120))

            if response.status_code == 206:  # Partial Content
                return response.content
            elif response.status_code == 200:
                return response.content
            else:
                print(f"💥 Moon Dev unexpected status code: {response.status_code}")
                return None

        except Exception as e:
            print(f"💥 Moon Dev error downloading chunk {chunk_number}: {e}")
            return None

    def _parse_liquidation_chunk(self, chunk_bytes):
        """Parse chunk bytes into list of liquidation records - PROVEN WORKING VERSION"""
        try:
            chunk_str = chunk_bytes.decode('utf-8')
            lines = [line.strip() for line in chunk_str.strip().split('\n') if line.strip()]

            records = []
            # Use the PROVEN column structure from api_chunks_fixed.py
            column_names = [
                "symbol", "side", "order_type", "time_in_force",
                "original_quantity", "price", "average_price", "order_status",
                "order_last_filled_quantity", "order_filled_accumulated_quantity",
                "order_trade_time", "usd_size"
            ]

            for line in lines:
                fields = line.split(',')
                if len(fields) >= 12:  # Should have at least 12 fields
                    try:
                        # Create record with proper column names (PROVEN METHOD)
                        record = {}
                        for i, col_name in enumerate(column_names):
                            if i < len(fields):
                                record[col_name] = fields[i].strip()

                        # Convert timestamp to int for sorting (order_trade_time is column 10)
                        if record.get('order_trade_time', '').isdigit():
                            record['order_trade_time'] = int(record['order_trade_time'])
                            records.append(record)
                    except Exception:
                        continue

            return records

        except Exception as e:
            print(f"💥 Moon Dev error parsing chunk: {e}")
            return []

    def _download_complete_chunked_dataset(self):
        """
        🌙 Moon Dev's NEW streaming download for complete 1.5GB dataset
        Uses chunked transfer encoding - no Content-Length header required!
        """
        url = f'{self.base_url}/files/liq_data.csv'

        print(f"🚀 Moon Dev: Starting NEW chunked streaming download...")
        print(f"✨ Using server's chunked transfer encoding - no file size needed!")

        try:
            # Use streaming request with iter_content - this is the KEY change!
            response = self.session.get(url, headers=self.headers, stream=True, timeout=(30, None))
            response.raise_for_status()

            print(f"📡 Moon Dev: Connected! Status: {response.status_code}")
            print(f"📋 Transfer-Encoding: {response.headers.get('Transfer-Encoding', 'not chunked')}")

            # Save to file using streaming
            full_data_path = self.base_dir / "liq_data_full.csv"
            print(f"💾 Moon Dev: Saving to {full_data_path}")

            chunk_size = 65536  # 64KB chunks as recommended by server team
            chunk_count = 0
            total_bytes = 0

            with open(full_data_path, 'wb') as f:
                print("🚀 Moon Dev: Starting chunked download...")
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        chunk_count += 1
                        total_bytes += len(chunk)

                        # Progress update every 1000 chunks (~64MB)
                        if chunk_count % 1000 == 0:
                            mb_downloaded = total_bytes / (1024**2)
                            print(f"📡 Moon Dev: Downloaded {chunk_count} chunks ({mb_downloaded:.1f} MB so far)... 🌙")

            print(f"✅ Moon Dev: Download complete! {chunk_count} chunks, {total_bytes:,} total bytes")

            # Verify file was saved and load as DataFrame
            if full_data_path.exists():
                file_size_mb = full_data_path.stat().st_size / (1024**2)
                print(f"📊 Moon Dev: File saved successfully! Size: {file_size_mb:.1f} MB")

                # Load into DataFrame
                print("📈 Moon Dev: Loading data into DataFrame...")
                df = pd.read_csv(full_data_path)

                # Check for datetime column and sort
                if 'datetime' in df.columns:
                    df['datetime'] = pd.to_datetime(df['datetime'])
                    df = df.sort_values('datetime', ascending=True)
                    print(f"📅 Date range: {df['datetime'].min()} → {df['datetime'].max()}")
                elif 'order_trade_time' in df.columns:
                    df['datetime'] = pd.to_datetime(df['order_trade_time'], unit='ms')
                    df = df.sort_values('datetime', ascending=True)
                    print(f"📅 Date range: {df['datetime'].min()} → {df['datetime'].max()}")

                print(f"✅ Moon Dev COMPLETE DATASET SUCCESS!")
                print(f"   📊 Total records: {len(df):,}")
                print(f"   💾 File size: {file_size_mb:.1f} MB")
                print(f"   🎯 Data sorted chronologically (oldest→newest like OHLCV)")

                return df
            else:
                print("💥 Moon Dev: File was not saved properly!")
                return None

        except requests.exceptions.Timeout:
            print("⏰ Moon Dev: Request timed out - server may be processing large file")
            print("💡 Try again or contact server admin to increase timeout")
            return None

        except requests.exceptions.ChunkedEncodingError as e:
            print(f"📦 Moon Dev: Chunk encoding error - partial download may have occurred")
            print(f"Error: {str(e)[:200]}")
            return None

        except Exception as e:
            print(f"💥 Moon Dev error downloading full dataset: {str(e)}")
            print(f"📋 Stack trace:\n{traceback.format_exc()}")
            return None

    def get_liquidation_data(self, limit=None):
        """
        🌙 Moon Dev Enhanced Liquidation Data

        Get historical liquidation data with advanced chunked downloading.
        Downloads recent data first for efficiency.

        Args:
            limit (int, optional): Number of most recent records to return
                - None: Get ALL data (~17M records, full 1.5GB dataset)
                - 50000: Get last 50,000 records (recommended for testing)
                - Any number: Get that many most recent records

        Returns:
            pandas.DataFrame: Liquidation data sorted chronologically (oldest first)
        """
        try:
            print(f"🌙 Moon Dev: Getting liquidation data (limit={limit})...")

            # Use the chunked API approach for better performance
            return self._fetch_liquidation_chunked(limit=limit)

        except Exception as e:
            print(f"💥 Error in get_liquidation_data: {str(e)}")
            print(f"📋 Stack trace:\n{traceback.format_exc()}")
            return None

    def get_funding_data(self):
        """Get funding data from API"""
        return self._fetch_csv("funding.csv")

    def get_token_addresses(self):
        """Get token addresses from API"""
        return self._fetch_csv("new_token_addresses.csv")

    def get_oi_total(self):
        """Get total open interest data from API"""
        return self._fetch_csv("oi_total.csv")

    def get_oi_data(self):
        """Get detailed open interest data from API"""
        max_retries = 3
        retry_delay = 2  # seconds

        for attempt in range(max_retries):
            try:
                url = f'{self.base_url}/files/oi.csv'

                # Use stream=True and a larger chunk size
                response = self.session.get(url, headers=self.headers, stream=True)
                response.raise_for_status()

                # Save streamed content to a temporary file first
                temp_file = self.base_dir / "temp_oi.csv"
                with open(temp_file, 'wb') as f:
                    # Use a larger chunk size for better performance
                    for chunk in response.iter_content(chunk_size=8192*16):
                        if chunk:
                            f.write(chunk)

                # Once download is complete, read the file
                df = pd.read_csv(temp_file)

                # Move temp file to final location
                final_file = self.base_dir / "oi.csv"
                temp_file.rename(final_file)

                return df

            except (requests.exceptions.ChunkedEncodingError,
                    requests.exceptions.ConnectionError,
                    requests.exceptions.RequestException) as e:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    print(f"💥 Error fetching oi.csv after {max_retries} attempts: {str(e)}")
                    print(f"📋 Stack trace:\n{traceback.format_exc()}")
                    return None

            except Exception as e:
                print(f"💥 Unexpected error fetching oi.csv: {str(e)}")
                print(f"📋 Stack trace:\n{traceback.format_exc()}")
                return None

    def get_copybot_follow_list(self):
        """Get current copy trading follow list"""
        try:
            print("📋 Moon Dev CopyBot: Fetching follow list...")
            if not self.api_key:
                print("❗ API key is required for copybot endpoints")
                return None

            response = self.session.get(
                f"{self.base_url}/copybot/data/follow_list",
                headers=self.headers
            )

            if response.status_code == 403:
                print("❗ Invalid API key or insufficient permissions")
                print(f"🔑 Please check your API key in .env file")
                return None

            response.raise_for_status()

            # Save to cache and read
            save_path = self.base_dir / "follow_list.csv"
            with open(save_path, 'wb') as f:
                f.write(response.content)

            df = pd.read_csv(save_path)
            print(f"✨ Successfully loaded {len(df)} rows from follow list")
            return df

        except Exception as e:
            print(f"💥 Error fetching follow list: {str(e)}")
            if "403" in str(e):
                print("❗ Make sure your API key is set in the .env file and has the correct permissions")
            return None

    def get_copybot_recent_transactions(self):
        """Get recent copy trading transactions"""
        try:
            print("🔄 Moon Dev CopyBot: Fetching recent transactions...")
            if not self.api_key:
                print("❗ API key is required for copybot endpoints")
                return None

            response = self.session.get(
                f"{self.base_url}/copybot/data/recent_txs",
                headers=self.headers
            )

            if response.status_code == 403:
                print("❗ Invalid API key or insufficient permissions")
                print(f"🔑 Please check your API key in .env file")
                return None

            response.raise_for_status()

            # Save directly to moondev_api data directory
            save_path = self.base_dir / "recent_txs.csv"
            with open(save_path, 'wb') as f:
                f.write(response.content)

            df = pd.read_csv(save_path)
            print(f"✨ Successfully loaded {len(df)} rows from recent transactions")
            print(f"💾 Data saved to: {save_path}")
            return df

        except Exception as e:
            print(f"💥 Error fetching recent transactions: {str(e)}")
            if "403" in str(e):
                print("❗ Make sure your API key is set in the .env file and has the correct permissions")
            return None

    def get_agg_positions_hlp(self):
        """Get aggregated positions on HLP data"""
        return self._fetch_csv("agg_positions_on_hlp.csv")

    def get_positions_hlp(self):
        """Get detailed positions on HLP data"""
        return self._fetch_csv("positions_on_hlp.csv")

    def get_whale_addresses(self):
        """Get list of whale addresses"""
        try:
            print("🐋 Moon Dev API: Fetching whale addresses...")

            url = f'{self.base_url}/files/whale_addresses.txt'
            response = self.session.get(url, headers=self.headers)
            response.raise_for_status()

            # Save directly to moondev_api data directory
            save_path = self.base_dir / "whale_addresses.txt"
            with open(save_path, 'wb') as f:
                f.write(response.content)

            # Read the text file
            with open(save_path, 'r') as f:
                addresses = f.read().splitlines()

            print(f"✨ Successfully loaded {len(addresses)} whale addresses")
            print(f"💾 Data saved to: {save_path}")
            return addresses

        except Exception as e:
            print(f"💥 Error fetching whale addresses: {str(e)}")
            return None

if __name__ == "__main__":
    print("🌙 Moon Dev API Test Suite 🚀")
    print("=" * 50)

    # Initialize API
    api = MoonDevAPI()

    # Test Historical Liquidation Data
    print("\n💥 Testing Liquidation Data...")
    liq_data = api.get_liquidation_data(limit=50000)
    if liq_data is not None:
        print(f"✨ Latest Liquidation Data Preview:\n{liq_data.head()}")

    print("\n✨ Moon Dev API Test Complete! ✨")
    print("\n💡 Note: Make sure to set MOONDEV_API_KEY in your .env file")
