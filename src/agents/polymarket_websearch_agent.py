"""
🌙 Moon Dev's Polymarket Web Search Agent
Built with love by Moon Dev 🚀

This agent combines Polymarket whale tracking with WEB SEARCH capabilities!
It searches the web for context on each market before sending to the AI swarm.

Features:
- Real-time WebSocket tracking of Polymarket trades
- Web search for each market using OpenAI's gpt-4o-mini-search-preview
- Enriched AI analysis with news context
- Same swarm consensus as polymarket_agent.py

Based on polymarket_agent.py + websearch_agent.py patterns
"""

import os
import sys
import time
import json
import requests
import pandas as pd
import threading
import websocket
from datetime import datetime, timedelta
from pathlib import Path
from termcolor import cprint

# Add project root to path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.models.model_factory import ModelFactory
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ==============================================================================
# CONFIGURATION - Moon Dev's Web Search Polymarket Agent
# ==============================================================================

# Trade filtering (same as polymarket_agent)
MIN_TRADE_SIZE_USD = 500  # Only track trades over this amount
IGNORE_PRICE_THRESHOLD = 0.02  # Ignore trades within X cents of resolution ($0 or $1)
LOOKBACK_HOURS = 24  # How many hours back to fetch historical trades on startup

# 🌙 Moon Dev - Market category filters (case-insensitive)
IGNORE_CRYPTO_KEYWORDS = [
    'bitcoin', 'btc', 'ethereum', 'eth', 'crypto', 'solana', 'sol',
    'dogecoin', 'doge', 'shiba', 'cardano', 'ada', 'ripple', 'xrp',
]

IGNORE_SPORTS_KEYWORDS = [
    'nba', 'nfl', 'mlb', 'nhl', 'mls', 'ufc', 'boxing',
    'football', 'basketball', 'baseball', 'hockey', 'soccer',
    'super bowl', 'world series', 'playoffs', 'championship',
    'lakers', 'warriors', 'celtics', 'knicks', 'heat', 'bucks',
    'cowboys', 'patriots', 'chiefs', 'eagles', 'packers',
    'yankees', 'dodgers', 'red sox', 'mets',
    'premier league', 'la liga', 'champions league',
    'tennis', 'golf', 'nascar', 'formula 1', 'f1',
    'cricket',
]

# Agent behavior - REAL-TIME WebSocket + Analysis
ANALYSIS_CHECK_INTERVAL_SECONDS = 300  # How often to check for new markets to analyze (5 minutes)
NEW_MARKETS_FOR_ANALYSIS = 3  # Trigger analysis when we have 3 NEW unanalyzed markets
MARKETS_TO_ANALYZE = 3  # Number of recent markets to send to AI
MARKETS_TO_DISPLAY = 20  # Number of recent markets to print after each update
REANALYSIS_HOURS = 8  # Re-analyze markets after this many hours (even if previously analyzed)

# AI Configuration
USE_SWARM_MODE = True  # Use swarm AI (multiple models) instead of single XAI model
AI_MODEL_PROVIDER = "xai"  # Model to use if USE_SWARM_MODE = False
AI_MODEL_NAME = "grok-2-fast-reasoning"  # Model name if not using swarm
SEND_PRICE_INFO_TO_AI = False  # Send market price/odds to AI models

# 🌙 Moon Dev - WEB SEARCH Configuration (NEW!)
WEB_SEARCH_MODEL = "gpt-4o-mini-search-preview"  # OpenAI search model with built-in web search
WEB_SEARCH_TIMEOUT = 60  # Seconds timeout for web search
OPENAI_API_KEY = os.getenv("OPENAI_KEY")

# 🌙 Moon Dev - AI Prompts
MARKET_ANALYSIS_SYSTEM_PROMPT = """You are a prediction market expert analyzing Polymarket markets.
You have been provided with RECENT NEWS AND CONTEXT for each market from web search.
Use this context to make more informed predictions.

For each market, provide your prediction in this exact format:

MARKET [number]: [decision]
Reasoning: [brief 1-2 sentence explanation that references the news context if relevant]

Decision must be one of: YES, NO, or NO_TRADE
- YES means you would bet on the "Yes" outcome
- NO means you would bet on the "No" outcome
- NO_TRADE means you would not take a position

Be concise and focused on the most promising opportunities."""

# Consensus AI prompt for identifying top markets
TOP_MARKETS_COUNT = 5  # How many top markets to identify
CONSENSUS_AI_PROMPT_TEMPLATE = """You are analyzing predictions from multiple AI models on Polymarket markets.

MARKET REFERENCE:
{market_reference}

ALL AI RESPONSES:
{all_responses}

Based on ALL of these AI responses, identify the TOP {top_count} MARKETS that have the STRONGEST CONSENSUS across all models.

Rules:
- Look for markets where most AIs agree on the same side (YES, NO, or NO_TRADE)
- Ignore markets with split opinions
- Focus on clear, strong agreement
- DO NOT use any reasoning or thinking - just analyze the responses
- Provide exactly {top_count} markets ranked by consensus strength

Format your response EXACTLY like this:

TOP {top_count} CONSENSUS PICKS:

1. Market [number]: [market title]
   Side: [YES/NO/NO_TRADE]
   Consensus: [X out of Y models agreed]
   Link: [polymarket URL from market reference]
   Reasoning: [1 sentence why this is a strong pick]

2. Market [number]: [market title]
   Side: [YES/NO/NO_TRADE]
   Consensus: [X out of Y models agreed]
   Link: [polymarket URL from market reference]
   Reasoning: [1 sentence why this is a strong pick]

[Continue for all {top_count} markets...]
"""

# Data paths
DATA_FOLDER = os.path.join(project_root, "src/data/polymarket_websearch")
MARKETS_CSV = os.path.join(DATA_FOLDER, "markets.csv")
PREDICTIONS_CSV = os.path.join(DATA_FOLDER, "predictions.csv")
CONSENSUS_PICKS_CSV = os.path.join(DATA_FOLDER, "consensus_picks.csv")
WEB_SEARCH_LOG_CSV = os.path.join(DATA_FOLDER, "web_search_log.csv")  # 🌙 NEW: Log web searches

# Polymarket API & WebSocket
POLYMARKET_API_BASE = "https://data-api.polymarket.com"
WEBSOCKET_URL = "wss://ws-live-data.polymarket.com"

# ==============================================================================
# Polymarket Web Search Agent
# ==============================================================================

class PolymarketWebSearchAgent:
    """Agent that tracks Polymarket markets with WEB SEARCH enriched AI predictions"""

    def __init__(self):
        """Initialize the Polymarket Web Search agent"""
        cprint("\n" + "="*80, "cyan")
        cprint("🌙 Moon Dev's Polymarket WEB SEARCH Agent - Initializing", "cyan", attrs=['bold'])
        cprint("🔍 This agent searches the web for context before AI analysis!", "yellow")
        cprint("="*80, "cyan")

        # Create data folder if it doesn't exist
        os.makedirs(DATA_FOLDER, exist_ok=True)

        # Thread-safe lock for CSV access
        self.csv_lock = threading.Lock()

        # Track which markets have been analyzed
        self.last_analyzed_count = 0
        self.last_analysis_run_timestamp = None

        # WebSocket connection
        self.ws = None
        self.ws_connected = False
        self.total_trades_received = 0
        self.filtered_trades_count = 0
        self.ignored_crypto_count = 0
        self.ignored_sports_count = 0

        # 🌙 Moon Dev - Check OpenAI API key for web search
        if not OPENAI_API_KEY:
            cprint("⚠️ WARNING: OPENAI_KEY not found - web search will fail!", "red", attrs=['bold'])
        else:
            cprint(f"✅ OpenAI API key configured for web search", "green")
            cprint(f"🔍 Web search model: {WEB_SEARCH_MODEL}", "cyan")

        # Initialize AI models
        if USE_SWARM_MODE:
            cprint("🤖 Using SWARM MODE - Multiple AI models", "green")
            try:
                from src.agents.swarm_agent import SwarmAgent
                self.swarm = SwarmAgent()
                cprint("✅ Swarm agent loaded successfully", "green")
            except Exception as e:
                cprint(f"❌ Failed to load swarm agent: {e}", "red")
                cprint("💡 Falling back to single model mode", "yellow")
                self.swarm = None
                self.model = ModelFactory().get_model(AI_MODEL_PROVIDER, AI_MODEL_NAME)
        else:
            cprint(f"🤖 Using single model: {AI_MODEL_PROVIDER}/{AI_MODEL_NAME}", "green")
            self.model = ModelFactory().get_model(AI_MODEL_PROVIDER, AI_MODEL_NAME)
            self.swarm = None

        # Initialize markets DataFrame
        self.markets_df = self._load_markets()

        # Initialize predictions DataFrame
        self.predictions_df = self._load_predictions()

        # Initialize web search log
        self._init_web_search_log()

        cprint(f"📊 Loaded {len(self.markets_df)} existing markets from CSV", "cyan")
        cprint(f"🔮 Loaded {len(self.predictions_df)} existing predictions from CSV", "cyan")
        cprint("✨ Initialization complete!\n", "green")

    def _init_web_search_log(self):
        """Initialize the web search log CSV"""
        if not os.path.exists(WEB_SEARCH_LOG_CSV):
            df = pd.DataFrame(columns=[
                'timestamp', 'market_title', 'search_query', 'response_length', 'response_preview'
            ])
            df.to_csv(WEB_SEARCH_LOG_CSV, index=False)
            cprint(f"📝 Created web search log: {WEB_SEARCH_LOG_CSV}", "cyan")

    def _load_markets(self):
        """Load existing markets from CSV or create empty DataFrame"""
        if os.path.exists(MARKETS_CSV):
            try:
                df = pd.read_csv(MARKETS_CSV)
                cprint(f"✅ Loaded existing markets from {MARKETS_CSV}", "green")
                return df
            except Exception as e:
                cprint(f"⚠️ Error loading CSV: {e}", "yellow")

        return pd.DataFrame(columns=[
            'timestamp', 'market_id', 'event_slug', 'title',
            'outcome', 'price', 'size_usd', 'first_seen', 'last_analyzed', 'last_trade_timestamp'
        ])

    def _load_predictions(self):
        """Load existing predictions from CSV or create empty DataFrame"""
        if os.path.exists(PREDICTIONS_CSV):
            try:
                df = pd.read_csv(PREDICTIONS_CSV)
                cprint(f"✅ Loaded existing predictions from {PREDICTIONS_CSV}", "green")
                return df
            except Exception as e:
                cprint(f"⚠️ Error loading predictions CSV: {e}", "yellow")

        return pd.DataFrame(columns=[
            'analysis_timestamp', 'analysis_run_id', 'market_title', 'market_slug',
            'claude_prediction', 'opus_prediction', 'openai_prediction', 'groq_prediction',
            'gemini_prediction', 'deepseek_prediction', 'xai_prediction',
            'ollama_prediction', 'consensus_prediction', 'num_models_responded',
            'web_search_used', 'market_link'
        ])

    def _save_markets(self):
        """Save markets DataFrame to CSV (thread-safe, silent)"""
        try:
            with self.csv_lock:
                self.markets_df.to_csv(MARKETS_CSV, index=False)
        except Exception as e:
            cprint(f"❌ Error saving CSV: {e}", "red")

    def _save_predictions(self):
        """Save predictions DataFrame to CSV (thread-safe)"""
        try:
            with self.csv_lock:
                self.predictions_df.to_csv(PREDICTIONS_CSV, index=False)
            cprint(f"💾 Saved {len(self.predictions_df)} predictions to CSV", "green")
        except Exception as e:
            cprint(f"❌ Error saving predictions CSV: {e}", "red")

    # ==========================================================================
    # 🌙 Moon Dev - WEB SEARCH FUNCTIONALITY (NEW!)
    # ==========================================================================

    def search_market_context(self, market_title: str) -> str:
        """
        🌙 Moon Dev - Search the web for context about a specific Polymarket market

        Uses OpenAI's gpt-4o-mini-search-preview which has built-in web search.
        Returns the web search results as a string.

        Args:
            market_title: The title of the market to search for

        Returns:
            str: Web search results/context for the market
        """
        cprint(f"\n{'='*60}", "yellow")
        cprint(f"🔍 WEB SEARCH: {market_title[:50]}...", "yellow", attrs=['bold'])
        cprint(f"{'='*60}", "yellow")

        if not OPENAI_API_KEY:
            cprint("❌ No OpenAI API key - skipping web search", "red")
            return "No web search context available (API key missing)"

        try:
            # Build the search request
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            }

            # Use market title directly as the search query
            user_message = f"""Search for the latest news and information about: {market_title}

Find recent news, updates, and relevant context that would help predict the outcome of this prediction market.
Focus on:
- Recent news articles
- Official announcements
- Expert opinions
- Relevant statistics or data

Provide a concise summary of the most relevant and recent information."""

            payload = {
                "model": WEB_SEARCH_MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": user_message
                    }
                ]
            }

            cprint(f"📡 Sending to OpenAI {WEB_SEARCH_MODEL}...", "cyan")
            cprint(f"🔎 Search query: {market_title}", "white")

            # Make the API request
            response = requests.post(url, headers=headers, json=payload, timeout=WEB_SEARCH_TIMEOUT)

            cprint(f"📥 Response status: {response.status_code} ({response.elapsed.total_seconds():.2f}s)",
                   "green" if response.status_code == 200 else "red")

            if response.status_code != 200:
                cprint(f"❌ API Error: {response.text[:200]}", "red")
                return f"Web search failed (status {response.status_code})"

            # Parse the response
            response_json = response.json()
            content = ""

            if 'choices' in response_json and len(response_json['choices']) > 0:
                message = response_json['choices'][0].get('message', {})
                content = message.get('content', '')

            if content:
                # 🌙 Moon Dev - SHOW THE WEB SEARCH RESULTS
                cprint(f"\n{'─'*60}", "green")
                cprint("📰 WEB SEARCH RESULTS:", "green", attrs=['bold'])
                cprint(f"{'─'*60}", "green")
                # Show first 500 chars in console
                preview = content[:500] + "..." if len(content) > 500 else content
                cprint(preview, "white")
                cprint(f"{'─'*60}", "green")
                cprint(f"📏 Total length: {len(content)} characters", "cyan")

                # Log to CSV
                self._log_web_search(market_title, market_title, content)

                return content
            else:
                cprint("⚠️ Empty response from web search", "yellow")
                return "No web search results found"

        except requests.exceptions.Timeout:
            cprint(f"⏰ Web search timed out after {WEB_SEARCH_TIMEOUT}s", "red")
            return "Web search timed out"
        except Exception as e:
            cprint(f"❌ Web search error: {e}", "red")
            return f"Web search error: {str(e)}"

    def _log_web_search(self, market_title: str, search_query: str, response: str):
        """Log web search to CSV for analysis"""
        try:
            with self.csv_lock:
                df = pd.read_csv(WEB_SEARCH_LOG_CSV) if os.path.exists(WEB_SEARCH_LOG_CSV) else pd.DataFrame()
                new_row = pd.DataFrame([{
                    'timestamp': datetime.now().isoformat(),
                    'market_title': market_title,
                    'search_query': search_query,
                    'response_length': len(response),
                    'response_preview': response[:200]
                }])
                df = pd.concat([df, new_row], ignore_index=True)
                df.to_csv(WEB_SEARCH_LOG_CSV, index=False)
        except Exception as e:
            cprint(f"⚠️ Error logging web search: {e}", "yellow")

    # ==========================================================================
    # Market filtering (same as polymarket_agent)
    # ==========================================================================

    def is_near_resolution(self, price):
        """Check if price is within threshold of $0 or $1 (near resolution)"""
        price_float = float(price)
        return price_float <= IGNORE_PRICE_THRESHOLD or price_float >= (1.0 - IGNORE_PRICE_THRESHOLD)

    def should_ignore_market(self, title):
        """Check if market should be ignored based on category keywords"""
        title_lower = title.lower()

        for keyword in IGNORE_CRYPTO_KEYWORDS:
            if keyword in title_lower:
                return (True, f"crypto/bitcoin ({keyword})")

        for keyword in IGNORE_SPORTS_KEYWORDS:
            if keyword in title_lower:
                return (True, f"sports ({keyword})")

        return (False, None)

    # ==========================================================================
    # WebSocket handlers (same as polymarket_agent)
    # ==========================================================================

    def on_ws_message(self, ws, message):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(message)

            if isinstance(data, dict):
                if data.get('type') == 'subscribed':
                    cprint("✅ Moon Dev WebSocket subscribed to live trades!", "green")
                    self.ws_connected = True
                    return

                if data.get('type') == 'pong':
                    return

                topic = data.get('topic')
                msg_type = data.get('type')
                payload = data.get('payload', {})

                if topic == 'activity' and msg_type == 'orders_matched':
                    self.total_trades_received += 1

                    if not self.ws_connected:
                        self.ws_connected = True

                    price = float(payload.get('price', 0))
                    size = float(payload.get('size', 0))
                    usd_amount = price * size
                    title = payload.get('title', 'Unknown')

                    should_ignore, ignore_reason = self.should_ignore_market(title)
                    if should_ignore:
                        if 'crypto' in ignore_reason or 'bitcoin' in ignore_reason:
                            self.ignored_crypto_count += 1
                        elif 'sports' in ignore_reason:
                            self.ignored_sports_count += 1
                        return

                    if usd_amount >= MIN_TRADE_SIZE_USD and not self.is_near_resolution(price):
                        self.filtered_trades_count += 1

                        trade_data = {
                            'timestamp': payload.get('timestamp', time.time()),
                            'conditionId': payload.get('conditionId', payload.get('id', f"ws_{time.time()}")),
                            'eventSlug': payload.get('eventSlug', '') or payload.get('slug', ''),
                            'title': title,
                            'outcome': payload.get('outcome', 'Unknown'),
                            'price': price,
                            'size': usd_amount,
                            'side': payload.get('side', ''),
                            'trader': payload.get('name', payload.get('pseudonym', 'Unknown'))
                        }

                        self.process_trades([trade_data])

        except json.JSONDecodeError:
            pass
        except Exception as e:
            cprint(f"⚠️ Error processing WebSocket message: {e}", "yellow")

    def on_ws_error(self, ws, error):
        """Handle WebSocket errors"""
        cprint(f"❌ WebSocket Error: {error}", "red")

    def on_ws_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket close"""
        self.ws_connected = False
        cprint(f"\n🔌 WebSocket connection closed: {close_status_code} - {close_msg}", "yellow")
        cprint("Reconnecting in 5 seconds...", "cyan")
        time.sleep(5)
        self.connect_websocket()

    def on_ws_open(self, ws):
        """Handle WebSocket open - send subscription"""
        cprint("🔌 WebSocket connected!", "green")

        subscription_msg = {
            "action": "subscribe",
            "subscriptions": [
                {
                    "topic": "activity",
                    "type": "orders_matched"
                }
            ]
        }

        cprint(f"📡 Sending subscription for live trades...", "cyan")
        ws.send(json.dumps(subscription_msg))
        self.ws_connected = True
        cprint("✅ Subscription sent! Waiting for trades...", "green")

        def send_ping():
            while True:
                time.sleep(5)
                try:
                    ws.send(json.dumps({"type": "ping"}))
                except:
                    break

        ping_thread = threading.Thread(target=send_ping, daemon=True)
        ping_thread.start()

    def connect_websocket(self):
        """Connect to Polymarket WebSocket"""
        cprint(f"🚀 Connecting to {WEBSOCKET_URL}...", "cyan")

        self.ws = websocket.WebSocketApp(
            WEBSOCKET_URL,
            on_open=self.on_ws_open,
            on_message=self.on_ws_message,
            on_error=self.on_ws_error,
            on_close=self.on_ws_close
        )

        ws_thread = threading.Thread(target=self.ws.run_forever, daemon=True)
        ws_thread.start()
        cprint("✅ WebSocket thread started!", "green")

    def fetch_historical_trades(self, hours_back=None):
        """Fetch historical trades from Polymarket API on startup"""
        if hours_back is None:
            hours_back = LOOKBACK_HOURS

        try:
            cprint(f"\n📡 Fetching historical trades (last {hours_back}h)...", "yellow")

            cutoff_time = datetime.now() - timedelta(hours=hours_back)
            cutoff_timestamp = int(cutoff_time.timestamp())

            url = f"{POLYMARKET_API_BASE}/trades"
            params = {
                'limit': 1000,
                '_min_timestamp': cutoff_timestamp
            }

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            trades = response.json()
            cprint(f"✅ Fetched {len(trades)} total historical trades", "green")

            filtered_trades = []
            for trade in trades:
                price = float(trade.get('price', 0))
                size = float(trade.get('size', 0))
                usd_amount = price * size
                title = trade.get('title', 'Unknown')

                should_ignore, _ = self.should_ignore_market(title)
                if should_ignore:
                    continue

                if usd_amount >= MIN_TRADE_SIZE_USD and not self.is_near_resolution(price):
                    filtered_trades.append(trade)

            cprint(f"💰 Found {len(filtered_trades)} trades over ${MIN_TRADE_SIZE_USD}", "cyan")
            return filtered_trades

        except Exception as e:
            cprint(f"❌ Error fetching historical trades: {e}", "red")
            return []

    def process_trades(self, trades):
        """Process trades and add new markets to DataFrame"""
        if not trades:
            return

        unique_markets = {}
        for trade in trades:
            market_id = trade.get('conditionId', '')
            if market_id and market_id not in unique_markets:
                unique_markets[market_id] = trade

        new_markets = 0
        updated_markets = 0

        for market_id, trade in unique_markets.items():
            try:
                event_slug = trade.get('eventSlug', '')
                title = trade.get('title', 'Unknown Market')
                outcome = trade.get('outcome', '')
                price = float(trade.get('price', 0))
                size_usd = float(trade.get('size', 0))
                timestamp = trade.get('timestamp', '')
                condition_id = trade.get('conditionId', '')

                if market_id in self.markets_df['market_id'].values:
                    mask = self.markets_df['market_id'] == market_id
                    self.markets_df.loc[mask, 'timestamp'] = timestamp
                    self.markets_df.loc[mask, 'outcome'] = outcome
                    self.markets_df.loc[mask, 'price'] = price
                    self.markets_df.loc[mask, 'size_usd'] = size_usd
                    self.markets_df.loc[mask, 'last_trade_timestamp'] = datetime.now().isoformat()
                    updated_markets += 1
                    continue

                new_market = {
                    'timestamp': timestamp,
                    'market_id': condition_id,
                    'event_slug': event_slug,
                    'title': title,
                    'outcome': outcome,
                    'price': price,
                    'size_usd': size_usd,
                    'first_seen': datetime.now().isoformat(),
                    'last_analyzed': None,
                    'last_trade_timestamp': datetime.now().isoformat()
                }

                self.markets_df = pd.concat([
                    self.markets_df,
                    pd.DataFrame([new_market])
                ], ignore_index=True)

                new_markets += 1
                cprint(f"✨ NEW: ${size_usd:,.0f} - {title[:70]}", "green")

            except Exception as e:
                cprint(f"⚠️ Error processing trade: {e}", "yellow")
                continue

        if new_markets > 0 or updated_markets > 0:
            self._save_markets()

    def display_recent_markets(self):
        """Display the most recent markets from CSV"""
        if len(self.markets_df) == 0:
            cprint("\n📊 No markets in database yet", "yellow")
            return

        cprint("\n" + "="*80, "cyan")
        cprint(f"📊 Most Recent {min(MARKETS_TO_DISPLAY, len(self.markets_df))} Markets", "cyan", attrs=['bold'])
        cprint("="*80, "cyan")

        recent = self.markets_df.tail(MARKETS_TO_DISPLAY)

        for idx, row in recent.iterrows():
            title = row['title'][:60] + "..." if len(row['title']) > 60 else row['title']
            size = row['size_usd']
            outcome = row['outcome']

            cprint(f"\n💵 ${size:,.2f} trade on {outcome}", "yellow")
            cprint(f"📌 {title}", "white")
            cprint(f"🔗 https://polymarket.com/event/{row['event_slug']}", "cyan")

        cprint("\n" + "="*80, "cyan")
        cprint(f"Total markets tracked: {len(self.markets_df)}", "green", attrs=['bold'])
        cprint("="*80 + "\n", "cyan")

    # ==========================================================================
    # 🌙 Moon Dev - AI PREDICTIONS WITH WEB SEARCH (MODIFIED!)
    # ==========================================================================

    def get_ai_predictions(self):
        """Get AI predictions for recent markets WITH WEB SEARCH CONTEXT"""
        if len(self.markets_df) == 0:
            cprint("\n⚠️ No markets to analyze yet", "yellow")
            return

        markets_to_analyze = self.markets_df.tail(MARKETS_TO_ANALYZE)

        analysis_run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        analysis_timestamp = datetime.now().isoformat()

        cprint("\n" + "="*80, "magenta")
        cprint(f"🤖 AI Analysis WITH WEB SEARCH - Analyzing {len(markets_to_analyze)} markets", "magenta", attrs=['bold'])
        cprint(f"📊 Analysis Run ID: {analysis_run_id}", "magenta")
        cprint("🔍 Web search ENABLED for each market!", "yellow", attrs=['bold'])
        cprint("="*80, "magenta")

        # ==========================================================================
        # 🌙 Moon Dev - SEARCH WEB FOR EACH MARKET BEFORE AI ANALYSIS
        # ==========================================================================
        cprint("\n" + "="*80, "yellow")
        cprint("🔍 PHASE 1: WEB SEARCH FOR MARKET CONTEXT", "yellow", attrs=['bold'])
        cprint("="*80, "yellow")

        web_contexts = {}
        for i, (_, row) in enumerate(markets_to_analyze.iterrows()):
            market_title = row['title']
            cprint(f"\n🔎 Searching web for market {i+1}/{len(markets_to_analyze)}...", "cyan")

            # Search the web for this market
            web_context = self.search_market_context(market_title)
            web_contexts[market_title] = web_context

            # Small delay between searches to be nice to API
            if i < len(markets_to_analyze) - 1:
                time.sleep(2)

        # ==========================================================================
        # 🌙 Moon Dev - BUILD ENRICHED PROMPT WITH WEB CONTEXT
        # ==========================================================================
        cprint("\n" + "="*80, "green")
        cprint("📝 PHASE 2: BUILDING ENRICHED PROMPT WITH WEB CONTEXT", "green", attrs=['bold'])
        cprint("="*80, "green")

        markets_text = ""
        for i, (_, row) in enumerate(markets_to_analyze.iterrows()):
            market_title = row['title']
            web_context = web_contexts.get(market_title, "No web context available")

            # Truncate web context if too long
            if len(web_context) > 1000:
                web_context = web_context[:1000] + "..."

            if SEND_PRICE_INFO_TO_AI:
                markets_text += f"""
Market {i+1}:
Title: {row['title']}
Current Price: ${row['price']:.2f} ({row['price']*100:.1f}% odds for {row['outcome']})
Recent trade: ${row['size_usd']:,.2f} on {row['outcome']}
Link: https://polymarket.com/event/{row['event_slug']}

📰 RECENT NEWS/CONTEXT FROM WEB SEARCH:
{web_context}

---
"""
            else:
                markets_text += f"""
Market {i+1}:
Title: {row['title']}
Recent trade: ${row['size_usd']:,.2f} on {row['outcome']}
Link: https://polymarket.com/event/{row['event_slug']}

📰 RECENT NEWS/CONTEXT FROM WEB SEARCH:
{web_context}

---
"""

        # Show the enriched prompt
        cprint("\n" + "─"*60, "cyan")
        cprint("📤 ENRICHED PROMPT BEING SENT TO AI:", "cyan", attrs=['bold'])
        cprint("─"*60, "cyan")
        # Show first 2000 chars
        preview = markets_text[:2000] + "..." if len(markets_text) > 2000 else markets_text
        cprint(preview, "white")
        cprint("─"*60, "cyan")
        cprint(f"📏 Total prompt length: {len(markets_text)} characters", "cyan")

        system_prompt = MARKET_ANALYSIS_SYSTEM_PROMPT

        user_prompt = f"""Analyze these {len(markets_to_analyze)} Polymarket markets and provide your predictions.
You have been given RECENT NEWS AND CONTEXT from web search for each market.
Use this information to make more informed predictions.

{markets_text}

Provide predictions for each market in the specified format."""

        # ==========================================================================
        # Send to AI Swarm (same as polymarket_agent)
        # ==========================================================================
        if USE_SWARM_MODE and self.swarm:
            cprint("\n" + "="*80, "blue")
            cprint("🌊 PHASE 3: SENDING TO AI SWARM", "blue", attrs=['bold'])
            cprint("="*80, "blue")

            cprint("\n🌊 Getting predictions from AI swarm (120s timeout per model)...\n", "cyan")

            swarm_result = self.swarm.query(
                prompt=user_prompt,
                system_prompt=system_prompt
            )

            if not swarm_result or not swarm_result.get('responses'):
                cprint("❌ No responses from swarm - all models failed", "red")
                return

            successful_responses = [
                name for name, data in swarm_result.get('responses', {}).items()
                if data.get('success')
            ]

            if not successful_responses:
                cprint("❌ All AI models failed - no predictions available", "red")
                return

            cprint(f"\n✅ Received {len(successful_responses)}/{len(swarm_result['responses'])} successful responses!\n", "green", attrs=['bold'])

            # Display individual AI responses
            cprint("="*80, "yellow")
            cprint("🤖 Individual AI Predictions (WITH WEB CONTEXT)", "yellow", attrs=['bold'])
            cprint("="*80, "yellow")

            for model_name, model_data in swarm_result.get('responses', {}).items():
                if model_data.get('success'):
                    response_time = model_data.get('response_time', 0)
                    cprint(f"\n{'='*80}", "cyan")
                    cprint(f"✅ {model_name.upper()} ({response_time:.1f}s)", "cyan", attrs=['bold'])
                    cprint(f"{'='*80}", "cyan")
                    cprint(model_data.get('response', 'No response'), "white")
                else:
                    error = model_data.get('error', 'Unknown error')
                    cprint(f"\n❌ {model_name.upper()} - FAILED: {error}", "red", attrs=['bold'])

            # Calculate consensus
            consensus_text = self._calculate_polymarket_consensus(swarm_result, markets_to_analyze)

            cprint("\n" + "="*80, "green")
            cprint("🎯 CONSENSUS ANALYSIS (Web Search Enhanced!)", "green", attrs=['bold'])
            cprint(f"Based on {len(successful_responses)} AI models with web context", "green")
            cprint("="*80, "green")
            cprint(consensus_text, "white")
            cprint("="*80 + "\n", "green")

            # Get top consensus picks
            self._get_top_consensus_picks(swarm_result, markets_to_analyze)

            # Save predictions
            try:
                self._save_swarm_predictions(
                    analysis_run_id=analysis_run_id,
                    analysis_timestamp=analysis_timestamp,
                    markets=markets_to_analyze,
                    swarm_result=swarm_result
                )
                cprint(f"\n📁 Predictions saved to: {PREDICTIONS_CSV}", "cyan", attrs=['bold'])
            except Exception as e:
                cprint(f"❌ Error saving predictions: {e}", "red")

            self._mark_markets_analyzed(markets_to_analyze, analysis_timestamp)

        else:
            # Single model mode
            cprint(f"\n🤖 Getting predictions from {AI_MODEL_PROVIDER}/{AI_MODEL_NAME}...\n", "cyan")

            try:
                response = self.model.generate_response(
                    system_prompt=system_prompt,
                    user_content=user_prompt,
                    temperature=0.7
                )

                cprint("="*80, "green")
                cprint("🎯 AI PREDICTION (Web Search Enhanced!)", "green", attrs=['bold'])
                cprint("="*80, "green")
                cprint(response.content, "white")
                cprint("="*80 + "\n", "green")

                self._mark_markets_analyzed(markets_to_analyze, analysis_timestamp)

            except Exception as e:
                cprint(f"❌ Error getting prediction: {e}", "red")

    def _mark_markets_analyzed(self, markets, analysis_timestamp):
        """Mark markets as analyzed with timestamp"""
        try:
            analyzed_market_ids = markets['market_id'].tolist()

            for market_id in analyzed_market_ids:
                mask = self.markets_df['market_id'] == market_id
                self.markets_df.loc[mask, 'last_analyzed'] = analysis_timestamp

            self._save_markets()
            cprint(f"✅ Marked {len(analyzed_market_ids)} markets with analysis timestamp", "green")

        except Exception as e:
            cprint(f"❌ Error marking markets as analyzed: {e}", "red")

    def _save_swarm_predictions(self, analysis_run_id, analysis_timestamp, markets, swarm_result):
        """Save swarm predictions to CSV database"""
        try:
            market_predictions = {}

            for model_name, model_data in swarm_result.get('responses', {}).items():
                if not model_data.get('success'):
                    continue

                response = model_data.get('response', '')
                lines = response.strip().split('\n')

                for line in lines:
                    line_upper = line.upper()

                    if 'MARKET' in line_upper and ':' in line:
                        try:
                            market_part = line_upper.split('MARKET')[1].split(':')[0].strip()
                            market_num = int(''.join(filter(str.isdigit, market_part)))

                            if market_num < 1 or market_num > len(markets):
                                continue

                            if market_num not in market_predictions:
                                market_predictions[market_num] = {}

                            if 'NO_TRADE' in line_upper or 'NO TRADE' in line_upper:
                                market_predictions[market_num][model_name] = 'NO_TRADE'
                            elif 'YES' in line_upper:
                                market_predictions[market_num][model_name] = 'YES'
                            elif 'NO' in line_upper:
                                market_predictions[market_num][model_name] = 'NO'
                        except:
                            continue

            markets_list = list(markets.iterrows())
            new_records = []

            for market_num, predictions in market_predictions.items():
                if 1 <= market_num <= len(markets_list):
                    idx, row = markets_list[market_num - 1]
                    market_title = row['title']
                    market_slug = row['event_slug']
                    market_link = f"https://polymarket.com/event/{market_slug}"

                    votes = {"YES": 0, "NO": 0, "NO_TRADE": 0}
                    for pred in predictions.values():
                        if pred in votes:
                            votes[pred] += 1

                    majority = max(votes, key=votes.get)
                    total = sum(votes.values())
                    confidence = int((votes[majority] / total) * 100) if total > 0 else 0
                    consensus = f"{majority} ({confidence}%)"

                    record = {
                        'analysis_timestamp': analysis_timestamp,
                        'analysis_run_id': analysis_run_id,
                        'market_title': market_title,
                        'market_slug': market_slug,
                        'claude_prediction': predictions.get('claude', 'N/A'),
                        'opus_prediction': predictions.get('opus', 'N/A'),
                        'openai_prediction': predictions.get('openai', 'N/A'),
                        'groq_prediction': predictions.get('groq', 'N/A'),
                        'gemini_prediction': predictions.get('gemini', 'N/A'),
                        'deepseek_prediction': predictions.get('deepseek', 'N/A'),
                        'xai_prediction': predictions.get('xai', 'N/A'),
                        'ollama_prediction': predictions.get('ollama', 'N/A'),
                        'consensus_prediction': consensus,
                        'num_models_responded': len(predictions),
                        'web_search_used': 'YES',  # 🌙 Moon Dev - Mark that web search was used!
                        'market_link': market_link
                    }
                    new_records.append(record)

            if new_records:
                self.predictions_df = pd.concat([
                    self.predictions_df,
                    pd.DataFrame(new_records)
                ], ignore_index=True)
                self._save_predictions()
                cprint(f"✅ Saved {len(new_records)} market predictions with web search context", "green")

        except Exception as e:
            cprint(f"❌ Error saving predictions: {e}", "red")

    def _calculate_polymarket_consensus(self, swarm_result, markets_df):
        """Calculate consensus from individual swarm responses"""
        try:
            market_votes = {}
            model_predictions = {}

            for provider, data in swarm_result["responses"].items():
                if not data["success"]:
                    continue

                response_text = data["response"]
                model_predictions[provider] = response_text

                lines = response_text.strip().split('\n')
                for line in lines:
                    line_upper = line.upper()

                    if 'MARKET' in line_upper and ':' in line:
                        try:
                            market_part = line_upper.split('MARKET')[1].split(':')[0].strip()
                            market_num = int(''.join(filter(str.isdigit, market_part)))

                            if market_num < 1 or market_num > len(markets_df):
                                continue

                            if market_num not in market_votes:
                                market_votes[market_num] = {"YES": 0, "NO": 0, "NO_TRADE": 0}

                            if 'NO_TRADE' in line_upper or 'NO TRADE' in line_upper:
                                market_votes[market_num]["NO_TRADE"] += 1
                            elif 'YES' in line_upper:
                                market_votes[market_num]["YES"] += 1
                            elif 'NO' in line_upper:
                                market_votes[market_num]["NO"] += 1
                        except:
                            continue

            total_models = len(model_predictions)

            if total_models == 0:
                return "No valid model responses to analyze"

            consensus_text = f"Analyzed responses from {total_models} AI models (with web search context)\n\n"

            if market_votes:
                consensus_text += "MARKET CONSENSUS:\n"
                consensus_text += "="*80 + "\n\n"

                markets_list = list(markets_df.iterrows())

                for market_num in sorted(market_votes.keys()):
                    votes = market_votes[market_num]
                    total_votes = sum(votes.values())

                    if total_votes == 0:
                        continue

                    majority = max(votes, key=votes.get)
                    majority_count = votes[majority]
                    confidence = int((majority_count / total_votes) * 100)

                    if 1 <= market_num <= len(markets_list):
                        idx, row = markets_list[market_num - 1]
                        market_title = row['title']
                        market_slug = row['event_slug']
                        market_link = f"https://polymarket.com/event/{market_slug}"

                        display_title = market_title[:70] + "..." if len(market_title) > 70 else market_title

                        consensus_text += f"Market {market_num}: {majority} ({confidence}% consensus)\n"
                        consensus_text += f"  📌 {display_title}\n"
                        consensus_text += f"  🔗 {market_link}\n"
                        consensus_text += f"  Votes: YES: {votes['YES']} | NO: {votes['NO']} | NO_TRADE: {votes['NO_TRADE']}\n\n"

            consensus_text += "\nRESPONDED MODELS:\n"
            consensus_text += "="*60 + "\n"
            for model_name in model_predictions.keys():
                consensus_text += f"  ✅ {model_name}\n"

            failed_models = [
                provider for provider, data in swarm_result["responses"].items()
                if not data["success"]
            ]
            if failed_models:
                consensus_text += "\nFAILED/TIMEOUT MODELS:\n"
                consensus_text += "="*60 + "\n"
                for model_name in failed_models:
                    error = swarm_result["responses"][model_name].get("error", "Unknown")
                    consensus_text += f"  ❌ {model_name}: {error}\n"

            return consensus_text

        except Exception as e:
            cprint(f"❌ Error calculating consensus: {e}", "red")
            return f"Error calculating consensus: {str(e)}"

    def _get_top_consensus_picks(self, swarm_result, markets_df):
        """Use consensus AI to identify top markets with strongest agreement"""
        try:
            cprint("\n" + "="*80, "yellow")
            cprint(f"🧠 Running Consensus AI to identify top {TOP_MARKETS_COUNT} picks...", "yellow", attrs=['bold'])
            cprint("="*80 + "\n", "yellow")

            all_responses_text = ""
            for model_name, model_data in swarm_result.get('responses', {}).items():
                if model_data.get('success'):
                    all_responses_text += f"\n{'='*60}\n"
                    all_responses_text += f"{model_name.upper()} PREDICTIONS:\n"
                    all_responses_text += f"{'='*60}\n"
                    all_responses_text += model_data.get('response', '') + "\n"

            markets_list = list(markets_df.iterrows())
            market_reference = "\n".join([
                f"Market {i+1}: {row['title']}\nLink: https://polymarket.com/event/{row['event_slug']}"
                for i, (_, row) in enumerate(markets_list)
            ])

            consensus_prompt = CONSENSUS_AI_PROMPT_TEMPLATE.format(
                market_reference=market_reference,
                all_responses=all_responses_text,
                top_count=TOP_MARKETS_COUNT
            )

            consensus_model = ModelFactory().get_model('claude', 'claude-sonnet-4-5')

            cprint("⏳ Analyzing all responses for strongest consensus...\n", "cyan")

            response = consensus_model.generate_response(
                system_prompt="You are a consensus analyzer that identifies the strongest agreements across multiple AI predictions. Be concise and clear.",
                user_content=consensus_prompt,
                temperature=0.3,
                max_tokens=1000
            )

            cprint("\n" + "="*80, "white", "on_blue", attrs=['bold'])
            cprint(f"🏆 TOP {TOP_MARKETS_COUNT} CONSENSUS PICKS - MOON DEV AI (Web Search Enhanced!)", "white", "on_blue", attrs=['bold'])
            cprint("="*80, "white", "on_blue", attrs=['bold'])
            cprint("", "white")

            cprint(response.content, "cyan", attrs=['bold'])

            cprint("\n" + "="*80, "white", "on_blue", attrs=['bold'])
            cprint("="*80 + "\n", "white", "on_blue", attrs=['bold'])

            self._save_consensus_picks_to_csv(response.content, markets_df)

        except Exception as e:
            cprint(f"❌ Error getting top consensus picks: {e}", "red")

    def _save_consensus_picks_to_csv(self, consensus_response, markets_df):
        """Save top consensus picks to dedicated CSV"""
        try:
            import re

            picks = []
            lines = consensus_response.split('\n')

            current_pick = {}
            for line in lines:
                line = line.strip()

                market_match = re.match(r'(\d+)\.\s+Market\s+(\d+):\s+(.+)', line)
                if market_match:
                    if current_pick:
                        picks.append(current_pick)

                    rank = market_match.group(1)
                    market_num = int(market_match.group(2))
                    title = market_match.group(3)

                    current_pick = {
                        'rank': rank,
                        'market_number': market_num,
                        'market_title': title
                    }

                elif line.startswith('Side:'):
                    current_pick['side'] = line.replace('Side:', '').strip()

                elif line.startswith('Consensus:'):
                    consensus_text = line.replace('Consensus:', '').strip()
                    current_pick['consensus'] = consensus_text
                    consensus_match = re.search(r'(\d+)\s+out\s+of\s+(\d+)', consensus_text)
                    if consensus_match:
                        current_pick['consensus_count'] = int(consensus_match.group(1))
                        current_pick['total_models'] = int(consensus_match.group(2))

                elif line.startswith('Link:'):
                    current_pick['link'] = line.replace('Link:', '').strip()

                elif line.startswith('Reasoning:'):
                    current_pick['reasoning'] = line.replace('Reasoning:', '').strip()

            if current_pick:
                picks.append(current_pick)

            if not picks:
                cprint("⚠️ Could not parse consensus picks from response", "yellow")
                return

            timestamp = datetime.now().isoformat()
            run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

            records = []
            for pick in picks:
                record = {
                    'timestamp': timestamp,
                    'run_id': run_id,
                    'rank': pick.get('rank', ''),
                    'market_number': pick.get('market_number', ''),
                    'market_title': pick.get('market_title', ''),
                    'side': pick.get('side', ''),
                    'consensus': pick.get('consensus', ''),
                    'consensus_count': pick.get('consensus_count', ''),
                    'total_models': pick.get('total_models', ''),
                    'reasoning': pick.get('reasoning', ''),
                    'web_search_used': 'YES',
                    'link': pick.get('link', '')
                }
                records.append(record)

            if os.path.exists(CONSENSUS_PICKS_CSV):
                consensus_df = pd.read_csv(CONSENSUS_PICKS_CSV)
            else:
                consensus_df = pd.DataFrame(columns=[
                    'timestamp', 'run_id', 'rank', 'market_number', 'market_title',
                    'side', 'consensus', 'consensus_count', 'total_models', 'reasoning',
                    'web_search_used', 'link'
                ])

            consensus_df = pd.concat([
                consensus_df,
                pd.DataFrame(records)
            ], ignore_index=True)

            with self.csv_lock:
                consensus_df.to_csv(CONSENSUS_PICKS_CSV, index=False)

            cprint(f"✅ Saved {len(records)} consensus picks to CSV", "green")
            cprint(f"📁 Consensus picks CSV: {CONSENSUS_PICKS_CSV}", "cyan", attrs=['bold'])

        except Exception as e:
            cprint(f"❌ Error saving consensus picks: {e}", "red")

    # ==========================================================================
    # Status and Analysis Loops
    # ==========================================================================

    def status_display_loop(self):
        """Display status updates every 30 seconds"""
        cprint("\n📊 STATUS DISPLAY THREAD STARTED", "cyan", attrs=['bold'])

        while True:
            try:
                time.sleep(30)

                total_markets = len(self.markets_df)
                now = datetime.now()
                cutoff_time = now - timedelta(hours=REANALYSIS_HOURS)
                fresh_eligible_count = 0

                for idx, row in self.markets_df.iterrows():
                    last_analyzed = row.get('last_analyzed')
                    last_trade = row.get('last_trade_timestamp')

                    is_eligible = False
                    if pd.isna(last_analyzed) or last_analyzed is None:
                        is_eligible = True
                    else:
                        try:
                            analyzed_time = pd.to_datetime(last_analyzed)
                            if analyzed_time < cutoff_time:
                                is_eligible = True
                        except:
                            is_eligible = True

                    has_fresh_trade = False
                    if self.last_analysis_run_timestamp is None:
                        has_fresh_trade = not pd.isna(last_trade) and last_trade is not None
                    else:
                        try:
                            if not pd.isna(last_trade) and last_trade is not None:
                                trade_time = pd.to_datetime(last_trade)
                                last_run_time = pd.to_datetime(self.last_analysis_run_timestamp)
                                if trade_time > last_run_time:
                                    has_fresh_trade = True
                        except:
                            pass

                    if is_eligible and has_fresh_trade:
                        fresh_eligible_count += 1

                cprint(f"\n{'='*60}", "cyan")
                cprint(f"📊 Moon Dev Web Search Agent Status @ {datetime.now().strftime('%H:%M:%S')}", "cyan", attrs=['bold'])
                cprint(f"{'='*60}", "cyan")
                cprint(f"   WebSocket: {'✅ Connected' if self.ws_connected else '❌ Disconnected'}", "green" if self.ws_connected else "red")
                cprint(f"   Total trades: {self.total_trades_received}", "white")
                cprint(f"   Filtered trades (>=${MIN_TRADE_SIZE_USD}): {self.filtered_trades_count}", "yellow")
                cprint(f"   Total markets: {total_markets}", "white")
                cprint(f"   Fresh eligible: {fresh_eligible_count}", "yellow" if fresh_eligible_count < NEW_MARKETS_FOR_ANALYSIS else "green", attrs=['bold'])
                cprint(f"   🔍 Web search: ENABLED", "green")
                cprint(f"{'='*60}\n", "cyan")

            except KeyboardInterrupt:
                break
            except Exception as e:
                cprint(f"❌ Error in status display: {e}", "red")

    def analysis_cycle(self):
        """Check if we have enough eligible markets and run AI analysis"""
        cprint("\n" + "="*80, "magenta")
        cprint("🤖 ANALYSIS CYCLE CHECK (Web Search Enabled)", "magenta", attrs=['bold'])
        cprint(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "magenta")
        cprint("="*80 + "\n", "magenta")

        with self.csv_lock:
            self.markets_df = self._load_markets()

        total_markets = len(self.markets_df)

        if total_markets == 0:
            cprint(f"\n⏳ No markets in database yet! WebSocket is collecting...", "yellow", attrs=['bold'])
            return

        now = datetime.now()
        cutoff_time = now - timedelta(hours=REANALYSIS_HOURS)

        fresh_eligible_count = 0
        for idx, row in self.markets_df.iterrows():
            last_analyzed = row.get('last_analyzed')
            last_trade = row.get('last_trade_timestamp')

            is_eligible = False
            if pd.isna(last_analyzed) or last_analyzed is None:
                is_eligible = True
            else:
                try:
                    analyzed_time = pd.to_datetime(last_analyzed)
                    if analyzed_time < cutoff_time:
                        is_eligible = True
                except:
                    is_eligible = True

            has_fresh_trade = False
            if self.last_analysis_run_timestamp is None:
                has_fresh_trade = not pd.isna(last_trade) and last_trade is not None
            else:
                try:
                    if not pd.isna(last_trade) and last_trade is not None:
                        trade_time = pd.to_datetime(last_trade)
                        last_run_time = pd.to_datetime(self.last_analysis_run_timestamp)
                        if trade_time > last_run_time:
                            has_fresh_trade = True
                except:
                    pass

            if is_eligible and has_fresh_trade:
                fresh_eligible_count += 1

        is_first_run = (self.last_analysis_run_timestamp is None)

        cprint(f"📊 Market Analysis Status:", "cyan", attrs=['bold'])
        cprint(f"   Total markets: {total_markets}", "white")
        cprint(f"   Fresh eligible: {fresh_eligible_count}", "yellow" if fresh_eligible_count < NEW_MARKETS_FOR_ANALYSIS else "green", attrs=['bold'])
        cprint(f"   🔍 Web search will be used for each market!", "green")

        should_analyze = (is_first_run and total_markets > 0) or (fresh_eligible_count >= NEW_MARKETS_FOR_ANALYSIS)

        if should_analyze:
            if is_first_run:
                cprint(f"\n✅ First run with {total_markets} markets! Running AI analysis with web search...\n", "green", attrs=['bold'])
            else:
                cprint(f"\n✅ {fresh_eligible_count} fresh eligible markets! Running AI analysis with web search...\n", "green", attrs=['bold'])

            self.display_recent_markets()
            self.get_ai_predictions()

            self.last_analysis_run_timestamp = datetime.now().isoformat()
            self.last_analyzed_count = total_markets
        else:
            needed = NEW_MARKETS_FOR_ANALYSIS - fresh_eligible_count
            cprint(f"\n⏳ Need {needed} more fresh eligible markets before next analysis", "yellow")

        cprint("\n" + "="*80, "green")
        cprint("✅ Analysis check complete!", "green", attrs=['bold'])
        cprint("="*80 + "\n", "green")

    def analysis_loop(self):
        """Continuously check for new markets to analyze"""
        cprint("\n🤖 ANALYSIS THREAD STARTED (Web Search Enabled)", "magenta", attrs=['bold'])
        cprint(f"🧠 Running first analysis NOW, then every {ANALYSIS_CHECK_INTERVAL_SECONDS}s\n", "magenta")

        while True:
            try:
                self.analysis_cycle()

                next_check = datetime.now() + timedelta(seconds=ANALYSIS_CHECK_INTERVAL_SECONDS)
                cprint(f"⏰ Next analysis check at: {next_check.strftime('%H:%M:%S')}\n", "magenta")

                time.sleep(ANALYSIS_CHECK_INTERVAL_SECONDS)
            except KeyboardInterrupt:
                break
            except Exception as e:
                cprint(f"❌ Error in analysis loop: {e}", "red")
                time.sleep(ANALYSIS_CHECK_INTERVAL_SECONDS)


def main():
    """🌙 Moon Dev Main - WebSocket + Web Search + AI Analysis"""
    cprint("\n" + "="*80, "cyan")
    cprint("🌙 Moon Dev's Polymarket WEB SEARCH Agent!", "cyan", attrs=['bold'])
    cprint("🔍 This agent searches the web for context before AI analysis!", "yellow", attrs=['bold'])
    cprint("="*80, "cyan")
    cprint(f"💰 Tracking trades over ${MIN_TRADE_SIZE_USD}", "yellow")
    cprint(f"🔍 Web search model: {WEB_SEARCH_MODEL}", "green")
    cprint(f"📜 Lookback period: {LOOKBACK_HOURS} hours", "yellow")
    cprint("")
    cprint("🔄 How it works:", "green", attrs=['bold'])
    cprint(f"   1. WebSocket collects whale trades from Polymarket", "cyan")
    cprint(f"   2. For each market, WEB SEARCH finds latest news/context", "cyan")
    cprint(f"   3. AI swarm analyzes markets WITH web context", "cyan")
    cprint(f"   4. Consensus picks are generated with better info!", "cyan")
    cprint("")
    cprint(f"🤖 AI Mode: {'SWARM (7 models)' if USE_SWARM_MODE else 'Single Model'}", "yellow")
    cprint("="*80 + "\n", "cyan")

    # Initialize agent
    agent = PolymarketWebSearchAgent()

    # Fetch historical trades
    cprint("\n" + "="*80, "yellow")
    cprint(f"📜 Fetching historical data from last {LOOKBACK_HOURS} hours...", "yellow", attrs=['bold'])
    cprint("="*80, "yellow")

    historical_trades = agent.fetch_historical_trades()
    if historical_trades:
        cprint(f"\n📦 Processing {len(historical_trades)} historical trades...", "cyan")
        agent.process_trades(historical_trades)
        cprint(f"✅ Database populated with {len(agent.markets_df)} markets", "green")
    else:
        cprint("⚠️ No historical trades found - will start fresh from WebSocket", "yellow")

    cprint("="*80 + "\n", "yellow")

    # Connect WebSocket
    agent.connect_websocket()

    # Create threads
    status_thread = threading.Thread(target=agent.status_display_loop, daemon=True, name="Status")
    analysis_thread = threading.Thread(target=agent.analysis_loop, daemon=True, name="Analysis")

    try:
        cprint("🚀 Moon Dev starting threads...\n", "green", attrs=['bold'])
        status_thread.start()
        analysis_thread.start()

        cprint("✨ Moon Dev Web Search Agent running! Press Ctrl+C to stop.\n", "green", attrs=['bold'])
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        cprint("\n\n" + "="*80, "yellow")
        cprint("⚠️ Moon Dev Polymarket Web Search Agent stopped by user", "yellow", attrs=['bold'])
        cprint("="*80 + "\n", "yellow")
        sys.exit(0)


if __name__ == "__main__":
    main()
