# Hyperliquid Volume Agent - AI Swarm Edition

**Built by Moon Dev**

An autonomous AI-powered agent that monitors Hyperliquid's top 15 highest-volume altcoins every 4 hours and uses a multi-model AI swarm to identify the best trading opportunities before they blow up on Crypto Twitter.

---

## What It Does

The Volume Agent continuously:
1. Fetches top 15 highest-volume altcoins from Hyperliquid (excludes BTC/ETH/SOL)
2. Tracks 4-hour volume changes, price movements, and rank shifts
3. Analyzes market data with 5+ AI models running in parallel (via SwarmAgent)
4. Provides individual AI recommendations + consensus pick
5. Logs all data and analysis to CSV/JSONL files

---

## File Location

- **Agent**: `src/agents/volume_agent.py`
- **Data Directory**: `src/data/volume_agent/`
  - `volume_history.csv` - All volume snapshots
  - `agent_analysis.jsonl` - AI swarm analysis logs

---

## Quick Start

```bash
# Make sure you're in the right environment
conda activate tflow

# Single run (test mode)
python src/agents/volume_agent.py --once

# Continuous mode (checks every 4 hours)
python src/agents/volume_agent.py

# Run in background (24/7)
nohup python src/agents/volume_agent.py > volume_agent.log 2>&1 &
```

---

## Configuration

All settings are at the top of `volume_agent.py`:

```python
# Trade filtering
EXCLUDED_TOKENS = ['BTC', 'ETH', 'SOL']  # Skip majors
TOP_N = 15  # Top N altcoins to track

# Check interval
CHECK_INTERVAL = 4 * 60 * 60  # 4 hours

# Data paths (auto-configured to project structure)
DATA_DIR = "src/data/volume_agent"
```

---

## Features

### Data Collection
- Real-time Hyperliquid API integration
- Top 15 altcoins by 24h volume (majors excluded)
- 4-hour volume change tracking
- Price change monitoring (24h)
- Rank movement detection
- Funding rate analysis
- Open interest tracking

### AI Swarm Analysis
- 5+ AI models query in parallel (via SwarmAgent)
- Individual reasoning from each model
- Consensus recommendation generation
- Response time tracking
- Success/failure handling

### Terminal Output
- Beautiful color-coded data tables
- 170-character wide display for maximum data density
- Auto-detected signals (NEW, VOL+50%, PUMP+30%, etc.)
- Market snapshot summaries
- Full AI recommendation display with reasoning
- Clean data table for human analysis (after AI results)
- Clean, scrollable format for all-day monitoring

### Data Persistence
- CSV logging of all volume snapshots (`volume_history.csv`)
- JSONL logging of AI analysis (`agent_analysis.jsonl`)
- Timestamped entries for historical analysis

---

## Terminal Output Example

### Output Flow
1. **Top 15 Altcoins Table** (with signals and colors)
2. **Market Snapshot** (summary of key signals)
3. **AI Swarm Analysis** (consensus + individual recommendations)
4. **Data Table** (clean tabular view for human analysis)

### Top 15 Altcoins Table
Shows all 15 tokens with:
- Rank
- Symbol
- Price
- 24H Volume
- 4H Volume Change (GREEN = up, RED = down, YELLOW = new)
- 24H Price Change (GREEN = up, RED = down)
- Rank Movement (arrows showing up/down/stable)
- Funding Rate (YELLOW = high, MAGENTA = negative)
- Open Interest
- Signals (auto-detected patterns)

### Market Snapshot
Quick summary showing:
- New top-15 entries
- Big 24H movers (>20%)
- Volume accelerators (>50%)
- Rank climbers

### AI Swarm Analysis
- **CONSENSUS RECOMMENDATION** (what all AIs agree on)
- **INDIVIDUAL RECOMMENDATIONS** (all 5+ AIs with full reasoning)

### Data Table (After AI Analysis)
Clean tabular view of all 15 tokens showing:
- Rank, Symbol, Price
- 24H Volume, 4H Volume Change, 24H Volume Change
- 24H Price Change
- Funding Rate, Open Interest

**Purpose**: Compare AI recommendations with raw data to find your own edge!

**Note**: 24H VOL Δ shows volume change over 24 hours (requires 6+ checks / 24h of history). Shows "N/A" for first day.

---

## Signals Explained

- **NEW** - New top-15 entry
- **VOL+50%** - Volume spiked >50% in 4h
- **VOL+20%** - Volume increased >20% in 4h
- **CLIMB+3** - Rank climbed 3+ positions
- **PUMP+30%** - Price pumped >30% in 24h
- **PUMP+15%** - Price pumped >15% in 24h

---

## Data Files

### volume_history.csv
All volume snapshots with columns:
- `timestamp`, `datetime`
- `rank`, `symbol`
- `volume_24h`, `price`
- `change_24h_pct`, `funding_rate_pct`, `open_interest`

### agent_analysis.jsonl
AI swarm analysis logs with:
- `timestamp`, `datetime`
- `changes` - Array of market changes
- `swarm_result` - Full swarm analysis with:
  - `consensus_summary` - AI consensus
  - `model_mapping` - Which AI corresponds to which provider
  - `responses` - Individual AI responses
  - `metadata` - Timing and success stats

---

## How It Works

### 1. Data Fetching
- `get_all_tokens_volume()` - Hits Hyperliquid API
- `get_top_altcoins()` - Filters to top 15 altcoins
- Uses Hyperliquid's `metaAndAssetCtxs` endpoint

### 2. Change Calculation
- `load_previous_snapshot()` - Loads last 4h snapshot from CSV
- `calculate_changes()` - Compares current vs previous
- Calculates:
  - 4-hour volume change percentage
  - Rank movement (up/down/new/stable)
  - Identifies new top-15 entries

### 3. AI Swarm Analysis
- `SwarmAgent()` - Initializes 5+ AI models
- `swarm.query(prompt)` - Parallel queries with ThreadPoolExecutor
- Process:
  1. Creates detailed prompt with all 15 tokens + changes
  2. Queries 5+ models in parallel
  3. Collects individual responses
  4. Generates consensus summary
  5. Returns structured result with timing data

### 4. Data Table Display
- `display_data_table(changes)` - Shows clean tabular view
- Displays after AI analysis for human comparison
- Allows non-AI analysis and edge-finding
- All 15 tokens with key metrics in one view

### 5. Data Logging
- `log_volume_snapshot(tokens)` - Appends to CSV
- `log_agent_analysis(changes, swarm_result)` - Appends to JSONL

---

## Key Signals to Watch For

### Volume Signals
- **VOL+50%**: Massive volume spike - something BIG is happening
- **VOL+20%**: Strong volume growth - increasing interest
- Negative 4H volume: Cooling off, profit taking

### Price Signals
- **PUMP+30%**: Major price movement - verify volume confirmation
- **PUMP+15%**: Solid momentum - check if sustainable
- Price + Volume aligned: High conviction setup

### Rank Signals
- **CLIMB+3**: Token moving up ranks - gaining market share
- **NEW**: Fresh entry to top 15 - catch early breakout
- Stable rank: Established volume leader

### Funding Rate
- **YELLOW (>0.01%)**: Longs paying shorts - overheating warning
- **MAGENTA (<-0.01%)**: Shorts paying longs - potential squeeze
- **WHITE (normal)**: Balanced market

### Liquidity (Open Interest)
- **>$100M**: High liquidity - safe for larger positions
- **$10M-$100M**: Medium liquidity - moderate position sizes
- **<$10M**: Low liquidity - small positions only, risk of slippage

---

## Trading Strategy Ideas

### Moon Dev's Approach: "Data Dog Mode"
1. Watch all day - Terminal always open
2. AI swarm validation - If 3+ AIs agree, high conviction
3. Volume + Price confirmation - Both must align
4. Check every 4 hours - Catch moves early
5. Compare consensus changes - Track AI sentiment shifts

### Signal Combinations
1. **Strong Buy**: NEW + VOL+50% + PUMP+30% + AI consensus
2. **Momentum Play**: CLIMB+3 + VOL+20% + High OI
3. **Early Breakout**: NEW + Positive 4H volume + 3+ AI picks
4. **Contrarian**: MAGENTA funding + Stable volume + High OI

---

## Dependencies

### Core Libraries
```bash
pip install requests termcolor
```

### Moon Dev Framework
- `src/agents/swarm_agent.py` - Multi-model AI swarm
- `src/models/model_factory.py` - Unified model interface

### AI Model Providers (configured in `.env`)
```bash
DEEPSEEK_KEY=sk-your-deepseek-key
GROK_API_KEY=xai-your-grok-key
OPENROUTER_API_KEY=sk-or-your-openrouter-key
ANTHROPIC_KEY=sk-ant-your-claude-key
# Add more as needed by SwarmAgent
```

---

## API Costs

Running continuously with swarm mode:
- **Per analysis**: ~5-6 models × 15 markets × 100 tokens = ~$0.10-0.50
- **Per day**: 6 runs × $0.30 = ~$1.80/day
- **Per month**: ~$54/month

Cost reduction:
- Use cheaper models (DeepSeek, Groq are nearly free)
- Reduce check frequency (e.g., 6 hours instead of 4)
- Disable expensive models in SwarmAgent config

---

## Troubleshooting

**Q: Module 'SwarmAgent' not found**
- Ensure you're running from the project root
- Check that `src/agents/swarm_agent.py` exists

**Q: API key errors**
- Verify `.env` file exists in project root
- Check all required keys are present
- Ensure keys are valid and have credit

**Q: Connection refused to Hyperliquid**
- Check internet connection
- Hyperliquid API is public and requires no authentication
- Verify API endpoint: `https://api.hyperliquid.xyz/info`

**Q: Terminal output too wide**
- Maximize terminal window
- Or reduce width constant in code (currently 170 chars)

---

## Integration with Main Orchestrator

To add to `main.py`:

```python
from src.agents.volume_agent import run_check as volume_agent_check

# In main loop:
if should_run_agent('volume_agent'):
    volume_agent_check()
```

Or run standalone for 24/7 monitoring without orchestrator.

---

## Future Enhancements

Planned features:
- Discord/Telegram notifications for high-conviction signals
- Historical backtesting of AI consensus accuracy
- Additional exchanges (dYdX, GMX, etc.)
- Correlation analysis between tokens
- Custom signal threshold configuration
- Web dashboard for remote monitoring
- Position size calculator based on liquidity
- Stop-loss/take-profit suggestions from AI

---

## Disclaimers

- **Not Financial Advice**: This is a research tool, not trading advice
- **Use At Your Own Risk**: Trading crypto is highly risky
- **No Guarantees**: Past performance ≠ future results
- **API Costs**: Running 5+ AI models per check costs money
- **Rate Limits**: Respect API rate limits for all services

---

## Support

Built by Moon Dev for the Data Dogs

**Location**: `/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/agents/volume_agent.py`

**Data**: `/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/volume_agent/`

---

Built with Moon Dev 🌙

*"Catch the pumps BEFORE Crypto Twitter"*
