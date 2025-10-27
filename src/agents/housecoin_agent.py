#!/usr/bin/env python3
"""
🏠 Moon Dev's Housecoin DCA Agent with AI Decision Making 🏠

⚠️ NOT FINANCIAL ADVICE ⚠️
This is an experimental DCA (Dollar Cost Average) bot for Housecoin.
This may go to zero. The thesis: 1 House = 1 Housecoin.
Anything bought will eventually be sold. Trade at your own risk.

This agent implements the Housecoin accumulation strategy with an additional
AI decision layer. When the strategy triggers a buy signal, it consults an
AI model for final confirmation before executing the trade.

Strategy:
- Below 20-day SMA: Aggressive accumulation with 5-min SMA confirmation
- Above 20-day SMA: Buy only near daily lows
- AI Confirmation: Every buy must be approved by the AI model

Built with love by Moon Dev 🚀
"""

import os
import sys
import time
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
import pandas as pd
from termcolor import colored, cprint
from dotenv import load_dotenv
import requests

# Add project root to path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

# Import Moon Dev modules
from src.config import EXCHANGE, MONITORED_TOKENS
from src import nice_funcs as n
from src.models.model_factory import model_factory

# Load environment variables
load_dotenv()

# ============== AI DECISION PROMPT ==============
AI_DECISION_PROMPT = """You are an AI trading assistant evaluating a Housecoin DCA (Dollar Cost Average) buy signal.

Our strategy has triggered a buy signal because the price has separated sufficiently from the moving averages,
indicating a solid entry point for dollar cost averaging.

Current Market Conditions:
{market_conditions}

Recent Price Data (55 x 5-minute bars):
{price_data}

Technical Analysis:
{technical_analysis}

The strategy wants to buy now because:
{buy_reason}

Please analyze the data provided. You are the final decision layer on top of our existing strategy.

If you agree with the buy signal, respond with exactly: "BUY"
If you disagree, respond with exactly: "DONT BUY"

Then provide a brief explanation of your decision (1-2 sentences).
"""

# ============== STRATEGY CONSTANTS ==============
# Housecoin contract address (Solana)
HOUSECOIN_ADDRESS = "DitHyRMQiSDhn5cnKMJV2CDDt6sVct96YrECiM49pump"
USDC_ADDRESS = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"

# Exit criteria
EXIT_PRICE = 1.68  # Sell everything at $1.68

# When BELOW 20-day SMA: Aggressive accumulation mode
BELOW_SMA_BUY_MINUTES = 15  # Buy every X minutes
BELOW_SMA_BUY_AMOUNT = 2  # Buy $Y each time (in USDC)
BELOW_SMA_DAILY_CAP = 1500  # Max $Z per day

# When ABOVE 20-day SMA: Smart entry mode
ABOVE_SMA_CHECK_MINUTES = 5  # Check every X minutes
ABOVE_SMA_BUY_AMOUNT = 1  # Buy amount when conditions met
ABOVE_SMA_DAILY_CAP = 100  # Max daily spend when above SMA
DAILY_LOW_THRESHOLD = 0.01  # Buy within 1% of daily low

# Trading hours (ET)
TRADING_START_HOUR = 6  # 6 AM ET
TRADING_END_HOUR = 20  # 8 PM ET (20:00 in 24-hour format)

# Trading Configuration
SLIPPAGE = 499  # 5% slippage
PRIORITY_FEE = 20000  # Priority fee for transactions

# AI Model Configuration
AI_MODEL_TYPE = 'xai'  # Using xAI's Grok for fast reasoning
AI_MODEL_NAME = 'grok-4-fast-reasoning'  # Grok-4 fast - best value with 2M context!
AI_TEMPERATURE = 0.3  # Lower temperature for more consistent decisions
AI_MAX_TOKENS = 150  # Short responses for buy/don't buy decisions

# State file for tracking buys
STATE_FILE = os.path.join(project_root, "src", "data", "housecoin_agent", "housecoin_agent_state.json")

# ============== HOUSECOIN THESIS ==============
THESIS_STATEMENTS = [
    "Every single real estate agent in the world will eventually have to own Housecoin",
    "Anyone who owns a house needs to hedge their home with Housecoin",
    "Houses are in a huge bubble. No one can afford real estate, but they CAN afford Housecoin",
    "1 House = 1 Housecoin - It's that simple",
    "Eventually all real estate will be on blockchain. Housecoin is best positioned",
    "2.3 billion homes in the world but only 1 billion Housecoin - supply shock incoming",
    "Real estate is a $300+ trillion market. Housecoin captures this digitally",
]

class HousecoinAgent:
    def __init__(self):
        """Initialize the Housecoin DCA Agent"""
        cprint("\n🏠 Initializing Housecoin DCA Agent with AI Decision Layer 🏠", "cyan", attrs=['bold'])

        # Initialize AI model
        cprint(f"🤖 Loading {AI_MODEL_TYPE} model: {AI_MODEL_NAME}", "yellow")
        self.model = model_factory.get_model(AI_MODEL_TYPE, AI_MODEL_NAME)

        if not self.model:
            cprint(f"❌ Failed to initialize {AI_MODEL_TYPE} model!", "red")
            raise ValueError("Model initialization failed")

        cprint(f"✅ AI Model ready: {self.model.model_name}", "green")

        # Load state
        self.state = self.load_state()
        self.last_buy_time = datetime.fromisoformat(self.state['last_buy_time']) if self.state['last_buy_time'] else None

        # API keys
        self.birdeye_api_key = os.getenv('birdeye_api_key') or os.getenv('BIRDEYE_API_KEY')

        if not self.birdeye_api_key:
            cprint("⚠️ Warning: BIRDEYE_API_KEY not found", "yellow")

        cprint("✅ Housecoin Agent initialized!", "green")
        cprint("⚠️ NOT FINANCIAL ADVICE - Trade at your own risk!", "yellow", attrs=['bold'])

    def load_state(self):
        """Load agent state from file"""
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        return {
            'daily_spent': 0,
            'last_reset_date': str(datetime.now().date()),
            'last_buy_time': None,
            'buy_history': [],
            'total_bought': 0,
            'ai_decisions': []
        }

    def save_state(self):
        """Save agent state to file"""
        with open(STATE_FILE, 'w') as f:
            json.dump(self.state, f, indent=2)

    def get_current_price_and_sma(self):
        """Fetch current price and calculate 20-day SMA"""
        try:
            # Get 20 days of daily data for SMA
            df = n.get_data(HOUSECOIN_ADDRESS, 20, '1D')

            if df is not None and not df.empty:
                # Check which columns are available - try different column names
                close_col = None
                if 'close' in df.columns:
                    close_col = 'close'
                elif 'Close' in df.columns:
                    close_col = 'Close'
                elif 'c' in df.columns:
                    close_col = 'c'
                elif 'value' in df.columns:
                    close_col = 'value'

                if close_col:
                    # Calculate 20-day SMA
                    sma_20 = df[close_col].mean()
                    current_price = df.iloc[-1][close_col]
                    cprint(f"✅ Price: ${current_price:.8f}, SMA: ${sma_20:.8f}", "green")
                    return current_price, sma_20
                else:
                    cprint(f"❌ No close column found. Available columns: {df.columns.tolist()}", "red")
                    # Try to use the last numeric column as price
                    numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
                    if len(numeric_cols) > 0:
                        cprint(f"Using numeric column: {numeric_cols[-1]}", "yellow")
                        sma_20 = df[numeric_cols[-1]].mean()
                        current_price = df.iloc[-1][numeric_cols[-1]]
                        return current_price, sma_20

        except Exception as e:
            cprint(f"Error fetching price data: {e}", "red")
            import traceback
            traceback.print_exc()

        return None, None

    def get_5min_data(self, bars=55):
        """Fetch 5-minute candles for AI analysis"""
        try:
            # Get 55 bars of 5-minute data (about 4.5 hours)
            df = n.get_data(HOUSECOIN_ADDRESS, 0.25, '5m')  # 0.25 days = ~6 hours

            if df is not None and not df.empty:
                # Get last 55 bars
                df = df.tail(bars)

                # Check which columns are available
                close_col = None
                if 'close' in df.columns:
                    close_col = 'close'
                elif 'Close' in df.columns:
                    close_col = 'Close'
                elif 'c' in df.columns:
                    close_col = 'c'
                elif 'value' in df.columns:
                    close_col = 'value'

                if close_col and len(df) >= 20:
                    # Calculate 20-period SMA on 5-minute chart
                    sma_5min_20 = df.tail(20)[close_col].mean()
                    current_price = df.iloc[-1][close_col]
                    return df, current_price, sma_5min_20
                elif not close_col:
                    # Try to use the last numeric column
                    numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
                    if len(numeric_cols) > 0 and len(df) >= 20:
                        close_col = numeric_cols[-1]
                        sma_5min_20 = df.tail(20)[close_col].mean()
                        current_price = df.iloc[-1][close_col]
                        return df, current_price, sma_5min_20

        except Exception as e:
            cprint(f"Error fetching 5-min data: {e}", "red")

        return None, None, None

    def get_daily_low(self):
        """Get today's low price"""
        try:
            # Get today's hourly data
            df = n.get_data(HOUSECOIN_ADDRESS, 1, '1H')  # 1 day of hourly data

            if df is not None and not df.empty:
                # Filter for today only
                today = datetime.now().date()

                # Check for datetime column variations
                date_col = None
                if 'datetime' in df.columns:
                    date_col = 'datetime'
                elif 'date' in df.columns:
                    date_col = 'date'
                elif 'time' in df.columns:
                    date_col = 'time'
                elif 'timestamp' in df.columns:
                    date_col = 'timestamp'

                if date_col:
                    df['date'] = pd.to_datetime(df[date_col]).dt.date
                    today_df = df[df['date'] == today]

                    # Check for low column variations
                    low_col = None
                    if 'low' in df.columns:
                        low_col = 'low'
                    elif 'Low' in df.columns:
                        low_col = 'Low'
                    elif 'l' in df.columns:
                        low_col = 'l'

                    if low_col and not today_df.empty:
                        return today_df[low_col].min()

        except Exception as e:
            cprint(f"Error fetching daily low: {e}", "red")

        return None

    def is_trading_hours(self):
        """Check if current time is within trading hours (ET)"""
        et_tz = timezone(timedelta(hours=-5))  # ET is UTC-5
        current_et = datetime.now(et_tz)
        current_hour = current_et.hour

        if TRADING_END_HOUR == 24:
            return TRADING_START_HOUR <= current_hour
        return TRADING_START_HOUR <= current_hour < TRADING_END_HOUR

    def get_ai_confirmation(self, current_price, sma_20, buy_reason, df_5min):
        """Get AI confirmation for the buy signal"""
        try:
            # Prepare market conditions
            market_conditions = f"""
- Current Price: ${current_price:.8f}
- 20-Day SMA: ${sma_20:.8f}
- Price vs SMA: {((current_price/sma_20 - 1) * 100):+.2f}%
- Trading Hours: {'Yes' if self.is_trading_hours() else 'No'}
- Daily Spent: ${self.state['daily_spent']}
"""

            # Prepare price data (last 55 5-minute bars)
            if df_5min is not None:
                # Get available columns for display
                cols_to_show = []
                for col in ['datetime', 'date', 'time', 'timestamp', 'open', 'high', 'low', 'close', 'volume', 'value']:
                    if col in df_5min.columns:
                        cols_to_show.append(col)

                # If we have columns to show, display them
                if cols_to_show:
                    price_data = df_5min[cols_to_show].tail(10).to_string()
                else:
                    # Just show all columns if our specific ones aren't found
                    price_data = df_5min.tail(10).to_string()

                # Find the close column for technical analysis
                close_col = None
                for col in ['close', 'Close', 'c', 'value']:
                    if col in df_5min.columns:
                        close_col = col
                        break

                # Technical analysis
                rsi = None
                technical_analysis = ""

                if close_col:
                    if len(df_5min) >= 14:
                        # Simple RSI calculation
                        delta = df_5min[close_col].diff()
                        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                        rs = gain / loss
                        rsi = 100 - (100 / (1 + rs)).iloc[-1]

                    technical_analysis = f"- 5-min SMA (20): ${df_5min.tail(20)[close_col].mean():.8f}\n"

                    # Add volume if available
                    if 'volume' in df_5min.columns:
                        technical_analysis += f"- Volume (last 5 bars): {df_5min.tail(5)['volume'].mean():.0f}\n"

                    # Add price range if we have high/low columns
                    low_col = None
                    high_col = None
                    for col in ['low', 'Low', 'l']:
                        if col in df_5min.columns:
                            low_col = col
                            break
                    for col in ['high', 'High', 'h']:
                        if col in df_5min.columns:
                            high_col = col
                            break

                    if low_col and high_col:
                        technical_analysis += f"- Price Range (last hour): ${df_5min.tail(12)[low_col].min():.8f} - ${df_5min.tail(12)[high_col].max():.8f}\n"

                    if rsi:
                        technical_analysis += f"- RSI (14): {rsi:.1f}"
            else:
                price_data = "No recent price data available"
                technical_analysis = "Technical indicators unavailable"

            # Prepare the prompt
            prompt = AI_DECISION_PROMPT.format(
                market_conditions=market_conditions,
                price_data=price_data,
                technical_analysis=technical_analysis,
                buy_reason=buy_reason
            )

            # Get AI decision
            cprint("\n🤖 Consulting AI for trade confirmation...", "cyan")
            response = self.model.generate_response(
                system_prompt="You are a trading assistant that must respond with either 'BUY' or 'DONT BUY' followed by a brief explanation.",
                user_content=prompt,
                temperature=AI_TEMPERATURE,
                max_tokens=AI_MAX_TOKENS
            )

            # Parse response
            if response:
                response_text = str(response).strip().upper()

                # Check for BUY or DONT BUY
                if "BUY" in response_text and "DONT" not in response_text and "DON'T" not in response_text:
                    cprint("✅ AI APPROVED: BUY", "green", attrs=['bold'])
                    return True, response
                else:
                    cprint("❌ AI REJECTED: DON'T BUY", "red", attrs=['bold'])
                    return False, response
            else:
                cprint("⚠️ AI did not respond, defaulting to NO BUY", "yellow")
                return False, "No response from AI"

        except Exception as e:
            cprint(f"❌ Error getting AI confirmation: {e}", "red")
            return False, f"Error: {str(e)}"

    def execute_buy(self, amount, reason):
        """Execute a market buy after AI confirmation"""
        try:
            cprint(f"\n💰 Executing buy for ${amount} worth of Housecoin", "green", attrs=['bold'])

            # Execute buy using nice_funcs with slippage
            tx_id = n.market_buy(HOUSECOIN_ADDRESS, amount, SLIPPAGE)

            if tx_id:
                cprint(f"✅ Buy successful! TX: {tx_id}", "green")

                # Update state
                self.state['daily_spent'] += amount
                self.state['last_buy_time'] = datetime.now().isoformat()
                self.state['total_bought'] += amount
                self.state['buy_history'].append({
                    'time': datetime.now().isoformat(),
                    'amount': amount,
                    'reason': reason,
                    'tx_id': tx_id
                })
                self.save_state()
                self.last_buy_time = datetime.now()

                return True
            else:
                cprint("❌ Buy transaction failed", "red")
                return False

        except Exception as e:
            cprint(f"❌ Buy execution error: {e}", "red")
            return False

    def run(self):
        """Main agent loop"""
        print("\n" + "="*60)
        cprint("🏠 Housecoin DCA Agent with AI Decisions 🏠", "cyan", attrs=['bold'])
        print("="*60)
        cprint("⚠️ NOT FINANCIAL ADVICE - This may go to zero!", "yellow", attrs=['bold'])
        cprint(f"Thesis: 1 House = 1 Housecoin", "magenta")
        cprint(f"Exit Target: ${EXIT_PRICE}", "yellow")
        cprint(f"Trading Hours: {TRADING_START_HOUR}AM-{TRADING_END_HOUR-12}PM ET", "cyan")
        cprint(f"AI Model: {AI_MODEL_TYPE} - {AI_MODEL_NAME}", "green")
        print("="*60)

        while True:
            try:
                # Reset daily spending at midnight
                current_date = str(datetime.now().date())
                if current_date != self.state['last_reset_date']:
                    self.state['daily_spent'] = 0
                    self.state['last_reset_date'] = current_date
                    self.save_state()
                    cprint(f"\n📅 New day! Daily spending reset.", "cyan")

                # Get current price and SMA
                current_price, sma_20 = self.get_current_price_and_sma()
                if current_price is None:
                    cprint("Failed to get price data, retrying...", "yellow")
                    time.sleep(60)
                    continue

                # Check exit criteria
                if current_price >= EXIT_PRICE:
                    cprint(f"\n🚀 EXIT PRICE REACHED! Current: ${current_price:.8f} Target: ${EXIT_PRICE}", "yellow", attrs=['bold', 'blink'])
                    cprint("Manual intervention required to sell position", "red")
                    cprint(f"Total invested: ${self.state['total_bought']}", "green")
                    break

                # Check trading hours
                if not self.is_trading_hours():
                    cprint(f"\n🌙 Outside trading hours ({TRADING_START_HOUR}:00 AM - {TRADING_END_HOUR-12}:00 PM ET)", "blue")
                    print(f"  Current price: ${current_price:.8f}")
                    print(f"  20-Day SMA: ${sma_20:.8f}")
                    time.sleep(300)  # Check every 5 minutes when outside hours
                    continue

                below_sma = current_price < sma_20

                # Get 5-minute data for analysis
                df_5min, current_5min, sma_5min = self.get_5min_data()
                below_5min_sma = current_5min < sma_5min if sma_5min else False

                # Display status
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}]", end=" ")
                cprint(f"${current_price:.8f}", "yellow", attrs=['bold'])

                # SMA status
                sma_status = "BELOW" if below_sma else "ABOVE"
                sma_color = "red" if below_sma else "green"
                print(f"20D-SMA: ", end="")
                cprint(f"{sma_status} {((current_price/sma_20 - 1) * 100):+.1f}%", sma_color, end=" ")

                # 5-min SMA
                if sma_5min:
                    sma5_status = "BELOW" if below_5min_sma else "ABOVE"
                    sma5_color = "red" if below_5min_sma else "green"
                    print("| 5M-SMA: ", end="")
                    cprint(f"{sma5_status}", sma5_color)
                else:
                    print()

                # Strategy logic
                should_check_buy = False
                buy_amount = 0
                buy_reason = ""

                if below_sma:
                    # Aggressive accumulation mode
                    if self.state['daily_spent'] >= BELOW_SMA_DAILY_CAP:
                        cprint(f"⚠️ Daily cap reached (${BELOW_SMA_DAILY_CAP})", "yellow")
                    elif self.last_buy_time and (datetime.now() - self.last_buy_time).seconds < BELOW_SMA_BUY_MINUTES * 60:
                        seconds_until_next = BELOW_SMA_BUY_MINUTES * 60 - (datetime.now() - self.last_buy_time).seconds
                        cprint(f"⏳ Next buy check in {seconds_until_next//60}m {seconds_until_next%60}s", "yellow")
                    elif not below_5min_sma:
                        cprint(f"⏸️ Waiting for 5-min SMA confirmation", "yellow")
                    else:
                        should_check_buy = True
                        buy_amount = BELOW_SMA_BUY_AMOUNT
                        buy_reason = "Price below both 20-day and 5-min SMAs - DCA accumulation signal"
                        cprint("📊 Strategy: ACCUMULATION MODE", "red", attrs=['bold'])
                else:
                    # Smart entry mode
                    daily_low = self.get_daily_low()
                    if daily_low:
                        percent_from_low = ((current_price - daily_low) / daily_low) * 100

                        if percent_from_low <= DAILY_LOW_THRESHOLD * 100:
                            if self.state['daily_spent'] >= ABOVE_SMA_DAILY_CAP:
                                cprint(f"⚠️ Daily cap reached (${ABOVE_SMA_DAILY_CAP})", "yellow")
                            else:
                                should_check_buy = True
                                buy_amount = ABOVE_SMA_BUY_AMOUNT
                                buy_reason = f"Price near daily low ({percent_from_low:.1f}% from low)"
                                cprint("📊 Strategy: NEAR DAILY LOW", "green", attrs=['bold'])
                        else:
                            cprint(f"⏸️ Waiting ({percent_from_low:.1f}% from low, need < {DAILY_LOW_THRESHOLD*100}%)", "yellow")

                # Check with AI if strategy triggered
                if should_check_buy:
                    cprint(f"\n🎯 Strategy triggered! Checking with AI...", "cyan", attrs=['bold'])

                    # Get AI confirmation
                    ai_approved, ai_response = self.get_ai_confirmation(
                        current_price, sma_20, buy_reason, df_5min
                    )

                    # Log AI decision
                    self.state['ai_decisions'].append({
                        'time': datetime.now().isoformat(),
                        'price': current_price,
                        'approved': ai_approved,
                        'response': str(ai_response)[:200]  # Limit response length
                    })
                    self.save_state()

                    if ai_approved:
                        # Execute the buy
                        estimated_housecoin = int(buy_amount / current_price)
                        cprint(f"\n🚀 Buying ~{estimated_housecoin:,} Housecoin for ${buy_amount}", "green", attrs=['bold'])

                        if self.execute_buy(buy_amount, buy_reason):
                            # Show a random thesis after successful buy
                            thesis = random.choice(THESIS_STATEMENTS)
                            print()
                            cprint("🏠 HOUSECOIN THESIS:", "cyan", attrs=['bold'])
                            cprint(thesis, "white", "on_blue")
                    else:
                        cprint("\n🤖 AI rejected the buy signal. Waiting for better conditions...", "yellow")
                        print(f"AI reasoning: {str(ai_response)[:150]}")

                # Sleep based on mode
                if below_sma:
                    time.sleep(60)  # Check every minute when below SMA
                else:
                    time.sleep(ABOVE_SMA_CHECK_MINUTES * 60)  # Check every X minutes when above SMA

            except KeyboardInterrupt:
                cprint("\n\n👋 Shutting down Housecoin Agent...", "yellow")
                cprint(f"Total invested: ${self.state['total_bought']}", "green")
                cprint(f"Total buys: {len(self.state['buy_history'])}", "cyan")
                break

            except Exception as e:
                cprint(f"\n❌ Error in main loop: {e}", "red")
                time.sleep(60)

def main():
    """Run the Housecoin DCA Agent"""
    try:
        # Check if we're on Solana
        if EXCHANGE != 'solana':
            cprint("⚠️ Warning: Housecoin is currently only on Solana", "yellow")
            cprint(f"Current exchange: {EXCHANGE}", "yellow")
            cprint("Switching to Solana mode for Housecoin...", "cyan")

        # Initialize and run the agent
        agent = HousecoinAgent()
        agent.run()

    except Exception as e:
        cprint(f"❌ Fatal error: {e}", "red")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()