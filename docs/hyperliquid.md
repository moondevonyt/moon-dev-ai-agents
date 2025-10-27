# HyperLiquid Integration

Trade perpetuals on HyperLiquid alongside Solana spot trading.

## Setup
```bash
# Add to .env
HYPER_LIQUID_KEY=your_ethereum_private_key
```

## Usage in Agents

### For HyperLiquid Trading:
```python
# Import HyperLiquid functions
import nice_funcs_hyperliquid as hl
import eth_account

# Initialize account
account = eth_account.Account.from_key(os.getenv('HYPER_LIQUID_KEY'))

# Trade on HyperLiquid
hl.market_buy('BTC', 100, account)  # Buy $100 of BTC perps
hl.market_sell('ETH', 50, account)  # Sell $50 of ETH perps
position = hl.get_position('BTC', account)
hl.pnl_close('BTC', target=2, max_loss=-1, account)
```

### For Solana Trading:
```python
# Import Solana functions
from nice_funcs import market_buy, market_sell, get_position

# Trade on Solana
market_buy('token_address', 100)  # Buy $100 of token
market_sell('token_address', 50)  # Sell 50% of position
```

## Key Differences

| Feature | Solana | HyperLiquid |
|---------|--------|-------------|
| Symbol | Contract address | Symbol (BTC, ETH, SOL) |
| Account | Uses SOLANA_PRIVATE_KEY | Pass account object |
| Trading | Spot tokens | Perpetual futures |
| Size | Token amount | USD size |

## Testing
```bash
python src/scripts/test_hyperliquid_mm.py
```

## Available Functions
- `market_buy(symbol, usd_size, account)`
- `market_sell(symbol, usd_size, account)`
- `limit_order(symbol, is_buy, size, price, reduce_only, account)`
- `get_position(symbol, account)`
- `pnl_close(symbol, target, max_loss, account)`
- `cancel_all_orders(account)`
- `kill_switch(symbol, account)`
- `get_balance(account)`
- `get_account_value(account)`