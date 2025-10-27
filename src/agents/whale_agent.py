"""
🐳 Moon Dev's Whale Watcher
Built with love by Moon Dev 🚀

Dez the Whale Agent tracks open interest changes across different timeframes and announces market moves if she sees anomalies 
"""

# Model override settings
# Set to "0" to use config.py's AI_MODEL setting
# Available models:
# - "deepseek-chat" (DeepSeek's V3 model - fast & efficient)
# - "deepseek-reasoner" (DeepSeek's R1 reasoning model)
# - "0" (Use config.py's AI_MODEL setting)
MODEL_OVERRIDE = "deepseek-chat"  # Set to "0" to disable override
DEEPSEEK_BASE_URL = "https://api.deepseek.com"  # Base URL for DeepSeek API

import os
import pandas as pd
import time
from datetime import datetime, timedelta
from termcolor import colored, cprint
from dotenv import load_dotenv
import openai
from pathlib import Path
from src import nice_funcs as n
from src import nice_funcs_hyperliquid as hl  # Add import for hyperliquid functions
from src.agents.api import MoonDevAPI
from collections import deque
from src.agents.base_agent import BaseAgent
import traceback
import numpy as np
import anthropic

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Configuration
CHECK_INTERVAL_MINUTES = 5  # How often to check OI (can be set to 0.5 for 30 seconds)
LOOKBACK_PERIODS = {
    '15min': 15  # Simplified to just 15 minutes
}

# Whale Detection Settings
WHALE_THRESHOLD_MULTIPLIER = 1.31 #1.25  # Multiplier for average change to detect whale activity (e.g. 1.25 = 25% above average)

# AI Settings - Override config.py if set
from src import config

# Only set these if you want to override config.py settings
AI_MODEL = False  # Set to model name to override config.AI_MODEL
AI_TEMPERATURE = 0  # Set > 0 to override config.AI_TEMPERATURE
AI_MAX_TOKENS = 50  # Set > 0 to override config.AI_MAX_TOKENS

# Voice settings
VOICE_MODEL = "tts-1"  # or tts-1-hd for higher quality
VOICE_NAME = "shimmer"   # Options: alloy, echo, fable, onyx, nova, shimmer
VOICE_SPEED = 1      # 0.25 to 4.0

# AI Analysis Prompt
WHALE_ANALYSIS_PROMPT = """You must respond in exactly 3 lines:
Line 1: Only write BUY, SELL, or NOTHING
Line 2: One short reason why
Line 3: Only write "Confidence: X%" where X is 0-100

Analyze BTC with {pct_change}% OI change in {interval}m:
Current OI: ${current_oi}
Previous OI: ${previous_oi}
{market_data}

Large OI increases with price up may indicate strong momentum
Large OI decreases with price down may indicate capitulation which can be a good buy or a confirmation of a trend, you will need to look at the data
"""

class WhaleAgent(BaseAgent):
    """Dez the Whale Watcher 🐋"""
    
    def __init__(self):
        """Initialize Dez the Whale Agent"""
        super().__init__('whale')  # Initialize base agent with type
        
        # Set AI parameters - use config values unless overridden
        self.ai_model = MODEL_OVERRIDE if MODEL_OVERRIDE != "0" else config.AI_MODEL
        self.ai_temperature = AI_TEMPERATURE if AI_TEMPERATURE > 0 else config.AI_TEMPERATURE
        self.ai_max_tokens = AI_MAX_TOKENS if AI_MAX_TOKENS > 0 else config.AI_MAX_TOKENS
        
        print(f"🤖 Using AI Model: {self.ai_model}")
        if AI_MODEL or AI_TEMPERATURE > 0 or AI_MAX_TOKENS > 0:
            print("⚠️ Note: Using some override settings instead of config.py defaults")
            if AI_MODEL:
                print(f"  - Model: {AI_MODEL}")
            if AI_TEMPERATURE > 0:
                print(f"  - Temperature: {AI_TEMPERATURE}")
            if AI_MAX_TOKENS > 0:
                print(f"  - Max Tokens: {AI_MAX_TOKENS}")
        
        load_dotenv()
        
        # Get API keys
        openai_key = os.getenv("OPENAI_KEY")
        anthropic_key = os.getenv("ANTHROPIC_KEY")
        
        if not openai_key:
            raise ValueError("🚨 OPENAI_KEY not found in environment variables!")
        if not anthropic_key:
            raise ValueError("🚨 ANTHROPIC_KEY not found in environment variables!")
            
        openai.api_key = openai_key
        self.client = anthropic.Anthropic(api_key=anthropic_key)

        # Initialize DeepSeek client if needed
        if "deepseek" in self.ai_model.lower():
            deepseek_key = os.getenv("DEEPSEEK_KEY")
            if deepseek_key:
                self.deepseek_client = openai.OpenAI(
                    api_key=deepseek_key,
                    base_url=DEEPSEEK_BASE_URL
                )
                print("🚀 Moon Dev's Whale Agent using DeepSeek override!")
            else:
                self.deepseek_client = None
                print("⚠️ DEEPSEEK_KEY not found - DeepSeek model will not be available")
        else:
            self.deepseek_client = None
            print(f"🎯 Moon Dev's Whale Agent using Claude model: {self.ai_model}!")
        
        # Initialize Moon Dev API with correct base URL
        self.api = MoonDevAPI(base_url="http://api.moondev.com:8000")
        
        # Create data directories if they don't exist
        self.audio_dir = PROJECT_ROOT / "src" / "audio"
        self.data_dir = PROJECT_ROOT / "src" / "data"
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize or load historical data
        self.history_file = self.data_dir / "oi_history.csv"
        self.load_history()
        
        print("🐋 Dez the Whale Agent initialized!")
        
    def load_history(self):
        """Load or initialize historical OI data with change tracking"""
        try:
            print("🔄 Starting history load...")
            if self.history_file.exists():
                print("📂 Found existing history file")
                df = pd.read_csv(self.history_file)
                
                # Check if we have the new column format
                required_columns = ['timestamp', 'btc_oi', 'eth_oi', 'total_oi', 'btc_change_pct', 'eth_change_pct', 'total_change_pct']
                if all(col in df.columns for col in required_columns):
                    print("✅ Column format is correct")
                    self.oi_history = df
                    self.oi_history['timestamp'] = pd.to_datetime(self.oi_history['timestamp'])
                    print(f"📈 Loaded {len(self.oi_history)} historical OI records")
                else:
                    print("🔄 Detected old format, creating new history file")
                    print(f"Current columns: {df.columns.tolist()}")
                    self.oi_history = pd.DataFrame(columns=required_columns)
                    if self.history_file.exists():
                        print("🗑️ Removing old history file")
                        self.history_file.unlink()
            else:
                print("📝 No history file found, creating new one")
                self.oi_history = pd.DataFrame(columns=['timestamp', 'btc_oi', 'eth_oi', 'total_oi', 
                                                      'btc_change_pct', 'eth_change_pct', 'total_change_pct'])
                
            # Clean up old data (keep only last 24 hours)
            if not self.oi_history.empty:
                print(f"🧹 Cleaning old data. Current size: {len(self.oi_history)}")
                cutoff_time = datetime.now() - timedelta(hours=24)
                self.oi_history = self.oi_history[self.oi_history['timestamp'] > cutoff_time]
                print(f"✨ New size after cleanup: {len(self.oi_history)}")
                print("💾 Saving cleaned history to file...")
                self.oi_history.to_csv(self.history_file, index=False)
                print("✅ History save complete")
                
            print("🎉 History load complete!")
            
        except Exception as e:
            print(f"❌ Error loading history: {str(e)}")
            print(f"📋 Stack trace: {traceback.format_exc()}")
            self.oi_history = pd.DataFrame(columns=['timestamp', 'btc_oi', 'eth_oi', 'total_oi', 
                                                  'btc_change_pct', 'eth_change_pct', 'total_change_pct'])
            print("⚠️ Created empty history due to error")
            
    def _save_oi_data(self, timestamp, btc_oi, eth_oi, total_oi):
        """Save new OI data point with change percentages"""
        try:
            print("\n🔄 Starting to save new OI data point...")
            print(f"📊 Input data:")
            print(f"  Timestamp: {timestamp}")
            print(f"  BTC OI: ${btc_oi:,.2f}")
            print(f"  ETH OI: ${eth_oi:,.2f}")
            print(f"  Total OI: ${total_oi:,.2f}")
            
            # Calculate percentage changes if we have previous data
            btc_change_pct = eth_change_pct = total_change_pct = 0.0
            
            if not self.oi_history.empty:
                prev_data = self.oi_history.iloc[-1]
                print("\n📊 Previous vs Current OI:")
                print(f"Previous BTC OI: ${prev_data['btc_oi']:,.2f}")
                print(f"Current BTC OI: ${btc_oi:,.2f}")
                
                btc_change_pct = ((btc_oi - prev_data['btc_oi']) / prev_data['btc_oi']) * 100
                eth_change_pct = ((eth_oi - prev_data['eth_oi']) / prev_data['eth_oi']) * 100
                total_change_pct = ((total_oi - prev_data['total_oi']) / prev_data['total_oi']) * 100
                
                print(f"\n📈 Calculated Changes:")
                print(f"BTC Change: {btc_change_pct:.4f}%")
                print(f"ETH Change: {eth_change_pct:.4f}%")
                print(f"Total Change: {total_change_pct:.4f}%")
            else:
                print("\n⚠️ No previous data found, setting changes to 0")
            
            # Add new data point
            print("\n📝 Creating new data row...")
            new_row = pd.DataFrame([{
                'timestamp': timestamp,
                'btc_oi': float(btc_oi),
                'eth_oi': float(eth_oi),
                'total_oi': float(total_oi),
                'btc_change_pct': btc_change_pct,
                'eth_change_pct': eth_change_pct,
                'total_change_pct': total_change_pct
            }])
            
            print("\n📊 Adding new data point to history...")
            print(f"History size before: {len(self.oi_history)}")
            self.oi_history = pd.concat([self.oi_history, new_row], ignore_index=True)
            print(f"History size after: {len(self.oi_history)}")
            
            # Clean up old data
            print("\n🧹 Cleaning up old data...")
            cutoff_time = datetime.now() - timedelta(hours=24)
            old_size = len(self.oi_history)
            self.oi_history = self.oi_history[self.oi_history['timestamp'] > cutoff_time]
            print(f"Removed {old_size - len(self.oi_history)} old records")
            
            # Save to file
            print("\n💾 Saving to history file...")
            self.oi_history.to_csv(self.history_file, index=False)
            print("✅ Save complete!")
            
        except Exception as e:
            print(f"\n❌ Error saving OI data: {str(e)}")
            print(f"📋 Stack trace:\n{traceback.format_exc()}")
            
    def _format_number_for_speech(self, number):
        """Convert numbers to speech-friendly format"""
        billions = number / 1e9
        if billions >= 1:
            return f"{billions:.4f} billion"
        millions = number / 1e6
        return f"{millions:.2f} million"

    def _get_current_oi(self):
        """Get current open interest data from API"""
        try:
            print("\n🔍 Fetching fresh OI data from API...")
            df = self.api.get_oi_data()  # Changed from get_open_interest to get_oi_data
            
            if df is None:
                print("❌ Failed to get current OI data")
                return None
                
            print(f"✨ Successfully fetched {len(df)} OI records")
            
            # Process the latest data point for each symbol
            if not df.empty:
                # Get latest BTC and ETH data
                btc_data = df[df['symbol'] == 'BTCUSDT'].iloc[-1]
                eth_data = df[df['symbol'] == 'ETHUSDT'].iloc[-1]
                
                # Use the most recent timestamp between BTC and ETH
                current_time = pd.to_datetime(max(btc_data['time'], eth_data['time']))
                
                # Calculate OI values (openInterest * price)
                btc_oi = float(btc_data['openInterest']) * float(btc_data['price'])
                eth_oi = float(eth_data['openInterest']) * float(eth_data['price'])
                total_oi = btc_oi + eth_oi
                
                # Save the data point
                self._save_oi_data(current_time, btc_oi, eth_oi, total_oi)
                
            return self.oi_history
            
        except Exception as e:
            print(f"❌ Error getting OI data: {str(e)}")
            print(f"Stack trace: {traceback.format_exc()}")
            return None
            
    def _get_historical_oi(self, minutes_ago):
        """Get OI data from X minutes ago"""
        try:
            target_time = datetime.now() - timedelta(minutes=minutes_ago)
            
            # Find closest data point before target time
            historical_data = self.oi_history[self.oi_history['timestamp'] <= target_time]
            
            if not historical_data.empty:
                return float(historical_data.iloc[-1]['total_oi'])
            return None
            
        except Exception as e:
            print(f"❌ Error getting historical OI: {str(e)}")
            return None
        
    def _calculate_changes(self, current_oi):
        """Calculate OI changes for the configured interval"""
        changes = {}
        
        print("\n📊 Calculating OI Changes:")
        
        # Get current BTC value from latest history entry
        if self.oi_history.empty:
            print("❌ No history data available")
            return None
            
        current_btc = float(self.oi_history.iloc[-1]['btc_oi'])
        current_time = self.oi_history.iloc[-1]['timestamp']
        print(f"Current BTC OI: ${current_btc:,.2f}")
        print(f"Current Time: {current_time}")
        
        # Use our local CHECK_INTERVAL_MINUTES constant
        interval = CHECK_INTERVAL_MINUTES
        
        # Use the current timestamp from history instead of datetime.now()
        target_time = current_time - timedelta(minutes=interval)
        
        print(f"\n🔍 Looking for data {interval}m ago from {target_time}")
        print("\n📅 Full Historical Data:")
        print("=" * 80)
        print("Timestamp | BTC OI | ETH OI | Total OI | BTC Change% | ETH Change% | Total Change%")
        print("-" * 80)
        for idx, row in self.oi_history.iterrows():
            print(f"{row['timestamp']} | ${row['btc_oi']:,.2f} | ${row['eth_oi']:,.2f} | ${row['total_oi']:,.2f} | {row['btc_change_pct']:,.4f}% | {row['eth_change_pct']:,.4f}% | {row['total_change_pct']:,.4f}%")
        print("=" * 80)
        
        # Get historical data from X minutes ago
        historical_data = self.oi_history[
            self.oi_history['timestamp'] <= target_time
        ]
        
        print(f"\n📊 Found {len(historical_data)} historical records")
        
        if not historical_data.empty:
            historical_btc = float(historical_data.iloc[-1]['btc_oi'])
            historical_time = historical_data.iloc[-1]['timestamp']
            print(f"Historical BTC OI ({interval}m ago): ${historical_btc:,.2f}")
            print(f"Historical Time: {historical_time}")
            
            # Calculate percentage change
            btc_pct_change = ((current_btc - historical_btc) / historical_btc) * 100
            print(f"Calculated change: {btc_pct_change:.4f}%")
            
            changes = {
                'btc': btc_pct_change,
                'interval': interval,
                'start_btc': historical_btc,
                'current_btc': current_btc
            }
        else:
            print(f"⚠️ No historical data found from {interval}m ago")
            print("💡 This might be because:")
            print(f"1. All timestamps are after {target_time}")
            print(f"2. We need to wait {interval}m to build enough history")
            print(f"3. Current time in history: {current_time}")
        
        return changes
        
    def _analyze_opportunity(self, changes, market_data):
        """Get AI analysis of the whale movement"""
        try:
            # Get proper OHLCV data from Hyperliquid
            print("\n📊 Getting market data from Hyperliquid...")
            df = hl.get_data(
                symbol='BTC',  # Use BTC not BTCUSDT for Hyperliquid
                timeframe='15m',
                bars=100,
                add_indicators=True  # This will add SMA, RSI, MACD, etc.
            )
            
            if df is not None and not df.empty:
                print("\n📈 Latest Market Data:")
                print("=" * 80)
                print(df.tail().to_string())
                print("=" * 80)
                market_data_str = df.tail().to_string()
            else:
                print("⚠️ No market data available from Hyperliquid")
                market_data_str = "No market data available"
            
            # Prepare the context
            context = WHALE_ANALYSIS_PROMPT.format(
                pct_change=f"{changes['btc']:.2f}",
                interval=changes['interval'],
                current_oi=self._format_number_for_speech(changes['current_btc']),
                previous_oi=self._format_number_for_speech(changes['start_btc']),
                market_data=market_data_str
            )
            
            # Use either DeepSeek or Claude based on model setting
            if "deepseek" in self.ai_model.lower():
                if not self.deepseek_client:
                    raise ValueError("🚨 DeepSeek client not initialized - check DEEPSEEK_KEY")
                    
                print(f"\n🤖 Analyzing whale movement with DeepSeek model: {self.ai_model}...")
                # Make DeepSeek API call
                response = self.deepseek_client.chat.completions.create(
                    model=self.ai_model,  # Use the actual model from override
                    messages=[
                        {"role": "system", "content": WHALE_ANALYSIS_PROMPT},
                        {"role": "user", "content": context}
                    ],
                    max_tokens=self.ai_max_tokens,
                    temperature=self.ai_temperature,
                    stream=False
                )
                response_text = response.choices[0].message.content.strip()
            else:
                print(f"\n🤖 Analyzing whale movement with Claude model: {self.ai_model}...")
                # Get AI analysis using Claude
                message = self.client.messages.create(
                    model=self.ai_model,
                    max_tokens=self.ai_max_tokens,
                    temperature=self.ai_temperature,
                    messages=[{
                        "role": "user",
                        "content": context
                    }]
                )
                # Handle both string and list responses
                if isinstance(message.content, list):
                    response_text = message.content[0].text if message.content else ""
                else:
                    response_text = message.content
            
            # Handle response
            if not response_text:
                print("❌ No response from AI")
                return None
                
            # Parse response - handle both string and list formats
            if isinstance(response_text, list):
                lines = [line.strip() for line in response_text if line.strip()]
            else:
                lines = [line.strip() for line in response_text.split('\n') if line.strip()]
                
            if not lines:
                print("❌ Empty response from AI")
                return None
                
            # First line should be the action
            action = lines[0].strip().upper()
            if action not in ['BUY', 'SELL', 'NOTHING']:
                print(f"⚠️ Invalid action: {action}")
                return None
                
            # Rest is analysis
            analysis = '\n'.join(lines[1:]) if len(lines) > 1 else ""
            
            # Extract confidence
            confidence = 50  # Default confidence
            for line in lines:
                if 'confidence' in line.lower():
                    try:
                        import re
                        matches = re.findall(r'(\d+)%', line)
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
            
    def _format_announcement(self, changes):
        """Format OI changes into a speech-friendly message with whale detection and AI analysis"""
        if changes:
            btc_change = changes['btc']
            interval = changes['interval']
            
            # Format direction
            btc_direction = "up" if btc_change > 0 else "down"
            
            # Check for whale activity
            is_whale = self._detect_whale_activity(btc_change)
            
            # Get market data for analysis if it's a whale movement
            market_data = None
            if is_whale:
                print("\n📊 Fetching market data for analysis...")
                market_data = hl.get_data(
                    symbol='BTC',
                    timeframe='15m',
                    bars=100,
                    add_indicators=True
                )
            
            # Build base message
            message = f"ayo moon dev 777! BTC OI {btc_direction} {abs(btc_change):.3f}% in {interval}m, "
            message += f"from {self._format_number_for_speech(changes['start_btc'])} "
            message += f"to {self._format_number_for_speech(changes['current_btc'])}"
            
            # Add AI analysis for whale movements
            if is_whale:
                analysis = self._analyze_opportunity(changes, market_data)
                if analysis:
                    # Get first line of analysis by splitting and taking first element
                    analysis_first_line = analysis['analysis'].split('\n')[0] if analysis['analysis'] else ""
                    message += f" | AI suggests {analysis['action']} with {analysis['confidence']}% confidence. "
                    message += f"Analysis: {analysis_first_line} 🌙"
            
            # Return both message and whale status
            return message, is_whale
        return None, False
        
    def run_monitoring_cycle(self):
        """Run one monitoring cycle"""
        try:
            print("\n📊 Checking Open Interest...")
            current_oi = self._get_current_oi()
            
            if current_oi is None:
                print("❌ Failed to get current OI data")
                return
                
            # Calculate and announce changes if we have enough data
            if len(self.oi_history) > 2:  # Need at least 2 data points
                changes = self._calculate_changes(current_oi)
                if changes:
                    announcement, is_whale = self._format_announcement(changes)
                    if announcement:
                        self._announce(announcement, is_whale)
            else:
                print("📝 Building historical data... Need at least 2 data points")
                print(f"Current data points: {len(self.oi_history)}")
                
        except Exception as e:
            print(f"❌ Error in monitoring cycle: {str(e)}")
            print(f"Stack trace: {traceback.format_exc()}")
            print("🔧 Moon Dev suggests checking the logs and trying again!")
            time.sleep(60)  # Sleep for 1 minute on error
            
    def _announce(self, message, is_whale=False):
        """Announce a message, only use voice for whale alerts"""
        try:
            print(f"\n🗣️ {message}")
            
            # Only use voice for whale alerts
            if not is_whale:
                return
                
            # Generate speech using OpenAI
            response = openai.audio.speech.create(
                model=VOICE_MODEL,
                voice=VOICE_NAME,
                speed=VOICE_SPEED,
                input=message
            )
            
            # Save and play the audio
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            audio_file = self.audio_dir / f"whale_alert_{timestamp}.mp3"
            
            response.stream_to_file(audio_file)
            
            # Play audio using system command
            os.system(f"afplay {audio_file}")
            
        except Exception as e:
            print(f"❌ Error in announcement: {str(e)}")
            traceback.print_exc()

    def _announce_initial_summary(self):
        """Announce the current state of the market based on existing data"""
        try:
            if self.oi_history.empty:
                current_data = self._get_current_oi()
                if current_data is not None:
                    latest_data = self.oi_history.iloc[-1]
                    btc_oi = latest_data['btc_oi']
                    eth_oi = latest_data['eth_oi']
                    total_oi = latest_data['total_oi']
                    
                    message = "🌙 Moon Dev's Whale Watcher starting fresh! I'll compare changes once I have more data. "
                    message += f"Current total open interest is {self._format_number_for_speech(total_oi)} with Bitcoin at "
                    message += f"{(btc_oi/total_oi)*100:.1f}% and Ethereum at {(eth_oi/total_oi)*100:.1f}% of the market."
                    self._announce(message)
                return
                
            # Rest of the method remains unchanged
            current_oi = float(self.oi_history.iloc[-1]['total_oi'])
            changes = {}
            available_periods = []
            
            # Check what historical data we have
            for period_name, minutes in LOOKBACK_PERIODS.items():
                historical_oi = self._get_historical_oi(minutes)
                if historical_oi is not None:
                    pct_change = ((current_oi - historical_oi) / historical_oi) * 100
                    changes[period_name] = pct_change
                    available_periods.append(period_name)
            
            if not changes:
                earliest_data = self.oi_history.iloc[0]
                latest_data = self.oi_history.iloc[-1]
                minutes_diff = (latest_data['timestamp'] - earliest_data['timestamp']).total_seconds() / 60
                pct_change = ((latest_data['total_oi'] - earliest_data['total_oi']) / earliest_data['total_oi']) * 100
                
                message = f"Open Interest has {('increased' if pct_change > 0 else 'decreased')} "
                message += f"by {abs(pct_change):.1f}% over the last {int(minutes_diff)} minutes."
            else:
                message = "Initial market summary: "
                for period in available_periods:
                    change = changes[period]
                    direction = "up" if change > 0 else "down"
                    message += f"OI is {direction} {abs(change):.1f}% over the last {period}. "
            
            self._announce(message)
            
        except Exception as e:
            print(f"❌ Error in initial summary: {str(e)}")
            print(f"Stack trace: {traceback.format_exc()}")

    def _detect_whale_activity(self, current_change):
        """Detect if current change is significantly above rolling average"""
        try:
            if len(self.oi_history) < 10:  # Need some history for meaningful average
                print("⚠️ Not enough history for whale detection")
                return False
            
            # Get rolling average of absolute changes
            historical_changes = self.oi_history['btc_change_pct'].abs().rolling(window=10).mean().dropna()
            if historical_changes.empty:
                print("⚠️ No historical changes available")
                return False
                
            avg_change = historical_changes.mean()
            threshold = avg_change * WHALE_THRESHOLD_MULTIPLIER
            
            print(f"\n🔍 Whale Detection Analysis:")
            print(f"Current change: {abs(current_change):.4f}%")
            print(f"Average change: {avg_change:.4f}%")
            print(f"Threshold ({(WHALE_THRESHOLD_MULTIPLIER-1)*100:.0f}% above avg): {threshold:.4f}%")
            print(f"Is whale? {'Yes! 🐋' if abs(current_change) > threshold else 'No'}")
            
            return abs(current_change) > threshold
            
        except Exception as e:
            print(f"❌ Error detecting whale activity: {str(e)}")
            print(f"Stack trace: {traceback.format_exc()}")
            return False

if __name__ == "__main__":
    agent = WhaleAgent()
    
    # Run the agent continuously
    print("\n🐋 Moon Dev's Whale Agent starting monitoring cycle...")
    while True:
        try:
            agent.run_monitoring_cycle()
            time.sleep(60 * CHECK_INTERVAL_MINUTES)  # Sleep for the configured interval
        except KeyboardInterrupt:
            print("\n👋 Whale Agent shutting down gracefully...")
            break
        except Exception as e:
            print(f"❌ Error in main loop: {str(e)}")
            print("🔧 Moon Dev suggests checking the logs and trying again!")
            time.sleep(60)  # Sleep for 1 minute on error 