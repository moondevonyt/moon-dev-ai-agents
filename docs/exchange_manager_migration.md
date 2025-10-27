# 🔄 Exchange Manager Migration Guide

## Quick Start

### 1. Switch Exchange in Config

Edit `src/config.py`:

```python
# For Solana (memecoins, spot trading)
EXCHANGE = 'solana'

# For HyperLiquid (BTC/ETH/SOL perpetuals)
EXCHANGE = 'hyperliquid'
```

### 2. Update Your Agent

**BEFORE (Solana only):**
```python
from src import nice_funcs as n

class TradingAgent:
    def execute_trades(self):
        # Get position
        current_position = n.get_token_balance_usd(token)

        # Entry
        n.ai_entry(token, amount)

        # Exit
        n.chunk_kill(token, max_usd_order_size, slippage)
```

**AFTER (Works with both exchanges):**
```python
from src.exchange_manager import ExchangeManager

class TradingAgent:
    def __init__(self):
        self.em = ExchangeManager()  # Uses config.EXCHANGE automatically

    def execute_trades(self):
        # Get position (works for both!)
        current_position = self.em.get_token_balance_usd(symbol_or_token)

        # Entry (works for both!)
        self.em.ai_entry(symbol_or_token, amount)

        # Exit (works for both!)
        self.em.chunk_kill(symbol_or_token)
```

## Function Mapping

| Old (Solana only) | New (Unified) | Notes |
|-------------------|---------------|-------|
| `n.market_buy(token, usd)` | `em.market_buy(symbol_or_token, usd)` | Works for both |
| `n.market_sell(token, percent)` | `em.market_sell(symbol_or_token, amount)` | HyperLiquid uses USD amount |
| `n.get_token_balance_usd(token)` | `em.get_token_balance_usd(symbol_or_token)` | Returns USD value |
| `n.get_position(token)` | `em.get_position(symbol_or_token)` | Normalized format |
| `n.chunk_kill(token, max, slip)` | `em.chunk_kill(symbol_or_token)` | Auto-handles both |
| `n.ai_entry(token, usd)` | `em.ai_entry(symbol_or_token, usd)` | Works for both |
| `n.fetch_wallet_holdings_og(addr)` | `em.fetch_wallet_holdings()` | Returns DataFrame |
| `n.token_price(token)` | `em.get_current_price(symbol_or_token)` | Works for both |

## Exchange-Specific Features

### HyperLiquid Only
```python
# Set leverage (not available on Solana)
em.set_leverage('BTC', 10)  # 10x leverage

# Get account value (total portfolio)
value = em.get_account_value()
```

### Handling Token Lists
```python
from src.config import get_active_tokens

# This returns the right list based on active exchange
tokens = get_active_tokens()
# Solana: Returns MONITORED_TOKENS (contract addresses)
# HyperLiquid: Returns HYPERLIQUID_SYMBOLS (['BTC', 'ETH', 'SOL'])

for token in tokens:
    position = em.get_position(token)
    price = em.get_current_price(token)
```

## Complete Agent Example

```python
"""
Example: Migrated Trading Agent
Works with both Solana and HyperLiquid
"""

from src.exchange_manager import ExchangeManager
from src.config import get_active_tokens, EXCHANGE
from termcolor import cprint

class UnifiedTradingAgent:
    def __init__(self):
        self.em = ExchangeManager()
        cprint(f"✅ Trading Agent initialized for {EXCHANGE}", "green")

    def check_positions(self):
        """Check all positions on current exchange"""
        tokens = get_active_tokens()

        for token in tokens:
            position = self.em.get_position(token)

            if position['has_position']:
                cprint(f"📊 {token}: {position['size']} @ ${position['entry_price']:.2f}", "cyan")
                cprint(f"   PnL: {position['pnl_percent']:.2f}%", "white")
            else:
                cprint(f"   No position in {token}", "gray")

    def execute_entry(self, token, amount):
        """Execute entry on current exchange"""
        cprint(f"🎯 Entering {token} with ${amount}", "green")

        # This works for both exchanges!
        result = self.em.ai_entry(token, amount)

        cprint(f"✅ Entry executed on {EXCHANGE}", "green")
        return result

    def execute_exit(self, token):
        """Exit position on current exchange"""
        position = self.em.get_position(token)

        if position['has_position']:
            cprint(f"🚪 Exiting {token}", "yellow")
            result = self.em.chunk_kill(token)
            cprint(f"✅ Exit executed on {EXCHANGE}", "green")
            return result
        else:
            cprint(f"⚠️ No position to exit in {token}", "yellow")
            return None

    def run(self):
        """Main agent loop"""
        cprint(f"\n🤖 Running on {EXCHANGE.upper()}", "cyan", attrs=['bold'])

        # Check all positions
        self.check_positions()

        # Get balance
        balance = self.em.get_balance()
        cprint(f"\n💰 Available balance: ${balance:.2f}", "green")

        # Your trading logic here...

if __name__ == "__main__":
    agent = UnifiedTradingAgent()
    agent.run()
```

## Testing Your Migration

1. **Test with Solana first** (your current setup):
```python
# config.py
EXCHANGE = 'solana'
```

2. **Switch to HyperLiquid**:
```python
# config.py
EXCHANGE = 'hyperliquid'
HYPERLIQUID_SYMBOLS = ['BTC', 'ETH', 'SOL']
```

3. **Run the test script**:
```bash
python src/scripts/test_exchange_manager.py
```

## Common Issues & Solutions

### Issue: "HYPER_LIQUID_KEY not found"
**Solution:** Add to `.env`:
```
HYPER_LIQUID_KEY=your_ethereum_private_key_here
```

### Issue: Different position formats
**Solution:** Use the normalized format from `em.get_position()`:
```python
position = em.get_position(token)
# Always returns:
# {
#   'has_position': bool,
#   'size': float,
#   'entry_price': float,
#   'pnl_percent': float,
#   'is_long': bool
# }
```

### Issue: Token vs Symbol confusion
**Solution:** Let the exchange manager handle it:
- Solana: Pass contract addresses
- HyperLiquid: Pass symbols ('BTC', 'ETH', 'SOL')
- The manager knows which is which!

## Gradual Migration Strategy

1. **Phase 1**: Update critical agents (trading_agent, risk_agent)
2. **Phase 2**: Update data collection agents
3. **Phase 3**: Update analysis agents
4. **Phase 4**: Update content/UI agents

You don't need to migrate everything at once! The old `nice_funcs` still works for Solana-only operations.

## Hybrid Trading (Future)

```python
# Future feature: Route different assets to different exchanges
TOKEN_EXCHANGE_MAP = {
    'BTC': 'hyperliquid',  # Use HyperLiquid for majors
    'ETH': 'hyperliquid',
    'SOL': 'hyperliquid',
    '9BB6NFE...': 'solana',  # Use Solana for memecoins
}
```

## Summary

✅ **One line config change** to switch exchanges
✅ **Minimal code changes** in agents
✅ **Same functions** work for both exchanges
✅ **Backward compatible** with existing Solana code
✅ **Future proof** for adding more exchanges

🌙 Moon Dev's Exchange Manager - Trade Anywhere! 🚀