# RBI Agent (Research-Based Inference)

**Created by Moon Dev**

The RBI Agent is an AI-powered system that converts strategy ideas from any source (text, videos, PDFs, or files) into backtested trading strategies using DeepSeek-R1 reasoning AI.

## Overview

**RBI = Research-Based Inference**

The agent analyzes trading content, extracts strategy logic, generates Python backtesting code, and executes multi-timeframe, multi-asset tests automatically.

**Current Version**: `rbi_agent_pp_multi.py` (Parallel Processor + Multi-Data)

## Key Features

- **Multi-Source Input**: Text, YouTube URLs, PDFs, or strategy files
- **AI Code Generation**: DeepSeek-R1 generates backtesting.py code
- **Multi-Timeframe Testing**: Tests each strategy on 4+ data configurations
- **Parallel Processing**: 4 concurrent worker threads
- **Continuous Monitoring**: Watches for new strategies in real-time
- **Duplicate Prevention**: Never processes same strategy twice
- **Heavy Logging**: All results tracked in CSV files
- **File-Based Input** ⭐ NEW: Read strategies from folder of .md/.txt files

## Two Modes of Operation

The RBI Agent supports **two ways** to read strategy ideas:

### Mode 1: Classic Line-by-Line (Default)

**Configuration**: `STRATEGIES_FROM_FILES = False`

Reads from `ideas.txt` where each line is one strategy:

```txt
# ideas.txt
Create a simple RSI strategy that buys when RSI < 30
Momentum strategy using 20/50 SMA crossover
Mean reversion with Bollinger Bands
```

**When to use**:
- Manual strategy entry
- Quick one-liner ideas
- Traditional workflow

### Mode 2: File-Based Reading ⭐ NEW

**Configuration**: `STRATEGIES_FROM_FILES = True`

Reads all `.md` and `.txt` files from a specified folder, where each file is one complete strategy:

```python
# In rbi_agent_pp_multi.py (lines 102-103)
STRATEGIES_FROM_FILES = True
STRATEGIES_FOLDER = "/path/to/strategy/files"
```

**When to use**:
- **Web Search Agent integration** (auto-generated strategies)
- Longer, detailed strategy descriptions
- Organized strategy libraries
- Batch processing

## Installation

### Prerequisites

```bash
# Required API key in .env
DEEPSEEK_API_KEY=your_key_here
```

### Script Location

```bash
# Main parallel processor
src/agents/rbi_agent_pp_multi.py

# Output folder
src/data/rbi_pp_multi/
```

## Usage

### Basic Usage

Run the agent (continuous monitoring mode):
```bash
python src/agents/rbi_agent_pp_multi.py
```

The agent will:
1. Start 4 worker threads
2. Monitor for new strategies (every 1 second)
3. Process strategies as they appear
4. Log all results to CSV files

### Classic Mode: Add Strategy to ideas.txt

```bash
# Add a strategy idea
echo "RSI divergence with MACD confirmation" >> src/data/rbi_pp_multi/ideas.txt

# Agent automatically picks it up and processes it
```

### File Mode: Add Strategy Files

```bash
# 1. Configure file mode in rbi_agent_pp_multi.py
STRATEGIES_FROM_FILES = True
STRATEGIES_FOLDER = "/path/to/strategies"

# 2. Add .md or .txt files to that folder
echo "# RSI Mean Reversion

This strategy uses RSI oversold conditions..." > /path/to/strategies/strategy1.md

# 3. Agent automatically detects and processes new files
```

## Configuration

**Location**: `src/agents/rbi_agent_pp_multi.py`

### Strategy Input Configuration (NEW!)

```python
# ============================================
# 📁 STRATEGY SOURCE CONFIGURATION - Moon Dev
# ============================================
# Option 1 (Default): STRATEGIES_FROM_FILES = False
#   - Reads from ideas.txt (one strategy per line)
#   - Classic behavior
#
# Option 2: STRATEGIES_FROM_FILES = True
#   - Reads all .md and .txt files from STRATEGIES_FOLDER
#   - Each FILE = one complete strategy idea
#   - Perfect for web search agent integration!
#
STRATEGIES_FROM_FILES = False  # Set to True for file mode
STRATEGIES_FOLDER = "/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/web_search_research/final_strategies"
```

### Performance Settings

```python
# Minimum return percentage to consider successful
TARGET_RETURN = 20.0

# Number of concurrent processing threads
MAX_PARALLEL_THREADS = 4
```

### AI Model

```python
# DeepSeek R1 - Best for reasoning and code generation
MODEL = "deepseek/deepseek-r1"
```

### Data Configuration

```python
# Where OHLCV data is stored
DATA_DIR = "/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi"

# CSV file with strategy ideas (classic mode only)
IDEAS_FILE = "/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi_pp_multi/ideas.txt"
```

## Startup Messages

When you run the agent, clear messages show which configuration is active:

### Classic Mode Output

```
============================================================
🌟 Moon Dev's RBI AI v3.0 PARALLEL PROCESSOR + MULTI-DATA 🚀
============================================================

📅 Date: 2025-10-28
🎯 Target Return: 20.0%
🔀 Max Parallel Threads: 4

============================================================
📝 STRATEGY SOURCE: ideas.txt (line by line)
📄 File: /path/to/ideas.txt
💡 Classic mode - one strategy per line
============================================================

🔄 CONTINUOUS QUEUE MODE ACTIVATED
⏰ Monitoring ideas.txt every 1 second
🧵 4 worker threads ready
```

### File Mode Output

```
============================================================
🌟 Moon Dev's RBI AI v3.0 PARALLEL PROCESSOR + MULTI-DATA 🚀
============================================================

📅 Date: 2025-10-28
🎯 Target Return: 20.0%
🔀 Max Parallel Threads: 4

============================================================
📁 STRATEGY SOURCE: FILES FROM FOLDER
📂 Folder: /path/to/strategies
📊 Found 28 strategy files (.md/.txt)
============================================================

🔄 CONTINUOUS QUEUE MODE ACTIVATED
⏰ Monitoring strategy files in folder every 1 second
🧵 4 worker threads ready
```

## How It Works

### Processing Pipeline

```
1. Input Strategy (from ideas.txt OR folder)
   ↓
2. Hash Check (skip if already processed)
   ↓
3. Content Analysis
   - YouTube: Download & transcribe
   - PDF: Extract text
   - Text/File: Use directly
   ↓
4. DeepSeek R1 Reasoning
   - Analyze trading logic
   - Extract entry/exit rules
   - Identify indicators
   ↓
5. Code Generation
   - Generate backtesting.py code
   - Use pandas_ta for indicators
   - Create Strategy class
   ↓
6. Multi-Data Testing
   ├─> BTC 15m (30 days)
   ├─> BTC 1H (90 days)
   ├─> ETH 15m (30 days)
   └─> ETH 1H (90 days)
   ↓
7. Results Aggregation
   - Select best performing config
   - Log all results to CSV
   - Save generated code
```

### Multi-Threaded Architecture

**Producer-Consumer Pattern**:
- 1 monitor thread (producer) - watches for new strategies
- 4 worker threads (consumers) - process strategies in parallel
- Queue-based coordination
- Thread-safe logging and file operations

**Benefits**:
- Process 4 strategies simultaneously
- ~2-4x faster than single-threaded
- Continuous operation without blocking

## Integration with Web Search Agent

This is the **killer feature** - fully automated strategy discovery and backtesting.

### The Complete Pipeline

```
Step 1: Web Search Agent
   ↓
Searches web for trading strategies
   ↓
Scrapes and extracts content
   ↓
Saves clean files to:
  src/data/web_search_research/final_strategies/

Step 2: RBI Agent (This)
   ↓
Reads all .md/.txt files from that folder
   ↓
Generates backtest code for each
   ↓
Tests on 4+ timeframes/assets
   ↓
Logs results to backtest_stats.csv
```

### Setup Instructions

**1. Run Web Search Agent** (generates strategy files):
```bash
python src/agents/websearch_agent.py
```

**2. Configure RBI Agent** for file mode:

Edit `src/agents/rbi_agent_pp_multi.py` (lines 102-103):
```python
STRATEGIES_FROM_FILES = True
STRATEGIES_FOLDER = "/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/web_search_research/final_strategies"
```

**3. Run RBI Agent**:
```bash
python src/agents/rbi_agent_pp_multi.py
```

**4. Watch the automation**:
- Web search agent finds strategies (every 60 seconds)
- Saves clean files to final_strategies/
- RBI agent detects new files (every 1 second)
- Generates and tests each strategy
- Logs results

**Result**: Fully automated strategy research, discovery, coding, and backtesting!

### Running Both Agents Simultaneously

```bash
# Terminal 1: Web Search Agent
python src/agents/websearch_agent.py

# Terminal 2: RBI Agent (in file mode)
python src/agents/rbi_agent_pp_multi.py

# Both agents run continuously, feeding each other
# Web search → finds strategies
# RBI agent → backtests them
```

## Input Sources

The RBI Agent accepts multiple input formats:

### Text Descriptions
```txt
Create a momentum strategy using 20/50 SMA crossover with volume confirmation
```

### YouTube URLs
```txt
https://www.youtube.com/watch?v=dQw4w9WgXcQ
```
Agent will:
- Download video
- Extract audio
- Transcribe to text
- Extract strategy

### PDF Files
```txt
/path/to/trading_strategy.pdf
```
Agent will:
- Extract text from PDF
- Parse strategy details
- Generate code

### Strategy Files (NEW!)
```markdown
# RSI Mean Reversion Strategy

This strategy uses RSI oversold conditions combined with
volume spikes to identify high-probability entries...
```

Format: Just strategy name + description (no metadata needed)

## Output Files

### backtest_stats.csv
**Primary output** - All backtest results:

Key columns:
- `timestamp` - When backtest ran
- `strategy_name` - Name of strategy
- `idea_text` - Original description
- `return_pct` - Total return %
- `sharpe_ratio` - Risk-adjusted returns
- `max_drawdown` - Worst drawdown
- `num_trades` - Number of trades
- `win_rate` - Win percentage
- `timeframe` - Data timeframe tested
- `asset` - Asset symbol
- `code_filepath` - Generated code location
- `error` - Error if failed

### strategy_ideas.csv
Quick overview of attempts:
- `timestamp`
- `idea`
- `status` (success/failed)
- `return` (best return %)
- `target_hit` (hit TARGET_RETURN?)
- `error`

### processed_ideas.log
Tracks processed strategies by hash to prevent duplicates:
```
abc123def456...
789ghi012jkl...
```

### Daily Folders (YYYY_MM_DD/)
Generated Python files organized by date:
- `strategy_name_HHMMSS.py` - Backtest code
- Timestamped for organization

## Multi-Data Testing

Each strategy is tested on multiple configurations:

```python
MULTI_DATA_CONFIGS = [
    {
        "symbol": "BTC-USD",
        "timeframe": "15m",
        "days": 30,
        "description": "Bitcoin 15-minute (1 month)"
    },
    {
        "symbol": "BTC-USD",
        "timeframe": "1H",
        "days": 90,
        "description": "Bitcoin 1-hour (3 months)"
    },
    {
        "symbol": "ETH-USD",
        "timeframe": "15m",
        "days": 30,
        "description": "Ethereum 15-minute (1 month)"
    },
    {
        "symbol": "ETH-USD",
        "timeframe": "1H",
        "days": 90,
        "description": "Ethereum 1-hour (3 months)"
    }
]
```

**Purpose**: Validate strategy works across:
- Different timeframes (15m, 1H)
- Different assets (BTC, ETH)
- Different periods (30-90 days)

**Result Selection**: Best performing configuration is logged

## Performance & Costs

### Per Strategy
- DeepSeek R1 API call: ~$0.01-0.03
- Code generation: ~$0.02
- **Total cost**: ~$0.027 per strategy

### Processing Time
- Strategy analysis: 30-60 seconds
- Code generation: 20-40 seconds
- Backtests (4 configs): 10-30 seconds
- **Total time**: 1-2 minutes per strategy

### Throughput
- **4 parallel threads**: 120-240 strategies/hour
- **24/7 operation**: 2,880-5,760 strategies/day
- **With web search agent**: Fully automated unlimited

### Success Rates
Typical results:
- Code generation success: 80-90%
- Successful backtests: 60-80%
- Hit target return (20%): 5-15%
- Publishable strategies: 1-5%

## Analyzing Results

### View Best Strategies
```bash
# Sort by return percentage
sort -t',' -k4 -rn src/data/rbi_pp_multi/backtest_stats.csv | head -10

# Filter for successful strategies
grep -v "error" src/data/rbi_pp_multi/backtest_stats.csv | sort -t',' -k4 -rn
```

### Check Processing Status
```bash
# Count processed strategies
wc -l src/data/rbi_pp_multi/processed_ideas.log

# View recent attempts
tail -20 src/data/rbi_pp_multi/strategy_ideas.csv
```

### Review Generated Code
```bash
# Find today's generated strategies
ls -lt src/data/rbi_pp_multi/$(date +%m_%d_%Y)/
```

## Troubleshooting

### "Strategy already processed"

**Cause**: Strategy hash exists in `processed_ideas.log`

**Fix**: Delete that hash from the log file to reprocess
```bash
# Remove specific hash
sed -i '' '/abc123def456/d' src/data/rbi_pp_multi/processed_ideas.log
```

### No strategies being processed

**Check**:
1. Configuration is correct (STRATEGIES_FROM_FILES and path)
2. Files exist in folder (if file mode) or ideas.txt has content
3. Look for startup messages showing config

**Fix**: Review startup output to confirm correct mode

### Code generation failures

**Cause**: Strategy description too vague or complex

**Check**: Error column in `backtest_stats.csv`

**Fix**: Add more specific details:
- Mention specific indicators (RSI, MACD, SMA)
- Include parameter values (RSI < 30)
- Specify entry/exit rules clearly

### Backtest failures

**Cause**: Generated code has errors or logical issues

**Check**: Review `.py` file in daily folder

**Note**: This is normal - not every strategy will work perfectly

## Tips for Best Results

### Strategy Descriptions

**Good examples**:
```
RSI mean reversion: Buy when RSI < 30, sell when RSI > 70

Momentum breakout: Buy when price crosses above 20-day SMA with volume > 2x average

Bollinger Band squeeze: Enter when bands width < 2% of price, exit at band touch
```

**Bad examples**:
```
Buy low sell high  (too vague)
Make money trading  (no logic)
Use AI to predict  (not backtestable)
```

### For File Mode

- Use web search agent to auto-generate files
- Let both agents run 24/7
- Check results periodically in backtest_stats.csv
- Delete low-quality files if needed

### For Classic Mode

- Be specific with parameters
- One strategy per line
- Mention timeframe if important
- Include risk management rules

## Advanced Features

### Custom Run Names

Organize experiments by adding metadata:
```bash
python src/agents/rbi_agent_pp_multi.py --run-name "momentum_strategies"
```

### Custom Ideas File

Use different source file (classic mode):
```bash
python src/agents/rbi_agent_pp_multi.py --ideas-file "/path/to/custom_ideas.txt"
```

### Adjust Thread Count

Edit `MAX_PARALLEL_THREADS` in code:
- Lower (2): Less resource usage
- Higher (6-8): Faster processing (if system handles it)

### Modify Data Configurations

Edit `MULTI_DATA_CONFIGS` in code to test on:
- Different assets (add SOL, DOGE, etc.)
- Different timeframes (5m, 4H, 1D)
- Different lookback periods

## Monitoring

### Key Metrics

1. **Processing Rate**: strategies/hour
2. **Success Rate**: successful backtests / attempts
3. **Target Hit Rate**: strategies > TARGET_RETURN
4. **Error Rate**: failures / total

### Files to Watch

- `backtest_stats.csv` - All results
- `strategy_ideas.csv` - Overview of attempts
- `processed_ideas.log` - What's been processed
- Daily folders - Generated code

### Real-Time Monitoring

Watch logs in real-time:
```bash
# Watch backtest stats
tail -f src/data/rbi_pp_multi/backtest_stats.csv

# Watch strategy attempts
tail -f src/data/rbi_pp_multi/strategy_ideas.csv
```

## Architecture Notes

### Why DeepSeek R1?

- Reasoning capabilities for strategy analysis
- Excellent code generation
- Cheap (~$0.027 per strategy)
- Fast inference

### Why Multi-Data Testing?

- Validates across timeframes
- Catches overfitting
- Tests on different assets
- More robust strategies

### Why Parallel Processing?

- 4x throughput increase
- Better resource utilization
- Can handle web search agent output
- Continuous operation

### Thread Safety

All operations are thread-safe:
- Console output uses locks
- File operations synchronized
- API rate limiting enforced
- Queue-based coordination

## Related Documentation

- [Web Search Agent](websearch_agent.md) - Auto-generates strategy files
- [OpenRouter](openrouter.md) - Alternative AI providers
- [Backtest Dashboard](backtest_dashboard.md) - Visualize results

## Notes

- **Continuous monitoring**: Checks every 1 second for new strategies
- **Duplicate prevention**: Hashes prevent reprocessing
- **Thread-safe**: All operations use proper locking
- **Graceful shutdown**: Ctrl+C stops cleanly
- **Heavy logging**: Everything tracked in CSVs
- **Real data only**: No fake/synthetic data ever
- **Multi-timeframe**: Every strategy tested on 4+ configs

---

**Made with ❤️ by Moon Dev**

*Part of the Moon Dev AI Agents for Trading project*

**GitHub**: https://github.com/moon-dev-ai-agents-for-trading
