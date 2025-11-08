"""
🌙 Moon Dev's Extended Exchange Trading Functions

This module provides trading functions for Extended Exchange (X10).
Compatible with the trading_agent.py exchange selector.

API Documentation: https://api.starknet.extended.exchange
"""

import os
import asyncio
import time
import requests
from typing import Dict, Optional, List
from decimal import Decimal
from termcolor import cprint
from dotenv import load_dotenv

# Extended Exchange SDK imports
try:
    from x10.perpetual.trading_client import PerpetualTradingClient
    from x10.perpetual.configuration import TESTNET_CONFIG, MAINNET_CONFIG
    from x10.perpetual.orders import OrderSide
    from x10.perpetual.accounts import StarkPerpetualAccount
except ImportError:
    cprint("⚠️  Extended Exchange SDK not installed. Install with: pip install x10-perpetual-sdk", "yellow")
    raise

load_dotenv()

# =============================================================================
# 🌙 Moon Dev's Symbol Format Conversion
# =============================================================================

def format_symbol_for_extended(symbol: str) -> str:
    """
    Convert simple symbol format to Extended format

    Moon Dev says: Keep using 'BTC', 'ETH', 'SOL' everywhere!
    This function automatically converts to Extended's format internally.

    Args:
        symbol: 'BTC', 'ETH', 'SOL', etc.

    Returns:
        Extended format: 'BTC-USD', 'ETH-USD', 'SOL-USD'
    """
    # If already has -USD suffix, return as is
    if '-USD' in symbol.upper():
        return symbol

    # Otherwise, append -USD
    return f"{symbol}-USD"

# =============================================================================
# 🔧 CONFIGURATION
# =============================================================================

# Extended Exchange API Configuration
X10_API_KEY = os.getenv("X10_API_KEY")
X10_PRIVATE_KEY = os.getenv("X10_PRIVATE_KEY")
X10_PUBLIC_KEY = os.getenv("X10_PUBLIC_KEY")
X10_VAULT_ID = int(os.getenv("X10_VAULT_ID", "110198"))

# Trading Configuration
DEFAULT_LEVERAGE = 20  # Default leverage for Extended Exchange (matches trading_agent.py)
USE_TESTNET = False    # Set to True for testnet

# =============================================================================
# 🏦 EXTENDED EXCHANGE API CLASS
# =============================================================================

class ExtendedExchangeAPI:
    """Extended Exchange API wrapper for trading operations"""

    def __init__(self, api_key: str = None, private_key: str = None, public_key: str = None, vault_id: int = None):
        """Initialize Extended Exchange API client"""
        self.api_key = api_key or X10_API_KEY
        self.private_key = private_key or X10_PRIVATE_KEY
        self.public_key = public_key or X10_PUBLIC_KEY
        self.vault_id = vault_id or X10_VAULT_ID

        if not all([self.api_key, self.private_key, self.public_key]):
            raise ValueError("Extended Exchange credentials not found in environment!")

        # Initialize configuration
        self.config = TESTNET_CONFIG if USE_TESTNET else MAINNET_CONFIG

        # Create StarkPerpetualAccount
        self.stark_account = StarkPerpetualAccount(
            vault=self.vault_id,
            private_key=self.private_key,
            public_key=self.public_key,
            api_key=self.api_key
        )

        # Create trading client
        self.trading_client = PerpetualTradingClient(self.config, self.stark_account)

        # REST API session for operations not supported by SDK
        self.base_url = "https://api.starknet.extended.exchange" if not USE_TESTNET else "https://api-testnet.extended.exchange"
        self.session = requests.Session()
        self.session.headers.update({
            "X-Api-Key": self.api_key,
            "User-Agent": "moon-dev-extended-bot/1.0",
            "Content-Type": "application/json"
        })

        # Event loop for async operations
        self._event_loop = None

    def _get_event_loop(self):
        """Get or create event loop for async operations"""
        if self._event_loop is None or self._event_loop.is_closed():
            try:
                self._event_loop = asyncio.get_event_loop()
            except RuntimeError:
                self._event_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._event_loop)
        return self._event_loop

    def _request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """🌙 Moon Dev's REST API request handler"""
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.request(method, url, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            cprint(f"REST API Error: {e}", "red")
            cprint(f"Endpoint: {endpoint}", "yellow")
            raise

    def get_account_info(self) -> Dict:
        """Get account information including balance and positions"""
        loop = self._get_event_loop()

        async def get_info():
            balance = await self.trading_client.account.get_balance()
            positions = await self.trading_client.account.get_positions()
            return {
                "balance": balance,
                "positions": positions,
                "stark_key": self.stark_account.public_key,
                "vault": self.stark_account.vault
            }

        return loop.run_until_complete(get_info())

    def get_position(self, symbol: str) -> Dict:
        """
        Get position information for a symbol
        Returns dict matching Aster/HyperLiquid format:
            {
                'position_amount': float,  # Positive for long, negative for short
                'entry_price': float,
                'mark_price': float,
                'pnl': float,
                'pnl_percentage': float,
                'is_long': bool
            }
        """
        # 🌙 Moon Dev: Auto-convert symbol format
        symbol = format_symbol_for_extended(symbol)

        try:
            account_info = self.get_account_info()
            positions = account_info['positions'].data

            for pos in positions:
                # Get market name
                market_attr = getattr(pos, 'market_name', None) or getattr(pos, 'market', None) or getattr(pos, 'symbol', None)

                if market_attr == symbol:
                    mypos_size = float(pos.size)
                    entry_px = float(getattr(pos, 'entry_price', 0) or getattr(pos, 'open_price', 0))
                    mark_px = float(getattr(pos, 'mark_price', 0) or entry_px)

                    # Get PnL from Extended API
                    unrealized_pnl = float(getattr(pos, 'unrealised_pnl', 0) or getattr(pos, 'unrealized_pnl', 0))

                    # 🌙 Moon Dev: Calculate P&L % using actual position leverage
                    # Matches reference: actual_margin = (position_size * entry_price) / LEVERAGE
                    position_value = mypos_size * entry_px
                    position_leverage = float(getattr(pos, 'leverage', DEFAULT_LEVERAGE))
                    actual_margin = position_value / position_leverage if position_leverage > 0 else position_value
                    pnl_perc = (unrealized_pnl / actual_margin) * 100 if actual_margin > 0 else 0

                    # 🌙 Moon Dev: Determine position direction from 'side' field (not size!)
                    # Extended uses 'side' field: 'LONG' or 'SHORT'
                    side = str(getattr(pos, 'side', 'LONG')).upper()
                    is_long = side != 'SHORT'

                    # For position_amount, make it negative for shorts (matches Aster/HyperLiquid format)
                    signed_size = -mypos_size if side == 'SHORT' else mypos_size

                    # Return dict format matching Aster/HyperLiquid
                    return {
                        'position_amount': signed_size,  # Negative for shorts, positive for longs
                        'entry_price': entry_px,
                        'mark_price': mark_px,
                        'pnl': unrealized_pnl,
                        'pnl_percentage': pnl_perc,
                        'is_long': is_long
                    }

            # No position found - return None (matching Aster behavior)
            return None

        except Exception as e:
            cprint(f"Error getting position: {e}", "red")
            return None

    def set_leverage(self, symbol: str, leverage: int):
        """Set leverage for a symbol"""
        loop = self._get_event_loop()

        async def set_lev():
            try:
                return await self.trading_client.account.update_leverage(
                    market_name=symbol,
                    leverage=leverage
                )
            except Exception as e:
                cprint(f"Leverage update note: {e}", "yellow")
                return None

        return loop.run_until_complete(set_lev())

    def buy_limit(self, symbol: str, quantity: float, price: float, leverage: int = None) -> Dict:
        """Place a buy limit order"""
        if leverage:
            self.set_leverage(symbol, leverage)
            time.sleep(0.3)

        loop = self._get_event_loop()

        async def place_order():
            rounded_price = int(round(price))  # Extended requires integer prices for BTC-USD
            response = await self.trading_client.place_order(
                market_name=symbol,
                amount_of_synthetic=Decimal(str(quantity)),
                price=Decimal(str(rounded_price)),
                side=OrderSide.BUY,
                post_only=True
            )
            return response

        return loop.run_until_complete(place_order())

    def sell_limit(self, symbol: str, quantity: float, price: float, leverage: int = None) -> Dict:
        """Place a sell limit order"""
        if leverage:
            self.set_leverage(symbol, leverage)
            time.sleep(0.3)

        loop = self._get_event_loop()

        async def place_order():
            rounded_price = int(round(price))  # Extended requires integer prices for BTC-USD
            response = await self.trading_client.place_order(
                market_name=symbol,
                amount_of_synthetic=Decimal(str(quantity)),
                price=Decimal(str(rounded_price)),
                side=OrderSide.SELL,
                post_only=True
            )
            return response

        return loop.run_until_complete(place_order())

    def buy_market(self, symbol: str, quantity: float, leverage: int = None) -> Dict:
        """Place a buy market order (aggressive limit order)"""
        if leverage:
            self.set_leverage(symbol, leverage)
            time.sleep(0.3)

        loop = self._get_event_loop()

        async def place_order():
            # Get current ask price for aggressive execution
            orderbook = await self.trading_client.markets_info.get_orderbook_snapshot(market_name=symbol)
            ask_price = float(orderbook.data.ask[0].price) if orderbook.data.ask else 0
            aggressive_price = round(ask_price * 1.01)  # 1% above ask, rounded to integer

            response = await self.trading_client.place_order(
                market_name=symbol,
                amount_of_synthetic=Decimal(str(quantity)),
                price=Decimal(str(int(aggressive_price))),  # Integer price for BTC-USD
                side=OrderSide.BUY,
                post_only=False
            )
            return response

        return loop.run_until_complete(place_order())

    def sell_market(self, symbol: str, quantity: float, leverage: int = None) -> Dict:
        """Place a sell market order (aggressive limit order)"""
        if leverage:
            self.set_leverage(symbol, leverage)
            time.sleep(0.3)

        loop = self._get_event_loop()

        async def place_order():
            # Get current bid price for aggressive execution
            orderbook = await self.trading_client.markets_info.get_orderbook_snapshot(market_name=symbol)
            bid_price = float(orderbook.data.bid[0].price) if orderbook.data.bid else 0
            aggressive_price = round(bid_price * 0.99)  # 1% below bid, rounded to integer

            response = await self.trading_client.place_order(
                market_name=symbol,
                amount_of_synthetic=Decimal(str(quantity)),
                price=Decimal(str(int(aggressive_price))),  # Integer price for BTC-USD
                side=OrderSide.SELL,
                post_only=False
            )
            return response

        return loop.run_until_complete(place_order())

    def cancel_all_orders(self, symbol: Optional[str] = None):
        """Cancel all open orders using REST API"""
        try:
            data = {}
            if symbol:
                data["market"] = symbol

            response = self._request("POST", "/api/v1/user/order/massCancel", data)
            return response.get('success', False) or response.get('status') == 'OK'
        except Exception as e:
            cprint(f"Error canceling orders: {e}", "yellow")
            return False

    def get_open_orders(self, symbol: str) -> List[Dict]:
        """Get all open orders for a symbol using REST API"""
        try:
            # Use REST API to get orders
            response = self._request("GET", f"/api/v1/user/orders?market={symbol}&status=OPEN")

            if not response or 'data' not in response:
                return []

            orders_data = response['data']
            if not isinstance(orders_data, list):
                return []

            # Format orders
            symbol_orders = []
            for order in orders_data:
                symbol_orders.append({
                    'id': order.get('id', ''),
                    'price': float(order.get('price', 0)),
                    'side': order.get('side', 'UNKNOWN'),
                    'quantity': float(order.get('quantity', 0) or order.get('amount', 0)),
                    'status': order.get('status', 'UNKNOWN')
                })

            return symbol_orders
        except Exception as e:
            cprint(f"Error getting open orders: {e}", "yellow")
            return []

    def close_position(self, symbol: str) -> bool:
        """Close an open position"""
        try:
            position = self.get_position(symbol)

            if not position or position['position_amount'] == 0:
                return False

            # Cancel all orders first
            self.cancel_all_orders(symbol)
            time.sleep(0.5)

            # Close position with market order
            mypos_size = position['position_amount']
            is_long = position['is_long']
            close_size = abs(mypos_size)

            if is_long:
                self.sell_market(symbol, close_size)
            else:
                self.buy_market(symbol, close_size)

            time.sleep(2)

            # Verify closure
            new_position = self.get_position(symbol)
            return not new_position or new_position['position_amount'] == 0

        except Exception as e:
            cprint(f"Error closing position: {e}", "red")
            return False

    def get_account_balance(self) -> Dict:
        """Get account balance in format expected by trading_agent"""
        try:
            account_info = self.get_account_info()

            # Extract equity from balance
            equity = 0
            if hasattr(account_info['balance'], 'data'):
                if hasattr(account_info['balance'].data, 'equity'):
                    equity = float(account_info['balance'].data.equity)
                elif hasattr(account_info['balance'].data, 'total_balance'):
                    equity = float(account_info['balance'].data.total_balance)

            return {"equity": equity}
        except Exception as e:
            cprint(f"Error getting account balance: {e}", "red")
            return {"equity": 0}

    def usd_to_asset_size(self, symbol: str, usd_amount: float) -> float:
        """
        Convert USD amount to asset size for trading
        🌙 Moon Dev's asset converter for Extended Exchange
        """
        try:
            loop = self._get_event_loop()

            async def get_prices():
                orderbook = await self.trading_client.markets_info.get_orderbook_snapshot(market_name=symbol)
                return {
                    "bid": float(orderbook.data.bid[0].price) if orderbook.data.bid else 0.0,
                    "ask": float(orderbook.data.ask[0].price) if orderbook.data.ask else 0.0
                }

            bid_ask = loop.run_until_complete(get_prices())
            mid_price = (bid_ask['bid'] + bid_ask['ask']) / 2

            if mid_price <= 0:
                cprint(f"❌ Invalid price for {symbol}: {mid_price}", "red")
                return 0

            # Calculate asset size
            asset_size = usd_amount / mid_price

            # Round to appropriate precision for different assets
            if 'BTC' in symbol:
                asset_size = round(asset_size, 3)
                if asset_size == 0.0 and usd_amount > 0:
                    asset_size = 0.001  # Minimum BTC size
            elif 'ETH' in symbol:
                asset_size = round(asset_size, 4)
                if asset_size == 0 and usd_amount > 0:
                    asset_size = max(0.0001, asset_size)
            elif 'SOL' in symbol:
                asset_size = round(asset_size, 2)
                if asset_size == 0 and usd_amount > 0:
                    asset_size = max(0.01, asset_size)
            else:
                asset_size = round(asset_size, 4)
                if asset_size == 0 and usd_amount > 0:
                    asset_size = max(0.0001, asset_size)

            cprint(f"💱 USD to Asset: ${usd_amount} → {asset_size} {symbol} @ ${mid_price:,.2f}", "cyan")
            return asset_size

        except Exception as e:
            cprint(f"❌ Error converting USD to asset size: {e}", "red")
            return 0

# =============================================================================
# 🎯 GLOBAL API INSTANCE
# =============================================================================

# Create global API instance for easy imports
try:
    api = ExtendedExchangeAPI()
    cprint("✅ Extended Exchange API initialized", "green")
except Exception as e:
    cprint(f"⚠️  Failed to initialize Extended Exchange API: {e}", "yellow")
    api = None

# =============================================================================
# 🔄 TRADING FUNCTIONS FOR TRADING_AGENT COMPATIBILITY
# =============================================================================

def get_account_balance() -> Dict:
    """Get account balance - trading_agent compatible"""
    if api is None:
        return {"equity": 0}
    return api.get_account_balance()

def get_position(symbol: str) -> Dict:
    """Get position - trading_agent compatible

    Returns dict:
        {
            'position_amount': float,  # Positive for long, negative for short
            'entry_price': float,
            'mark_price': float,
            'pnl': float,
            'pnl_percentage': float,
            'is_long': bool
        }
    Or None if no position
    """
    if api is None:
        return None
    return api.get_position(symbol)

def market_buy(symbol: str, usd_amount: float, slippage=None, leverage: int = DEFAULT_LEVERAGE):
    """Buy market order - trading_agent compatible

    Args:
        symbol: Trading symbol (BTC, ETH, etc.)
        usd_amount: USD amount to buy
        slippage: Not used by Extended (kept for compatibility)
        leverage: Leverage multiplier
    """
    # 🌙 Moon Dev: Auto-convert symbol format
    symbol = format_symbol_for_extended(symbol)

    if api is None:
        raise Exception("Extended API not initialized")

    # Convert USD to properly rounded asset size
    quantity = api.usd_to_asset_size(symbol, usd_amount)

    if quantity <= 0:
        raise Exception(f"Invalid quantity calculated: {quantity}")

    return api.buy_market(symbol, quantity, leverage)

def market_sell(symbol: str, usd_amount: float, slippage=None, leverage: int = DEFAULT_LEVERAGE):
    """Sell market order - trading_agent compatible

    Args:
        symbol: Trading symbol (BTC, ETH, etc.)
        usd_amount: USD amount to sell
        slippage: Not used by Extended (kept for compatibility)
        leverage: Leverage multiplier
    """
    # 🌙 Moon Dev: Auto-convert symbol format
    symbol = format_symbol_for_extended(symbol)

    if api is None:
        raise Exception("Extended API not initialized")

    # Convert USD to properly rounded asset size
    quantity = api.usd_to_asset_size(symbol, usd_amount)

    if quantity <= 0:
        raise Exception(f"Invalid quantity calculated: {quantity}")

    return api.sell_market(symbol, quantity, leverage)

def open_long(symbol: str, usd_amount: float, slippage=None, leverage: int = DEFAULT_LEVERAGE):
    """Open long position - trading_agent compatible

    Args:
        symbol: Trading symbol (BTC, ETH, etc.)
        usd_amount: USD amount for position
        slippage: Not used by Extended (kept for compatibility)
        leverage: Leverage multiplier
    """
    return market_buy(symbol, usd_amount, slippage, leverage)

def open_short(symbol: str, usd_amount: float, slippage=None, leverage: int = DEFAULT_LEVERAGE):
    """Open short position - trading_agent compatible

    Args:
        symbol: Trading symbol (BTC, ETH, etc.)
        usd_amount: USD amount for position
        slippage: Not used by Extended (kept for compatibility)
        leverage: Leverage multiplier
    """
    return market_sell(symbol, usd_amount, slippage, leverage)

def close_position(symbol: str) -> bool:
    """Close position - trading_agent compatible"""
    # 🌙 Moon Dev: Auto-convert symbol format
    symbol = format_symbol_for_extended(symbol)

    if api is None:
        return False
    return api.close_position(symbol)

def chunk_kill(symbol: str, max_chunk_size: float = 999999, slippage: int = None) -> bool:
    """
    🌙 Moon Dev's Extended Exchange Chunk Kill Function

    Close position with maker orders - loops until FULLY closed
    Adjusts order size if partially filled
    NO MAX ATTEMPTS - will continue until position is fully closed

    Args:
        symbol: Trading symbol (BTC, ETH, etc.)
        max_chunk_size: Not used (kept for compatibility with other exchanges)
        slippage: Not used (kept for compatibility with other exchanges)

    Returns:
        True if position closed successfully
    """
    # 🌙 Moon Dev: Auto-convert symbol format
    symbol = format_symbol_for_extended(symbol)

    if api is None:
        cprint("❌ Extended API not initialized", "red")
        return False

    cprint(f"\n🔄 Moon Dev's Chunk Kill: Closing {symbol} position (MAKER orders)...", "yellow")

    last_price = None
    last_size = None
    attempt = 0
    ORDER_REPLACE_DELAY = 0.5  # 500ms between order replacements

    while True:  # No max attempts - MUST close position
        attempt += 1

        # Get current position
        position = get_position(symbol)

        # Check if position is closed
        if not position or position['position_amount'] == 0:
            cprint(f"✅ Position FULLY closed (verified)", "green")
            time.sleep(0.3)

            # Double-check closure
            double_check = get_position(symbol)
            if not double_check or double_check['position_amount'] == 0:
                return True
            else:
                cprint(f"⚠️  Position reappeared: {abs(double_check['position_amount'])} - continuing close", "yellow")
                position = double_check

        # Get remaining size and direction
        remaining_size = abs(position['position_amount'])
        is_long = position['is_long']

        # Detect partial fills
        if last_size is not None and remaining_size < last_size:
            cprint(f"📉 Partial fill detected: {last_size} → {remaining_size}", "yellow")

        # Get current best bid/ask
        ticker = get_ticker(symbol)
        if not ticker or 'bid' not in ticker or 'ask' not in ticker:
            cprint("⚠️  Could not get ticker data, retrying...", "yellow")
            time.sleep(0.1)
            continue

        bid = ticker['bid']
        ask = ticker['ask']

        # Choose close price (use ask for long, bid for short)
        close_price = ask if is_long else bid

        # If price changed OR size changed, cancel and replace
        if close_price != last_price or remaining_size != last_size:
            # Cancel all existing orders
            cancel_all_orders(symbol)
            time.sleep(0.1)

            close_side = 'SELL' if is_long else 'BUY'
            cprint(f"📝 Close attempt {attempt}: {close_side} {remaining_size} @ ${close_price:,.2f} (maker)", "cyan")

            # Convert size to USD amount
            usd_amount = remaining_size * close_price

            # Place limit order to close
            try:
                if is_long:
                    # Closing long = sell limit
                    order_result = limit_sell(symbol, usd_amount, close_price, slippage=slippage)
                else:
                    # Closing short = buy limit
                    order_result = limit_buy(symbol, usd_amount, close_price, slippage=slippage)

                if order_result:
                    last_price = close_price
                    last_size = remaining_size
                    cprint(f"✅ Close order placed", "green")
            except Exception as e:
                cprint(f"⚠️  Close order error: {e}", "yellow")

        time.sleep(ORDER_REPLACE_DELAY)

def cancel_all_orders(symbol: str):
    """Cancel all orders - trading_agent compatible"""
    # 🌙 Moon Dev: Auto-convert symbol format
    symbol = format_symbol_for_extended(symbol)

    if api is None:
        return
    api.cancel_all_orders(symbol)

# =============================================================================
# 📊 MARKET DATA FUNCTIONS
# =============================================================================

def get_ticker(symbol: str) -> Dict:
    """Get ticker data including bid, ask, and mark price"""
    # 🌙 Moon Dev: Auto-convert symbol format
    symbol = format_symbol_for_extended(symbol)

    if api is None:
        return {}

    loop = api._get_event_loop()

    async def fetch_ticker():
        orderbook = await api.trading_client.markets_info.get_orderbook_snapshot(market_name=symbol)
        bid = float(orderbook.data.bid[0].price) if orderbook.data.bid else 0
        ask = float(orderbook.data.ask[0].price) if orderbook.data.ask else 0
        mark = (bid + ask) / 2 if bid and ask else 0
        return {
            'bid': bid,
            'ask': ask,
            'mark_price': mark
        }

    return loop.run_until_complete(fetch_ticker())

def get_current_price(symbol: str) -> float:
    """Get current mid price for a symbol"""
    # 🌙 Moon Dev: Auto-convert symbol format
    symbol = format_symbol_for_extended(symbol)

    if api is None:
        return 0

    loop = api._get_event_loop()

    async def get_price():
        orderbook = await api.trading_client.markets_info.get_orderbook_snapshot(market_name=symbol)
        bid = float(orderbook.data.bid[0].price) if orderbook.data.bid else 0
        ask = float(orderbook.data.ask[0].price) if orderbook.data.ask else 0
        return (bid + ask) / 2 if bid and ask else 0

    return loop.run_until_complete(get_price())

def get_open_orders(symbol: str) -> List[Dict]:
    """Get list of open orders for a symbol"""
    # 🌙 Moon Dev: Auto-convert symbol format
    symbol = format_symbol_for_extended(symbol)

    if api is None:
        return []

    # Use the class method which uses REST API
    return api.get_open_orders(symbol)

def limit_buy(symbol: str, usd_amount: float, limit_price: float, leverage: int = DEFAULT_LEVERAGE, slippage: int = None):
    """Place a limit buy order (slippage ignored for compatibility)"""
    # 🌙 Moon Dev: Auto-convert symbol format
    symbol = format_symbol_for_extended(symbol)

    if api is None:
        cprint("❌ Extended Exchange API not initialized!", "red")
        return None

    try:
        # Convert USD to asset size
        asset_size = api.usd_to_asset_size(symbol, usd_amount)
        if asset_size <= 0:
            cprint(f"❌ Invalid asset size: {asset_size}", "red")
            return None

        cprint(f"📈 Placing limit BUY order", "cyan")
        cprint(f"   Symbol: {symbol}", "white")
        cprint(f"   Size: {asset_size} ({usd_amount} USD)", "white")
        cprint(f"   Price: ${limit_price:,.2f}", "white")
        cprint(f"   Leverage: {leverage}x", "white")

        # Place limit order
        result = api.buy_limit(symbol, asset_size, limit_price, leverage=leverage)

        if result:
            cprint(f"✅ Limit buy order placed!", "green")
            return result
        else:
            cprint(f"⚠️  Order placement returned no result", "yellow")
            return None

    except Exception as e:
        cprint(f"❌ Error placing limit buy order: {e}", "red")
        import traceback
        traceback.print_exc()
        return None

def limit_sell(symbol: str, usd_amount: float, limit_price: float, leverage: int = DEFAULT_LEVERAGE, slippage: int = None):
    """Place a limit sell order (slippage ignored for compatibility)"""
    # 🌙 Moon Dev: Auto-convert symbol format
    symbol = format_symbol_for_extended(symbol)

    if api is None:
        cprint("❌ Extended Exchange API not initialized!", "red")
        return None

    try:
        # Convert USD to asset size
        asset_size = api.usd_to_asset_size(symbol, usd_amount)
        if asset_size <= 0:
            cprint(f"❌ Invalid asset size: {asset_size}", "red")
            return None

        cprint(f"📉 Placing limit SELL order", "cyan")
        cprint(f"   Symbol: {symbol}", "white")
        cprint(f"   Size: {asset_size} ({usd_amount} USD)", "white")
        cprint(f"   Price: ${limit_price:,.2f}", "white")
        cprint(f"   Leverage: {leverage}x", "white")

        # Place limit order
        result = api.sell_limit(symbol, asset_size, limit_price, leverage=leverage)

        if result:
            cprint(f"✅ Limit sell order placed!", "green")
            return result
        else:
            cprint(f"⚠️  Order placement returned no result", "yellow")
            return None

    except Exception as e:
        cprint(f"❌ Error placing limit sell order: {e}", "red")
        import traceback
        traceback.print_exc()
        return None

# =============================================================================
# 🌙 MOON DEV UTILITIES
# =============================================================================

cprint("""
╔══════════════════════════════════════════════════════╗
║  🌙 Moon Dev's Extended Exchange Functions Loaded   ║
╚══════════════════════════════════════════════════════╝
""", "cyan")

if __name__ == "__main__":
    # Test the API
    cprint("\n🧪 Testing Extended Exchange API...\n", "yellow", attrs=['bold'])

    if api:
        # Test get balance
        balance = get_account_balance()
        cprint(f"💰 Account Equity: ${balance.get('equity', 0):,.2f}", "green")

        # Test get position
        test_symbol = "BTC-USD"
        _, in_pos, size, _, entry, pnl, is_long = get_position(test_symbol)
        if in_pos:
            cprint(f"📊 Position: {'LONG' if is_long else 'SHORT'} {abs(size)} {test_symbol} @ ${entry:,.2f} | PnL: {pnl:.2f}%", "cyan")
        else:
            cprint(f"📊 No position in {test_symbol}", "yellow")

        cprint("\n✅ Extended Exchange API test complete!", "green")
    else:
        cprint("\n❌ Extended Exchange API not available", "red")
