"""
🌙 Moon Dev's Polymarket Prediction Market Agent
Built with love by Moon Dev 🚀

This agent scans Polymarket trades, saves markets to CSV, and uses AI to make predictions.
NO ACTUAL TRADING - just predictions and analysis for now.
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

# ==============================================================================
# CONFIGURATION - Customize these settings
# ==============================================================================

# Trade filtering
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
SEND_PRICE_INFO_TO_AI = False  # Send market price/odds to AI models (True = include price, False = no price)

# 🌙 Moon Dev - AI Prompts (customize these for your own edge!)
# ==============================================================================

# System prompt for individual AI market analysis
MARKET_ANALYSIS_SYSTEM_PROMPT = """You are a prediction market expert analyzing Polymarket markets.
For each market, provide your prediction in this exact format:

MARKET [number]: [decision]
Reasoning: [brief 1-2 sentence explanation]

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
DATA_FOLDER = os.path.join(project_root, "src/data/polymarket")
MARKETS_CSV = os.path.join(DATA_FOLDER, "markets.csv")
PREDICTIONS_CSV = os.path.join(DATA_FOLDER, "predictions.csv")
CONSENSUS_PICKS_CSV = os.path.join(DATA_FOLDER, "consensus_picks.csv")  # 🌙 Moon Dev - Top consensus picks only

# Polymarket API & WebSocket
POLYMARKET_API_BASE = "https://data-api.polymarket.com"
WEBSOCKET_URL = "wss://ws-live-data.polymarket.com"

# ==============================================================================
# Polymarket Agent
# ==============================================================================

class PolymarketAgent:
    """Agent that tracks Polymarket markets and provides AI predictions"""

    def __init__(self):
        """Initialize the Polymarket agent"""
        cprint("\n" + "="*80, "cyan")
        cprint("🌙 Polymarket Prediction Market Agent - Initializing", "cyan", attrs=['bold'])
        cprint("="*80, "cyan")

        # Create data folder if it doesn't exist
        os.makedirs(DATA_FOLDER, exist_ok=True)

        # Thread-safe lock for CSV access
        self.csv_lock = threading.Lock()

        # Track which markets have been analyzed
        self.last_analyzed_count = 0
        self.last_analysis_run_timestamp = None  # When we last ran AI analysis

        # WebSocket connection
        self.ws = None
        self.ws_connected = False
        self.total_trades_received = 0
        self.filtered_trades_count = 0
        self.ignored_crypto_count = 0
        self.ignored_sports_count = 0

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

        cprint(f"📊 Loaded {len(self.markets_df)} existing markets from CSV", "cyan")
        cprint(f"🔮 Loaded {len(self.predictions_df)} existing predictions from CSV", "cyan")

        if len(self.predictions_df) > 0:
            # Show summary of prediction history
            unique_runs = self.predictions_df['analysis_run_id'].nunique()
            cprint(f"   └─ {unique_runs} historical analysis runs", "cyan")

        cprint("✨ Initialization complete!\n", "green")

    def _load_markets(self):
        """Load existing markets from CSV or create empty DataFrame"""
        if os.path.exists(MARKETS_CSV):
            try:
                df = pd.read_csv(MARKETS_CSV)
                cprint(f"✅ Loaded existing markets from {MARKETS_CSV}", "green")
                return df
            except Exception as e:
                cprint(f"⚠️ Error loading CSV: {e}", "yellow")
                cprint("Creating new DataFrame", "yellow")

        # Create new DataFrame with required columns
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
                cprint("Creating new predictions DataFrame", "yellow")

        # Create new DataFrame with required columns
        # 🌙 Moon Dev - Link column at END for clickable CSVs in Excel/Numbers
        return pd.DataFrame(columns=[
            'analysis_timestamp', 'analysis_run_id', 'market_title', 'market_slug',
            'claude_prediction', 'openai_prediction', 'groq_prediction',
            'gemini_prediction', 'deepseek_prediction', 'xai_prediction',
            'ollama_prediction', 'consensus_prediction', 'num_models_responded',
            'market_link'  # 🌙 Link at end for clickable CSVs
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

    def is_near_resolution(self, price):
        """Check if price is within threshold of $0 or $1 (near resolution)"""
        price_float = float(price)
        return price_float <= IGNORE_PRICE_THRESHOLD or price_float >= (1.0 - IGNORE_PRICE_THRESHOLD)

    def should_ignore_market(self, title):
        """🌙 Moon Dev - Check if market should be ignored based on category keywords

        Returns:
            tuple: (should_ignore: bool, reason: str or None)
        """
        title_lower = title.lower()

        # Check crypto keywords
        for keyword in IGNORE_CRYPTO_KEYWORDS:
            if keyword in title_lower:
                return (True, f"crypto/bitcoin ({keyword})")

        # Check sports keywords
        for keyword in IGNORE_SPORTS_KEYWORDS:
            if keyword in title_lower:
                return (True, f"sports ({keyword})")

        return (False, None)

    def on_ws_message(self, ws, message):
        """🌙 Moon Dev - Handle incoming WebSocket messages"""
        try:
            data = json.loads(message)

            # Check if this is a trade message
            if isinstance(data, dict):
                # Handle subscription confirmation
                if data.get('type') == 'subscribed':
                    cprint("✅ Moon Dev WebSocket subscribed successfully to live trades!", "green")
                    self.ws_connected = True
                    return

                # Handle pong
                if data.get('type') == 'pong':
                    return

                # Handle trade data
                topic = data.get('topic')
                msg_type = data.get('type')
                payload = data.get('payload', {})

                if topic == 'activity' and msg_type == 'orders_matched':
                    self.total_trades_received += 1

                    # If we're receiving trades, WebSocket is definitely connected
                    if not self.ws_connected:
                        self.ws_connected = True

                    # Extract trade info
                    price = float(payload.get('price', 0))
                    size = float(payload.get('size', 0))
                    usd_amount = price * size
                    title = payload.get('title', 'Unknown')

                    # 🌙 Moon Dev - Check if we should ignore this market category
                    should_ignore, ignore_reason = self.should_ignore_market(title)
                    if should_ignore:
                        # Track what we're ignoring
                        if 'crypto' in ignore_reason or 'bitcoin' in ignore_reason:
                            self.ignored_crypto_count += 1
                        elif 'sports' in ignore_reason:
                            self.ignored_sports_count += 1
                        # Skip this market silently (don't spam console)
                        return

                    # Filter by minimum amount and near-resolution prices
                    if usd_amount >= MIN_TRADE_SIZE_USD and not self.is_near_resolution(price):
                        self.filtered_trades_count += 1

                        # 🌙 MOON DEV - Process this trade immediately
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

                        # Process this single trade (silently - status thread shows stats)
                        self.process_trades([trade_data])

        except json.JSONDecodeError:
            pass  # Ignore malformed messages
        except Exception as e:
            cprint(f"⚠️ Moon Dev - Error processing WebSocket message: {e}", "yellow")

    def on_ws_error(self, ws, error):
        """🌙 Moon Dev - Handle WebSocket errors"""
        cprint(f"❌ Moon Dev WebSocket Error: {error}", "red")

    def on_ws_close(self, ws, close_status_code, close_msg):
        """🌙 Moon Dev - Handle WebSocket close"""
        self.ws_connected = False
        cprint(f"\n🔌 Moon Dev WebSocket connection closed: {close_status_code} - {close_msg}", "yellow")
        cprint("Reconnecting in 5 seconds...", "cyan")
        time.sleep(5)
        self.connect_websocket()

    def on_ws_open(self, ws):
        """🌙 Moon Dev - Handle WebSocket open - send subscription"""
        cprint("🔌 Moon Dev WebSocket connected!", "green")

        # Subscribe to all trades on the activity topic
        subscription_msg = {
            "action": "subscribe",
            "subscriptions": [
                {
                    "topic": "activity",
                    "type": "orders_matched"
                }
            ]
        }

        cprint(f"📡 Moon Dev sending subscription for live trades...", "cyan")
        ws.send(json.dumps(subscription_msg))

        # Set connected flag immediately after sending subscription
        self.ws_connected = True
        cprint("✅ Moon Dev subscription sent! Waiting for trades...", "green")

        # Start ping thread to keep connection alive
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
        """🌙 Moon Dev - Connect to Polymarket WebSocket"""
        cprint(f"🚀 Moon Dev connecting to {WEBSOCKET_URL}...", "cyan")

        self.ws = websocket.WebSocketApp(
            WEBSOCKET_URL,
            on_open=self.on_ws_open,
            on_message=self.on_ws_message,
            on_error=self.on_ws_error,
            on_close=self.on_ws_close
        )

        # Run WebSocket in a thread
        ws_thread = threading.Thread(target=self.ws.run_forever, daemon=True)
        ws_thread.start()

        cprint("✅ Moon Dev WebSocket thread started!", "green")

    def fetch_historical_trades(self, hours_back=None):
        """🌙 Moon Dev - Fetch historical trades from Polymarket API on startup

        Args:
            hours_back: How many hours back to fetch (defaults to LOOKBACK_HOURS)

        Returns:
            List of trade dictionaries
        """
        if hours_back is None:
            hours_back = LOOKBACK_HOURS

        try:
            cprint(f"\n📡 Moon Dev fetching historical trades (last {hours_back}h)...", "yellow")

            # Calculate timestamp for X hours ago
            cutoff_time = datetime.now() - timedelta(hours=hours_back)
            cutoff_timestamp = int(cutoff_time.timestamp())

            # Fetch trades from activity stream
            url = f"{POLYMARKET_API_BASE}/trades"
            params = {
                'limit': 1000,  # Max allowed by API
                '_min_timestamp': cutoff_timestamp
            }

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            trades = response.json()
            cprint(f"✅ Fetched {len(trades)} total historical trades", "green")

            # Filter and process trades
            filtered_trades = []
            for trade in trades:
                # Get trade info
                price = float(trade.get('price', 0))
                size = float(trade.get('size', 0))
                usd_amount = price * size
                title = trade.get('title', 'Unknown')

                # Check if we should ignore this market category
                should_ignore, _ = self.should_ignore_market(title)
                if should_ignore:
                    continue

                # Filter by minimum amount and near-resolution prices
                if usd_amount >= MIN_TRADE_SIZE_USD and not self.is_near_resolution(price):
                    filtered_trades.append(trade)

            cprint(f"💰 Found {len(filtered_trades)} trades over ${MIN_TRADE_SIZE_USD} (after filters)", "cyan")

            return filtered_trades

        except Exception as e:
            cprint(f"❌ Error fetching historical trades: {e}", "red")
            return []

    def process_trades(self, trades):
        """Process trades and add new markets to DataFrame

        Args:
            trades: List of trade dictionaries from API
        """
        if not trades:
            return

        # Get unique markets from trades
        # Use conditionId as the unique market identifier
        unique_markets = {}
        for trade in trades:
            # conditionId is the unique identifier for each market/outcome
            market_id = trade.get('conditionId', '')
            if market_id and market_id not in unique_markets:
                unique_markets[market_id] = trade

        new_markets = 0
        updated_markets = 0

        for market_id, trade in unique_markets.items():
            try:
                # Extract trade data from Polymarket API structure
                event_slug = trade.get('eventSlug', '')
                title = trade.get('title', 'Unknown Market')
                outcome = trade.get('outcome', '')
                price = float(trade.get('price', 0))
                size_usd = float(trade.get('size', 0))
                timestamp = trade.get('timestamp', '')
                condition_id = trade.get('conditionId', '')

                # Check if market already exists
                if market_id in self.markets_df['market_id'].values:
                    # 🌙 Moon Dev - UPDATE existing market with new trade data (fresh odds!)
                    mask = self.markets_df['market_id'] == market_id
                    self.markets_df.loc[mask, 'timestamp'] = timestamp
                    self.markets_df.loc[mask, 'outcome'] = outcome
                    self.markets_df.loc[mask, 'price'] = price
                    self.markets_df.loc[mask, 'size_usd'] = size_usd
                    self.markets_df.loc[mask, 'last_trade_timestamp'] = datetime.now().isoformat()  # Track fresh trade!
                    updated_markets += 1
                    continue

                # Add new market
                new_market = {
                    'timestamp': timestamp,
                    'market_id': condition_id,  # Use conditionId as unique identifier
                    'event_slug': event_slug,
                    'title': title,
                    'outcome': outcome,
                    'price': price,
                    'size_usd': size_usd,
                    'first_seen': datetime.now().isoformat(),
                    'last_analyzed': None,  # Never analyzed yet
                    'last_trade_timestamp': datetime.now().isoformat()  # Fresh trade!
                }

                self.markets_df = pd.concat([
                    self.markets_df,
                    pd.DataFrame([new_market])
                ], ignore_index=True)

                new_markets += 1

                # Only print if it's a new market
                cprint(f"✨ NEW: ${size_usd:,.0f} - {title[:70]}", "green")

            except Exception as e:
                cprint(f"⚠️ Error processing trade: {e}", "yellow")
                continue

        # Save if we added or updated markets
        if new_markets > 0 or updated_markets > 0:
            self._save_markets()
            if updated_markets > 0:
                cprint(f"🔄 Updated {updated_markets} existing markets with fresh trade data", "cyan")

    def display_recent_markets(self):
        """Display the most recent markets from CSV"""
        if len(self.markets_df) == 0:
            cprint("\n📊 No markets in database yet", "yellow")
            return

        cprint("\n" + "="*80, "cyan")
        cprint(f"📊 Most Recent {min(MARKETS_TO_DISPLAY, len(self.markets_df))} Markets", "cyan", attrs=['bold'])
        cprint("="*80, "cyan")

        # Get most recent markets
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

    def get_ai_predictions(self):
        """Get AI predictions for recent markets"""
        if len(self.markets_df) == 0:
            cprint("\n⚠️ No markets to analyze yet", "yellow")
            return

        # Get last N markets for analysis
        markets_to_analyze = self.markets_df.tail(MARKETS_TO_ANALYZE)

        # Generate unique analysis run ID
        analysis_run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        analysis_timestamp = datetime.now().isoformat()

        cprint("\n" + "="*80, "magenta")
        cprint(f"🤖 AI Analysis - Analyzing {len(markets_to_analyze)} markets", "magenta", attrs=['bold'])
        cprint(f"📊 Analysis Run ID: {analysis_run_id}", "magenta")
        cprint(f"💰 Price info to AI: {'✅ ENABLED' if SEND_PRICE_INFO_TO_AI else '❌ DISABLED'}", "green" if SEND_PRICE_INFO_TO_AI else "yellow")
        cprint("="*80, "magenta")

        # Build prompt with market information
        # 🌙 Moon Dev - Conditionally include price info based on config
        if SEND_PRICE_INFO_TO_AI:
            markets_text = "\n\n".join([
                f"Market {i+1}:\n"
                f"Title: {row['title']}\n"
                f"Current Price: ${row['price']:.2f} ({row['price']*100:.1f}% odds for {row['outcome']})\n"
                f"Recent trade: ${row['size_usd']:,.2f} on {row['outcome']}\n"
                f"Link: https://polymarket.com/event/{row['event_slug']}"
                for i, (_, row) in enumerate(markets_to_analyze.iterrows())
            ])
        else:
            markets_text = "\n\n".join([
                f"Market {i+1}:\n"
                f"Title: {row['title']}\n"
                f"Recent trade: ${row['size_usd']:,.2f} on {row['outcome']}\n"
                f"Link: https://polymarket.com/event/{row['event_slug']}"
                for i, (_, row) in enumerate(markets_to_analyze.iterrows())
            ])

        system_prompt = MARKET_ANALYSIS_SYSTEM_PROMPT

        user_prompt = f"""Analyze these {len(markets_to_analyze)} Polymarket markets and provide your predictions:

{markets_text}

Provide predictions for each market in the specified format."""

        if USE_SWARM_MODE and self.swarm:
            # Use swarm mode - get predictions from multiple AIs
            cprint("\n🌊 Getting predictions from AI swarm (120s timeout per model)...\n", "cyan")

            # Query the swarm (swarm handles timeouts gracefully and returns partial results)
            cprint("📡 Moon Dev sending prompts to swarm...", "cyan")
            swarm_result = self.swarm.query(
                prompt=user_prompt,
                system_prompt=system_prompt
            )

            # Check if we got any responses
            if not swarm_result or not swarm_result.get('responses'):
                cprint("❌ No responses from swarm - all models failed or timed out", "red")
                return

            # Count successful responses
            successful_responses = [
                name for name, data in swarm_result.get('responses', {}).items()
                if data.get('success')
            ]

            if not successful_responses:
                cprint("❌ All AI models failed - no predictions available", "red")
                return

            cprint(f"\n✅ Received {len(successful_responses)}/{len(swarm_result['responses'])} successful responses from swarm!\n", "green", attrs=['bold'])

            # Display individual AI responses as they arrive
            cprint("="*80, "yellow")
            cprint("🤖 Individual AI Predictions", "yellow", attrs=['bold'])
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

            # Calculate and display consensus (pass markets for title mapping)
            consensus_text = self._calculate_polymarket_consensus(swarm_result, markets_to_analyze)

            cprint("\n" + "="*80, "green")
            cprint("🎯 CONSENSUS ANALYSIS", "green", attrs=['bold'])
            cprint(f"Based on {len(successful_responses)} AI models", "green")
            cprint("="*80, "green")
            cprint(consensus_text, "white")
            cprint("="*80 + "\n", "green")

            # 🌙 Moon Dev - Run final consensus AI to pick top 3 markets
            self._get_top_consensus_picks(swarm_result, markets_to_analyze)

            # Save predictions to database
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
                import traceback
                traceback.print_exc()

            # 🌙 Moon Dev - Mark analyzed markets with timestamp
            self._mark_markets_analyzed(markets_to_analyze, analysis_timestamp)
        else:
            # Use single model
            cprint(f"\n🤖 Getting predictions from {AI_MODEL_PROVIDER}/{AI_MODEL_NAME}...\n", "cyan")

            try:
                response = self.model.generate_response(
                    system_prompt=system_prompt,
                    user_content=user_prompt,
                    temperature=0.7
                )

                cprint("="*80, "green")
                cprint("🎯 AI PREDICTION", "green", attrs=['bold'])
                cprint("="*80, "green")
                cprint(response.content, "white")
                cprint("="*80 + "\n", "green")

                # Save single model prediction
                prediction_summary = response.content.split('\n')[0][:200] if response.content else 'No response'
                prediction_record = {
                    'analysis_timestamp': analysis_timestamp,
                    'analysis_run_id': analysis_run_id,
                    'market_title': f"Analyzed {len(markets_to_analyze)} markets",
                    'market_slug': 'batch_analysis',
                    'claude_prediction': 'N/A',
                    'openai_prediction': 'N/A',
                    'groq_prediction': 'N/A',
                    'gemini_prediction': 'N/A',
                    'deepseek_prediction': 'N/A',
                    'xai_prediction': prediction_summary if AI_MODEL_PROVIDER == 'xai' else 'N/A',
                    'ollama_prediction': 'N/A',
                    'consensus_prediction': prediction_summary,
                    'num_models_responded': 1
                }

                self.predictions_df = pd.concat([
                    self.predictions_df,
                    pd.DataFrame([prediction_record])
                ], ignore_index=True)
                self._save_predictions()
                cprint(f"✅ Saved analysis run {analysis_run_id} to predictions database", "green")

                # 🌙 Moon Dev - Mark analyzed markets with timestamp
                self._mark_markets_analyzed(markets_to_analyze, analysis_timestamp)

            except Exception as e:
                cprint(f"❌ Error getting prediction: {e}", "red")

    def _mark_markets_analyzed(self, markets, analysis_timestamp):
        """🌙 Moon Dev - Mark markets as analyzed with timestamp

        Args:
            markets: DataFrame of markets that were just analyzed
            analysis_timestamp: ISO timestamp of when analysis completed
        """
        try:
            cprint("\n🕒 Marking markets as analyzed...", "cyan")

            # Get market_ids from the analyzed markets
            analyzed_market_ids = markets['market_id'].tolist()

            # Update last_analyzed for these markets
            for market_id in analyzed_market_ids:
                mask = self.markets_df['market_id'] == market_id
                self.markets_df.loc[mask, 'last_analyzed'] = analysis_timestamp

            # Save updated markets DataFrame
            self._save_markets()

            cprint(f"✅ Marked {len(analyzed_market_ids)} markets with analysis timestamp", "green")
            cprint(f"   Next re-analysis eligible after: {REANALYSIS_HOURS}h", "cyan")

        except Exception as e:
            cprint(f"❌ Error marking markets as analyzed: {e}", "red")
            import traceback
            traceback.print_exc()

    def _save_swarm_predictions(self, analysis_run_id, analysis_timestamp, markets, swarm_result):
        """🌙 Moon Dev - Save swarm predictions to CSV database (one row per market)

        Args:
            analysis_run_id: Unique ID for this analysis run
            analysis_timestamp: ISO timestamp of analysis
            markets: DataFrame of markets analyzed
            swarm_result: Dictionary containing swarm responses
        """
        try:
            cprint("\n💾 Saving predictions to database...", "cyan")

            # Parse each model's predictions by market number
            market_predictions = {}  # {market_num: {model_name: prediction}}

            for model_name, model_data in swarm_result.get('responses', {}).items():
                if not model_data.get('success'):
                    continue

                response = model_data.get('response', '')
                lines = response.strip().split('\n')

                for line in lines:
                    line_upper = line.upper()

                    # Look for "MARKET X:" pattern
                    if 'MARKET' in line_upper and ':' in line:
                        try:
                            # Extract market number
                            market_part = line_upper.split('MARKET')[1].split(':')[0].strip()
                            market_num = int(''.join(filter(str.isdigit, market_part)))

                            # 🌙 Moon Dev - Validate market number is within range
                            if market_num < 1 or market_num > len(markets):
                                continue  # Skip invalid market numbers (AI hallucination)

                            # Initialize if needed
                            if market_num not in market_predictions:
                                market_predictions[market_num] = {}

                            # Extract the prediction (YES/NO/NO_TRADE)
                            if 'NO_TRADE' in line_upper or 'NO TRADE' in line_upper:
                                market_predictions[market_num][model_name] = 'NO_TRADE'
                            elif 'YES' in line_upper:
                                market_predictions[market_num][model_name] = 'YES'
                            elif 'NO' in line_upper:
                                market_predictions[market_num][model_name] = 'NO'
                        except:
                            continue

            # Save one row per market
            markets_list = list(markets.iterrows())
            new_records = []

            for market_num, predictions in market_predictions.items():
                # Get market details (market_num is 1-indexed)
                if 1 <= market_num <= len(markets_list):
                    idx, row = markets_list[market_num - 1]
                    market_title = row['title']
                    market_slug = row['event_slug']
                    market_link = f"https://polymarket.com/event/{market_slug}"

                    # Calculate consensus for this market
                    votes = {"YES": 0, "NO": 0, "NO_TRADE": 0}
                    for pred in predictions.values():
                        if pred in votes:
                            votes[pred] += 1

                    majority = max(votes, key=votes.get)
                    total = sum(votes.values())
                    confidence = int((votes[majority] / total) * 100) if total > 0 else 0
                    consensus = f"{majority} ({confidence}%)"

                    # Create record
                    record = {
                        'analysis_timestamp': analysis_timestamp,
                        'analysis_run_id': analysis_run_id,
                        'market_title': market_title,
                        'market_slug': market_slug,
                        'claude_prediction': predictions.get('claude', 'N/A'),
                        'openai_prediction': predictions.get('openai', 'N/A'),
                        'groq_prediction': predictions.get('groq', 'N/A'),
                        'gemini_prediction': predictions.get('gemini', 'N/A'),
                        'deepseek_prediction': predictions.get('deepseek', 'N/A'),
                        'xai_prediction': predictions.get('xai', 'N/A'),
                        'ollama_prediction': predictions.get('ollama', 'N/A'),
                        'consensus_prediction': consensus,
                        'num_models_responded': len(predictions),
                        'market_link': market_link  # 🌙 Moon Dev - Link at end for clickable CSVs
                    }
                    new_records.append(record)

            if new_records:
                # Add all new records
                self.predictions_df = pd.concat([
                    self.predictions_df,
                    pd.DataFrame(new_records)
                ], ignore_index=True)

                # Save to CSV
                self._save_predictions()

                cprint(f"✅ Saved {len(new_records)} market predictions (run {analysis_run_id})", "green")
            else:
                cprint(f"⚠️ No structured predictions found to save", "yellow")

        except Exception as e:
            cprint(f"❌ Error saving predictions: {e}", "red")
            import traceback
            traceback.print_exc()

    def _calculate_polymarket_consensus(self, swarm_result, markets_df):
        """
        🌙 Moon Dev - Calculate consensus from individual swarm responses for Polymarket predictions

        Args:
            swarm_result: Result dict from swarm.query() containing individual responses
            markets_df: DataFrame of markets being analyzed (to map numbers to titles)

        Returns:
            str: Formatted consensus text with vote breakdown and analysis
        """
        try:
            # Count votes for each prediction across all markets
            # For polymarket we look for YES, NO, NO_TRADE patterns
            market_votes = {}  # {market_num: {YES: count, NO: count, NO_TRADE: count}}
            model_predictions = {}  # {model_name: response_text}

            # Collect all successful model responses
            for provider, data in swarm_result["responses"].items():
                if not data["success"]:
                    continue

                response_text = data["response"]
                model_predictions[provider] = response_text

                # Parse each market prediction from the response
                lines = response_text.strip().split('\n')
                for line in lines:
                    line_upper = line.upper()

                    # Look for "MARKET X:" pattern
                    if 'MARKET' in line_upper and ':' in line:
                        try:
                            # Extract market number
                            market_part = line_upper.split('MARKET')[1].split(':')[0].strip()
                            market_num = int(''.join(filter(str.isdigit, market_part)))

                            # 🌙 Moon Dev - Validate market number is within range
                            if market_num < 1 or market_num > len(markets_df):
                                continue  # Skip invalid market numbers (AI hallucination)

                            # Initialize market votes if not exists
                            if market_num not in market_votes:
                                market_votes[market_num] = {"YES": 0, "NO": 0, "NO_TRADE": 0}

                            # Count the vote
                            if 'NO_TRADE' in line_upper or 'NO TRADE' in line_upper:
                                market_votes[market_num]["NO_TRADE"] += 1
                            elif 'YES' in line_upper:
                                market_votes[market_num]["YES"] += 1
                            elif 'NO' in line_upper:
                                market_votes[market_num]["NO"] += 1
                        except:
                            continue

            # Build consensus summary
            total_models = len(model_predictions)

            if total_models == 0:
                return "No valid model responses to analyze"

            consensus_text = f"Analyzed responses from {total_models} AI models\n\n"

            # Show consensus for each market
            if market_votes:
                consensus_text += "MARKET CONSENSUS:\n"
                consensus_text += "="*80 + "\n\n"

                # Convert markets_df to list for indexing
                markets_list = list(markets_df.iterrows())

                for market_num in sorted(market_votes.keys()):
                    votes = market_votes[market_num]
                    total_votes = sum(votes.values())

                    if total_votes == 0:
                        continue

                    # Find majority
                    majority = max(votes, key=votes.get)
                    majority_count = votes[majority]
                    confidence = int((majority_count / total_votes) * 100)

                    # Get market title and slug from DataFrame (market_num is 1-indexed)
                    if 1 <= market_num <= len(markets_list):
                        idx, row = markets_list[market_num - 1]
                        market_title = row['title']
                        market_slug = row['event_slug']
                        market_link = f"https://polymarket.com/event/{market_slug}"

                        # Truncate title if too long
                        display_title = market_title[:70] + "..." if len(market_title) > 70 else market_title

                        consensus_text += f"Market {market_num}: {majority} ({confidence}% consensus)\n"
                        consensus_text += f"  📌 {display_title}\n"
                        consensus_text += f"  🔗 {market_link}\n"
                        consensus_text += f"  Votes: YES: {votes['YES']} | NO: {votes['NO']} | NO_TRADE: {votes['NO_TRADE']}\n\n"
                    else:
                        consensus_text += f"Market {market_num}: {majority} ({confidence}% consensus)\n"
                        consensus_text += f"  YES: {votes['YES']} | NO: {votes['NO']} | NO_TRADE: {votes['NO_TRADE']}\n\n"
            else:
                consensus_text += "⚠️ Could not extract structured market predictions from responses\n"
                consensus_text += "Models may have used different formatting\n\n"

            # List which models responded
            consensus_text += "\nRESPONDED MODELS:\n"
            consensus_text += "="*60 + "\n"
            for model_name in model_predictions.keys():
                consensus_text += f"  ✅ {model_name}\n"

            # Show failed models
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
            cprint(f"❌ Error calculating polymarket consensus: {e}", "red")
            import traceback
            traceback.print_exc()
            return f"Error calculating consensus: {str(e)}"

    def _get_top_consensus_picks(self, swarm_result, markets_df):
        """
        🌙 Moon Dev - Use consensus AI to identify top 3 markets with strongest agreement

        Args:
            swarm_result: Result dict from swarm.query() containing all AI responses
            markets_df: DataFrame of markets being analyzed
        """
        try:
            cprint("\n" + "="*80, "yellow")
            cprint("🧠 Running Consensus AI to identify top 3 picks...", "yellow", attrs=['bold'])
            cprint("="*80 + "\n", "yellow")

            # Build comprehensive summary of all AI responses
            all_responses_text = ""
            for model_name, model_data in swarm_result.get('responses', {}).items():
                if model_data.get('success'):
                    all_responses_text += f"\n{'='*60}\n"
                    all_responses_text += f"{model_name.upper()} PREDICTIONS:\n"
                    all_responses_text += f"{'='*60}\n"
                    all_responses_text += model_data.get('response', '') + "\n"

            # Create market reference list
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

            # Use Claude 4.5 Sonnet for consensus (fast and reliable)
            consensus_model = ModelFactory().get_model('claude', 'claude-sonnet-4-5')

            cprint("⏳ Analyzing all responses for strongest consensus...\n", "cyan")

            response = consensus_model.generate_response(
                system_prompt="You are a consensus analyzer that identifies the strongest agreements across multiple AI predictions. Be concise and clear.",
                user_content=consensus_prompt,
                temperature=0.3,  # Low temperature for consistent analysis
                max_tokens=1000
            )

            # Print with BLUE background
            cprint("\n" + "="*80, "white", "on_blue", attrs=['bold'])
            cprint(f"🏆 TOP {TOP_MARKETS_COUNT} CONSENSUS PICKS - MOON DEV AI RECOMMENDATION", "white", "on_blue", attrs=['bold'])
            cprint("="*80, "white", "on_blue", attrs=['bold'])
            cprint("", "white")  # Reset color

            # Print the actual response
            cprint(response.content, "cyan", attrs=['bold'])

            cprint("\n" + "="*80, "white", "on_blue", attrs=['bold'])
            cprint("="*80 + "\n", "white", "on_blue", attrs=['bold'])

            # 🌙 Moon Dev - Save consensus picks to dedicated CSV
            self._save_consensus_picks_to_csv(response.content, markets_df)

        except Exception as e:
            cprint(f"❌ Error getting top consensus picks: {e}", "red")
            import traceback
            traceback.print_exc()

    def _save_consensus_picks_to_csv(self, consensus_response, markets_df):
        """
        🌙 Moon Dev - Save top consensus picks to dedicated CSV (append-only)

        This CSV only contains the TOP consensus picks from each analysis run.
        Perfect for reviewing what the AI swarm agreed on throughout the day!

        Args:
            consensus_response: The consensus AI's response text
            markets_df: DataFrame of markets being analyzed
        """
        try:
            import re
            from datetime import datetime

            cprint("\n💾 Saving top consensus picks to CSV...", "cyan")

            # Parse the consensus response to extract picks
            picks = []
            lines = consensus_response.split('\n')

            current_pick = {}
            for line in lines:
                line = line.strip()

                # Look for market number and title (e.g., "1. Market 5: Bitcoin to hit $100k?")
                market_match = re.match(r'(\d+)\.\s+Market\s+(\d+):\s+(.+)', line)
                if market_match:
                    # Save previous pick if exists
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

                # Extract Side
                elif line.startswith('Side:'):
                    current_pick['side'] = line.replace('Side:', '').strip()

                # Extract Consensus
                elif line.startswith('Consensus:'):
                    consensus_text = line.replace('Consensus:', '').strip()
                    current_pick['consensus'] = consensus_text
                    # Try to extract the count (e.g., "5 out of 6" -> 5, 6)
                    consensus_match = re.search(r'(\d+)\s+out\s+of\s+(\d+)', consensus_text)
                    if consensus_match:
                        current_pick['consensus_count'] = int(consensus_match.group(1))
                        current_pick['total_models'] = int(consensus_match.group(2))

                # Extract Link
                elif line.startswith('Link:'):
                    current_pick['link'] = line.replace('Link:', '').strip()

                # Extract Reasoning
                elif line.startswith('Reasoning:'):
                    current_pick['reasoning'] = line.replace('Reasoning:', '').strip()

            # Add last pick
            if current_pick:
                picks.append(current_pick)

            if not picks:
                cprint("⚠️ Could not parse consensus picks from response", "yellow")
                return

            # Create timestamp for this analysis run
            timestamp = datetime.now().isoformat()
            run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Convert to records for CSV (🌙 Moon Dev - link at END for clickable CSVs)
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
                    'link': pick.get('link', '')  # 🌙 Link at end for clickable CSVs
                }
                records.append(record)

            # Load or create consensus picks CSV (🌙 Moon Dev - link at END for clickable CSVs)
            if os.path.exists(CONSENSUS_PICKS_CSV):
                consensus_df = pd.read_csv(CONSENSUS_PICKS_CSV)
            else:
                consensus_df = pd.DataFrame(columns=[
                    'timestamp', 'run_id', 'rank', 'market_number', 'market_title',
                    'side', 'consensus', 'consensus_count', 'total_models', 'reasoning',
                    'link'  # 🌙 Link at end for clickable CSVs
                ])

            # Append new records
            consensus_df = pd.concat([
                consensus_df,
                pd.DataFrame(records)
            ], ignore_index=True)

            # Save to CSV
            with self.csv_lock:
                consensus_df.to_csv(CONSENSUS_PICKS_CSV, index=False)

            cprint(f"✅ Saved {len(records)} consensus picks to CSV", "green")
            cprint(f"📁 Consensus picks CSV: {CONSENSUS_PICKS_CSV}", "cyan", attrs=['bold'])
            cprint(f"📊 Total consensus picks in history: {len(consensus_df)}", "cyan")

        except Exception as e:
            cprint(f"❌ Error saving consensus picks: {e}", "red")
            import traceback
            traceback.print_exc()

    def status_display_loop(self):
        """🌙 Moon Dev - Display status updates every 30 seconds"""
        cprint("\n📊 STATUS DISPLAY THREAD STARTED", "cyan", attrs=['bold'])
        cprint(f"📡 Showing stats every 30 seconds\n", "cyan")

        while True:
            try:
                time.sleep(30)

                total_markets = len(self.markets_df)

                # 🌙 Moon Dev - Count markets with FRESH TRADES that are also ELIGIBLE
                now = datetime.now()
                cutoff_time = now - timedelta(hours=REANALYSIS_HOURS)
                fresh_eligible_count = 0

                for idx, row in self.markets_df.iterrows():
                    last_analyzed = row.get('last_analyzed')
                    last_trade = row.get('last_trade_timestamp')

                    # Check if eligible
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

                    # Check if has fresh trade
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
                cprint(f"📊 Moon Dev Status @ {datetime.now().strftime('%H:%M:%S')}", "cyan", attrs=['bold'])
                cprint(f"{'='*60}", "cyan")
                cprint(f"   WebSocket Connected: {'✅ YES' if self.ws_connected else '❌ NO'}", "green" if self.ws_connected else "red")
                cprint(f"   Total trades received: {self.total_trades_received}", "white")
                cprint(f"   Ignored crypto/bitcoin: {self.ignored_crypto_count}", "red")
                cprint(f"   Ignored sports: {self.ignored_sports_count}", "red")
                cprint(f"   Filtered trades (>=${MIN_TRADE_SIZE_USD}): {self.filtered_trades_count}", "yellow")
                cprint(f"   Total markets in database: {total_markets}", "white")
                cprint(f"   Fresh eligible markets: {fresh_eligible_count}", "yellow" if fresh_eligible_count < NEW_MARKETS_FOR_ANALYSIS else "green", attrs=['bold'])
                cprint(f"   (Eligible + traded since last run)", "white")

                if fresh_eligible_count >= NEW_MARKETS_FOR_ANALYSIS:
                    cprint(f"   ✅ Ready for analysis! (Have {fresh_eligible_count}, need {NEW_MARKETS_FOR_ANALYSIS})", "green", attrs=['bold'])
                else:
                    cprint(f"   ⏳ Collecting... (Have {fresh_eligible_count}, need {NEW_MARKETS_FOR_ANALYSIS})", "yellow")

                cprint(f"{'='*60}\n", "cyan")

            except KeyboardInterrupt:
                break
            except Exception as e:
                cprint(f"❌ Error in status display loop: {e}", "red")

    def analysis_cycle(self):
        """Check if we have enough eligible markets and run AI analysis"""
        cprint("\n" + "="*80, "magenta")
        cprint("🤖 ANALYSIS CYCLE CHECK", "magenta", attrs=['bold'])
        cprint(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "magenta")
        cprint("="*80 + "\n", "magenta")

        # Reload markets from CSV to get latest from collection thread
        with self.csv_lock:
            self.markets_df = self._load_markets()

        total_markets = len(self.markets_df)

        # 🌙 Moon Dev - Skip if no markets exist yet
        if total_markets == 0:
            cprint(f"\n⏳ No markets in database yet! WebSocket is collecting...", "yellow", attrs=['bold'])
            cprint(f"   First analysis will run when markets are collected\n", "yellow")
            return

        # 🌙 Moon Dev - Count markets with FRESH TRADES that are also ELIGIBLE for re-analysis
        now = datetime.now()
        cutoff_time = now - timedelta(hours=REANALYSIS_HOURS)

        fresh_eligible_count = 0
        for idx, row in self.markets_df.iterrows():
            last_analyzed = row.get('last_analyzed')
            last_trade = row.get('last_trade_timestamp')

            # Check if market is ELIGIBLE (never analyzed OR past threshold)
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

            # Check if market has FRESH TRADE (traded since last analysis run)
            has_fresh_trade = False
            if self.last_analysis_run_timestamp is None:
                # First run - all markets with trades are "fresh"
                has_fresh_trade = not pd.isna(last_trade) and last_trade is not None
            else:
                # Subsequent runs - only count if traded after last analysis
                try:
                    if not pd.isna(last_trade) and last_trade is not None:
                        trade_time = pd.to_datetime(last_trade)
                        last_run_time = pd.to_datetime(self.last_analysis_run_timestamp)
                        if trade_time > last_run_time:
                            has_fresh_trade = True
                except:
                    pass

            # Count if BOTH eligible AND has fresh trade
            if is_eligible and has_fresh_trade:
                fresh_eligible_count += 1

        is_first_run = (self.last_analysis_run_timestamp is None)

        cprint(f"📊 Market Analysis Status:", "cyan", attrs=['bold'])
        cprint(f"   Total markets in database: {total_markets}", "white")
        cprint(f"   Fresh eligible markets: {fresh_eligible_count}", "yellow" if fresh_eligible_count < NEW_MARKETS_FOR_ANALYSIS else "green", attrs=['bold'])
        cprint(f"   (Eligible markets with trades since last run)", "white")
        cprint("", "white")

        if is_first_run:
            cprint(f"🎬 FIRST ANALYSIS RUN", "yellow", attrs=['bold'])
            cprint(f"   Will analyze whatever markets we have collected (minimum 1)", "yellow")
            cprint(f"   Future runs will require {NEW_MARKETS_FOR_ANALYSIS} fresh eligible markets\n", "yellow")
        else:
            cprint(f"🎯 Analysis Trigger Requirement:", "cyan", attrs=['bold'])
            cprint(f"   Need: {NEW_MARKETS_FOR_ANALYSIS} fresh eligible markets", "white")
            cprint(f"   Have: {fresh_eligible_count} fresh eligible markets", "white")
            if fresh_eligible_count >= NEW_MARKETS_FOR_ANALYSIS:
                cprint(f"   ✅ REQUIREMENT MET - Running analysis!", "green", attrs=['bold'])
            else:
                cprint(f"   ❌ Need {NEW_MARKETS_FOR_ANALYSIS - fresh_eligible_count} more fresh eligible markets", "yellow", attrs=['bold'])
            cprint("", "white")

        # First run: analyze whatever we have (if at least 1 market)
        # Subsequent runs: wait for NEW_MARKETS_FOR_ANALYSIS fresh eligible markets
        should_analyze = (is_first_run and total_markets > 0) or (fresh_eligible_count >= NEW_MARKETS_FOR_ANALYSIS)

        if should_analyze:
            if is_first_run:
                cprint(f"\n✅ First run with {total_markets} markets! Running initial AI analysis...\n", "green", attrs=['bold'])
            else:
                cprint(f"\n✅ {fresh_eligible_count} fresh eligible markets! Running AI analysis...\n", "green", attrs=['bold'])

            # Display recent markets
            self.display_recent_markets()

            # Run AI predictions
            self.get_ai_predictions()

            # 🌙 Moon Dev - Update analysis run timestamp
            self.last_analysis_run_timestamp = datetime.now().isoformat()
            self.last_analyzed_count = total_markets
            cprint(f"\n💾 Updated analysis tracker: {self.last_analyzed_count} markets in database", "green")
            cprint(f"⏰ Next run will only count markets with fresh trades after {datetime.now().strftime('%H:%M:%S')}", "cyan")
        else:
            needed = NEW_MARKETS_FOR_ANALYSIS - fresh_eligible_count
            cprint(f"\n⏳ Need {needed} more fresh eligible markets before next analysis", "yellow")
            cprint(f"   Waiting for trades on eligible markets (never analyzed OR >{REANALYSIS_HOURS}h old)", "yellow")

        cprint("\n" + "="*80, "green")
        cprint("✅ Analysis check complete!", "green", attrs=['bold'])
        cprint("="*80 + "\n", "green")


    def analysis_loop(self):
        """🌙 Moon Dev - Continuously check for new markets to analyze (runs immediately!)"""
        cprint("\n🤖 ANALYSIS THREAD STARTED", "magenta", attrs=['bold'])
        cprint(f"🧠 Running first analysis NOW, then checking every {ANALYSIS_CHECK_INTERVAL_SECONDS} seconds\n", "magenta")

        # 🌙 Moon Dev - Run first analysis IMMEDIATELY (no waiting!)
        cprint("🚀 Moon Dev running first analysis immediately...\n", "yellow", attrs=['bold'])

        while True:
            try:
                self.analysis_cycle()

                # Show when next check will happen
                next_check = datetime.now() + timedelta(seconds=ANALYSIS_CHECK_INTERVAL_SECONDS)
                cprint(f"⏰ Next analysis check at: {next_check.strftime('%H:%M:%S')}\n", "magenta")

                time.sleep(ANALYSIS_CHECK_INTERVAL_SECONDS)
            except KeyboardInterrupt:
                break
            except Exception as e:
                cprint(f"❌ Error in analysis loop: {e}", "red")
                import traceback
                traceback.print_exc()
                time.sleep(ANALYSIS_CHECK_INTERVAL_SECONDS)


def main():
    """🌙 Moon Dev Main - WebSocket real-time data + AI analysis threads"""
    cprint("\n" + "="*80, "cyan")
    cprint("🌙 Moon Dev's Polymarket Agent - WebSocket Edition!", "cyan", attrs=['bold'])
    cprint("="*80, "cyan")
    cprint(f"💰 Tracking trades over ${MIN_TRADE_SIZE_USD}", "yellow")
    cprint(f"🚫 Ignoring prices within {IGNORE_PRICE_THRESHOLD:.2f} of $0 or $1", "yellow")
    cprint(f"🚫 Filtering out crypto/Bitcoin markets ({len(IGNORE_CRYPTO_KEYWORDS)} keywords)", "red")
    cprint(f"🚫 Filtering out sports markets ({len(IGNORE_SPORTS_KEYWORDS)} keywords)", "red")
    cprint(f"📜 Lookback period: {LOOKBACK_HOURS} hours (fetches historical data on startup)", "yellow")
    cprint("", "yellow")
    cprint("🔄 REAL-TIME WebSocket MODE:", "green", attrs=['bold'])
    cprint(f"   🌐 WebSocket: {WEBSOCKET_URL}", "cyan")
    cprint(f"   📊 Status Display: Every 30s - Shows collection stats", "cyan")
    cprint(f"   🤖 Analysis Thread: Every {ANALYSIS_CHECK_INTERVAL_SECONDS}s - Checks for new markets", "magenta")
    cprint(f"   🎯 AI Analysis triggers when {NEW_MARKETS_FOR_ANALYSIS} new markets collected", "yellow")
    cprint("", "yellow")
    cprint(f"🤖 AI Mode: {'SWARM (6 models)' if USE_SWARM_MODE else 'Single Model'}", "yellow")
    cprint(f"💰 Price Info to AI: {'ENABLED' if SEND_PRICE_INFO_TO_AI else 'DISABLED'}", "green" if SEND_PRICE_INFO_TO_AI else "yellow")
    cprint("", "yellow")
    cprint("📁 Data Files:", "cyan", attrs=['bold'])
    cprint(f"   Markets: {MARKETS_CSV}", "white")
    cprint(f"   Predictions: {PREDICTIONS_CSV}", "white")
    cprint("="*80 + "\n", "cyan")

    # Initialize agent
    agent = PolymarketAgent()

    # 🌙 Moon Dev - Fetch historical trades on startup to populate database
    cprint("\n" + "="*80, "yellow")
    cprint(f"📜 Moon Dev fetching historical data from last {LOOKBACK_HOURS} hours...", "yellow", attrs=['bold'])
    cprint("="*80, "yellow")

    historical_trades = agent.fetch_historical_trades()
    if historical_trades:
        cprint(f"\n📦 Processing {len(historical_trades)} historical trades...", "cyan")
        agent.process_trades(historical_trades)
        cprint(f"✅ Database populated with {len(agent.markets_df)} markets", "green")
    else:
        cprint("⚠️ No historical trades found - will start fresh from WebSocket", "yellow")

    cprint("="*80 + "\n", "yellow")

    # Connect WebSocket (runs in its own thread)
    agent.connect_websocket()

    # Create threads for status display and analysis
    status_thread = threading.Thread(target=agent.status_display_loop, daemon=True, name="Status")
    analysis_thread = threading.Thread(target=agent.analysis_loop, daemon=True, name="Analysis")

    # Start threads
    try:
        cprint("🚀 Moon Dev starting threads...\n", "green", attrs=['bold'])
        status_thread.start()
        analysis_thread.start()

        # Keep main thread alive
        cprint("✨ Moon Dev WebSocket + AI running! Press Ctrl+C to stop.\n", "green", attrs=['bold'])
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        cprint("\n\n" + "="*80, "yellow")
        cprint("⚠️ Moon Dev Polymarket Agent stopped by user", "yellow", attrs=['bold'])
        cprint("="*80 + "\n", "yellow")
        sys.exit(0)


if __name__ == "__main__":
    main()
