#!/usr/bin/env python3
"""
🌙 Moon Dev's Giveaway Agent 🌙

Tracks chat participation across YouTube, Twitch, and X via Restream.
- Monitors chat messages and awards points for participation
- Collects and stores Solana wallet addresses
- Maintains point leaderboard for giveaway eligibility

Built with love by Moon Dev 🚀
"""

import sys
from pathlib import Path

# 🌙 Moon Dev: Dynamic path calculation
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "src" / "data"

# Add project root to path
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

import os
import time
import csv
from datetime import datetime
from termcolor import colored, cprint
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import threading

# Load environment variables
env_path = PROJECT_ROOT / '.env'
load_dotenv(dotenv_path=env_path)

# ============================================
# 🎯 CONFIGURATION - EDIT THIS SECTION
# ============================================

# Minimum characters for a chat to be considered
MIN_CHARS = 10

# Flash duration for status messages (seconds)
FLASH_DURATION = 3  # How long to show "+1 username" or "username addy saved"

# 777 auto-point settings
SEVEN_SEVEN_SEVEN_COOLDOWN = 900  # 15 minutes in seconds

# Restream configuration
RESTREAM_EMBED_TOKEN = os.getenv('RESTREAM_EMBED_TOKEN')
if not RESTREAM_EMBED_TOKEN:
    raise ValueError("❌ RESTREAM_EMBED_TOKEN not found in .env file!")
RESTREAM_CHAT_URL = f"https://chat.restream.io/embed?token={RESTREAM_EMBED_TOKEN}"

# CSV file to store user data
GIVEAWAY_DATA_DIR = DATA_DIR / "giveaway_agent"
GIVEAWAY_CSV = GIVEAWAY_DATA_DIR / "participants.csv"

# Poll interval for checking new messages
POLL_INTERVAL = 0.1  # 100ms for responsiveness

# ============================================
# END CONFIGURATION
# ============================================


class GiveawayAgent:
    """🌙 Moon Dev's Giveaway Agent for tracking chat participation"""

    def __init__(self):
        """Initialize the Giveaway Agent"""
        self.driver = None
        self.connected = False
        self.last_message_content = None
        self.last_777_time = {}  # Track last 777 time per user

        # Create data directory
        GIVEAWAY_DATA_DIR.mkdir(parents=True, exist_ok=True)

        # Initialize CSV if doesn't exist
        if not GIVEAWAY_CSV.exists():
            with open(GIVEAWAY_CSV, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['username', 'solana_address', 'points'])

    def load_user_data(self):
        """Load all user data from CSV"""
        users = {}
        try:
            with open(GIVEAWAY_CSV, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    users[row['username']] = {
                        'solana_address': row['solana_address'],
                        'points': int(row['points'])
                    }
        except:
            pass
        return users

    def save_user_data(self, users):
        """Save all user data to CSV"""
        try:
            with open(GIVEAWAY_CSV, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['username', 'solana_address', 'points'])
                for username, data in users.items():
                    writer.writerow([
                        username,
                        data['solana_address'],
                        data['points']
                    ])
        except:
            pass

    def display_status(self, message_type, username=None):
        """
        Print status to terminal - overwrites same line

        Args:
            message_type: 'prompt' or 'point' or 'addy_saved'
            username: Username if showing point earned or addy saved
        """
        # Clear the line
        print('\r' + ' ' * 100, end='', flush=True)

        if message_type == 'prompt':
            print('\r', end='')
            cprint("Drop Sol Wallet To Enter", "black", "on_yellow", end='', flush=True)
        elif message_type == 'point' and username:
            print('\r', end='')
            cprint(f"+1 {username}", "white", "on_green", end='', flush=True)
            # Wait before reverting to prompt
            time.sleep(FLASH_DURATION)
            self.display_status('prompt')
        elif message_type == 'addy_saved' and username:
            print('\r', end='')
            cprint(f"{username} addy saved", "white", "on_green", end='', flush=True)
            # Wait before reverting to prompt
            time.sleep(FLASH_DURATION)
            self.display_status('prompt')

    def process_message(self, username, text):
        """
        Process a chat message

        Args:
            username: Username of the person who sent message
            text: Message text
        """
        # Load current user data
        users = self.load_user_data()

        # Check if user exists
        if username not in users:
            users[username] = {
                'solana_address': 'PENDING',
                'points': 0
            }

        # Check if message looks like a Solana address (32-44 chars, alphanumeric, no spaces)
        if 32 <= len(text) <= 44 and text.isalnum():
            # Always save/update their address (most recent wins)
            users[username]['solana_address'] = text
            self.save_user_data(users)
            # Show "addy saved" (don't give points)
            self.display_status('addy_saved', username)
            return

        # 🎰 777 auto-point check (bypasses all other rules!)
        if '777' in text:
            current_time = time.time()
            last_777 = self.last_777_time.get(username, 0)

            # Check if cooldown has passed (15 minutes)
            if current_time - last_777 >= SEVEN_SEVEN_SEVEN_COOLDOWN:
                # Give point!
                users[username]['points'] += 1
                self.save_user_data(users)

                # Update last 777 time
                self.last_777_time[username] = current_time

                # Display green flash with username
                self.display_status('point', username)
            # If cooldown still active, silently skip
            return

        # Check minimum character count
        if len(text) < MIN_CHARS:
            return

        # Add point!
        users[username]['points'] += 1
        self.save_user_data(users)

        # Display green flash with username
        self.display_status('point', username)

    def start_browser(self):
        """Start headless Chrome browser"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

            self.driver = webdriver.Chrome(options=chrome_options)

            # Navigate to Restream chat
            self.driver.get(RESTREAM_CHAT_URL)

            # Wait for chat to load
            time.sleep(3)

            self.connected = True
            return True

        except:
            return False

    def poll_messages(self):
        """Poll for new chat messages"""
        while self.connected:
            try:
                # Look for message containers
                message_containers = []
                for class_name in ["message-info-container", "chat-message", "message-wrapper"]:
                    containers = self.driver.find_elements(By.CLASS_NAME, class_name)
                    if containers:
                        message_containers.extend(containers)

                if not message_containers:
                    time.sleep(POLL_INTERVAL)
                    continue

                # Get the last message
                latest_msg = message_containers[-1]

                try:
                    # Extract username
                    username = None
                    for class_name in ["message-sender", "chat-author", "username"]:
                        try:
                            username_elem = latest_msg.find_element(By.CLASS_NAME, class_name)
                            if username_elem:
                                username = username_elem.text.strip()
                                break
                        except:
                            continue

                    if not username:
                        continue

                    # Extract message text
                    text = None
                    for class_name in ["chat-text-normal", "message-text", "chat-message-text"]:
                        try:
                            text_elem = latest_msg.find_element(By.CLASS_NAME, class_name)
                            if text_elem:
                                text = text_elem.text.strip()
                                break
                        except:
                            continue

                    if not text:
                        continue

                    # Create unique message identifier
                    current_content = f"{username}:{text}"

                    # Only process if this is a new message
                    if current_content != self.last_message_content and username:
                        # Skip system messages
                        if username == "Restream.io" or not text:
                            continue

                        # Process message
                        self.process_message(username, text)

                        # Update last message
                        self.last_message_content = current_content

                except Exception as e:
                    # Silently skip errors
                    pass

                time.sleep(POLL_INTERVAL)

            except Exception as e:
                # Silently skip errors
                time.sleep(POLL_INTERVAL)

    def run(self):
        """Run the giveaway agent"""
        # Start browser
        if not self.start_browser():
            return

        # Display initial prompt
        self.display_status('prompt')

        # Start polling in background thread
        poll_thread = threading.Thread(target=self.poll_messages, daemon=True)
        poll_thread.start()

        # Keep main thread alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.connected = False
            if self.driver:
                self.driver.quit()

    def __del__(self):
        """Clean up resources"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass


def main():
    """Main entry point"""
    agent = GiveawayAgent()
    agent.run()


if __name__ == "__main__":
    main()
