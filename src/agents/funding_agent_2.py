"""
💰 Moon Dev's HyperLiquid Funding Rate Scanner
Built with love by Moon Dev 🚀

This agent scans ALL HyperLiquid symbols for funding rate anomalies and announces the top 5 biggest and smallest with AI voice.

Need an API key? for a limited time, bootcamp members get free api keys for claude, openai, helius, birdeye & quant elite gets access to the moon dev api. join here: https://algotradecamp.com
"""

import os
import pandas as pd
import time
import requests
from datetime import datetime
from termcolor import colored, cprint
from dotenv import load_dotenv
import openai
from pathlib import Path
from src.agents.base_agent import BaseAgent
import traceback

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Configuration
BASE_URL = 'https://api.hyperliquid.xyz/info'
CHECK_INTERVAL_MINUTES = 15  # How often to scan funding rates

# Voice settings
VOICE_MODEL = "tts-1"
VOICE_NAME = "fable"  # Options: alloy, echo, fable, onyx, nova, shimmer
VOICE_SPEED = 1.0

class FundingAgent2(BaseAgent):
    """Moon Dev's HyperLiquid Funding Rate Scanner 💰"""

    def __init__(self):
        """Initialize the Funding Agent 2"""
        super().__init__('funding_agent_2')

        load_dotenv()

        # Initialize OpenAI client for voice
        openai_key = os.getenv("OPENAI_KEY")
        if not openai_key:
            raise ValueError("🚨 OPENAI_KEY not found in environment variables!")
        openai.api_key = openai_key

        # Create directories
        self.audio_dir = PROJECT_ROOT / "src" / "audio"
        self.data_dir = PROJECT_ROOT / "src" / "data" / "funding_agent_2"
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        cprint("💰 Moon Dev's HyperLiquid Funding Scanner initialized!", "green")

    def get_all_symbols(self):
        """Get all available symbols from HyperLiquid"""
        try:
            cprint("\n🔄 Fetching all HyperLiquid symbols...", "cyan")
            response = requests.post(
                BASE_URL,
                headers={'Content-Type': 'application/json'},
                json={"type": "meta"}
            )

            if response.status_code == 200:
                data = response.json()
                if 'universe' in data:
                    symbols = [coin['name'] for coin in data['universe']]
                    cprint(f"✅ Found {len(symbols)} symbols", "green")
                    return symbols
                else:
                    cprint("❌ No universe data in response", "red")
                    return []
            else:
                cprint(f"❌ Bad status code: {response.status_code}", "red")
                return []
        except Exception as e:
            cprint(f"❌ Error getting symbols: {str(e)}", "red")
            traceback.print_exc()
            return []

    def get_all_funding_rates(self):
        """Get funding rates for all symbols"""
        try:
            cprint("\n🔄 Fetching funding rates for all symbols...", "cyan")
            response = requests.post(
                BASE_URL,
                headers={'Content-Type': 'application/json'},
                json={"type": "metaAndAssetCtxs"}
            )

            if response.status_code == 200:
                data = response.json()
                if len(data) >= 2 and isinstance(data[0], dict) and isinstance(data[1], list):
                    # Get universe (symbols) from first element
                    universe = data[0]['universe']
                    funding_data = data[1]

                    # Create list of funding rates
                    funding_list = []
                    for i, coin in enumerate(universe):
                        if i < len(funding_data):
                            asset_data = funding_data[i]
                            symbol = coin['name']

                            # Calculate rates
                            # The API returns hourly funding rate
                            hourly_rate = float(asset_data['funding']) * 100  # Convert to percentage
                            annual_rate = hourly_rate * 24 * 365  # Convert to annual

                            funding_list.append({
                                'symbol': symbol,
                                'hourly_rate': hourly_rate,
                                'annual_rate': annual_rate,
                                'mark_price': float(asset_data['markPx']),
                                'open_interest': float(asset_data['openInterest'])
                            })

                    cprint(f"✅ Retrieved funding rates for {len(funding_list)} symbols", "green")
                    return pd.DataFrame(funding_list)
                else:
                    cprint("❌ Unexpected response format", "red")
                    return pd.DataFrame()
            else:
                cprint(f"❌ Bad status code: {response.status_code}", "red")
                return pd.DataFrame()
        except Exception as e:
            cprint(f"❌ Error getting funding rates: {str(e)}", "red")
            traceback.print_exc()
            return pd.DataFrame()

    def find_anomalies(self, df):
        """Find top 3 most positive and most negative funding rates"""
        if df.empty:
            return None, None

        # Sort by annual rate
        df_sorted = df.sort_values('annual_rate', ascending=False)

        # Get top 3 most positive
        top_3_positive = df_sorted.head(3)

        # Get top 3 most negative
        top_3_negative = df_sorted.tail(3).sort_values('annual_rate')

        return top_3_positive, top_3_negative

    def format_announcement(self, top_3_positive, top_3_negative):
        """Format the funding anomalies into a speech-friendly message"""
        try:
            message_parts = ["ayo moon dev seven seven seven! Let me tell you about the funding rate anomalies on HyperLiquid."]

            # Announce most positive funding rates
            message_parts.append("First, the top 3 most positive funding rates.")
            for idx, row in top_3_positive.iterrows():
                symbol = row['symbol']
                annual_rate = row['annual_rate']
                message_parts.append(
                    f"{symbol} has a positive funding rate of {annual_rate:.2f} percent annual."
                )

            # Announce most negative funding rates
            message_parts.append("Now, the top 3 most negative funding rates.")
            for idx, row in top_3_negative.iterrows():
                symbol = row['symbol']
                annual_rate = row['annual_rate']
                # Make sure to say "negative" clearly
                message_parts.append(
                    f"{symbol} has a negative funding rate of {annual_rate:.2f} percent annual."
                )

            message_parts.append("That's all for now! Moon Dev out!")

            return " ".join(message_parts)

        except Exception as e:
            cprint(f"❌ Error formatting announcement: {str(e)}", "red")
            traceback.print_exc()
            return None

    def announce(self, message):
        """Announce message using OpenAI TTS"""
        if not message:
            return

        try:
            cprint(f"\n📢 Moon Dev is announcing the funding anomalies...", "yellow")

            # Generate speech
            response = openai.audio.speech.create(
                model=VOICE_MODEL,
                voice=VOICE_NAME,
                input=message,
                speed=VOICE_SPEED
            )

            # Save audio file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            audio_file = self.audio_dir / f"funding_anomalies_{timestamp}.mp3"

            # Write audio to file
            with open(audio_file, 'wb') as f:
                f.write(response.content)

            cprint(f"💾 Saved audio to: {audio_file}", "green")

            # Play audio using system command
            os.system(f"afplay {audio_file}")

            cprint("✅ Announcement completed!", "green")

        except Exception as e:
            cprint(f"❌ Error in announcement: {str(e)}", "red")
            traceback.print_exc()

    def print_fancy_table(self, df, title):
        """Print a fancy table of funding rates"""
        print("\n" + "╔" + "═" * 70 + "╗")
        print(f"║{title.center(70)}║")
        print("╠" + "═" * 70 + "╣")
        print("║  Symbol      │  Hourly Rate  │  Annual Rate  │  Open Interest ║")
        print("╟" + "─" * 70 + "╢")

        for _, row in df.iterrows():
            symbol = row['symbol'][:10]
            hourly = row['hourly_rate']
            annual = row['annual_rate']
            oi = row['open_interest']

            # Color based on rate
            if annual > 20:
                status = "🔥"
            elif annual < -5:
                status = "❄️"
            else:
                status = "  "

            print(f"║ {status} {symbol:<10} │  {hourly:>9.4f}%  │  {annual:>9.2f}%  │  {oi:>13,.0f} ║")

        print("╚" + "═" * 70 + "╝")

    def run_scan_cycle(self):
        """Run one funding rate scan cycle"""
        try:
            cprint("\n🚀 Starting Moon Dev's Funding Rate Scan...", "green", attrs=['bold'])

            # Get all funding rates
            df = self.get_all_funding_rates()

            if df.empty:
                cprint("❌ No funding data retrieved", "red")
                return

            # Save full data to CSV
            output_file = self.data_dir / f"funding_rates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            df.to_csv(output_file, index=False)
            cprint(f"\n💾 Saved full funding data to: {output_file}", "green")

            # Print summary statistics
            cprint("\n📊 Funding Rate Summary:", "cyan", attrs=['bold'])
            print(f"Total symbols: {len(df)}")
            print(f"Average annual rate: {df['annual_rate'].mean():.2f}%")
            print(f"Highest annual rate: {df['annual_rate'].max():.2f}% ({df.loc[df['annual_rate'].idxmax(), 'symbol']})")
            print(f"Lowest annual rate: {df['annual_rate'].min():.2f}% ({df.loc[df['annual_rate'].idxmin(), 'symbol']})")

            # Find anomalies
            top_3_positive, top_3_negative = self.find_anomalies(df)

            if top_3_positive is not None and top_3_negative is not None:
                # Print fancy tables
                self.print_fancy_table(top_3_positive, "🌙 Top 3 MOST POSITIVE Funding Rates (Moon Dev) 🌙")
                self.print_fancy_table(top_3_negative, "🌙 Top 3 MOST NEGATIVE Funding Rates (Moon Dev) 🌙")

                # Format and announce
                message = self.format_announcement(top_3_positive, top_3_negative)
                if message:
                    self.announce(message)

            cprint("\n✨ Moon Dev's Funding Scanner cycle completed! ✨", "green", attrs=['bold'])

        except Exception as e:
            cprint(f"❌ Error in scan cycle: {str(e)}", "red")
            traceback.print_exc()

    def run(self):
        """Run the funding rate scanner continuously"""
        cprint("\n🚀 Moon Dev's HyperLiquid Funding Scanner Starting...", "green", attrs=['bold'])
        cprint(f"⏰ Scanning every {CHECK_INTERVAL_MINUTES} minutes", "yellow")
        cprint("Press Ctrl+C to stop\n", "yellow")

        while True:
            try:
                self.run_scan_cycle()
                cprint(f"\n💤 Sleeping for {CHECK_INTERVAL_MINUTES} minutes...", "yellow")
                time.sleep(CHECK_INTERVAL_MINUTES * 60)

            except KeyboardInterrupt:
                cprint("\n👋 Moon Dev's Funding Scanner shutting down gracefully...", "yellow")
                break
            except Exception as e:
                cprint(f"❌ Error in main loop: {str(e)}", "red")
                traceback.print_exc()
                cprint(f"⏰ Retrying in 1 minute...", "yellow")
                time.sleep(60)  # Sleep for a minute before retrying

if __name__ == "__main__":
    agent = FundingAgent2()
    agent.run()
