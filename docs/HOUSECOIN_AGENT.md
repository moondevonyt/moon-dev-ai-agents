# 🏠 Housecoin DCA Agent

AI-powered Dollar Cost Averaging agent for Housecoin with Grok-4 confirmation layer.

## ⚠️ WARNING ⚠️
**NOT FINANCIAL ADVICE** - This is an experimental DCA bot. Housecoin may go to zero. Trade at your own risk. This agent will buy and eventually sell. Past performance does not guarantee future results

## The Thesis: 1 House = 1 Housecoin 🏠

Key beliefs driving this strategy:
- Every real estate agent will eventually need Housecoin
- Anyone with a house needs to hedge with Housecoin
- Real estate bubble makes homes unaffordable, but Housecoin IS affordable
- 2.3 billion homes vs 1 billion Housecoin = supply shock
- Real estate: $300+ trillion market opportunity
- Eventually all real estate → blockchain, Housecoin best positioned

## How It Works

### Strategy Logic
- **Below 20-day SMA**: Aggressive accumulation every 15 minutes
- **Above 20-day SMA**: Buy only near daily lows
- **Exit Target**: $1.68 (sells everything)
- **Trading Hours**: 6 AM - 8 PM ET only

### AI Decision Layer
- Uses xAI's Grok-4 fast model for trade confirmation
- Analyzes 55 x 5-minute bars before each trade
- AI must approve every buy signal
- Provides reasoning for each decision

## Quick Start

```bash
# Set in config.py
EXCHANGE = 'solana'  # Housecoin is on Solana

# Run the agent
python src/agents/housecoin_agent.py
```

## Configuration

Edit these values in `housecoin_agent.py`:

```python
# Exit criteria
EXIT_PRICE = 1.68  # Sell everything at $1.68

# Below SMA settings
BELOW_SMA_BUY_MINUTES = 15  # Buy frequency
BELOW_SMA_BUY_AMOUNT = 2    # $2 per buy
BELOW_SMA_DAILY_CAP = 1500  # Max $1500/day

# Above SMA settings
ABOVE_SMA_BUY_AMOUNT = 1    # $1 per buy
ABOVE_SMA_DAILY_CAP = 100   # Max $100/day
DAILY_LOW_THRESHOLD = 0.01  # Within 1% of daily low
```

## Features

### Smart DCA Logic
- Tracks 20-day and 5-minute SMAs
- Adjusts strategy based on trend
- Respects daily spending caps
- Trading hours enforcement

### AI Integration
- Real-time market analysis
- RSI and volume indicators
- Pattern recognition
- Risk assessment per trade

### Position Management
- Automatic state tracking
- Transaction history
- Daily spending limits
- Exit price monitoring

## State Tracking

The agent maintains state in `housecoin_agent_state.json`:
- Daily spending totals
- Buy history with timestamps
- AI decision log
- Total invested amount

## Risk Controls

1. **Daily Caps**: Limits spending per day
2. **Trading Hours**: Only trades during specified hours
3. **AI Confirmation**: Second layer of validation
4. **Exit Strategy**: Clear profit target at $1.68
5. **Slippage Protection**: 5% default slippage tolerance

## Sample Output

```
🏠 Housecoin DCA Agent with AI Decisions 🏠
============================================================
⚠️ NOT FINANCIAL ADVICE - This may go to zero!
Thesis: 1 House = 1 Housecoin
Exit Target: $1.68

[09:43:02] $0.00489151
20D-SMA: BELOW -32.3% | 5M-SMA: BELOW
📊 Strategy: ACCUMULATION MODE

🎯 Strategy triggered! Checking with AI...
🤖 Consulting AI for trade confirmation...
✅ AI APPROVED: BUY

🚀 Buying ~408 Housecoin for $2
✅ Buy successful! TX: 35uaUgYBy2F58PP4...

🏠 HOUSECOIN THESIS:
1 House = 1 Housecoin
```

## Dependencies

- xAI Grok API key (`GROK_API_KEY`)
- Solana private key (`SOLANA_PRIVATE_KEY`)
- BirdEye API key (`BIRDEYE_API_KEY`)
- RPC endpoint (`RPC_ENDPOINT`)

## Important Notes

- Housecoin contract: `DitHyRMQiSDhn5cnKMJV2CDDt6sVct96YrECiM49pump`
- Only runs on Solana (not HyperLiquid)
- Requires USDC for purchases
- All transactions on-chain and verifiable

---

🌙 *Built with love by Moon Dev - Remember: 1 House = 1 Housecoin!*