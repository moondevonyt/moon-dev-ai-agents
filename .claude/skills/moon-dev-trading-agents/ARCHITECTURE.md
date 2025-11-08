# System Architecture

Deep dive into Moon Dev's AI trading system architecture.

---

## High-Level Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Main Orchestrator                     │
│                    (src/main.py)                        │
└───────────┬─────────────────────────────────┬───────────┘
            │                                 │
            ▼                                 ▼
    ┌──────────────┐                 ┌──────────────┐
    │ Risk Agent   │ ◄───────────────┤ Active Agents │
    │ (runs first) │                 │  Trading      │
    └──────┬───────┘                 │  Sentiment    │
           │                         │  Whale        │
           │                         │  RBI          │
           ▼                         │  etc...       │
    ┌──────────────┐                └───────┬───────┘
    │ Risk OK?     │                        │
    │ Circuit      │                        │
    │ Breakers     │                        ▼
    └──────┬───────┘              ┌─────────────────┐
           │                      │  ModelFactory   │
           │                      │  (LLM Provider) │
           │                      └────────┬────────┘
           │                               │
           ▼                               │
    ┌─────────────────────────────────────┴────────┐
    │           Exchange Layer                      │
    │  ┌──────────┐  ┌──────────┐  ┌─────────┐   │
    │  │Hyperliquid│  │ BirdEye  │  │Extended │   │
    │  │  (HL)     │  │ (Solana) │  │  (X10)  │   │
    │  └──────────┘  └──────────┘  └─────────┘   │
    └───────────────────────────────────────────────┘
```

---

## Core Components

### 1. Main Orchestrator (main.py)

**Purpose**: Coordinates multiple agents in infinite loop

**Flow**:
1. Load configuration from config.py
2. Check ACTIVE_AGENTS dict
3. Run risk_agent first (always)
4. If risk checks pass, run active agents
5. Sleep SLEEP_BETWEEN_RUNS_MINUTES
6. Repeat

**Key Features**:
- Graceful shutdown on Ctrl+C
- Error handling per agent
- Agent independence (one failure doesn't stop others)
- Configurable agent activation

**Code Pattern**:
```python
while True:
    try:
        # Risk checks first
        if ACTIVE_AGENTS.get("risk_agent"):
            risk_result = run_risk_agent()
            if not risk_result['ok']:
                continue  # Skip trading if risk violated

        # Run other active agents
        for agent_name, is_active in ACTIVE_AGENTS.items():
            if is_active and agent_name != "risk_agent":
                run_agent(agent_name)

        time.sleep(SLEEP_BETWEEN_RUNS_MINUTES * 60)
    except KeyboardInterrupt:
        break
```

---

### 2. Agent Architecture

**Agent Types**:
- **Autonomous**: Run independently, make decisions
- **Data Collectors**: Fetch and store market data
- **Analyzers**: Process data, generate insights
- **Executors**: Execute trades based on signals

**Agent Lifecycle**:
```
Initialize → Load Config → Fetch Data → AI Analysis →
Generate Output → Store Results → (Optional) Execute Trade
```

**Common Agent Structure**:
```python
# 1. Imports
from src.models.model_factory import ModelFactory
from termcolor import cprint
import os

# 2. Configuration
OUTPUT_DIR = "src/data/agent_name/"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 3. Main function
def main():
    # Initialize model
    model = ModelFactory.create_model('anthropic')

    # Fetch data
    data = fetch_market_data()

    # AI analysis
    analysis = model.generate_response(system_prompt, user_content)

    # Store results
    save_results(OUTPUT_DIR, analysis)

    # Optional: Execute trade
    execute_trade_if_needed()

# 4. Entry point
if __name__ == "__main__":
    main()
```

**Agent Independence**:
- Each agent is self-contained
- Can run standalone or via orchestrator
- Shared utilities via nice_funcs.py
- No inter-agent dependencies (except risk_agent)

---

### 3. LLM Provider Abstraction (ModelFactory)

**Location**: `src/models/`

**Purpose**: Unified interface for multiple LLM providers

**Architecture**:
```
ModelFactory
├── BaseModel (abstract class)
│   ├── generate_response()
│   ├── generate_structured_output()
│   └── get_model_info()
│
├── AnthropicModel (Claude)
├── OpenAIModel (GPT-4)
├── DeepSeekModel (DeepSeek-R1, V3)
├── GroqModel (Fast inference)
├── GeminiModel (Google)
└── OllamaModel (Local models)
```

**Usage Pattern**:
```python
# Create model instance
model = ModelFactory.create_model('anthropic')  # or any provider

# Generate response (unified interface)
response = model.generate_response(
    system_prompt="You are a trading analyst",
    user_content="Analyze BTC market",
    temperature=0.3,
    max_tokens=2000
)

# All providers implement same interface
# Switch providers by changing one line
```

**Benefits**:
- Provider-agnostic code
- Easy A/B testing
- Cost optimization (use cheap models for simple tasks)
- Fallback options if one provider is down

**Provider Selection Strategy**:
- **Claude Sonnet**: Default, balanced quality/cost
- **Claude Haiku**: Fast, cheap, simple tasks
- **Claude Opus**: Complex reasoning, expensive
- **DeepSeek-R1**: Deep reasoning, very cheap
- **Groq**: Ultra-fast inference
- **Ollama**: Local, no API costs

---

### 4. Exchange Layer

**Three Exchange Integrations**:

#### Hyperliquid (nice_funcs_hl.py)
- **Type**: EVM-compatible perpetuals DEX
- **Blockchain**: Custom L1
- **Assets**: BTC, ETH, SOL, 50+ pairs
- **Leverage**: Up to 50x
- **API**: REST + WebSocket
- **Key Functions**:
  - `market_buy()`, `market_sell()`
  - `get_position()`, `close_position()`
  - `chunk_kill()` (maker orders)
  - `get_account_balance()`

#### BirdEye (nice_funcs.py)
- **Type**: Solana token data + spot trading
- **Blockchain**: Solana
- **Assets**: 15,000+ Solana tokens
- **Leverage**: None (spot only)
- **API**: REST
- **Key Functions**:
  - `token_overview()`, `token_price()`
  - `get_ohlcv_data()` (historical)
  - `get_token_security()` (rug check)

#### Extended Exchange (nice_funcs_extended.py)
- **Type**: StarkNet perpetuals DEX
- **Blockchain**: StarkNet L2
- **Assets**: BTC-USD, ETH-USD, SOL-USD
- **Leverage**: Up to 20x
- **API**: REST + SDK (async)
- **Key Functions**:
  - Same as Hyperliquid (API compatibility)
  - Auto symbol conversion (BTC → BTC-USD)
  - `format_symbol_for_extended()`

**Unified Trading Interface**:
All three exchanges implement same function signatures:
```python
# Works with all exchanges
nf.market_buy(symbol, usd_amount, leverage)
nf.get_position(symbol)
nf.close_position(symbol)
nf.get_account_balance()
```

**Exchange Selection**:
```python
# In agent code
EXCHANGE = "hyperliquid"  # or "birdeye", "extended"

if EXCHANGE == "hyperliquid":
    from src import nice_funcs_hl as nf
elif EXCHANGE == "extended":
    from src import nice_funcs_extended as nf
elif EXCHANGE == "birdeye":
    from src import nice_funcs as nf
```

---

### 5. Configuration Management

**Two-Layer Config**:

#### Layer 1: config.py (Trading Settings)
```python
# Monitored assets
MONITORED_TOKENS = ["BTC", "ETH", "SOL"]
EXCLUDED_TOKENS = ["SCAM", "RUG"]

# Position sizing
usd_size = 100
max_usd_order_size = 500

# Risk limits
CASH_PERCENTAGE = 10
MAX_POSITION_PERCENTAGE = 50
MAX_LOSS_USD = 500
MAX_GAIN_USD = 2000
MINIMUM_BALANCE_USD = 100

# Agent behavior
SLEEP_BETWEEN_RUNS_MINUTES = 15

# AI settings
AI_MODEL = "claude-3-sonnet-20240229"
AI_MAX_TOKENS = 4000
AI_TEMPERATURE = 0.3
```

#### Layer 2: .env (Secrets)
```bash
# AI Providers
ANTHROPIC_KEY=sk-ant-...
OPENAI_KEY=sk-...
DEEPSEEK_KEY=...
GROQ_API_KEY=...

# Trading APIs
BIRDEYE_API_KEY=...
MOONDEV_API_KEY=...

# Exchanges
HYPER_LIQUID_ETH_PRIVATE_KEY=0x...
X10_API_KEY=...
X10_PRIVATE_KEY=0x...

# Blockchain
SOLANA_PRIVATE_KEY=...
RPC_ENDPOINT=https://...
```

**Loading Pattern**:
```python
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("BIRDEYE_API_KEY")
```

---

### 6. Data Flow Architecture

**Request Flow**:
```
User/Scheduler
    ↓
Main Orchestrator (main.py)
    ↓
Risk Agent (circuit breaker check)
    ↓
Active Agents (parallel execution possible)
    ↓
ModelFactory → LLM Provider
    ↓
Exchange API (Hyperliquid/BirdEye/Extended)
    ↓
Blockchain/Market
```

**Response Flow**:
```
Market Data (OHLCV, positions, balance)
    ↓
Exchange API Response
    ↓
Agent Processing (nice_funcs.py)
    ↓
LLM Analysis (ModelFactory)
    ↓
Decision Output
    ↓
Result Storage (src/data/agent_name/)
    ↓
Optional: Trade Execution
```

**Data Storage Pattern**:
```
src/data/
├── agent_name/
│   ├── latest_analysis.json
│   ├── decisions.csv
│   └── historical_trades.csv
└── shared/
    └── market_cache/
```

---

### 7. Risk Management Layer

**Risk-First Architecture**:

Risk agent ALWAYS runs before trading:
```python
# In main.py
risk_result = run_risk_agent()

if not risk_result['ok']:
    cprint("⚠️  Risk checks failed, skipping trading", "yellow")
    continue  # Skip this loop iteration
```

**Risk Checks**:
1. **Account Balance Check**:
   - Current balance > MINIMUM_BALANCE_USD?
   - If not: Stop all trading

2. **Loss Limit Check**:
   - Total loss today > MAX_LOSS_USD?
   - If yes: Close positions, stop trading

3. **Gain Target Check**:
   - Total gain today > MAX_GAIN_USD?
   - If yes: Close positions, take profit

4. **Position Size Check**:
   - Position size < MAX_POSITION_PERCENTAGE of account?
   - If not: Reduce position

5. **Exposure Check**:
   - Total exposure across all positions reasonable?
   - Cash percentage maintained?

**Circuit Breaker Pattern**:
```python
if current_balance < MINIMUM_BALANCE_USD:
    close_all_positions()
    send_alert("CRITICAL: Balance too low")
    sys.exit(1)

if daily_loss > MAX_LOSS_USD:
    close_all_positions()
    send_alert("WARNING: Max loss exceeded")
    pause_trading_for_today()
```

---

### 8. Backtesting Infrastructure

**RBI Agent Architecture** (Research-Based Inference):

```
User Input (YouTube/PDF/Text)
    ↓
DeepSeek-R1 (strategy extraction)
    ↓
Strategy Code Generation (backtesting.py format)
    ↓
Code Runner Agent (sandboxed execution)
    ↓
Backtest Execution (historical data)
    ↓
Performance Metrics (Sharpe, drawdown, etc.)
    ↓
Results Output (CSV + visualization)
```

**Backtesting Stack**:
- **Library**: backtesting.py (Python backtesting framework)
- **Indicators**: pandas_ta, talib (NOT backtesting.py built-ins)
- **Data**: Historical OHLCV from BirdEye API
- **Sample Data**: `src/data/rbi/BTC-USD-15m.csv`

**Strategy Format**:
```python
from backtesting import Strategy
import pandas_ta as ta

class MyStrategy(Strategy):
    def init(self):
        # Calculate indicators
        self.rsi = self.I(ta.rsi, pd.Series(self.data.Close), 14)

    def next(self):
        # Trading logic
        if self.rsi[-1] < 30:
            self.buy()
        elif self.rsi[-1] > 70:
            self.sell()
```

---

### 9. Agent Communication

**Current Architecture**: No direct inter-agent communication

**Data Sharing**:
- Agents write to `src/data/[agent_name]/`
- Other agents can read from those directories
- No shared memory or message passing

**Future Architecture** (via swarm_agent.py):
- Agent coordination layer
- Task distribution
- Result aggregation
- Shared context management

---

### 10. Error Handling Philosophy

**Moon Dev's Approach**: Minimal error handling

**Rationale**:
- See errors immediately
- Avoid hiding bugs
- Fail fast, fix fast
- No over-engineering

**Pattern**:
```python
# ❌ NOT THIS (over-engineered)
try:
    result = api_call()
except Exception as e:
    log.error(f"Error: {e}")
    return None

# ✅ DO THIS (fail fast)
result = api_call()  # Let it crash if it fails
```

**Exceptions**:
- Network calls (retries acceptable)
- User input (validation acceptable)
- Critical operations (position closing)

---

### 11. Scalability Considerations

**Current Scale**:
- 48+ agents
- 3 exchanges
- 6 LLM providers
- 15,000+ tokens tracked
- ~1,200 lines of shared utilities

**Performance Optimizations**:
- Agent independence (parallel execution possible)
- Lazy loading (only load what's needed)
- Result caching (avoid redundant API calls)
- ModelFactory (cheap models for simple tasks)

**Future Scaling**:
- Message queue for inter-agent communication
- Database for historical data (vs CSV)
- Load balancing across multiple instances
- Rate limit management per exchange

---

### 12. Security Architecture

**API Key Management**:
- All keys in `.env` (never committed)
- `load_dotenv()` at startup
- No hardcoded secrets

**Private Key Storage**:
- Ethereum private keys for Hyperliquid
- StarkNet keys for Extended
- Solana keys for on-chain operations
- Encrypted at rest (user's responsibility)

**Network Security**:
- HTTPS for all API calls
- WebSocket over WSS
- No credentials in logs
- No credentials shown in terminal output

**Agent Security**:
- Code execution sandboxed (RBI agent)
- No eval() of user input
- Input validation where needed

---

## System Characteristics

**Strengths**:
- Modular agent architecture
- Multi-exchange support
- Provider-agnostic LLM layer
- Risk-first approach
- Standalone agent execution

**Trade-offs**:
- No inter-agent communication (intentional)
- Minimal error handling (by design)
- CSV-based storage (simple, not scalable)
- No built-in backtesting UI

**Design Philosophy**:
> "Never over-engineer, always ship real trading systems."
>
> — Moon Dev

---

**Built with 🌙 by Moon Dev**

*Architecture for experimental AI trading at scale.*
