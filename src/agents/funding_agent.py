"""
💰 Moon Dev's Funding Rate Monitor
Built with love by Moon Dev 🚀

Fran the Funding Agent tracks funding rate changes across different timeframes and announces significant changes via OpenAI TTS.

Updated to use OpenRouter for unified LLM access.

Need an API key? for a limited time, bootcamp members get free api keys for claude, openai, helius, birdeye & quant elite gets access to the moon dev api. join here: https://algotradecamp.com
"""

import os
import pandas as pd
import time
from datetime import datetime, timedelta
from termcolor import colored, cprint
from dotenv import load_dotenv
import openai
from pathlib import Path
from src import nice_funcs as n
from src import nice_funcs_hl as hl
from src.agents.api import MoonDevAPI
from collections import deque
from src.agents.base_agent import BaseAgent
from src.agents.model_helper import get_agent_model
import traceback
import numpy as np
import re

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Configuration
CHECK_INTERVAL_MINUTES = 15  # How often to check funding rates
NEGATIVE_THRESHOLD = -5 # AI Run & Alert if annual rate below -1%
POSITIVE_THRESHOLD = 20  # AI Run & Alert if annual rate above 20%

# OHLCV Data Settings
TIMEFRAME = '15m'  # Candlestick timeframe
LOOKBACK_BARS = 100  # Number of candles to analyze

# Symbol to name mapping
SYMBOL_NAMES = {
    # 'BTC': 'Bitcoin',
    # 'ETH': 'Ethereum',
    # 'SOL': 'Solana',
    # 'WIF': 'Wif',
    # 'BNB': 'BNB',
    'FARTCOIN': 'Fart Coin'
}

# AI Settings - Override config.py if set
# Import defaults from config
from src import config

# Only set these if you want to override config.py settings
AI_MODEL = False  # Set to model name to override config.AI_MODEL
AI_TEMPERATURE = 0  # Set > 0 to override config.AI_TEMPERATURE
AI_MAX_TOKENS = 25  # Set > 0 to override config.AI_MAX_TOKENS

# Voice settings
VOICE_MODEL = "tts-1"
VOICE_NAME = "fable"  # Options: alloy, echo, fable, onyx, nova, shimmer
VOICE_SPEED = 1

# AI Analysis Prompt
FUNDING_ANALYSIS_PROMPT = """You must respond in exactly 3 lines:
Line 1: Only write BUY, SELL, or NOTHING
Line 2: One short reason why
Line 3: Only write "Confidence: X%" where X is 0-100

Analyze {symbol} with {rate}% funding rate:

Below is Bitcoin (BTC) market data which shows overall market direction:
{market_data}

Above is Bitcoin's market data which indicates overall market direction.
Below is the funding rate data for {symbol}:
{funding_data}

Remember:
- Super negative funding rates in a trending up market may signal a good buy (shorts getting squeezed)
- Super high funding rates in a downtrend may signal a good sell (longs getting liquidated)
- Use BTC's trend to gauge overall market direction
"""

class FundingAgent(BaseAgent):
    """Fran the Funding Rate Monitor 💰"""
    
    def __init__(self):
        """Initialize Fran the Funding Agent"""
        super().__init__('funding')

        load_dotenv()

        # Initialize AI model using helper (uses config.py or OpenRouter)
        self.model = get_agent_model(verbose=True)

        if not self.model:
            raise ValueError("🚨 Failed to initialize AI model! Check your API keys in .env")

        # Initialize OpenAI client for voice only
        openai_key = os.getenv("OPENAI_KEY")
        if not openai_key:
            raise ValueError("🚨 OPENAI_KEY not found in environment variables!")
        openai.api_key = openai_key

        # Set AI parameters from config
        self.ai_temperature = config.AI_TEMPERATURE if AI_TEMPERATURE == 0 else AI_TEMPERATURE
        self.ai_max_tokens = config.AI_MAX_TOKENS if AI_MAX_TOKENS == 0 else AI_MAX_TOKENS

        self.api = MoonDevAPI()
        
        # Create data directories if they don't exist
        self.audio_dir = PROJECT_ROOT / "src" / "audio"
        self.data_dir = PROJECT_ROOT / "src" / "data"
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize or load historical data
        self.history_file = self.data_dir / "funding_history.csv"
        self.load_history()
        
        print("💰 Fran the Funding Agent initialized!")
        print(f"🎯 Alerting on funding rates: below {NEGATIVE_THRESHOLD}% or above {POSITIVE_THRESHOLD}%")
        print(f"📊 Analyzing {LOOKBACK_BARS} {TIMEFRAME} candles for context")
        
    def _analyze_opportunity(self, symbol, funding_data, market_data):
        """Get AI analysis of the opportunity"""
        try:
            # Debug print raw funding rate
            rate = funding_data['annual_rate'].iloc[0]
            print(f"\n🔍 Raw funding rate for {symbol}: {rate:.2f}%")
            
            # Get BTC market data as market barometer
            btc_data = hl.get_data(
                symbol="BTC",
                timeframe=TIMEFRAME,
                bars=LOOKBACK_BARS,
                add_indicators=True
            )
            
            # Get symbol specific data if not BTC
            symbol_data = None
            if symbol != "BTC":
                symbol_data = hl.get_data(
                    symbol=symbol,
                    timeframe=TIMEFRAME,
                    bars=LOOKBACK_BARS,
                    add_indicators=True
                )
            
            # Format market data context
            market_context = f"BTC Market Data (Last 5 candles):\n{btc_data.tail(5).to_string()}\n\n"
            if symbol_data is not None and symbol != "BTC":
                market_context += f"{symbol} Technical Data (Last 5 candles):\n{symbol_data.tail(5).to_string()}\n\n"
            
            # Add some basic trend analysis
            btc_close = btc_data['close'].iloc[-1]
            btc_sma = btc_data['close'].rolling(20).mean().iloc[-1]
            btc_trend = "UPTREND" if btc_close > btc_sma else "DOWNTREND"
            market_context += f"\nBTC Trend Analysis:\n- Current Price vs 20 SMA: {btc_trend}\n"
            
            # Prepare the context
            rate = funding_data['annual_rate'].iloc[0]
            context = FUNDING_ANALYSIS_PROMPT.format(
                symbol=symbol,
                rate=f"{rate:.2f}",
                market_data=market_context,
                funding_data=funding_data.to_string()
            )
            
            print(f"\n🤖 Analyzing {symbol} with AI...")

            # Use unified model interface (OpenRouter or configured provider)
            response = self.model.generate_response(
                system_prompt=FUNDING_ANALYSIS_PROMPT,
                user_content=context,
                temperature=self.ai_temperature,
                max_tokens=self.ai_max_tokens
            )

            if response and hasattr(response, 'content'):
                content = response.content.strip()
            else:
                content = str(response).strip()
            
            # Debug: Print raw response
            print("\n🔍 Raw response:")
            print(repr(content))
            
            # Clean up any remaining formatting
            content = content.replace('\\n', '\n')
            content = content.strip('[]')
            
            # Split into lines and clean each line
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            
            if not lines:
                print("❌ Empty response from AI")
                return None
            
            # First line should be the action
            action = lines[0].strip().upper()
            if action not in ['BUY', 'SELL', 'NOTHING']:
                print(f"⚠️ Invalid action: {action}")
                return None
            
            # Rest is analysis
            analysis = lines[1] if len(lines) > 1 else ""
            
            # Extract confidence from third line
            confidence = 50  # Default confidence
            if len(lines) > 2:
                try:
                    matches = re.findall(r'(\d+)%', lines[2])
                    if matches:
                        confidence = int(matches[0])
                except:
                    print("⚠️ Could not parse confidence, using default")
            
            return {
                'action': action,
                'analysis': analysis,
                'confidence': confidence
            }
            
        except Exception as e:
            print(f"❌ Error in AI analysis: {str(e)}")
            traceback.print_exc()
            return None
            
    def _detect_significant_changes(self, current_data):
        """Detect extreme funding rates and analyze opportunities"""
        try:
            opportunities = {}
            
            for _, row in current_data.iterrows():
                try:
                    annual_rate = float(row['annual_rate'])
                    symbol = str(row['symbol'])
                    
                    if annual_rate < NEGATIVE_THRESHOLD or annual_rate > POSITIVE_THRESHOLD:
                        # Get OHLCV data silently
                        market_data = hl.get_data(
                            symbol=symbol,
                            timeframe=TIMEFRAME,
                            bars=LOOKBACK_BARS,
                            add_indicators=True
                        )
                        
                        if not market_data.empty:
                            analysis = self._analyze_opportunity(
                                symbol=symbol,
                                funding_data=row.to_frame().T,
                                market_data=market_data
                            )
                            
                            if analysis:
                                opportunities[symbol] = {
                                    'annual_rate': annual_rate,
                                    'action': analysis['action'],
                                    'analysis': analysis['analysis'],
                                    'confidence': analysis['confidence']
                                }
                            
                except Exception as e:
                    continue
            
            return opportunities if opportunities else None
            
        except Exception as e:
            return None

    def _format_announcement(self, opportunities):
        """Format funding rate changes and analysis into a speech-friendly message"""
        try:
            messages = []
            
            for symbol, data in opportunities.items():
                # Get full name from mapping
                token_name = SYMBOL_NAMES.get(symbol, symbol)
                rate = data['annual_rate']
                action = data['action']
                confidence = data['confidence']
                analysis = data['analysis'].split('\n')[0]  # Get just the first line of analysis
                
                if rate < NEGATIVE_THRESHOLD:
                    messages.append(
                        f"{token_name} has negative funding at {rate:.2f}% annual. "
                        f"AI suggests {action} with {confidence}% confidence. "
                        f"Analysis: {analysis} 🌙"
                    )
                elif rate > POSITIVE_THRESHOLD:
                    messages.append(
                        f"{token_name} has high funding at {rate:.2f}% annual. "
                        f"AI suggests {action} with {confidence}% confidence. "
                        f"Analysis: {analysis} 🌙"
                    )
                
            if messages:
                return "ayo moon dev seven seven seven! " + " | ".join(messages) + "!"
            return None
            
        except Exception as e:
            print(f"❌ Error formatting announcement: {str(e)}")
            return None
            
    def _announce(self, message):
        """Announce message using OpenAI TTS"""
        if not message:
            return
            
        try:
            print(f"\n📢 Announcing: {message}")
            
            # Generate speech
            response = openai.audio.speech.create(
                model=VOICE_MODEL,
                voice=VOICE_NAME,
                input=message,
                speed=VOICE_SPEED
            )
            
            # Save audio file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            audio_file = self.audio_dir / f"funding_alert_{timestamp}.mp3"
            
            response.stream_to_file(audio_file)
            
            # Play audio using system command
            os.system(f"afplay {audio_file}")
            
        except Exception as e:
            print(f"❌ Error in announcement: {str(e)}")

    def load_history(self):
        """Load or initialize historical funding rate data"""
        try:
            # Always start with clean history using the new format
            self.funding_history = pd.DataFrame(columns=['timestamp', 'symbol', 'funding_rate', 'annual_rate'])
            print("📝 Initialized new funding rate history")
            
            if self.history_file.exists():
                # Keep just one backup file
                backup_file = self.data_dir / "funding_history_backup.csv"
                os.rename(self.history_file, backup_file)
                print(f"📦 Backed up old history file")
                
        except Exception as e:
            print(f"❌ Error loading history: {str(e)}")
            self.funding_history = pd.DataFrame(columns=['timestamp', 'symbol', 'funding_rate', 'annual_rate'])
            
    def _get_current_funding(self):
        """Get current funding rate data"""
        try:
            df = self.api.get_funding_data()
            
            if df is not None and not df.empty:
                # Get latest data for each symbol
                current_data = df.sort_values('event_time').groupby('symbol').last().reset_index()
                
                # Ensure funding_rate and yearly_funding_rate are numeric
                numeric_cols = ['funding_rate', 'yearly_funding_rate']
                for col in numeric_cols:
                    current_data[col] = pd.to_numeric(current_data[col], errors='coerce')
                
                # Rename yearly_funding_rate to annual_rate for consistency
                current_data = current_data.rename(columns={'yearly_funding_rate': 'annual_rate'})
                
                return current_data
            return None
            
        except Exception as e:
            print(f"❌ Error getting funding data: {str(e)}")
            traceback.print_exc()
            return None

    def _save_to_history(self, current_data):
        """Save current funding data to history"""
        try:
            if current_data is not None and not current_data.empty:
                # Convert to wide format with all symbols in one row
                wide_data = pd.DataFrame()
                wide_data['event_time'] = [current_data['event_time'].iloc[0]]  # Use first event_time
                
                # Add columns for each symbol's funding and annual rates
                for _, row in current_data.iterrows():
                    symbol = row['symbol']
                    wide_data[f'{symbol}_funding_rate'] = row['funding_rate']
                    wide_data[f'{symbol}_annual_rate'] = row['annual_rate']
                
                # Concatenate with existing history
                if self.funding_history.empty:
                    self.funding_history = wide_data
                else:
                    self.funding_history = pd.concat([self.funding_history, wide_data], ignore_index=True)
                
                # Drop duplicates based on event_time
                self.funding_history = self.funding_history.drop_duplicates(
                    subset=['event_time'], 
                    keep='last'
                )
                
                # Keep only last 24 hours of data
                cutoff_time = datetime.now() - timedelta(hours=24)
                self.funding_history = self.funding_history[
                    pd.to_datetime(self.funding_history['event_time']) > cutoff_time
                ]
                
                # Sort by event_time
                self.funding_history = self.funding_history.sort_values('event_time')
                
                # Save to file
                self.funding_history.to_csv(self.history_file, index=False)
                
        except Exception as e:
            print(f"❌ Error saving to history: {str(e)}")
            traceback.print_exc()

    def run_monitoring_cycle(self):
        """Run one monitoring cycle"""
        try:
            # Get current funding rates
            current_data = self._get_current_funding()
            
            if current_data is not None:
                # Save to history silently
                self._save_to_history(current_data)
                
                # Check for significant changes
                opportunities = self._detect_significant_changes(current_data)
                
                if opportunities:
                    # Format and announce changes
                    message = self._format_announcement(opportunities)
                    if message:
                        self._announce(message)
            
            # Always print the final box after any announcements
            print("\n" + "╔" + "═" * 50 + "╗")
            print("║         🌙 Moon Dev's Funding Party 🎉          ║")
            print("╠" + "═" * 50 + "╣")
            print("║  Symbol  │  Annual Rate  │      Status      ║")
            print("╟" + "─" * 50 + "╢")
            
            for _, row in current_data.iterrows():
                # Get fun status emoji based on rate
                if row['annual_rate'] > 20:
                    status = "🔥 SUPER HOT!"
                elif row['annual_rate'] < -5:
                    status = "❄️ SUPER COLD"
                elif row['annual_rate'] > 10:
                    status = "📈 HEATING UP"
                elif row['annual_rate'] < 0:
                    status = "📉 COOLING"
                else:
                    status = "😴 CHILL"
                    
                # Truncate symbol to 4 characters
                symbol = row['symbol'][:4]
                print(f"║  {symbol:<4} │  {row['annual_rate']:>8.2f}%  │  {status:<13} ║")
            
            print("╚" + "═" * 50 + "╝")
            
        except Exception as e:
            print(f"❌ Error in monitoring cycle: {str(e)}")

    def run(self):
        """Run the funding rate monitor continuously"""
        print("\n🚀 Starting funding rate monitoring...")
        
        while True:
            try:
                self.run_monitoring_cycle()
                print(f"\n💤 Sleeping for {CHECK_INTERVAL_MINUTES} minutes...")
                time.sleep(CHECK_INTERVAL_MINUTES * 60)
                
            except KeyboardInterrupt:
                print("\n👋 Fran the Funding Agent shutting down gracefully...")
                break
            except Exception as e:
                print(f"❌ Error in main loop: {str(e)}")
                time.sleep(60)  # Sleep for a minute before retrying

if __name__ == "__main__":
    agent = FundingAgent()
    agent.run()
