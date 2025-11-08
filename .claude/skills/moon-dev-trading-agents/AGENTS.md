# Complete Agent Reference

Comprehensive list of all 48+ specialized AI agents in Moon Dev's trading system.

---

## Trading Agents

**trading_agent.py**
- Primary trading execution agent
- Supports Hyperliquid, BirdEye, Extended Exchange
- Makes buy/sell decisions based on market analysis
- Configurable exchange selection via EXCHANGE variable

**strategy_agent.py**
- Executes user-defined strategies from src/strategies/
- Generates signals: BUY, SELL, NOTHING with confidence scores
- Loads strategies dynamically from strategy classes

**risk_agent.py**
- **RUNS FIRST** before any trading decisions
- Monitors portfolio risk, P&L, and exposure
- Circuit breakers: MAX_LOSS_USD, MAX_GAIN_USD, MINIMUM_BALANCE_USD
- Can force-close positions on risk violations

**copybot_agent.py**
- Copies trades from successful wallets/traders
- Uses Moon Dev API for copybot follow list
- Analyzes wallet activity and replicates positions

---

## Market Analysis Agents

**sentiment_agent.py**
- Analyzes market sentiment from social media, news
- Aggregates sentiment scores for tokens
- Helps inform trading decisions

**whale_agent.py**
- Tracks large wallet movements ("whale watching")
- Identifies significant buy/sell pressure
- Alerts on whale accumulation/distribution

**funding_agent.py**
- Monitors perpetual funding rates across exchanges
- Identifies funding rate arbitrage opportunities
- Tracks basis between spot and perps

**liquidation_agent.py**
- Tracks liquidation data from exchanges
- Identifies liquidation clusters and cascades
- Helps predict volatility and support/resistance

**chartanalysis_agent.py**
- Technical analysis using AI vision models
- Analyzes price charts for patterns
- Generates trading signals from chart patterns

**coingecko_agent.py**
- Fetches token metadata from CoinGecko API
- 15,000+ token market caps, volumes, sentiment
- Enriches token data for analysis

---

## Research & Strategy Development

**rbi_agent.py** (Research-Based Inference)
- **PRIMARY VERSION**: Codes backtests from videos/PDFs/text
- Uses DeepSeek-R1 for strategy extraction
- Generates backtesting.py compatible code
- Executes backtest and returns metrics
- Cost: ~$0.027 per backtest (~6 minutes)

**rbi_agent_v2.py**
- Alternative RBI implementation
- Enhanced strategy parsing

**rbi_agent_v3.py**
- Latest RBI version with improvements

**rbi_agent_pp.py**
- PowerPoint presentation integration for RBI

**rbi_agent_pp_multi.py**
- Multi-slide PowerPoint analysis

**rbi_batch_backtester.py**
- Batch backtest multiple strategies
- Compares strategy performance

**research_agent.py**
- General market research and analysis
- Compiles research reports
- Identifies trading opportunities

**websearch_agent.py**
- Web search capabilities for market research
- Fetches real-time news and data
- Enriches analysis with current information

---

## Content Creation Agents

**chat_agent.py**
- **PRIMARY VERSION**: Conversational AI for trading questions
- Answers user queries about markets, agents, strategies
- Provides explanations and guidance

**chat_agent_og.py**
- Original chat agent implementation

**chat_agent_ad.py**
- Ad-supported chat variant

**chat_question_generator.py**
- Generates questions for user engagement
- Creates content ideas

**clips_agent.py**
- Creates short video clips for social media
- Highlights key market moments

**realtime_clips_agent.py**
- Real-time clip generation
- Captures live market events

**tweet_agent.py**
- Generates tweets about market activity
- Automates social media posting
- Creates engagement content

**video_agent.py**
- Full-length video content creation
- Market analysis videos
- Educational content

**shortvid_agent.py**
- Short-form video content (TikTok, Reels)
- Vertical video format

**tiktok_agent.py**
- TikTok-specific content generation
- Trends and viral content

**phone_agent.py**
- Voice/phone interaction capabilities
- Audio-based market updates

---

## Specialized Trading Agents

**sniper_agent.py**
- Fast execution for new token launches
- Front-running strategies
- Quick entry/exit on opportunities

**solana_agent.py**
- Solana-specific trading operations
- On-chain transaction execution
- Solana DEX interactions

**tx_agent.py**
- Transaction monitoring and analysis
- On-chain activity tracking
- Wallet transaction parsing

**million_agent.py**
- High-volume trading strategies
- Aims for million-dollar targets
- Aggressive position sizing

**polymarket_agent.py**
- Polymarket prediction market integration
- Binary options trading
- Event-driven betting strategies

**housecoin_agent.py**
- Custom token (housecoin) specific agent
- Project-specific operations

**compliance_agent.py**
- Regulatory compliance monitoring
- Risk mitigation for legal requirements
- Trade logging and reporting

**focus_agent.py**
- Focuses on specific market segments
- Concentrated analysis on selected tokens

---

## Arbitrage Agents

**fundingarb_agent.py**
- Funding rate arbitrage strategies
- Exploits funding rate differentials
- Spot-perp arbitrage

**listingarb_agent.py**
- New listing arbitrage opportunities
- Cross-exchange price differences
- Launch price discrepancies

---

## Multi-Agent Coordination

**swarm_agent.py**
- Coordinates multiple agents simultaneously
- Orchestrates agent collaboration
- Distributes tasks across agent swarm
- Advanced multi-agent workflows

**base_agent.py**
- Base class for all agents
- Common agent functionality
- Inheritance pattern for new agents

**example_unified_agent.py**
- Example implementation of unified agent pattern
- Template for creating new agents

---

## Infrastructure & Utilities

**api.py**
- MoonDevAPI class for custom API endpoints
- Liquidation data, funding data, OI data
- Copybot follow list management

**backtest_runner.py**
- Executes backtests programmatically
- Integrates with backtesting.py library
- Strategy testing infrastructure

**code_runner_agent.py**
- Executes generated code safely
- Sandboxed code execution
- Used by RBI agent

**clean_ideas.py**
- Cleans and organizes trading ideas
- Data preprocessing utility

**new_or_top_agent.py**
- Identifies new or trending tokens
- Top mover detection
- Market scanning

**stream_agent.py**
- Real-time data streaming
- Live market updates
- WebSocket connections

**demo_countdown.py**
- Demo countdown timer
- Presentation utility

---

## Agent Categories Summary

| Category | Count | Examples |
|----------|-------|----------|
| **Trading** | 4 | trading_agent, strategy_agent, risk_agent, copybot_agent |
| **Market Analysis** | 6 | sentiment_agent, whale_agent, funding_agent, liquidation_agent |
| **Research** | 7 | rbi_agent (+ variants), research_agent, websearch_agent |
| **Content Creation** | 8 | chat_agent, clips_agent, tweet_agent, video_agent |
| **Specialized Trading** | 8 | sniper_agent, solana_agent, polymarket_agent, million_agent |
| **Arbitrage** | 2 | fundingarb_agent, listingarb_agent |
| **Coordination** | 2 | swarm_agent, base_agent |
| **Infrastructure** | 7 | api, backtest_runner, code_runner_agent, stream_agent |

---

## Running Agents

### Standalone Execution

Any agent can run independently:
```bash
# Activate your environment (e.g., conda activate your_env_name)
python src/agents/[agent_name].py
```

### Orchestrator Execution

Run multiple agents via main.py:
```bash
python src/main.py
```

Configure active agents in `main.py`:
```python
ACTIVE_AGENTS = {
    "risk_agent": True,      # Always runs first
    "trading_agent": True,
    "sentiment_agent": True,
    # ... etc
}
```

---

## Agent Output Storage

Each agent stores outputs in dedicated folder:
```
src/data/
├── risk_agent/          # Risk reports, circuit breaker logs
├── trading_agent/       # Trade logs, decisions
├── sentiment_agent/     # Sentiment scores
├── rbi_agent/           # Generated backtests
├── whale_agent/         # Whale activity logs
└── [agent_name]/        # Agent-specific outputs
```

Output formats: CSV, JSON, TXT

---

## Agent Selection Guide

**Want to trade?** → `trading_agent.py`

**Need risk management?** → `risk_agent.py` (runs first!)

**Test a strategy?** → `rbi_agent.py` (backtest from video/PDF)

**Custom strategy?** → `strategy_agent.py` (load from src/strategies/)

**Market sentiment?** → `sentiment_agent.py`, `whale_agent.py`

**Find opportunities?** → `funding_agent.py`, `liquidation_agent.py`, `listingarb_agent.py`

**Prediction markets?** → `polymarket_agent.py`

**Copy traders?** → `copybot_agent.py`

**Create content?** → `chat_agent.py`, `tweet_agent.py`, `video_agent.py`

**On-chain analysis?** → `tx_agent.py`, `solana_agent.py`

**Coordinate multiple agents?** → `swarm_agent.py`

---

## Creating New Agents

Follow the agent development pattern:

```python
"""
🌙 Moon Dev's [Agent Name]
[Brief description]
"""

from src.models.model_factory import ModelFactory
from termcolor import cprint
import os

# Configuration
OUTPUT_DIR = "src/data/my_agent/"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def main():
    """Main agent logic"""
    cprint("🌙 Moon Dev's [Agent Name] starting...", "cyan")

    # Initialize LLM
    model = ModelFactory.create_model('anthropic')

    # Agent logic here
    # ...

    # Store results
    # Save to OUTPUT_DIR

    cprint("✅ Agent complete!", "green")

if __name__ == "__main__":
    main()
```

**Requirements:**
- Under 800 lines (split if longer)
- Use ModelFactory for LLM access
- Store outputs in src/data/[agent_name]/
- Make independently executable
- Follow naming: `[purpose]_agent.py`

---

**Built with 🌙 by Moon Dev**

*48+ agents, each a specialist in its domain.*
