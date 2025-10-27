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
MIN_TRADE_SIZE_USD = 100  # Only track trades over this amount
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
NEW_MARKETS_FOR_ANALYSIS = 25  # Trigger analysis when we have 25 NEW unanalyzed markets
MARKETS_TO_ANALYZE = 25  # Number of recent markets to send to AI
MARKETS_TO_DISPLAY = 20  # Number of recent markets to print after each update

# AI Configuration
USE_SWARM_MODE = True  # Use swarm AI (multiple models) instead of single XAI model
AI_MODEL_PROVIDER = "xai"  # Model to use if USE_SWARM_MODE = False
AI_MODEL_NAME = "grok-2-fast-reasoning"  # Model name if not using swarm

# Data paths
DATA_FOLDER = os.path.join(project_root, "src/data/polymarket")
MARKETS_CSV = os.path.join(DATA_FOLDER, "markets.csv")
PREDICTIONS_CSV = os.path.join(DATA_FOLDER, "predictions.csv")

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
            'outcome', 'price', 'size_usd', 'first_seen'
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
        return pd.DataFrame(columns=[
            'analysis_timestamp', 'analysis_run_id', 'market_title', 'market_slug',
            'claude_prediction', 'openai_prediction', 'groq_prediction',
            'gemini_prediction', 'deepseek_prediction', 'xai_prediction',
            'ollama_prediction', 'consensus_prediction', 'num_models_responded'
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

        for market_id, trade in unique_markets.items():
            try:
                # Check if market already exists
                if market_id in self.markets_df['market_id'].values:
                    continue

                # Extract trade data from Polymarket API structure
                event_slug = trade.get('eventSlug', '')
                title = trade.get('title', 'Unknown Market')
                outcome = trade.get('outcome', '')
                price = float(trade.get('price', 0))
                size_usd = float(trade.get('size', 0))
                timestamp = trade.get('timestamp', '')

                # conditionId is the unique market identifier
                condition_id = trade.get('conditionId', '')

                # Add new market
                new_market = {
                    'timestamp': timestamp,
                    'market_id': condition_id,  # Use conditionId as unique identifier
                    'event_slug': event_slug,
                    'title': title,
                    'outcome': outcome,
                    'price': price,
                    'size_usd': size_usd,
                    'first_seen': datetime.now().isoformat()
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

        # Save if we added new markets
        if new_markets > 0:
            self._save_markets()

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
        cprint("="*80, "magenta")

        # Build prompt with market information
        markets_text = "\n\n".join([
            f"Market {i+1}:\n"
            f"Title: {row['title']}\n"
            f"Recent trade: ${row['size_usd']:,.2f} on {row['outcome']}\n"
            f"Link: https://polymarket.com/event/{row['event_slug']}"
            for i, (_, row) in enumerate(markets_to_analyze.iterrows())
        ])

        system_prompt = """You are a prediction market expert analyzing Polymarket markets.
For each market, provide your prediction in this exact format:

MARKET [number]: [decision]
Reasoning: [brief 1-2 sentence explanation]

Decision must be one of: YES, NO, or NO_TRADE
- YES means you would bet on the "Yes" outcome
- NO means you would bet on the "No" outcome
- NO_TRADE means you would not take a position

Be concise and focused on the most promising opportunities."""

        user_prompt = f"""Analyze these {len(markets_to_analyze)} Polymarket markets and provide your predictions:

{markets_text}

Provide predictions for each market in the specified format."""

        if USE_SWARM_MODE and self.swarm:
            # Use swarm mode - get predictions from multiple AIs
            cprint("\n🌊 Getting predictions from AI swarm (90s timeout per model)...\n", "cyan")

            # 🌙 Moon Dev - DEBUG: Show what we're sending to the swarm
            cprint("\n" + "="*80, "blue")
            cprint("🔍 MOON DEV DEBUG - SYSTEM PROMPT:", "blue", attrs=['bold'])
            cprint("="*80, "blue")
            cprint(system_prompt, "white")
            cprint("="*80 + "\n", "blue")

            cprint("="*80, "blue")
            cprint("🔍 MOON DEV DEBUG - USER PROMPT (first 500 chars):", "blue", attrs=['bold'])
            cprint("="*80, "blue")
            cprint(user_prompt[:500] + "...", "white")
            cprint(f"\n(Total prompt length: {len(user_prompt)} characters)", "yellow")
            cprint("="*80 + "\n", "blue")

            swarm_result = None
            try:
                cprint("📡 Moon Dev sending prompts to swarm...", "cyan")
                # Query the swarm (90 second timeout per model)
                swarm_result = self.swarm.query(
                    prompt=user_prompt,
                    system_prompt=system_prompt
                )
                cprint("✅ Moon Dev received swarm_result object!", "green")

            except Exception as timeout_error:
                # Handle timeout - some models may have responded before timeout
                error_str = str(timeout_error)
                if 'TimeoutError' in str(type(timeout_error)) or 'futures unfinished' in error_str:
                    cprint(f"⚠️ Swarm timeout: {error_str}", "yellow")
                    cprint("⏱️ Some models took too long - processing partial results...", "yellow")
                    # swarm_result might still have partial data
                else:
                    cprint(f"❌ Swarm error: {timeout_error}", "red")
                    import traceback
                    traceback.print_exc()
                    return

            try:
                # 🌙 Moon Dev - DEBUG: Show what we got back
                cprint("\n" + "="*80, "blue")
                cprint("🔍 MOON DEV DEBUG - SWARM RESULT:", "blue", attrs=['bold'])
                cprint("="*80, "blue")
                if swarm_result:
                    cprint(f"Type: {type(swarm_result)}", "white")
                    cprint(f"Keys: {swarm_result.keys() if isinstance(swarm_result, dict) else 'N/A'}", "white")
                    if isinstance(swarm_result, dict) and 'responses' in swarm_result:
                        cprint(f"Response models: {list(swarm_result['responses'].keys())}", "white")
                        for model_name, model_data in swarm_result['responses'].items():
                            status = "✅ SUCCESS" if model_data.get('success') else "❌ FAILED"
                            cprint(f"  {model_name}: {status}", "green" if model_data.get('success') else "red")
                            if not model_data.get('success'):
                                cprint(f"    Error: {model_data.get('error', 'Unknown')}", "red")
                else:
                    cprint("swarm_result is None!", "red")
                cprint("="*80 + "\n", "blue")

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

                cprint(f"✅ Received {len(successful_responses)} successful responses from swarm", "green")

                # Display individual AI responses
                cprint("\n" + "="*80, "yellow")
                cprint("🤖 Individual AI Predictions", "yellow", attrs=['bold'])
                cprint("="*80, "yellow")

                for model_name, model_data in swarm_result.get('responses', {}).items():
                    if model_data.get('success'):
                        cprint(f"\n{'='*80}", "cyan")
                        cprint(f"🤖 {model_name.upper()}", "cyan", attrs=['bold'])
                        cprint(f"{'='*80}", "cyan")
                        cprint(model_data.get('response', 'No response'), "white")
                    else:
                        cprint(f"\n⚠️ {model_name.upper()} failed: {model_data.get('error', 'Unknown error')}", "yellow")

                # Display consensus (calculated from successful responses only)
                cprint("\n" + "="*80, "green")
                cprint("🎯 CONSENSUS DECISION", "green", attrs=['bold'])
                cprint(f"Based on {len(successful_responses)} AI models", "green")
                cprint("="*80, "green")
                cprint(swarm_result.get('consensus', 'No consensus available'), "white")
                cprint("="*80 + "\n", "green")

                # Save predictions to database
                self._save_swarm_predictions(
                    analysis_run_id=analysis_run_id,
                    analysis_timestamp=analysis_timestamp,
                    markets=markets_to_analyze,
                    swarm_result=swarm_result
                )

            except Exception as e:
                cprint(f"❌ Error getting swarm predictions: {e}", "red")
                import traceback
                traceback.print_exc()
                return
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

            except Exception as e:
                cprint(f"❌ Error getting prediction: {e}", "red")

    def _save_swarm_predictions(self, analysis_run_id, analysis_timestamp, markets, swarm_result):
        """Save swarm predictions to CSV database

        Args:
            analysis_run_id: Unique ID for this analysis run
            analysis_timestamp: ISO timestamp of analysis
            markets: DataFrame of markets analyzed
            swarm_result: Dictionary containing swarm responses
        """
        try:
            cprint("\n💾 Saving predictions to database...", "cyan")

            # Extract individual model predictions from swarm result
            model_predictions = {}
            for model_name, model_data in swarm_result.get('responses', {}).items():
                if model_data.get('success'):
                    # Extract just the prediction (not full response)
                    response = model_data.get('response', '')
                    # Try to extract first line or first 100 chars as summary
                    prediction_summary = response.split('\n')[0][:100] if response else 'No response'
                    model_predictions[model_name] = prediction_summary
                else:
                    model_predictions[model_name] = 'FAILED'

            # Get consensus
            consensus = swarm_result.get('consensus', 'No consensus')
            consensus_summary = consensus.split('\n')[0][:200] if consensus else 'No consensus'

            # Create prediction record for this analysis run
            prediction_record = {
                'analysis_timestamp': analysis_timestamp,
                'analysis_run_id': analysis_run_id,
                'market_title': f"Analyzed {len(markets)} markets",
                'market_slug': 'batch_analysis',
                'claude_prediction': model_predictions.get('claude', 'N/A'),
                'openai_prediction': model_predictions.get('openai', 'N/A'),
                'groq_prediction': model_predictions.get('groq', 'N/A'),
                'gemini_prediction': model_predictions.get('gemini', 'N/A'),
                'deepseek_prediction': model_predictions.get('deepseek', 'N/A'),
                'xai_prediction': model_predictions.get('xai', 'N/A'),
                'ollama_prediction': model_predictions.get('ollama', 'N/A'),
                'consensus_prediction': consensus_summary,
                'num_models_responded': len([v for v in model_predictions.values() if v != 'FAILED'])
            }

            # Add to predictions DataFrame
            self.predictions_df = pd.concat([
                self.predictions_df,
                pd.DataFrame([prediction_record])
            ], ignore_index=True)

            # Save to CSV
            self._save_predictions()

            cprint(f"✅ Saved analysis run {analysis_run_id} to predictions database", "green")

        except Exception as e:
            cprint(f"❌ Error saving predictions: {e}", "red")
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
                new_markets = total_markets - self.last_analyzed_count

                cprint(f"\n{'='*60}", "cyan")
                cprint(f"📊 Moon Dev Status @ {datetime.now().strftime('%H:%M:%S')}", "cyan", attrs=['bold'])
                cprint(f"{'='*60}", "cyan")
                cprint(f"   WebSocket Connected: {'✅ YES' if self.ws_connected else '❌ NO'}", "green" if self.ws_connected else "red")
                cprint(f"   Total trades received: {self.total_trades_received}", "white")
                cprint(f"   Ignored crypto/bitcoin: {self.ignored_crypto_count}", "red")
                cprint(f"   Ignored sports: {self.ignored_sports_count}", "red")
                cprint(f"   Filtered trades (>=${MIN_TRADE_SIZE_USD}): {self.filtered_trades_count}", "yellow")
                cprint(f"   Total markets in database: {total_markets}", "white")
                cprint(f"   Already analyzed: {self.last_analyzed_count}", "white")
                cprint(f"   New unanalyzed: {new_markets}", "yellow" if new_markets < NEW_MARKETS_FOR_ANALYSIS else "green", attrs=['bold'])

                if new_markets >= NEW_MARKETS_FOR_ANALYSIS:
                    cprint(f"   ✅ Ready for analysis! (Have {new_markets}, need {NEW_MARKETS_FOR_ANALYSIS})", "green", attrs=['bold'])
                else:
                    cprint(f"   ⏳ Collecting... (Have {new_markets}, need {NEW_MARKETS_FOR_ANALYSIS})", "yellow")

                cprint(f"{'='*60}\n", "cyan")

            except KeyboardInterrupt:
                break
            except Exception as e:
                cprint(f"❌ Error in status display loop: {e}", "red")

    def analysis_cycle(self):
        """Check if we have enough new markets and run AI analysis"""
        cprint("\n" + "="*80, "magenta")
        cprint("🤖 ANALYSIS CYCLE CHECK", "magenta", attrs=['bold'])
        cprint(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "magenta")
        cprint("="*80 + "\n", "magenta")

        # Reload markets from CSV to get latest from collection thread
        with self.csv_lock:
            self.markets_df = self._load_markets()

        # Check how many new markets we have
        total_markets = len(self.markets_df)
        new_markets = total_markets - self.last_analyzed_count
        is_first_run = (self.last_analyzed_count == 0)

        cprint(f"📊 Market Analysis Status:", "cyan", attrs=['bold'])
        cprint(f"   Total markets in database: {total_markets}", "white")
        cprint(f"   Already analyzed (last run): {self.last_analyzed_count}", "white")
        cprint(f"   New unanalyzed markets: {new_markets}", "yellow" if new_markets < NEW_MARKETS_FOR_ANALYSIS else "green", attrs=['bold'])
        cprint("", "white")

        if is_first_run:
            cprint(f"🎬 FIRST ANALYSIS RUN", "yellow", attrs=['bold'])
            cprint(f"   Will analyze whatever markets we have collected (minimum 1)", "yellow")
            cprint(f"   Future runs will require {NEW_MARKETS_FOR_ANALYSIS} NEW markets\n", "yellow")
        else:
            cprint(f"🎯 Analysis Trigger Requirement:", "cyan", attrs=['bold'])
            cprint(f"   Need: {NEW_MARKETS_FOR_ANALYSIS} new markets", "white")
            cprint(f"   Have: {new_markets} new markets", "white")
            if new_markets >= NEW_MARKETS_FOR_ANALYSIS:
                cprint(f"   ✅ REQUIREMENT MET - Running analysis!", "green", attrs=['bold'])
            else:
                cprint(f"   ❌ Need {NEW_MARKETS_FOR_ANALYSIS - new_markets} more markets", "yellow", attrs=['bold'])
            cprint("", "white")

        # First run: analyze whatever we have (if at least 1 market)
        # Subsequent runs: wait for NEW_MARKETS_FOR_ANALYSIS
        should_analyze = (is_first_run and total_markets > 0) or (new_markets >= NEW_MARKETS_FOR_ANALYSIS)

        # 🌙 Moon Dev - Skip if no markets exist yet
        if total_markets == 0:
            cprint(f"\n⏳ No markets in database yet! WebSocket is collecting...", "yellow", attrs=['bold'])
            cprint(f"   First analysis will run when markets are collected\n", "yellow")
            return

        if should_analyze:
            if is_first_run:
                cprint(f"\n✅ First run with {total_markets} markets! Running initial AI analysis...\n", "green", attrs=['bold'])
            else:
                cprint(f"\n✅ {new_markets} new markets! Running AI analysis...\n", "green", attrs=['bold'])

            # Display recent markets
            self.display_recent_markets()

            # Run AI predictions
            self.get_ai_predictions()

            # Update the last analyzed count
            self.last_analyzed_count = total_markets
            cprint(f"\n💾 Updated analysis tracker: {self.last_analyzed_count} markets analyzed", "green")
        else:
            needed = NEW_MARKETS_FOR_ANALYSIS - new_markets
            cprint(f"\n⏳ Need {needed} more new markets before next analysis", "yellow")

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
