"""
🌙 Moon Dev's Funding Arbitrage Agent 💰

This agent scans all tokens on Hyperliquid for funding rate opportunities.
When it finds rates above our threshold, it analyzes the opportunity using AI.

Need an API key? for a limited time, bootcamp members get free api keys for claude, openai, helius, birdeye & quant elite gets access to the moon dev api. join here: https://algotradecamp.com
"""

import os
import time
import traceback
from datetime import datetime
from pathlib import Path
import re

import pandas as pd
from openai import OpenAI  # Use OpenAI client for Ollama
from dotenv import load_dotenv
import pyttsx3  # Add pyttsx3 for TTS

from src.agents.base_agent import BaseAgent
from src.nice_funcs_hl import get_funding_rates
from src.config import AI_MODEL, AI_TEMPERATURE, AI_MAX_TOKENS

# Configuration
CHECK_INTERVAL_MINUTES = 15  # How often to check funding rates
YEARLY_FUNDING_THRESHOLD = 100  # 100% yearly funding rate threshold - only for positive rates

# Only set these if you want to override config.py settings
AI_MODEL = False  # Set to model name to override config.AI_MODEL
AI_TEMPERATURE = 0  # Set > 0 to override config.AI_TEMPERATURE
AI_MAX_TOKENS = 25  # Set > 0 to override config.AI_MAX_TOKENS

# Voice settings (pyttsx3)
VOICE_NAME = "fable"  # Not used in pyttsx3, but kept for compatibility
VOICE_SPEED = 1  # Not used in pyttsx3, but kept for compatibility

# Tokens to monitor for funding arbitrage
# These should be liquid tokens with reliable funding rates
MONITOR_TOKENS = [
    "SOL",   # Solana
    "FARTCOIN", # Fartcoin
    'AI16Z',
    'AIXBT',
    'TRUMP',
    'MELANIA',
    'kBONK',
    'PENGU',
    'POPCAT',
    'WIF',
    'ZEREBRO',
    'GRIFFAIN',
    'PURR',
    'GOAT',
    'CHILLGUY',
    'MOODENG',
]

# AI Analysis Prompt
FUNDING_ANALYSIS_PROMPT = """
Market Data:
{market_data}

COPY THIS FORMAT EXACTLY (2 LINES):
ARBITRAGE
High funding rate of 150% yearly with good liquidity makes arbitrage profitable

Note: First line must be ARBITRAGE or SKIP
"""

class FundingArbAgent(BaseAgent):
    """Moon Dev's Funding Arbitrage Agent 💰"""
    
    def __init__(self):
        """Initialize Moon Dev's Funding Arbitrage Agent"""
        super().__init__('fundingarb')  # Initialize base agent with type
        
        # Set AI parameters - use config values unless overridden
        self.ai_model = AI_MODEL if AI_MODEL else "llama2"  # Use Ollama model
        self.ai_temperature = AI_TEMPERATURE if AI_TEMPERATURE > 0 else 0.5
        self.ai_max_tokens = AI_MAX_TOKENS if AI_MAX_TOKENS > 0 else 150
        
        print(f"🤖 Using AI Model: {self.ai_model}")
        if AI_MODEL or AI_TEMPERATURE > 0 or AI_MAX_TOKENS > 0:
            print("⚠️ Note: Using some override settings instead of defaults")
            if AI_MODEL:
                print(f"  - Model: {AI_MODEL}")
            if AI_TEMPERATURE > 0:
                print(f"  - Temperature: {AI_TEMPERATURE}")
            if AI_MAX_TOKENS > 0:
                print(f"  - Max Tokens: {AI_MAX_TOKENS}")
        
        # Load environment variables
        load_dotenv()
        
        # Initialize Ollama client
        self.client = OpenAI(
            base_url="http://localhost:11434/v1",  # Ollama's OpenAI-compatible endpoint
            api_key="ollama"  # API key is not required for Ollama
        )
        
        # Initialize pyttsx3 TTS engine
        self.tts_engine = pyttsx3.init()
        self.tts_engine.setProperty('rate', 150)  # Speed of speech
        self.tts_engine.setProperty('volume', 1.0)  # Volume level (0.0 to 1.0)
        
        # Create data directories
        self.data_dir = Path("src/data/fundingarb")
        self.audio_dir = Path("src/audio")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        
        print("✨ Funding Arbitrage Agent initialized! Let's find some opportunities!")
        
    def _analyze_opportunity(self, symbol, data, market_data):
        """Analyze a funding opportunity with AI"""
        try:
            # Format the market context
            hourly_rate = float(data['funding_rate']) * 100
            annual_rate = hourly_rate * 24 * 365
            
            context = f"""
            Symbol: {symbol}
            Current Price: ${data['mark_price']:,.2f}
            Hourly Funding Rate: {hourly_rate:.4f}%
            Annualized Rate: {annual_rate:.2f}%
            Open Interest: {data['open_interest']:,.2f}
            
            Market Analysis:
            {market_data}
            """
            
            # Get AI analysis using Ollama client
            response = self.client.chat.completions.create(
                model=self.ai_model,
                messages=[
                    {"role": "system", "content": "You are a funding arbitrage analyst. You must respond in exactly 2 lines: ARBITRAGE/SKIP and your reason."},
                    {"role": "user", "content": FUNDING_ANALYSIS_PROMPT.format(
                        market_data=context,
                        threshold=YEARLY_FUNDING_THRESHOLD
                    )}
                ],
                temperature=self.ai_temperature,
                max_tokens=self.ai_max_tokens
            )
            
            content = response.choices[0].message.content
            print(f"\n🤖 Raw AI response:\n{content}")  # Debug print
            
            # Clean up response and split into lines
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            print(f"📝 Parsed lines: {lines}")  # Debug print
            
            # Ensure we have exactly 2 lines
            if len(lines) != 2:
                print(f"❌ Expected 2 lines, got {len(lines)}")
                return None
                
            action = lines[0].strip().upper()
            analysis = lines[1].strip()
            
            # Validate action
            if action not in ["ARBITRAGE", "SKIP"]:
                print(f"❌ Invalid action: {action}")
                return None
            
            result = {
                'action': action,
                'analysis': analysis,
                'confidence': "Confidence: 100%"  # Default confidence for announcements
            }
            print(f"✅ Valid analysis format: {result}")  # Debug print
            return result
            
        except Exception as e:
            print(f"❌ Error in AI analysis: {str(e)}")
            traceback.print_exc()
            return None
    
    def _format_announcement(self, symbol, data, analysis):
        """Format the voice announcement"""
        hourly_rate = float(data['funding_rate']) * 100
        annual_rate = hourly_rate * 24 * 365
        
        announcement = f"""
        Yo Moon Dev seven seven seven! High funding arbitrage opportunity detected!
        
        {symbol} has a {annual_rate:.2f}% annualized funding rate!
        Suggested arbitrage: Short on Hyperliquid and buy spot elsewhere
        
        AI Analysis: {analysis['analysis']}
        {analysis['confidence']}
        
        Moon Dev's Funding Arbitrage Agent - Making that funding money! 🌙
        """
        return announcement
    
    def _announce(self, message):
        """Announce message using pyttsx3"""
        if not message:
            return
            
        try:
            print(f"\n📢 Announcing: {message}")
            
            # Use pyttsx3 to speak the message
            self.tts_engine.say(message)
            self.tts_engine.runAndWait()
            
        except Exception as e:
            print(f"❌ Error in announcement: {str(e)}")
            
    def speak(self, message):
        """Wrapper for _announce to match base agent interface"""
        self._announce(message)
    
    def run_monitoring_cycle(self):
        """Run one monitoring cycle checking all tokens"""
        try:
            print("\n🔍 Scanning monitored tokens for funding arbitrage opportunities...")
            print(f"📊 Checking {len(MONITOR_TOKENS)} tokens: {', '.join(MONITOR_TOKENS)}")
            
            # Check each monitored symbol
            for symbol in MONITOR_TOKENS:
                try:
                    print(f"\n🔄 Fetching funding rate for {symbol}...")
                    data = get_funding_rates(symbol)
                    if data:
                        hourly_rate = float(data['funding_rate']) * 100
                        annual_rate = hourly_rate * 24 * 365
                        
                        # Always show the funding rate
                        print(f"💰 Annual Rate: {annual_rate:.2f}%")
                        
                        # Only check positive rates above threshold
                        if annual_rate > YEARLY_FUNDING_THRESHOLD:
                            print(f"\n🎯 High positive funding detected on {symbol}!")
                            
                            # Get market data for context
                            market_data = f"""
                            Symbol: {symbol}
                            Current Price: ${data['mark_price']:,.2f}
                            Hourly Funding Rate: {hourly_rate:.4f}%
                            Annualized Rate: {annual_rate:.2f}%
                            Open Interest: {data['open_interest']:,.2f}
                            """
                            
                            # Analyze opportunity with debug prints
                            print(f"🤖 Analyzing {symbol} opportunity...")
                            analysis = self._analyze_opportunity(symbol, data, market_data)
                            
                            if analysis:
                                print(f"✅ Analysis received: {analysis}")
                                if analysis['action'] == "ARBITRAGE":
                                    # Format and speak announcement
                                    announcement = self._format_announcement(symbol, data, analysis)
                                    self.speak(announcement)
                            else:
                                print("❌ No valid analysis received")
                                
                except Exception as e:
                    print(f"❌ Error processing {symbol}: {str(e)}")
                    continue
            
            print("\n✨ Monitoring cycle complete!")
            
        except Exception as e:
            print(f"❌ Error in monitoring cycle: {str(e)}")
            traceback.print_exc()
    
    def run(self):
        """Run the funding arbitrage agent"""
        print("\n🚀 Starting Funding Arbitrage Agent...")
        print(f"👀 Monitoring for funding rates above {YEARLY_FUNDING_THRESHOLD}% yearly")
        
        try:
            while True:
                self.run_monitoring_cycle()
                
                # Sleep until next check
                print(f"\n😴 Sleeping for {CHECK_INTERVAL_MINUTES} minutes...")
                time.sleep(CHECK_INTERVAL_MINUTES * 60)
                
        except KeyboardInterrupt:
            print("\n👋 Shutting down Funding Arbitrage Agent...")
        except Exception as e:
            print(f"❌ Error running agent: {str(e)}")
            traceback.print_exc()

if __name__ == "__main__":
    # Create and run the agent
    agent = FundingArbAgent()
    agent.run()