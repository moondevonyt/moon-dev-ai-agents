# Common Development Workflows

Practical examples for working with Moon Dev's trading system.

---

## Environment Setup

### Initial Setup

```bash
# Activate conda environment (NEVER create new venv!)
# Activate your environment (e.g., conda activate your_env_name)

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env_example .env
# Edit .env with your API keys
```

### Adding New Package

```bash
# Activate your environment (e.g., conda activate your_env_name)
pip install package-name
pip freeze > requirements.txt  # CRITICAL: Always update!
```

---

## Running Agents

### Run Single Agent

```bash
# Activate environment
# Activate your environment (e.g., conda activate your_env_name)

# Run any agent standalone
python src/agents/trading_agent.py
python src/agents/risk_agent.py
python src/agents/sentiment_agent.py
python src/agents/rbi_agent.py
```

### Run Main Orchestrator

```bash
# Run multiple agents in loop
python src/main.py
```

Configure which agents run in `main.py`:
```python
ACTIVE_AGENTS = {
    "risk_agent": True,        # Always first
    "trading_agent": True,
    "sentiment_agent": False,  # Disabled
    "whale_agent": True,
}
```

---

## Exchange Configuration

### Switch Exchange in Trading Agent

Edit `src/agents/trading_agent.py`:

```python
# Exchange Configuration - Line ~20
EXCHANGE = "hyperliquid"  # Options: "hyperliquid", "birdeye", "extended"

# Import corresponding functions
if EXCHANGE == "hyperliquid":
    from src import nice_funcs_hl as nf
elif EXCHANGE == "extended":
    from src import nice_funcs_extended as nf
elif EXCHANGE == "birdeye":
    from src import nice_funcs as nf
```

### Test Exchange Connection

**Hyperliquid:**
```python
from src import nice_funcs_hl as hl

# Get balance
balance = hl.get_account_balance()
print(f"Balance: {balance['equity']}")

# Get position
position = hl.get_position("BTC")
if position:
    print(f"Position: {position['position_amount']}")
```

**Extended Exchange:**
```bash
# Run comprehensive test
python src/scripts/test_extended.py

# Debug position issues
python src/scripts/debug_extended_position.py
```

**BirdEye (Solana):**
```python
from src import nice_funcs as nf

# Get token data
token_addr = "your_token_address"
overview = nf.token_overview(token_addr)
price = nf.token_price(token_addr)
```

---

## AI Model Configuration

### Switch Default Model

Edit `src/config.py`:

```python
# AI Configuration
AI_MODEL = "claude-3-haiku-20240307"    # Fast, cheap
# AI_MODEL = "claude-3-sonnet-20240229"  # Balanced (recommended)
# AI_MODEL = "claude-3-opus-20240229"    # Most powerful, expensive

AI_MAX_TOKENS = 4000
AI_TEMPERATURE = 0.3
```

### Use Different Model Per Agent

```python
from src.models.model_factory import ModelFactory

# Use Claude for reasoning
claude = ModelFactory.create_model('anthropic')
response = claude.generate_response(
    system_prompt="You are a trading analyst",
    user_content="Analyze BTC",
    temperature=0.3,
    max_tokens=2000
)

# Use DeepSeek for cheap inference
deepseek = ModelFactory.create_model('deepseek')
response = deepseek.generate_response(system_prompt, user_content)

# Use Groq for speed
groq = ModelFactory.create_model('groq')
response = groq.generate_response(system_prompt, user_content)
```

### Available Providers

```python
ModelFactory.create_model('anthropic')  # Claude (default)
ModelFactory.create_model('openai')     # GPT-4
ModelFactory.create_model('deepseek')   # DeepSeek-R1, V3
ModelFactory.create_model('groq')       # Fast inference
ModelFactory.create_model('gemini')     # Google Gemini
ModelFactory.create_model('ollama')     # Local models
```

---

## Backtesting Strategies

### Using RBI Agent (Recommended)

```bash
# Activate your environment (e.g., conda activate your_env_name)
python src/agents/rbi_agent.py
```

**Workflow:**
1. Agent prompts: "Provide YouTube URL, PDF path, or describe strategy"
2. You provide input (e.g., YouTube link to trading tutorial)
3. DeepSeek-R1 extracts strategy logic
4. Generates backtesting.py compatible code
5. Executes backtest with sample data
6. Returns performance metrics

**Sample Input:**
- YouTube: `https://youtube.com/watch?v=...` (trading strategy video)
- PDF: `/path/to/strategy.pdf`
- Text: "RSI oversold strategy with 30/70 thresholds on 1H timeframe"

**Output:** Backtest results with Sharpe ratio, max drawdown, win rate, etc.

### Manual Backtesting

```python
from backtesting import Backtest, Strategy
import pandas_ta as ta
import pandas as pd

# Load sample data
df = pd.read_csv("src/data/rbi/BTC-USD-15m.csv")
df['Date'] = pd.to_datetime(df['Date'])
df.set_index('Date', inplace=True)

# Define strategy
class MyStrategy(Strategy):
    def init(self):
        # Calculate indicators using pandas_ta
        self.rsi = self.I(ta.rsi, pd.Series(self.data.Close), length=14)

    def next(self):
        if self.rsi[-1] < 30:  # Oversold
            self.buy()
        elif self.rsi[-1] > 70:  # Overbought
            self.sell()

# Run backtest
bt = Backtest(df, MyStrategy, cash=10000, commission=.002)
stats = bt.run()
print(stats)
bt.plot()
```

**IMPORTANT:**
- Use `pandas_ta` or `talib` for indicators (NOT backtesting.py built-ins)
- Sample data available: `src/data/rbi/BTC-USD-15m.csv`

---

## Trading Workflows

### Execute Manual Trade (Hyperliquid)

```python
from src import nice_funcs_hl as nf

# Market buy $100 BTC with 10x leverage
nf.market_buy("BTC", usd_amount=100, leverage=10)

# Check position
position = nf.get_position("BTC")
print(f"Entry: ${position['entry_price']:,.2f}")
print(f"PnL: {position['pnl_percentage']:.2f}%")

# Close position
nf.close_position("BTC")
```

### Execute Manual Trade (Extended)

```python
from src import nice_funcs_extended as nf

# Market buy $100 BTC with 15x leverage
nf.market_buy("BTC", usd_amount=100, leverage=15)

# Check position (auto-converts BTC to BTC-USD)
position = nf.get_position("BTC")
print(f"Size: {position['position_amount']}")
print(f"PnL: {position['pnl_percentage']:.2f}%")

# Close with maker orders (chunk_kill)
nf.chunk_kill("BTC")
```

### Monitor Positions

```python
from src import nice_funcs_hl as nf

# Get all positions
symbols = ["BTC", "ETH", "SOL"]
for symbol in symbols:
    position = nf.get_position(symbol)
    if position and position['position_amount'] != 0:
        print(f"{symbol}: {position['position_amount']} @ ${position['entry_price']:,.2f}")
        print(f"  PnL: {position['pnl_percentage']:.2f}%")
```

---

## Creating Custom Strategy

### Method 1: Strategy Class

Create `src/strategies/my_strategy.py`:

```python
"""
🌙 Moon Dev's Custom Strategy
"""

from src.strategies.base_strategy import BaseStrategy

class MyStrategy(BaseStrategy):
    name = "my_strategy"
    description = "My custom trading strategy"

    def generate_signals(self, token_address, market_data):
        """
        Generate trading signals

        Returns:
            {
                "action": "BUY" | "SELL" | "NOTHING",
                "confidence": 0-100,
                "reasoning": "Explanation"
            }
        """
        # Your logic here
        if market_data['price'] < market_data['support']:
            return {
                "action": "BUY",
                "confidence": 85,
                "reasoning": "Price below support level"
            }

        return {
            "action": "NOTHING",
            "confidence": 0,
            "reasoning": "No signal"
        }
```

Use with strategy_agent:
```python
python src/agents/strategy_agent.py
```

### Method 2: Custom Agent

Create `src/agents/my_custom_agent.py`:

```python
"""
🌙 Moon Dev's Custom Trading Agent
"""

from src.models.model_factory import ModelFactory
from src import nice_funcs_hl as nf
from termcolor import cprint
import os

OUTPUT_DIR = "src/data/my_custom_agent/"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def main():
    cprint("🌙 Moon Dev's Custom Agent starting...", "cyan")

    # Initialize AI model
    model = ModelFactory.create_model('anthropic')

    # Get market data
    position = nf.get_position("BTC")

    # Prepare prompt
    system_prompt = "You are a trading analyst"
    user_content = f"Current BTC position: {position}"

    # Get AI analysis
    response = model.generate_response(
        system_prompt,
        user_content,
        temperature=0.3,
        max_tokens=1000
    )

    cprint(f"Analysis: {response}", "white")

    # Execute trade if needed
    # nf.market_buy("BTC", 100, leverage=10)

    # Save results
    with open(f"{OUTPUT_DIR}/analysis.txt", "w") as f:
        f.write(response)

    cprint("✅ Agent complete!", "green")

if __name__ == "__main__":
    main()
```

Run:
```bash
python src/agents/my_custom_agent.py
```

---

## Data Collection

### Get OHLCV Data (BirdEye)

```python
from src.nice_funcs import get_ohlcv_data

# Get 3 days of 1H candles
token_addr = "your_token_address"
ohlcv = get_ohlcv_data(token_addr, timeframe='1H', days_back=3)

# Returns DataFrame with: open, high, low, close, volume
print(ohlcv.head())
```

### Get Token Overview (BirdEye)

```python
from src.nice_funcs import token_overview

overview = token_overview(token_addr)
print(f"Price: ${overview['price']}")
print(f"Volume 24h: ${overview['volume24h']}")
print(f"Liquidity: ${overview['liquidity']}")
```

### Get Liquidation Data (Moon Dev API)

```python
from src.agents.api import MoonDevAPI

api = MoonDevAPI()

# Get liquidations for BTC
liq_data = api.get_liquidation_data("BTC")
print(f"Total liquidations: ${liq_data['total']:,.0f}")
```

---

## Risk Management

### Check Risk Before Trading

```bash
# Run risk agent first
python src/agents/risk_agent.py
```

Risk agent checks:
- Current P&L vs MAX_LOSS_USD
- Account balance vs MINIMUM_BALANCE_USD
- Position size vs MAX_POSITION_PERCENTAGE
- Daily/weekly loss limits

### Configure Risk Limits

Edit `src/config.py`:

```python
# Risk Management
MAX_LOSS_USD = 500          # Stop trading if loss exceeds
MAX_GAIN_USD = 2000         # Take profit if gain exceeds
MINIMUM_BALANCE_USD = 100   # Stop trading if balance below
MAX_POSITION_PERCENTAGE = 50 # Max % of account per position
CASH_PERCENTAGE = 10        # Keep % in cash
```

### Force Close All Positions

```python
from src import nice_funcs_hl as nf

# Emergency close all
symbols = ["BTC", "ETH", "SOL"]
for symbol in symbols:
    position = nf.get_position(symbol)
    if position and position['position_amount'] != 0:
        nf.close_position(symbol)
        print(f"✅ Closed {symbol}")
```

---

## Debugging

### Check Agent Output

Agents save outputs to `src/data/[agent_name]/`:

```bash
# View latest risk report
cat src/data/risk_agent/latest_report.txt

# View trading decisions
cat src/data/trading_agent/decisions.csv

# View RBI backtest results
ls src/data/rbi_agent/
```

### Test Exchange Connectivity

```python
# Hyperliquid
from src import nice_funcs_hl as hl
balance = hl.get_account_balance()
print(f"Connected! Balance: ${balance['equity']:,.2f}")

# Extended
from src import nice_funcs_extended as ex
balance = ex.get_account_balance()
print(f"Connected! Balance: ${balance['equity']:,.2f}")
```

### View Logs

Agents use colored terminal output (termcolor):
- Green: Success
- Yellow: Warnings
- Red: Errors
- Cyan: Info

---

## Git Workflow

### Commit Changes

```bash
# Check status
git status

# Stage changes
git add src/agents/my_new_agent.py

# Commit
git commit -m "Added my new agent"

# Push to main
git push origin main
```

### Revert File to Last Commit

```bash
# Revert specific file
git checkout HEAD -- src/agents/trading_agent.py

# Verify
git status
```

---

## Production Deployment

### Run Main Loop in Background

```bash
# Activate your environment (e.g., conda activate your_env_name)

# Run with nohup
nohup python src/main.py > trading.log 2>&1 &

# View logs
tail -f trading.log

# Stop
pkill -f main.py
```

### Monitor Active Agents

```bash
# Check running processes
ps aux | grep python | grep agents

# Monitor system resources
htop
```

---

## Common Issues

**"Module not found":**
```bash
# Activate your environment (e.g., conda activate your_env_name)
pip install missing-module
pip freeze > requirements.txt
```

**"API key not found":**
- Check `.env` file has required keys
- Verify key names match (ANTHROPIC_KEY, OPENAI_KEY, etc.)

**"Invalid quantity":**
- Position size too small for asset
- Increase USD amount or check minimum sizes

**"Position not found":**
- Verify symbol format (use "BTC" not "BTCUSD")
- Check exchange is correct (Hyperliquid vs Extended)

---

**Built with 🌙 by Moon Dev**

*Workflows for shipping real trading systems.*
