"""
🌙 Moon Dev's Aster DEX Functions
Built with love by Moon Dev 🚀

Aster-specific trading functions for futures trading.
Supports both LONG and SHORT positions.

LEVERAGE & POSITION SIZING:
- All 'amount' parameters represent NOTIONAL position size (total exposure)
- Leverage is applied by the exchange, reducing required margin
- Example: $25 position at 5x leverage = $25 notional, $5 margin required
- Formula: Required Margin = Notional Position / Leverage
- Default leverage: 5x (configurable below)

QUANTITY CALCULATION:
- quantity = notional_position_size / current_price
- This gives the amount of tokens for the desired exposure
- The exchange handles margin requirements automatically
"""

import os
import sys
import time
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

# Verify API keys
if not ASTER_API_KEY or not ASTER_API_SECRET:
    cprint("❌ ASTER API keys not found in .env file!", "red")
    cprint("Please add ASTER_API_KEY and ASTER_API_SECRET to your .env file", "yellow")
    sys.exit(1)

# Initialize API (global instance)
api = AsterAPI(ASTER_API_KEY, ASTER_API_SECRET)
funcs = AsterFuncs(api)

# ============================================================================
# CONFIGURATION
# ============================================================================
DEFAULT_LEVERAGE = 5  # Change this to adjust leverage globally (1-125x)
                      # Higher leverage = less margin required, but higher liquidation risk
                      # Examples:
                      # - 5x: $25 position needs $5 margin
                      # - 10x: $25 position needs $2.50 margin
                      # - 20x: $25 position needs $1.25 margin

DEFAULT_SYMBOL_SUFFIX = 'USDT'  # Aster uses BTCUSDT, ETHUSDT, etc.

# Precision cache
SYMBOL_PRECISION_CACHE = {}


def get_symbol_precision(symbol):
    """Get price and quantity precision for a symbol

    Returns:
        tuple: (price_precision, quantity_precision) as number of decimal places
    """
    if symbol in SYMBOL_PRECISION_CACHE:
        return SYMBOL_PRECISION_CACHE[symbol]

    try:
        exchange_info = api.get_exchange_info()

        for sym_info in exchange_info.get('symbols', []):
            if sym_info['symbol'] == symbol:
                price_precision = 2
                quantity_precision = 3

                for filter_info in sym_info.get('filters', []):
                    if filter_info['filterType'] == 'PRICE_FILTER':
                        tick_size = filter_info.get('tickSize', '0.01')
                        price_precision = len(tick_size.rstrip('0').split('.')[-1]) if '.' in tick_size else 0

                    if filter_info['filterType'] == 'LOT_SIZE':
                        step_size = filter_info.get('stepSize', '0.001')
                        quantity_precision = len(step_size.rstrip('0').split('.')[-1]) if '.' in step_size else 0

                SYMBOL_PRECISION_CACHE[symbol] = (price_precision, quantity_precision)
                return price_precision, quantity_precision

        # Default if not found
        SYMBOL_PRECISION_CACHE[symbol] = (2, 3)
        return 2, 3

    except Exception as e:
        cprint(f"❌ Error getting precision: {e}", "red")
        return 2, 3


def format_symbol(token):
    """Convert token address/symbol to Aster format

    For now, assumes token is already in correct format (BTCUSDT, ETHUSDT, etc.)
    Future: Could map token addresses to symbols
    """
    if not token.endswith(DEFAULT_SYMBOL_SUFFIX):
        return f"{token}{DEFAULT_SYMBOL_SUFFIX}"
    return token


def token_price(address):
    """Get current token price from bid/ask midpoint

    Args:
        address: Token symbol (e.g., 'BTCUSDT')

    Returns:
        float: Current price
    """
    try:
        symbol = format_symbol(address)
        ask, bid, _ = api.get_ask_bid(symbol)
        midpoint = (ask + bid) / 2
        return midpoint
    except Exception as e:
        cprint(f"❌ Error getting price for {address}: {e}", "red")
        return 0


def get_best_bid_ask(symbol):
    """Get best bid and ask prices from order book

    Returns:
        tuple: (best_bid, best_ask) or (None, None) if error
    """
    try:
        orderbook = api.get_orderbook(symbol, limit=5)

        if not orderbook:
            return None, None

        bids = orderbook.get('bids', [])
        asks = orderbook.get('asks', [])

        if not bids or not asks:
            return None, None

        best_bid = float(bids[0][0])  # First bid price
        best_ask = float(asks[0][0])  # First ask price

        return best_bid, best_ask

    except Exception as e:
        cprint(f"❌ Error getting order book for {symbol}: {e}", "red")
        return None, None


def place_limit_order_with_chase(symbol, side, quantity, leverage, max_attempts=20, check_interval=0.5):
    """Place limit order at best bid/ask and chase until filled

    Args:
        symbol: Token symbol (e.g., 'BTCUSDT')
        side: 'BUY' or 'SELL'
        quantity: Order quantity
        leverage: Leverage to use
        max_attempts: Maximum number of attempts to chase the order (default: 20)
        check_interval: Seconds to wait between checks (default: 0.5)

    Returns:
        dict: Final filled order info or None if failed
    """
    try:
        # Set leverage first
        api.change_leverage(symbol, leverage)

        current_order_id = None
        last_price = None
        attempts = 0

        while attempts < max_attempts:
            attempts += 1

            # Get best bid/ask
            best_bid, best_ask = get_best_bid_ask(symbol)
            if not best_bid or not best_ask:
                cprint(f"❌ Could not get order book", "red")
                time.sleep(check_interval)
                continue

            # Determine target price (bid for buy, ask for sell)
            target_price = best_bid if side == 'BUY' else best_ask

            # Round price to proper precision
            price_precision, _ = get_symbol_precision(symbol)
            target_price = round(target_price, price_precision)

            # If we have an existing order and price hasn't changed, check status
            if current_order_id and target_price == last_price:
                # Check if order is filled
                order_status = api.get_order(symbol, order_id=current_order_id)
                status = order_status.get('status', '')

                if status == 'FILLED':
                    cprint(f"✅ Order FILLED! Order ID: {current_order_id}", "green", attrs=['bold'])
                    return order_status

                # Order still open, wait and continue
                time.sleep(check_interval)
                continue

            # Price changed or first order - cancel old order if exists
            if current_order_id:
                try:
                    cprint(f"🔄 Best {side} price changed: ${last_price:.2f} → ${target_price:.2f}", "yellow")
                    api.cancel_order(symbol, order_id=current_order_id)
                    cprint(f"❌ Cancelled order {current_order_id}", "yellow")
                    time.sleep(0.2)  # Brief delay after cancel
                except Exception as e:
                    # Order might have filled during cancel
                    cprint(f"   Could not cancel order {current_order_id}: {e}", "yellow")

            # Place new limit order at best bid/ask
            cprint(f"📝 Placing LIMIT {side}: {quantity} {symbol} @ ${target_price:.2f}", "cyan")
            order = api.place_order(
                symbol=symbol,
                side=side,
                order_type='LIMIT',
                quantity=quantity,
                price=target_price,
                time_in_force='GTC'
            )

            current_order_id = order.get('orderId')
            last_price = target_price
            cprint(f"   Order placed: ID {current_order_id}", "cyan")

            time.sleep(check_interval)

        # Max attempts reached
        if current_order_id:
            cprint(f"⚠️  Max attempts reached, cancelling order {current_order_id}", "yellow")
            try:
                api.cancel_order(symbol, order_id=current_order_id)
            except:
                pass

        return None

    except Exception as e:
        cprint(f"❌ Error in limit order chase: {e}", "red")
        return None


def get_position(token_mint_address):
    """Get current position for a token

    Args:
        token_mint_address: Token symbol (e.g., 'BTCUSDT')

    Returns:
        dict: Position info or None if no position
            {
                'position_amount': float,  # Positive for long, negative for short
                'entry_price': float,
                'mark_price': float,
                'pnl': float,
                'pnl_percentage': float,
                'is_long': bool
            }
    """
    try:
        symbol = format_symbol(token_mint_address)
        position = api.get_position(symbol)
        return position
    except Exception as e:
        cprint(f"❌ Error getting position for {token_mint_address}: {e}", "red")
        return None


def get_token_balance_usd(token_mint_address):
    """Get USD value of current position

    Args:
        token_mint_address: Token symbol (e.g., 'BTCUSDT')

    Returns:
        float: USD value of position (absolute value)
    """
    try:
        position = get_position(token_mint_address)
        if not position:
            return 0

        position_amt = position.get('position_amount', 0)
        mark_price = position.get('mark_price', 0)

        # Return absolute USD value
        return abs(position_amt * mark_price)

    except Exception as e:
        cprint(f"❌ Error getting balance for {token_mint_address}: {e}", "red")
        return 0


def market_buy(token, amount, slippage, leverage=DEFAULT_LEVERAGE):
    """Open or add to LONG position with MARKET order (immediate fill)

    Args:
        token: Token symbol (e.g., 'BTCUSDT')
        amount: USD NOTIONAL position size (total exposure, not margin)
                Example: $25 at 5x leverage = $25 position, $5 margin required
        slippage: Slippage tolerance (not used for market orders on Aster)
        leverage: Leverage multiplier (default: 5)

    Returns:
        dict: Order response or None if failed
    """
    try:
        symbol = format_symbol(token)

        # Set leverage
        cprint(f"⚙️  Setting leverage to {leverage}x for {symbol}", "yellow")
        api.change_leverage(symbol, leverage)

        # Get current price and calculate quantity
        current_price = token_price(token)
        if current_price == 0:
            cprint(f"❌ Could not get price for {symbol}", "red")
            return None

        # Calculate quantity based on NOTIONAL value
        quantity = amount / current_price

        # Round to proper precision
        _, quantity_precision = get_symbol_precision(symbol)
        quantity = round(quantity, quantity_precision)

        # Check if quantity is too small
        min_notional = 5.0
        actual_notional = quantity * current_price

        if quantity <= 0 or actual_notional < min_notional:
            cprint(f"❌ Position size too small for {symbol}!", "red")
            cprint(f"   Calculated Quantity: {quantity} {symbol}", "red")
            cprint(f"   Actual Notional: ${actual_notional:.2f} (minimum: ${min_notional:.2f})", "red")
            cprint(f"   💡 Need at least ${min_notional:.2f} position size", "yellow")
            return None

        # Calculate required margin for logging
        required_margin = amount / leverage

        cprint(f"🚀 MARKET BUY: {quantity} {symbol} @ ~${current_price:.2f}", "green")
        cprint(f"💰 Notional Position: ${amount:.2f} | Margin Required: ${required_margin:.2f} ({leverage}x)", "cyan")

        # Place market buy order
        order = api.place_order(
            symbol=symbol,
            side='BUY',
            order_type='MARKET',
            quantity=quantity
        )

        cprint(f"✅ Market buy order placed! Order ID: {order.get('orderId')}", "green")
        return order

    except Exception as e:
        cprint(f"❌ Error placing market buy: {e}", "red")
        return None


def limit_buy(token, amount, slippage, leverage=DEFAULT_LEVERAGE):
    """Open or add to LONG position with LIMIT order at best bid (chase until filled)

    Args:
        token: Token symbol (e.g., 'BTCUSDT')
        amount: USD NOTIONAL position size (total exposure, not margin)
                Example: $25 at 5x leverage = $25 position, $5 margin required
        slippage: Slippage tolerance (not used - we chase the bid)
        leverage: Leverage multiplier (default: 5)

    Returns:
        dict: Order response or None if failed
    """
    try:
        symbol = format_symbol(token)

        # Get current price and calculate quantity
        current_price = token_price(token)
        if current_price == 0:
            cprint(f"❌ Could not get price for {symbol}", "red")
            return None

        # Calculate quantity based on NOTIONAL value
        quantity = amount / current_price

        # Round to proper precision
        _, quantity_precision = get_symbol_precision(symbol)
        quantity = round(quantity, quantity_precision)

        # Check if quantity is too small
        min_notional = 5.0
        actual_notional = quantity * current_price

        if quantity <= 0 or actual_notional < min_notional:
            cprint(f"❌ Position size too small for {symbol}!", "red")
            cprint(f"   Calculated Quantity: {quantity} {symbol}", "red")
            cprint(f"   Actual Notional: ${actual_notional:.2f} (minimum: ${min_notional:.2f})", "red")
            cprint(f"   💡 Need at least ${min_notional:.2f} position size", "yellow")
            return None

        # Calculate required margin for logging
        required_margin = amount / leverage

        cprint(f"🚀 LIMIT BUY: {quantity} {symbol} (chasing best bid)", "green")
        cprint(f"💰 Notional Position: ${amount:.2f} | Margin Required: ${required_margin:.2f} ({leverage}x)", "cyan")

        # Place limit order at best bid and chase until filled
        order = place_limit_order_with_chase(
            symbol=symbol,
            side='BUY',
            quantity=quantity,
            leverage=leverage,
            max_attempts=20,
            check_interval=0.5
        )

        if order:
            return order
        else:
            cprint(f"❌ Failed to fill buy order after chasing", "red")
            return None

    except Exception as e:
        cprint(f"❌ Error placing limit buy: {e}", "red")
        return None


def market_sell(token, amount, slippage, leverage=DEFAULT_LEVERAGE):
    """Close LONG or open SHORT position with MARKET order (immediate fill)

    Args:
        token: Token symbol (e.g., 'BTCUSDT')
        amount: USD NOTIONAL amount (total exposure, not margin)
        slippage: Slippage tolerance (not used for market orders on Aster)
        leverage: Leverage multiplier (default: 5)

    Returns:
        dict: Order response or None if failed
    """
    try:
        symbol = format_symbol(token)

        # Check current position
        position = get_position(token)

        # Get current price and calculate quantity
        current_price = token_price(token)
        if current_price == 0:
            cprint(f"❌ Could not get price for {symbol}", "red")
            return None

        # Calculate quantity based on NOTIONAL value
        quantity = amount / current_price

        # Round to proper precision
        _, quantity_precision = get_symbol_precision(symbol)
        quantity = round(quantity, quantity_precision)

        if position and position['position_amount'] > 0:
            # We have a long position - close it (reduce_only)
            cprint(f"📉 Closing LONG: {quantity} {symbol} @ MARKET", "red")
            cprint(f"💰 Closing ${amount:.2f} notional position", "cyan")

            order = api.place_order(
                symbol=symbol,
                side='SELL',
                order_type='MARKET',
                quantity=quantity,
                reduce_only=True
            )

            cprint(f"✅ Market sell order placed! Order ID: {order.get('orderId')}", "green")
            return order
        else:
            # No long position - open short
            # Check if quantity is too small
            min_notional = 5.0
            actual_notional = quantity * current_price

            if quantity <= 0 or actual_notional < min_notional:
                cprint(f"❌ Position size too small for {symbol}!", "red")
                cprint(f"   Calculated Quantity: {quantity} {symbol}", "red")
                cprint(f"   Actual Notional: ${actual_notional:.2f} (minimum: ${min_notional:.2f})", "red")
                cprint(f"   💡 Need at least ${min_notional:.2f} position size", "yellow")
                return None

            cprint(f"⚙️  Setting leverage to {leverage}x for {symbol}", "yellow")
            api.change_leverage(symbol, leverage)

            required_margin = amount / leverage
            cprint(f"📉 MARKET SELL (SHORT): {quantity} {symbol} @ ~${current_price:.2f}", "red")
            cprint(f"💰 Notional Position: ${amount:.2f} | Margin Required: ${required_margin:.2f} ({leverage}x)", "cyan")

            order = api.place_order(
                symbol=symbol,
                side='SELL',
                order_type='MARKET',
                quantity=quantity
            )

            cprint(f"✅ Market sell order placed! Order ID: {order.get('orderId')}", "green")
            return order

    except Exception as e:
        cprint(f"❌ Error placing market sell: {e}", "red")
        return None


def limit_sell(token, amount, slippage, leverage=DEFAULT_LEVERAGE):
    """Close LONG or open SHORT position with LIMIT order at best ask (chase until filled)

    Args:
        token: Token symbol (e.g., 'BTCUSDT')
        amount: USD NOTIONAL amount (total exposure, not margin)
        slippage: Slippage tolerance (not used - we chase the ask)
        leverage: Leverage multiplier (default: 5)

    Returns:
        dict: Order response or None if failed
    """
    try:
        symbol = format_symbol(token)

        # Check current position
        position = get_position(token)

        # Get current price and calculate quantity
        current_price = token_price(token)
        if current_price == 0:
            cprint(f"❌ Could not get price for {symbol}", "red")
            return None

        # Calculate quantity based on NOTIONAL value
        quantity = amount / current_price

        # Round to proper precision
        _, quantity_precision = get_symbol_precision(symbol)
        quantity = round(quantity, quantity_precision)

        if position and position['position_amount'] > 0:
            # We have a long position - close it (reduce_only)
            # Use market order for immediate exit when closing
            cprint(f"📉 Closing LONG: {quantity} {symbol} @ MARKET (immediate exit)", "red")
            cprint(f"💰 Closing ${amount:.2f} notional position", "cyan")

            order = api.place_order(
                symbol=symbol,
                side='SELL',
                order_type='MARKET',
                quantity=quantity,
                reduce_only=True
            )

            cprint(f"✅ Market sell order placed! Order ID: {order.get('orderId')}", "green")
            return order
        else:
            # No long position - open short using limit order chase
            # Check if quantity is too small
            min_notional = 5.0
            actual_notional = quantity * current_price

            if quantity <= 0 or actual_notional < min_notional:
                cprint(f"❌ Position size too small for {symbol}!", "red")
                cprint(f"   Calculated Quantity: {quantity} {symbol}", "red")
                cprint(f"   Actual Notional: ${actual_notional:.2f} (minimum: ${min_notional:.2f})", "red")
                cprint(f"   💡 Need at least ${min_notional:.2f} position size", "yellow")
                return None

            required_margin = amount / leverage
            cprint(f"🚀 LIMIT SELL (SHORT): {quantity} {symbol} (chasing best ask)", "red")
            cprint(f"💰 Notional Position: ${amount:.2f} | Margin Required: ${required_margin:.2f} ({leverage}x)", "cyan")

            # Place limit order at best ask and chase until filled
            order = place_limit_order_with_chase(
                symbol=symbol,
                side='SELL',
                quantity=quantity,
                leverage=leverage,
                max_attempts=20,
                check_interval=0.5
            )

            if order:
                return order
            else:
                cprint(f"❌ Failed to fill sell order after chasing", "red")
                return None

    except Exception as e:
        cprint(f"❌ Error placing limit sell: {e}", "red")
        return None


def chunk_kill(token_mint_address, max_usd_order_size, slippage):
    """Close entire position in chunks

    Args:
        token_mint_address: Token symbol (e.g., 'BTCUSDT')
        max_usd_order_size: Maximum USD per chunk
        slippage: Slippage tolerance

    Returns:
        bool: True if successful
    """
    try:
        symbol = format_symbol(token_mint_address)
        position = get_position(token_mint_address)

        if not position:
            cprint(f"⚠️  No position to close for {symbol}", "yellow")
            return True

        position_amt = position['position_amount']
        is_long = position['is_long']

        cprint(f"🔄 Closing position: {position_amt} {symbol} ({'LONG' if is_long else 'SHORT'})", "cyan")

        # Determine close side (opposite of position)
        close_side = 'SELL' if is_long else 'BUY'

        # Get total position value
        total_value = abs(position_amt * position['mark_price'])

        # Calculate number of chunks needed
        num_chunks = int(total_value / max_usd_order_size) + 1
        chunk_size_tokens = abs(position_amt) / num_chunks

        # Round to proper precision
        _, quantity_precision = get_symbol_precision(symbol)
        chunk_size_tokens = round(chunk_size_tokens, quantity_precision)

        cprint(f"📊 Closing in {num_chunks} chunks of ~{chunk_size_tokens} tokens", "yellow")

        for i in range(num_chunks):
            # Check remaining position
            current_position = get_position(token_mint_address)
            if not current_position or abs(current_position['position_amount']) < 0.0001:
                cprint(f"✅ Position fully closed after {i} chunks!", "green")
                break

            # Calculate chunk size (use remaining position for last chunk)
            remaining = abs(current_position['position_amount'])
            chunk = min(chunk_size_tokens, remaining)
            chunk = round(chunk, quantity_precision)

            cprint(f"🔄 Chunk {i+1}/{num_chunks}: Closing {chunk} {symbol}", "cyan")

            # Place market order to close chunk
            order = api.place_order(
                symbol=symbol,
                side=close_side,
                order_type='MARKET',
                quantity=chunk,
                reduce_only=True
            )

            cprint(f"✅ Chunk order placed! Order ID: {order.get('orderId')}", "green")
            time.sleep(1)  # Small delay between chunks

        # Verify position closed
        final_position = get_position(token_mint_address)
        if not final_position or abs(final_position['position_amount']) < 0.0001:
            cprint(f"✅ Position closed successfully!", "green", attrs=['bold'])
            return True
        else:
            cprint(f"⚠️  Position still has {final_position['position_amount']} remaining", "yellow")
            return False

    except Exception as e:
        cprint(f"❌ Error in chunk_kill: {e}", "red")
        return False


def ai_entry(symbol, amount, max_chunk_size=None, leverage=DEFAULT_LEVERAGE, use_limit=True):
    """Smart entry with automatic chunking

    Args:
        symbol: Token symbol (e.g., 'BTCUSDT')
        amount: Total USD amount to invest
        max_chunk_size: Maximum USD per order (default: use full amount)
        leverage: Leverage multiplier (default: 5)
        use_limit: If True, use limit orders with chase (default: True)
                   If False, use market orders for immediate fill

    Returns:
        bool: True if successful
    """
    try:
        symbol = format_symbol(symbol)

        if max_chunk_size is None or amount <= max_chunk_size:
            # Single order
            if use_limit:
                result = limit_buy(symbol, amount, slippage=0, leverage=leverage)
            else:
                result = market_buy(symbol, amount, slippage=0, leverage=leverage)
            return result is not None

        # Multiple chunks
        num_chunks = int(amount / max_chunk_size) + 1
        chunk_size = amount / num_chunks

        order_type_str = "LIMIT" if use_limit else "MARKET"
        cprint(f"🎯 AI Entry: ${amount} in {num_chunks} {order_type_str} chunks of ${chunk_size:.2f}", "cyan")

        for i in range(num_chunks):
            cprint(f"🔄 Chunk {i+1}/{num_chunks}: ${chunk_size:.2f}", "cyan")

            if use_limit:
                result = limit_buy(symbol, chunk_size, slippage=0, leverage=leverage)
            else:
                result = market_buy(symbol, chunk_size, slippage=0, leverage=leverage)

            if not result:
                cprint(f"❌ Chunk {i+1} failed!", "red")
                return False

            time.sleep(1)  # Delay between chunks

        cprint(f"✅ AI Entry complete! ${amount} deployed across {num_chunks} {order_type_str} orders", "green")
        return True

    except Exception as e:
        cprint(f"❌ Error in ai_entry: {e}", "red")
        return False


def open_short(token, amount, slippage, leverage=DEFAULT_LEVERAGE):
    """Open SHORT position explicitly

    Args:
        token: Token symbol (e.g., 'BTCUSDT')
        amount: USD NOTIONAL position size (total exposure, not margin)
                Example: $25 short at 5x leverage = $25 position, $5 margin required
        slippage: Slippage tolerance
        leverage: Leverage multiplier

    Returns:
        dict: Order response
    """
    try:
        symbol = format_symbol(token)

        # Set leverage
        cprint(f"⚙️  Setting leverage to {leverage}x for {symbol}", "yellow")
        api.change_leverage(symbol, leverage)

        # Get current price and calculate quantity
        current_price = token_price(token)
        if current_price == 0:
            cprint(f"❌ Could not get price for {symbol}", "red")
            return None

        # Calculate quantity based on NOTIONAL value
        quantity = amount / current_price

        # Round to proper precision
        _, quantity_precision = get_symbol_precision(symbol)
        quantity = round(quantity, quantity_precision)

        # Calculate required margin
        required_margin = amount / leverage

        cprint(f"📉 Opening SHORT: {quantity} {symbol} @ ~${current_price:.2f}", "red")
        cprint(f"💰 Notional Position: ${amount:.2f} | Margin Required: ${required_margin:.2f} ({leverage}x)", "cyan")

        # Place market sell order to open short
        order = api.place_order(
            symbol=symbol,
            side='SELL',
            order_type='MARKET',
            quantity=quantity
        )

        cprint(f"✅ Short position opened! Order ID: {order.get('orderId')}", "green")
        return order

    except Exception as e:
        cprint(f"❌ Error opening short: {e}", "red")
        return None


def get_account_balance():
    """Get account balance information

    Returns:
        dict: Account balance info
            {
                'available': float,
                'total_equity': float,
                'position_margin': float,
                'unrealized_pnl': float
            }
    """
    try:
        account_info = api.get_account_info()

        available = float(account_info.get('availableBalance', 0))
        position_margin = float(account_info.get('totalPositionInitialMargin', 0))
        unrealized_profit = float(account_info.get('totalUnrealizedProfit', 0))
        total_equity = available + position_margin + unrealized_profit

        return {
            'available': available,
            'total_equity': total_equity,
            'position_margin': position_margin,
            'unrealized_pnl': unrealized_profit
        }
    except Exception as e:
        cprint(f"❌ Error getting account balance: {e}", "red")
        return None


# Initialize on import
cprint("✨ Aster DEX functions loaded successfully!", "green")
