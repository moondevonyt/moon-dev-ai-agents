# 🚀 Complete HyperLiquid Setup Guide

Step-by-step guide to get your Moon Dev agents trading on HyperLiquid.

## Prerequisites

1. **Python Environment**: Make sure you're in the `tflow` conda environment
2. **Dependencies**: The HyperLiquid SDK should already be installed
3. **Funds**: You'll need USDC on Arbitrum to deposit to HyperLiquid.

## Step 1: Get Your HyperLiquid Private Key

HyperLiquid uses Ethereum-style wallets, NOT Solana wallets.

### Option A: Use Existing Ethereum Wallet
If you have MetaMask or another Ethereum wallet:
1. Open your wallet
2. Export the private key
3. It should start with `0x` or be 64 hex characters

### Option B: Create New Wallet for HyperLiquid
```python
# Run this to generate a new wallet
import eth_account

# Generate new account
account = eth_account.Account.create()
print(f"Address: {account.address}")
print(f"Private Key: {account.key.hex()}")
# SAVE THIS PRIVATE KEY SECURELY!
```

## Step 2: Add Private Key to .env

Edit your `.env` file:
```bash
# Add this line (replace with your actual key)
HYPER_LIQUID_KEY=0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef
```

⚠️ **Security**: Never commit your `.env` file to git!

## Step 3: Fund Your HyperLiquid Account

1. **Go to HyperLiquid**: https://app.hyperliquid.xyz
2. **Connect Wallet**: Use the address from your private key
3. **Deposit USDC**:
   - Click "Deposit"
   - Bridge USDC from Arbitrum
   - Minimum recommended: $50 for testing

## Step 4: Configure Your Trading

Edit `src/config.py`:

```python
# 🔄 Switch to HyperLiquid
EXCHANGE = 'hyperliquid'  # Changed from 'solana'

# ⚡ Configure HyperLiquid Trading
HYPERLIQUID_SYMBOLS = ['BTC', 'ETH', 'SOL']  # What to trade
HYPERLIQUID_LEVERAGE = 5  # Leverage (1-50x)

# Adjust position sizes for perps
usd_size = 25  # Position size in USD
max_usd_order_size = 15  # Max order size for HyperLiquid
```

## Step 5: Test Your Setup

### Quick Connection Test
```python
# Test connection (run this in Python)
from src.exchange_manager import ExchangeManager

em = ExchangeManager()
print(f"Balance: ${em.get_balance():.2f}")
print(f"Account Value: ${em.get_account_value():.2f}")
```

### Full Test Suite
```bash
# Run the complete test
python src/scripts/test_hyperliquid_mm.py
```

This will:
- ✅ Test basic functions (prices, balances)
- ✅ Place limit orders 10% away from market
- ✅ Execute a small market order
- ✅ Close the position
- ✅ Verify everything works

## Step 6: Run Your Agents

### Test with Example Agent
```bash
# This agent works with both exchanges!
python src/agents/example_unified_agent.py
```

### Run Your Trading Agents
```python
# Your existing agents now work with HyperLiquid!
python src/agents/trading_agent.py  # Uses ExchangeManager automatically
python src/agents/strategy_agent.py  # Also updated for HyperLiquid
```

## Step 7: Monitor Your Trades

### Via Command Line
```python
from src.exchange_manager import ExchangeManager

em = ExchangeManager()

# Check all positions
positions = em.get_all_positions()
for pos in positions:
    print(f"{pos['symbol']}: {pos['size']} @ ${pos['entry_price']:.2f}")
    print(f"  PnL: {pos['pnl_percent']:.2f}%")
```

### Via HyperLiquid UI
1. Go to https://app.hyperliquid.xyz
2. Connect with your wallet address
3. View positions, orders, and PnL

## Common Operations

### Set Leverage
```python
em = ExchangeManager()
em.set_leverage('BTC', 10)  # Set 10x leverage
```

### Open Position
```python
# Long position
em.market_buy('BTC', 50)  # Open $50 long

# Short position (HyperLiquid only!)
em.market_sell('BTC', 50)  # Open $50 short
```

### Close Position
```python
em.chunk_kill('BTC')  # Closes entire position
```

### Check PnL
```python
position = em.get_position('BTC')
print(f"PnL: {position['pnl_percent']:.2f}%")
```

## Switching Between Exchanges

It's just one line in `config.py`:

```python
# For HyperLiquid (BTC/ETH/SOL perps)
EXCHANGE = 'hyperliquid'

# For Solana (memecoins, spot)
EXCHANGE = 'solana'
```

Your agents automatically adapt!

## Risk Management

### Position Sizing
```python
# In config.py - adjust for HyperLiquid
MAX_POSITION_PERCENTAGE = 20  # Max 20% per position
CASH_PERCENTAGE = 30  # Keep 30% as buffer
```

### Stop Losses
```python
# Use the kill_switch for emergency closes
em.chunk_kill('BTC')  # Instantly close position
```

### Leverage Guidelines
- **Testing**: Start with 1-3x leverage
- **Production**: 5-10x for majors (BTC/ETH)
- **Maximum**: 50x available (use with extreme caution!)

## Available Symbols

Check available symbols: https://app.hyperliquid.xyz/trade

Popular perpetuals:
- **Majors**: BTC, ETH, SOL
- **L1s**: AVAX, ATOM, NEAR, SUI
- **DeFi**: UNI, AAVE, CRV, LDO
- **Memes**: DOGE, SHIB, PEPE, WIF

## Troubleshooting

### "HYPER_LIQUID_KEY not found"
- Check your `.env` file has the key
- Make sure it's 64 hex characters (with or without 0x prefix)

### "Insufficient balance"
- Deposit USDC to HyperLiquid
- Check balance: `em.get_balance()`

### "Order must have minimum value of $10"
- HyperLiquid minimum order is $10
- Increase your position size

### "Price must be divisible by tick size"
- BTC needs whole number prices
- ETH needs 0.1 decimal precision
- The ExchangeManager handles this automatically

### Position not showing
- Wait 2-3 seconds after order
- Orders are IOC (immediate or cancel)
- Check if order actually filled

## Advanced Features

### Limit Orders
```python
import nice_funcs_hyperliquid as hl
import eth_account

account = eth_account.Account.from_key(os.getenv('HYPER_LIQUID_KEY'))

# Place limit buy 5% below market
current_price = hl.get_current_price('BTC')
limit_price = round(current_price * 0.95)
hl.limit_order('BTC', True, 0.001, limit_price, False, account)
```

### PnL-Based Exits
```python
# Auto-close at 5% profit or -2% loss
hl.pnl_close('BTC', target=5, max_loss=-2, account)
```

### Multiple Positions
```python
# Trade multiple symbols
for symbol in ['BTC', 'ETH', 'SOL']:
    em.market_buy(symbol, 20)  # $20 each
```

## Best Practices

1. **Start Small**: Test with $10-20 positions first
2. **Use Stop Losses**: Set max_loss in risk_agent
3. **Monitor Leverage**: Higher leverage = higher risk
4. **Check Funding Rates**: Avoid high funding periods
5. **Diversify**: Trade multiple symbols
6. **Keep Reserves**: Don't use 100% of balance

## Next Steps

1. ✅ Test with small positions
2. ✅ Adjust leverage and position sizes
3. ✅ Configure your agents for HyperLiquid symbols
4. ✅ Monitor performance
5. ✅ Scale up gradually

## Support

- **HyperLiquid Docs**: https://hyperliquid.gitbook.io
- **Discord**: Join Moon Dev's community
- **Issues**: Report bugs on GitHub

---

🌙 Happy trading with HyperLiquid and Moon Dev! 🚀