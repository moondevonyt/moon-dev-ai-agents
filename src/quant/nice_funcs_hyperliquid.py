"""
🌙 Moon Dev's HyperLiquid Trading Functions
Focused functions for HyperLiquid perps trading
Built with love by Moon Dev 🚀

LEVERAGE & POSITION SIZING:
- All 'amount' parameters represent NOTIONAL position size (total exposure)
- Leverage is applied by the exchange, reducing required margin
- Example: $25 position at 5x leverage = $25 notional, $5 margin required
- Formula: Required Margin = Notional Position / Leverage
- Default leverage: 5x (configurable below)
"""

import os
import json
import time
import requests
import pandas as pd
import numpy as np
import pandas_ta as ta
import datetime
from datetime import timedelta
from termcolor import colored, cprint
from eth_account.signers.local import LocalAccount
import eth_account
from hyperliquid.info import Info
from hyperliquid.exchange import Exchange
from hyperliquid.utils import constants
from dotenv import load_dotenv
import traceback

# Load environment variables
load_dotenv()

# Hide all warnings
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION
# ============================================================================
DEFAULT_LEVERAGE = 5  # Change this to adjust leverage globally (1-50x on HyperLiquid)
                      # Higher leverage = less margin required, but higher liquidation risk
                      # Examples:
                      # - 5x: $25 position needs $5 margin
                      # - 10x: $25 position needs $2.50 margin
                      # - 20x: $25 position needs $1.25 margin

# Constants
BATCH_SIZE = 5000  # MAX IS 5000 FOR HYPERLIQUID
MAX_RETRIES = 3
MAX_ROWS = 5000
BASE_URL = 'https://api.hyperliquid.xyz/info'

# Global variable to store timestamp offset
timestamp_offset = None

def adjust_timestamp(dt):
    """Adjust API timestamps by subtracting the timestamp offset."""
    if timestamp_offset is not None:
        corrected_dt = dt - timestamp_offset
        return corrected_dt
    return dt

def ask_bid(symbol):
    """Get ask and bid prices for a symbol"""
    url = 'https://api.hyperliquid.xyz/info'
    headers = {'Content-Type': 'application/json'}

    data = {
        'type': 'l2Book',
        'coin': symbol
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))
    l2_data = response.json()
    l2_data = l2_data['levels']

    # get bid and ask
    bid = float(l2_data[0][0]['px'])
    ask = float(l2_data[1][0]['px'])

    return ask, bid, l2_data

def get_sz_px_decimals(symbol):
    """Get size and price decimals for a symbol"""
    url = 'https://api.hyperliquid.xyz/info'
    headers = {'Content-Type': 'application/json'}
    data = {'type': 'meta'}

    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        data = response.json()
        symbols = data['universe']
        symbol_info = next((s for s in symbols if s['name'] == symbol), None)
        if symbol_info:
            sz_decimals = symbol_info['szDecimals']
        else:
            print('Symbol not found')
            return 0, 0
    else:
        print('Error:', response.status_code)
        return 0, 0

    ask = ask_bid(symbol)[0]
    ask_str = str(ask)

    if '.' in ask_str:
        px_decimals = len(ask_str.split('.')[1])
    else:
        px_decimals = 0

    print(f'{symbol} price: {ask} | sz decimals: {sz_decimals} | px decimals: {px_decimals}')
    return sz_decimals, px_decimals

def get_position(symbol, account):
    """Get current position for a symbol"""
    print(f'{colored("Getting position for", "cyan")} {colored(symbol, "yellow")}')

    info = Info(constants.MAINNET_API_URL, skip_ws=True)
    user_state = info.user_state(account.address)

    positions = []
    for position in user_state["assetPositions"]:
        if position["position"]["coin"] == symbol and float(position["position"]["szi"]) != 0:
            positions.append(position["position"])
            coin = position["position"]["coin"]
            pos_size = float(position["position"]["szi"])
            entry_px = float(position["position"]["entryPx"])
            pnl_perc = float(position["position"]["returnOnEquity"]) * 100
            print(f'{colored(f"{coin} position:", "green")} Size: {pos_size} | Entry: ${entry_px} | PnL: {pnl_perc:.2f}%')

    im_in_pos = len(positions) > 0

    if not im_in_pos:
        print(f'{colored("No position in", "yellow")} {symbol}')
        return positions, im_in_pos, 0, symbol, 0, 0, True

    # Return position details
    pos_size = positions[0]["szi"]
    pos_sym = positions[0]["coin"]
    entry_px = float(positions[0]["entryPx"])
    pnl_perc = float(positions[0]["returnOnEquity"]) * 100
    is_long = float(pos_size) > 0

    if is_long:
        print(f'{colored("LONG", "green")} position')
    else:
        print(f'{colored("SHORT", "red")} position')

    return positions, im_in_pos, pos_size, pos_sym, entry_px, pnl_perc, is_long

def set_leverage(symbol, leverage, account):
    """Set leverage for a symbol"""
    print(f'Setting leverage for {symbol} to {leverage}x')
    exchange = Exchange(account, constants.MAINNET_API_URL)

    # Update leverage (is_cross=True for cross margin)
    result = exchange.update_leverage(leverage, symbol, is_cross=True)
    print(f'✅ Leverage set to {leverage}x for {symbol}')
    return result

def adjust_leverage_usd_size(symbol, usd_size, leverage, account):
    """Adjust leverage and calculate position size"""
    print(f'Adjusting leverage for {symbol} to {leverage}x with ${usd_size} size')

    # Set the leverage
    set_leverage(symbol, leverage, account)

    # Get current price
    ask, bid, _ = ask_bid(symbol)
    mid_price = (ask + bid) / 2

    # Calculate position size in coins
    pos_size = usd_size / mid_price

    # Get decimals for rounding
    sz_decimals, _ = get_sz_px_decimals(symbol)
    pos_size = round(pos_size, sz_decimals)

    print(f'Position size: {pos_size} {symbol} (${usd_size} at ${mid_price:.2f})')

    return leverage, pos_size

def cancel_all_orders(account):
    """Cancel all open orders"""
    print(colored('🚫 Cancelling all orders', 'yellow'))
    exchange = Exchange(account, constants.MAINNET_API_URL)
    info = Info(constants.MAINNET_API_URL, skip_ws=True)

    # Get all open orders
    open_orders = info.open_orders(account.address)

    if not open_orders:
        print(colored('   No open orders to cancel', 'yellow'))
        return

    # Cancel each order
    for order in open_orders:
        try:
            exchange.cancel(order['coin'], order['oid'])
            print(colored(f'   ✅ Cancelled {order["coin"]} order', 'green'))
        except Exception as e:
            print(colored(f'   ⚠️ Could not cancel {order["coin"]} order: {str(e)}', 'yellow'))

    print(colored('✅ All orders cancelled', 'green'))
    return

def limit_order(coin, is_buy, sz, limit_px, reduce_only, account):
    """Place a limit order"""
    exchange = Exchange(account, constants.MAINNET_API_URL)

    rounding = get_sz_px_decimals(coin)[0]
    sz = round(sz, rounding)

    print(f"🌙 Moon Dev placing order:")
    print(f"Symbol: {coin}")
    print(f"Side: {'BUY' if is_buy else 'SELL'}")
    print(f"Size: {sz}")
    print(f"Price: ${limit_px}")
    print(f"Reduce Only: {reduce_only}")

    order_result = exchange.order(coin, is_buy, sz, limit_px, {"limit": {"tif": "Gtc"}}, reduce_only=reduce_only)

    if isinstance(order_result, dict) and 'response' in order_result:
        print(f"✅ Order placed with status: {order_result['response']['data']['statuses'][0]}")
    else:
        print(f"✅ Order placed")

    return order_result

def kill_switch(symbol, account):
    """Close position at market price"""
    print(colored(f'🔪 KILL SWITCH ACTIVATED for {symbol}', 'red', attrs=['bold']))

    info = Info(constants.MAINNET_API_URL, skip_ws=True)
    exchange = Exchange(account, constants.MAINNET_API_URL)

    # Get current position
    positions, im_in_pos, pos_size, _, _, _, is_long = get_position(symbol, account)

    if not im_in_pos:
        print(colored('No position to close', 'yellow'))
        return

    # Place market order to close
    side = not is_long  # Opposite side to close
    abs_size = abs(float(pos_size))

    print(f'Closing {"LONG" if is_long else "SHORT"} position: {abs_size} {symbol}')

    # Get current price for market order
    ask, bid, _ = ask_bid(symbol)

    # For closing positions with IOC orders:
    # - Closing long: Sell below bid (undersell)
    # - Closing short: Buy above ask (overbid)
    if is_long:
        close_price = bid * 0.999  # Undersell to close long
    else:
        close_price = ask * 1.001  # Overbid to close short

    # Round to appropriate decimals for BTC
    if symbol == 'BTC':
        close_price = round(close_price)
    else:
        close_price = round(close_price, 1)

    print(f'   Placing IOC at ${close_price} to close position')

    # Place reduce-only order to close
    order_result = exchange.order(symbol, side, abs_size, close_price, {"limit": {"tif": "Ioc"}}, reduce_only=True)

    print(colored('✅ Kill switch executed - position closed', 'green'))
    return order_result

def pnl_close(symbol, target, max_loss, account):
    """Close position if PnL target or stop loss is hit"""
    print(f'{colored("Checking PnL conditions", "cyan")}')
    print(f'Target: {target}% | Stop loss: {max_loss}%')

    # Get current position info
    positions, im_in_pos, pos_size, pos_sym, entry_px, pnl_perc, is_long = get_position(symbol, account)

    if not im_in_pos:
        print(colored('No position to check', 'yellow'))
        return False

    print(f'Current PnL: {colored(f"{pnl_perc:.2f}%", "green" if pnl_perc > 0 else "red")}')

    # Check if we should close
    if pnl_perc >= target:
        print(colored(f'✅ Target reached! Closing position WIN at {pnl_perc:.2f}%', 'green', attrs=['bold']))
        kill_switch(symbol, account)
        return True
    elif pnl_perc <= max_loss:
        print(colored(f'🛑 Stop loss hit! Closing position LOSS at {pnl_perc:.2f}%', 'red', attrs=['bold']))
        kill_switch(symbol, account)
        return True
    else:
        print(f'Position still open. PnL: {pnl_perc:.2f}%')
        return False

def get_current_price(symbol):
    """Get current price for a symbol"""
    ask, bid, _ = ask_bid(symbol)
    mid_price = (ask + bid) / 2
    return mid_price

def get_account_value(account):
    """Get total account value"""
    info = Info(constants.MAINNET_API_URL, skip_ws=True)
    user_state = info.user_state(account.address)
    account_value = float(user_state["marginSummary"]["accountValue"])
    print(f'Account value: ${account_value:,.2f}')
    return account_value

def market_buy(symbol, usd_size, account):
    """Market buy using HyperLiquid"""
    print(colored(f'🛒 Market BUY {symbol} for ${usd_size}', 'green'))

    # Get current ask price
    ask, bid, _ = ask_bid(symbol)

    # Overbid by 0.1% to ensure fill (market buy needs to be above ask)
    buy_price = ask * 1.001

    # Round to appropriate decimals for BTC (whole numbers)
    if symbol == 'BTC':
        buy_price = round(buy_price)
    else:
        buy_price = round(buy_price, 1)

    # Calculate position size
    pos_size = usd_size / buy_price

    # Get decimals and round
    sz_decimals, _ = get_sz_px_decimals(symbol)
    pos_size = round(pos_size, sz_decimals)

    # Ensure minimum order value
    order_value = pos_size * buy_price
    if order_value < 10:
        print(f'   ⚠️ Order value ${order_value:.2f} below $10 minimum, adjusting...')
        pos_size = 11 / buy_price  # $11 to have buffer
        pos_size = round(pos_size, sz_decimals)

    print(f'   Placing IOC buy at ${buy_price} (0.1% above ask ${ask})')
    print(f'   Position size: {pos_size} {symbol} (value: ${pos_size * buy_price:.2f})')

    # Place IOC order above ask to ensure fill
    exchange = Exchange(account, constants.MAINNET_API_URL)
    order_result = exchange.order(symbol, True, pos_size, buy_price, {"limit": {"tif": "Ioc"}}, reduce_only=False)

    print(colored(f'✅ Market buy executed: {pos_size} {symbol} at ${buy_price}', 'green'))
    return order_result

def market_sell(symbol, usd_size, account):
    """Market sell using HyperLiquid"""
    print(colored(f'💸 Market SELL {symbol} for ${usd_size}', 'red'))

    # Get current bid price
    ask, bid, _ = ask_bid(symbol)

    # Undersell by 0.1% to ensure fill (market sell needs to be below bid)
    sell_price = bid * 0.999

    # Round to appropriate decimals for BTC (whole numbers)
    if symbol == 'BTC':
        sell_price = round(sell_price)
    else:
        sell_price = round(sell_price, 1)

    # Calculate position size
    pos_size = usd_size / sell_price

    # Get decimals and round
    sz_decimals, _ = get_sz_px_decimals(symbol)
    pos_size = round(pos_size, sz_decimals)

    # Ensure minimum order value
    order_value = pos_size * sell_price
    if order_value < 10:
        print(f'   ⚠️ Order value ${order_value:.2f} below $10 minimum, adjusting...')
        pos_size = 11 / sell_price  # $11 to have buffer
        pos_size = round(pos_size, sz_decimals)

    print(f'   Placing IOC sell at ${sell_price} (0.1% below bid ${bid})')
    print(f'   Position size: {pos_size} {symbol} (value: ${pos_size * sell_price:.2f})')

    # Place IOC order below bid to ensure fill
    exchange = Exchange(account, constants.MAINNET_API_URL)
    order_result = exchange.order(symbol, False, pos_size, sell_price, {"limit": {"tif": "Ioc"}}, reduce_only=False)

    print(colored(f'✅ Market sell executed: {pos_size} {symbol} at ${sell_price}', 'red'))
    return order_result

def close_position(symbol, account):
    """Close any open position for a symbol"""
    positions, im_in_pos, pos_size, _, _, pnl_perc, is_long = get_position(symbol, account)

    if not im_in_pos:
        print(f'No position to close for {symbol}')
        return None

    print(f'Closing {"LONG" if is_long else "SHORT"} position with PnL: {pnl_perc:.2f}%')
    return kill_switch(symbol, account)

# Additional helper functions for agents
def get_balance(account):
    """Get USDC balance"""
    info = Info(constants.MAINNET_API_URL, skip_ws=True)
    user_state = info.user_state(account.address)

    # Get withdrawable balance (free balance)
    balance = float(user_state["withdrawable"])
    print(f'Available balance: ${balance:,.2f}')
    return balance

def get_all_positions(account):
    """Get all open positions"""
    info = Info(constants.MAINNET_API_URL, skip_ws=True)
    user_state = info.user_state(account.address)

    positions = []
    for position in user_state["assetPositions"]:
        if float(position["position"]["szi"]) != 0:
            positions.append({
                'symbol': position["position"]["coin"],
                'size': float(position["position"]["szi"]),
                'entry_price': float(position["position"]["entryPx"]),
                'pnl_percent': float(position["position"]["returnOnEquity"]) * 100,
                'is_long': float(position["position"]["szi"]) > 0
            })

    return positions

# ============================================================================
# ADDITIONAL HELPER FUNCTIONS (from nice_funcs_hl.py)
# ============================================================================

def _get_exchange():
    """Get exchange instance"""
    private_key = os.getenv('HYPER_LIQUID_ETH_PRIVATE_KEY')
    if not private_key:
        raise ValueError("HYPER_LIQUID_ETH_PRIVATE_KEY not found in .env file")
    account = eth_account.Account.from_key(private_key)
    return Exchange(account, constants.MAINNET_API_URL)

def _get_info():
    """Get info instance"""
    return Info(constants.MAINNET_API_URL, skip_ws=True)

def _get_account_from_env():
    """Initialize and return HyperLiquid account from env"""
    private_key = os.getenv('HYPER_LIQUID_ETH_PRIVATE_KEY')
    if not private_key:
        raise ValueError("HYPER_LIQUID_ETH_PRIVATE_KEY not found in .env file")
    return eth_account.Account.from_key(private_key)

# ============================================================================
# OHLCV DATA FUNCTIONS
# ============================================================================

def _get_ohlcv(symbol, interval, start_time, end_time, batch_size=BATCH_SIZE):
    """Internal function to fetch OHLCV data from Hyperliquid"""
    global timestamp_offset
    print(f'\n🔍 Requesting data for {symbol}:')
    print(f'📊 Batch Size: {batch_size}')
    print(f'⏰ Interval: {interval}')
    print(f'🚀 Start: {start_time.strftime("%Y-%m-%d %H:%M:%S")} UTC')
    print(f'🎯 End: {end_time.strftime("%Y-%m-%d %H:%M:%S")} UTC')

    start_ts = int(start_time.timestamp() * 1000)
    end_ts = int(end_time.timestamp() * 1000)

    # Build request payload
    request_payload = {
        "type": "candleSnapshot",
        "req": {
            "coin": symbol,
            "interval": interval,
            "startTime": start_ts,
            "endTime": end_ts,
            "limit": batch_size
        }
    }

    print(f'\n📤 API Request Payload:')
    print(f'   URL: {BASE_URL}')
    print(f'   Payload: {request_payload}')

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(
                BASE_URL,
                headers={'Content-Type': 'application/json'},
                json=request_payload,
                timeout=10
            )

            print(f'\n📥 API Response:')
            print(f'   Status Code: {response.status_code}')
            print(f'   Response Text: {response.text[:500]}...' if len(response.text) > 500 else f'   Response Text: {response.text}')

            if response.status_code == 200:
                snapshot_data = response.json()
                if snapshot_data:
                    # Handle timestamp offset
                    if timestamp_offset is None:
                        latest_api_timestamp = datetime.datetime.utcfromtimestamp(snapshot_data[-1]['t'] / 1000)
                        system_current_date = datetime.datetime.utcnow()
                        expected_latest_timestamp = system_current_date
                        timestamp_offset = latest_api_timestamp - expected_latest_timestamp
                        print(f"⏱️ Calculated timestamp offset: {timestamp_offset}")

                    # Adjust timestamps
                    for candle in snapshot_data:
                        dt = datetime.datetime.utcfromtimestamp(candle['t'] / 1000)
                        adjusted_dt = adjust_timestamp(dt)
                        candle['t'] = int(adjusted_dt.timestamp() * 1000)

                    first_time = datetime.datetime.utcfromtimestamp(snapshot_data[0]['t'] / 1000)
                    last_time = datetime.datetime.utcfromtimestamp(snapshot_data[-1]['t'] / 1000)
                    print(f'✨ Received {len(snapshot_data)} candles')
                    print(f'📈 First: {first_time}')
                    print(f'📉 Last: {last_time}')
                    return snapshot_data
                print('❌ No data returned by API')
                return None

            print(f'\n⚠️ HTTP Error {response.status_code}')
            print(f'❌ Error details: {response.text}')

            # Try to parse error as JSON for better readability
            try:
                error_json = response.json()
                print(f'📋 Parsed error: {error_json}')
            except:
                pass

        except requests.exceptions.RequestException as e:
            print(f'\n⚠️ Request failed (attempt {attempt + 1}): {e}')
            import traceback
            traceback.print_exc()
            time.sleep(1)
        except Exception as e:
            print(f'\n❌ Unexpected error (attempt {attempt + 1}): {e}')
            import traceback
            traceback.print_exc()
            time.sleep(1)

    print('\n❌ All retry attempts failed')
    return None

def _process_data_to_df(snapshot_data):
    """Convert raw API data to DataFrame"""
    if snapshot_data:
        columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        data = []
        for snapshot in snapshot_data:
            timestamp = datetime.datetime.utcfromtimestamp(snapshot['t'] / 1000)
            # Convert all numeric values to float
            data.append([
                timestamp,
                float(snapshot['o']),
                float(snapshot['h']),
                float(snapshot['l']),
                float(snapshot['c']),
                float(snapshot['v'])
            ])
        df = pd.DataFrame(data, columns=columns)

        # Ensure numeric columns are float64
        numeric_cols = ['open', 'high', 'low', 'close', 'volume']
        df[numeric_cols] = df[numeric_cols].astype('float64')

        print("\n📊 OHLCV Data Types:")
        print(df.dtypes)

        print("\n📈 First 5 rows of data:")
        print(df.head())

        return df
    return pd.DataFrame()

def add_technical_indicators(df):
    """Add technical indicators to the dataframe"""
    if df.empty:
        return df

    try:
        print("\n🔧 Adding technical indicators...")

        # Ensure numeric columns are float64
        numeric_cols = ['open', 'high', 'low', 'close', 'volume']
        df[numeric_cols] = df[numeric_cols].astype('float64')

        # Add basic indicators
        df['sma_20'] = ta.sma(df['close'], length=20)
        df['sma_50'] = ta.sma(df['close'], length=50)
        df['rsi'] = ta.rsi(df['close'], length=14)

        # Add MACD
        macd = ta.macd(df['close'])
        df = pd.concat([df, macd], axis=1)

        # Add Bollinger Bands
        bbands = ta.bbands(df['close'])
        df = pd.concat([df, bbands], axis=1)

        print("✅ Technical indicators added successfully")
        return df

    except Exception as e:
        print(f"❌ Error adding technical indicators: {str(e)}")
        traceback.print_exc()
        return df

def get_data(symbol, timeframe='15m', bars=100, add_indicators=True):
    """
    🌙 Moon Dev's Hyperliquid Data Fetcher

    Args:
        symbol (str): Trading pair symbol (e.g., 'BTC', 'ETH')
        timeframe (str): Candle timeframe (default: '15m')
        bars (int): Number of bars to fetch (default: 100, max: 5000)
        add_indicators (bool): Whether to add technical indicators

    Returns:
        pd.DataFrame: OHLCV data with columns [timestamp, open, high, low, close, volume]
                     and technical indicators if requested
    """
    print("\n🌙 Moon Dev's Hyperliquid Data Fetcher")
    print(f"🎯 Symbol: {symbol}")
    print(f"⏰ Timeframe: {timeframe}")
    print(f"📊 Requested bars: {min(bars, MAX_ROWS)}")

    # Ensure we don't exceed max rows
    bars = min(bars, MAX_ROWS)

    # Calculate time window
    end_time = datetime.datetime.utcnow()
    # Add extra time to ensure we get enough bars
    start_time = end_time - timedelta(days=60)

    data = _get_ohlcv(symbol, timeframe, start_time, end_time, batch_size=bars)

    if not data:
        print("❌ No data available.")
        return pd.DataFrame()

    df = _process_data_to_df(data)

    if not df.empty:
        # Get the most recent bars
        df = df.sort_values('timestamp', ascending=False).head(bars).sort_values('timestamp')
        df = df.reset_index(drop=True)

        # Add technical indicators if requested
        if add_indicators:
            df = add_technical_indicators(df)

        print("\n📊 Data summary:")
        print(f"📈 Total candles: {len(df)}")
        print(f"📅 Range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        print("✨ Thanks for using Moon Dev's Data Fetcher! ✨")

    return df

# ============================================================================
# MARKET INFO FUNCTIONS
# ============================================================================

def get_market_info():
    """Get current market info for all coins on Hyperliquid"""
    try:
        print("\n🔄 Sending request to Hyperliquid API...")
        response = requests.post(
            BASE_URL,
            headers={'Content-Type': 'application/json'},
            json={"type": "allMids"}
        )

        print(f"📡 Response status code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"📦 Raw response data: {data}")
            return data
        print(f"❌ Bad status code: {response.status_code}")
        print(f"📄 Response text: {response.text}")
        return None
    except Exception as e:
        print(f"❌ Error getting market info: {str(e)}")
        traceback.print_exc()
        return None

def test_market_info():
    print("\n💹 Testing Market Info...")
    try:
        print("🎯 Fetching current market prices...")
        info = get_market_info()

        print(f"\n📊 Response type: {type(info)}")
        if info is not None:
            print(f"📝 Response content: {info}")

        if info and isinstance(info, dict):
            print("\n💰 Current Market Prices:")
            print("=" * 50)
            # Target symbols we're interested in
            target_symbols = ["BTC", "ETH", "SOL", "ARB", "OP", "MATIC"]

            for symbol in target_symbols:
                if symbol in info:
                    try:
                        price = float(info[symbol])
                        print(f"Symbol: {symbol:8} | Price: ${price:,.2f}")
                    except (ValueError, TypeError) as e:
                        print(f"⚠️ Error processing price for {symbol}: {str(e)}")
                else:
                    print(f"⚠️ No price data for {symbol}")
        else:
            print("❌ No valid market info received")
            if info is None:
                print("📛 Response was None")
            else:
                print(f"❓ Unexpected response type: {type(info)}")
    except Exception as e:
        print(f"❌ Error in market info test: {str(e)}")
        print(f"🔍 Full error traceback:")
        traceback.print_exc()

# ============================================================================
# FUNDING RATE FUNCTIONS
# ============================================================================

def get_funding_rates(symbol):
    """
    Get current funding rate for a specific coin on Hyperliquid

    Args:
        symbol (str): Trading pair symbol (e.g., 'BTC', 'ETH', 'FARTCOIN')

    Returns:
        dict: Funding data including rate, mark price, and open interest
    """
    try:
        print(f"\n🔄 Fetching funding rate for {symbol}...")
        response = requests.post(
            BASE_URL,
            headers={'Content-Type': 'application/json'},
            json={"type": "metaAndAssetCtxs"}
        )

        if response.status_code == 200:
            data = response.json()
            if len(data) >= 2 and isinstance(data[0], dict) and isinstance(data[1], list):
                # Get universe (symbols) from first element
                universe = {coin['name']: i for i, coin in enumerate(data[0]['universe'])}

                # Check if symbol exists
                if symbol not in universe:
                    print(f"❌ Symbol {symbol} not found in Hyperliquid universe")
                    print(f"📝 Available symbols: {', '.join(universe.keys())}")
                    return None

                # Get funding data from second element
                funding_data = data[1]
                idx = universe[symbol]

                if idx < len(funding_data):
                    asset_data = funding_data[idx]
                    return {
                        'funding_rate': float(asset_data['funding']),
                        'mark_price': float(asset_data['markPx']),
                        'open_interest': float(asset_data['openInterest'])
                    }

            print("❌ Unexpected response format")
            return None
        print(f"❌ Bad status code: {response.status_code}")
        return None
    except Exception as e:
        print(f"❌ Error getting funding rate for {symbol}: {str(e)}")
        traceback.print_exc()
        return None

def test_funding_rates():
    print("\n💸 Testing Funding Rates...")
    try:
        # Test with some interesting symbols
        test_symbols = ["BTC", "ETH", "SOL"]

        for symbol in test_symbols:
            print(f"\n📊 Testing {symbol}:")
            print("=" * 50)
            data = get_funding_rates(symbol)

            if data:
                # The API returns the 8-hour funding rate
                # To get hourly rate: funding_rate
                # To get annual rate: hourly * 24 * 365
                hourly_rate = float(data['funding_rate']) * 100  # Convert to percentage
                annual_rate = hourly_rate * 24 * 365  # Convert hourly to annual

                print(f"Symbol: {symbol:8} | Hourly: {hourly_rate:7.4f}% | Annual: {annual_rate:7.2f}% | OI: {data['open_interest']:10.2f}")
            else:
                print(f"❌ No funding data received for {symbol}")

    except Exception as e:
        print(f"❌ Error in funding rates test: {str(e)}")
        print(f"🔍 Full error traceback:")
        traceback.print_exc()

# ============================================================================
# ADDITIONAL TRADING FUNCTIONS
# ============================================================================

def get_token_balance_usd(token_mint_address, account):
    """Get USD value of current position

    Args:
        token_mint_address: Token symbol (e.g., 'BTC', 'ETH')
        account: HyperLiquid account object

    Returns:
        float: USD value of position (absolute value)
    """
    try:
        positions, im_in_pos, pos_size, _, _, _, _ = get_position(token_mint_address, account)
        if not im_in_pos:
            return 0

        # Get current price
        mid_price = get_current_price(token_mint_address)
        return abs(float(pos_size) * mid_price)
    except Exception as e:
        cprint(f"❌ Error getting balance for {token_mint_address}: {e}", "red")
        return 0

def ai_entry(symbol, amount, max_chunk_size=None, leverage=DEFAULT_LEVERAGE, account=None):
    """Smart entry (HyperLiquid doesn't need chunking)

    Args:
        symbol: Token symbol
        amount: Total USD amount to invest
        max_chunk_size: Ignored (kept for compatibility)
        leverage: Leverage multiplier
        account: HyperLiquid account object (optional, will create from env if not provided)

    Returns:
        bool: True if successful
    """
    if account is None:
        account = _get_account_from_env()

    # Set leverage
    set_leverage(symbol, leverage, account)

    result = market_buy(symbol, amount, account)
    return result is not None

def open_short(token, amount, slippage=None, leverage=DEFAULT_LEVERAGE, account=None):
    """Open SHORT position explicitly

    Args:
        token: Token symbol
        amount: USD NOTIONAL position size
        slippage: Not used (kept for compatibility)
        leverage: Leverage multiplier
        account: HyperLiquid account object (optional, will create from env if not provided)

    Returns:
        dict: Order response
    """
    if account is None:
        account = _get_account_from_env()

    try:
        # Set leverage
        set_leverage(token, leverage, account)

        # Get current ask price
        ask, bid, _ = ask_bid(token)

        # Overbid to ensure fill (market short needs to sell below current price)
        # But we're opening a short, so we sell, which means we want to sell below bid
        sell_price = bid * 0.999

        # Round to appropriate decimals
        if token == 'BTC':
            sell_price = round(sell_price)
        else:
            sell_price = round(sell_price, 1)

        # Calculate quantity
        pos_size = amount / sell_price

        # Get decimals and round
        sz_decimals, _ = get_sz_px_decimals(token)
        pos_size = round(pos_size, sz_decimals)

        # Calculate required margin
        required_margin = amount / leverage

        print(colored(f'📉 Opening SHORT: {pos_size} {token} @ ${sell_price}', 'red'))
        print(colored(f'💰 Notional Position: ${amount:.2f} | Margin Required: ${required_margin:.2f} ({leverage}x)', 'cyan'))

        # Place market sell to open short
        exchange = Exchange(account, constants.MAINNET_API_URL)
        order_result = exchange.order(token, False, pos_size, sell_price, {"limit": {"tif": "Ioc"}}, reduce_only=False)

        print(colored(f'✅ Short position opened!', 'green'))
        return order_result

    except Exception as e:
        print(colored(f'❌ Error opening short: {e}', 'red'))
        traceback.print_exc()
        return None

# Initialize on import
print("✨ HyperLiquid trading functions loaded successfully!")