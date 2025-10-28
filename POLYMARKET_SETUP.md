# Polymarket Agent Setup Guide

Welcome! This guide will help you set up and run the Polymarket prediction market agents.

## What's Available

Your codebase now includes:

1. **Polymarket Agent** (`src/agents/polymarket_agent.py`) - Real-time market monitoring with AI analysis
2. **Market Data** - CSV databases for tracking markets and predictions
3. **AI Integration** - Swarm mode (6 models) or single model analysis

## What It Does

- Monitors Polymarket trades in real-time via WebSocket
- Filters interesting markets (ignores crypto/sports)
- Uses AI to predict market outcomes
- Saves all data to CSV for historical analysis
- **NO ACTUAL TRADING** - Analysis only!

## Quick Setup

### 1. Install Dependencies ✅

```bash
# The websocket-client has been installed
pip install websocket-client

# Verify installation
python -c "import websocket; print('✅ Ready!')"
```

### 2. Configure API Keys

You need to create a `.env` file with your API keys. Copy from `.env_example`:

```bash
cp .env_example .env
```

Then edit `.env` and add your API keys:

**Required for Swarm Mode (default):**
```bash
ANTHROPIC_KEY=your_claude_key_here      # Claude 4.5
OPENAI_KEY=your_openai_key_here         # GPT
GROQ_API_KEY=your_groq_api_key_here     # Groq
GEMINI_KEY=your_google_api_key_here     # Gemini
DEEPSEEK_KEY=your_deepseek_key_here     # DeepSeek
GROK_API_KEY=your_xai_key_here          # Grok (XAI)
```

**For Single Model Mode (optional):**
Just need one of the above keys and change settings in the agent.

### 3. Run the Agent

```bash
# Make sure you're in the right environment
conda activate tflow

# Run the Polymarket agent
python src/agents/polymarket_agent.py
```

## Configuration Options

Edit these settings at the top of `src/agents/polymarket_agent.py`:

```python
# Trade filtering
MIN_TRADE_SIZE_USD = 100              # Only track trades over this amount
LOOKBACK_HOURS = 24                    # Historical data on startup
NEW_MARKETS_FOR_ANALYSIS = 25          # Trigger AI after this many new markets
ANALYSIS_CHECK_INTERVAL_SECONDS = 300  # Check every 5 minutes

# AI Configuration
USE_SWARM_MODE = True                  # Use 6 AI models (or single model)
AI_MODEL_PROVIDER = "xai"              # Model to use if not swarm
AI_MODEL_NAME = "grok-2-fast-reasoning"

# Category Filters
IGNORE_CRYPTO_KEYWORDS = ['bitcoin', 'btc', 'ethereum', ...]
IGNORE_SPORTS_KEYWORDS = ['nba', 'nfl', 'ufc', ...]
```

## How It Works

The agent runs 3 parallel threads:

1. **WebSocket Thread** - Collects trades in real-time, saves to CSV
2. **Status Thread** - Prints stats every 30 seconds
3. **Analysis Thread** - Runs AI analysis when enough new markets collected

## Output Files

All data is saved to `src/data/polymarket/`:

- `markets.csv` - All markets with trades over $100
- `predictions.csv` - AI predictions for each analysis run

## What You'll See

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
   Filtered trades (>=$100): 89
   Total markets in database: 1,336
   New unanalyzed: 25
   ✅ Ready for analysis!

🤖 AI ANALYSIS - Analyzing 25 markets
🌊 Getting predictions from AI swarm...
```

## Advanced Features

### Swarm Mode (Default)
Uses 6 AI models in parallel:
- Claude 4.5 Sonnet
- GPT-4o
- Groq Mixtral
- Google Gemini
- DeepSeek
- Grok (XAI)

Each model gets 90 seconds to respond. Consensus is calculated from all responses.

### Single Model Mode
Faster and cheaper - uses just one model:

```python
USE_SWARM_MODE = False
AI_MODEL_PROVIDER = "xai"
AI_MODEL_NAME = "grok-2-fast-reasoning"
```

## Roadmap

According to `docs/polymarket_agents.md`, there are plans for:

1. ✅ **Data Collection System** - COMPLETE (11,862 markets in database)
2. 🔜 **Sweep Quality Scorer** - Score sweep quality, follow best traders
3. 📝 **Event Catalyst Agent** - News-based trading opportunities
4. 📝 **Resolution Probability Recalibrator** - AI-powered probability estimation

## Troubleshooting

**"No module named 'websocket'"**
```bash
pip install websocket-client
```

**"API key not found"**
- Make sure you created `.env` file
- Check that your API keys are set correctly
- Verify the key names match `.env_example`

**WebSocket disconnects**
- This is normal - agent auto-reconnects
- Check your internet connection
- Polymarket API might be rate-limiting

**No markets showing up**
- Adjust `MIN_TRADE_SIZE_USD` lower (try 50 or 25)
- Check if filters are too restrictive
- Wait a few minutes for trades to come in

## Notes

- This agent does **NO ACTUAL TRADING** - it's analysis only
- WebSocket runs 24/7 with auto-reconnect
- CSV files grow over time (markets.csv can get large)
- First analysis runs immediately if markets exist
- Each analysis run gets a unique timestamp ID

## Resources

- **Documentation:** `docs/polymarket_agent.md`
- **Roadmap:** `docs/polymarket_agents.md`
- **Agent Code:** `src/agents/polymarket_agent.py`
- **Data Folder:** `src/data/polymarket/`

---

Built by Moon Dev | Part of the moon-dev-ai-agents-for-trading system 🌙
