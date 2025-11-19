"""
🐦 Moon Dev's Tweet Generator
Built with love by Moon Dev 🚀

This agent takes text input and generates tweets based on the content.
"""

import os
import pandas as pd
import time
from datetime import datetime
from pathlib import Path

# 🌙 Moon Dev: Calculate project root dynamically (MUST be before OG_TWEET_FILE)
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "src" / "data"

# Model override settings
# Set to "0" to use config.py's AI_MODEL setting
# Available models:
# - "deepseek-chat" (DeepSeek's V3 model - fast & efficient)
# - "deepseek-reasoner" (DeepSeek's R1 reasoning model)
# - "0" (Use config.py's AI_MODEL setting)
MODEL_OVERRIDE = "deepseek-chat"  # Set to "0" to disable override
DEEPSEEK_BASE_URL = "https://api.deepseek.com"  # Base URL for DeepSeek API

# Text Processing Settings
MAX_CHUNK_SIZE = 10000  # Maximum characters per chunk
TWEETS_PER_CHUNK = 3   # Number of tweets to generate per chunk
USE_TEXT_FILE = True   # Whether to use og_tweet_text.txt by default
# if the above is true, then the below is the file to use
OG_TWEET_FILE = DATA_DIR / "tweets" / "og_tweet_text.txt"  # 🌙 Moon Dev: Dynamic path!
from dotenv import load_dotenv
import openai
import anthropic
import traceback
import math
from termcolor import colored, cprint
import sys

# AI Settings - Override config.py if set
from src import config

# Only set these if you want to override config.py settings
AI_MODEL = False  # Set to model name to override config.AI_MODEL
AI_TEMPERATURE = 0  # Set > 0 to override config.AI_TEMPERATURE
AI_MAX_TOKENS = 150  # Set > 0 to override config.AI_MAX_TOKENS

# Tweet Generation Prompt
TWEET_PROMPT = """Here is a chunk of transcript or text. Please generate three tweets for that text.
Use the below manifest to understand how to speak in the tweet.
Don't use emojis or any corny stuff!
Don't number the tweets - just separate them with blank lines.

Text to analyze:
{text}

Manifest:
- Keep it casual and concise
- Focus on key insights and facts
- no emojis
- always be kind
- No hashtags unless absolutely necessary
- Maximum 280 characters per tweet
- no capitalization
- don't number the tweets
- separate tweets with blank lines

EACH TWEET MUST BE A COMPLETE TAKE AND BE INTERESTING
"""

# Color settings for terminal output
TWEET_COLORS = [
    {'text': 'white', 'bg': 'on_green'},
    {'text': 'white', 'bg': 'on_blue'},
    {'text': 'white', 'bg': 'on_red'}
]

class TweetAgent:
    """Moon Dev's Tweet Generator 🐦"""
    
    def __init__(self):
        """Initialize the Tweet Agent"""
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
            else:
                self.deepseek_client = None
                print("⚠️ DEEPSEEK_KEY not found - DeepSeek model will not be available")
        else:
            self.deepseek_client = None
        
        # Create tweets directory if it doesn't exist - 🌙 Moon Dev: Dynamic path!
        self.tweets_dir = DATA_DIR / "tweets"
        self.tweets_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate output filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_file = self.tweets_dir / f"generated_tweets_{timestamp}.txt"
        
    def _chunk_text(self, text):
        """Split text into chunks of MAX_CHUNK_SIZE characters"""
        return [text[i:i + MAX_CHUNK_SIZE] 
                for i in range(0, len(text), MAX_CHUNK_SIZE)]
    
    def _get_input_text(self, text=None):
        """Get input text from either file or direct input"""
        if USE_TEXT_FILE:
            try:
                with open(OG_TWEET_FILE, 'r') as f:
                    return f.read()
            except Exception as e:
                print(f"❌ Error reading text file: {str(e)}")
                print("⚠️ Falling back to direct text input if provided")
                
        return text
    
    def _print_colored_tweet(self, tweet, color_idx):
        """Print tweet with color based on its position"""
        color_settings = TWEET_COLORS[color_idx % len(TWEET_COLORS)]
        cprint(tweet, color_settings['text'], color_settings['bg'])
        print()  # Add spacing between tweets
    
    def generate_tweets(self, text=None):
        """Generate tweets from text input or file"""
        try:
            # Get input text
            input_text = self._get_input_text(text)
            
            if not input_text:
                print("❌ No input text provided and couldn't read from file")
                return None
            
            # Calculate and display text stats
            total_chars = len(input_text)
            total_chunks = math.ceil(total_chars / MAX_CHUNK_SIZE)
            total_tweets = total_chunks * TWEETS_PER_CHUNK
            
            print(f"\n📊 Text Analysis:")
            print(f"Total characters: {total_chars:,}")
            print(f"Chunk size: {MAX_CHUNK_SIZE:,}")
            print(f"Number of chunks: {total_chunks:,}")
            print(f"Tweets per chunk: {TWEETS_PER_CHUNK}")
            print(f"Total tweets to generate: {total_tweets:,}")
            print("=" * 50)
            
            # Split text into chunks if needed
            chunks = self._chunk_text(input_text)
            all_tweets = []
            
            for i, chunk in enumerate(chunks, 1):
                print(f"\n🔄 Processing chunk {i}/{total_chunks} ({len(chunk):,} characters)")
                
                # Prepare the context
                context = TWEET_PROMPT.format(text=chunk)
                
                # Use either DeepSeek or Claude based on model setting
                if "deepseek" in self.ai_model.lower():
                    if not self.deepseek_client:
                        raise ValueError("🚨 DeepSeek client not initialized - check DEEPSEEK_KEY")
                        
                    # Make DeepSeek API call
                    response = self.deepseek_client.chat.completions.create(
                        model=self.ai_model,
                        messages=[
                            {"role": "system", "content": TWEET_PROMPT},
                            {"role": "user", "content": context}
                        ],
                        max_tokens=self.ai_max_tokens,
                        temperature=self.ai_temperature,
                        stream=False
                    )
                    response_text = response.choices[0].message.content.strip()
                else:
                    # Get tweets using Claude
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
                
                # Parse tweets from response and remove any numbering
                chunk_tweets = []
                for line in response_text.split('\n'):
                    line = line.strip()
                    if line:
                        # Remove any leading numbers (1., 2., etc.)
                        cleaned_line = line.lstrip('0123456789. ')
                        if cleaned_line:
                            chunk_tweets.append(cleaned_line)
                
                # Print tweets with colors to terminal
                print("\n🐦 Generated tweets for this chunk:")
                for idx, tweet in enumerate(chunk_tweets):
                    self._print_colored_tweet(tweet, idx)
                
                all_tweets.extend(chunk_tweets)
                
                # Write tweets to file with paragraph spacing (clean format)
                with open(self.output_file, 'a') as f:
                    for tweet in chunk_tweets:
                        f.write(f"{tweet}\n\n")  # Double newline for paragraph spacing
                
                # Small delay between chunks to avoid rate limits
                if i < total_chunks:
                    time.sleep(1)
            
            return all_tweets
            
        except Exception as e:
            print(f"❌ Error generating tweets: {str(e)}")
            traceback.print_exc()
            return None

if __name__ == "__main__":
    agent = TweetAgent()
    
    # Example usage with direct text
    test_text = """Bitcoin showing strong momentum with increasing volume. 
    Price action suggests accumulation phase might be complete. 
    Key resistance at $69,000 with support holding at $65,000."""
    
    # If USE_TEXT_FILE is True, it will use the file instead of test_text
    tweets = agent.generate_tweets(test_text)
    
    if tweets:
        print(f"\nTweets have been saved to: {agent.output_file}")
