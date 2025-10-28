# Running the Polymarket Agent with Ollama

## ✅ Setup Complete!

Your Polymarket agent is now configured to use **Ollama** (local AI - 100% free!)

---

## Prerequisites

Before running the agent, make sure:

1. ✅ **Ollama is running** on your Linux Mint machine
   - It's already running (you got "address already in use" - that's good!)

2. ✅ **You have llama3.2 model downloaded**
   - Run: `ollama list` to check
   - If not listed, run: `ollama pull llama3.2`

---

## How to Run

### On Your Linux Mint Host Machine (NOT in Docker)

The agent needs to connect to Ollama on `localhost:11434`, so run it on your host:

```bash
# Navigate to the project directory
cd /path/to/moon-dev-ai-agents

# Activate conda environment (if you use one)
conda activate tflow

# Run the Polymarket agent
python src/agents/polymarket_agent.py
```

---

## What Will Happen

When you run it, you'll see:

```
🌙 Polymarket Prediction Market Agent
================================================================================
✅ Loaded X existing markets from CSV
✨ Successfully connected to Ollama API
📚 Available Ollama models: ['llama3.2']
📡 Fetching historical trades (last 24h)...
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

🤖 AI ANALYSIS - Analyzing 25 markets with Ollama llama3.2
```

---

## Configuration

**Current Settings** (`src/agents/polymarket_agent.py`):

```python
USE_SWARM_MODE = False       # Single model (not 6 models)
AI_MODEL_PROVIDER = "ollama"  # Using local Ollama
AI_MODEL_NAME = "llama3.2"    # Free local model
MIN_TRADE_SIZE_USD = 100      # Only track $100+ trades
```

---

## Output Files

All data saved to `src/data/polymarket/`:

- `markets.csv` - All markets with trades over $100
- `predictions.csv` - AI predictions for each analysis run

---

## Benefits of Ollama

✅ **100% Free** - No API costs ever
✅ **No Geographic Restrictions** - Works anywhere
✅ **Privacy** - Your data never leaves your machine
✅ **Fast** - Runs locally, no internet needed
✅ **No Rate Limits** - Use as much as you want

---

## Troubleshooting

**"Could not connect to Ollama API"**
- Make sure Ollama is running: `ollama serve` (might already be running)
- Check it's accessible: `curl http://localhost:11434`

**"Model llama3.2 not found"**
- Download it: `ollama pull llama3.2`
- Check installed models: `ollama list`

**WebSocket issues**
- Check your internet connection
- The agent will auto-reconnect if disconnected

---

## Next Steps

1. ✅ Make sure `ollama pull llama3.2` finished downloading
2. ✅ Run `ollama list` to confirm llama3.2 is installed
3. ✅ Run the agent: `python src/agents/polymarket_agent.py`
4. ✅ Watch it analyze Polymarket markets in real-time!

---

**Built by Moon Dev** | 100% Free Local AI Setup 🌙
