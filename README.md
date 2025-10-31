# 🤖 AI AGENTS FOR TRADING

<p align="center">
  <a href="https://www.moondev.com/"><img src="moondev.png" width="300" alt="Moon Dev"></a>
</p>

## 🎯 Vision
ai agents are clearly the future and the entire workforce will be replaced or atleast using ai agents. while i am a quant and building agents for algo trading i will be contributing to all different types of ai agent flows and placing all of the agents here for free, 100% open sourced because i believe code is the great equalizer and we have never seen a regime shift like this so i need to get this code to the people

feel free to join [our discord](https://discord.gg/8UPuVZ53bh) if you beleive ai agents will be integrated into the workforce

## Video Updates & Training

⭐️ [first full concise documentation video (watch here)](https://youtu.be/RlqzkSgDKDc)

⭐️ [second full walkthrough video(watch here)](https://youtu.be/tjY24JR8Cso?si=Za-PQ2L79US6cu2T)

⭐️ [third full walkthrough w/ big updates, new models, new agents(watch here)](https://youtu.be/qZv6IFIkk6I)

⭐️ [forth full walkthrough w/ new agents & ai models](https://youtu.be/D0VRQj0tuCI)


📀 follow all updates here on youtube in this playlist: https://www.youtube.com/playlist?list=PLXrNVMjRZUJg4M4uz52iGd1LhXXGVbIFz

---

## 🤖 All Available Agents

**⚠️ For live trading agents: Only use these AFTER thoroughly backtesting your strategies!**

### Backtesting & Research Agents
- **RBI Agent** (`rbi_agent.py`): Uses DeepSeek to research trading strategies based on YouTube videos, PDFs, or text you provide, then codes out the backtest automatically
- **RBI Parallel Agent** (`rbi_agent_pp_multi.py`): Parallel version with 18 threads, tests across 20+ data sources, web dashboard included
- **Research Agent** (`research_agent.py`): Fills the ideas.txt file so the RBI agent can run forever
- **Websearch Agent** (`websearch_agent.py`): This agent searches the web, in my use case for trading strategy resources and then uses other ai's to split the website ideas into strategy files i can have my  `rbi_agent_pp_multi.py` process and build out backtests

### Live Trading Agents
- **Trading Agent** (`trading_agent.py`): **DUAL-MODE AI trading system** - Toggle between single model (fast ~10s) or swarm mode (6-model consensus ~45-60s). Swarm mode queries Claude 4.5, GPT-5, Gemini 2.5, Grok-4, DeepSeek, and DeepSeek-R1 local for majority vote trading decisions. Configure via `USE_SWARM_MODE` in config.py
- **Strategy Agent** (`strategy_agent.py`): Manages and executes trading strategies placed in the strategies folder
- **Risk Agent** (`risk_agent.py`): Monitors and manages portfolio risk, enforcing position limits and PnL thresholds
- **Copy Agent** (`copy_agent.py`): Monitors copy bot for potential trades
- **Swarm Agent** (`swarm_agent.py`): Queries 6 AI models in parallel (Claude 4.5, GPT-5, Gemini 2.5, Grok-4, DeepSeek, DeepSeek-R1 local), generates AI consensus summary, returns clean JSON with model mapping for easy parsing 🐝

### Market Analysis Agents
- **Whale Agent** (`whale_agent.py`): Monitors whale activity and announces when a whale enters the market
- **Sentiment Agent** (`sentiment_agent.py`): Analyzes Twitter sentiment for crypto tokens with voice announcements
- **Chart Agent** (`chartanalysis_agent.py`): Looks at any crypto chart and analyzes it with AI to make a buy/sell/nothing recommendation
- **Funding Agent** (`funding_agent.py`): Monitors funding rates across exchanges and uses AI to analyze opportunities, providing voice alerts for extreme funding situations with technical context 🌙
- **Liquidation Agent** (`liquidation_agent.py`): Tracks liquidation events with configurable time windows (15min/1hr/4hr), providing AI analysis and voice alerts for significant liquidation spikes 💦
- **Listing Arbitrage Agent** (`listingarb_agent.py`): Identifies promising Solana tokens on CoinGecko before they reach major exchanges like Binance and Coinbase, using parallel AI analysis for technical and fundamental insights
- **Funding Arbitrage Agent** (`fundingarb_agent.py`): Tracks the funding rate on HyperLiquid to find funding rate arbitrage opportunities between HL and Solana
- **New or Top Tokens Agent** (`new_or_top_agent.py`): Looks at the new tokens and the top tokens from CoinGecko API

### Solana-Specific Agents
- **Sniper Agent** (`sniper_agent.py`): Watches for new Solana token launches, analyzes them, and maybe snipes
- **TX Agent** (`tx_agent.py`): Watches transactions made by your copy list and prints them out with optional auto tab open
- **Solana Agent** (`solana_agent.py`): Looks at the sniper agent and the TX agent to select which memes may be interesting

### Content Creation Agents
- **Chat Agent** (`chat_agent.py`): Monitors YouTube live stream chat, moderates & responds to known questions. Absolute fire.
- **Twitter Agent** (`tweet_agent.py`): Takes in text and creates tweets using DeepSeek or other models
- **Video Agent** (`video_agent.py`): 🎬 Parallel AI video generation using OpenAI's Sora 2 API - create videos directly from text prompts with 9 concurrent workers, configurable resolutions (720p/1080p), durations (4/8/12s), and aspect ratios (9:16 for TikTok/Reels, 16:9 for YouTube, 1:1 for Instagram). [See full docs](docs/video_agent.md)
- **Clips Agent** (`clips_agent.py`): Helps clip long videos into shorter ones so you can upload to your YouTube and get paid. More info: https://discord.gg/XAw8US9aHT
- **Real-Time Clips Agent** (`realtime_clips_agent.py`): Makes real-time clips of streamers using OBS
- **Phone Agent** (`phone_agent.py`): An AI agent that can take phone calls for you

### Specialized Agents
- **Prompt Agent** (`prompt_agent.py`): 🎯 Interactive prompt enhancement tool that transforms basic prompts into professional, production-ready prompts using best practices from Parahelp & Cursor. Stays open in terminal, continuously ready to enhance your prompts with expert design principles (role-based prompting, structured formatting, explicit thinking order). Auto-saves and copies enhanced prompts. Perfect for improving prompts for any AI task. [See full docs](docs/prompt_agent.md)
- **Focus Agent** (`focus_agent.py`): Randomly samples audio during coding sessions to maintain productivity, providing focus scores and voice alerts when focus drops (~$10/month, perfect for voice-to-code workflows)
- **Million Agent** (`million_agent.py`): Uses million context window from Gemini to pull in a knowledge base
- **TikTok Agent** (`tiktok_agent.py`): Scrolls TikTok and gets screenshots of the video + comments to extract consumer data to feed into algos. Sometimes called social arbitrage
- **Compliance Agent** (`compliance_agent.py`): Analyzes TikTok ads for Facebook advertising compliance, extracting frames and transcribing audio to check against FB guidelines
- **Housecoin Agent** (`housecoin_agent.py`): DCA (dollar cost average) agent with AI confirmation layer using Grok-4 for the thesis: 1 House = 1 Housecoin 🏠
- **Polymarket Agent** (`polymarket_agent.py`): Connects to the live trades feed via WebSocket and analyzes with the swarm agent to see which markets could be interesting to trade


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
OPENROUTER_API_KEY=your_openrouter_api_key_here    # OpenRouter (200+ models!)

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
- **OpenRouter**: https://openrouter.ai/keys (access 200+ models including Qwen, GLM, and more!)
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

Open browser to: `http://localhost:8001`

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
