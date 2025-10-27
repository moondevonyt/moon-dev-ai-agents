# 🚀 HyperLiquid Integration Guide

How to use HyperLiquid for perpetual futures trading alongside Solana spot trading.

## Quick Start

### 1. Add HyperLiquid Key to .env
```bash
HYPER_LIQUID_KEY=your_ethereum_private_key_here
```

⚠️ **Important**: This is an Ethereum-style private key (64 hex characters), NOT a Solana key.

### 2. Switch to HyperLiquid in Config.

Edit `src/config.py`:
```python
# 🔄 Exchange Selection
EXCHANGE = 'hyperliquid'  # Switch from 'solana' to 'hyperliquid'

# Configure which symbols to trade
HYPERLIQUID_SYMBOLS = ['BTC', 'ETH', 'SOL']  # Add more as needed
HYPERLIQUID_LEVERAGE = 5  # 1-50x leverage
```

### 3. Your Agents Automatically Work!

No code changes needed in most agents! The ExchangeManager handles everything:

```python
# Your existing agent code still works:
from src.exchange_manager import ExchangeManager

em = ExchangeManager()  # Automatically uses config.EXCHANGE
em.market_buy('BTC', 100)  # Works with HyperLiquid!
em.get_position('BTC')  # Returns normalized position data
```

## Using the Exchange Manager

### Basic Usage (Works for Both Exchanges!)

```python
from src.exchange_manager import ExchangeManager
from src.config import get_active_tokens

# Initialize (automatically uses config.EXCHANGE)
em = ExchangeManager()

# Get appropriate token list
tokens = get_active_tokens()
# Returns ['BTC', 'ETH', 'SOL'] for HyperLiquid
# Returns contract addresses for Solana

# These functions work identically on both exchanges:
for token in tokens:
    # Get price
    price = em.get_current_price(token)

    # Check position
    position = em.get_position(token)
    if position['has_position']:
        print(f"Size: {position['size']}")
        print(f"PnL: {position['pnl_percent']}%")

    # Execute trades
    em.market_buy(token, 100)  # Buy $100 worth
    em.chunk_kill(token)  # Close position
```

### HyperLiquid-Specific Features

```python
# Set leverage (HyperLiquid only)
em.set_leverage('BTC', 10)  # 10x leverage

# Get account value
value = em.get_account_value()  # Total portfolio value

# Get available balance
balance = em.get_balance()  # Free balance for trading
```

## Key Differences

| Feature | Solana | HyperLiquid |
|---------|--------|-------------|
| **Asset Type** | Spot tokens | Perpetual futures |
| **Identifiers** | Contract addresses | Symbol strings ('BTC', 'ETH') |
| **Leverage** | No | Yes (1-50x) |
| **Fees** | Higher | Lower |
| **Liquidity** | Varies by token | Excellent for majors |
| **Best For** | Memecoins, new launches | BTC, ETH, SOL trading |

## Migrating Your Agents

### Option 1: No Changes Needed! (Recommended)

If your agent already uses nice_funcs, just switch to ExchangeManager:

**Before:**
```python
from src import nice_funcs as n

n.market_buy(token, 100)
n.get_position(token)
n.chunk_kill(token, max_size, slippage)
```

**After:**
```python
from src.exchange_manager import ExchangeManager

em = ExchangeManager()
em.market_buy(token, 100)  # Works for both!
em.get_position(token)  # Normalized format
em.chunk_kill(token)  # Auto-handles params
```

### Option 2: Direct HyperLiquid Usage

For HyperLiquid-specific features:

```python
import nice_funcs_hyperliquid as hl
import eth_account

account = eth_account.Account.from_key(os.getenv('HYPER_LIQUID_KEY'))

# HyperLiquid specific functions
hl.set_leverage('BTC', 10, account)
hl.limit_order('BTC', True, 0.001, 95000, False, account)
hl.pnl_close('BTC', target=5, max_loss=-2, account)
```

## Testing Your Setup

### 1. Test Exchange Manager
```bash
python src/scripts/test_exchange_manager.py
```

### 2. Test HyperLiquid Functions
```bash
python src/scripts/test_hyperliquid_mm.py
```

### 3. Run Example Agent
```bash
# Set EXCHANGE='hyperliquid' in config.py first
python src/agents/example_unified_agent.py
```

## Complete Example Agent

```python
#!/usr/bin/env python3
"""Example agent that works with both exchanges"""

from src.exchange_manager import ExchangeManager
from src.config import EXCHANGE, get_active_tokens
from termcolor import cprint

class HybridAgent:
    def __init__(self):
        self.em = ExchangeManager()
        cprint(f"✅ Agent initialized for {EXCHANGE}", "green")

    def check_all_positions(self):
        """Works for both exchanges!"""
        tokens = get_active_tokens()

        for token in tokens:
            position = self.em.get_position(token)
            if position['has_position']:
                cprint(f"{token}: {position['size']} @ ${position['entry_price']:.2f}", "cyan")
                cprint(f"  PnL: {position['pnl_percent']:.2f}%",
                      "green" if position['pnl_percent'] > 0 else "red")

    def execute_trade(self, token, amount):
        """Same code works for both exchanges!"""
        # Entry
        self.em.market_buy(token, amount)

        # Check position
        position = self.em.get_position(token)

        # Exit if profitable
        if position['pnl_percent'] > 5:
            self.em.chunk_kill(token)

if __name__ == "__main__":
    agent = HybridAgent()
    agent.check_all_positions()
```

## Troubleshooting

### "HYPER_LIQUID_KEY not found"
Add to `.env`:
```
HYPER_LIQUID_KEY=0x... (your Ethereum private key)
```

### "Order must have minimum value of $10"
HyperLiquid requires minimum $10 per order. The ExchangeManager automatically handles this.

### "Price must be divisible by tick size"
BTC requires whole number prices. The ExchangeManager handles rounding automatically.

### Position Not Showing After Market Order
HyperLiquid orders need time to settle. Wait 2-3 seconds after execution.

## When to Use Which Exchange

### Use HyperLiquid for:
- **Major cryptocurrencies** (BTC, ETH, SOL)
- **Leveraged trading** (up to 50x)
- **Lower fees** on high volume
- **Shorting** capability
- **Professional trading** with better liquidity

### Use Solana for:
- **Memecoins** and new launches
- **Small cap tokens**
- **Spot trading** (actually owning tokens)
- **DeFi interactions**
- **Tokens not on HyperLiquid**

## Advanced: Hybrid Trading

Future feature - route different assets to optimal exchanges:

```python
# In config.py (coming soon)
TOKEN_EXCHANGE_MAP = {
    'BTC': 'hyperliquid',  # Better liquidity
    'ETH': 'hyperliquid',  # Lower fees
    'BONK': 'solana',      # Only on Solana
    'WIF': 'solana'        # Memecoin trading
}
```

## Summary

✅ **One line change** in config.py to switch exchanges
✅ **Same functions** work for both Solana and HyperLiquid
✅ **Automatic handling** of differences (leverage, parameters, etc.)
✅ **Backward compatible** with existing code

🌙 Trade anywhere with Moon Dev's Exchange Manager! 🚀