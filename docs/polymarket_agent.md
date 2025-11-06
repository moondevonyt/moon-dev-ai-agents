# Polymarket Prediction Agent

**Built by Moon Dev** - Real-time prediction market analysis using AI swarm consensus

## What It Does

Monitors Polymarket in real-time via WebSocket, collects large trades, uses AI swarm to predict market outcomes, and identifies the TOP 5 consensus picks.

- **Watches** live trades over $100 (configurable)
- **Filters** out crypto, sports, and near-resolution markets
- **Analyzes** markets with 6 AI models in parallel (swarm mode)
- **Identifies** top 5 strongest consensus picks using Claude 4.5
- **Displays** consensus picks with blue background for easy spotting
- **Saves** all data to 3 CSV files for historical tracking and analysis

## Quick Start

```bash
# Make sure you're in the right environment
conda activate tflow

# Run the agent
python src/agents/polymarket_agent.py
```

## Configuration

All settings are at the top of `polymarket_agent.py` for easy customization:

### Basic Settings
```python
MIN_TRADE_SIZE_USD = 100              # Only track trades over this amount ($1000 for whales)
LOOKBACK_HOURS = 24                    # Historical data on startup
NEW_MARKETS_FOR_ANALYSIS = 25          # Trigger AI after this many new markets
ANALYSIS_CHECK_INTERVAL_SECONDS = 300  # Check every 5 minutes
MARKETS_TO_ANALYZE = 25                # Number of recent markets to send to AI
USE_SWARM_MODE = True                  # Use 6 AI models (or single model)
TOP_MARKETS_COUNT = 5                  # How many top consensus picks to show
```

### AI Prompts (🌙 Customize for Your Own Edge!)
```python
MARKET_ANALYSIS_SYSTEM_PROMPT = """..."""      # Prompt for individual AI models
CONSENSUS_AI_PROMPT_TEMPLATE = """..."""       # Prompt for consensus AI
```

**These prompts are your edge!** Modify them to:
- Change analysis criteria (technical, fundamental, sentiment)
- Add market-specific knowledge
- Adjust risk tolerance
- Focus on specific market types

### Category Filters
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
├── markets.csv          - All markets with trades over $100
├── predictions.csv      - All 25 market predictions per analysis run
└── consensus_picks.csv  - 🌙 ONLY the top 5 consensus picks (append-only)
```

### markets.csv (All Discovered Markets)
Tracks every unique market from trades over your threshold.

**Columns:** `timestamp`, `market_id`, `event_slug`, `title`, `outcome`, `price`, `size_usd`, `first_seen`

### predictions.csv (Detailed Analysis Results)
One row per market analyzed (25 markets per run).

**Columns:**
- `analysis_timestamp`, `analysis_run_id` - When and which run
- `market_title`, `market_slug`, `market_link` - Market details
- Individual predictions: `claude_prediction`, `openai_prediction`, `groq_prediction`, `gemini_prediction`, `deepseek_prediction`, `xai_prediction`
- `consensus_prediction` - Overall consensus (e.g., "YES (83%)")
- `num_models_responded` - How many AIs successfully responded

### consensus_picks.csv (🌙 Top Consensus Picks - Your Trading List!)
**APPEND-ONLY** - Builds history throughout the day. Contains ONLY the top 5 strongest consensus picks from each analysis run.

**Columns:**
- `timestamp`, `run_id` - When this pick was made
- `rank` - 1-5 (position in top 5)
- `market_number` - Market number from analysis
- `market_title` - Full market name
- `side` - YES, NO, or NO_TRADE
- `consensus` - "5 out of 6 models agreed"
- `consensus_count` - 5 (how many agreed)
- `total_models` - 6 (total models that responded)
- `link` - Direct Polymarket URL
- `reasoning` - Why this is a strong pick

**Perfect for:**
- Finding markets with repeated strong consensus over time
- Analyzing which markets keep appearing in top picks
- Building automated trading signals from AI agreement
- Reviewing the best opportunities throughout the day

**Example:** If running every 5 minutes for 24 hours = 288 runs × 5 picks = 1,440 consensus picks tracked!

## AI Analysis Flow

### Step 1: Swarm Analysis (6 Models in Parallel)
```python
USE_SWARM_MODE = True  # Default
```

**Models Used:**
- Claude (Anthropic)
- OpenAI (GPT)
- Groq (Qwen)
- Gemini (Google)
- DeepSeek
- XAI (Grok)
- OpenRouter (Gemini/GLM as backup)

Each model gets **120 seconds** to respond. If one times out, the others continue - partial results are always used!

**Each AI provides:** YES, NO, or NO_TRADE decision for each of the 25 markets

### Step 2: Consensus AI (Claude 4.5 Sonnet)
After all individual AIs respond, a **consensus AI** analyzes all responses to identify the **TOP 5 markets with strongest agreement**.

**Consensus AI evaluates:**
- Which markets have the most AI models agreeing
- Ignores split opinions
- Focuses on clear, strong agreement (e.g., 5 out of 6 agree on YES)
- Ranks by consensus strength

**Output:** TOP 5 CONSENSUS PICKS displayed with **BLUE BACKGROUND** 🏆

### Single Model Mode (Alternative)
```python
USE_SWARM_MODE = False
AI_MODEL_PROVIDER = "xai"
AI_MODEL_NAME = "grok-2-fast-reasoning"
```
Faster, cheaper, single perspective - no consensus analysis.

## Features

### Core Features
- **Real-time WebSocket** with auto-reconnect and ping/pong keepalive
- **Thread-safe CSV** operations for concurrent access
- **Historical data fetch** on startup (24h lookback)
- **Smart filtering** - ignores crypto/sports/near-resolution markets
- **Status display** every 30s (trades, filters, markets)
- **Intelligent analysis** - only runs when enough new markets collected
- **No duplicate analysis** - tracks which markets already analyzed

### AI Swarm Features (🌙 New!)
- **Parallel execution** - 6 AI models analyze simultaneously
- **Graceful timeout handling** - if 1 AI times out, continue with 5
- **120-second timeout** per model (increased from 90s for reliability)
- **Partial results** - always uses whatever AIs successfully responded
- **Individual predictions** displayed with timing for each model
- **Consensus AI** - Claude 4.5 analyzes all responses to pick top 5
- **Blue background display** - makes top picks impossible to miss
- **Invalid market filtering** - skips AI hallucinations (market numbers out of range)

### CSV History Features (🌙 New!)
- **Append-only consensus CSV** - builds trading signal history over time
- **Full market predictions** - saves all 25 markets × all 6 models
- **Consensus tracking** - see which markets get repeated strong agreement
- **Direct links** - every market has clickable Polymarket URL
- **Structured data** - easy to analyze in Excel/Python/R

### Customization Features (🌙 New!)
- **Editable prompts** - customize AI analysis at top of file
- **Build your edge** - change analysis criteria, risk tolerance, market focus
- **Configurable consensus** - change from 5 picks to any number
- **Easy settings** - all config variables at top of file

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
🌊 Getting predictions from AI swarm (120s timeout per model)...

================================================================================
✅ XAI (23.4s)
================================================================================
MARKET 1: NO
Reasoning: Regulatory hurdles make December launch impossible...
[continues for all 25 markets]

[5 more AI models display their predictions...]

✅ Received 6/6 successful responses from swarm!

🎯 CONSENSUS ANALYSIS
Based on 6 AI models
================================================================================

Market 1: NO (66% consensus)
  📌 Will Tesla launch unsupervised FSD by December 31?
  🔗 https://polymarket.com/event/tesla-fsd-december-2025
  Votes: YES: 0 | NO: 4 | NO_TRADE: 2

Market 2: YES (83% consensus)
  📌 Hezbollah strike on Israel by December 31?
  🔗 https://polymarket.com/event/hezbollah-israel-strike
  Votes: YES: 5 | NO: 1 | NO_TRADE: 0

[23 more markets...]

================================================================================
🧠 Running Consensus AI to identify top 5 picks...
================================================================================

⏳ Analyzing all responses for strongest consensus...

================================================================================
🏆 TOP 5 CONSENSUS PICKS - MOON DEV AI RECOMMENDATION
================================================================================

1. Market 24: Tesla launches unsupervised full self driving (FSD) by December 31?
   Side: NO
   Consensus: 5 out of 5 models agreed
   Link: https://polymarket.com/event/tesla-fsd-december-2025
   Reasoning: All models unanimously agree regulatory hurdles make this impossible

2. Market 15: Hezbollah strike on Israel by December 31?
   Side: YES
   Consensus: 5 out of 5 models agreed
   Link: https://polymarket.com/event/hezbollah-israel-strike
   Reasoning: Perfect consensus that ongoing tensions make strikes highly probable

3. Market 6: BNB all time high by December 31?
   Side: NO
   Consensus: 4 out of 5 models agreed
   Link: https://polymarket.com/event/bnb-ath-2025
   Reasoning: Strong majority consensus BNB lacks catalysts for 40% gain

4. Market 11: Fed raises rates in December?
   Side: NO
   Consensus: 5 out of 5 models agreed
   Link: https://polymarket.com/event/fed-december-rates
   Reasoning: Unanimous agreement Fed will hold rates given inflation data

5. Market 19: Trump pardons Hunter Biden?
   Side: YES
   Consensus: 5 out of 6 models agreed
   Link: https://polymarket.com/event/trump-pardons-hunter
   Reasoning: Strong consensus based on Trump's pardon patterns

================================================================================

💾 Saving top consensus picks to CSV...
✅ Saved 5 consensus picks to CSV
📁 Consensus picks CSV: /Users/md/.../consensus_picks.csv
📊 Total consensus picks in history: 143

💾 Saving predictions to database...
💾 Saved 25 predictions to CSV
✅ Saved 25 market predictions (run 20251106_102204)

📁 Predictions saved to: /Users/md/.../predictions.csv
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

## Advanced Usage

### Running 24/7 for Maximum Insights
Let the agent run continuously to build a powerful dataset:

```bash
# Run in background (on Linux/Mac)
nohup python src/agents/polymarket_agent.py > polymarket.log 2>&1 &

# Or use screen/tmux for persistent sessions
screen -S polymarket
python src/agents/polymarket_agent.py
# Ctrl+A, D to detach
```

**What you'll get after 24 hours:**
- ~288 analysis runs (every 5 minutes)
- ~1,440 consensus picks tracked
- Historical view of market sentiment shifts
- Patterns of repeated high-consensus markets

### Building Trading Signals

Use `consensus_picks.csv` to find the best opportunities:

```python
import pandas as pd

# Load consensus picks
df = pd.read_csv('src/data/polymarket/consensus_picks.csv')

# Find markets that appear in top 5 multiple times
repeated_picks = df.groupby('market_title').size()
hot_markets = repeated_picks[repeated_picks >= 3]  # Appeared 3+ times

# Find unanimous picks (all models agreed)
unanimous = df[df['consensus_count'] == df['total_models']]

# Filter by side
strong_yes = df[(df['side'] == 'YES') & (df['consensus_count'] >= 5)]
```

### Customizing Analysis

**Example: Focus on political markets**
```python
# Edit MARKET_ANALYSIS_SYSTEM_PROMPT
MARKET_ANALYSIS_SYSTEM_PROMPT = """You are a political prediction expert.
Focus heavily on:
- Policy implications
- Historical precedents
- Political incentives
- Timing around elections

For each market..."""
```

**Example: More conservative (only trade 6/6 consensus)**
```python
TOP_MARKETS_COUNT = 3  # Only show top 3

# Edit CONSENSUS_AI_PROMPT_TEMPLATE
# Add: "Only include markets where ALL models agree..."
```

## Troubleshooting

**Q: Some AI models timing out?**
- Increase timeout: Edit `MODEL_TIMEOUT = 120` in `swarm_agent.py` to 180
- Some models (Gemini) can be slow on complex prompts
- Agent continues with partial results - this is expected behavior

**Q: Too many markets being analyzed?**
- Increase `NEW_MARKETS_FOR_ANALYSIS = 50` to analyze less frequently
- Increase `MIN_TRADE_SIZE_USD = 1000` to only track large trades

**Q: Not enough markets?**
- Decrease `MIN_TRADE_SIZE_USD = 50` to track more markets
- Remove sports/crypto filters by commenting out keywords

**Q: Want to backtest my custom prompts?**
- Keep original `consensus_picks.csv` as ground truth
- Modify prompts, run on historical `markets.csv`
- Compare consensus picks to actual market resolutions

## Notes

- **NO ACTUAL TRADING** - This is analysis only (no money at risk)
- **WebSocket runs 24/7** with auto-reconnect on disconnect
- **CSV files grow over time** - markets.csv can get large (compress old data)
- **First analysis runs immediately** if markets exist in database
- **Each run gets unique ID** - timestamp format (YYYYMMDD_HHMMSS)
- **Predictions saved with full breakdown** - all individual AI responses
- **Consensus picks append-only** - never overwrites, builds history
- **Market links always included** - click straight to Polymarket

## API Cost Estimation

Running continuously with swarm mode:
- **Per analysis:** ~6 models × 25 markets × 100 tokens = ~$0.10
- **Per day:** 288 runs × $0.10 = ~$28.80/day
- **Cost reduction:** Use cheaper models (Groq, DeepSeek are nearly free)

---

**Built by Moon Dev** 🌙 | Part of the moon-dev-ai-agents-for-trading system

**Latest Update:** Added consensus AI, top 5 picks display, append-only CSV tracking, customizable prompts, and graceful partial response handling.
