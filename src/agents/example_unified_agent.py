#!/usr/bin/env python3
"""
🌙 Moon Dev's Example Unified Trading Agent
Shows how to use Exchange Manager for both Solana and HyperLiquid
Built with love by Moon Dev 🚀
"""

import sys
import os
from pathlib import Path
from termcolor import colored, cprint
from dotenv import load_dotenv
import time

# Add project root to path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

# Load environment variables
load_dotenv()

# Import the exchange manager
from src.exchange_manager import ExchangeManager
from src.config import EXCHANGE, get_active_tokens, max_usd_order_size, slippage

class UnifiedTradingAgent:
    """
    Example agent that works with both Solana and HyperLiquid
    """

    def __init__(self):
        """Initialize the unified agent"""
        # Create exchange manager (automatically uses config.EXCHANGE)
        self.em = ExchangeManager()

        cprint(f"\n🤖 Unified Trading Agent Initialized", "cyan", attrs=['bold'])
        cprint(f"📍 Active Exchange: {EXCHANGE.upper()}", "green")

        # Get the appropriate token list based on exchange
        self.tokens = get_active_tokens()
        cprint(f"📋 Monitoring {len(self.tokens)} tokens/symbols", "cyan")

    def display_account_info(self):
        """Display account information"""
        cprint("\n💰 Account Information", "yellow", attrs=['bold'])
        cprint("="*50, "yellow")

        try:
            # Get balance (works for both exchanges!)
            balance = self.em.get_balance()
            cprint(f"Available Balance: ${balance:.2f}", "green")

            # Get total account value
            total_value = self.em.get_account_value()
            cprint(f"Total Account Value: ${total_value:.2f}", "green")

        except Exception as e:
            cprint(f"Error getting account info: {str(e)}", "red")

    def check_all_positions(self):
        """Check positions across all monitored tokens"""
        cprint("\n📊 Position Summary", "cyan", attrs=['bold'])
        cprint("="*50, "cyan")

        positions_found = False

        for token in self.tokens:
            try:
                # Get position (unified interface!)
                position = self.em.get_position(token)

                if position['has_position']:
                    positions_found = True

                    # Display position info
                    if EXCHANGE == 'hyperliquid':
                        side = "LONG" if position['is_long'] else "SHORT"
                        cprint(f"\n{token} {side}:", "white", attrs=['bold'])
                    else:
                        cprint(f"\n{token[:8]}...:", "white", attrs=['bold'])

                    cprint(f"  Size: {position['size']}", "white")
                    cprint(f"  Entry: ${position['entry_price']:.4f}", "white")
                    cprint(f"  PnL: {position['pnl_percent']:.2f}%",
                          "green" if position['pnl_percent'] > 0 else "red")

                    # Calculate USD value
                    usd_value = self.em.get_token_balance_usd(token)
                    cprint(f"  Value: ${usd_value:.2f}", "cyan")

            except Exception as e:
                cprint(f"Error checking {token}: {str(e)}", "red")

        if not positions_found:
            cprint("No open positions found", "gray")

    def execute_test_trade(self):
        """Execute a small test trade (DO NOT RUN WITH REAL MONEY)"""
        cprint("\n⚠️  Test Trade Example (DO NOT RUN ON MAINNET)", "yellow", attrs=['bold'])
        cprint("="*50, "yellow")

        # Pick first token from list
        if not self.tokens:
            cprint("No tokens configured", "red")
            return

        token = self.tokens[0]
        cprint(f"Would trade: {token}", "cyan")

        # Get current price
        try:
            price = self.em.get_current_price(token)
            cprint(f"Current price: ${price:.6f}", "green")
        except:
            cprint("Could not get price", "red")

        # Show how you would execute trades
        cprint("\n📝 Trade Examples (not executing):", "yellow")

        cprint("\nMarket Buy:", "cyan")
        cprint(f"  em.market_buy('{token}', 10)  # Buy $10 worth", "white")

        cprint("\nMarket Sell:", "cyan")
        if EXCHANGE == 'hyperliquid':
            cprint(f"  em.market_sell('{token}', 10)  # Sell $10 worth", "white")
        else:
            cprint(f"  em.market_sell('{token}', 50)  # Sell 50% of position", "white")

        cprint("\nAI Entry:", "cyan")
        cprint(f"  em.ai_entry('{token}', 10)  # Smart entry with $10", "white")

        cprint("\nClose Position:", "cyan")
        cprint(f"  em.chunk_kill('{token}')  # Close entire position", "white")

        if EXCHANGE == 'hyperliquid':
            cprint("\nSet Leverage (HyperLiquid only):", "cyan")
            cprint(f"  em.set_leverage('{token}', 5)  # Set 5x leverage", "white")

    def demonstrate_unified_interface(self):
        """Show how the same code works for both exchanges"""
        cprint("\n🔄 Unified Interface Demo", "magenta", attrs=['bold'])
        cprint("="*50, "magenta")

        cprint("""
The beauty of the Exchange Manager is that the same code
works for both Solana and HyperLiquid:

# This code works regardless of exchange!
em = ExchangeManager()
position = em.get_position(token_or_symbol)
em.market_buy(token_or_symbol, 100)
em.chunk_kill(token_or_symbol)

Current Settings:
""", "white")

        cprint(f"  EXCHANGE = '{EXCHANGE}'", "cyan")

        if EXCHANGE == 'hyperliquid':
            cprint(f"  Symbols: {self.tokens}", "cyan")
            cprint("  Type: Perpetual Futures with leverage", "white")
        else:
            cprint(f"  Tokens: {len(self.tokens)} contract addresses", "cyan")
            cprint("  Type: Spot trading on-chain", "white")

    def run(self):
        """Main agent execution"""
        cprint(f"\n🌙 Moon Dev's Unified Agent Running on {EXCHANGE.upper()} 🚀",
               "cyan", attrs=['bold'])
        cprint("="*60, "cyan")

        # Display account info
        self.display_account_info()

        # Check all positions
        self.check_all_positions()

        # Show test trade examples
        self.execute_test_trade()

        # Demonstrate unified interface
        self.demonstrate_unified_interface()

        cprint("\n✅ Agent demonstration complete!", "green", attrs=['bold'])
        cprint("="*60, "green")

        # Tips
        cprint("\n💡 Quick Tips:", "yellow", attrs=['bold'])
        cprint("1. Change EXCHANGE in config.py to switch exchanges", "white")
        cprint("2. Use get_active_tokens() to get the right token list", "white")
        cprint("3. All main trading functions work the same way!", "white")
        cprint("4. Position data is normalized across both exchanges", "white")

        if EXCHANGE == 'solana':
            cprint("\n🔄 To try HyperLiquid:", "cyan")
            cprint("  1. Set EXCHANGE = 'hyperliquid' in config.py", "white")
            cprint("  2. Run this agent again!", "white")
        else:
            cprint("\n🔄 To try Solana:", "cyan")
            cprint("  1. Set EXCHANGE = 'solana' in config.py", "white")
            cprint("  2. Run this agent again!", "white")

def main():
    """Run the example agent"""
    try:
        agent = UnifiedTradingAgent()
        agent.run()

    except KeyboardInterrupt:
        cprint("\n👋 Agent stopped by user", "yellow")
    except Exception as e:
        cprint(f"\n❌ Error: {str(e)}", "red")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()