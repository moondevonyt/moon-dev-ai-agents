---
name: moon-dev-trading-agents
description: Master Moon Dev's Ai Agents Github with 48+ specialized agents, multi-exchange support, LLM abstraction, and autonomous trading capabilities across crypto markets
---

# Moon Dev's AI Trading Agents System

Expert knowledge for working with Moon Dev's experimental AI trading system that orchestrates 48+ specialized AI agents for cryptocurrency trading across Hyperliquid, Solana (BirdEye), Asterdex, and Extended Exchange.

## When to Use This Skill

Use this skill when:
- Working with Moon Dev's trading agents repository
- Need to understand agent architecture and capabilities
- Running, modifying, or creating trading agents
- Configuring trading system, exchanges, or LLM providers
- Debugging trading operations or agent interactions
- Understanding backtesting with RBI agent
- Setting up new exchanges or strategies

## Environment Setup Note

**For New Users**: This repo uses Python 3.10.9. If using conda, the README shows setting up an environment named `tflow`, but you can name it whatever you want. If you don't use conda, standard pip/venv works fine too.

## Quick Start Commands

```bash
# Activate your Python environment (conda, venv, or whatever you use)
# Example with conda: conda activate tflow
# Example with venv: source venv/bin/activate
# Use whatever environment manager you prefer

# Run main orchestrator (controls multiple agents)
python src/main.py

# Run individual agent
python src/agents/trading_agent.py
python src/agents/risk_agent.py
python src/agents/rbi_agent.py

# Update requirements after adding packages
pip freeze > requirements.txt
```

## Core Architecture

### Directory Structure

```
src/
├── agents/              # 48+ specialized AI agents (<800 lines each)
├── models/              # LLM provider abstraction (ModelFactory)
├── strategies/          # User-defined trading strategies
├── scripts/             # Standalone utility scripts
├── data/                # Agent outputs, memory, analysis results
├── config.py            # Global configuration
├── main.py              # Main orchestrator loop
├── nice_funcs.py        # Core trading utilities (~1,200 lines)
├── nice_funcs_hl.py     # Hyperliquid-specific functions
├── nice_funcs_extended.py # Extended Exchange functions
└── ezbot.py             # Legacy trading controller
```

### Key Components

**Agents** (src/agents/)
- Each agent is standalone executable
- Uses ModelFactory for LLM access
- Stores outputs in src/data/[agent_name]/
- Under 800 lines (split if longer)

**LLM Integration** (src/models/)
- ModelFactory provides unified interface
- Supports: Claude, GPT-4, DeepSeek, Groq, Gemini, Ollama
- Pattern: `ModelFactory.create_model('anthropic')`

**Trading Utilities**
- `nice_funcs.py`: Core functions (Solana/BirdEye)
- `nice_funcs_hl.py`: Hyperliquid exchange
- `nice_funcs_extended.py`: Extended Exchange (X10)

**Configuration**
- `config.py`: Trading settings, risk limits, agent behavior
- `.env`: API keys and secrets (never expose these)

## Agent Categories

**Trading**: trading_agent, strategy_agent, risk_agent, copybot_agent

**Market Analysis**: sentiment_agent, whale_agent, funding_agent, liquidation_agent, chartanalysis_agent

**Content**: chat_agent, clips_agent, tweet_agent, video_agent, phone_agent

**Research**: rbi_agent (codes backtests from videos/PDFs), research_agent, websearch_agent

**Specialized**: sniper_agent, solana_agent, tx_agent, million_agent, polymarket_agent, compliance_agent, swarm_agent

See AGENTS.md for complete list with descriptions.

## Common Workflows

### 1. Run Single Agent

```bash
# Activate your environment first
python src/agents/[agent_name].py
```

Each agent is standalone and can run independently.

### 2. Run Main Orchestrator

```bash
python src/main.py
```

Runs multiple agents in loop based on `ACTIVE_AGENTS` dict in main.py.

### 3. Change Exchange

Edit agent file or config:
```python
EXCHANGE = "hyperliquid"  # or "birdeye", "extended"
```

Then import corresponding functions:
```python
if EXCHANGE == "hyperliquid":
    from src import nice_funcs_hl as nf
elif EXCHANGE == "extended":
    from src import nice_funcs_extended as nf
```

### 4. Switch AI Model

Edit `src/config.py`:
```python
AI_MODEL = "claude-3-haiku-20240307"  # Fast, cheap
# AI_MODEL = "claude-3-sonnet-20240229"  # Balanced
# AI_MODEL = "claude-3-opus-20240229"  # Most powerful
```

Or use ModelFactory per-agent:
```python
from src.models.model_factory import ModelFactory
model = ModelFactory.create_model('deepseek')  # or 'openai', 'groq', etc.
response = model.generate_response(system_prompt, user_content, temperature, max_tokens)
```

### 5. Backtest Strategy (RBI Agent)

```python
python src/agents/rbi_agent.py
```

Provide: YouTube URL, PDF, or trading idea text
→ DeepSeek-R1 extracts strategy logic
→ Generates backtesting.py compatible code
→ Executes backtest, returns metrics

See WORKFLOWS.md for more examples.

## Development Rules

### CRITICAL Rules

1. **Keep files under 800 lines** - split into new files if longer
2. **NEVER move files** - can create new, but no moving without asking
3. **Use existing environment** - don't create new virtual environments, use the one from initial setup
4. **Update requirements.txt** after any pip install: `pip freeze > requirements.txt`
5. **Use real data only** - never synthetic/fake data
6. **Minimal error handling** - user wants to see errors, not over-engineered try/except
7. **Never expose API keys** - don't show .env contents

### Agent Development Pattern

Creating new agents:
```python
# 1. Use ModelFactory for LLM
from src.models.model_factory import ModelFactory
model = ModelFactory.create_model('anthropic')

# 2. Store outputs in src/data/
output_dir = "src/data/my_agent/"

# 3. Make independently executable
if __name__ == "__main__":
    # Standalone logic here

# 4. Follow naming: [purpose]_agent.py

# 5. Add to config.py if needed
```

### Backtesting

- Use `backtesting.py` library (NOT built-in indicators)
- Use `pandas_ta` or `talib` for indicators
- Sample data: `src/data/rbi/BTC-USD-15m.csv`

## Configuration Files

**config.py**: Trading settings
- `MONITORED_TOKENS`, `EXCLUDED_TOKENS`
- Position sizing: `usd_size`, `max_usd_order_size`
- Risk: `CASH_PERCENTAGE`, `MAX_LOSS_USD`, `MAX_GAIN_USD`
- Agent: `SLEEP_BETWEEN_RUNS_MINUTES`, `ACTIVE_AGENTS`
- AI: `AI_MODEL`, `AI_MAX_TOKENS`, `AI_TEMPERATURE`

**.env**: Secrets (NEVER expose)
- Trading APIs: `BIRDEYE_API_KEY`, `MOONDEV_API_KEY`, `COINGECKO_API_KEY`
- AI: `ANTHROPIC_KEY`, `OPENAI_KEY`, `DEEPSEEK_KEY`, `GROQ_API_KEY`, `GEMINI_KEY`
- Blockchain: `SOLANA_PRIVATE_KEY`, `HYPER_LIQUID_ETH_PRIVATE_KEY`, `RPC_ENDPOINT`
- Extended: `X10_API_KEY`, `X10_PRIVATE_KEY`, `X10_PUBLIC_KEY`, `X10_VAULT_ID`

## Exchange Support

**Hyperliquid** (`nice_funcs_hl.py`)
- EVM-compatible perpetuals DEX
- Functions: `market_buy()`, `market_sell()`, `get_position()`, `close_position()`
- Leverage up to 50x

**BirdEye/Solana** (`nice_funcs.py`)
- Solana spot token data and trading
- Functions: `token_overview()`, `token_price()`, `get_ohlcv_data()`
- Real-time market data for 15,000+ tokens

**Extended Exchange** (`nice_funcs_extended.py`)
- StarkNet-based perpetuals (X10)
- Auto symbol conversion (BTC → BTC-USD)
- Leverage up to 20x
- Functions match Hyperliquid API for compatibility

See docs/hyperliquid.md, docs/extended_exchange.md for exchange-specific guides.

## Data Flow Pattern

```
Config/Input → Agent Init → API Data Fetch → Data Parsing →
LLM Analysis (via ModelFactory) → Decision Output →
Result Storage (CSV/JSON in src/data/) → Optional Trade Execution
```

## Common Tasks

**Add new package:**
```bash
# Make sure your environment is activated first
pip install package-name
pip freeze > requirements.txt
```

**Read market data:**
```python
from src.nice_funcs import token_overview, get_ohlcv_data, token_price

overview = token_overview(token_address)
ohlcv = get_ohlcv_data(token_address, timeframe='1H', days_back=3)
price = token_price(token_address)
```

**Execute trade (Hyperliquid):**
```python
from src import nice_funcs_hl as nf
nf.market_buy("BTC", usd_amount=100, leverage=10)
position = nf.get_position("BTC")
nf.close_position("BTC")
```

**Execute trade (Extended):**
```python
from src import nice_funcs_extended as nf
nf.market_buy("BTC", usd_amount=100, leverage=15)
position = nf.get_position("BTC")
nf.close_position("BTC")
```

## Git Operations

**Current branch**: main
**Main branch for PRs**: main

**Recent commits:**
- dc55e90: websearch agent
- 921ead6: websearch_agent launched and rbi agent updated
- 6bb55c2: backtest dash

**Modified files** (current):
- .env_example
- src/agents/swarm_agent.py
- src/agents/trading_agent.py
- src/data/ohlcv_collector.py

## Documentation

**Main docs** (docs/):
- `CLAUDE.md`: Project overview and development guidelines
- `hyperliquid.md`, `hyperliquid_setup.md`: Hyperliquid exchange
- `extended_exchange.md`: Extended Exchange (X10) setup
- `rbi_agent.md`: Research-Based Inference agent
- `websearch_agent.md`: Web search capabilities
- `swarm_agent.md`: Multi-agent coordination
- `[agent_name].md`: Individual agent docs

**README files**:
- Root `README.md`: Project overview
- `src/models/README.md`: LLM provider guide

## Risk Management

- Risk Agent runs FIRST before any trading decisions
- Circuit breakers: `MAX_LOSS_USD`, `MINIMUM_BALANCE_USD`
- AI confirmation for position-closing (configurable)
- Default loop: every 15 minutes (`SLEEP_BETWEEN_RUNS_MINUTES`)

## Philosophy

This is an **experimental, educational project**:
- No guarantees of profitability
- Open source and free
- YouTube-driven development
- Community-supported via Discord
- No official token (avoid scams)

Goal: Democratize AI agent development through practical trading examples.

## Additional Resources

For complete agent list, see AGENTS.md
For workflow examples, see WORKFLOWS.md
For architecture details, see ARCHITECTURE.md

---

**Built with 🌙 by Moon Dev**

*"Never over-engineer, always ship real trading systems."*
