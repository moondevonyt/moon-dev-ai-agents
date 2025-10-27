# Polymarket Prediction Agent

**Built by Moon Dev** - Real-time prediction market analysis using AI

## What It Does

Monitors Polymarket in real-time via WebSocket, collects large trades, and uses AI to predict market outcomes.

- **Watches** live trades over $100 (configurable)
- **Filters** out crypto, sports, and near-resolution markets
- **Analyzes** markets with AI (swarm mode = 6 models, or single model)
- **Saves** all data to CSV for historical tracking

## Quick Start

```bash
# Make sure you're in the right environment
conda activate tflow

# Run the agent
python src/agents/polymarket_agent.py
```

## Configuration

Edit these settings at the top of `polymarket_agent.py`:

```python
MIN_TRADE_SIZE_USD = 100              # Only track trades over this amount
LOOKBACK_HOURS = 24                    # Historical data on startup
NEW_MARKETS_FOR_ANALYSIS = 25          # Trigger AI after this many new markets
ANALYSIS_CHECK_INTERVAL_SECONDS = 300  # Check every 5 minutes
USE_SWARM_MODE = True                  # Use 6 AI models (or single model)
```

**Category Filters:**
- `IGNORE_CRYPTO_KEYWORDS` - Skip BTC, ETH, SOL markets
- `IGNORE_SPORTS_KEYWORDS` - Skip NBA, NFL, UFC markets

## How It Works

**3 Parallel Threads:**

1. **WebSocket Thread** - Collects trades in real-time, saves to CSV silently
2. **Status Thread** - Prints stats every 30 seconds (trades, filters, markets)
3. **Analysis Thread** - Checks every 5 minutes for new markets, runs AI when threshold hit

**AI Analysis:**
- First run: Analyzes whatever markets exist
- Subsequent runs: Waits for 25 NEW markets before analyzing again
- Analyzes the 25 most recent markets each time
- Swarm mode: Claude, OpenAI, Groq, Gemini, DeepSeek, XAI (all run in parallel)

## Output Files

```
src/data/polymarket/
├── markets.csv      - All markets with trades over $100
└── predictions.csv  - AI predictions for each analysis run
```

**markets.csv columns:**
- `timestamp`, `market_id`, `event_slug`, `title`
- `outcome`, `price`, `size_usd`, `first_seen`

**predictions.csv columns:**
- `analysis_timestamp`, `analysis_run_id`, `market_title`, `market_slug`
- Individual model predictions: `claude_prediction`, `openai_prediction`, etc.
- `consensus_prediction`, `num_models_responded`

## AI Modes

**Swarm Mode** (default):
```python
USE_SWARM_MODE = True
```
Uses 6 models in parallel. Each gets 90 seconds to respond. Partial results saved if timeout.

**Single Model Mode:**
```python
USE_SWARM_MODE = False
AI_MODEL_PROVIDER = "xai"
AI_MODEL_NAME = "grok-2-fast-reasoning"
```
Faster, cheaper, single perspective.

## Features

- Real-time WebSocket connection with auto-reconnect
- Thread-safe CSV operations
- Historical data fetch on startup (24h lookback)
- Smart filtering (ignores crypto/sports/near-resolution)
- Status display shows collection stats every 30s
- AI analysis only runs when enough new markets collected
- Tracks which markets have been analyzed (no duplicate analysis)

## Sample Output

```
🌙 Polymarket Prediction Market Agent
================================================================================
✅ Loaded 1,247 existing markets from CSV
✅ Loaded 18 existing predictions from CSV
📡 Fetching historical trades (last 24h)...
✅ Fetched 856 historical trades
💰 Found 342 trades over $100 (after filters)
🔌 WebSocket connected!
✅ Subscription sent! Waiting for trades...

📊 Status @ 14:23:45
================================================================================
   WebSocket Connected: ✅ YES
   Total trades received: 1,234
   Ignored crypto/bitcoin: 456
   Ignored sports: 789
   Filtered trades (>=$100): 89
   Total markets in database: 1,336
   New unanalyzed: 25
   ✅ Ready for analysis!

🤖 AI ANALYSIS - Analyzing 25 markets
🌊 Getting predictions from AI swarm...

[Individual model predictions...]

🎯 CONSENSUS DECISION
Based on 6 AI models
================================================================================
Market 1: YES - Strong fundamentals
Market 2: NO_TRADE - Too uncertain
...
```

## API Requirements

Add to your `.env`:
```bash
ANTHROPIC_KEY=your_key_here   # For Claude
OPENAI_KEY=your_key_here      # For GPT
GROQ_API_KEY=your_key_here    # For Groq
GEMINI_KEY=your_key_here      # For Gemini
DEEPSEEK_KEY=your_key_here    # For DeepSeek
XAI_API_KEY=your_key_here     # For Grok
```

Only need XAI_API_KEY if using single model mode with XAI.

## Notes

- **NO ACTUAL TRADING** - This is analysis only
- WebSocket stays connected 24/7 (auto-reconnect on disconnect)
- CSV files grow over time (markets.csv can get large)
- First analysis runs immediately if markets exist
- Each analysis run gets unique ID (timestamp)
- Predictions are saved with full model breakdown

---

**Built by Moon Dev** | Part of the moon-dev-ai-agents-for-trading system
