from pathlib import Path

"""
🌙 Moon Dev's CoinGecko Agent 🦎
Provides comprehensive access to CoinGecko API data and market intelligence

=================================
📚 FILE OVERVIEW & DOCUMENTATION
=================================

This file implements a multi-agent AI trading system that analyzes crypto markets using CoinGecko data.
The system consists of three specialized agents working together:

1. Agent One (Technical Analysis) 📊
   - Focuses on charts, patterns, and technical indicators
   - Uses shorter-term analysis for trading opportunities
   - Configured with AGENT_ONE_MODEL and AGENT_ONE_MAX_TOKENS

2. Agent Two (Fundamental Analysis) 🌍
   - Analyzes macro trends and fundamental data
   - Provides longer-term market perspective
   - Configured with AGENT_TWO_MODEL and AGENT_TWO_MAX_TOKENS

3. Token Extractor Agent 🔍
   - Monitors agent conversations
   - Extracts mentioned tokens/symbols
   - Maintains historical token discussion data
   - Uses minimal tokens/temperature for precise extraction

Key Components:
--------------
1. Configuration Section
   - Model selection for each agent
   - Response length control (max_tokens)
   - Creativity control (temperature)
   - Round timing configuration

2. Memory System
   - Stores agent conversations in JSON files
   - Maintains token discussion history in CSV
   - Keeps track of last 50 rounds
   - Auto-cleans old memory files

3. CoinGecko API Integration
   - Comprehensive market data access
   - Rate limiting and error handling
   - Multiple endpoints (prices, trends, history)

4. Game Loop Structure
   - Runs in continuous rounds
   - Each round:
     a. Fetch fresh market data
     b. Agent One analyzes
     c. Agent Two responds
     d. Extract mentioned tokens
     e. Generate round synopsis
     f. Wait for next round

5. Output Formatting
   - Colorful terminal output
   - Clear section headers
   - Structured agent responses
   - Easy-to-read summaries

File Structure:
--------------
1. Configuration & Constants
2. Helper Functions (print_banner, print_section)
3. Core Classes:
   - AIAgent: Base agent functionality
   - CoinGeckoAPI: API wrapper
   - TokenExtractorAgent: Symbol extraction
   - MultiAgentSystem: Orchestrates everything

Usage:
------
1. Ensure environment variables are set:
   - ANTHROPIC_KEY
   - COINGECKO_API_KEY

2. Run the file directly:
   python src/agents/coingecko_agent.py

3. Or import the classes:
   from agents.coingecko_agent import MultiAgentSystem

Configuration:
-------------
Adjust the constants at the top of the file to:
- Change agent models
- Modify response lengths
- Control creativity levels
- Adjust round timing

Memory Files:
------------
- src/data/agent_memory/agent_one.json
- src/data/agent_memory/agent_two.json
- src/data/agent_discussed_tokens.csv

Author: Moon Dev 🌙
"""

# Model override settings
# Set to "0" to use config.py's AI_MODEL setting
# Available models:
# - "deepseek-chat" (DeepSeek's V3 model - fast & efficient)
# - "deepseek-reasoner" (DeepSeek's R1 reasoning model)
# - "0" (Use config.py's AI_MODEL setting)
# Model settings managed via model_helper for unified access

# 🤖 Agent Prompts & Personalities
AGENT_ONE_PROMPT = """
You are Agent One - The Technical Analysis Expert 📊
Your role is to analyze charts, patterns, and market indicators to identify trading opportunities.

Focus on:
- Price action and chart patterns
- Technical indicators (RSI, MACD, etc.)
- Volume analysis
- Support/resistance levels
- Short to medium-term opportunities

Remember to be specific about entry/exit points and always consider Moon Dev's risk management rules! 🎯
"""

AGENT_TWO_PROMPT = """
You are Agent Two - The Fundamental Analysis Expert 🌍
Your role is to analyze macro trends, project fundamentals, and long-term potential.

Focus on:
- Project fundamentals and technology
- Team and development activity
- Market trends and sentiment
- Competitor analysis
- Long-term growth potential

Always consider the bigger picture and help guide Moon Dev's long-term strategy! 🚀
"""

TOKEN_EXTRACTOR_PROMPT = """
You are the Token Extraction Agent 🔍
Your role is to identify and extract all cryptocurrency symbols and tokens mentioned in conversations.

Rules:
- Extract both well-known (BTC, ETH) and newer tokens
- Include tokens mentioned by name or symbol
- Format as a clean list of symbols
- Be thorough but avoid duplicates
- When only a name is given, provide the symbol

Keep Moon Dev's token tracking clean and organized! 📝
"""

SYNOPSIS_AGENT_PROMPT = """
You are the Round Synopsis Agent 📊
Your role is to create clear, concise summaries of trading discussions.

Guidelines:
- Summarize key points in 1-2 sentences
- Focus on actionable decisions
- Highlight agreement between agents
- Note significant market observations
- Track progress toward the $10M goal

Help Moon Dev keep track of the trading journey! 🎯
"""

# 🤖 Agent Model Selection
# AI models now managed via OpenRouter for unified access
AGENT_ONE_MODEL = "claude-3-haiku-20240307"  # For reference
AGENT_TWO_MODEL = "claude-3-sonnet-20240229"  # For reference
TOKEN_EXTRACTOR_MODEL = "claude-3-haiku-20240307"  # For reference

# 🎮 Game Configuration
MINUTES_BETWEEN_ROUNDS = 30  # Time to wait between trading rounds (in minutes)

# 🔧 Agent Response Configuration
# Max Tokens (Controls response length):
AGENT_ONE_MAX_TOKENS = 1000    # Technical analysis needs decent space (500-1000 words)
AGENT_TWO_MAX_TOKENS = 1000    # Fundamental analysis might need more detail (600-1200 words)
EXTRACTOR_MAX_TOKENS = 100     # Keep it brief, just token lists (50-100 words)
SYNOPSIS_MAX_TOKENS = 100      # Brief round summaries (50-100 words)

# Temperature (Controls response creativity/randomness):
AGENT_ONE_TEMP = 0.7    # Balanced creativity for technical analysis (0.5-0.8)
AGENT_TWO_TEMP = 0.7    # Balanced creativity for fundamental analysis (0.5-0.8)
EXTRACTOR_TEMP = 0      # Zero creativity, just extract tokens (always 0)
SYNOPSIS_TEMP = 0.3     # Low creativity for consistent summaries (0.2-0.4)

# Token Log File
TOKEN_LOG_FILE = Path("src/data/agent_discussed_tokens.csv")

# Available Models:
# - claude-3-opus-20240229    (Most powerful, longest responses)
# - claude-3-sonnet-20240229  (Balanced performance)
# - claude-3-haiku-20240307   (Fastest, shorter responses)
# - claude-2.1                (Previous generation)
# - claude-2.0                (Previous generation)

"""
Response Length Guide (max_tokens):
50-100:   Ultra concise, bullet points
100-200:  Short paragraphs
500-800:  Detailed explanation
1000+:    In-depth analysis

Temperature Guide:
0.0:  Deterministic, same response every time
0.3:  Very focused, minimal variation
0.7:  Creative but stays on topic
1.0:  Maximum creativity/variation
"""

"""
SYSTEM GOAL:
Two AI agents (Haiku & Sonnet) collaborate to grow a $10,000 portfolio to $10,000,000 using CoinGecko's 
comprehensive crypto data (since 2014). They analyze market trends, identify opportunities, and make 
strategic decisions together while maintaining a conversation log in the data folder.

Agent One: Technical Analysis Expert 📊
Agent Two: Fundamental/Macro Analysis Expert 🌍
"""


import os
import requests
import pandas as pd
import json
from typing import Dict, List, Optional, Union
from datetime import datetime, timedelta
import time
from dotenv import load_dotenv
from termcolor import colored, cprint
from pathlib import Path
from src.agents.model_helper import get_agent_model

# Local imports
from src.config import *

# Load environment variables
load_dotenv()

def print_banner():
    """Print a fun colorful banner"""
    cprint("\n" + "="*70, "white", "on_blue")
    cprint("🌙 🎮 Moon Dev's Crypto Trading Game! 🎮 🌙", "white", "on_magenta", attrs=["bold"])
    cprint("="*70 + "\n", "white", "on_blue")

def print_section(title: str, color: str = "on_blue"):
    """Print a section header"""
    cprint(f"\n{'='*35}", "white", color)
    cprint(f" {title} ", "white", color, attrs=["bold"])
    cprint(f"{'='*35}\n", "white", color)

# Create data directory for agent memory in the correct project structure
AGENT_MEMORY_DIR = Path("src/data/agent_memory")
AGENT_MEMORY_DIR.mkdir(parents=True, exist_ok=True)

def cleanup_old_memory_files():
    """Clean up old memory files from previous naming conventions"""
    old_files = ['haiku_memory.json', 'sonnet_memory.json']
    for file in old_files:
        try:
            old_file = AGENT_MEMORY_DIR / file
            if old_file.exists():
                old_file.unlink()
                cprint(f"🧹 Cleaned up old memory file: {file}", "white", "on_blue")
        except Exception as e:
            cprint(f"⚠️ Error cleaning up {file}: {e}", "white", "on_yellow")

print(f"📁 Agent memory directory: {AGENT_MEMORY_DIR}")
cleanup_old_memory_files()  # Clean up old files on startup

class AIAgent:
    """Individual AI Agent for collaborative decision making"""
    
    def __init__(self, name: str):
        self.name = name

        # Initialize AI model via OpenRouter
        self.model = get_agent_model(verbose=True)
        if not self.model:
            raise ValueError(f"🚨 Failed to initialize AI model for {name}!")
            
        # Use a simpler memory file name
        self.memory_file = AGENT_MEMORY_DIR / f"{name.lower().replace(' ', '_')}.json"
        self.load_memory()
        
    def load_memory(self):
        """Load agent's memory from file"""
        if self.memory_file.exists():
            with open(self.memory_file, 'r') as f:
                self.memory = json.load(f)
        else:
            self.memory = {
                'conversations': [],
                'decisions': [],
                'portfolio_history': []
            }
            self.save_memory()
            
    def save_memory(self):
        """Save agent's memory to file"""
        with open(self.memory_file, 'w') as f:
            json.dump(self.memory, f, indent=2)
            
    def think(self, market_data: Dict, other_agent_message: str = None) -> str:
        """Process market data and other agent's message to make decisions"""
        try:
            print_section(f"🤔 {self.name} is thinking...", "on_magenta")
            
            # Get the right configuration based on agent name
            max_tokens = AGENT_ONE_MAX_TOKENS if self.name == "Agent One" else AGENT_TWO_MAX_TOKENS
            temperature = AGENT_ONE_TEMP if self.name == "Agent One" else AGENT_TWO_TEMP
            prompt = AGENT_ONE_PROMPT if self.name == "Agent One" else AGENT_TWO_PROMPT
            
            # Add market data context
            market_context = f"""
Current Market Data:
{json.dumps(market_data, indent=2)}

Previous Agent Message:
{other_agent_message if other_agent_message else 'No previous message'}

Remember to format your response like this:

🤖 Hey Moon Dev! {self.name} here!
=================================

📊 Market Vibes:
[Your main market thoughts in simple terms]

💡 Opportunities I See:
- [Opportunity 1]
- [Opportunity 2]
- [Opportunity 3]

🎯 My Recommendations:
1. [Clear action item]
2. [Clear action item]
3. [Clear action item]

💰 Portfolio Impact:
[How this helps reach our $10M goal]

🌙 Moon Dev Wisdom:
[Fun reference to Moon Dev's trading style]
"""
            
            # Get AI response via OpenRouter
            response = self.model.generate_response(
                system_prompt=prompt,
                user_content=market_context,
                temperature=temperature,
                max_tokens=max_tokens
            )

            # Parse response
            if response and hasattr(response, 'content'):
                response_text = response.content
            else:
                response_text = str(response)
            
            # Clean up the response
            response = (response_text
                .replace("TextBlock(text='", "")
                .replace("')", "")
                .replace("\\n", "\n")
                .replace("*", "")
                .replace("```", "")
                .strip())
            
            # Add extra newlines between sections for readability
            sections = ["Market Vibes:", "Opportunities I See:", "My Recommendations:", "Portfolio Impact:", "Moon Dev Wisdom:"]
            for section in sections:
                response = response.replace(section, f"\n{section}\n")
            
            # Save to memory
            self.memory['conversations'].append({
                'timestamp': datetime.now().isoformat(),
                'market_data': market_data,
                'other_message': other_agent_message,
                'response': response
            })
            self.save_memory()
            
            return response
            
        except Exception as e:
            cprint(f"❌ Error in agent thinking: {str(e)}", "white", "on_red")
            return f"Error processing market data: {str(e)}"

class CoinGeckoAPI:
    """Utility class for CoinGecko API calls 🦎"""
    
    def __init__(self):
        self.api_key = os.getenv("COINGECKO_API_KEY")
        if not self.api_key:
            print("⚠️ Warning: COINGECKO_API_KEY not found in environment variables!")
        self.base_url = "https://pro-api.coingecko.com/api/v3"
        self.headers = {
            "x-cg-pro-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        print("🦎 Moon Dev's CoinGecko API initialized!")
        
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make API request with rate limiting and error handling"""
        try:
            url = f"{self.base_url}/{endpoint}"
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 429:
                print("⚠️ Rate limit hit! Waiting before retry...")
                time.sleep(60)  # Wait 60 seconds before retry
                return self._make_request(endpoint, params)
                
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"❌ API request failed: {str(e)}")
            return {}

    def get_ping(self) -> bool:
        """Check API server status"""
        try:
            response = self._make_request("ping")
            return "gecko_says" in response
        except:
            return False

    def get_price(self, ids: Union[str, List[str]], vs_currencies: Union[str, List[str]]) -> Dict:
        """Get current price data for coins
        
        Args:
            ids: Coin ID(s) (e.g. 'bitcoin' or ['bitcoin', 'ethereum'])
            vs_currencies: Currency(ies) to get price in (e.g. 'usd' or ['usd', 'eur'])
        """
        if isinstance(ids, str):
            ids = [ids]
        if isinstance(vs_currencies, str):
            vs_currencies = [vs_currencies]
            
        params = {
            'ids': ','.join(ids),
            'vs_currencies': ','.join(vs_currencies)
        }
        
        print(f"🔍 Getting prices for: {', '.join(ids)}")
        return self._make_request("simple/price", params)

    def get_coin_market_data(self, id: str) -> Dict:
        """Get current market data for a coin
        
        Args:
            id: Coin ID (e.g. 'bitcoin')
        """
        print(f"📊 Getting market data for {id}...")
        return self._make_request(f"coins/{id}")

    def get_trending(self) -> List[Dict]:
        """Get trending search coins (Top-7) in the last 24 hours"""
        print("🔥 Getting trending coins...")
        response = self._make_request("search/trending")
        return response.get('coins', [])

    def get_global_data(self) -> Dict:
        """Get cryptocurrency global market data"""
        print("🌍 Getting global market data...")
        return self._make_request("global")

    def get_exchanges(self) -> List[Dict]:
        """Get all exchanges data"""
        print("💱 Getting exchanges data...")
        return self._make_request("exchanges")

    def get_exchange_rates(self) -> Dict:
        """Get BTC-to-Currency exchange rates"""
        print("💱 Getting exchange rates...")
        return self._make_request("exchange_rates")

    def get_coin_history(self, id: str, date: str) -> Dict:
        """Get historical data for a coin at a specific date
        
        Args:
            id: Coin ID (e.g. 'bitcoin')
            date: Date in DD-MM-YYYY format
        """
        print(f"📅 Getting historical data for {id} on {date}...")
        return self._make_request(f"coins/{id}/history", {'date': date})

    def get_coin_market_chart(self, id: str, vs_currency: str, days: int) -> Dict:
        """Get historical market data
        
        Args:
            id: Coin ID (e.g. 'bitcoin')
            vs_currency: Currency (e.g. 'usd')
            days: Number of days of data to retrieve
        """
        params = {
            'vs_currency': vs_currency,
            'days': days
        }
        print(f"📈 Getting {days} days of market data for {id}...")
        return self._make_request(f"coins/{id}/market_chart", params)

    def get_coin_ohlc(self, id: str, vs_currency: str, days: int) -> List:
        """Get coin's OHLC data
        
        Args:
            id: Coin ID (e.g. 'bitcoin')
            vs_currency: Currency (e.g. 'usd')
            days: Number of days of data to retrieve
        """
        params = {
            'vs_currency': vs_currency,
            'days': days
        }
        print(f"📊 Getting {days} days of OHLC data for {id}...")
        return self._make_request(f"coins/{id}/ohlc", params)

class TokenExtractorAgent:
    """Agent that extracts token/crypto symbols from conversations"""
    
    def __init__(self):
        # Initialize AI model via OpenRouter
        self.model = get_agent_model(verbose=True)
        if not self.model:
            raise ValueError("🚨 Failed to initialize AI model for Token Extractor!")
        self.token_history = self._load_token_history()
        cprint("🔍 Token Extractor Agent initialized!", "white", "on_cyan")
        
    def _load_token_history(self) -> pd.DataFrame:
        """Load or create token history DataFrame"""
        if TOKEN_LOG_FILE.exists():
            return pd.read_csv(TOKEN_LOG_FILE)
        else:
            df = pd.DataFrame(columns=['timestamp', 'round', 'token', 'context'])
            df.to_csv(TOKEN_LOG_FILE, index=False)
            return df
            
    def extract_tokens(self, round_num: int, agent_one_msg: str, agent_two_msg: str) -> List[Dict]:
        """Extract tokens/symbols from agent messages"""
        try:
            print_section("🔍 Extracting Mentioned Tokens", "on_cyan")

            # Get AI response via OpenRouter
            response = self.model.generate_response(
                system_prompt=TOKEN_EXTRACTOR_PROMPT,
                user_content=f"""
Agent One said:
{agent_one_msg}

Agent Two said:
{agent_two_msg}

Extract all token symbols and return as a simple list.
""",
                temperature=EXTRACTOR_TEMP,
                max_tokens=EXTRACTOR_MAX_TOKENS
            )

            # Parse response
            if response and hasattr(response, 'content'):
                response_text = response.content
            else:
                response_text = str(response)

            # Clean up response and split into list
            tokens = response_text.strip().split('\n')
            tokens = [t.strip().upper() for t in tokens if t.strip()]
            
            # Create records for each token
            timestamp = datetime.now().isoformat()
            records = []
            for token in tokens:
                records.append({
                    'timestamp': timestamp,
                    'round': round_num,
                    'token': token,
                    'context': f"Round {round_num} discussion"
                })
                
            # Log to DataFrame
            new_records = pd.DataFrame(records)
            self.token_history = pd.concat([self.token_history, new_records], ignore_index=True)
            self.token_history.to_csv(TOKEN_LOG_FILE, index=False)
            
            # Print extracted tokens
            cprint("\n📝 Tokens Mentioned This Round:", "white", "on_cyan")
            for token in tokens:
                cprint(f"• {token}", "white", "on_cyan")
            
            return records
            
        except Exception as e:
            cprint(f"❌ Error extracting tokens: {str(e)}", "white", "on_red")
            return []

class MultiAgentSystem:
    """System managing multiple AI agents analyzing CoinGecko data"""
    
    def __init__(self):
        print_banner()
        self.api = CoinGeckoAPI()
        self.agent_one = AIAgent("Agent One")
        self.agent_two = AIAgent("Agent Two")
        self.token_extractor = TokenExtractorAgent()
        self.round_history = []  # Store round synopses
        self.max_history_rounds = 50  # Keep last 50 rounds of context
        cprint("🎮 Moon Dev's Trading Game System Ready! 🎮", "white", "on_green", attrs=["bold"])
        
    def generate_round_synopsis(self, agent_one_response: str, agent_two_response: str) -> str:
        """Generate a brief synopsis of the round's key points using Synopsis Agent"""
        try:
            message = self.agent_one.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=SYNOPSIS_MAX_TOKENS,
                temperature=SYNOPSIS_TEMP,
                system=SYNOPSIS_AGENT_PROMPT,  # Use the synopsis agent prompt
                messages=[{
                    "role": "user",
                    "content": f"""
Agent One said:
{agent_one_response}

Agent Two said:
{agent_two_response}

Create a brief synopsis of this trading round.
"""
                }]
            )
            
            synopsis = str(message.content).strip()
            return synopsis
            
        except Exception as e:
            cprint(f"⚠️ Error generating synopsis: {e}", "white", "on_yellow")
            return "Synopsis generation failed"
    
    def get_recent_history(self) -> str:
        """Get formatted string of recent round synopses"""
        if not self.round_history:
            return "No previous rounds yet."
            
        history = "\n".join([
            f"Round {i+1}: {synopsis}"
            for i, synopsis in enumerate(self.round_history[-10:])  # Show last 10 rounds
        ])
        return f"\n📜 Recent Trading History:\n{history}\n"
        
    def run_conversation_cycle(self):
        """Run one cycle of agent conversation"""
        try:
            print_section("🔄 Starting New Trading Round!", "on_blue")
            
            # Get fresh market data
            cprint("📊 Gathering Market Intelligence...", "white", "on_magenta")
            market_data = {
                'overview': self.api.get_global_data(),
                'trending': self.api.get_trending(),
                'bitcoin': self.api.get_coin_market_data('bitcoin'),
                'ethereum': self.api.get_coin_market_data('ethereum')
            }
            
            # Add round history to market context
            market_data['recent_history'] = self.get_recent_history()
            
            # Agent One starts the conversation
            print_section("🤖 Agent One's Analysis", "on_blue")
            agent_one_response = self.agent_one.think(market_data)
            print(agent_one_response)
            
            # Agent Two responds
            print_section("🤖 Agent Two's Response", "on_magenta")
            agent_two_response = self.agent_two.think(market_data, agent_one_response)
            print(agent_two_response)
            
            # Extract tokens from conversation
            self.token_extractor.extract_tokens(
                len(self.round_history) + 1,
                agent_one_response,
                agent_two_response
            )
            
            # Generate and store round synopsis
            synopsis = self.generate_round_synopsis(agent_one_response, agent_two_response)
            self.round_history.append(synopsis)
            
            # Keep only last N rounds
            if len(self.round_history) > self.max_history_rounds:
                self.round_history = self.round_history[-self.max_history_rounds:]
            
            # Print round synopsis
            print_section("📝 Round Synopsis", "on_green")
            cprint(synopsis, "white", "on_green")
            
            cprint("\n🎯 Trading Round Complete! 🎯", "white", "on_green", attrs=["bold"])
            
        except Exception as e:
            cprint(f"\n❌ Error in trading round: {str(e)}", "white", "on_red")

def main():
    """Main function to run the multi-agent system"""
    print_banner()
    cprint("🎮 Welcome to Moon Dev's Trading Game! 🎮", "white", "on_magenta", attrs=["bold"])
    cprint("Two AI agents will collaborate to turn $10,000 into $10,000,000!", "white", "on_blue")
    cprint("Let the trading begin! 🚀\n", "white", "on_green", attrs=["bold"])
    
    system = MultiAgentSystem()
    
    try:
        round_number = 1
        while True:
            print_section(f"🎮 Round {round_number} 🎮", "on_blue")
            system.run_conversation_cycle()
            next_round_time = datetime.now() + timedelta(minutes=MINUTES_BETWEEN_ROUNDS)
            cprint(f"\n⏳ Next round starts in {MINUTES_BETWEEN_ROUNDS} minutes (at {next_round_time.strftime('%H:%M:%S')})...", 
                  "white", "on_magenta")
            time.sleep(MINUTES_BETWEEN_ROUNDS * 60)  # Convert minutes to seconds
            round_number += 1
            
    except KeyboardInterrupt:
        cprint("\n👋 Thanks for playing Moon Dev's Trading Game! 🌙", "white", "on_magenta", attrs=["bold"])
    except Exception as e:
        cprint(f"\n❌ Game Error: {str(e)}", "white", "on_red")

if __name__ == "__main__":
    main()