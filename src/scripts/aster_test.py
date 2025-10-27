"""
🌙 Moon Dev's Aster Test Script
Tests Aster Exchange integration with proof of concept

Workflow:
1. Get and print portfolio balance
2. Get bid/ask for Bitcoin
3. Place limit orders $10 away from midpoint (buy and sell)
4. Cancel those orders
5. Place a market order
6. Close the position
7. Show final balance

Built with love by Moon Dev 🚀
"""

import os
import time
import sys
from termcolor import cprint
from dotenv import load_dotenv

# Add Aster Dex Trading Bots to path
aster_bots_path = '/Users/md/Dropbox/dev/github/Aster-Dex-Trading-Bots'
if aster_bots_path not in sys.path:
    sys.path.insert(0, aster_bots_path)

# Try importing Aster modules
try:
    from aster_api import AsterAPI  # type: ignore
    from aster_funcs import AsterFuncs  # type: ignore
except ImportError as e:
    cprint(f"❌ Failed to import Aster modules: {e}", "red")
    cprint(f"Make sure Aster-Dex-Trading-Bots exists at: {aster_bots_path}", "yellow")
    sys.exit(1)

# Load environment variables
load_dotenv()

# Get API keys
ASTER_API_KEY = os.getenv('ASTER_API_KEY')
ASTER_API_SECRET = os.getenv('ASTER_API_SECRET')

# Verify API keys are loaded
if not ASTER_API_KEY or not ASTER_API_SECRET:
    cprint("❌ ASTER API keys not found in .env file!", "red")
    cprint("Please add ASTER_API_KEY and ASTER_API_SECRET to your .env file", "yellow")
    sys.exit(1)

# Initialize API
api = AsterAPI(ASTER_API_KEY, ASTER_API_SECRET)
funcs = AsterFuncs(api)

# Configuration
SYMBOL = 'BTCUSDT'
ORDER_OFFSET = 10  # $10 away from midpoint
MARKET_ORDER_SIZE = 0.001  # Small size for testing
LEVERAGE = 70

# Precision cache
SYMBOL_PRECISION_CACHE = {}

def get_symbol_precision(symbol):
    """Get price and quantity precision for a symbol

    Returns:
        tuple: (price_precision, quantity_precision) as number of decimal places
    """
    # Check cache first
    if symbol in SYMBOL_PRECISION_CACHE:
        return SYMBOL_PRECISION_CACHE[symbol]

    try:
        # Get exchange info
        exchange_info = api.get_exchange_info()

        for sym_info in exchange_info.get('symbols', []):
            if sym_info['symbol'] == symbol:
                price_precision = 2  # Default
                quantity_precision = 3  # Default

                # Parse filters for precision
                for filter_info in sym_info.get('filters', []):
                    if filter_info['filterType'] == 'PRICE_FILTER':
                        tick_size = filter_info.get('tickSize', '0.01')
                        # Count decimal places
                        price_precision = len(tick_size.rstrip('0').split('.')[-1]) if '.' in tick_size else 0

                    if filter_info['filterType'] == 'LOT_SIZE':
                        step_size = filter_info.get('stepSize', '0.001')
                        # Count decimal places
                        quantity_precision = len(step_size.rstrip('0').split('.')[-1]) if '.' in step_size else 0

                # Cache the result
                SYMBOL_PRECISION_CACHE[symbol] = (price_precision, quantity_precision)
                cprint(f"📏 Precision for {symbol}: Price={price_precision} decimals, Qty={quantity_precision} decimals", "cyan")
                return price_precision, quantity_precision

        # If symbol not found, use defaults
        cprint(f"⚠️  Symbol {symbol} not found in exchange info, using defaults", "yellow")
        SYMBOL_PRECISION_CACHE[symbol] = (2, 3)
        return 2, 3

    except Exception as e:
        cprint(f"❌ Error getting precision: {e}", "red")
        # Use safe defaults
        return 2, 3

def print_separator():
    """Print a fancy separator"""
    cprint("\n" + "="*60, "cyan")

def get_portfolio_balance():
    """Get and display portfolio balance"""
    cprint("\n🏦 STEP 1: Getting Portfolio Balance...", "cyan", attrs=['bold'])

    try:
        account_info = api.get_account_info()

        available = float(account_info.get('availableBalance', 0))
        position_margin = float(account_info.get('totalPositionInitialMargin', 0))
        unrealized_profit = float(account_info.get('totalUnrealizedProfit', 0))
        total_equity = available + position_margin + unrealized_profit

        cprint(f"💰 Available Balance: ${available:.2f}", "green")
        cprint(f"📊 Position Margin: ${position_margin:.2f}", "yellow")
        cprint(f"📈 Unrealized P&L: ${unrealized_profit:.2f}", "yellow")
        cprint(f"🎯 Total Equity: ${total_equity:.2f}", "green", attrs=['bold'])

        return total_equity

    except Exception as e:
        cprint(f"❌ Error getting balance: {e}", "red")
        raise

def get_bid_ask(symbol):
    """Get and display bid/ask for symbol"""
    cprint(f"\n📊 STEP 2: Getting Bid/Ask for {symbol}...", "cyan", attrs=['bold'])

    try:
        ask, bid, _ = api.get_ask_bid(symbol)
        midpoint = (ask + bid) / 2
        spread = ask - bid
        spread_pct = (spread / midpoint) * 100

        cprint(f"📉 Bid: ${bid:.2f}", "red")
        cprint(f"📈 Ask: ${ask:.2f}", "green")
        cprint(f"🎯 Midpoint: ${midpoint:.2f}", "yellow")
        cprint(f"📏 Spread: ${spread:.2f} ({spread_pct:.4f}%)", "white")

        return ask, bid, midpoint

    except Exception as e:
        cprint(f"❌ Error getting bid/ask: {e}", "red")
        raise

def place_limit_orders(symbol, midpoint):
    """Place limit buy and sell orders $10 away from midpoint"""
    cprint(f"\n📝 STEP 3: Placing Limit Orders ${ORDER_OFFSET} from Midpoint...", "cyan", attrs=['bold'])

    try:
        # Get precision for this symbol
        price_precision, quantity_precision = get_symbol_precision(symbol)

        # Calculate prices with proper rounding
        buy_price = round(midpoint - ORDER_OFFSET, price_precision)
        sell_price = round(midpoint + ORDER_OFFSET, price_precision)

        # Round quantity to proper precision
        quantity = round(MARKET_ORDER_SIZE, quantity_precision)

        cprint(f"💰 Buy Order: {quantity} @ ${buy_price:.2f}", "green")
        cprint(f"💰 Sell Order: {quantity} @ ${sell_price:.2f}", "red")

        # Place buy order
        buy_order = api.place_order(
            symbol=symbol,
            side='BUY',
            order_type='LIMIT',
            quantity=quantity,
            price=buy_price,
            time_in_force='GTC'
        )
        cprint(f"✅ Buy order placed! Order ID: {buy_order.get('orderId')}", "green")

        time.sleep(1)  # Small delay

        # Place sell order
        sell_order = api.place_order(
            symbol=symbol,
            side='SELL',
            order_type='LIMIT',
            quantity=quantity,
            price=sell_price,
            time_in_force='GTC'
        )
        cprint(f"✅ Sell order placed! Order ID: {sell_order.get('orderId')}", "green")

        return buy_order, sell_order

    except Exception as e:
        cprint(f"❌ Error placing limit orders: {e}", "red")
        raise

def check_open_orders(symbol):
    """Check and display open orders"""
    try:
        open_orders = api.get_open_orders(symbol)

        if open_orders:
            cprint(f"\n📋 Open Orders ({len(open_orders)}):", "yellow")
            for order in open_orders:
                order_id = order.get('orderId')
                side = order.get('side')
                price = float(order.get('price', 0))
                qty = float(order.get('origQty', 0))
                cprint(f"  • Order #{order_id}: {side} {qty} @ ${price:.2f}", "white")
        else:
            cprint("\n📋 No open orders", "yellow")

        return open_orders

    except Exception as e:
        cprint(f"❌ Error checking orders: {e}", "red")
        return []

def cancel_all_orders(symbol):
    """Cancel all open orders"""
    cprint(f"\n🗑️  STEP 4: Canceling All Orders...", "cyan", attrs=['bold'])

    try:
        result = api.cancel_all_orders(symbol)
        cprint(f"✅ All orders canceled for {symbol}", "green")

        # Verify no orders remain
        time.sleep(1)
        remaining_orders = check_open_orders(symbol)
        if not remaining_orders:
            cprint("✅ Confirmed: No orders remaining", "green")

        return result

    except Exception as e:
        cprint(f"❌ Error canceling orders: {e}", "red")
        raise

def place_market_order(symbol):
    """Place a small market order"""
    cprint(f"\n🚀 STEP 5: Placing Market Order...", "cyan", attrs=['bold'])

    try:
        # Set leverage first
        cprint(f"⚙️  Setting leverage to {LEVERAGE}x...", "yellow")
        api.change_leverage(symbol, LEVERAGE)

        # Get precision and round quantity
        _, quantity_precision = get_symbol_precision(symbol)
        quantity = round(MARKET_ORDER_SIZE, quantity_precision)

        cprint(f"💰 Placing MARKET BUY for {quantity} {symbol}", "green")

        order = api.place_order(
            symbol=symbol,
            side='BUY',
            order_type='MARKET',
            quantity=quantity
        )

        cprint(f"✅ Market order placed! Order ID: {order.get('orderId')}", "green")

        # Wait for fill
        time.sleep(2)

        # Check position
        position = api.get_position(symbol)
        if position:
            cprint(f"📊 Position opened:", "yellow")
            cprint(f"  • Amount: {position['position_amount']}", "white")
            cprint(f"  • Entry Price: ${position['entry_price']:.2f}", "white")
            cprint(f"  • Mark Price: ${position['mark_price']:.2f}", "white")
            cprint(f"  • PnL: ${position['pnl']:.2f} ({position['pnl_percentage']:.2f}%)", "white")

        return order, position

    except Exception as e:
        cprint(f"❌ Error placing market order: {e}", "red")
        raise

def close_position(symbol):
    """Close the open position"""
    cprint(f"\n🔄 STEP 6: Closing Position...", "cyan", attrs=['bold'])

    try:
        # Get current position
        position = api.get_position(symbol)

        if not position:
            cprint("⚠️  No position to close", "yellow")
            return

        position_amt = position['position_amount']
        is_long = position['is_long']

        cprint(f"📊 Current position: {position_amt} ({'LONG' if is_long else 'SHORT'})", "yellow")
        cprint(f"💰 Closing with MARKET order...", "green")

        # Determine close side and get precision
        close_side = 'SELL' if is_long else 'BUY'
        _, quantity_precision = get_symbol_precision(symbol)
        close_qty = round(abs(position_amt), quantity_precision)

        # Place market order to close
        close_order = api.place_order(
            symbol=symbol,
            side=close_side,
            order_type='MARKET',
            quantity=close_qty,
            reduce_only=True
        )

        cprint(f"✅ Close order placed! Order ID: {close_order.get('orderId')}", "green")

        # Wait for close
        time.sleep(2)

        # Verify position closed
        new_position = api.get_position(symbol)
        if not new_position:
            cprint("✅ Position closed successfully!", "green", attrs=['bold'])
        else:
            cprint(f"⚠️  Position still exists: {new_position['position_amount']}", "yellow")

        return close_order

    except Exception as e:
        cprint(f"❌ Error closing position: {e}", "red")
        raise

def main():
    """Main test flow"""
    cprint("\n" + "="*60, "cyan", attrs=['bold'])
    cprint("🌙 Moon Dev's Aster Exchange Test Script 🚀", "cyan", attrs=['bold'])
    cprint("="*60 + "\n", "cyan", attrs=['bold'])

    try:
        # Step 1: Get initial balance
        print_separator()
        initial_balance = get_portfolio_balance()

        # Step 2: Get bid/ask
        print_separator()
        _, _, midpoint = get_bid_ask(SYMBOL)

        # Step 3: Place limit orders
        print_separator()
        place_limit_orders(SYMBOL, midpoint)

        # Check orders were placed
        time.sleep(1)
        check_open_orders(SYMBOL)

        # Step 4: Cancel all orders
        print_separator()
        cancel_all_orders(SYMBOL)

        # Step 5: Place market order
        print_separator()
        place_market_order(SYMBOL)

        # Step 6: Close position
        print_separator()
        close_position(SYMBOL)

        # Step 7: Get final balance
        print_separator()
        cprint("\n💰 STEP 7: Final Balance Check...", "cyan", attrs=['bold'])
        final_balance = get_portfolio_balance()

        # Summary
        print_separator()
        cprint("\n✨ TEST SUMMARY ✨", "green", attrs=['bold'])
        print_separator()

        balance_change = final_balance - initial_balance
        cprint(f"💰 Initial Balance: ${initial_balance:.2f}", "white")
        cprint(f"💰 Final Balance: ${final_balance:.2f}", "white")
        cprint(f"📊 Change: ${balance_change:+.2f}", "green" if balance_change >= 0 else "red", attrs=['bold'])

        cprint("\n✅ All tests completed successfully!", "green", attrs=['bold'])
        cprint("🚀 Aster Exchange integration is working! 🌙\n", "cyan", attrs=['bold'])

        print_separator()

    except Exception as e:
        cprint(f"\n❌ Test failed: {e}", "red", attrs=['bold'])
        import traceback
        cprint(traceback.format_exc(), "red")

        # Try to clean up
        try:
            cprint("\n🧹 Attempting cleanup...", "yellow")
            cancel_all_orders(SYMBOL)
            position = api.get_position(SYMBOL)
            if position:
                close_position(SYMBOL)
        except:
            pass

if __name__ == "__main__":
    main()
