"""
🌙 Moon Dev's Listing Arbitrage Agent 🔍

=================================
📚 OVERVIEW & DOCUMENTATION
=================================

This agent is designed to find potential "gem" tokens before they get listed on major exchanges.
It's specifically built to analyze Solana tokens that meet these criteria:
- Not yet listed on Binance or Coinbase
- Market cap under $10M
- 24h volume over $100k

Key Features:
------------
1. Dual AI Analysis System:
   - Technical Analysis Agent (Default: Claude Haiku)
     • Analyzes price charts and patterns
     • Studies volume trends
     • Identifies support/resistance levels
     • Evaluates OHLCV patterns
   
   - Fundamental Analysis Agent (Default: Claude Sonnet)
     • Evaluates project quality
     • Assesses team and development
     • Analyzes market positioning
     • Reviews technical analysis findings

2. Data Collection:
   - Fetches 14 days of historical data
   - Uses 4-hour candle intervals
   - Calculates key metrics:
     • Volatility
     • Price trends
     • Volume patterns
     • Support/resistance levels

3. AI Model Flexibility:
   - Supports multiple AI models:
     • Claude models (default)
     • DeepSeek Chat
     • DeepSeek Reasoner
   - Easy model switching via MODEL_OVERRIDE setting

4. Performance Optimization:
   - Parallel processing (50 processes)
   - 24-hour analysis cycles
   - Smart token skipping:
     • Recently analyzed tokens
     • Stablecoins
     • Wrapped tokens

5. Results & Storage:
   - Main results: src/data/ai_analysis.csv
   - Buy signals: src/data/ai_analysis_buys.csv
   - Agent memory: src/data/agent_memory/

Usage:
------
1. Ensure required API keys in .env:
   - ANTHROPIC_KEY (for Claude)
   - DEEPSEEK_KEY (for DeepSeek)
   - COINGECKO_API_KEY

2. Configure model preference:
   MODEL_OVERRIDE = "0"           # Use Claude (default)
   MODEL_OVERRIDE = "deepseek-chat"    # Use DeepSeek Chat
   MODEL_OVERRIDE = "deepseek-reasoner" # Use DeepSeek Reasoner

3. Run the agent:
   python src/agents/listingarb_agent.py

Output Files:
------------
1. ai_analysis.csv:
   - Full analysis of all tokens
   - Includes both agent recommendations
   - Price and volume data
   - Timestamps of analysis

2. ai_analysis_buys.csv:
   - Filtered list of "BUY" recommendations
   - Only tokens under $10M market cap
   - Sorted by timestamp (newest first)

Memory System:
-------------
- Stores last 100 analyses per agent
- Tracks promising tokens
- Maintains conversation history
- Auto-cleans old records

Performance Notes:
----------------
- Analyzes ~1000 tokens per run
- Takes 2-3 hours for full analysis
- Uses rate limiting for API calls
- Parallel processing reduces runtime

Created by Moon Dev 🌙
For updates: https://github.com/moon-dev-ai-agents-for-trading
"""

import os
import pandas as pd
import json
from typing import Dict, List
from datetime import datetime, timedelta
import time
from pathlib import Path
from termcolor import colored, cprint
from dotenv import load_dotenv
import requests
import numpy as np
import concurrent.futures
import src.config as config
from src.agents.model_helper import get_agent_model

# Load environment variables
load_dotenv()

# 📁 File Paths
DISCOVERED_TOKENS_FILE = Path("src/data/discovered_tokens.csv")  # Input from token discovery script
AI_ANALYSIS_FILE = Path("src/data/ai_analysis.csv")  # AI analysis results

# 🤖 CoinGecko API Settings
COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY")
COINGECKO_BASE_URL = "https://pro-api.coingecko.com/api/v3"
TEMP_DATA_DIR = Path("src/data/temp_data")

# ⚙️ Configuration
HOURS_BETWEEN_RUNS = 24        # Run AI analysis every 24 hours to manage API costs
PARALLEL_PROCESSES = 50        # Number of parallel processes to run
MIN_VOLUME_USD = 100_000      # Minimum 24h volume to analyze
MAX_MARKET_CAP = 10_000_000   # Maximum market cap to include in analysis (10M)

# 🤖 Tokens to Ignore
DO_NOT_ANALYZE = [
    'tether',           # USDT - Stablecoin
    'usdt',            # Alternative USDT id
    'usdtsolana',      # Solana USDT
    'usdc',            # USDC
    'usd-coin',        # Alternative USDC id
    'busd',            # Binance USD
    'dai',             # DAI
    'frax',            # FRAX
    'true-usd',        # TUSD
    'wrapped-bitcoin',  # WBTC
    'wrapped-solana',  # WSOL
]

# 🤖 Agent Prompts
AGENT_ONE_PROMPT = """
You are the Technical Analysis Agent 📊
Your role is to analyze token metrics, market data, and OHLCV patterns.

IMPORTANT: Start your response with one of these recommendations:
RECOMMENDATION: BUY
RECOMMENDATION: SELL
RECOMMENDATION: DO NOTHING

Then provide your detailed analysis.

Focus on:
- Volume trends and liquidity patterns
- Price action and momentum using OHLCV data
- Support and resistance levels from price history
- Market cap relative to competitors
- Technical indicators and patterns
- 4-hour chart analysis for the past 14 days

Help Moon Dev identify tokens with strong technical setups! 🎯
"""

AGENT_TWO_PROMPT = """
You are the Fundamental Analysis Agent 🔬
Your role is to analyze project fundamentals and potential.

IMPORTANT: Start your response with one of these recommendations:
RECOMMENDATION: BUY
RECOMMENDATION: SELL
RECOMMENDATION: DO NOTHING

Then provide your detailed analysis.

Focus on:
- Project technology and innovation
- Team background and development activity
- Community growth and engagement
- Competition and market positioning
- Growth potential and risks
- How the technical analysis aligns with fundamentals

Help Moon Dev evaluate which tokens have the best fundamentals! 🚀
"""

class AIAgent:
    """AI Agent for analyzing tokens"""
    
    def __init__(self, name: str):
        self.name = name

        # Initialize AI model via OpenRouter
        self.model = get_agent_model(verbose=True)
        if not self.model:
            raise ValueError(f"🚨 Failed to initialize AI model for {name}!")
            
        self.memory_file = Path(f"src/data/agent_memory/{name.lower().replace(' ', '_')}.json")
        self.memory = {
            'analyzed_tokens': [],
            'promising_tokens': [],
            'conversations': []
        }
        self.load_memory()
        
    def load_memory(self):
        """Load agent memory"""
        try:
            if self.memory_file.exists():
                with open(self.memory_file, 'r') as f:
                    try:
                        loaded_memory = json.load(f)
                        # Ensure all required keys exist
                        for key in ['analyzed_tokens', 'promising_tokens', 'conversations']:
                            if key not in loaded_memory:
                                loaded_memory[key] = []
                        self.memory = loaded_memory
                        print(f"📚 Loaded {len(self.memory['conversations'])} previous conversations for {self.name}")
                    except json.JSONDecodeError:
                        print(f"⚠️ Warning: Corrupted memory file for {self.name}, using empty memory")
            else:
                print(f"📝 Created new memory file for {self.name}")
                self.memory_file.parent.mkdir(parents=True, exist_ok=True)
                self.save_memory()
        except Exception as e:
            print(f"⚠️ Error loading memory for {self.name}: {str(e)}")
            
    def save_memory(self):
        """Save agent memory"""
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.memory_file, 'w') as f:
            json.dump(self.memory, f, indent=2)
            
    def analyze(self, token_data: Dict, other_agent_analysis: str = None) -> str:
        """Analyze a token and provide insights"""
        try:
            # Validate token_data has required fields
            required_fields = ['name', 'symbol', 'token_id', 'price', 'volume_24h', 'market_cap']
            for field in required_fields:
                if field not in token_data:
                    token_data[field] = 'Unknown' if field in ['name', 'symbol', 'token_id'] else 0
                    
            # Format token data for analysis with clear sections
            token_info = f"""
🪙 Token Information:
• Name: {token_data['name']} ({token_data['symbol']})
• Token ID: {token_data['token_id']}
• Current Price: ${float(token_data.get('price', 0)):,.8f}
• 24h Volume: ${float(token_data.get('volume_24h', 0)):,.2f}
• Market Cap: ${float(token_data.get('market_cap', 0)):,.2f}

{token_data.get('ohlcv_data', '❌ No OHLCV data available')}
"""
            
            # Build the prompt with clear instructions
            if self.name == "Agent One":
                system_prompt = AGENT_ONE_PROMPT
                user_prompt = f"""Please analyze this token's technical metrics and OHLCV data:

{token_info}

Focus on:
1. Price action patterns in the 4h chart
2. Volume trends and anomalies
3. Support/resistance levels
4. Technical indicators from the OHLCV data
5. Potential entry/exit points based on the data

Remember to reference specific data points from the OHLCV table in your analysis!"""

            else:
                system_prompt = AGENT_TWO_PROMPT
                user_prompt = f"""Please analyze this token considering the technical analysis and OHLCV data:

{token_info}

Agent One's Technical Analysis:
{other_agent_analysis}

Focus on:
1. How the OHLCV data supports or contradicts the fundamentals
2. Volume patterns that indicate growing/declining interest
3. Price stability and growth potential
4. Market positioning based on the data
5. Risk assessment using both technical and fundamental factors

Remember to reference specific data points from the OHLCV table in your analysis!"""
            
            # Get AI response via OpenRouter
            response = self.model.generate_response(
                system_prompt=system_prompt,
                user_content=user_prompt,
                temperature=0.7,
                max_tokens=300
            )

            # Parse response
            if response and hasattr(response, 'content'):
                analysis = response.content
            else:
                analysis = str(response)
            
            # Update memory with OHLCV context
            if not isinstance(self.memory['analyzed_tokens'], list):
                self.memory['analyzed_tokens'] = []
            if not isinstance(self.memory['conversations'], list):
                self.memory['conversations'] = []
                
            self.memory['analyzed_tokens'].append({
                'token_id': token_data['token_id'],
                'timestamp': datetime.now().isoformat(),
                'analysis': analysis,
                'had_ohlcv_data': 'ohlcv_data' in token_data
            })
            
            self.memory['conversations'].append({
                'timestamp': datetime.now().isoformat(),
                'token': token_data['token_id'],
                'prompt': user_prompt,
                'response': analysis,
                'included_ohlcv': 'ohlcv_data' in token_data
            })
            
            # Keep memory size manageable
            if len(self.memory['conversations']) > 100:
                self.memory['conversations'] = self.memory['conversations'][-100:]
            if len(self.memory['analyzed_tokens']) > 100:
                self.memory['analyzed_tokens'] = self.memory['analyzed_tokens'][-100:]
                
            self.save_memory()
            
            # Print confirmation that OHLCV data was included
            if 'ohlcv_data' in token_data:
                print(f"\n📊 Included OHLCV data in {self.name}'s analysis")
            
            return analysis
            
        except Exception as e:
            print(f"⚠️ Error in {self.name}'s analysis: {str(e)}")
            print(f"⚠️ Token data: {token_data.get('name', 'Unknown')} ({token_data.get('symbol', 'Unknown')})")
            return f"Error analyzing token: {str(e)}"

class ListingArbSystem:
    """AI Agent system for analyzing potential listing opportunities"""
    
    def __init__(self):
        self.agent_one = AIAgent("Agent One")
        self.agent_two = AIAgent("Agent Two")
        self.analysis_log = self._load_analysis_log()
        cprint("🔍 Moon Dev's Listing Arb System Ready!", "white", "on_green", attrs=["bold"])
        
    def _load_analysis_log(self) -> pd.DataFrame:
        """Load or create AI analysis log"""
        if AI_ANALYSIS_FILE.exists():
            df = pd.read_csv(AI_ANALYSIS_FILE)
            print(f"\n📈 Loaded analysis log with {len(df)} previous analyses")
            return df
        else:
            df = pd.DataFrame(columns=[
                'timestamp', 
                'token_id', 
                'symbol', 
                'name',
                'price', 
                'volume_24h', 
                'market_cap',
                'agent_one_recommendation', 
                'agent_two_recommendation'
            ])
            df.to_csv(AI_ANALYSIS_FILE, index=False)
            print("\n📝 Created new analysis log")
            return df
            
    def load_discovered_tokens(self) -> pd.DataFrame:
        """Load tokens from discovery script"""
        if not DISCOVERED_TOKENS_FILE.exists():
            raise FileNotFoundError(f"❌ No discovered tokens file found at {DISCOVERED_TOKENS_FILE}")
            
        df = pd.read_csv(DISCOVERED_TOKENS_FILE)
        print(f"\n📚 Loaded {len(df)} tokens from {DISCOVERED_TOKENS_FILE}")
        return df
        
    def get_ohlcv_data(self, token_id: str) -> str:
        """Get OHLCV data for the past 14 days in 4-hour intervals"""
        try:
            # Skip ignored tokens
            if token_id.lower() in DO_NOT_ANALYZE:
                print(f"⏭️ Skipping ignored token: {token_id}")
                return "❌ Token in ignore list"
            
            print(f"\n📈 Fetching OHLCV data for {token_id}...")
            
            url = f"{COINGECKO_BASE_URL}/coins/{token_id}/ohlc"
            params = {
                'vs_currency': 'usd',  # Required parameter
                'days': '14'           # Will give us 4h intervals based on docs
            }
            headers = {
                'x-cg-pro-api-key': COINGECKO_API_KEY
            }
            
            response = requests.get(url, headers=headers, params=params)
            
            # Print raw response for debugging
            print("\n🔍 Raw API Response:")
            print(f"Status Code: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            print(f"Response Data: {response.text[:500]}...")  # First 500 chars
            
            # Handle API errors gracefully
            if response.status_code != 200:
                print(f"⚠️ API returned status code {response.status_code} for {token_id}")
                return f"❌ No OHLCV data available (API Error: {response.status_code})"
            
            ohlcv_data = response.json()
            
            if not ohlcv_data or len(ohlcv_data) < 2:  # Need at least 2 data points
                print(f"⚠️ No OHLCV data returned for {token_id}")
                return "❌ No OHLCV data available (Empty Response)"
            
            # Format OHLCV data for AI analysis
            formatted_data = "📊 OHLCV Data (4h intervals, past 14 days):\n"
            formatted_data += "Timestamp | Open | High | Low | Close\n"
            formatted_data += "-" * 50 + "\n"
            
            try:
                # Process each OHLCV entry
                # OHLCV format from API: [timestamp, open, high, low, close]
                for entry in ohlcv_data[-10:]:  # Show last 10 entries for readability
                    timestamp = datetime.fromtimestamp(entry[0]/1000).strftime('%Y-%m-%d %H:%M')
                    open_price = f"${entry[1]:,.8f}"
                    high = f"${entry[2]:,.8f}"
                    low = f"${entry[3]:,.8f}"
                    close = f"${entry[4]:,.8f}"
                    
                    formatted_data += f"{timestamp} | {open_price} | {high} | {low} | {close}\n"
                
                # Add some basic statistics
                prices = np.array([float(entry[4]) for entry in ohlcv_data])  # Close prices
                
                stats = f"""
                📈 Price Statistics:
                • Highest Price: ${np.max(prices):,.8f}
                • Lowest Price: ${np.min(prices):,.8f}
                • Average Price: ${np.mean(prices):,.8f}
                • Price Volatility: {np.std(prices)/np.mean(prices)*100:.2f}%
                
                📊 Trading Activity:
                • Number of Candles: {len(ohlcv_data)}
                • Latest Close: ${prices[-1]:,.8f}
                • Price Change: {((prices[-1]/prices[0])-1)*100:,.2f}% over period
                """
                
                # Print formatted data for verification
                print("\n📊 Formatted OHLCV Data:")
                print(formatted_data)
                print(stats)
                
                return formatted_data + stats
                
            except (IndexError, TypeError, ValueError) as e:
                print(f"⚠️ Error processing OHLCV data for {token_id}: {str(e)}")
                return "❌ No OHLCV data available (Data Processing Error)"
                
        except Exception as e:
            print(f"⚠️ Error fetching OHLCV data for {token_id}: {str(e)}")
            return "❌ No OHLCV data available (Network/API Error)"

    def _should_analyze_token(self, token_id: str) -> bool:
        """Check if token needs analysis based on last analysis time"""
        if not self.analysis_log.empty:
            last_analysis = self.analysis_log[self.analysis_log['token_id'] == token_id]
            if not last_analysis.empty:
                last_time = pd.to_datetime(last_analysis['timestamp'].iloc[-1])
                hours_since = (datetime.now() - last_time).total_seconds() / 3600
                if hours_since < HOURS_BETWEEN_RUNS:
                    print(f"⏭️ Skipping {token_id} - Analyzed {hours_since:.1f} hours ago")
                    return False
        return True

    def analyze_tokens_parallel(self, tokens_batch):
        """Analyze a batch of tokens in parallel"""
        with concurrent.futures.ThreadPoolExecutor(max_workers=PARALLEL_PROCESSES) as executor:
            # Create a list of tokens that need analysis
            tokens_to_analyze = []
            for _, token_data in tokens_batch.iterrows():
                if self._should_analyze_token(token_data['token_id']):
                    tokens_to_analyze.append(token_data.to_dict())
            
            if tokens_to_analyze:
                # Submit all tokens for analysis
                futures = [executor.submit(self.analyze_token, token) for token in tokens_to_analyze]
                # Wait for all to complete
                concurrent.futures.wait(futures)
            
            print(f"✅ Batch complete - Analyzed {len(tokens_to_analyze)} tokens")

    def analyze_token(self, token_data: Dict):
        """Have both agents analyze a token"""
        try:
            name = token_data.get('name', 'Unknown')
            symbol = token_data.get('symbol', 'UNKNOWN')
            token_id = token_data.get('token_id', '')
            
            try:
                volume = float(token_data.get('volume_24h', 0))
                price = float(token_data.get('price', 0))
                market_cap = float(token_data.get('market_cap', 0))
            except (TypeError, ValueError):
                volume = 0
                price = 0
                market_cap = 0
                
            print(f"\n🔍 Analyzing: {name} ({symbol})")
            print(f"📊 24h Volume: ${volume:,.2f}")
            print(f"💰 Market Cap: ${market_cap:,.2f}")
            
            # Skip if market cap too high (check this first)
            if market_cap > MAX_MARKET_CAP:
                print(f"⏭️ Skipping - Market cap above maximum (${MAX_MARKET_CAP:,.0f})")
                return
            
            # Skip if volume too low
            if volume < MIN_VOLUME_USD:
                print(f"⏭️ Skipping - Volume below minimum (${MIN_VOLUME_USD:,.2f})")
                return
            
            # Get OHLCV data
            ohlcv_data = self.get_ohlcv_data(token_id)
            
            # Skip if OHLCV data fetch failed
            if ohlcv_data.startswith("❌"):
                print(f"⏭️ Skipping - Failed to get OHLCV data")
                return
            
            # Add OHLCV data to token_data for analysis
            analysis_data = token_data.copy()
            analysis_data['ohlcv_data'] = ohlcv_data
            
            # Ensure all required fields exist with defaults
            for field in ['price', 'market_cap']:
                if field not in analysis_data:
                    analysis_data[field] = 0
                
            # Agent One analyzes first
            agent_one_analysis = self.agent_one.analyze(analysis_data)
            if agent_one_analysis.startswith("Error analyzing token"):
                print("⚠️ Agent One analysis failed, skipping token")
                return
            
            # Extract Agent One's recommendation
            agent_one_rec = "DO NOTHING"  # Default
            if "RECOMMENDATION:" in agent_one_analysis:
                rec_line = agent_one_analysis.split("\n")[0]
                if "BUY" in rec_line:
                    agent_one_rec = "BUY"
                elif "SELL" in rec_line:
                    agent_one_rec = "SELL"
            
            print("\n🤖 Agent One Analysis:")
            cprint(agent_one_analysis, "white", "on_green")
            
            # Agent Two responds
            agent_two_analysis = self.agent_two.analyze(analysis_data, agent_one_analysis)
            if agent_two_analysis.startswith("Error analyzing token"):
                print("⚠️ Agent Two analysis failed, skipping token")
                return
            
            # Extract Agent Two's recommendation
            agent_two_rec = "DO NOTHING"  # Default
            if "RECOMMENDATION:" in agent_two_analysis:
                rec_line = agent_two_analysis.split("\n")[0]
                if "BUY" in rec_line:
                    agent_two_rec = "BUY"
                elif "SELL" in rec_line:
                    agent_two_rec = "SELL"
            
            print("\n🤖 Agent Two Analysis:")
            cprint(agent_two_analysis, "white", "on_green")
            
            # Save analysis to log
            try:
                self.analysis_log = pd.concat([
                    self.analysis_log,
                    pd.DataFrame([{
                        'timestamp': datetime.now().isoformat(),
                        'token_id': token_id,
                        'symbol': symbol,
                        'name': name,
                        'price': price,
                        'volume_24h': volume,
                        'market_cap': analysis_data.get('market_cap', 0),
                        'agent_one_recommendation': agent_one_rec,
                        'agent_two_recommendation': agent_two_rec,
                        'coingecko_url': f"https://www.coingecko.com/en/coins/{token_id}"
                    }])
                ], ignore_index=True)
                
                # Save to CSV
                self.analysis_log.to_csv(AI_ANALYSIS_FILE, index=False)
                print(f"\n💾 Analysis saved to {AI_ANALYSIS_FILE}")
                print(f"📊 Recommendations: Agent One: {agent_one_rec} | Agent Two: {agent_two_rec}")
                print(f"🔗 CoinGecko URL: https://www.coingecko.com/en/coins/{token_id}")
                
            except Exception as e:
                print(f"⚠️ Error saving analysis: {str(e)}")
            
        except Exception as e:
            print(f"⚠️ Error analyzing {token_data.get('name', 'Unknown')}: {str(e)}")
            
    def run_analysis_cycle(self):
        """Run one complete analysis cycle with parallel processing"""
        try:
            print("\n🔄 Starting New Analysis Round!")
            
            # Load discovered tokens
            discovered_tokens_df = self.load_discovered_tokens()
            
            # Sort by volume for efficiency
            discovered_tokens_df = discovered_tokens_df.sort_values('volume_24h', ascending=False)
            
            # Split into batches for parallel processing
            batch_size = max(1, len(discovered_tokens_df) // PARALLEL_PROCESSES)
            batches = [discovered_tokens_df[i:i + batch_size] for i in range(0, len(discovered_tokens_df), batch_size)]
            
            print(f"\n📊 Processing {len(discovered_tokens_df)} tokens in {len(batches)} batches")
            print(f"⚡ Using {PARALLEL_PROCESSES} parallel processes")
            print(f"⏰ Minimum {HOURS_BETWEEN_RUNS} hours between token analysis")
            
            # Process each batch
            for i, batch in enumerate(batches, 1):
                print(f"\n🔄 Processing batch {i}/{len(batches)} ({len(batch)} tokens)")
                self.analyze_tokens_parallel(batch)
                
            # After completing the analysis, create filtered buy recommendations
            if AI_ANALYSIS_FILE.exists():
                # Read the full analysis file
                full_analysis = pd.read_csv(AI_ANALYSIS_FILE)
                
                # Safety check: Ensure all entries have CoinGecko URLs
                print("\n🔍 Checking for missing CoinGecko URLs...")
                if 'coingecko_url' not in full_analysis.columns:
                    print("➕ Adding CoinGecko URL column")
                    full_analysis['coingecko_url'] = full_analysis['token_id'].apply(
                        lambda x: f"https://www.coingecko.com/en/coins/{x}"
                    )
                else:
                    # Fill in any missing URLs
                    missing_urls = full_analysis['coingecko_url'].isna()
                    if missing_urls.any():
                        print(f"🔗 Adding missing URLs for {missing_urls.sum()} entries")
                        full_analysis.loc[missing_urls, 'coingecko_url'] = full_analysis.loc[missing_urls, 'token_id'].apply(
                            lambda x: f"https://www.coingecko.com/en/coins/{x}"
                        )
                
                # Save the updated full analysis
                full_analysis.to_csv(AI_ANALYSIS_FILE, index=False)
                print("💾 Saved updated analysis with CoinGecko URLs")
                
                # Filter for tokens where at least one agent recommended BUY
                # and market cap is under MAX_MARKET_CAP
                buy_recommendations = full_analysis[
                    ((full_analysis['agent_one_recommendation'] == 'BUY') | 
                    (full_analysis['agent_two_recommendation'] == 'BUY')) &
                    (full_analysis['market_cap'] <= MAX_MARKET_CAP)
                ]
                
                # Sort by timestamp descending to show newest first
                buy_recommendations = buy_recommendations.sort_values('timestamp', ascending=False)
                
                # Save to new CSV
                buys_file = Path("src/data/ai_analysis_buys.csv")
                buy_recommendations.to_csv(buys_file, index=False)
                
                print(f"\n💰 Found {len(buy_recommendations)} buy recommendations under ${MAX_MARKET_CAP:,.0f} market cap")
                print(f"📝 Buy recommendations saved to: {buys_file.absolute()}")
                
            print("\n✨ Analysis round complete!")
            print(f"📊 Processed {len(discovered_tokens_df)} tokens")
            print(f"💾 Results saved to {AI_ANALYSIS_FILE}")
            
        except Exception as e:
            print(f"❌ Error in analysis cycle: {str(e)}")
            
        # Schedule next round
        next_run = datetime.now() + timedelta(hours=HOURS_BETWEEN_RUNS)
        print(f"\n⏳ Next round starts in {HOURS_BETWEEN_RUNS} hours (at {next_run.strftime('%H:%M:%S')})")

def main():
    """Main function to run the Listing Arb system"""
    print("\n🌙 Moon Dev's Listing Arb System Starting Up! 🚀")
    print(f"⚙️ Configuration:")
    print(f"  • Hours between full runs: {HOURS_BETWEEN_RUNS}")
    print(f"  • Parallel processes: {PARALLEL_PROCESSES}")
    print(f"  • Minimum volume: ${MIN_VOLUME_USD:,.2f}")
    print(f"📝 Reading discovered tokens from: {DISCOVERED_TOKENS_FILE.absolute()}")
    print(f"📝 Saving AI analysis to: {AI_ANALYSIS_FILE.absolute()}")
    
    system = ListingArbSystem()
    
    try:
        round_number = 1
        while True:
            print(f"\n🔄 Starting Round {round_number}")
            system.run_analysis_cycle()
            
            next_round = datetime.now() + timedelta(hours=HOURS_BETWEEN_RUNS)
            print(f"\n⏳ Next round starts in {HOURS_BETWEEN_RUNS} hours (at {next_round.strftime('%H:%M:%S')})")
            time.sleep(HOURS_BETWEEN_RUNS * 3600)
            round_number += 1
            
    except KeyboardInterrupt:
        print("\n👋 Moon Dev's Listing Arb System signing off!")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        raise

if __name__ == "__main__":
    main()