'''
🌙 Moon Dev's Transaction Scanner - Built with love by Moon Dev 🚀
Watches for new Solana transactions and displays them with fun animations!
'''

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import requests
import pandas as pd
import time
import random
from termcolor import colored
import logging
from rich.console import Console
from rich import print as rprint
from playsound import playsound

# 🌙 Moon Dev: Calculate project root dynamically
PROJECT_ROOT = Path(__file__).parent.parent.parent
GITHUB_DIR = PROJECT_ROOT.parent  # Parent folder containing all repos

# Add src directory to Python path
src_path = str(Path(__file__).parent.parent)
if src_path not in sys.path:
    sys.path.append(src_path)

# Load environment variables for API key
load_dotenv()

# Suppress ALL logs except critical
logging.getLogger().setLevel(logging.CRITICAL)

# Initialize Rich console
console = Console()

# Constants
PAST_TRANSACTIONS_TO_SHOW = 40
CHECK_INTERVAL = 3
DISPLAY_DELAY = 0.5
BASE_URL = "http://api.moondev.com:8000"
SOUND_ENABLED = True
AUTO_OPEN_BROWSER = True  # Set to True to automatically open new transactions in browser
USE_DEXSCREENER = True  # Set to True to use DexScreener instead of Birdeye
DATA_FOLDER = Path(__file__).parent.parent / "data" / "tx_agent"  # Folder for transaction data

# Background colors for transaction announcements
BACKGROUND_COLORS = [
    'on_blue', 'on_magenta', 'on_cyan', 'on_green',  
    'on_yellow'  # Removed white for better readability
]

TRANSACTION_EMOJIS = [
    "💸", "💰", "💎", "💵", "💶", "💷",  # Money
    "🏦", "🏧", "💱", "💲", "🤑", "💹",  # Banking & finance
    "📈", "📊", "📉", "🎯", "🎰", "🎲",  # Trading & games
    "🌙", "⭐", "✨", "💫", "🌟", "⚡",   # Moon Dev specials
]

# Sound effects paths - 🌙 Moon Dev: External repo (sibling to this repo)
SOUND_EFFECTS = [
    str(GITHUB_DIR / "Untitled" / "sounds" / "crack1.wav"),
    str(GITHUB_DIR / "Untitled" / "sounds" / "golfhit25.MP3")
]

class TxScanner:
    def __init__(self):
        """🌙 Moon Dev's Transaction Scanner - Built with love by Moon Dev 🚀"""
        self.base_dir = Path(__file__).parent / "api_data"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir = DATA_FOLDER
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.seen_links = set()
        self.last_check_time = None
        self.sound_enabled = SOUND_ENABLED
        self.api_key = os.getenv('MOONDEV_API_KEY')
        self.headers = {'X-API-Key': self.api_key} if self.api_key else {}
        self.session = requests.Session()
        
        # Only check sound files if sound is enabled
        if self.sound_enabled:
            for sound_file in SOUND_EFFECTS:
                if not os.path.exists(sound_file):
                    self.sound_enabled = False
                    break

    def get_recent_transactions(self):
        """Fetch recent transactions data silently"""
        try:
            url = f'{BASE_URL}/copybot/data/recent_txs'
            response = self.session.get(url, headers=self.headers)
            response.raise_for_status()
            
            # Save to cache
            save_path = self.base_dir / "recent_txs.csv"
            with open(save_path, 'wb') as f:
                f.write(response.content)
            
            # Read without printing status
            with pd.option_context('mode.chained_assignment', None):
                df = pd.read_csv(save_path)
                return df
                
        except Exception:
            return None
            
    def get_display_link(self, birdeye_link):
        """Convert Birdeye link to DexScreener link if enabled"""
        if not USE_DEXSCREENER:
            return birdeye_link
            
        try:
            # Extract contract address from Birdeye link
            # Format: https://birdeye.so/token/CONTRACT_ADDRESS?chain=solana
            contract_address = birdeye_link.split('/token/')[1].split('?')[0]
            return f"https://dexscreener.com/solana/{contract_address}"
        except Exception:
            return birdeye_link
            
    def display_past_transaction(self, row):
        """Display a past transaction without animation"""
        try:
            time_obj = pd.to_datetime(row['blockTime'], unit='s')
            time_str = time_obj.strftime("%m-%d %H:%M")
        except:
            time_str = "Unknown Time"
            
        random_emoji = random.choice(TRANSACTION_EMOJIS)
        random_bg = random.choice(BACKGROUND_COLORS)
        
        display_link = self.get_display_link(row['birdeye_link'])
        
        # Single line format without extra newlines
        print(f"{colored(f'{random_emoji} NEW TRANSACTION {time_str}', 'white', random_bg)} {display_link}")
        
        # Auto-open in browser if enabled
        if AUTO_OPEN_BROWSER:
            try:
                import webbrowser
                webbrowser.open(display_link)
            except Exception:
                pass
                
        try:
            time.sleep(DISPLAY_DELAY)
        except KeyboardInterrupt:
            raise
            
    def save_transactions_for_analysis(self, df):
        """Save transactions to CSV for analysis"""
        try:
            # Add timestamp column for when we saved this data
            df['saved_at'] = pd.Timestamp.now()
            
            # Save to CSV
            save_path = self.data_dir / "recent_transactions.csv"
            df.to_csv(save_path, index=False)
        except Exception:
            pass
            
    def show_past_transactions(self):
        """Display past transactions"""
        df = self.get_recent_transactions()
        if df is None or df.empty:
            return
            
        # Remove duplicates keeping only the first occurrence of each birdeye link
        df = df.drop_duplicates(subset=['birdeye_link'], keep='first')
        
        # Get the most recent transactions
        recent_txs = df.tail(PAST_TRANSACTIONS_TO_SHOW)
        
        # Store seen transactions and last check time
        self.seen_links = set(recent_txs['birdeye_link'])
        self.last_check_time = pd.to_datetime(recent_txs.iloc[-1]['blockTime'], unit='s')
        
        # Save transactions for analysis
        self.save_transactions_for_analysis(recent_txs)
        
        print("\n🔍 Recent Transactions:")
        for _, row in recent_txs.iterrows():
            self.display_past_transaction(row)
            
    def play_sound(self):
        """Play a random sound effect safely"""
        if not self.sound_enabled:
            return
            
        try:
            sound_file = random.choice(SOUND_EFFECTS)
            playsound(sound_file, block=False)
        except Exception:
            pass
            
    def display_transaction(self, row):
        """Display a new transaction with sound"""
        try:
            time_obj = pd.to_datetime(row['blockTime'], unit='s')
            time_str = time_obj.strftime("%m-%d %H:%M")
        except:
            time_str = "Unknown Time"
            
        random_emoji = random.choice(TRANSACTION_EMOJIS)
        random_bg = random.choice(BACKGROUND_COLORS)
        
        display_link = self.get_display_link(row['birdeye_link'])
        
        # Play sound and display with color
        self.play_sound()
        print(f"\n{colored(f'{random_emoji} NEW TRANSACTION {time_str}', 'white', random_bg)} {display_link}")
        
        # Auto-open in browser if enabled
        if AUTO_OPEN_BROWSER:
            try:
                import webbrowser
                webbrowser.open(display_link)
            except Exception:
                pass
        
    def monitor_transactions(self):
        """Monitor for new transactions silently"""
        while True:
            try:
                df = self.get_recent_transactions()
                if df is None or df.empty:
                    time.sleep(CHECK_INTERVAL)
                    continue
                
                # Remove duplicates keeping only the first occurrence of each birdeye link
                df = df.drop_duplicates(subset=['birdeye_link'], keep='first')
                
                # Get the newest transaction's time
                current_time = pd.to_datetime(df.iloc[-1]['blockTime'], unit='s')
                
                if self.last_check_time and current_time > self.last_check_time:
                    # Get only transactions newer than our last check
                    new_df = df[pd.to_datetime(df['blockTime'], unit='s') > self.last_check_time]
                    new_links = set(new_df['birdeye_link']) - self.seen_links
                    
                    if new_links:
                        # Get all new transactions in chronological order
                        new_txs = new_df[new_df['birdeye_link'].isin(new_links)]
                        
                        # Save updated transactions list for analysis
                        all_recent = pd.concat([
                            pd.read_csv(self.data_dir / "recent_transactions.csv"),
                            new_txs
                        ]).tail(PAST_TRANSACTIONS_TO_SHOW)
                        self.save_transactions_for_analysis(all_recent)
                        
                        # Display new transactions
                        for _, row in new_txs.iterrows():
                            try:
                                self.display_transaction(row)
                                self.seen_links.add(row['birdeye_link'])
                            except Exception:
                                pass
                        
                        self.last_check_time = current_time
                
            except Exception:
                pass
                
            time.sleep(CHECK_INTERVAL)

def main():
    """Main entry point"""
    scanner = TxScanner()
    scanner.show_past_transactions()
    scanner.monitor_transactions()

if __name__ == "__main__":
    main() 