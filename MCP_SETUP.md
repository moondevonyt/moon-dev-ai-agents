# 🌙 MCP Integration Setup Guide

## What is MCP?

**MCP (Model Context Protocol)** allows your Research Agent to fetch **real-time market data** from the web, forums, YouTube, and deep research tools before generating trading strategies.

Instead of generating strategies blindly, the AI now:
1. **Researches** current market conditions via MCP
2. **Analyzes** liquidations, funding rates, volatility, sentiment
3. **Generates** strategies tailored to **actual market conditions**

---

## Quick Start

### 1. Install NPM (if not already installed)

```bash
# Check if npm is installed
npm --version

# If not, install Node.js from https://nodejs.org/
```

### 2. Test MCP Connection (No API Key Required)

The default setup uses `@baranwang/mcp-deep-research` which works **without API keys** for basic research:

```bash
npx -y @smithery/cli@latest run @baranwang/mcp-deep-research
```

If this runs without errors, you're good to go!

### 3. Enable MCP in Research Agent

Open `src/agents/research_agent.py` and verify:

```python
MCP_ENABLED = True  # ✅ Should be True
```

### 4. Start Research Agent

```bash
python3 src/agents/research_agent.py
```

You should see:
```
🌍 Fetching live market context via MCP...
🔍 Using tool: deep_research
✅ Market context fetched (1234 chars)
```

---

## Advanced: Using API Keys (Optional)

Some MCP servers offer enhanced features with API keys.

### Option A: Environment Variables (Recommended)

```bash
# Add to ~/.zshrc or ~/.bashrc
export SMITHERY_KEY="your-key-here"
export SMITHERY_PROFILE="your-profile-here"
```

Then uncomment in `research_agent.py`:

```python
SMITHERY_CONFIG = {
    "command": "npx",
    "args": [
        "-y",
        "@smithery/cli@latest",
        "run",
        "@baranwang/mcp-deep-research",
        "--key", os.getenv("SMITHERY_KEY", ""),  # ✅ Uncomment
        "--profile", os.getenv("SMITHERY_PROFILE", ""),  # ✅ Uncomment
    ],
    "timeout": 30
}
```

### Option B: Hardcode (Not Recommended for Git)

```python
"--key", "your-key-here",
"--profile", "your-profile-here",
```

---

## Customizing Research Queries

Edit the `RESEARCH_QUERY` in `research_agent.py`:

```python
RESEARCH_QUERY = """
Analyze the crypto trading landscape in the last 24-48 hours:
1. Notable liquidation events (BTC/ETH/SOL)
2. Funding rate anomalies
3. Volume spikes
4. Volatility changes
5. Technical breakouts
6. Sentiment shifts

Focus on ACTIONABLE insights.
"""
```

---

## Disabling MCP

If you want to turn off web research:

```python
MCP_ENABLED = False  # In research_agent.py
```

The agent will fall back to generating ideas without market context.

---

## Troubleshooting

### "No research tool found"

- Make sure `npx @smithery/cli` can run
- Try: `npx -y @smithery/cli@latest run @baranwang/mcp-deep-research`

### "MCP call timeout"

- Increase timeout: `SMITHERY_CONFIG = {"timeout": 60}`
- Check internet connection

### "Module 'src' not found"

- Run from project root: `/Users/bb1151/Desktop/git_projects/bb1151-dev-ai-agents/`

---

## Available MCP Servers

Explore more MCP servers at:
- https://smithery.ai/
- https://github.com/modelcontextprotocol

Popular options:
- `@baranwang/mcp-deep-research` - Deep web research
- `@modelcontextprotocol/server-brave-search` - Brave search
- `@modelcontextprotocol/server-youtube` - YouTube transcripts

To switch servers, change the `SMITHERY_CONFIG` args in `research_agent.py`.

---

## Example Output

**Without MCP:**
```
Strategy: Buy when RSI < 30
```

**With MCP:**
```
🌍 Fetching live market context via MCP...
✅ Market context fetched (1523 chars)

Key Findings:
- BTC saw $200M liquidations in last 12h
- ETH funding rate spiked to 0.08% (extreme)
- SOL volume up 300% in last 24h

Strategy: Liquidation cascade reversal - Buy BTC when funding > 0.05% 
and liquidations > $100M/h, targeting 2% bounce
```

**Result:** Strategies are now **context-aware** and exploit **real market conditions**! 🚀

---

## Status Check

Verify MCP is working:

```bash
# Check if Research Agent is using MCP
tail -f logs/research_agent.log | grep "MCP"
```

You should see:
```
🌍 Fetching live market context via MCP...
✅ Market context fetched
```

---

**Happy Trading! 🌙**
