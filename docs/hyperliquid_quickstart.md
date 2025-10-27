# 🚀 HyperLiquid Integration - Quick Reference

## 5-Minute Setup

### 1️⃣ Add Your Key
```bash
# In .env file
HYPER_LIQUID_KEY=your_ethereum_private_key_here
```

### 2️⃣ Switch Exchange
```python
# In src/config.py
EXCHANGE = 'hyperliquid'  # Switch from 'solana'
```

### 3️⃣ Test It
```bash
python src/scripts/test_exchange_manager.py
```

That's it! Your agents now trade on HyperLiquid! 🎉

## Quick Commands

### Check Everything Works
```python
from src.exchange_manager import ExchangeManager

em = ExchangeManager()
print(f"Balance: ${em.get_balance():.2f}")
print(f"BTC Price: ${em.get_current_price('BTC'):,.2f}")
```

### Execute Trades
```python
# Open long position
em.market_buy('BTC', 50)  # $50 long

# Check position
pos = em.get_position('BTC')
print(f"PnL: {pos['pnl_percent']:.2f}%")

# Close position
em.chunk_kill('BTC')
```

### Set Leverage
```python
em.set_leverage('BTC', 10)  # 10x leverage
```

## Your Agents Work Automatically!

These agents already support HyperLiquid via ExchangeManager:
- ✅ `trading_agent.py` - LLM trading decisions
- ✅ `strategy_agent.py` - Strategy-based trading
- ✅ `base_agent.py` - Parent class for all agents
- ✅ `example_unified_agent.py` - Example implementation

Just change `EXCHANGE = 'hyperliquid'` and run them!

## Config Options

```python
# In src/config.py

# What to trade on HyperLiquid
HYPERLIQUID_SYMBOLS = ['BTC', 'ETH', 'SOL']

# Leverage setting (1-50x)
HYPERLIQUID_LEVERAGE = 5

# Position sizes (adjust for perps)
usd_size = 25  # $25 positions
max_usd_order_size = 15  # Max $15 per order
```

## Switch Between Exchanges

```python
# For HyperLiquid (perps with leverage)
EXCHANGE = 'hyperliquid'

# For Solana (spot memecoins)
EXCHANGE = 'solana'
```

Same code works for both! The ExchangeManager handles everything.

## Test Scripts

```bash
# Test HyperLiquid connection and trading
python src/scripts/test_hyperliquid_mm.py

# Test exchange switching
python src/scripts/test_exchange_manager.py

# Example agent (works with both exchanges)
python src/agents/example_unified_agent.py
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "HYPER_LIQUID_KEY not found" | Add key to `.env` file |
| "Order minimum $10" | Increase position size |
| "Insufficient balance" | Deposit USDC to HyperLiquid |
| Position not showing | Wait 2-3 seconds after order |

## Full Documentation

- 📖 **Setup Guide**: [hyperliquid_setup.md](hyperliquid_setup.md)
- 🔄 **Migration Guide**: [hyperliquid_migration.md](hyperliquid_migration.md)
- 📊 **Exchange Manager**: [exchange_manager_migration.md](exchange_manager_migration.md)

## Why HyperLiquid?

- ⚡ **Leverage**: Up to 50x (be careful!)
- 💰 **Lower Fees**: Better for high volume
- 📊 **Majors**: Best liquidity for BTC/ETH/SOL
- 🔻 **Shorting**: Can profit from downtrends
- 🚀 **Fast**: CEX-like speed, DEX benefits

## Why Keep Solana?

- 🐕 **Memecoins**: Where the degen action is
- 🆕 **New Launches**: First access to tokens
- 💎 **Spot Trading**: Actually own the tokens
- 🌊 **DeFi**: Liquidity pools, staking, etc.

---

**TL;DR**: Change one line in config.py, and your bots trade anywhere! 🌙🚀

*Built with love by Moon Dev*