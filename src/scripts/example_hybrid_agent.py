#!/usr/bin/env python3
"""
🌙 Moon Dev's Hybrid Trading Example
Shows how to use both Solana and HyperLiquid in one agent
Built with love by Moon Dev 🚀
"""

import os
import sys
import time
from termcolor import cprint
from dotenv import load_dotenv
import eth_account

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment
load_dotenv()

# Import BOTH trading functions
import nice_funcs as solana  # Solana spot trading
import nice_funcs_hyperliquid as hl  # HyperLiquid perps

def trade_on_solana():
    """Example: Trade spot tokens on Solana"""
    cprint("\n🌊 SOLANA SPOT TRADING", "cyan", attrs=['bold'])
    cprint("="*50, "cyan")

    try:
        # Example token address (replace with real one)
        token_address = "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"  # Example: Bonk

        # Get token info
        cprint("Getting token overview...", "yellow")
        # overview = solana.token_overview(token_address)
        # price = solana.token_price(token_address)
        # cprint(f"Token price: ${price}", "green")

        # Check position
        # position = solana.get_position(token_address)
        # if position:
        #     cprint(f"Current position: {position}", "green")

        # Example trade (commented for safety)
        # solana.market_buy(token_address, 10)  # Buy $10 worth
        # solana.market_sell(token_address, 50)  # Sell 50% of position

        cprint("✅ Solana functions work!", "green")

    except Exception as e:
        cprint(f"❌ Solana error: {str(e)}", "red")

def trade_on_hyperliquid():
    """Example: Trade perpetuals on HyperLiquid"""
    cprint("\n⚡ HYPERLIQUID PERPS TRADING", "magenta", attrs=['bold'])
    cprint("="*50, "magenta")

    try:
        # Initialize HyperLiquid account
        account = eth_account.Account.from_key(os.getenv('HYPER_LIQUID_KEY'))

        # Get BTC price
        cprint("Getting BTC perp price...", "yellow")
        btc_price = hl.get_current_price('BTC')
        cprint(f"BTC perp price: ${btc_price:,.2f}", "green")

        # Check account value
        account_value = hl.get_account_value(account)
        cprint(f"Account value: ${account_value:,.2f}", "green")

        # Check position
        positions, im_in_pos, size, sym, entry, pnl, is_long = hl.get_position('BTC', account)
        if im_in_pos:
            side = "LONG" if is_long else "SHORT"
            cprint(f"Current position: {side} {size} BTC @ ${entry:.2f} (PnL: {pnl:.2f}%)", "green")
        else:
            cprint("No BTC position", "yellow")

        # Example trades (commented for safety)
        # hl.market_buy('BTC', 10, account)  # Buy $10 of BTC perps
        # hl.market_sell('ETH', 10, account)  # Sell $10 of ETH perps

        cprint("✅ HyperLiquid functions work!", "green")

    except Exception as e:
        cprint(f"❌ HyperLiquid error: {str(e)}", "red")

def hybrid_strategy_example():
    """Example: Use both exchanges in one strategy"""
    cprint("\n🔀 HYBRID STRATEGY EXAMPLE", "yellow", attrs=['bold'])
    cprint("="*50, "yellow")

    cprint("""
Strategy Idea:
1. Monitor BTC perps on HyperLiquid for direction
2. When BTC pumps on perps, buy SOL memecoins on Solana
3. When BTC dumps on perps, sell memecoins on Solana

This leverages:
- HyperLiquid: Better for BTC/ETH with leverage
- Solana: Better for memecoins and new tokens
    """, "white")

    # Example implementation skeleton:
    try:
        # Get HyperLiquid account
        hl_account = eth_account.Account.from_key(os.getenv('HYPER_LIQUID_KEY'))

        # Check BTC trend on HyperLiquid
        btc_price_now = hl.get_current_price('BTC')
        cprint(f"BTC on HyperLiquid: ${btc_price_now:,.2f}", "cyan")

        # Make decision
        if btc_price_now > 100000:  # Example condition
            cprint("📈 BTC looks bullish, would buy memecoins on Solana", "green")
            # solana.market_buy(memecoin_address, 100)
        else:
            cprint("📉 BTC looks bearish, would sell memecoins on Solana", "red")
            # solana.market_sell(memecoin_address, 100)

        cprint("\n✅ Hybrid strategy logic works!", "green", attrs=['bold'])

    except Exception as e:
        cprint(f"❌ Hybrid strategy error: {str(e)}", "red")

def main():
    """Run examples"""
    cprint("\n" + "="*60, "cyan")
    cprint("🌙 MOON DEV'S HYBRID TRADING EXAMPLE", "cyan", attrs=['bold'])
    cprint("="*60, "cyan")

    # Check environment
    has_solana = os.getenv('SOLANA_PRIVATE_KEY') is not None
    has_hyperliquid = os.getenv('HYPER_LIQUID_KEY') is not None

    cprint("\n🔑 Environment Check:", "yellow")
    cprint(f"  Solana: {'✅' if has_solana else '❌'} SOLANA_PRIVATE_KEY", "white")
    cprint(f"  HyperLiquid: {'✅' if has_hyperliquid else '❌'} HYPER_LIQUID_KEY", "white")

    # Run examples based on what's configured
    if has_solana:
        trade_on_solana()
    else:
        cprint("\n⚠️  Skipping Solana (no key)", "yellow")

    if has_hyperliquid:
        trade_on_hyperliquid()
    else:
        cprint("\n⚠️  Skipping HyperLiquid (no key)", "yellow")

    if has_solana and has_hyperliquid:
        hybrid_strategy_example()
    else:
        cprint("\n⚠️  Skipping hybrid strategy (need both keys)", "yellow")

    cprint("\n" + "="*60, "cyan")
    cprint("📚 SUMMARY", "cyan", attrs=['bold'])
    cprint("="*60, "cyan")

    cprint("""
How to use in your agents:

1. For Solana only:
   from nice_funcs import market_buy, market_sell

2. For HyperLiquid only:
   import nice_funcs_hyperliquid as hl
   account = eth_account.Account.from_key(key)
   hl.market_buy('BTC', 100, account)

3. For both (hybrid):
   import nice_funcs as solana
   import nice_funcs_hyperliquid as hl

Choose based on your needs:
- Solana: Spot tokens, memecoins, new launches
- HyperLiquid: BTC/ETH/SOL perps with leverage
    """, "white")

    cprint("\n🌕 Thanks for using Moon Dev Trading Bots! 🤖", "magenta")

if __name__ == "__main__":
    main()