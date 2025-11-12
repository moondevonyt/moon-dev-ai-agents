# Volume Agent - Hyperliquid Volume Tracker

**Built by Moon Dev** 🌙

An autonomous AI-powered agent that monitors Hyperliquid's top 15 highest-volume altcoins every 4 hours and uses a multi-model AI swarm to identify volume acceleration patterns BEFORE they blow up on Crypto Twitter.

---

## 🎯 What It Does

The Volume Agent is a **pure volume tracker** that:

1. **Fetches** top 15 highest-volume altcoins from Hyperliquid (excludes BTC/ETH/SOL)
2. **Tracks** 4-hour and 24-hour volume changes
3. **Detects** rank movements and new entries
4. **Analyzes** with 5+ AI models running in parallel (SwarmAgent)
5. **Provides** volume-only recommendations (NO price, funding, or OI data to AI)
6. **Displays** clean data table for human analysis
7. **Logs** all data to CSV/JSONL for historical tracking

**The Edge**: Catch volume spikes BEFORE Crypto Twitter notices them!

---

## 🚀 Quick Start

```bash
# Make sure you're in the right environment
conda activate tflow

# Test run (single check)
python src/agents/volume_agent.py --once

# Continuous mode (checks every 4 hours)
python src/agents/volume_agent.py

# Background mode (24/7 monitoring)
nohup python src/agents/volume_agent.py > volume_agent.log 2>&1 &
```

---

## 📁 File Locations

- **Agent**: `src/agents/volume_agent.py`
- **Data Directory**: `src/data/volume_agent/`
  - `volume_history.csv` - All volume snapshots (every 4 hours)
  - `agent_analysis.jsonl` - AI swarm analysis results

---

## ⚙️ Configuration

Edit constants at the top of `volume_agent.py`:

```python
# API
HYPERLIQUID_API = "https://api.hyperliquid.xyz/info"

# Data paths (auto-configured)
DATA_DIR = "src/data/volume_agent"

# Excluded tokens (skip majors)
EXCLUDED_TOKENS = ['BTC', 'ETH', 'SOL']

# Top N altcoins to track
TOP_N = 15

# Check interval (4 hours)
CHECK_INTERVAL = 4 * 60 * 60
```

---

## 📊 Terminal Output Flow

### 1. Top 15 Altcoins Table (Colorful)
Shows all 15 tokens with:
- Rank, Symbol, Price
- 24H Volume
- 4H Volume Change (GREEN = up, RED = down, YELLOW = new)
- 24H Price Change
- Rank Movement (arrows)
- Funding Rate, Open Interest
- **Auto-detected signals**: NEW, VOL+50%, VOL+20%, CLIMB+3, PUMP+30%, PUMP+15%

### 2. Market Snapshot
Quick summary showing:
- New top-15 entries
- Big 24H movers (>20%)
- Volume accelerators (>50%)
- Rank climbers (+3 or more)

### 3. AI Swarm Analysis
- **CONSENSUS RECOMMENDATION** (what all AIs agree on)
- **INDIVIDUAL RECOMMENDATIONS** (all 5+ AIs with full reasoning)
- Response times for each model
- Success/failure stats

### 4. Data Table (Clean View)
Raw data table showing:
- Rank, Symbol, Price
- 24H Volume
- **4H VOL Δ** (volume change over 4 hours)
- **24H VOL Δ** (volume change over 24 hours)
- 24H Price Change
- Funding Rate, Open Interest

**Purpose**: Compare AI picks with raw numbers to find your own edge!

---

## 🤖 AI Prompt Structure (VOLUME ONLY)

### What the AI Receives

The AI swarm gets **VOLUME DATA ONLY** - no price, no funding, no open interest:

```
You are a VOLUME TRACKER analyzing Hyperliquid volume patterns.

Your ONLY job is to identify volume acceleration and momentum.
DO NOT consider price, funding rates, or any other data.

1. STRK:
   - Current 24H Volume: $65.10M
   - 4H Volume Change: NEW ENTRY
   - 24H Volume Change: +15.5%
   - Rank Movement: NEW ENTRY

2. PUMP:
   - Current 24H Volume: $61.36M
   - 4H Volume Change: +12.4%
   - 24H Volume Change: -5.2%
   - Rank Movement: CLIMBED 3 spots
```

### AI Instructions

```
Based on VOLUME DATA ONLY, which token would you buy right now?

Consider ONLY:
- Volume acceleration (4H vs 24H trends)
- Absolute volume size (bigger = more liquidity/interest)
- Rank climbing patterns (gaining market share)
- New entries with strong volume
- Sustained volume growth vs flash spikes
```

### Why Volume Only?

**No bias from:**
- ❌ Price pumps without volume confirmation
- ❌ Funding rates showing overheating
- ❌ Open interest affecting risk assessment

**Pure signal:**
- ✅ Volume acceleration (NOW vs sustained)
- ✅ Rank movements (market share shifts)
- ✅ Absolute size (liquidity/interest)

---

## 📈 Key Metrics Explained

### 4H VOL Δ (4-Hour Volume Change)
- Shows volume change over the last 4 hours (since last check)
- **NEW** = First time in top 15
- Positive % = Volume increasing
- Negative % = Volume decreasing

### 24H VOL Δ (24-Hour Volume Change)
- Shows volume change over the last 24 hours (6 checks ago)
- **N/A** = Need 24+ hours of history (7+ checks)
- Positive % = Sustained volume growth
- Negative % = Volume declining over time

### Comparing 4H vs 24H

**Volume Acceleration Patterns:**

- **4H > 24H**: Volume accelerating NOW (e.g., 4H: +45%, 24H: +22%)
  - 🔥 Strong short-term momentum

- **4H < 24H**: Volume decelerating (e.g., 4H: +12%, 24H: +35%)
  - ⚠️ Momentum cooling off

- **Both Positive**: Sustained growth (e.g., 4H: +20%, 24H: +18%)
  - ✅ Healthy uptrend

- **Both Negative**: Sustained decline (e.g., 4H: -10%, 24H: -15%)
  - 🚨 Losing interest

### Rank Movement
- **CLIMBED X spots**: Moving up in volume rankings (gaining market share)
- **DROPPED X spots**: Moving down in rankings (losing market share)
- **STABLE**: Maintaining position
- **NEW ENTRY**: Just entered top 15

---

## 🎨 Signal Explanations

Auto-detected signals in the colorful table:

- **🆕 NEW** - New top-15 entry (catch early breakouts)
- **🔥 VOL+50%** - Volume spiked >50% in 4h (something BIG happening)
- **📈 VOL+20%** - Volume increased >20% in 4h (strong interest)
- **⬆️ CLIMB+3** - Rank climbed 3+ positions (gaining market share)
- **🚀 PUMP+30%** - Price pumped >30% in 24h (verify with volume)
- **💚 PUMP+15%** - Price pumped >15% in 24h (solid momentum)

---

## 📂 Data Files

### volume_history.csv

Stores all volume snapshots (appends every 4 hours):

```csv
timestamp,datetime,rank,symbol,volume_24h,price,change_24h_pct,funding_rate_pct,open_interest
1762782524.398975,2025-11-10 09:48:44,1,STRK,65103000,0.3732,34.70,0.0013,265660000
1762782524.398975,2025-11-10 09:48:44,2,PUMP,61360000,0.032184,11.30,0.0006,373810000
```

**Columns:**
- `timestamp` - Unix timestamp
- `datetime` - Human-readable datetime
- `rank` - Position in top 15
- `symbol` - Token symbol
- `volume_24h` - 24-hour volume in USD
- `price` - Current price
- `change_24h_pct` - 24H price change %
- `funding_rate_pct` - Funding rate %
- `open_interest` - Open interest in USD

### agent_analysis.jsonl

Stores AI swarm analysis (appends after each run):

```json
{
  "timestamp": 1762782524.3992379,
  "datetime": "2025-11-10 09:48:44",
  "changes": [...],
  "swarm_result": {
    "consensus_summary": "All models picked STRK...",
    "model_mapping": {"AI #1": "DEEPSEEK", "AI #2": "XAI", ...},
    "responses": {...},
    "metadata": {"total_time": 25.84, "successful_responses": 5}
  }
}
```

---

## 🧠 AI Swarm Configuration

The agent uses **SwarmAgent** with these models (configurable in `swarm_agent.py`):

**Default Active Models:**
- DeepSeek Chat (fast, cheap)
- XAI Grok-4 (advanced reasoning)
- Qwen 3 Max (via OpenRouter)
- Claude Sonnet 4.5 (balanced)
- GLM 4.6 (via OpenRouter)

**Cost per run:** ~$0.10-0.50 (depends on models)

**Edit models in:** `src/agents/swarm_agent.py` → `SWARM_MODELS` dict

---

## 💡 Trading Strategy Ideas

### Moon Dev's "Data Dog" Approach

1. **Watch all day** - Terminal always open
2. **AI consensus validation** - If 3+ AIs agree, high conviction
3. **Volume-only focus** - Pure acceleration signal
4. **Compare 4H vs 24H** - Identify accelerating vs decelerating
5. **Check every 4 hours** - Catch moves early

### Volume Signal Combinations

**Strong Buy Signals:**
- NEW + 4H: NEW + 24H: +50% + AI consensus = Early high-volume breakout
- CLIMB+3 + 4H: +45% + 24H: +22% + 3+ AI picks = Accelerating momentum
- 4H: +50% + 24H: +30% + High volume ($100M+) = Sustained volume spike

**Caution Signals:**
- 4H: NEW + 24H: -20% = Fresh entry but volume declining (cooling off)
- 4H: +10% + 24H: +60% = Decelerating (4H < 24H)
- 4H: -15% + 24H: -30% = Sustained decline (avoid)

**Neutral/Monitor:**
- 4H: +20% + 24H: +18% = Steady growth (watch for acceleration)
- NEW + 24H: N/A = Brand new, need more history

---

## 🔧 How It Works

### 1. Data Fetching
```python
get_all_tokens_volume()  # Hits Hyperliquid API
get_top_altcoins()       # Filters to top 15 altcoins (excludes BTC/ETH/SOL)
```

Uses Hyperliquid's `metaAndAssetCtxs` endpoint - no API key required.

### 2. Change Calculation
```python
load_previous_snapshot()  # Loads 4h ago snapshot from CSV
load_24h_snapshot()       # Loads 24h ago snapshot (6 checks back)
calculate_changes()       # Compares current vs previous
```

Calculates:
- 4-hour volume change %
- 24-hour volume change %
- Rank movement (up/down/stable/new)

### 3. AI Swarm Analysis
```python
swarm = SwarmAgent()                    # Initializes 5+ AI models
result = swarm.query(volume_prompt)     # Parallel queries with ThreadPoolExecutor
```

Process:
1. Creates volume-only prompt (no price/funding/OI)
2. Queries 5+ models in parallel (120s timeout per model)
3. Collects individual responses
4. Generates consensus summary using DeepSeek
5. Returns structured result with timing data

### 4. Data Display & Logging
```python
display_changes()        # Colorful table with signals
display_swarm_results()  # AI consensus + individual picks
display_data_table()     # Clean tabular view for humans
log_volume_snapshot()    # Append to CSV
log_agent_analysis()     # Append to JSONL
```

---

## 📊 Example Output

```
==========================================================================================================
📊 HYPERLIQUID TOP 15 ALTCOINS - COMPLETE MARKET VIEW 📊
==========================================================================================================

#    SYMBOL      PRICE           24H VOLUME        4H VOL Δ        24H PRICE Δ     RANK Δ         FUNDING      OPEN INT          SIGNALS
──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
1    STRK        $0.3732         $65.10M           NEW             +34.70%         NEW            +0.0013%     $265.66M          🆕NEW 🚀PUMP+30%
2    PUMP        $0.032184       $61.36M           NEW             +11.30%         NEW            +0.0006%     $373.81M          🆕NEW
3    VISTA       $0.000009       $35.24M           +45.60%         +18.90%         ↑ +3           +0.0008%     $124.33M          🔥VOL+50% ⬆️CLIMB+3 💚PUMP+15%
...

==========================================================================================================
🔍 MARKET SNAPSHOT:
   🆕 New Top-15 Entries: STRK, PUMP, WLFI
   🚀 24H Big Movers (>20%): STRK (+34.7%), VISTA (+18.9%)
   🔥 Volume Accelerators (>50%): VISTA (+45.6%)
   ⬆️  Rank Climbers (+3 or more): VISTA (↑3)
==========================================================================================================


==========================================================================================================
🧠 AI SWARM ANALYSIS - INDIVIDUAL RECOMMENDATIONS + CONSENSUS 🧠
==========================================================================================================

🎯 CONSENSUS RECOMMENDATION (ALL AIs AGREE):
──────────────────────────────────────────────────────────────────────────────────────────────────────────
All five AI models unanimously selected VISTA as the best volume opportunity, citing explosive 4H volume
acceleration (+45.6%), rank climbing (+3 spots), and strong absolute volume as key consensus factors.
──────────────────────────────────────────────────────────────────────────────────────────────────────────

📋 INDIVIDUAL AI RECOMMENDATIONS:
──────────────────────────────────────────────────────────────────────────────────────────────────────────

═══════════════════════════════════════════════════════════════════════════════════════════════════════════
💬 AI #1: DEEPSEEK (Response Time: 6.35s)
───────────────────────────────────────────────────────────────────────────────────────────────────────────
Based on volume data, I would pick **VISTA**.

VISTA shows explosive short-term acceleration (+45.6% in 4H) with a solid $35.24M absolute volume base.
The rank climb of 3 positions confirms genuine market interest shift, making it the strongest pure volume
momentum play right now.
───────────────────────────────────────────────────────────────────────────────────────────────────────────

[... other 4 AI responses ...]

📊 SWARM STATS:
   ✅ Successful Responses: 5/5
   ⏱️  Total Analysis Time: 25.84s


==========================================================================================================
📊 TOP 15 DATA TABLE - RAW DATA FOR MOON DEV'S ANALYSIS 📊
==========================================================================================================

RANK  SYMBOL      PRICE           24H VOLUME        4H VOL Δ        24H VOL Δ       24H PRICE Δ     FUNDING %     OPEN INT
──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
1     STRK        $0.373200       $65.10M           NEW             +15.50%         +34.70%         +0.0013%      $265.66M
2     PUMP        $0.032184       $61.36M           NEW             -5.20%          +11.30%         +0.0006%      $373.81M
3     VISTA       $0.000009       $35.24M           +45.60%         +22.10%         +18.90%         +0.0008%      $124.33M
...

==========================================================================================================
💡 Moon Dev Tip: Compare this data with AI consensus to find your edge!
==========================================================================================================
```

---

## 🛠️ Dependencies

### Core Libraries
```bash
pip install requests termcolor
```

### Moon Dev Framework
- `src/agents/swarm_agent.py` - Multi-model AI swarm
- `src/models/model_factory.py` - Unified model interface

### AI Model API Keys (in `.env`)
```bash
DEEPSEEK_KEY=sk-your-deepseek-key
GROK_API_KEY=xai-your-grok-key
OPENROUTER_API_KEY=sk-or-your-openrouter-key
ANTHROPIC_KEY=sk-ant-your-claude-key
# Add more as needed by SwarmAgent
```

---

## 💰 Cost Estimation

**Per check (every 4 hours):**
- API calls: FREE (Hyperliquid public API)
- AI swarm: ~$0.10-0.50 (5-6 models analyzing 15 tokens)

**Daily cost:** 6 checks × $0.30 = ~$1.80/day

**Monthly cost:** ~$54/month

**Cost reduction tips:**
- Use cheaper models (DeepSeek, Groq are nearly free)
- Reduce check frequency (e.g., every 6 hours)
- Disable expensive models in SwarmAgent config

---

## 🔥 Pro Tips

### Finding Your Edge

1. **Compare AI consensus with raw data** - Do the numbers support the AI pick?
2. **Watch 4H vs 24H divergence** - Acceleration = opportunity
3. **Track repeated picks** - If same token shows up in multiple runs = high conviction
4. **Monitor new entries** - Fresh top-15 entries with growing volume = early catch
5. **Check rank climbing** - Tokens moving up ranks = gaining market share

### Example Analysis

**AI says**: "Buy VISTA"
**Your analysis**:
- 4H VOL Δ: +45.6% ✅ (accelerating)
- 24H VOL Δ: +22.10% ✅ (sustained growth)
- Rank: CLIMBED 3 spots ✅ (gaining market share)
- Volume: $35.24M ✅ (decent liquidity)

**Decision**: Strong buy signal - all indicators align!

---

## ⚠️ Important Notes

### Data Requirements

- **First run**: Shows "NEW" for all tokens (no history yet)
- **After 1 check (4h)**: Can calculate 4H VOL Δ
- **After 7 checks (28h)**: Can calculate 24H VOL Δ

**Best practice**: Let it run for 24-48 hours to build full dataset

### Limitations

- Hyperliquid only (not CEX or other DEXs)
- Altcoins only (BTC/ETH/SOL excluded by default)
- 4-hour intervals (not real-time tick data)
- Requires internet connection
- AI costs accumulate over time

---

## 🚨 Disclaimers

- **Not Financial Advice**: This is a research tool, not trading advice
- **Use At Your Own Risk**: Trading crypto is highly risky
- **No Guarantees**: Past performance ≠ future results
- **API Costs**: Running AI models costs money
- **Educational Purpose**: For learning algorithmic trading patterns

---

## 📞 Support

**Built by Moon Dev** for the Data Dogs 🐕

**GitHub**: moon-dev-ai-agents-for-trading
**Location**: `src/agents/volume_agent.py`
**Data**: `src/data/volume_agent/`

---

## 🎯 Quick Reference

### Commands
```bash
# Test run
python src/agents/volume_agent.py --once

# Continuous
python src/agents/volume_agent.py

# Background
nohup python src/agents/volume_agent.py > volume_agent.log 2>&1 &

# Stop background
pkill -f "python src/agents/volume_agent.py"
```

### Key Files
- Agent: `src/agents/volume_agent.py`
- Config: Edit constants at top of file
- Data: `src/data/volume_agent/`
- Swarm: `src/agents/swarm_agent.py`

### Key Metrics
- **4H VOL Δ**: Short-term volume change (last 4 hours)
- **24H VOL Δ**: Long-term volume change (last 24 hours)
- **Rank Movement**: Position change in top 15
- **Signals**: NEW, VOL+50%, VOL+20%, CLIMB+3, PUMP+30%, PUMP+15%

---

**Built with Moon Dev** 🌙

*"Catch the volume pumps BEFORE Crypto Twitter"*
