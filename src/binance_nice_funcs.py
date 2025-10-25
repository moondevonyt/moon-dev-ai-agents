"""
🌙 Moon Dev's Binance Functions - Binance trading integration
Built with love by Moon Dev 🚀
"""

import os
import sys
import time
import json
from datetime import datetime, timedelta
from termcolor import colored, cprint
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Binance imports
try:
    from binance.client import Client
    from binance.exceptions import BinanceAPIException, BinanceOrderException
except ImportError:
    print("❌ python-binance not installed. Run: pip install python-binance")
    sys.exit(1)

# Get Binance API keys from environment
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_SECRET_KEY = os.getenv("BINANCE_SECRET_KEY")

if not BINANCE_API_KEY or not BINANCE_SECRET_KEY:
    raise ValueError("🚨 BINANCE_API_KEY and BINANCE_SECRET_KEY not found in environment variables!")

# Initialize Binance client with timeout (prevents API hangs)
client = Client(BINANCE_API_KEY, BINANCE_SECRET_KEY)
# Set request timeout to 10 seconds to prevent hanging
client.REQUEST_TIMEOUT = 10

# Configuration from existing config
from src.config import usd_size, max_usd_order_size, slippage

# Binance precision requirements (stepSize from LOT_SIZE filter)
BINANCE_PRECISION = {
    'BTCUSDT': 0.00001,
    'ETHUSDT': 0.0001,
    'BNBUSDT': 0.001,
    'SOLUSDT': 0.001,
    'ADAUSDT': 0.1,
    'XRPUSDT': 0.1,
    'DOGEUSDT': 1.0,
    'DOTUSDT': 0.01,
}

def round_quantity_to_precision(symbol, quantity):
    """Round quantity to Binance's precision requirements"""
    if symbol not in BINANCE_PRECISION:
        # Default: round to 6 decimals if symbol not in our list
        return float(f"{quantity:.6f}")

    step_size = BINANCE_PRECISION[symbol]

    # Calculate number of decimal places from step size
    if step_size >= 1:
        decimals = 0
    else:
        decimals = len(str(step_size).split('.')[-1].rstrip('0'))

    # Round to the appropriate precision
    rounded = round(quantity / step_size) * step_size
    rounded = round(rounded, decimals)

    # Format to avoid scientific notation (force decimal format)
    return float(f"{rounded:.{decimals}f}")

def binance_market_buy(symbol, quantity, slippage_pct=0.02):
    """Execute market buy order on Binance"""
    try:
        # Round quantity to Binance's precision requirements
        quantity = round_quantity_to_precision(symbol, quantity)

        cprint(f"🟢 Placing MARKET BUY: {quantity} {symbol} with {slippage_pct*100}% slippage tolerance", "green")

        # Create market buy order
        order = client.order_market_buy(
            symbol=symbol,
            quantity=quantity
        )

        cprint(f"✅ BUY ORDER FILLED: {order['executedQty']} @ avg ${order['cummulativeQuoteQty']}", "green")
        return order

    except BinanceAPIException as e:
        cprint(f"❌ Binance API Error: {e}", "red")
        return None
    except BinanceOrderException as e:
        cprint(f"❌ Order Error: {e}", "red")
        return None
    except Exception as e:
        cprint(f"❌ Unexpected error in market buy: {str(e)}", "red")
        return None

def binance_market_sell(symbol, quantity, slippage_pct=0.02):
    """Execute market sell order on Binance"""
    try:
        # Round quantity to Binance's precision requirements
        quantity = round_quantity_to_precision(symbol, quantity)

        cprint(f"🔴 Placing MARKET SELL: {quantity} {symbol} with {slippage_pct*100}% slippage tolerance", "red")

        # Create market sell order
        order = client.order_market_sell(
            symbol=symbol,
            quantity=quantity
        )

        cprint(f"✅ SELL ORDER FILLED: {order['executedQty']} @ avg ${order['cummulativeQuoteQty']}", "red")
        return order

    except BinanceAPIException as e:
        cprint(f"❌ Binance API Error: {e}", "red")
        return None
    except BinanceOrderException as e:
        cprint(f"❌ Order Error: {e}", "red")
        return None
    except Exception as e:
        cprint(f"❌ Unexpected error in market sell: {str(e)}", "red")
        return None

def binance_get_position(symbol):
    """Get current position size for a symbol on Binance"""
    try:
        # Get account information
        account = client.get_account()

        # Find the asset in balances
        asset = symbol.replace('USDT', '').replace('BUSD', '').replace('USDC', '')  # Extract base asset

        for balance in account['balances']:
            if balance['asset'] == asset:
                free_balance = float(balance['free'])
                locked_balance = float(balance['locked'])
                total_balance = free_balance + locked_balance
                return total_balance

        return 0.0  # No position found

    except Exception as e:
        cprint(f"❌ Error getting position for {symbol}: {str(e)}", "red")
        return 0.0

def binance_token_price(symbol):
    """Get current price for a symbol on Binance"""
    try:
        ticker = client.get_symbol_ticker(symbol=symbol)
        return float(ticker['price'])
    except Exception as e:
        cprint(f"❌ Error getting price for {symbol}: {str(e)}", "red")
        return 0.0

def binance_get_token_balance_usd(symbol):
    """Get USD value of position for a symbol on Binance"""
    try:
        position_size = binance_get_position(symbol)
        price = binance_token_price(symbol)
        usd_value = position_size * price
        return usd_value

    except Exception as e:
        cprint(f"❌ Error getting balance for {symbol}: {str(e)}", "red")
        return 0.0

def binance_ai_entry(symbol, amount):
    """AI agent entry function for Binance trading 🤖"""
    cprint("🤖 Moon Dev's AI Trading Agent initiating Binance position entry...", "white", "on_blue")

    # amount passed in is the target allocation (up to 30% of usd_size)
    target_size = amount

    pos = binance_get_position(symbol)
    price = binance_token_price(symbol)
    pos_usd = pos * price

    cprint(f"🎯 Target allocation: ${target_size:.2f} USD", "white", "on_blue")
    cprint(f"📊 Current position: ${pos_usd:.2f} USD", "white", "on_blue")

    # Check if we're already at or above target
    if pos_usd >= (target_size * 0.97):
        cprint("✋ Position already at or above target size!", "white", "on_blue")
        return

    # Calculate how much more we need to buy
    size_needed = target_size - pos_usd
    if size_needed <= 0:
        cprint("🛑 No additional size needed", "white", "on_blue")
        return

    # For order execution, we'll chunk into max_usd_order_size pieces
    if size_needed > max_usd_order_size:
        chunk_size = max_usd_order_size
    else:
        chunk_size = size_needed

    # Convert USD amount to token quantity
    chunk_quantity = chunk_size / price

    cprint(f"💫 Entry chunk size: {chunk_quantity:.6f} {symbol} (${chunk_size:.2f})", "white", "on_blue")

    # Add retry limit to prevent infinite loops
    max_retries = 5
    retry_count = 0

    while pos_usd < (target_size * 0.97):
        cprint(f"🤖 AI Agent executing Binance entry for {symbol}...", "white", "on_blue")
        print(f"Position: {round(pos,6)} | Price: {round(price,4)} | USD Value: ${round(pos_usd,2)}")

        try:
            # Place market buy order
            order = binance_market_buy(symbol, chunk_quantity, slippage)
            if not order:
                retry_count += 1
                if retry_count >= max_retries:
                    cprint(f"❌ Max retries ({max_retries}) reached. Aborting entry for {symbol}.", "red")
                    break
                cprint(f"❌ Order failed, retrying in 30 seconds... (attempt {retry_count}/{max_retries})", "white", "on_blue")
                time.sleep(30)
                continue

            # Reset retry count on successful order
            retry_count = 0

            time.sleep(2)  # Brief pause after order

            # Update position info
            pos = binance_get_position(symbol)
            price = binance_token_price(symbol)
            pos_usd = pos * price

            # Break if we're at or above target
            if pos_usd >= (target_size * 0.97):
                break

            # Recalculate needed size
            size_needed = target_size - pos_usd
            if size_needed <= 0:
                break

            # Determine next chunk size
            if size_needed > max_usd_order_size:
                chunk_size = max_usd_order_size
            else:
                chunk_size = size_needed

            chunk_quantity = chunk_size / price

        except Exception as e:
            try:
                cprint("🔄 AI Agent retrying Binance order in 30 seconds...", "white", "on_blue")
                time.sleep(30)

                order = binance_market_buy(symbol, chunk_quantity, slippage)
                if order:
                    time.sleep(2)
                    pos = binance_get_position(symbol)
                    price = binance_token_price(symbol)
                    pos_usd = pos * price

                    if pos_usd >= (target_size * 0.97):
                        break

                    size_needed = target_size - pos_usd
                    if size_needed <= 0:
                        break

                    if size_needed > max_usd_order_size:
                        chunk_size = max_usd_order_size
                    else:
                        chunk_size = size_needed

                    chunk_quantity = chunk_size / price

            except:
                cprint("❌ AI Agent encountered critical error, manual intervention needed", "white", "on_red")
                return

    cprint("✨ AI Agent completed Binance position entry", "white", "on_blue")

def binance_chunk_kill(symbol, max_usd_order_size, slippage_pct=0.02):
    """Kill a position in chunks on Binance"""
    cprint(f"\n🔪 Moon Dev's AI Agent initiating Binance position exit...", "white", "on_cyan")

    # Binance minimum order size (NOTIONAL filter)
    MIN_ORDER_SIZE_USD = 5.0  # Most tokens require $5 minimum

    try:
        # Get current position
        pos = binance_get_position(symbol)
        price = binance_token_price(symbol)
        current_usd_value = pos * price

        cprint(f"📊 Initial position: {pos:.6f} {symbol} (${current_usd_value:.2f})", "white", "on_cyan")

        # If position is very small (under $15), sell all at once
        if current_usd_value < 15.0:
            cprint(f"💡 Small position (${current_usd_value:.2f}) - selling all at once to avoid NOTIONAL error", "yellow")
            try:
                order = binance_market_sell(symbol, pos, slippage_pct)
                if order:
                    cprint("\n✨ Position successfully closed!", "white", "on_green")
                    return
                else:
                    cprint("❌ Failed to close small position", "white", "on_red")
                    return
            except Exception as e:
                cprint(f"❌ Error closing small position: {str(e)}", "white", "on_red")
                return

        # Keep going until position is essentially zero
        while current_usd_value > 1.0:  # Keep going until less than $1
            # Calculate chunk size - ensure it's above minimum
            chunk_usd_value = max(MIN_ORDER_SIZE_USD, min(max_usd_order_size, current_usd_value / 3))
            chunk_quantity = chunk_usd_value / price

            cprint(f"\n🔄 Selling chunk of ${chunk_usd_value:.2f} (min ${MIN_ORDER_SIZE_USD:.2f} required)", "white", "on_cyan")

            # Execute sell orders in chunks
            for i in range(3):
                try:
                    cprint(f"\n💫 Executing sell chunk {i+1}/3...", "white", "on_cyan")
                    order = binance_market_sell(symbol, chunk_quantity, slippage_pct)
                    if not order:
                        cprint(f"❌ Sell chunk {i+1}/3 failed", "white", "on_red")
                    else:
                        cprint(f"✅ Sell chunk {i+1}/3 complete", "white", "on_green")
                    time.sleep(2)  # Small delay between chunks
                except Exception as e:
                    cprint(f"❌ Error in sell chunk: {str(e)}", "white", "on_red")

            # Check remaining position
            time.sleep(5)  # Wait for order to settle
            pos = binance_get_position(symbol)
            price = binance_token_price(symbol)
            current_usd_value = pos * price
            cprint(f"\n📊 Remaining position: {pos:.6f} {symbol} (${current_usd_value:.2f})", "white", "on_cyan")

            if current_usd_value > 1.0:
                cprint("🔄 Position still open - continuing to close...", "white", "on_cyan")
                time.sleep(2)

        cprint("\n✨ Position successfully closed!", "white", "on_green")

    except Exception as e:
        cprint(f"❌ Error during Binance position exit: {str(e)}", "white", "on_red")