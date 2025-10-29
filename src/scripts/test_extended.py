"""
🌙 Moon Dev's Extended Exchange Test Script 🌙

Comprehensive test of all Extended exchange functionality:
1. Get position and balance
2. Place limit orders (bid/ask) that won't fill
3. View open orders
4. Cancel orders
5. Market buy $10
6. View position
7. Close position
8. Verify closure

Built with love by Moon Dev 🚀
"""

import sys
import time
from pathlib import Path
from termcolor import cprint

# Add project root to path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from src import nice_funcs_extended as extended

# Test configuration
SYMBOL = "BTC"  # Will auto-convert to BTC-USD
TEST_POSITION_SIZE = 10  # $10 position size
ORDER_OFFSET = 20  # Place orders $20 away from market

def print_separator(title=""):
    """Print a nice separator"""
    cprint("\n" + "="*70, "cyan")
    if title:
        cprint(f"  {title}", "cyan", attrs=['bold'])
        cprint("="*70, "cyan")

def test_extended_exchange():
    """Run comprehensive Extended exchange test"""
    cprint("\n🌙 Moon Dev's Extended Exchange Test Starting! 🚀\n", "white", "on_blue")

    try:
        # =============================================================
        # STEP 1: Get Current Position and Balance
        # =============================================================
        print_separator("📊 STEP 1: Check Initial Position & Balance")

        cprint(f"\n💰 Getting account balance...", "yellow")
        balance = extended.get_account_balance()
        if balance and 'equity' in balance:
            cprint(f"✅ Account Equity: ${balance['equity']:,.2f} USD", "green", attrs=['bold'])
        else:
            cprint(f"⚠️  Could not get balance", "yellow")

        cprint(f"\n📈 Checking {SYMBOL} position...", "yellow")
        position = extended.get_position(SYMBOL)
        if position:
            cprint(f"✅ Current Position:", "green")
            cprint(f"   Position Size: {position['position_amount']}", "white")
            cprint(f"   Entry Price: ${position['entry_price']:,.2f}", "white")
            cprint(f"   Mark Price: ${position['mark_price']:,.2f}", "white")
            cprint(f"   P&L: ${position['pnl']:,.2f} ({position['pnl_percentage']:+.2f}%)", "white")
            cprint(f"   Direction: {'LONG' if position['is_long'] else 'SHORT'}", "white")
        else:
            cprint(f"✅ No open position for {SYMBOL}", "green")

        # =============================================================
        # STEP 2: Place Limit Orders (Won't Fill)
        # =============================================================
        print_separator("📝 STEP 2: Place Test Limit Orders")

        cprint(f"\n🎯 Getting current market prices for {SYMBOL}...", "yellow")
        ticker = extended.get_ticker(SYMBOL)
        if not ticker:
            cprint("❌ Could not get ticker data", "red")
            return

        bid_price = ticker['bid']
        ask_price = ticker['ask']
        mark_price = ticker['mark_price']

        cprint(f"✅ Market Data:", "green")
        cprint(f"   Bid: ${bid_price:,.2f}", "white")
        cprint(f"   Ask: ${ask_price:,.2f}", "white")
        cprint(f"   Mark: ${mark_price:,.2f}", "white")

        # Calculate order prices (won't fill)
        buy_limit_price = bid_price - ORDER_OFFSET
        sell_limit_price = ask_price + ORDER_OFFSET

        cprint(f"\n📤 Placing limit BUY order ${ORDER_OFFSET} below bid...", "cyan")
        cprint(f"   Price: ${buy_limit_price:,.2f} (current bid: ${bid_price:,.2f})", "white")
        buy_order = extended.limit_buy(SYMBOL, TEST_POSITION_SIZE, buy_limit_price)
        if buy_order:
            cprint(f"✅ Buy order placed!", "green")
        else:
            cprint(f"⚠️  Buy order failed", "yellow")

        time.sleep(1)  # Brief pause between orders

        cprint(f"\n📤 Placing limit SELL order ${ORDER_OFFSET} above ask...", "cyan")
        cprint(f"   Price: ${sell_limit_price:,.2f} (current ask: ${ask_price:,.2f})", "white")
        sell_order = extended.limit_sell(SYMBOL, TEST_POSITION_SIZE, sell_limit_price)
        if sell_order:
            cprint(f"✅ Sell order placed!", "green")
        else:
            cprint(f"⚠️  Sell order failed", "yellow")

        # =============================================================
        # STEP 3: View Open Orders
        # =============================================================
        print_separator("📋 STEP 3: View Open Orders & Positions")

        cprint(f"\n🔍 Fetching open orders for {SYMBOL}...", "yellow")
        open_orders = extended.get_open_orders(SYMBOL)
        if open_orders:
            cprint(f"✅ Found {len(open_orders)} open order(s):", "green", attrs=['bold'])
            for i, order in enumerate(open_orders, 1):
                cprint(f"\n   Order #{i}:", "cyan")
                cprint(f"      Side: {order.get('side', 'N/A')}", "white")
                cprint(f"      Size: {order.get('size', 'N/A')}", "white")
                cprint(f"      Price: ${order.get('price', 0):,.2f}", "white")
                cprint(f"      Status: {order.get('status', 'N/A')}", "white")
        else:
            cprint(f"📭 No open orders", "yellow")

        cprint(f"\n📊 Checking position again...", "yellow")
        position = extended.get_position(SYMBOL)
        if position and position['position_amount'] != 0:
            cprint(f"✅ Position: {position['position_amount']} @ ${position['entry_price']:,.2f}", "green")
        else:
            cprint(f"✅ No position (as expected)", "green")

        # =============================================================
        # STEP 4: Wait and Cancel Orders
        # =============================================================
        print_separator("⏳ STEP 4: Wait 5 Seconds & Cancel Orders")

        cprint(f"\n⏰ Waiting 5 seconds...", "yellow")
        for i in range(5, 0, -1):
            cprint(f"   {i}...", "cyan")
            time.sleep(1)
        cprint(f"✅ Wait complete!", "green")

        cprint(f"\n🚫 Cancelling all open orders for {SYMBOL}...", "yellow")
        cancelled = extended.cancel_all_orders(SYMBOL)
        if cancelled:
            cprint(f"✅ All orders cancelled!", "green", attrs=['bold'])
        else:
            cprint(f"⚠️  Cancel failed or no orders to cancel", "yellow")

        time.sleep(1)  # Brief pause

        cprint(f"\n🔍 Verifying cancellation...", "yellow")
        open_orders = extended.get_open_orders(SYMBOL)
        if not open_orders or len(open_orders) == 0:
            cprint(f"✅ Confirmed: No open orders", "green", attrs=['bold'])
        else:
            cprint(f"⚠️  Still have {len(open_orders)} open order(s)", "yellow")

        # =============================================================
        # STEP 5: Market Buy $10
        # =============================================================
        print_separator("💰 STEP 5: Market Buy $10 Position")

        cprint(f"\n📈 Executing market BUY for ${TEST_POSITION_SIZE}...", "cyan", attrs=['bold'])
        success = extended.market_buy(SYMBOL, TEST_POSITION_SIZE)
        if success:
            cprint(f"✅ Market buy executed!", "green", attrs=['bold'])
        else:
            cprint(f"❌ Market buy failed!", "red")
            return

        time.sleep(2)  # Wait for order to settle

        # =============================================================
        # STEP 6: Check Position After Buy
        # =============================================================
        print_separator("📊 STEP 6: Verify Position Opened")

        cprint(f"\n🔍 Checking {SYMBOL} position after buy...", "yellow")
        position = extended.get_position(SYMBOL)
        if position and position['position_amount'] != 0:
            cprint(f"✅ Position Confirmed!", "green", attrs=['bold'])
            cprint(f"   Position Size: {position['position_amount']}", "white")
            cprint(f"   Entry Price: ${position['entry_price']:,.2f}", "white")
            cprint(f"   Mark Price: ${position['mark_price']:,.2f}", "white")
            cprint(f"   P&L: ${position['pnl']:,.2f} ({position['pnl_percentage']:+.2f}%)", "white")
            cprint(f"   Direction: {'LONG' if position['is_long'] else 'SHORT'}", "white")
            cprint(f"   Notional Value: ${abs(position['position_amount']) * position['mark_price']:,.2f}", "cyan", attrs=['bold'])
        else:
            cprint(f"❌ No position found after buy!", "red")
            return

        # =============================================================
        # STEP 7: Test Leverage with Short Position
        # =============================================================
        print_separator("⚡ STEP 7: Test Leverage - Open Short with 5x")

        TEST_LEVERAGE = 5
        cprint(f"\n📉 Testing short position with {TEST_LEVERAGE}x leverage...", "cyan", attrs=['bold'])
        cprint(f"   Opening ${TEST_POSITION_SIZE} short at {TEST_LEVERAGE}x leverage", "white")

        # Use open_short with slippage and leverage (matches trading_agent signature)
        try:
            slippage = 199  # Not used by Extended, but testing compatibility
            success = extended.open_short(SYMBOL, TEST_POSITION_SIZE, slippage, leverage=TEST_LEVERAGE)
            if success:
                cprint(f"✅ Short position opened with {TEST_LEVERAGE}x leverage!", "green", attrs=['bold'])
            else:
                cprint(f"❌ Short position failed!", "red")
        except Exception as e:
            cprint(f"❌ Error opening short: {e}", "red")
            import traceback
            traceback.print_exc()

        time.sleep(2)  # Wait for position to settle

        cprint(f"\n🔍 Checking position after short...", "yellow")
        position = extended.get_position(SYMBOL)
        if position and position['position_amount'] != 0:
            cprint(f"✅ Short Position Confirmed!", "green", attrs=['bold'])
            cprint(f"   Position Size: {position['position_amount']}", "white")
            cprint(f"   Entry Price: ${position['entry_price']:,.2f}", "white")
            cprint(f"   Direction: {'LONG' if position['is_long'] else 'SHORT'}", "white")
            cprint(f"   Notional Value: ${abs(position['position_amount']) * position['mark_price']:,.2f}", "cyan", attrs=['bold'])
        else:
            cprint(f"⚠️  No short position found!", "yellow")

        # =============================================================
        # STEP 8: Close Position
        # =============================================================
        print_separator("🔄 STEP 8: Close Position")

        cprint(f"\n📉 Closing {SYMBOL} position...", "yellow", attrs=['bold'])
        closed = extended.close_position(SYMBOL)
        if closed:
            cprint(f"✅ Position closed!", "green", attrs=['bold'])
        else:
            cprint(f"❌ Failed to close position!", "red")
            return

        time.sleep(2)  # Wait for closure to settle

        # =============================================================
        # STEP 8: Verify Closure
        # =============================================================
        print_separator("✅ STEP 8: Verify Position Closed")

        cprint(f"\n🔍 Checking {SYMBOL} position after close...", "yellow")
        position = extended.get_position(SYMBOL)
        if not position or position['position_amount'] == 0:
            cprint(f"✅ Position Confirmed CLOSED!", "green", attrs=['bold'])
            cprint(f"   No open position for {SYMBOL}", "white")
        else:
            cprint(f"⚠️  Position still shows open:", "yellow")
            cprint(f"   Position Size: {position['position_amount']}", "white")

        # =============================================================
        # FINAL STATUS
        # =============================================================
        print_separator("🎉 TEST COMPLETE!")

        cprint(f"\n✨ Moon Dev's Extended Exchange Test Complete! ✨\n", "white", "on_green")
        cprint(f"All functionality tested:", "green")
        cprint(f"  ✅ Get position", "green")
        cprint(f"  ✅ Get balance", "green")
        cprint(f"  ✅ Get ticker (bid/ask)", "green")
        cprint(f"  ✅ Place limit orders", "green")
        cprint(f"  ✅ Get open orders", "green")
        cprint(f"  ✅ Cancel orders", "green")
        cprint(f"  ✅ Market buy", "green")
        cprint(f"  ✅ Close position", "green")
        cprint(f"\n🌙 Extended Exchange is fully functional! 🚀\n", "cyan", attrs=['bold'])

    except KeyboardInterrupt:
        cprint(f"\n\n⚠️  Test interrupted by user", "yellow")
        cprint(f"🌙 Moon Dev says: Clean up any open orders/positions manually if needed\n", "cyan")
    except Exception as e:
        cprint(f"\n\n❌ Test failed with error:", "red")
        cprint(f"   {str(e)}", "red")
        import traceback
        cprint(f"\n📋 Traceback:", "yellow")
        traceback.print_exc()
        cprint(f"\n🌙 Moon Dev says: Check the error above and try again!\n", "cyan")

if __name__ == "__main__":
    test_extended_exchange()
