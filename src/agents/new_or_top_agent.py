"""
🌙 Moon Dev's New & Top Coins Agent 🔍

This agent goes through and analyzes all of the new tokens that have been listed in the coin gecko and then also analyzes the top movers of the last 24 hours on coin gecko and then makes recommendations based off that data. 

=================================
📚 QUICK START GUIDE
=================================
1. Set up environment variables in .env:
   - COINGECKO_API_KEY
   - ANTHROPIC_KEY (for Claude)
   - DEEPSEEK_KEY (for DeepSeek)

2. Choose AI model by setting MODEL_OVERRIDE at top of file:
   ```python
   # Use config.py's AI_MODEL (Default)
   MODEL_OVERRIDE = "0"  
   
   # For DeepSeek Chat (Faster, more concise)
   MODEL_OVERRIDE = "deepseek-chat"  
   
   # For DeepSeek Reasoner (Better reasoning, more detailed)
   MODEL_OVERRIDE = "deepseek-reasoner"
   ```

   🔍 Model Comparison:
   - Claude (from config.py): Balanced analysis, good for general use
   - DeepSeek Chat: Faster responses, more concise analysis
   - DeepSeek Reasoner: Better for complex market analysis, 
     provides more detailed reasoning

   To switch models:
   1. Get your DeepSeek API key from: https://platform.deepseek.com
   2. Add it to .env as DEEPSEEK_KEY="your_key_here"
   3. Set MODEL_OVERRIDE to your preferred model
   4. Restart the agent

3. Run the agent:
   python src/agents/new_or_top_agent.py

4. Check results in src/data/coingecko_results:
   - top_gainers_losers.csv (Raw data of top performers)
   - new_coins.csv (Latest 200 added coins)
   - ai_picks.csv (AI analysis and recommendations)
   - ai_buys.csv (Only BUY recommendations)

The agent runs every hour and:
- Fetches top 30 gainers and losers
- Gets latest 200 new coins
- Analyzes each coin with AI
- Saves BUY/SELL/DO NOTHING recommendations

=================================
🤖 AI ANALYSIS PROMPT
=================================
You can modify this prompt to customize the AI analysis:
"""

AI_PROMPT = """
Please analyze this cryptocurrency and provide a clear BUY, SELL, or DO NOTHING recommendation.

Coin Information:
• Name: {name}
• Symbol: {symbol}
• Source: {source_type}

Market Data (USD):
• Current Price: ${price:,.8f}
• 24h Open: ${open:,.8f}
• 24h High: ${high:,.8f}
• 24h Low: ${low:,.8f}
• 24h Volume: ${volume:,.2f}
• Market Cap Rank: #{market_cap_rank}
• 24h Change: {change:,.2f}%
• 7d Change: {change_7d:,.2f}%
• 30d Change: {change_30d:,.2f}%

Community Data:
{community_data}

IMPORTANT: Start your response with one of these recommendations:
RECOMMENDATION: BUY
RECOMMENDATION: SELL
RECOMMENDATION: DO NOTHING

Then provide your detailed analysis.
"""

"""
Main Agent Code Below
=================================
"""

import os
import requests
import pandas as pd
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from src.agents.model_helper import get_agent_model
from typing import Dict, List
import time
from termcolor import colored, cprint
import random
import src.config as config

# Load environment variables
load_dotenv()

# Model override settings
# Set to "0" to use config.py's AI_MODEL setting
# Available models:
# - "deepseek-chat" (DeepSeek's V3 model - fast & efficient)
# - "deepseek-reasoner" (DeepSeek's R1 reasoning model)
# - "0" (Use config.py's AI_MODEL setting)
MODEL_OVERRIDE = "deepseek-chat"  # Set to "0" to disable override

# DeepSeek API settings
DEEPSEEK_BASE_URL = "https://api.deepseek.com"  # Base URL for DeepSeek API

# 🤖 Agent Model Selection
AI_MODEL = MODEL_OVERRIDE if MODEL_OVERRIDE != "0" else config.AI_MODEL

# Configuration
COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY")
BASE_URL = "https://pro-api.coingecko.com/api/v3"
RESULTS_DIR = Path("src/data/coingecko_results")
DELAY_BETWEEN_REQUESTS = 1  # Seconds between API calls

# Output files
TOP_GAINERS_LOSERS_FILE = RESULTS_DIR / "top_gainers_losers.csv"
NEW_COINS_FILE = RESULTS_DIR / "new_coins.csv"
AI_PICKS_FILE = RESULTS_DIR / "ai_picks.csv"
AI_BUYS_FILE = RESULTS_DIR / "ai_buys.csv"  # New file for buy signals

# Create results directory
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Fun emoji sets for different actions
SPINNER_EMOJIS = ['🌍', '🌎', '🌏']  # Earth spinning
MOON_PHASES = ['🌑', '🌒', '🌓', '🌔', '🌕', '🌖', '🌗', '🌘']  # Moon phases
ROCKET_SEQUENCE = ['🚀', '💫', '✨', '💫', '🌟']  # Rocket launch
ERROR_EMOJIS = ['💥', '🚨', '⚠️', '❌', '🔥']  # Error indicators
SUCCESS_EMOJIS = ['✨', '🎯', '🎨', '🎪', '🎭', '🎪']  # Success indicators

def print_spinner(message: str, emoji_set: List[str], color: str = 'white', bg_color: str = 'on_blue'):
    """Print a spinning emoji animation with message"""
    for emoji in emoji_set:
        print(f"\r{emoji} {colored(message, color, bg_color)}", end='', flush=True)
        time.sleep(0.2)
    print()  # New line after animation

def print_fancy(message: str, color: str = 'white', bg_color: str = 'on_blue', emojis: List[str] = None):
    """Print a message with random emojis from set"""
    if emojis:
        emoji = random.choice(emojis)
        cprint(f"{emoji} {message} {emoji}", color, bg_color)
    else:
        cprint(message, color, bg_color)

class NewOrTopAgent:
    """Agent for analyzing new and top performing coins"""
    
    def __init__(self):
        self.headers = {
            "x-cg-pro-api-key": COINGECKO_API_KEY,
            "Content-Type": "application/json"
        }
        
        # Initialize AI model via OpenRouter
        self.model = get_agent_model(verbose=True)
        if not self.model:
            raise ValueError("🚨 Failed to initialize AI model!")
            
        print_fancy("🌙 Moon Dev's New & Top Coins Agent Initialized! 🌟", 'white', 'on_magenta', SUCCESS_EMOJIS)
        
    def get_top_gainers(self) -> pd.DataFrame:
        """Get only top gainers (positive performers)"""
        try:
            print_spinner("🚀 Fetching top gainers...", ROCKET_SEQUENCE, 'cyan', 'on_blue')
            response = requests.get(
                f"{BASE_URL}/coins/top_gainers_losers",
                headers=self.headers,
                params={
                    "vs_currency": "usd",
                    "sparkline": "false"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract only gainers
                gainers = pd.DataFrame(data.get('top_gainers', []))
                
                if not gainers.empty:
                    gainers['type'] = 'gainer'
                    gainers['timestamp'] = datetime.now().isoformat()
                    # Add CoinGecko URL
                    gainers['coingecko_url'] = gainers['id'].apply(lambda x: f"https://www.coingecko.com/en/coins/{x}")
                    gainers.to_csv(TOP_GAINERS_LOSERS_FILE, index=False)
                    
                    # Print each gainer with its price change
                    print_fancy("\n🚀 Top Gainers Found:", 'white', 'on_green')
                    for _, coin in gainers.iterrows():
                        gain_str = f"+{coin['usd_24h_change']:,.2f}%" if 'usd_24h_change' in coin else 'N/A'
                        price_str = f"${coin['usd']:,.8f}" if 'usd' in coin else 'N/A'
                        print_fancy(f"{coin['name']} ({coin['symbol'].upper()}): {gain_str} @ {price_str}", 'green', 'on_grey', ['💰', '🚀', '📈'])
                    
                    return gainers
                else:
                    print_fancy("No gainers found in this cycle", 'yellow', 'on_grey')
                    return pd.DataFrame()
                
            else:
                print_fancy(f"Error fetching top gainers: {response.text}", 'white', 'on_red', ERROR_EMOJIS)
                return pd.DataFrame()
                
        except Exception as e:
            print_fancy(f"Error: {str(e)}", 'white', 'on_red', ERROR_EMOJIS)
            return pd.DataFrame()
            
    def get_new_coins(self) -> pd.DataFrame:
        """Get recently added coins"""
        try:
            print_spinner("Scanning for new coins...", MOON_PHASES, 'yellow', 'on_blue')
            response = requests.get(
                f"{BASE_URL}/coins/list/new",
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                df = pd.DataFrame(data)
                df['timestamp'] = datetime.now().isoformat()
                # Add CoinGecko URL
                df['coingecko_url'] = df['id'].apply(lambda x: f"https://www.coingecko.com/en/coins/{x}")
                df.to_csv(NEW_COINS_FILE, index=False)
                
                print_fancy(f"Discovered {len(df)} new cosmic tokens! 🪐", 'cyan', 'on_grey', SUCCESS_EMOJIS)
                return df
                
            else:
                print_fancy(f"Error fetching new coins: {response.text}", 'white', 'on_red', ERROR_EMOJIS)
                return pd.DataFrame()
                
        except Exception as e:
            print_fancy(f"Error: {str(e)}", 'white', 'on_red', ERROR_EMOJIS)
            return pd.DataFrame()
            
    def get_coin_data(self, coin_id: str) -> Dict:
        """Get detailed data for a coin"""
        try:
            print_spinner(f"Analyzing {coin_id}...", ROCKET_SEQUENCE, 'yellow', 'on_blue')
            
            # Get OHLCV data first
            ohlcv_response = requests.get(
                f"{BASE_URL}/coins/{coin_id}/ohlc",
                headers=self.headers,
                params={"vs_currency": "usd", "days": "1"}
            )
            
            # Get main coin data
            response = requests.get(
                f"{BASE_URL}/coins/{coin_id}",
                headers=self.headers,
                params={
                    "localization": False,
                    "tickers": True,
                    "market_data": True,
                    "community_data": True,
                    "developer_data": False  # No longer needed
                }
            )
            
            if response.status_code == 200 and ohlcv_response.status_code == 200:
                coin_data = response.json()
                ohlcv_data = ohlcv_response.json()
                
                # Convert OHLCV to DataFrame without printing
                if ohlcv_data and len(ohlcv_data) > 0:
                    ohlcv_df = pd.DataFrame(ohlcv_data, columns=['timestamp', 'open', 'high', 'low', 'close'])
                    latest_ohlcv = ohlcv_df.iloc[-1]
                    
                    # Create market data DataFrame
                    market_data = {
                        'price': coin_data.get('market_data', {}).get('current_price', {}).get('usd', 0),
                        'open': latest_ohlcv['open'],
                        'high': latest_ohlcv['high'],
                        'low': latest_ohlcv['low'],
                        'close': latest_ohlcv['close'],
                        'volume': coin_data.get('market_data', {}).get('total_volume', {}).get('usd', 0),
                        'market_cap_rank': coin_data.get('market_cap_rank', 'N/A'),
                        'change_24h': coin_data.get('market_data', {}).get('price_change_percentage_24h', 0),
                        'change_7d': coin_data.get('market_data', {}).get('price_change_percentage_7d', 0),
                        'change_30d': coin_data.get('market_data', {}).get('price_change_percentage_30d', 0)
                    }
                    
                    market_df = pd.DataFrame([market_data])
                    coin_data['market_data_df'] = market_df
                    coin_data['ohlcv_df'] = ohlcv_df
                    
                print_fancy(f"✨ Intel gathered on {coin_id}!", 'green', 'on_grey', SUCCESS_EMOJIS)
                return coin_data
            else:
                print_fancy(f"Error fetching coin data: {response.text}", 'white', 'on_red', ERROR_EMOJIS)
                return {}
                
        except Exception as e:
            print_fancy(f"Error: {str(e)}", 'white', 'on_red', ERROR_EMOJIS)
            return {}
            
    def analyze_coin(self, coin_data: Dict, source_type: str) -> str:
        """Analyze a coin using AI"""
        try:
            name = coin_data.get('name')
            symbol = coin_data.get('symbol', '').upper()
            
            # Clear visual break before new analysis
            print("\n" + "=" * 80)
            print_fancy("🤖 STARTING NEW AI ANALYSIS 🤖", 'white', 'on_magenta', ROCKET_SEQUENCE)
            print("=" * 80)
            
            # Show which coin we're analyzing
            print_fancy(f"Token: {name} ({symbol})", 'cyan', 'on_grey')
            price_str = f"${coin_data.get('market_data', {}).get('current_price', {}).get('usd', 0):,.8f}"
            print_fancy(f"Current Price: {price_str}", 'cyan', 'on_grey')
            print("=" * 80 + "\n")
            
            market_df = coin_data.get('market_data_df')
            if market_df is None or market_df.empty:
                print_fancy("No market data available!", 'white', 'on_red', ERROR_EMOJIS)
                return "Error: No market data available"
                
            market_data = market_df.iloc[0]
            
            # Format coin data for analysis
            prompt = AI_PROMPT.format(
                name=name,
                symbol=symbol,
                source_type=source_type,
                price=market_data['price'],
                open=market_data['open'],
                high=market_data['high'],
                low=market_data['low'],
                volume=market_data['volume'],
                market_cap_rank=market_data['market_cap_rank'],
                change=market_data['change_24h'],
                change_7d=market_data['change_7d'],
                change_30d=market_data['change_30d'],
                community_data=json.dumps(coin_data.get('community_data', {}), indent=2)
            )
            
            print_fancy("🧠 AI Agent Processing...", 'yellow', 'on_blue', SPINNER_EMOJIS)
            
            # Get AI response via OpenRouter
            response = self.model.generate_response(
                system_prompt="You are a cryptocurrency analyst.",
                user_content=prompt,
                temperature=0.7,
                max_tokens=500
            )

            # Parse response
            if response and hasattr(response, 'content'):
                analysis = response.content
            else:
                analysis = str(response)
                
            # Extract and display recommendation prominently
            recommendation = self.extract_recommendation(analysis)
            change_str = f"{market_data['change_24h']:+.2f}%"
            
            # Show recommendation with dramatic spacing
            print("\n" + "🎯 " * 20)
            if recommendation == "BUY":
                print_fancy(f"RECOMMENDATION FOR {name} ({symbol}):", 'white', 'on_green', ['💰', '🚀'])
                print_fancy(f"BUY @ {price_str} ({change_str})", 'white', 'on_green', ['💰', '🚀', '📈'])
            elif recommendation == "SELL":
                print_fancy(f"RECOMMENDATION FOR {name} ({symbol}):", 'white', 'on_red', ['💸', '📉'])
                print_fancy(f"SELL @ {price_str} ({change_str})", 'white', 'on_red', ['💸', '🔻', '📉'])
            else:
                print_fancy(f"RECOMMENDATION FOR {name} ({symbol}):", 'white', 'on_blue', ['🎯', '⏳'])
                print_fancy(f"DO NOTHING @ {price_str} ({change_str})", 'white', 'on_blue', ['🎯', '⏳', '🔄'])
            print("🎯 " * 20 + "\n")
            
            # End of analysis marker
            print("=" * 80)
            print_fancy("AI ANALYSIS COMPLETE", 'white', 'on_magenta', SUCCESS_EMOJIS)
            print("=" * 80 + "\n")
            
            return analysis
            
        except Exception as e:
            print_fancy(f"Error in AI analysis: {str(e)}", 'white', 'on_red', ERROR_EMOJIS)
            return "Error in analysis"
            
    def extract_recommendation(self, analysis: str) -> str:
        """Extract BUY/SELL/DO NOTHING from analysis"""
        if "RECOMMENDATION: BUY" in analysis:
            return "BUY"
        elif "RECOMMENDATION: SELL" in analysis:
            return "SELL"
        return "DO NOTHING"
        
    def save_analysis(self, result: Dict):
        """Save a single analysis result to CSV"""
        df = pd.DataFrame([result])
        
        # Save to main picks file
        if os.path.exists(AI_PICKS_FILE):
            df.to_csv(AI_PICKS_FILE, mode='a', header=False, index=False)
        else:
            df.to_csv(AI_PICKS_FILE, index=False)
        
        # If it's a BUY recommendation, also save to buys file
        if result['recommendation'] == "BUY":
            if os.path.exists(AI_BUYS_FILE):
                df.to_csv(AI_BUYS_FILE, mode='a', header=False, index=False)
            else:
                df.to_csv(AI_BUYS_FILE, index=False)
            print_fancy(f"💰 Added {result['name']} to AI Buys!", 'white', 'on_green', ['💰', '🚀', '📈'])
        else:
            print_fancy(f"💾 Saved analysis for {result['name']}", 'white', 'on_green', SUCCESS_EMOJIS)
            
    def run_analysis(self):
        """Run complete analysis cycle"""
        print_spinner("🚀 Initiating Moon Dev Analysis Sequence...", ROCKET_SEQUENCE, 'white', 'on_magenta')
        
        # Get only top gainers and new coins
        top_gainers_df = self.get_top_gainers()
        new_coins_df = self.get_new_coins()
        
        total_analyzed = 0
        
        # Analyze top gainers
        if not top_gainers_df.empty:
            for _, coin in top_gainers_df.iterrows():
                coin_data = self.get_coin_data(coin['id'])
                if coin_data:
                    analysis = self.analyze_coin(coin_data, "Top gainer")
                    recommendation = self.extract_recommendation(analysis)
                    
                    result = {
                        'timestamp': datetime.now().isoformat(),
                        'coin_id': coin['id'],
                        'name': coin['name'],
                        'symbol': coin['symbol'],
                        'source': "Top gainer",
                        'price_usd': coin['usd'],
                        'volume_24h': coin['usd_24h_vol'],
                        'price_change_24h': coin['usd_24h_change'],
                        'recommendation': recommendation,
                        'coingecko_url': coin['coingecko_url']
                    }
                    
                    # Save each analysis immediately
                    self.save_analysis(result)
                    total_analyzed += 1
                    
                time.sleep(DELAY_BETWEEN_REQUESTS)
                
        # Analyze new coins
        if not new_coins_df.empty:
            for _, coin in new_coins_df.iterrows():
                coin_data = self.get_coin_data(coin['id'])
                if coin_data:
                    analysis = self.analyze_coin(coin_data, "Recently Added")
                    recommendation = self.extract_recommendation(analysis)
                    
                    result = {
                        'timestamp': datetime.now().isoformat(),
                        'coin_id': coin['id'],
                        'name': coin['name'],
                        'symbol': coin['symbol'],
                        'source': "Recently Added",
                        'price_usd': coin_data.get('market_data', {}).get('current_price', {}).get('usd', 0),
                        'volume_24h': coin_data.get('market_data', {}).get('total_volume', {}).get('usd', 0),
                        'recommendation': recommendation,
                        'coingecko_url': coin['coingecko_url']
                    }
                    
                    # Save each analysis immediately
                    self.save_analysis(result)
                    total_analyzed += 1
                    
                time.sleep(DELAY_BETWEEN_REQUESTS)
                
        # Print final summary
        if total_analyzed > 0:
            print_fancy("\n🎮 ANALYSIS COMPLETE 🎮", 'white', 'on_green')
            print_fancy("=" * 50, 'blue', 'on_white')
            
            # Read the full file to get summary
            results_df = pd.read_csv(AI_PICKS_FILE)
            summary = results_df['recommendation'].value_counts()
            
            print_fancy(f"BUY: {summary.get('BUY', 0)} 💰", 'green', 'on_grey')
            print_fancy(f"SELL: {summary.get('SELL', 0)} 📉", 'red', 'on_grey')
            print_fancy(f"DO NOTHING: {summary.get('DO NOTHING', 0)} 🎯", 'yellow', 'on_grey')
            print_fancy("=" * 50, 'blue', 'on_white')

def main():
    """Main function to run the agent"""
    print_fancy("\n🌙 Moon Dev's Cosmic Token Analysis Starting! 🌟", 'white', 'on_magenta', SUCCESS_EMOJIS)
    agent = NewOrTopAgent()
    
    try:
        while True:
            agent.run_analysis()
            for emoji in MOON_PHASES:
                print_fancy(f"{emoji} Waiting for next analysis cycle...", 'cyan', 'on_blue')
                time.sleep(450)  # 450 * 8 = 3600 (1 hour)
            
    except KeyboardInterrupt:
        print_fancy("\n👋 Agent stopped by user - Moon Dev out! 🌙", 'white', 'on_magenta')
    except Exception as e:
        print_fancy(f"\nError: {str(e)}", 'white', 'on_red', ERROR_EMOJIS)

if __name__ == "__main__":
    main()
