"""
🌙 Moon Dev's RBI AI v3.0 PARALLEL PROCESSOR 🚀
Built with love by Moon Dev 🚀

PARALLEL PROCESSING: Run up to 5 backtests simultaneously!
- Each thread processes a different trading idea
- Thread-safe colored output
- Rate limiting to avoid API throttling
- Massively faster than sequential processing

HOW IT WORKS:
1. Reads trading ideas from ideas.txt
2. Spawns up to MAX_PARALLEL_THREADS workers
3. Each thread independently: Research → Backtest → Debug → Optimize
4. All threads run simultaneously until target returns are hit
5. Thread-safe file naming with unique 2-digit thread IDs

NEW FEATURES:
- 🎨 Color-coded output per thread (Thread 1 = cyan, Thread 2 = magenta, etc.)
- ⏱️ Rate limiting to avoid API throttling
- 🔒 Thread-safe file operations
- 📊 Real-time progress tracking across all threads
- 💾 Clean file organization with thread IDs in names

Required Setup:
1. Conda environment 'tflow' with backtesting packages
2. Set MAX_PARALLEL_THREADS (default: 5)
3. Run and watch all ideas process in parallel! 🚀💰

IMPORTANT: Each thread is fully independent and won't interfere with others!
"""

# Import execution functionality
import subprocess
import json
from pathlib import Path

# Core imports
import os
import time
import re
import hashlib
import csv
from datetime import datetime
from termcolor import cprint
import sys
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock, Semaphore

# Load environment variables FIRST
load_dotenv()
print("✅ Environment variables loaded")

# Add config values directly to avoid import issues
AI_TEMPERATURE = 0.7
AI_MAX_TOKENS = 4000

# Import model factory with proper path handling
import sys
sys.path.append('/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading')

try:
    from src.models import model_factory
    print("✅ Successfully imported model_factory")
except ImportError as e:
    print(f"⚠️ Could not import model_factory: {e}")
    sys.exit(1)

# ============================================
# 🎯 PARALLEL PROCESSING CONFIGURATION
# ============================================
MAX_PARALLEL_THREADS = 5  # How many ideas to process simultaneously
RATE_LIMIT_DELAY = 2  # Seconds to wait between API calls (per thread)
RATE_LIMIT_GLOBAL_DELAY = 0.5  # Global delay between any API calls

# Thread color mapping
THREAD_COLORS = {
    0: "cyan",
    1: "magenta",
    2: "yellow",
    3: "green",
    4: "blue"
}

# Global locks
console_lock = Lock()
api_lock = Lock()
file_lock = Lock()

# Rate limiter
rate_limiter = Semaphore(MAX_PARALLEL_THREADS)

# Model Configurations (same as v3)
RESEARCH_CONFIG = {
    "type": "xai",
    "name": "grok-4-fast-reasoning"
}

BACKTEST_CONFIG = {
    "type": "xai",
    "name": "grok-4-fast-reasoning"
}

DEBUG_CONFIG = {
    "type": "xai",
    "name": "grok-4-fast-reasoning"
}

PACKAGE_CONFIG = {
    "type": "xai",
    "name": "grok-4-fast-reasoning"
}

OPTIMIZE_CONFIG = {
    "type": "xai",
    "name": "grok-4-fast-reasoning"
}

# 🎯 PROFIT TARGET CONFIGURATION
TARGET_RETURN = 50  # Target return in %
SAVE_IF_OVER_RETURN = 1.0  # Save backtest to CSV and folders if return > this % (Moon Dev's threshold!)
CONDA_ENV = "tflow"
MAX_DEBUG_ITERATIONS = 10
MAX_OPTIMIZATION_ITERATIONS = 10
EXECUTION_TIMEOUT = 300  # 5 minutes

# DeepSeek Configuration
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

# Get today's date for organizing outputs
TODAY_DATE = datetime.now().strftime("%m_%d_%Y")

# Update data directory paths - Parallel version uses its own folder
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data/rbi_pp"
TODAY_DIR = DATA_DIR / TODAY_DATE
RESEARCH_DIR = TODAY_DIR / "research"
BACKTEST_DIR = TODAY_DIR / "backtests"
PACKAGE_DIR = TODAY_DIR / "backtests_package"
WORKING_BACKTEST_DIR = TODAY_DIR / "backtests_working"  # Moon Dev's working iterations!
FINAL_BACKTEST_DIR = TODAY_DIR / "backtests_final"
OPTIMIZATION_DIR = TODAY_DIR / "backtests_optimized"
CHARTS_DIR = TODAY_DIR / "charts"
EXECUTION_DIR = TODAY_DIR / "execution_results"
PROCESSED_IDEAS_LOG = DATA_DIR / "processed_ideas.log"
STATS_CSV = DATA_DIR / "backtest_stats.csv"  # Moon Dev's stats tracker!

IDEAS_FILE = DATA_DIR / "ideas.txt"

# Create main directories if they don't exist
for dir in [DATA_DIR, TODAY_DIR, RESEARCH_DIR, BACKTEST_DIR, PACKAGE_DIR,
            WORKING_BACKTEST_DIR, FINAL_BACKTEST_DIR, OPTIMIZATION_DIR, CHARTS_DIR, EXECUTION_DIR]:
    dir.mkdir(parents=True, exist_ok=True)

# ============================================
# 🎨 THREAD-SAFE PRINTING
# ============================================

def thread_print(message, thread_id, color=None, attrs=None):
    """Thread-safe colored print with thread ID prefix"""
    if color is None:
        color = THREAD_COLORS.get(thread_id % 5, "white")

    with console_lock:
        prefix = f"[T{thread_id:02d}]"
        cprint(f"{prefix} {message}", color, attrs=attrs)

def thread_print_status(thread_id, phase, message):
    """Print status update for a specific phase"""
    color = THREAD_COLORS.get(thread_id % 5, "white")
    with console_lock:
        cprint(f"[T{thread_id:02d}] {phase}: {message}", color)

# ============================================
# 🔒 RATE LIMITING
# ============================================

def rate_limited_api_call(func, thread_id, *args, **kwargs):
    """
    Wrapper for API calls with rate limiting
    - Per-thread rate limiting (RATE_LIMIT_DELAY)
    - Global rate limiting (RATE_LIMIT_GLOBAL_DELAY)
    """
    # Global rate limit (quick check)
    with api_lock:
        time.sleep(RATE_LIMIT_GLOBAL_DELAY)

    # Execute the API call
    result = func(*args, **kwargs)

    # Per-thread rate limit
    time.sleep(RATE_LIMIT_DELAY)

    return result

# ============================================
# 📝 PROMPTS (Same as v3)
# ============================================

RESEARCH_PROMPT = """
You are Moon Dev's Research AI 🌙

IMPORTANT NAMING RULES:
1. Create a UNIQUE TWO-WORD NAME for this specific strategy
2. The name must be DIFFERENT from any generic names like "TrendFollower" or "MomentumStrategy"
3. First word should describe the main approach (e.g., Adaptive, Neural, Quantum, Fractal, Dynamic)
4. Second word should describe the specific technique (e.g., Reversal, Breakout, Oscillator, Divergence)
5. Make the name SPECIFIC to this strategy's unique aspects

Examples of good names:
- "AdaptiveBreakout" for a strategy that adjusts breakout levels
- "FractalMomentum" for a strategy using fractal analysis with momentum
- "QuantumReversal" for a complex mean reversion strategy
- "NeuralDivergence" for a strategy focusing on divergence patterns

BAD names to avoid:
- "TrendFollower" (too generic)
- "SimpleMoving" (too basic)
- "PriceAction" (too vague)

Output format must start with:
STRATEGY_NAME: [Your unique two-word name]

Then analyze the trading strategy content and create detailed instructions.
Focus on:
1. Key strategy components
2. Entry/exit rules
3. Risk management
4. Required indicators

Your complete output must follow this format:
STRATEGY_NAME: [Your unique two-word name]

STRATEGY_DETAILS:
[Your detailed analysis]

Remember: The name must be UNIQUE and SPECIFIC to this strategy's approach!
"""

BACKTEST_PROMPT = """
You are Moon Dev's Backtest AI 🌙 ONLY SEND BACK CODE, NO OTHER TEXT.
Create a backtesting.py implementation for the strategy.
USE BACKTESTING.PY
Include:
1. All necessary imports
2. Strategy class with indicators
3. Entry/exit logic
4. Risk management
5. your size should be 1,000,000
6. If you need indicators use TA lib or pandas TA.

IMPORTANT DATA HANDLING:
1. Clean column names by removing spaces: data.columns = data.columns.str.strip().str.lower()
2. Drop any unnamed columns: data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
3. Ensure proper column mapping to match backtesting requirements:
   - Required columns: 'Open', 'High', 'Low', 'Close', 'Volume'
   - Use proper case (capital first letter)

FOR THE PYTHON BACKTESTING LIBRARY USE BACKTESTING.PY AND SEND BACK ONLY THE CODE, NO OTHER TEXT.

INDICATOR CALCULATION RULES:
1. ALWAYS use self.I() wrapper for ANY indicator calculations
2. Use talib functions instead of pandas operations:
   - Instead of: self.data.Close.rolling(20).mean()
   - Use: self.I(talib.SMA, self.data.Close, timeperiod=20)
3. For swing high/lows use talib.MAX/MIN:
   - Instead of: self.data.High.rolling(window=20).max()
   - Use: self.I(talib.MAX, self.data.High, timeperiod=20)

BACKTEST EXECUTION ORDER:
1. Run initial backtest with default parameters first
2. Print full stats using print(stats) and print(stats._strategy)
3. no optimization code needed, just print the final stats, make sure full stats are printed, not just part or some. stats = bt.run() print(stats) is an example of the last line of code. no need for plotting ever.

do not creeate charts to plot this, just print stats. no charts needed.

CRITICAL POSITION SIZING RULE:
When calculating position sizes in backtesting.py, the size parameter must be either:
1. A fraction between 0 and 1 (for percentage of equity)
2. A whole number (integer) of units

The common error occurs when calculating position_size = risk_amount / risk, which results in floating-point numbers. Always use:
position_size = int(round(position_size))

Example fix:
❌ self.buy(size=3546.0993)  # Will fail
✅ self.buy(size=int(round(3546.0993)))  # Will work

RISK MANAGEMENT:
1. Always calculate position sizes based on risk percentage
2. Use proper stop loss and take profit calculations
4. Print entry/exit signals with Moon Dev themed messages

If you need indicators use TA lib or pandas TA.

Use this data path: /Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv
the above data head looks like below
datetime, open, high, low, close, volume,
2023-01-01 00:00:00, 16531.83, 16532.69, 16509.11, 16510.82, 231.05338022,
2023-01-01 00:15:00, 16509.78, 16534.66, 16509.11, 16533.43, 308.12276951,

Always add plenty of Moon Dev themed debug prints with emojis to make debugging easier! 🌙 ✨ 🚀

FOR THE PYTHON BACKTESTING LIBRARY USE BACKTESTING.PY AND SEND BACK ONLY THE CODE, NO OTHER TEXT.
ONLY SEND BACK CODE, NO OTHER TEXT.
"""

DEBUG_PROMPT = """
You are Moon Dev's Debug AI 🌙
Fix technical issues in the backtest code WITHOUT changing the strategy logic.

CRITICAL ERROR TO FIX:
{error_message}

CRITICAL DATA LOADING REQUIREMENTS:
The CSV file has these exact columns after processing:
- datetime, open, high, low, close, volume (all lowercase after .str.lower())
- After capitalization: Datetime, Open, High, Low, Close, Volume

CRITICAL BACKTESTING REQUIREMENTS:
1. Data Loading Rules:
   - Use data.columns.str.strip().str.lower() to clean columns
   - Drop unnamed columns: data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
   - Rename columns properly: data.rename(columns={{'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'}})
   - Set datetime as index: data = data.set_index(pd.to_datetime(data['datetime']))

2. Position Sizing Rules:
   - Must be either a fraction (0 < size < 1) for percentage of equity
   - OR a positive whole number (round integer) for units
   - NEVER use floating point numbers for unit-based sizing

3. Indicator Issues:
   - Cannot use .shift() on backtesting indicators
   - Use array indexing like indicator[-2] for previous values
   - All indicators must be wrapped in self.I()

4. Position Object Issues:
   - Position object does NOT have .entry_price attribute
   - Use self.trades[-1].entry_price if you need entry price from last trade
   - Available position attributes: .size, .pl, .pl_pct
   - For partial closes: use self.position.close() without parameters (closes entire position)
   - For stop losses: use sl= parameter in buy/sell calls, not in position.close()

5. No Trades Issue (Signals but no execution):
   - If strategy prints "ENTRY SIGNAL" but shows 0 trades, the self.buy() call is not executing
   - Common causes: invalid size parameter, insufficient cash, missing self.buy() call
   - Ensure self.buy() is actually called in the entry condition block
   - Check size parameter: must be fraction (0-1) or positive integer
   - Verify cash/equity is sufficient for the trade size

Focus on:
1. KeyError issues with column names
2. Syntax errors and import statements
3. Indicator calculation methods
4. Data loading and preprocessing
5. Position object attribute errors (.entry_price, .close() parameters)

DO NOT change strategy logic, entry/exit conditions, or risk management rules.

Return the complete fixed code with Moon Dev themed debug prints! 🌙 ✨
ONLY SEND BACK CODE, NO OTHER TEXT.
"""

PACKAGE_PROMPT = """
You are Moon Dev's Package AI 🌙
Your job is to ensure the backtest code NEVER uses ANY backtesting.lib imports or functions.

❌ STRICTLY FORBIDDEN:
1. from backtesting.lib import *
2. import backtesting.lib
3. from backtesting.lib import crossover
4. ANY use of backtesting.lib

✅ REQUIRED REPLACEMENTS:
1. For crossover detection:
   Instead of: backtesting.lib.crossover(a, b)
   Use: (a[-2] < b[-2] and a[-1] > b[-1])  # for bullish crossover
        (a[-2] > b[-2] and a[-1] < b[-1])  # for bearish crossover

2. For indicators:
   - Use talib for all standard indicators (SMA, RSI, MACD, etc.)
   - Use pandas-ta for specialized indicators
   - ALWAYS wrap in self.I()

3. For signal generation:
   - Use numpy/pandas boolean conditions
   - Use rolling window comparisons with array indexing
   - Use mathematical comparisons (>, <, ==)

Example conversions:
❌ from backtesting.lib import crossover
❌ if crossover(fast_ma, slow_ma):
✅ if fast_ma[-2] < slow_ma[-2] and fast_ma[-1] > slow_ma[-1]:

❌ self.sma = self.I(backtesting.lib.SMA, self.data.Close, 20)
✅ self.sma = self.I(talib.SMA, self.data.Close, timeperiod=20)

IMPORTANT: Scan the ENTIRE code for any backtesting.lib usage and replace ALL instances!
Return the complete fixed code with proper Moon Dev themed debug prints! 🌙 ✨
ONLY SEND BACK CODE, NO OTHER TEXT.
"""

OPTIMIZE_PROMPT = """
You are Moon Dev's Optimization AI 🌙
Your job is to IMPROVE the strategy to achieve higher returns while maintaining good risk management.

CURRENT PERFORMANCE:
Return [%]: {current_return}%
TARGET RETURN: {target_return}%

YOUR MISSION: Optimize this strategy to hit the target return!

OPTIMIZATION TECHNIQUES TO CONSIDER:
1. **Entry Optimization:**
   - Tighten entry conditions to catch better setups
   - Add filters to avoid low-quality signals
   - Use multiple timeframe confirmation
   - Add volume/momentum filters

2. **Exit Optimization:**
   - Improve take profit levels
   - Add trailing stops
   - Use dynamic position sizing based on volatility
   - Scale out of positions

3. **Risk Management:**
   - Adjust position sizing
   - Use volatility-based position sizing (ATR)
   - Add maximum drawdown limits
   - Improve stop loss placement

4. **Indicator Optimization:**
   - Fine-tune indicator parameters
   - Add complementary indicators
   - Use indicator divergence
   - Combine multiple timeframes

5. **Market Regime Filters:**
   - Add trend filters
   - Avoid choppy/ranging markets
   - Only trade in favorable conditions

IMPORTANT RULES:
- DO NOT break the code structure
- Keep all Moon Dev debug prints
- Maintain proper backtesting.py format
- Use self.I() for all indicators
- Position sizes must be int or fraction (0-1)
- Focus on REALISTIC improvements (no curve fitting!)
- Explain your optimization changes in comments

Return the COMPLETE optimized code with Moon Dev themed comments explaining what you improved! 🌙 ✨
ONLY SEND BACK CODE, NO OTHER TEXT.
"""

# ============================================
# 🛠️ HELPER FUNCTIONS (with thread safety)
# ============================================

def parse_return_from_output(stdout: str, thread_id: int) -> float:
    """Extract the Return [%] from backtest output"""
    try:
        match = re.search(r'Return \[%\]\s+([-\d.]+)', stdout)
        if match:
            return_pct = float(match.group(1))
            thread_print(f"📊 Extracted return: {return_pct}%", thread_id)
            return return_pct
        else:
            thread_print("⚠️ Could not find Return [%] in output", thread_id, "yellow")
            return None
    except Exception as e:
        thread_print(f"❌ Error parsing return: {str(e)}", thread_id, "red")
        return None

def parse_all_stats_from_output(stdout: str, thread_id: int) -> dict:
    """
    🌙 Moon Dev's Stats Parser - Extract all key stats from backtest output!
    Returns dict with: return_pct, buy_hold_pct, max_drawdown_pct, sharpe, sortino, expectancy
    """
    stats = {
        'return_pct': None,
        'buy_hold_pct': None,
        'max_drawdown_pct': None,
        'sharpe': None,
        'sortino': None,
        'expectancy': None
    }

    try:
        # Return [%]
        match = re.search(r'Return \[%\]\s+([-\d.]+)', stdout)
        if match:
            stats['return_pct'] = float(match.group(1))

        # Buy & Hold Return [%]
        match = re.search(r'Buy & Hold Return \[%\]\s+([-\d.]+)', stdout)
        if match:
            stats['buy_hold_pct'] = float(match.group(1))

        # Max. Drawdown [%]
        match = re.search(r'Max\. Drawdown \[%\]\s+([-\d.]+)', stdout)
        if match:
            stats['max_drawdown_pct'] = float(match.group(1))

        # Sharpe Ratio
        match = re.search(r'Sharpe Ratio\s+([-\d.]+)', stdout)
        if match:
            stats['sharpe'] = float(match.group(1))

        # Sortino Ratio
        match = re.search(r'Sortino Ratio\s+([-\d.]+)', stdout)
        if match:
            stats['sortino'] = float(match.group(1))

        # Expectancy [%] (or Avg. Trade [%])
        match = re.search(r'Expectancy \[%\]\s+([-\d.]+)', stdout)
        if not match:
            match = re.search(r'Avg\. Trade \[%\]\s+([-\d.]+)', stdout)
        if match:
            stats['expectancy'] = float(match.group(1))

        thread_print(f"📊 Extracted {sum(1 for v in stats.values() if v is not None)}/6 stats", thread_id)
        return stats

    except Exception as e:
        thread_print(f"❌ Error parsing stats: {str(e)}", thread_id, "red")
        return stats

def log_stats_to_csv(strategy_name: str, iteration: int, thread_id: int, stats: dict, file_path: str) -> None:
    """
    🌙 Moon Dev's CSV Logger - Thread-safe stats logging!
    Appends backtest stats to CSV for easy analysis and comparison
    """
    try:
        with file_lock:
            # Create CSV with headers if it doesn't exist
            file_exists = STATS_CSV.exists()

            with open(STATS_CSV, 'a', newline='') as f:
                writer = csv.writer(f)

                # Write header if new file
                if not file_exists:
                    writer.writerow([
                        'Strategy Name',
                        'Iteration',
                        'Thread ID',
                        'Return %',
                        'Buy & Hold %',
                        'Max Drawdown %',
                        'Sharpe Ratio',
                        'Sortino Ratio',
                        'Expectancy %',
                        'File Path',
                        'Timestamp'
                    ])
                    thread_print("📝 Created new stats CSV with headers", thread_id, "green")

                # Write stats row
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                writer.writerow([
                    strategy_name,
                    iteration,
                    f"T{thread_id:02d}",
                    stats.get('return_pct', 'N/A'),
                    stats.get('buy_hold_pct', 'N/A'),
                    stats.get('max_drawdown_pct', 'N/A'),
                    stats.get('sharpe', 'N/A'),
                    stats.get('sortino', 'N/A'),
                    stats.get('expectancy', 'N/A'),
                    str(file_path),
                    timestamp
                ])

                thread_print(f"✅ Logged stats to CSV (Return: {stats.get('return_pct', 'N/A')}%)", thread_id, "green")

    except Exception as e:
        thread_print(f"❌ Error logging to CSV: {str(e)}", thread_id, "red")

def save_backtest_if_threshold_met(code: str, stats: dict, strategy_name: str, iteration: int, thread_id: int, phase: str = "debug") -> bool:
    """
    🌙 Moon Dev's Threshold Checker - Save backtests that pass the return threshold!

    Args:
        code: The backtest code to save
        stats: Dict of parsed stats
        strategy_name: Name of the strategy
        iteration: Current iteration number
        thread_id: Thread ID
        phase: "debug", "opt", or "final" to determine filename

    Returns:
        True if saved (threshold met), False otherwise
    """
    return_pct = stats.get('return_pct')

    # Check if return meets threshold
    if return_pct is None or return_pct <= SAVE_IF_OVER_RETURN:
        thread_print(f"⚠️ Return {return_pct}% ≤ {SAVE_IF_OVER_RETURN}% threshold - not saving", thread_id, "yellow")
        return False

    try:
        # Determine filename based on phase
        if phase == "debug":
            filename = f"T{thread_id:02d}_{strategy_name}_DEBUG_v{iteration}_{return_pct:.1f}pct.py"
        elif phase == "opt":
            filename = f"T{thread_id:02d}_{strategy_name}_OPT_v{iteration}_{return_pct:.1f}pct.py"
        else:  # final
            filename = f"T{thread_id:02d}_{strategy_name}_FINAL_{return_pct:.1f}pct.py"

        # Save to WORKING folder
        working_file = WORKING_BACKTEST_DIR / filename
        with file_lock:
            with open(working_file, 'w') as f:
                f.write(code)

        # Save to FINAL folder (same logic per Moon Dev's request)
        final_file = FINAL_BACKTEST_DIR / filename
        with file_lock:
            with open(final_file, 'w') as f:
                f.write(code)

        thread_print(f"💾 Saved to working & final! Return: {return_pct:.2f}%", thread_id, "green", attrs=['bold'])

        # Log to CSV
        log_stats_to_csv(strategy_name, iteration, thread_id, stats, str(working_file))

        return True

    except Exception as e:
        thread_print(f"❌ Error saving backtest: {str(e)}", thread_id, "red")
        return False

def execute_backtest(file_path: str, strategy_name: str, thread_id: int) -> dict:
    """Execute a backtest file in conda environment and capture output"""
    thread_print(f"🚀 Executing: {strategy_name}", thread_id)

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    cmd = [
        "conda", "run", "-n", CONDA_ENV,
        "python", str(file_path)
    ]

    start_time = datetime.now()

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=EXECUTION_TIMEOUT
    )

    execution_time = (datetime.now() - start_time).total_seconds()

    output = {
        "success": result.returncode == 0,
        "return_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "execution_time": execution_time,
        "timestamp": datetime.now().isoformat()
    }

    # Save execution results with thread ID
    result_file = EXECUTION_DIR / f"T{thread_id:02d}_{strategy_name}_{datetime.now().strftime('%H%M%S')}.json"
    with file_lock:
        with open(result_file, 'w') as f:
            json.dump(output, f, indent=2)

    if output['success']:
        thread_print(f"✅ Backtest executed in {execution_time:.2f}s!", thread_id, "green")
    else:
        thread_print(f"❌ Backtest failed: {output['return_code']}", thread_id, "red")

    return output

def parse_execution_error(execution_result: dict) -> str:
    """Extract meaningful error message for debug agent"""
    if execution_result.get('stderr'):
        return execution_result['stderr'].strip()
    return execution_result.get('error', 'Unknown error')

def get_idea_hash(idea: str) -> str:
    """Generate a unique hash for an idea to track processing status"""
    return hashlib.md5(idea.encode('utf-8')).hexdigest()

def is_idea_processed(idea: str) -> bool:
    """Check if an idea has already been processed (thread-safe)"""
    if not PROCESSED_IDEAS_LOG.exists():
        return False

    idea_hash = get_idea_hash(idea)

    with file_lock:
        with open(PROCESSED_IDEAS_LOG, 'r') as f:
            processed_hashes = [line.strip().split(',')[0] for line in f if line.strip()]

    return idea_hash in processed_hashes

def log_processed_idea(idea: str, strategy_name: str, thread_id: int) -> None:
    """Log an idea as processed with timestamp and strategy name (thread-safe)"""
    idea_hash = get_idea_hash(idea)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with file_lock:
        if not PROCESSED_IDEAS_LOG.exists():
            PROCESSED_IDEAS_LOG.parent.mkdir(parents=True, exist_ok=True)
            with open(PROCESSED_IDEAS_LOG, 'w') as f:
                f.write("# Moon Dev's RBI AI - Processed Ideas Log 🌙\n")
                f.write("# Format: hash,timestamp,thread_id,strategy_name,idea_snippet\n")

        idea_snippet = idea[:50].replace(',', ';') + ('...' if len(idea) > 50 else '')
        with open(PROCESSED_IDEAS_LOG, 'a') as f:
            f.write(f"{idea_hash},{timestamp},T{thread_id:02d},{strategy_name},{idea_snippet}\n")

    thread_print(f"📝 Logged processed idea: {strategy_name}", thread_id, "green")

def has_nan_results(execution_result: dict) -> bool:
    """Check if backtest results contain NaN values indicating no trades"""
    if not execution_result.get('success'):
        return False

    stdout = execution_result.get('stdout', '')

    nan_indicators = [
        '# Trades                                    0',
        'Win Rate [%]                              NaN',
        'Exposure Time [%]                         0.0',
        'Return [%]                                0.0'
    ]

    nan_count = sum(1 for indicator in nan_indicators if indicator in stdout)
    return nan_count >= 2

def analyze_no_trades_issue(execution_result: dict) -> str:
    """Analyze why strategy shows signals but no trades"""
    stdout = execution_result.get('stdout', '')

    if 'ENTRY SIGNAL' in stdout and '# Trades                                    0' in stdout:
        return "Strategy is generating entry signals but self.buy() calls are not executing. This usually means: 1) Position sizing issues (size parameter invalid), 2) Insufficient cash/equity, 3) Logic preventing buy execution, or 4) Missing actual self.buy() call in the code. The strategy prints signals but never calls self.buy()."

    elif '# Trades                                    0' in stdout:
        return "Strategy executed but took 0 trades, resulting in NaN values. The entry conditions are likely too restrictive or there are logic errors preventing trade execution."

    return "Strategy executed but took 0 trades, resulting in NaN values. Please adjust the strategy logic to actually generate trading signals and take trades."

def chat_with_model(system_prompt, user_content, model_config, thread_id):
    """Chat with AI model using model factory with rate limiting"""
    def _api_call():
        model = model_factory.get_model(model_config["type"], model_config["name"])
        if not model:
            raise ValueError(f"🚨 Could not initialize {model_config['type']} {model_config['name']} model!")

        if model_config["type"] == "ollama":
            response = model.generate_response(
                system_prompt=system_prompt,
                user_content=user_content,
                temperature=AI_TEMPERATURE
            )
            if isinstance(response, str):
                return response
            if hasattr(response, 'content'):
                return response.content
            return str(response)
        else:
            response = model.generate_response(
                system_prompt=system_prompt,
                user_content=user_content,
                temperature=AI_TEMPERATURE,
                max_tokens=AI_MAX_TOKENS
            )
            if not response:
                raise ValueError("Model returned None response")
            return response.content

    # Apply rate limiting
    return rate_limited_api_call(_api_call, thread_id)

def clean_model_output(output, content_type="text"):
    """Clean model output by removing thinking tags and extracting code from markdown"""
    cleaned_output = output

    if "<think>" in output and "</think>" in output:
        clean_content = output.split("</think>")[-1].strip()
        if not clean_content:
            import re
            clean_content = re.sub(r'<think>.*?</think>', '', output, flags=re.DOTALL).strip()
        if clean_content:
            cleaned_output = clean_content

    if content_type == "code" and "```" in cleaned_output:
        try:
            import re
            code_blocks = re.findall(r'```python\n(.*?)\n```', cleaned_output, re.DOTALL)
            if not code_blocks:
                code_blocks = re.findall(r'```(?:python)?\n(.*?)\n```', cleaned_output, re.DOTALL)
            if code_blocks:
                cleaned_output = "\n\n".join(code_blocks)
        except Exception as e:
            thread_print(f"❌ Error extracting code: {str(e)}", 0, "red")

    return cleaned_output

# ============================================
# 🤖 AI AGENT FUNCTIONS (Thread-safe versions)
# ============================================

def research_strategy(content, thread_id):
    """Research AI: Analyzes and creates trading strategy"""
    thread_print_status(thread_id, "🔍 RESEARCH", "Starting analysis...")

    output = chat_with_model(
        RESEARCH_PROMPT,
        content,
        RESEARCH_CONFIG,
        thread_id
    )

    if output:
        output = clean_model_output(output, "text")

        strategy_name = "UnknownStrategy"
        if "STRATEGY_NAME:" in output:
            try:
                name_section = output.split("STRATEGY_NAME:")[1].strip()
                if "\n\n" in name_section:
                    strategy_name = name_section.split("\n\n")[0].strip()
                else:
                    strategy_name = name_section.split("\n")[0].strip()

                strategy_name = re.sub(r'[^\w\s-]', '', strategy_name)
                strategy_name = re.sub(r'[\s]+', '', strategy_name)

                thread_print(f"✅ Strategy: {strategy_name}", thread_id, "green")
            except Exception as e:
                thread_print(f"⚠️ Error extracting strategy name: {str(e)}", thread_id, "yellow")

        # Add thread ID to filename
        filepath = RESEARCH_DIR / f"T{thread_id:02d}_{strategy_name}_strategy.txt"
        with file_lock:
            with open(filepath, 'w') as f:
                f.write(output)

        return output, strategy_name
    return None, None

def create_backtest(strategy, strategy_name, thread_id):
    """Backtest AI: Creates backtest implementation"""
    thread_print_status(thread_id, "📊 BACKTEST", "Creating backtest code...")

    output = chat_with_model(
        BACKTEST_PROMPT,
        f"Create a backtest for this strategy:\n\n{strategy}",
        BACKTEST_CONFIG,
        thread_id
    )

    if output:
        output = clean_model_output(output, "code")

        filepath = BACKTEST_DIR / f"T{thread_id:02d}_{strategy_name}_BT.py"
        with file_lock:
            with open(filepath, 'w') as f:
                f.write(output)

        thread_print(f"🔥 Backtest code saved", thread_id, "green")
        return output
    return None

def package_check(backtest_code, strategy_name, thread_id):
    """Package AI: Ensures correct indicator packages are used"""
    thread_print_status(thread_id, "📦 PACKAGE", "Checking imports...")

    output = chat_with_model(
        PACKAGE_PROMPT,
        f"Check and fix indicator packages in this code:\n\n{backtest_code}",
        PACKAGE_CONFIG,
        thread_id
    )

    if output:
        output = clean_model_output(output, "code")

        filepath = PACKAGE_DIR / f"T{thread_id:02d}_{strategy_name}_PKG.py"
        with file_lock:
            with open(filepath, 'w') as f:
                f.write(output)

        thread_print(f"📦 Package check complete", thread_id, "green")
        return output
    return None

def debug_backtest(backtest_code, error_message, strategy_name, thread_id, iteration=1):
    """Debug AI: Fixes technical issues in backtest code"""
    thread_print_status(thread_id, f"🔧 DEBUG #{iteration}", "Fixing errors...")

    debug_prompt_with_error = DEBUG_PROMPT.format(error_message=error_message)

    output = chat_with_model(
        debug_prompt_with_error,
        f"Fix this backtest code:\n\n{backtest_code}",
        DEBUG_CONFIG,
        thread_id
    )

    if output:
        output = clean_model_output(output, "code")

        # 🌙 Moon Dev: Save debug iterations to BACKTEST_DIR, not FINAL
        # Only threshold-passing backtests go to FINAL/WORKING folders!
        filepath = BACKTEST_DIR / f"T{thread_id:02d}_{strategy_name}_DEBUG_v{iteration}.py"
        with file_lock:
            with open(filepath, 'w') as f:
                f.write(output)

        thread_print(f"🔧 Debug iteration {iteration} complete", thread_id, "green")
        return output
    return None

def optimize_strategy(backtest_code, current_return, target_return, strategy_name, thread_id, iteration=1):
    """Optimization AI: Improves strategy to hit target return"""
    thread_print_status(thread_id, f"🎯 OPTIMIZE #{iteration}", f"{current_return}% → {target_return}%")

    optimize_prompt_with_stats = OPTIMIZE_PROMPT.format(
        current_return=current_return,
        target_return=target_return
    )

    output = chat_with_model(
        optimize_prompt_with_stats,
        f"Optimize this backtest code to hit the target:\n\n{backtest_code}",
        OPTIMIZE_CONFIG,
        thread_id
    )

    if output:
        output = clean_model_output(output, "code")

        filepath = OPTIMIZATION_DIR / f"T{thread_id:02d}_{strategy_name}_OPT_v{iteration}.py"
        with file_lock:
            with open(filepath, 'w') as f:
                f.write(output)

        thread_print(f"🎯 Optimization {iteration} complete", thread_id, "green")
        return output
    return None

# ============================================
# 🚀 PARALLEL PROCESSING CORE
# ============================================

def process_trading_idea_parallel(idea: str, thread_id: int) -> dict:
    """
    Process a single trading idea with full Research → Backtest → Debug → Optimize pipeline
    This is the worker function for each parallel thread
    """
    try:
        thread_print(f"🚀 Starting processing", thread_id, attrs=['bold'])

        # Phase 1: Research
        strategy, strategy_name = research_strategy(idea, thread_id)

        if not strategy:
            thread_print("❌ Research failed", thread_id, "red")
            return {"success": False, "error": "Research failed", "thread_id": thread_id}

        log_processed_idea(idea, strategy_name, thread_id)

        # Phase 2: Backtest
        backtest = create_backtest(strategy, strategy_name, thread_id)

        if not backtest:
            thread_print("❌ Backtest failed", thread_id, "red")
            return {"success": False, "error": "Backtest failed", "thread_id": thread_id}

        # Phase 3: Package Check
        package_checked = package_check(backtest, strategy_name, thread_id)

        if not package_checked:
            thread_print("❌ Package check failed", thread_id, "red")
            return {"success": False, "error": "Package check failed", "thread_id": thread_id}

        package_file = PACKAGE_DIR / f"T{thread_id:02d}_{strategy_name}_PKG.py"

        # Phase 4: Execution Loop
        debug_iteration = 0
        current_code = package_checked
        current_file = package_file
        error_history = []

        while debug_iteration < MAX_DEBUG_ITERATIONS:
            thread_print_status(thread_id, "🚀 EXECUTE", f"Attempt {debug_iteration + 1}/{MAX_DEBUG_ITERATIONS}")

            execution_result = execute_backtest(current_file, strategy_name, thread_id)

            if execution_result['success']:
                if has_nan_results(execution_result):
                    thread_print("⚠️ No trades taken", thread_id, "yellow")

                    error_message = analyze_no_trades_issue(execution_result)
                    debug_iteration += 1

                    if debug_iteration < MAX_DEBUG_ITERATIONS:
                        debugged_code = debug_backtest(
                            current_code,
                            error_message,
                            strategy_name,
                            thread_id,
                            debug_iteration
                        )

                        if not debugged_code:
                            thread_print("❌ Debug AI failed", thread_id, "red")
                            return {"success": False, "error": "Debug failed", "thread_id": thread_id}

                        current_code = debugged_code
                        # 🌙 Moon Dev: Update to match new debug file location
                        current_file = BACKTEST_DIR / f"T{thread_id:02d}_{strategy_name}_DEBUG_v{debug_iteration}.py"
                        continue
                    else:
                        thread_print(f"❌ Max debug iterations reached", thread_id, "red")
                        return {"success": False, "error": "Max debug iterations", "thread_id": thread_id}
                else:
                    # SUCCESS! Code executes with trades!
                    thread_print("🎉 BACKTEST SUCCESSFUL!", thread_id, "green", attrs=['bold'])

                    # 🌙 Moon Dev: Parse ALL stats, not just return!
                    all_stats = parse_all_stats_from_output(execution_result['stdout'], thread_id)
                    current_return = all_stats.get('return_pct')

                    if current_return is None:
                        thread_print("⚠️ Could not parse return", thread_id, "yellow")
                        final_file = FINAL_BACKTEST_DIR / f"T{thread_id:02d}_{strategy_name}_BTFinal_WORKING.py"
                        with file_lock:
                            with open(final_file, 'w') as f:
                                f.write(current_code)
                        break

                    # 🌙 Moon Dev: Check threshold and save if met!
                    save_backtest_if_threshold_met(
                        current_code,
                        all_stats,
                        strategy_name,
                        debug_iteration,
                        thread_id,
                        phase="debug"
                    )

                    thread_print(f"📊 Return: {current_return}% | Target: {TARGET_RETURN}%", thread_id)

                    if current_return >= TARGET_RETURN:
                        # TARGET HIT!
                        thread_print("🚀🚀🚀 TARGET HIT! 🚀🚀🚀", thread_id, "green", attrs=['bold'])

                        # 🌙 Moon Dev: Save to OPTIMIZATION_DIR for target hits
                        final_file = OPTIMIZATION_DIR / f"T{thread_id:02d}_{strategy_name}_TARGET_HIT_{current_return}pct.py"
                        with file_lock:
                            with open(final_file, 'w') as f:
                                f.write(current_code)

                        return {
                            "success": True,
                            "thread_id": thread_id,
                            "strategy_name": strategy_name,
                            "return": current_return,
                            "target_hit": True
                        }
                    else:
                        # Need to optimize
                        gap = TARGET_RETURN - current_return
                        thread_print(f"📈 Need {gap}% more - Starting optimization", thread_id)

                        optimization_iteration = 0
                        optimization_code = current_code
                        best_return = current_return
                        best_code = current_code

                        while optimization_iteration < MAX_OPTIMIZATION_ITERATIONS:
                            optimization_iteration += 1

                            optimized_code = optimize_strategy(
                                optimization_code,
                                best_return,
                                TARGET_RETURN,
                                strategy_name,
                                thread_id,
                                optimization_iteration
                            )

                            if not optimized_code:
                                thread_print("❌ Optimization AI failed", thread_id, "red")
                                break

                            opt_file = OPTIMIZATION_DIR / f"T{thread_id:02d}_{strategy_name}_OPT_v{optimization_iteration}.py"
                            opt_result = execute_backtest(opt_file, strategy_name, thread_id)

                            if not opt_result['success'] or has_nan_results(opt_result):
                                thread_print(f"⚠️ Optimization {optimization_iteration} failed", thread_id, "yellow")
                                continue

                            # 🌙 Moon Dev: Parse ALL stats from optimization!
                            opt_stats = parse_all_stats_from_output(opt_result['stdout'], thread_id)
                            new_return = opt_stats.get('return_pct')

                            if new_return is None:
                                continue

                            change = new_return - best_return
                            thread_print(f"📊 Opt {optimization_iteration}: {new_return}% ({change:+.2f}%)", thread_id)

                            if new_return > best_return:
                                thread_print(f"✅ Improved by {change:.2f}%!", thread_id, "green")
                                best_return = new_return
                                best_code = optimized_code
                                optimization_code = optimized_code

                                # 🌙 Moon Dev: Check threshold and save if met!
                                save_backtest_if_threshold_met(
                                    optimized_code,
                                    opt_stats,
                                    strategy_name,
                                    optimization_iteration,
                                    thread_id,
                                    phase="opt"
                                )

                                if new_return >= TARGET_RETURN:
                                    thread_print("🚀🚀🚀 TARGET HIT VIA OPTIMIZATION! 🚀🚀🚀", thread_id, "green", attrs=['bold'])

                                    final_file = OPTIMIZATION_DIR / f"T{thread_id:02d}_{strategy_name}_TARGET_HIT_{new_return}pct.py"
                                    with file_lock:
                                        with open(final_file, 'w') as f:
                                            f.write(best_code)

                                    return {
                                        "success": True,
                                        "thread_id": thread_id,
                                        "strategy_name": strategy_name,
                                        "return": new_return,
                                        "target_hit": True,
                                        "optimizations": optimization_iteration
                                    }

                        # Max optimization iterations reached
                        thread_print(f"⚠️ Max optimizations reached. Best: {best_return}%", thread_id, "yellow")

                        best_file = OPTIMIZATION_DIR / f"T{thread_id:02d}_{strategy_name}_BEST_{best_return}pct.py"
                        with file_lock:
                            with open(best_file, 'w') as f:
                                f.write(best_code)

                        return {
                            "success": True,
                            "thread_id": thread_id,
                            "strategy_name": strategy_name,
                            "return": best_return,
                            "target_hit": False
                        }
            else:
                # Execution failed
                error_message = parse_execution_error(execution_result)

                error_signature = error_message.split('\n')[-1] if '\n' in error_message else error_message
                if error_signature in error_history:
                    thread_print(f"🔄 Repeated error detected - stopping", thread_id, "red")
                    return {"success": False, "error": "Repeated error", "thread_id": thread_id}

                error_history.append(error_signature)
                debug_iteration += 1

                if debug_iteration < MAX_DEBUG_ITERATIONS:
                    debugged_code = debug_backtest(
                        current_code,
                        error_message,
                        strategy_name,
                        thread_id,
                        debug_iteration
                    )

                    if not debugged_code:
                        thread_print("❌ Debug AI failed", thread_id, "red")
                        return {"success": False, "error": "Debug failed", "thread_id": thread_id}

                    current_code = debugged_code
                    # 🌙 Moon Dev: Update to match new debug file location
                    current_file = BACKTEST_DIR / f"T{thread_id:02d}_{strategy_name}_DEBUG_v{debug_iteration}.py"
                else:
                    thread_print(f"❌ Max debug iterations reached", thread_id, "red")
                    return {"success": False, "error": "Max debug iterations", "thread_id": thread_id}

        return {"success": True, "thread_id": thread_id}

    except Exception as e:
        thread_print(f"❌ FATAL ERROR: {str(e)}", thread_id, "red", attrs=['bold'])
        return {"success": False, "error": str(e), "thread_id": thread_id}

def main():
    """Main parallel processing orchestrator"""
    cprint(f"\n{'='*60}", "cyan", attrs=['bold'])
    cprint(f"🌟 Moon Dev's RBI AI v3.0 PARALLEL PROCESSOR 🚀", "cyan", attrs=['bold'])
    cprint(f"{'='*60}", "cyan", attrs=['bold'])

    cprint(f"\n📅 Date: {TODAY_DATE}", "magenta")
    cprint(f"🎯 Target Return: {TARGET_RETURN}%", "green", attrs=['bold'])
    cprint(f"🔀 Max Parallel Threads: {MAX_PARALLEL_THREADS}", "yellow", attrs=['bold'])
    cprint(f"🐍 Conda env: {CONDA_ENV}", "cyan")
    cprint(f"📂 Data dir: {DATA_DIR}", "magenta")
    cprint(f"📝 Ideas file: {IDEAS_FILE}\n", "magenta")

    if not IDEAS_FILE.exists():
        cprint("❌ ideas.txt not found! Creating template...", "red")
        IDEAS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(IDEAS_FILE, 'w') as f:
            f.write("# Add your trading ideas here (one per line)\n")
            f.write("# Can be YouTube URLs, PDF links, or text descriptions\n")
            f.write("# Lines starting with # are ignored\n\n")
            f.write("Create a simple RSI strategy that buys when RSI < 30 and sells when RSI > 70\n")
            f.write("Momentum strategy using 20/50 SMA crossover with volume confirmation\n")
        cprint(f"📝 Created template ideas.txt at: {IDEAS_FILE}", "yellow")
        cprint("💡 Add your trading ideas and run again!", "yellow")
        return

    with open(IDEAS_FILE, 'r') as f:
        ideas = [line.strip() for line in f if line.strip() and not line.startswith('#')]

    total_ideas = len(ideas)
    already_processed = sum(1 for idea in ideas if is_idea_processed(idea))
    new_ideas = total_ideas - already_processed

    cprint(f"🎯 Total ideas: {total_ideas}", "cyan")
    cprint(f"✅ Already processed: {already_processed}", "green")
    cprint(f"🆕 New to process: {new_ideas}\n", "yellow", attrs=['bold'])

    if new_ideas == 0:
        cprint("🎉 All ideas have been processed!", "green", attrs=['bold'])
        return

    # Filter out already processed ideas
    ideas_to_process = [(i, idea) for i, idea in enumerate(ideas) if not is_idea_processed(idea)]

    cprint(f"🚀 Starting parallel processing with {MAX_PARALLEL_THREADS} threads...\n", "cyan", attrs=['bold'])

    start_time = datetime.now()

    # Process ideas in parallel
    with ThreadPoolExecutor(max_workers=MAX_PARALLEL_THREADS) as executor:
        # Submit all ideas as futures with thread IDs
        futures = {
            executor.submit(process_trading_idea_parallel, idea, thread_id): (thread_id, idea)
            for thread_id, idea in ideas_to_process
        }

        # Track results
        results = []
        completed = 0

        # Process completed futures as they finish
        for future in as_completed(futures):
            thread_id, idea = futures[future]
            completed += 1

            try:
                result = future.result()
                results.append(result)

                with console_lock:
                    cprint(f"\n{'='*60}", "green")
                    cprint(f"✅ Thread {thread_id:02d} COMPLETED ({completed}/{len(futures)})", "green", attrs=['bold'])
                    if result.get('success'):
                        if result.get('target_hit'):
                            cprint(f"🎯 TARGET HIT: {result.get('strategy_name')} @ {result.get('return')}%", "green", attrs=['bold'])
                        else:
                            cprint(f"📊 Best return: {result.get('return', 'N/A')}%", "yellow")
                    else:
                        cprint(f"❌ Failed: {result.get('error', 'Unknown error')}", "red")
                    cprint(f"{'='*60}\n", "green")

            except Exception as e:
                with console_lock:
                    cprint(f"\n❌ Thread {thread_id:02d} raised exception: {str(e)}", "red", attrs=['bold'])
                results.append({"success": False, "thread_id": thread_id, "error": str(e)})

    total_time = (datetime.now() - start_time).total_seconds()

    # Final summary
    cprint(f"\n{'='*60}", "cyan", attrs=['bold'])
    cprint(f"🎉 PARALLEL PROCESSING COMPLETE!", "cyan", attrs=['bold'])
    cprint(f"{'='*60}", "cyan", attrs=['bold'])

    cprint(f"\n⏱️  Total time: {total_time:.2f}s", "magenta")
    cprint(f"📊 Ideas processed: {len(results)}", "cyan")

    successful = [r for r in results if r.get('success')]
    failed = [r for r in results if not r.get('success')]
    targets_hit = [r for r in successful if r.get('target_hit')]

    cprint(f"✅ Successful: {len(successful)}", "green")
    cprint(f"🎯 Targets hit: {len(targets_hit)}", "green", attrs=['bold'])
    cprint(f"❌ Failed: {len(failed)}", "red")

    if targets_hit:
        cprint(f"\n🚀 STRATEGIES THAT HIT TARGET {TARGET_RETURN}%:", "green", attrs=['bold'])
        for r in targets_hit:
            cprint(f"  • {r.get('strategy_name')}: {r.get('return')}%", "green")

    cprint(f"\n✨ All results saved to: {TODAY_DIR}", "cyan")
    cprint(f"{'='*60}\n", "cyan", attrs=['bold'])

if __name__ == "__main__":
    main()
