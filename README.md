# 🤖 AI AGENTS FOR TRADING

<p align="center">
  <a href="https://www.moondev.com/"><img src="moondev.png" width="300" alt="Moon Dev"></a>
</p>

## 🎯 Vision
ai agents are clearly the future and the entire workforce will be replaced or atleast using ai agents. while i am a quant and building agents for algo trading i will be contributing to all different types of ai agent flows and placing all of the agents here for free, 100% open sourced because i beleive code is the great equalizer and we have never seen a regime shift like this so i need to get this code to the people

feel free to join [our discord](https://discord.gg/8UPuVZ53bh) if you beleive ai agents will be integrated into the workforce

## Video Updates & Training

⭐️ [first full concise documentation video (watch here)](https://youtu.be/RlqzkSgDKDc)

⭐️ [second full walkthrough video(watch here)](https://youtu.be/tjY24JR8Cso?si=Za-PQ2L79US6cu2T)

⭐️ [third full walkthrough w/ big updates, new models, new agents(watch here)](https://youtu.be/qZv6IFIkk6I)

📀 follow all updates here on youtube in this playlist: https://www.youtube.com/playlist?list=PLXrNVMjRZUJg4M4uz52iGd1LhXXGVbIFz

## ⚠️ Critical Disclaimers

*There is no token associated with this project and there never will be. any token launched is not affiliated with this project, moon dev will never dm you. be careful. don't send funds anywhere*

**PLEASE READ CAREFULLY:**

1. This is an experimental research project, NOT a trading system
2. There are NO plug-and-play solutions for guaranteed profits
3. We do NOT provide trading strategies
4. Success depends entirely on YOUR:
   - Trading strategy
   - Risk management
   - Market research
   - Testing and validation
   - Overall trading approach

5. NO AI agent can guarantee profitable trading
6. You MUST develop and validate your own trading approach
7. Trading involves substantial risk of loss
8. Past performance does not indicate future results

**⚠️ IMPORTANT: This is an experimental project. There are NO guarantees of profitability. Trading involves substantial risk of loss.**

## 👂 Looking for Updates?
Project updates will be posted in Discord, join here: [discord.gg/8UPuVZ53bh](https://discord.gg/8UPuVZ53bh)

## 🔗 Links
- Free Algo Trading Roadmap: [moondev.com](https://moondev.com)
- Algo Trading Education: [algotradecamp.com](https://algotradecamp.com)
- Business Contact [moon@algotradecamp.com](mailto:moon@algotradecamp.com)

---

## 🚀 Quick Start Guide - RBI Backtesting Agent

**Why Start with Backtesting?**

Before running ANY trading algorithm or AI agent with real money, you MUST backtest your strategies. Backtesting shows you how a strategy would have performed on historical data. The RBI (Research-Based Inference) Agent automates this entire process for you.

**What is the RBI Agent?**

The RBI Agent takes your trading ideas (from YouTube videos, PDFs, or plain text) and:
1. 🧠 Uses AI to understand the trading strategy
2. 💻 Codes a complete backtest using the `backtesting.py` library
3. 📊 Tests across 20+ different market data sources
4. ✅ Only saves strategies that pass a 1% return threshold
5. 🎯 Tries to optimize strategies to hit a 50% target return

**Python Version:** 3.10.9 was used during development

### Step 1: ⭐ Star & Fork the Repo
- Click the star button to save it to your GitHub favorites
- Fork to your GitHub account to get your own copy
- This lets you make changes and track updates

### Step 2: 💻 Clone to Your Machine
```bash
git clone https://github.com/YOUR_USERNAME/moon-dev-ai-agents-for-trading.git
cd moon-dev-ai-agents-for-trading
```

**Recommended IDEs:**
- [Cursor](https://www.cursor.com/) - AI-enabled coding
- [Windsurfer](https://codeium.com/) - AI-enabled coding

### Step 3: 🔑 Set Up Environment Variables

The RBI Agent needs API keys to function. Create a `.env` file in the root directory:

```bash
# Copy the example file
cp .env.example .env
```

**Required API Keys for RBI Agent:**

```bash
# AI Model APIs (you need at least ONE of these)
ANTHROPIC_KEY=your_anthropic_api_key_here          # Claude models (recommended)
OPENAI_KEY=your_openai_api_key_here                # GPT models
DEEPSEEK_KEY=your_deepseek_api_key_here            # DeepSeek models (cheap!)
GROQ_API_KEY=your_groq_api_key_here                # Groq (fast inference)
GEMINI_KEY=your_gemini_api_key_here                # Google Gemini
XAI_API_KEY=your_xai_api_key_here                  # Grok models

# Market Data APIs (for downloading price data)
BIRDEYE_API_KEY=your_birdeye_api_key_here          # Solana token data
COINGECKO_API_KEY=your_coingecko_api_key_here      # Crypto market data
```

**Where to Get API Keys:**
- **Anthropic Claude**: https://console.anthropic.com/
- **OpenAI GPT**: https://platform.openai.com/api-keys
- **DeepSeek**: https://platform.deepseek.com/ (very cheap, great for backtesting)
- **Groq**: https://console.groq.com/
- **Google Gemini**: https://aistudio.google.com/app/apikey
- **xAI Grok**: https://console.x.ai/
- **BirdEye**: https://birdeye.so/ (Solana data)
- **CoinGecko**: https://www.coingecko.com/en/api

⚠️ **Never commit or share your `.env` file! It's in .gitignore for your safety.**

### Step 4: 📦 Install Dependencies

Using conda (recommended):
```bash
conda create -n tflow python=3.10.9
conda activate tflow
pip install -r requirements.txt
```

Or using pip directly:
```bash
pip install -r requirements.txt
```

### Step 5: 🧪 Run Your First Backtest

**Option A: Single Strategy Test**

Create a file called `ideas.txt` in `src/data/rbi_pp_multi/`:

```
Buy when RSI < 30 and sell when RSI > 70
```

Then run:
```bash
python src/agents/rbi_agent_pp_multi.py
```

**Option B: Use the Web Dashboard**

Start the dashboard:
```bash
cd src/data/rbi_pp_multi
python app.py
```

Open browser to: `http://localhost:8000`

Click "New Backtests" and enter your strategy ideas!

### Step 6: 📊 Understanding Results

The agent will:
- Process your strategy idea
- Generate backtest code
- Test across 20+ market datasets (BTC, ETH, SOL, etc.)
- Show results in a table with:
  - Return %
  - Buy & Hold %
  - Max Drawdown
  - Sharpe Ratio
  - Sortino Ratio
  - Number of Trades

**Only strategies returning > 1% are saved to the CSV.**

Results are saved to:
- `src/data/rbi_pp_multi/backtest_stats.csv` - All passing backtests
- `src/data/rbi_pp_multi/user_folders/` - Organized by run name

### Step 7: 🔍 Analyze Backtest Code

Find your strategy files in:
```
src/data/rbi_pp_multi/10_25_2025_09_08/
```

Each successful backtest has:
- **Python file**: The actual backtest code you can review and modify
- **Results**: Performance metrics

**Read the code!** This is how you learn what works and what doesn't.

---

## 🎯 Configuration - RBI Agent

All settings are in `src/agents/rbi_agent_pp_multi.py` (lines 130-132):

```python
# 🎯 PROFIT TARGET CONFIGURATION
TARGET_RETURN = 50  # Target return in % (AI tries to optimize to this)
SAVE_IF_OVER_RETURN = 1.0  # Save backtest to CSV if return > this %
```

**How it works:**
- AI tries to optimize strategies to hit **50% return**
- But ANY backtest returning **> 1%** gets saved to CSV
- This way you can review all decent strategies, not just perfect ones

**Other Settings:**
```python
MAX_WORKERS = 18  # Number of parallel threads (adjust based on your CPU)
DEBUG_BACKTEST_ERRORS = True  # Auto-fix coding errors with AI
MAX_DEBUG_ITERATIONS = 10  # How many times to try fixing errors
```

---

## 📚 Advanced: Adding Custom Data Sources

Want to test on your own tokens? Edit the data list in `rbi_agent_pp_multi.py` (lines 157-178):

```python
ALL_DATA_CONFIGS = [
    # Crypto data from CoinGecko/BirdEye
    {'symbol': 'BTC-USD', 'timeframe': '15m', 'days_back': 90},
    {'symbol': 'ETH-USD', 'timeframe': '15m', 'days_back': 90},
    {'symbol': 'SOL-USD', 'timeframe': '15m', 'days_back': 90},

    # Add your own token (Solana contract address)
    {'symbol': 'YOUR_TOKEN_ADDRESS', 'timeframe': '1H', 'days_back': 30},
]
```

The agent will automatically download and cache the data.

---

## 🤖 Live Trading Agents

**⚠️ Only use these AFTER thoroughly backtesting your strategies!**

Once you've developed and validated profitable strategies through backtesting, you can explore the live trading agents:

### Traditional Trading Agents
- **Trading Agent** (`trading_agent.py`): Dual-mode AI trading system with swarm consensus
- **Strategy Agent** (`strategy_agent.py`): Manages and executes strategies from the strategies folder
- **Risk Agent** (`risk_agent.py`): Monitors and manages portfolio risk
- **Copy Agent** (`copy_agent.py`): Monitors copy bot for potential trades
- **Whale Agent** (`whale_agent.py`): Monitors whale activity
- **Sentiment Agent** (`sentiment_agent.py`): Analyzes Twitter sentiment
- **Chart Agent** (`chartanalysis_agent.py`): Analyzes charts with AI
- **Funding Agent** (`funding_agent.py`): Monitors funding rates
- **Liquidation Agent** (`liquidation_agent.py`): Tracks liquidation events

Plus 30+ other specialized agents for various trading tasks.

### 🔬 Quantitative Trading Agents (Jim Simons-Style)

**NEW**: Event-driven quantitative agents inspired by Renaissance Technologies:

- **Anomaly Detection Agent**: Detects statistical anomalies in market data (z-score > 2σ)
- **Signal Aggregation Agent**: Combines weak signals into strong predictions (70% consensus)
- **Transaction Cost Agent**: Analyzes and validates transaction costs (square-root model)
- **Backtesting Validation Agent**: Rigorous walk-forward analysis with statistical testing
- **Capacity Monitoring Agent**: Tracks strategy capacity limits and slippage
- **Signal Decay Agent**: Detects and retires degraded signals (Sharpe < 0.5)
- **Regime Detection Agent**: Identifies market regimes (volatility, trend, liquidity)
- **Correlation Matrix Agent**: Discovers hidden correlations across assets
- **Portfolio Optimization Agent**: MPT optimization with Kelly Criterion sizing
- **Alternative Data Agent**: Ingests social media, on-chain, and GitHub metrics

**Key Features**:
- 🎯 Event-driven architecture with Kafka
- 📊 Statistical rigor (p-values, Sharpe ratios, significance testing)
- 🔄 Automatic signal decay detection and retirement
- 💰 Transaction cost modeling and capacity monitoring
- 🧮 Modern Portfolio Theory optimization
- 📈 Walk-forward backtesting validation

**Quick Start**: See [QUANT_AGENTS_QUICKSTART.md](MOON_DEV_EDA_IMPLEMENTATION/QUANT_AGENTS_QUICKSTART.md)  
**Integration Guide**: See [QUANT_AGENTS_INTEGRATION_GUIDE.md](MOON_DEV_EDA_IMPLEMENTATION/QUANT_AGENTS_INTEGRATION_GUIDE.md)  
**Full Documentation**: See [src/agents/quant/README.md](MOON_DEV_EDA_IMPLEMENTATION/src/agents/quant/README.md)

**For detailed live trading documentation, see:** [TRADING.md](TRADING.md)

---

## 🗺️ ROADMAP

### In Progress
- [x] **HyperLiquid Perps Integration** ✅
- [x] **Swarm Consensus Trading** ✅
- [x] **RBI Parallel Backtesting** ✅

### Coming Soon
- [ ] **Polymarket Integration** - Prediction market trading
- [ ] **Base Chain Integration** - L2 network support
- [ ] **Extended Integration** - Additional exchange support
- [ ] **HyperLiquid Spot Trading** - Spot market support
- [ ] **Trending Agent** - Spots leaders on HyperLiquid
- [ ] **Position Sizing Agent** - Volume/liquidation-based sizing
- [ ] **Regime Agents** - Adaptive strategy switching
- [ ] **Polymarket Sweeper Agent** - Follow successful prediction traders

### Future Ideas
- [ ] **Lighter Integration**
- [ ] **Pacifica Integration**
- [ ] **Hibachi Integration**
- [ ] **Aster Integration**
- [ ] **HyperEVM Support**

---

*Built with love by Moon Dev - Pioneering the future of AI-powered trading*

## 📜 Detailed Disclaimer
The content presented is for educational and informational purposes only and does not constitute financial advice. All trading involves risk and may not be suitable for all investors. You should carefully consider your investment objectives, level of experience, and risk appetite before investing.

Past performance is not indicative of future results. There is no guarantee that any trading strategy or algorithm discussed will result in profits or will not incur losses.

**CFTC Disclaimer:** Commodity Futures Trading Commission (CFTC) regulations require disclosure of the risks associated with trading commodities and derivatives. There is a substantial risk of loss in trading and investing.

I am not a licensed financial advisor or a registered broker-dealer. Content & code is based on personal research perspectives and should not be relied upon as a guarantee of success in trading.
