"""
📊 Moon Dev's Chart Analysis Agent
Built with love by Moon Dev 🌙

Chuck the Chart Agent generates and analyzes trading charts using AI vision capabilities.
"""

import os
import pandas as pd
import numpy as np
import mplfinance as mpf
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from pathlib import Path
import time
from dotenv import load_dotenv
import anthropic
import openai
from src import nice_funcs as n
from src import nice_funcs_hyperliquid as hl
from src.agents.base_agent import BaseAgent
import traceback
import base64
from io import BytesIO
import re

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Configuration
CHECK_INTERVAL_MINUTES = 10  # 3 hours and 53 minutes
TIMEFRAMES = ['15m']#['15m', '1h', '4h', '1d']  # Multiple timeframes to analyze
LOOKBACK_BARS = 100  # Number of candles to analyze

# Trading Pairs to Monitor
SYMBOLS = ["BTC", "FARTCOIN"]  # Add or modify symbols here

# Chart Settings
CHART_STYLE = 'charles'  # mplfinance style
VOLUME_PANEL = True  # Show volume panel
INDICATORS = ['SMA20', 'SMA50', 'SMA200', 'RSI', 'MACD']  # Technical indicators to display

# AI Settings - Override config.py if set
from src import config

# Only set these if you want to override config.py settings
AI_MODEL = False  # Set to model name to override config.AI_MODEL
AI_TEMPERATURE = 0  # Set > 0 to override config.AI_TEMPERATURE 
AI_MAX_TOKENS = 0  # Set > 0 to override config.AI_MAX_TOKENS

# Voice settings
VOICE_MODEL = "tts-1"
VOICE_NAME = "shimmer" # Options: alloy, echo, fable, onyx, nova, shimmer
VOICE_SPEED = 1.0

# AI Analysis Prompt
CHART_ANALYSIS_PROMPT = """You must respond in exactly 3 lines:
Line 1: Only write BUY, SELL, or NOTHING
Line 2: One short reason why
Line 3: Only write "Confidence: X%" where X is 0-100

Analyze the chart data for {symbol} {timeframe}:

{chart_data}

Remember:
- Look for confluence between multiple indicators
- Volume should confirm price action
- Consider the timeframe context
"""

class ChartAnalysisAgent(BaseAgent):
    """Chuck the Chart Analysis Agent 📊"""
    
    def __init__(self):
        """Initialize Chuck the Chart Agent"""
        super().__init__('chartanalysis')
        
        # Set up directories
        self.charts_dir = PROJECT_ROOT / "src" / "data" / "charts"
        self.audio_dir = PROJECT_ROOT / "src" / "audio"
        self.charts_dir.mkdir(parents=True, exist_ok=True)
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        
        # Load environment variables
        load_dotenv()
        
        # Initialize API clients
        openai_key = os.getenv("OPENAI_KEY")
        anthropic_key = os.getenv("ANTHROPIC_KEY")
        
        if not openai_key or not anthropic_key:
            raise ValueError("🚨 API keys not found in environment variables!")
            
        self.openai_client = openai.OpenAI(api_key=openai_key)  # For TTS only
        self.client = anthropic.Anthropic(api_key=anthropic_key)
        
        # Set AI parameters - use config values unless overridden
        self.ai_model = AI_MODEL if AI_MODEL else config.AI_MODEL
        self.ai_temperature = AI_TEMPERATURE if AI_TEMPERATURE > 0 else config.AI_TEMPERATURE
        self.ai_max_tokens = AI_MAX_TOKENS if AI_MAX_TOKENS > 0 else config.AI_MAX_TOKENS
        
        print("📊 Chuck the Chart Agent initialized!")
        print(f"🤖 Using AI Model: {self.ai_model}")
        if AI_MODEL or AI_TEMPERATURE > 0 or AI_MAX_TOKENS > 0:
            print("⚠️ Note: Using some override settings instead of config.py defaults")
        print(f"🎯 Analyzing {len(TIMEFRAMES)} timeframes: {', '.join(TIMEFRAMES)}")
        print(f"📈 Using indicators: {', '.join(INDICATORS)}")
        
    def _generate_chart(self, symbol, timeframe, data):
        """Generate a chart using mplfinance"""
        try:
            # Prepare data
            df = data.copy()
            df.index = pd.to_datetime(df.index)
            
            # Check if data is valid
            if df.empty:
                print("❌ No data available for chart generation")
                return None
                
            # Calculate indicators
            if 'SMA20' in INDICATORS:
                df['SMA20'] = df['close'].rolling(window=20).mean()
            if 'SMA50' in INDICATORS:
                df['SMA50'] = df['close'].rolling(window=50).mean()
            if 'SMA200' in INDICATORS:
                df['SMA200'] = df['close'].rolling(window=200).mean()
            
            # Create addplot for indicators
            ap = []
            colors = ['blue', 'orange', 'purple']
            for i, sma in enumerate(['SMA20', 'SMA50', 'SMA200']):
                if sma in INDICATORS and sma in df.columns and not df[sma].isna().all():
                    ap.append(mpf.make_addplot(df[sma], color=colors[i]))
            
            # Save chart
            filename = f"{symbol}_{timeframe}_{int(time.time())}.png"
            chart_path = self.charts_dir / filename
            
            # Create the chart
            mpf.plot(df,
                    type='candle',
                    style=CHART_STYLE,
                    volume=VOLUME_PANEL,
                    addplot=ap if ap else None,
                    title=f"\n{symbol} {timeframe} Chart Analysis by Moon Dev 🌙",
                    savefig=chart_path)
            
            return chart_path
            
        except Exception as e:
            print(f"❌ Error generating chart: {str(e)}")
            traceback.print_exc()
            return None
            
    def _analyze_chart(self, symbol, timeframe, data):
        """Analyze chart data using Claude"""
        try:
            # Format the chart data
            chart_data = (
                f"Recent price action (last 5 candles):\n{data.tail(5).to_string()}\n\n"
                f"Technical Indicators:\n"
                f"- SMA20: {data['SMA20'].iloc[-1]:.2f}\n"
                f"- SMA50: {data['SMA50'].iloc[-1]:.2f}\n"
                f"- SMA200: {data['SMA200'].iloc[-1] if not pd.isna(data['SMA200'].iloc[-1]) else 'Not enough data'}\n"
                f"Current price: {data['close'].iloc[-1]:.2f}\n"
                f"24h High: {data['high'].max():.2f}\n"
                f"24h Low: {data['low'].min():.2f}\n"
                f"Volume trend: {'Increasing' if data['volume'].iloc[-1] > data['volume'].mean() else 'Decreasing'}"
            )
            
            # Prepare the context
            context = CHART_ANALYSIS_PROMPT.format(
                symbol=symbol,
                timeframe=timeframe,
                chart_data=chart_data
            )
            
            print(f"\n🤖 Analyzing {symbol} with AI...")
            
            # Get AI analysis using instance settings
            message = self.client.messages.create(
                model=self.ai_model,
                max_tokens=self.ai_max_tokens,
                temperature=self.ai_temperature,
                messages=[{
                    "role": "user",
                    "content": context
                }]
            )
            
            if not message or not message.content:
                print("❌ No response from AI")
                return None
                
            # Debug: Print raw response
            print("\n🔍 Raw response:")
            print(repr(message.content))
            
            # Get the raw content and convert to string
            content = str(message.content)
            
            # Clean up TextBlock formatting - new format handling
            if 'TextBlock' in content:
                # Extract just the text content between quotes
                match = re.search(r"text='([^']*)'", content, re.IGNORECASE)
                if match:
                    content = match.group(1)
            
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
            
            # Determine direction based on action
            if action == 'BUY':
                direction = 'BULLISH'
            elif action == 'SELL':
                direction = 'BEARISH'
            else:
                direction = 'SIDEWAYS'
            
            return {
                'direction': direction,
                'analysis': analysis,
                'action': action,
                'confidence': confidence
            }
            
        except Exception as e:
            print(f"❌ Error in chart analysis: {str(e)}")
            traceback.print_exc()
            return None
            
    def _format_announcement(self, symbol, timeframe, analysis):
        """Format analysis into speech-friendly message"""
        try:
            if not analysis:
                return None
                
            # Convert timeframe to speech-friendly format
            friendly_timeframe = timeframe.replace('m', ' minute').replace('h', ' hour').replace('d', ' day')
                
            message = (
                f"hi, Moon Dev seven seven seven! Chart analysis for {symbol} on the {friendly_timeframe} timeframe! "
                f"The trend is {analysis['direction']}. {analysis['analysis']} "
                f"AI suggests to {analysis['action']} with {analysis['confidence']}% confidence! "
            )
            
            return message
            
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
            response = self.openai_client.audio.speech.create(
                model=VOICE_MODEL,
                voice=VOICE_NAME,
                input=message,
                speed=VOICE_SPEED
            )
            
            # Save audio file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            audio_file = self.audio_dir / f"chart_alert_{timestamp}.mp3"
            
            response.stream_to_file(str(audio_file))
            
            # Play audio
            os.system(f"afplay {audio_file}")
            
        except Exception as e:
            print(f"❌ Error in announcement: {str(e)}")
            
    def analyze_symbol(self, symbol, timeframe):
        """Analyze a single symbol on a specific timeframe"""
        try:
            # Get market data
            data = hl.get_data(
                symbol=symbol,
                timeframe=timeframe,
                bars=LOOKBACK_BARS,
                add_indicators=True
            )
            
            if data is None or data.empty:
                print(f"❌ No data available for {symbol} {timeframe}")
                return
                
            # Calculate additional indicators
            if 'SMA20' not in data.columns:
                data['SMA20'] = data['close'].rolling(window=20).mean()
            if 'SMA50' not in data.columns:
                data['SMA50'] = data['close'].rolling(window=50).mean()
            if 'SMA200' not in data.columns:
                data['SMA200'] = data['close'].rolling(window=200).mean()
            
            # Generate and save chart first
            print(f"\n📊 Generating chart for {symbol} {timeframe}...")
            chart_path = self._generate_chart(symbol, timeframe, data)
            if chart_path:
                print(f"📈 Chart saved to: {chart_path}")
            
            # Debug print the chart data
            print("\n" + "╔" + "═" * 60 + "╗")
            print(f"║    🌙 Chart Data for {symbol} {timeframe} - Last 5 Candles    ║")
            print("╠" + "═" * 60 + "╣")
            print(f"║ Time │ Open │ High │ Low │ Close │ Volume │")
            print("╟" + "─" * 60 + "╢")
            
            # Print last 5 candles with proper timestamp formatting
            last_5 = data.tail(5)
            last_5.index = pd.to_datetime(last_5.index)
            for idx, row in last_5.iterrows():
                time_str = idx.strftime('%Y-%m-%d %H:%M')  # Include date and time
                print(f"║ {time_str} │ {row['open']:.2f} │ {row['high']:.2f} │ {row['low']:.2f} │ {row['close']:.2f} │ {row['volume']:.0f} │")
            
            print("\n║ Technical Indicators:")
            print(f"║ SMA20: {data['SMA20'].iloc[-1]:.2f}")
            print(f"║ SMA50: {data['SMA50'].iloc[-1]:.2f}")
            print(f"║ SMA200: {data['SMA200'].iloc[-1] if not pd.isna(data['SMA200'].iloc[-1]) else 'Not enough data'}")
            print(f"║ 24h High: {data['high'].max():.2f}")
            print(f"║ 24h Low: {data['low'].min():.2f}")
            print(f"║ Volume Trend: {'Increasing' if data['volume'].iloc[-1] > data['volume'].mean() else 'Decreasing'}")
            print("╚" + "═" * 60 + "╝")
                
            # Analyze with AI
            print(f"\n🔍 Analyzing {symbol} {timeframe}...")
            analysis = self._analyze_chart(symbol, timeframe, data)
            
            if analysis and all(k in analysis for k in ['direction', 'analysis', 'action', 'confidence']):
                # Format and announce
                message = self._format_announcement(symbol, timeframe, analysis)
                if message:
                    self._announce(message)
                    
                # Print analysis in a nice box
                print("\n" + "╔" + "═" * 50 + "╗")
                print(f"║    🌙 Moon Dev's Chart Analysis - {symbol} {timeframe}   ║")
                print("╠" + "═" * 50 + "╣")
                print(f"║  Direction: {analysis['direction']:<41} ║")
                print(f"║  Action: {analysis['action']:<44} ║")
                print(f"║  Confidence: {analysis['confidence']}%{' ' * 37}║")
                print("╟" + "─" * 50 + "╢")
                print(f"║  Analysis: {analysis['analysis']:<41} ║")
                print("╚" + "═" * 50 + "╝")
            else:
                print("❌ Invalid analysis result")
            
        except Exception as e:
            print(f"❌ Error analyzing {symbol} {timeframe}: {str(e)}")
            traceback.print_exc()
            
    def _cleanup_old_charts(self):
        """Remove all existing charts from the charts directory"""
        try:
            for chart in self.charts_dir.glob("*.png"):
                chart.unlink()
            print("🧹 Cleaned up old charts")
        except Exception as e:
            print(f"⚠️ Error cleaning up charts: {str(e)}")

    def run_monitoring_cycle(self):
        """Run one monitoring cycle"""
        try:
            # Clean up old charts before starting new cycle
            self._cleanup_old_charts()
            
            for symbol in SYMBOLS:
                for timeframe in TIMEFRAMES:
                    self.analyze_symbol(symbol, timeframe)
                    time.sleep(2)  # Small delay between analyses
                    
        except Exception as e:
            print(f"❌ Error in monitoring cycle: {str(e)}")
            
    def run(self):
        """Run the chart analysis monitor continuously"""
        print("\n🚀 Starting chart analysis monitoring...")
        
        while True:
            try:
                self.run_monitoring_cycle()
                print(f"\n💤 Sleeping for {CHECK_INTERVAL_MINUTES} minutes...")
                time.sleep(CHECK_INTERVAL_MINUTES * 60)
                
            except KeyboardInterrupt:
                print("\n👋 Chuck the Chart Agent shutting down gracefully...")
                break
            except Exception as e:
                print(f"❌ Error in main loop: {str(e)}")
                time.sleep(60)  # Sleep for a minute before retrying

if __name__ == "__main__":
    # Create and run the agent
    print("\n🌙 Moon Dev's Chart Analysis Agent Starting Up...")
    print("👋 Hey! I'm Chuck, your friendly chart analysis agent! 📊")
    print(f"🎯 Monitoring {len(SYMBOLS)} symbols: {', '.join(SYMBOLS)}")
    agent = ChartAnalysisAgent()
    
    # Run the continuous monitoring cycle
    agent.run()
