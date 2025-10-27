"""
🌙 Moon Dev's Exchange Manager
Unified interface for trading on Solana and HyperLiquid
Built with love by Moon Dev 🚀
"""

import os
import sys
from termcolor import colored, cprint
from dotenv import load_dotenv
import pandas as pd
import time

# Load environment variables
load_dotenv()

class ExchangeManager:
    """
    Unified exchange interface for seamless switching between Solana and HyperLiquid
    """

    def __init__(self, exchange=None):
        """Initialize the exchange manager with the specified exchange"""
        from src import config

        # Use provided exchange or default from config
        self.exchange = exchange or config.EXCHANGE
        self.account = None

        # Initialize based on exchange type
        if self.exchange.lower() == 'hyperliquid':
            try:
                import eth_account
                from src import nice_funcs_hyperliquid as hl

                # Get HyperLiquid key from environment
                hl_key = os.getenv('HYPER_LIQUID_KEY')
                if not hl_key:
                    raise ValueError("HYPER_LIQUID_KEY not found in environment")

                # Initialize account
                self.account = eth_account.Account.from_key(hl_key)
                self.hl = hl

                cprint(f"✅ Initialized HyperLiquid exchange manager", "green")
                cprint(f"   Account: {self.account.address[:6]}...{self.account.address[-4:]}", "cyan")

            except Exception as e:
                cprint(f"❌ Failed to initialize HyperLiquid: {str(e)}", "red")
                raise

        elif self.exchange.lower() == 'solana':
            try:
                from src import nice_funcs as solana
                self.solana = solana
                cprint(f"✅ Initialized Solana exchange manager", "green")

            except Exception as e:
                cprint(f"❌ Failed to initialize Solana: {str(e)}", "red")
                raise
        else:
            raise ValueError(f"Unknown exchange: {self.exchange}")

    def market_buy(self, symbol_or_token, usd_amount):
        """
        Execute a market buy order

        Args:
            symbol_or_token: Symbol (for HyperLiquid) or token address (for Solana)
            usd_amount: USD amount to buy

        Returns:
            Order result from the respective exchange
        """
        if self.exchange.lower() == 'hyperliquid':
            return self.hl.market_buy(symbol_or_token, usd_amount, self.account)
        else:
            return self.solana.market_buy(symbol_or_token, usd_amount)

    def market_sell(self, symbol_or_token, usd_amount_or_percent):
        """
        Execute a market sell order

        Args:
            symbol_or_token: Symbol (for HyperLiquid) or token address (for Solana)
            usd_amount_or_percent: USD amount for HyperLiquid, percentage for Solana

        Returns:
            Order result from the respective exchange
        """
        if self.exchange.lower() == 'hyperliquid':
            # HyperLiquid expects USD amount
            return self.hl.market_sell(symbol_or_token, usd_amount_or_percent, self.account)
        else:
            # Solana expects percentage (0-100)
            return self.solana.market_sell(symbol_or_token, usd_amount_or_percent)

    def get_position(self, symbol_or_token):
        """
        Get current position for a symbol/token

        Returns:
            Position data in normalized format
        """
        if self.exchange.lower() == 'hyperliquid':
            positions, im_in_pos, pos_size, pos_sym, entry_px, pnl_perc, is_long = \
                self.hl.get_position(symbol_or_token, self.account)

            # Normalize to common format
            if im_in_pos:
                return {
                    'has_position': True,
                    'size': float(pos_size),
                    'symbol': pos_sym,
                    'entry_price': entry_px,
                    'pnl_percent': pnl_perc,
                    'is_long': is_long,
                    'raw_data': positions
                }
            else:
                return {
                    'has_position': False,
                    'size': 0,
                    'symbol': symbol_or_token,
                    'entry_price': 0,
                    'pnl_percent': 0,
                    'is_long': True,
                    'raw_data': None
                }
        else:
            # Get Solana position
            try:
                position_data = self.solana.get_position(symbol_or_token)

                # Normalize Solana position data
                if position_data and position_data.get('amount', 0) > 0:
                    return {
                        'has_position': True,
                        'size': position_data.get('amount', 0),
                        'symbol': symbol_or_token,
                        'entry_price': position_data.get('entry_price', 0),
                        'pnl_percent': position_data.get('pnl_percent', 0),
                        'is_long': True,  # Solana is spot only
                        'raw_data': position_data
                    }
                else:
                    return {
                        'has_position': False,
                        'size': 0,
                        'symbol': symbol_or_token,
                        'entry_price': 0,
                        'pnl_percent': 0,
                        'is_long': True,
                        'raw_data': None
                    }
            except:
                return {
                    'has_position': False,
                    'size': 0,
                    'symbol': symbol_or_token,
                    'entry_price': 0,
                    'pnl_percent': 0,
                    'is_long': True,
                    'raw_data': None
                }

    def get_token_balance_usd(self, symbol_or_token):
        """
        Get USD value of token balance

        Returns:
            USD value of position
        """
        if self.exchange.lower() == 'hyperliquid':
            position = self.get_position(symbol_or_token)
            if position['has_position']:
                # Get current price
                price = self.hl.get_current_price(symbol_or_token)
                return abs(position['size']) * price
            return 0
        else:
            return self.solana.get_token_balance_usd(symbol_or_token)

    def close_position(self, symbol_or_token):
        """
        Close an open position

        Args:
            symbol_or_token: Symbol (for HyperLiquid) or token address (for Solana)

        Returns:
            Close order result
        """
        if self.exchange.lower() == 'hyperliquid':
            return self.hl.kill_switch(symbol_or_token, self.account)
        else:
            # Use chunk_kill for Solana
            from src.config import max_usd_order_size, slippage
            return self.solana.chunk_kill(symbol_or_token, max_usd_order_size, slippage)

    def ai_entry(self, symbol_or_token, usd_amount):
        """
        AI-assisted entry (wrapper for market_buy with additional logic)

        Args:
            symbol_or_token: Symbol (for HyperLiquid) or token address (for Solana)
            usd_amount: USD amount to enter
        """
        if self.exchange.lower() == 'hyperliquid':
            # For HyperLiquid, use market_buy directly
            return self.market_buy(symbol_or_token, usd_amount)
        else:
            # For Solana, use the ai_entry function
            return self.solana.ai_entry(symbol_or_token, usd_amount)

    def chunk_kill(self, symbol_or_token, max_order_size=None, slippage=None):
        """
        Close position in chunks (primarily for Solana, but works for both)

        Args:
            symbol_or_token: Symbol (for HyperLiquid) or token address (for Solana)
            max_order_size: Maximum order size per chunk
            slippage: Slippage tolerance
        """
        if self.exchange.lower() == 'hyperliquid':
            # HyperLiquid doesn't need chunking, just close the position
            return self.hl.kill_switch(symbol_or_token, self.account)
        else:
            from src.config import max_usd_order_size, slippage as default_slippage
            max_order_size = max_order_size or max_usd_order_size
            slippage = slippage or default_slippage
            return self.solana.chunk_kill(symbol_or_token, max_order_size, slippage)

    def get_current_price(self, symbol_or_token):
        """
        Get current price of symbol/token

        Returns:
            Current price in USD
        """
        if self.exchange.lower() == 'hyperliquid':
            return self.hl.get_current_price(symbol_or_token)
        else:
            return self.solana.token_price(symbol_or_token)

    def get_account_value(self):
        """
        Get total account value

        Returns:
            Total account value in USD
        """
        if self.exchange.lower() == 'hyperliquid':
            return self.hl.get_account_value(self.account)
        else:
            # For Solana, sum up all token values
            from src.config import address
            positions = self.solana.fetch_wallet_holdings_og(address)
            total_value = 0
            if positions is not None and not positions.empty:
                for _, row in positions.iterrows():
                    total_value += row.get('value_usd', 0)
            return total_value

    def get_balance(self):
        """
        Get available balance for trading

        Returns:
            Available balance in USD
        """
        if self.exchange.lower() == 'hyperliquid':
            return self.hl.get_balance(self.account)
        else:
            from src.config import USDC_ADDRESS
            return self.solana.get_token_balance_usd(USDC_ADDRESS)

    def get_all_positions(self):
        """
        Get all open positions

        Returns:
            List of position dictionaries
        """
        if self.exchange.lower() == 'hyperliquid':
            return self.hl.get_all_positions(self.account)
        else:
            from src.config import address, EXCLUDED_TOKENS
            positions = self.solana.fetch_wallet_holdings_og(address)

            all_positions = []
            if positions is not None and not positions.empty:
                for _, row in positions.iterrows():
                    token = row.get('token_address', '')
                    if token not in EXCLUDED_TOKENS and row.get('value_usd', 0) > 0:
                        all_positions.append({
                            'symbol': token,
                            'size': row.get('amount', 0),
                            'entry_price': row.get('price', 0),
                            'pnl_percent': 0,  # Solana doesn't track this directly
                            'is_long': True,  # Solana is spot only
                            'value_usd': row.get('value_usd', 0)
                        })
            return all_positions

    def set_leverage(self, symbol, leverage):
        """
        Set leverage for a symbol (HyperLiquid only)

        Args:
            symbol: Trading symbol
            leverage: Leverage amount (1-50)
        """
        if self.exchange.lower() == 'hyperliquid':
            return self.hl.set_leverage(symbol, leverage, self.account)
        else:
            cprint(f"⚠️ Leverage not applicable for Solana spot trading", "yellow")
            return None

    def get_data(self, symbol_or_token, days_back, timeframe):
        """
        Get OHLCV data for analysis

        Args:
            symbol_or_token: Symbol (for HyperLiquid) or token address (for Solana)
            days_back: Number of days of historical data
            timeframe: Timeframe (1m, 5m, 15m, 1H, etc.)

        Returns:
            DataFrame with OHLCV data
        """
        if self.exchange.lower() == 'hyperliquid':
            # HyperLiquid doesn't have get_data in our implementation yet
            # For now, return empty dataframe
            cprint(f"⚠️ OHLCV data not yet implemented for HyperLiquid", "yellow")
            return pd.DataFrame()
        else:
            return self.solana.get_data(symbol_or_token, days_back, timeframe)

    def fetch_wallet_holdings(self, wallet_address=None):
        """
        Fetch all wallet holdings

        Args:
            wallet_address: Optional wallet address (for Solana)

        Returns:
            DataFrame with holdings
        """
        if self.exchange.lower() == 'hyperliquid':
            # Convert HyperLiquid positions to DataFrame format
            positions = self.get_all_positions()
            if positions:
                df = pd.DataFrame(positions)
                return df
            return pd.DataFrame()
        else:
            from src.config import address
            wallet_address = wallet_address or address
            return self.solana.fetch_wallet_holdings_og(wallet_address)

    def __str__(self):
        """String representation of the exchange manager"""
        return f"ExchangeManager(exchange={self.exchange})"

    def __repr__(self):
        """Representation of the exchange manager"""
        return self.__str__()


# Convenience function for quick initialization
def create_exchange_manager(exchange=None):
    """
    Create and return an ExchangeManager instance

    Args:
        exchange: Optional exchange override ('solana' or 'hyperliquid')

    Returns:
        ExchangeManager instance
    """
    return ExchangeManager(exchange)