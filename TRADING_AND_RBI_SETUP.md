# Trading Agent & RBI Agent - Ollama Setup

## ✅ Configuration Complete!

Both the **Trading Agent** and **RBI Agent** are now configured to use **100% FREE local AI** via Ollama!

---

## 🤖 What's Been Configured

### 1. Trading Agent (`src/agents/trading_agent.py`)
- **AI Mode:** Single Model (fast, ~10s per token)
- **Model:** Ollama llama3.2:1b (FREE local AI)
- **Exchange:** Aster DEX (configurable)
- **Mode:** Long-only positions

### 2. RBI Agent (`src/agents/rbi_agent.py`)
- **Research:** Ollama llama3.2:1b
- **Backtesting:** Ollama llama3.2:1b
- **Debugging:** Ollama llama3.2:1b
- **Package Optimization:** Ollama llama3.2:1b

---

## 🚀 How to Use

### Prerequisites

1. **Ollama Running** - Check it's accessible:
   ```bash
   curl http://localhost:11434
   ```
   Should return: `Ollama is running`

2. **Model Downloaded** - Verify llama3.2:1b is ready:
   ```bash
   ollama list
   ```
   Should show `llama3.2:1b` in the list

3. **Virtual Environment** - Activate your venv:
   ```bash
   cd ~/Desktop/APPS/AI\ AGENTS/moon-dev-ai-agents-main
   source venv/bin/activate
   ```

---

## 📈 Using the Trading Agent

### What It Does
- Analyzes crypto markets using AI
- Makes BUY/SELL/HOLD decisions
- Executes trades on Aster DEX (or HyperLiquid/Solana)
- Uses local Ollama for all AI decisions (100% free!)

### How to Run

```bash
# Navigate to project
cd ~/Desktop/APPS/AI\ AGENTS/moon-dev-ai-agents-main

# Activate virtual environment
source venv/bin/activate

# Run the trading agent
python src/agents/trading_agent.py
```

### Configuration Options

Edit `src/agents/trading_agent.py` (lines 84-114):

```python
# Exchange Selection
EXCHANGE = "ASTER"  # Options: "ASTER", "HYPERLIQUID", "SOLANA"

# AI Mode
USE_SWARM_MODE = False  # False = Single Ollama model (fast & free)
                        # True = 6-model consensus (requires API keys)

# Model Settings
AI_MODEL_TYPE = 'ollama'
AI_MODEL_NAME = 'llama3.2:1b'  # Fast & lightweight!

# Trading Mode
LONG_ONLY = True  # True = Long positions only
                  # False = Long & Short (Aster/HyperLiquid only)

# Position Sizing
MAX_POSITION_PERCENTAGE = 90  # % of balance to use per position
LEVERAGE = 9  # Leverage multiplier (Aster/HyperLiquid only)
```

### Tokens to Trade

Edit the token list (lines 145-160):

```python
MONITORED_TOKENS = [
    'BTC',   # Bitcoin
    'ETH',   # Ethereum
    'SOL',   # Solana
    # Add more tokens here
]
```

---

## 🔬 Using the RBI Agent

### What It Does
1. **Research:** Takes YouTube videos, PDFs, or text about trading strategies
2. **Backtest:** Automatically codes and runs backtests
3. **Debug:** Fixes errors in generated code
4. **Optimize:** Improves strategy performance

All using **FREE local AI** - no API costs!

### Setup

Create the ideas file:
```bash
# Create ideas.txt if it doesn't exist
mkdir -p src/data/rbi
nano src/data/rbi/ideas.txt
```

Add trading ideas (one per line):
```
https://youtube.com/watch?v=xyz123  # YouTube strategy video
/path/to/strategy.pdf               # PDF document
Moving average crossover with RSI   # Text description
```

Lines starting with `#` are ignored (comments).

### How to Run

```bash
# Navigate to project
cd ~/Desktop/APPS/AI\ AGENTS/moon-dev-ai-agents-main

# Activate virtual environment
source venv/bin/activate

# Run the RBI agent
python src/agents/rbi_agent.py
```

### What Happens

The agent will:
1. Read ideas from `ideas.txt`
2. Research each strategy
3. Generate backtest code
4. Run backtests on historical data
5. Save results to `src/data/rbi/MM_DD_YYYY/`

### Output Structure

```
src/data/rbi/
└── MM_DD_YYYY/              # Today's date folder
    ├── research/            # Strategy research
    ├── backtests/           # Initial backtest code
    ├── backtests_final/     # Debugged code
    └── execution_results/   # Backtest results (JSON)
```

---

## 💰 Cost Breakdown

| Agent | AI Provider | Model | Cost Per Run |
|-------|-------------|-------|--------------|
| **Trading Agent** | Ollama (Local) | llama3.2:1b | **$0.00** |
| **RBI Agent** | Ollama (Local) | llama3.2:1b | **$0.00** |
| **Polymarket Agent** | Ollama (Local) | llama3.2 | **$0.00** |

**Total:** **$0.00 forever!** 🎉

---

## ⚙️ Advanced Configuration

### Use Different Ollama Models

If you have other models downloaded:

**Trading Agent** (edit `src/agents/trading_agent.py`):
```python
AI_MODEL_NAME = 'llama3.2'      # 2GB model (more powerful)
# OR
AI_MODEL_NAME = 'deepseek-r1:7b' # 4GB reasoning model
# OR
AI_MODEL_NAME = 'qwen3:8b'       # 4GB fast inference
```

**RBI Agent** (edit `src/agents/rbi_agent.py`):
```python
RESEARCH_CONFIG = {"type": "ollama", "name": "llama3.2"}
BACKTEST_CONFIG = {"type": "ollama", "name": "deepseek-r1:7b"}
DEBUG_CONFIG = {"type": "ollama", "name": "llama3.2"}
```

### Enable Swarm Mode (Trading Agent)

Requires API keys but gives better consensus:

```python
USE_SWARM_MODE = True  # Enable 6-model voting
```

You'll need:
- Claude API key (paid)
- OpenAI API key (paid)
- Groq API key (free)
- etc.

---

## 🐛 Troubleshooting

**"Could not connect to Ollama API"**
```bash
# Check if Ollama is running
curl http://localhost:11434

# If not, start it
ollama serve
```

**"Model llama3.2:1b not found"**
```bash
# Download the model
ollama pull llama3.2:1b

# Verify it's installed
ollama list
```

**"No module named 'X'"**
```bash
# Install missing dependencies
pip install -r requirements.txt
```

**Trading Agent doesn't execute trades**
- Check you have API keys configured in `.env`
- Check exchange is properly configured
- Check you have sufficient balance
- Review logs for errors

**RBI Agent errors during backtest**
- Check you have sample data in `src/data/rbi/`
- Verify the strategy description is clear
- Try simpler strategies first
- Check generated code in `backtests/` folder

---

## 📊 Performance Notes

### llama3.2:1b Performance
- **Speed:** Very fast (~5-10s per decision)
- **Quality:** Good for basic strategies
- **Size:** Only 1.3GB (lightweight!)

### When to Upgrade Models

Consider using larger models if:
- Strategies are complex
- Need deeper reasoning
- Want higher accuracy
- Have 4-8GB RAM to spare

**Better free models:**
```bash
ollama pull llama3.2        # 2GB - More powerful
ollama pull deepseek-r1:7b  # 4GB - Best reasoning
ollama pull qwen3:8b        # 4GB - Fast & accurate
```

---

## ⚠️ Important Disclaimers

1. **Trading involves risk** - Only trade what you can afford to lose
2. **Past performance ≠ future results** - Backtests don't guarantee profits
3. **Test thoroughly** - Paper trade before using real money
4. **Start small** - Use small position sizes when learning
5. **No guarantees** - AI can be wrong, markets are unpredictable

---

## 🎯 Next Steps

1. ✅ Verify llama3.2:1b is downloaded
2. ✅ Test Trading Agent with small positions
3. ✅ Create ideas.txt for RBI Agent
4. ✅ Run sample backtests
5. ✅ Monitor performance and adjust

---

**Built with ❤️ using 100% FREE local AI!** 🌙🚀

No API costs, no geographic restrictions, complete privacy.
