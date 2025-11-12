#!/usr/bin/env python3
"""
HYPERLIQUID VOLUME AGENT - SWARM EDITION
Made by Moon Dev

Autonomous agent that monitors top 15 Hyperliquid altcoins every 4 hours.
Uses AI swarm (via model_factory) to identify best trading opportunities.

The edge: Catch volume spikes BEFORE Crypto Twitter notices!
"""

import requests
import time
import csv
import os
import json
import sys
from datetime import datetime
from pathlib import Path
from termcolor import cprint

# Add project root to path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import Moon Dev's Swarm Agent
from src.agents.swarm_agent import SwarmAgent

# ============================================================================
# CONFIGURATION - Moon Dev
# ============================================================================
HYPERLIQUID_API = "https://api.hyperliquid.xyz/info"

# Data directory in proper location
DATA_DIR = os.path.join(project_root, "src/data/volume_agent")
VOLUME_LOG = os.path.join(DATA_DIR, "volume_history.csv")
ANALYSIS_LOG = os.path.join(DATA_DIR, "agent_analysis.jsonl")

CHECK_INTERVAL = 4 * 60 * 60  # 4 hours

# Exclude majors - we want altcoins only
EXCLUDED_TOKENS = ['BTC', 'ETH', 'SOL']
TOP_N = 15

# ============================================================================
# DATA FETCHING - Moon Dev
# ============================================================================

def get_all_tokens_volume():
    """Fetch all Hyperliquid tokens with volume data - Moon Dev"""
    try:
        payload = {"type": "metaAndAssetCtxs"}
        response = requests.post(HYPERLIQUID_API, json=payload, timeout=15)

        if response.status_code != 200:
            cprint(f"❌ API Error: {response.status_code}", "red")
            return []

        data = response.json()
        tokens = []

        universe = data[0].get('universe', [])
        contexts = data[1]

        for i, token_info in enumerate(universe):
            symbol = token_info.get('name', 'UNKNOWN')

            if i < len(contexts):
                ctx = contexts[i]
                mark_price = float(ctx.get('markPx', 0))
                volume_24h = float(ctx.get('dayNtlVlm', 0))
                funding = float(ctx.get('funding', 0))
                open_interest = float(ctx.get('openInterest', 0))
                prev_day_px = float(ctx.get('prevDayPx', mark_price))

                if prev_day_px > 0:
                    change_24h = ((mark_price - prev_day_px) / prev_day_px) * 100
                else:
                    change_24h = 0

                tokens.append({
                    'symbol': symbol,
                    'volume_24h': volume_24h,
                    'price': mark_price,
                    'change_24h': change_24h,
                    'funding_rate': funding * 100,
                    'open_interest': open_interest
                })

        return tokens

    except Exception as e:
        cprint(f"❌ Error fetching data: {e}", "red")
        return []

def get_top_altcoins():
    """Get top altcoins excluding BTC/ETH/SOL - Moon Dev"""
    tokens = get_all_tokens_volume()
    if not tokens:
        return []

    tokens_sorted = sorted(tokens, key=lambda x: x['volume_24h'], reverse=True)
    altcoins = [t for t in tokens_sorted if t['symbol'] not in EXCLUDED_TOKENS]

    return altcoins[:TOP_N]

# ============================================================================
# CHANGE CALCULATION - Moon Dev
# ============================================================================

def load_previous_snapshot():
    """Load the previous 4h snapshot from CSV - Moon Dev"""
    if not os.path.exists(VOLUME_LOG):
        return {}

    try:
        previous_data = {}

        with open(VOLUME_LOG, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

            if len(rows) == 0:
                return {}

            # Get the most recent check
            if len(rows) >= TOP_N:
                last_timestamp = rows[-1]['timestamp']

                for row in rows:
                    if row['timestamp'] == last_timestamp:
                        symbol = row['symbol']
                        previous_data[symbol] = {
                            'rank': int(row['rank']),
                            'volume_24h': float(row['volume_24h']),
                            'price': float(row['price']),
                            'change_24h': float(row['change_24h_pct'])
                        }

        return previous_data

    except Exception as e:
        cprint(f"⚠️ Error loading previous data: {e}", "yellow")
        return {}

def load_24h_snapshot():
    """Load snapshot from 24 hours ago (6 checks back) - Moon Dev"""
    if not os.path.exists(VOLUME_LOG):
        return {}

    try:
        snapshot_24h = {}

        with open(VOLUME_LOG, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

            if len(rows) == 0:
                return {}

            # Get all unique timestamps
            timestamps = sorted(list(set(row['timestamp'] for row in rows)))

            # Need at least 7 snapshots to go back 24h (6 intervals of 4h = 24h)
            if len(timestamps) < 7:
                return {}

            # Get timestamp from 6 checks ago (24h)
            target_timestamp = timestamps[-7]

            for row in rows:
                if row['timestamp'] == target_timestamp:
                    symbol = row['symbol']
                    snapshot_24h[symbol] = {
                        'volume_24h': float(row['volume_24h'])
                    }

        return snapshot_24h

    except Exception as e:
        cprint(f"⚠️ Error loading 24h data: {e}", "yellow")
        return {}

def calculate_changes(current_tokens, previous_data, data_24h=None):
    """Calculate 4-hour and 24-hour volume changes - Moon Dev"""
    changes = []

    for i, token in enumerate(current_tokens):
        symbol = token['symbol']
        current_rank = i + 1
        current_volume = token['volume_24h']

        change_info = {
            'symbol': symbol,
            'current_rank': current_rank,
            'current_volume': current_volume,
            'current_price': token['price'],
            'change_24h': token['change_24h'],
            'funding_rate': token['funding_rate'],
            'open_interest': token['open_interest'],
            'volume_change_4h': None,
            'volume_change_24h': None,
            'rank_change_4h': None,
            'is_new_entry': False
        }

        # Calculate 4H volume change
        if symbol in previous_data:
            prev_volume = previous_data[symbol]['volume_24h']
            prev_rank = previous_data[symbol]['rank']

            if prev_volume > 0:
                change_info['volume_change_4h'] = ((current_volume - prev_volume) / prev_volume) * 100

            change_info['rank_change_4h'] = prev_rank - current_rank
        else:
            change_info['is_new_entry'] = True

        # Calculate 24H volume change
        if data_24h and symbol in data_24h:
            vol_24h_ago = data_24h[symbol]['volume_24h']
            if vol_24h_ago > 0:
                change_info['volume_change_24h'] = ((current_volume - vol_24h_ago) / vol_24h_ago) * 100

        changes.append(change_info)

    return changes

# ============================================================================
# DATA LOGGING - Moon Dev
# ============================================================================

def initialize_data_dir():
    """Initialize data directory and CSV - Moon Dev"""
    os.makedirs(DATA_DIR, exist_ok=True)

    if not os.path.exists(VOLUME_LOG):
        with open(VOLUME_LOG, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'timestamp',
                'datetime',
                'rank',
                'symbol',
                'volume_24h',
                'price',
                'change_24h_pct',
                'funding_rate_pct',
                'open_interest'
            ])

def log_volume_snapshot(tokens):
    """Log current snapshot to CSV - Moon Dev"""
    timestamp = time.time()
    dt = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    with open(VOLUME_LOG, 'a', newline='') as f:
        writer = csv.writer(f)
        for rank, token in enumerate(tokens, 1):
            writer.writerow([
                timestamp,
                dt,
                rank,
                token['symbol'],
                f"{token['volume_24h']:.0f}",
                f"{token['price']:.6f}",
                f"{token['change_24h']:.2f}",
                f"{token['funding_rate']:.4f}",
                f"{token['open_interest']:.0f}"
            ])

def log_agent_analysis(changes, swarm_result):
    """Log agent analysis to JSONL - Moon Dev"""
    log_entry = {
        'timestamp': time.time(),
        'datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'changes': changes,
        'swarm_result': swarm_result
    }

    with open(ANALYSIS_LOG, 'a') as f:
        f.write(json.dumps(log_entry, default=str) + '\n')

# ============================================================================
# DISPLAY - Moon Dev
# ============================================================================

def format_volume(volume):
    """Format volume for display - Moon Dev"""
    if volume >= 1_000_000_000:
        return f"${volume/1_000_000_000:.2f}B"
    elif volume >= 1_000_000:
        return f"${volume/1_000_000:.2f}M"
    else:
        return f"${volume/1_000:.2f}K"

def display_changes(changes):
    """Display beautiful change report for the Data Dog - Moon Dev"""
    cprint("\n" + "=" * 170, "cyan", attrs=['bold'])
    cprint("📊 HYPERLIQUID TOP 15 ALTCOINS - COMPLETE MARKET VIEW 📊", "cyan", attrs=['bold'])
    cprint("=" * 170, "cyan", attrs=['bold'])

    # Header row
    header = (
        f"\n{'#':<4} "
        f"{'SYMBOL':<10} "
        f"{'PRICE':<14} "
        f"{'24H VOLUME':<16} "
        f"{'4H VOL Δ':<14} "
        f"{'24H PRICE Δ':<14} "
        f"{'RANK Δ':<12} "
        f"{'FUNDING':<12} "
        f"{'OPEN INT':<16} "
        f"{'SIGNALS':<30}"
    )
    cprint(header, "white", attrs=['bold'])
    print("─" * 170)

    for change in changes:
        rank = change['current_rank']
        symbol = change['symbol']
        price = f"${change['current_price']:.4f}" if change['current_price'] < 10 else f"${change['current_price']:.2f}"
        volume = format_volume(change['current_volume'])
        change_24h = change['change_24h']
        funding = change['funding_rate']
        oi = format_volume(change['open_interest'])

        # 4H Volume change with color
        if change['volume_change_4h'] is not None:
            vol_chg_4h = change['volume_change_4h']
            if vol_chg_4h > 0:
                vol_chg_str = f"+{vol_chg_4h:.1f}%"
                vol_color = "green"
            else:
                vol_chg_str = f"{vol_chg_4h:.1f}%"
                vol_color = "red"
        else:
            vol_chg_str = "NEW ENTRY"
            vol_color = "yellow"

        # 24H Price change with color
        if change_24h > 0:
            price_chg_str = f"+{change_24h:.2f}%"
            price_color = "green"
        else:
            price_chg_str = f"{change_24h:.2f}%"
            price_color = "red"

        # Rank change
        if change['rank_change_4h'] is not None:
            if change['rank_change_4h'] > 0:
                rank_chg = f"↑ +{change['rank_change_4h']}"
                rank_color = "green"
            elif change['rank_change_4h'] < 0:
                rank_chg = f"↓ {change['rank_change_4h']}"
                rank_color = "red"
            else:
                rank_chg = "→ 0"
                rank_color = "white"
        else:
            rank_chg = "NEW"
            rank_color = "yellow"

        # Funding color
        if funding > 0.01:
            fund_color = "yellow"
            fund_str = f"+{funding:.4f}%"
        elif funding < -0.01:
            fund_color = "magenta"
            fund_str = f"{funding:.4f}%"
        else:
            fund_color = "white"
            fund_str = f"{funding:.4f}%"

        # Signals - this is what catches Moon Dev's eye
        signals = []
        if change['is_new_entry']:
            signals.append("🆕NEW")
        if change['volume_change_4h'] and change['volume_change_4h'] > 50:
            signals.append("🔥VOL+50%")
        elif change['volume_change_4h'] and change['volume_change_4h'] > 20:
            signals.append("📈VOL+20%")
        if change['rank_change_4h'] and change['rank_change_4h'] >= 3:
            signals.append("⬆️CLIMB+3")
        if change_24h > 30:
            signals.append("🚀PUMP+30%")
        elif change_24h > 15:
            signals.append("💚PUMP+15%")

        signal_str = " ".join(signals) if signals else "─"
        signal_color = "yellow" if "🆕NEW" in signals else "green" if signals else "white"

        # Print row with proper spacing and colors
        print(f"{rank:<4} {symbol:<10} {price:<14} {volume:<16} ", end="")
        cprint(f"{vol_chg_str:<14}", vol_color, end=" ")
        cprint(f"{price_chg_str:<14}", price_color, end=" ")
        cprint(f"{rank_chg:<12}", rank_color, end=" ")
        cprint(f"{fund_str:<12}", fund_color, end=" ")
        print(f"{oi:<16} ", end="")
        cprint(signal_str, signal_color)

    cprint("\n" + "=" * 170, "cyan", attrs=['bold'])

    # Add a quick summary for the Data Dog
    cprint("\n🔍 MARKET SNAPSHOT:", "cyan", attrs=['bold'])
    new_entries = [c for c in changes if c['is_new_entry']]
    big_movers = [c for c in changes if c['change_24h'] > 20]
    vol_accelerators = [c for c in changes if c['volume_change_4h'] and c['volume_change_4h'] > 50]
    climbers = [c for c in changes if c['rank_change_4h'] and c['rank_change_4h'] >= 3]

    if new_entries:
        symbols = ", ".join([c['symbol'] for c in new_entries])
        cprint(f"   🆕 New Top-15 Entries: {symbols}", "yellow")
    if big_movers:
        symbols = ", ".join([f"{c['symbol']} ({c['change_24h']:+.1f}%)" for c in big_movers])
        cprint(f"   🚀 24H Big Movers (>20%): {symbols}", "green")
    if vol_accelerators:
        symbols = ", ".join([f"{c['symbol']} ({c['volume_change_4h']:+.1f}%)" for c in vol_accelerators])
        cprint(f"   🔥 Volume Accelerators (>50%): {symbols}", "green")
    if climbers:
        symbols = ", ".join([f"{c['symbol']} (↑{c['rank_change_4h']})" for c in climbers])
        cprint(f"   ⬆️  Rank Climbers (+3 or more): {symbols}", "green")
    if not (new_entries or big_movers or vol_accelerators or climbers):
        cprint("   ✅ Market steady - no major signals detected", "white")

    cprint("\n" + "=" * 170 + "\n", "cyan", attrs=['bold'])

# ============================================================================
# AI SWARM ANALYSIS - Moon Dev
# ============================================================================

def create_analysis_prompt(changes):
    """Create prompt for swarm agents - Moon Dev

    VOLUME ONLY - No price, no funding, no open interest.
    Pure volume analysis for the Data Dog.
    """

    prompt = """You are a VOLUME TRACKER analyzing Hyperliquid volume patterns.

Your ONLY job is to identify volume acceleration and momentum. DO NOT consider price, funding rates, or any other data.

Here is the current top 15 altcoins by 24H VOLUME with volume changes:

"""

    for change in changes:
        symbol = change['symbol']
        rank = change['current_rank']
        volume = format_volume(change['current_volume'])
        vol_chg_4h = change['volume_change_4h']
        vol_chg_24h = change['volume_change_24h']
        rank_chg = change['rank_change_4h']

        prompt += f"\n{rank}. {symbol}:\n"
        prompt += f"   - Current 24H Volume: {volume}\n"

        # 4H volume change
        if vol_chg_4h is not None:
            prompt += f"   - 4H Volume Change: {vol_chg_4h:+.1f}%\n"
        else:
            prompt += f"   - 4H Volume Change: NEW ENTRY (wasn't in top 15 last check)\n"

        # 24H volume change
        if vol_chg_24h is not None:
            prompt += f"   - 24H Volume Change: {vol_chg_24h:+.1f}%\n"
        else:
            prompt += f"   - 24H Volume Change: N/A (need more history)\n"

        # Rank movement
        if rank_chg is not None:
            if rank_chg > 0:
                prompt += f"   - Rank Movement: CLIMBED {rank_chg} spots\n"
            elif rank_chg < 0:
                prompt += f"   - Rank Movement: DROPPED {abs(rank_chg)} spots\n"
            else:
                prompt += f"   - Rank Movement: STABLE\n"
        else:
            prompt += f"   - Rank Movement: NEW ENTRY\n"

    prompt += """\n\nBased on VOLUME DATA ONLY, which token would you buy right now?

Consider ONLY:
- Volume acceleration (4H vs 24H trends)
- Absolute volume size (bigger = more liquidity/interest)
- Rank climbing patterns (gaining market share)
- New entries with strong volume
- Sustained volume growth vs flash spikes

Give your pick and explain your reasoning in 2-3 sentences. Focus EXCLUSIVELY on volume patterns."""

    return prompt

def run_swarm_analysis(changes):
    """Run swarm analysis - Moon Dev"""

    cprint("\n🤖 Running AI Swarm Analysis...\n", "cyan", attrs=['bold'])

    # Initialize swarm with Moon Dev's models
    swarm = SwarmAgent()

    # Create prompt
    prompt = create_analysis_prompt(changes)

    # Query the swarm
    result = swarm.query(prompt)

    return result

def display_swarm_results(result):
    """Display swarm analysis results for the Data Dog - Moon Dev"""

    cprint("\n" + "=" * 170, "green", attrs=['bold'])
    cprint("🧠 AI SWARM ANALYSIS - INDIVIDUAL RECOMMENDATIONS + CONSENSUS 🧠", "green", attrs=['bold'])
    cprint("=" * 170, "green", attrs=['bold'])

    # Show consensus FIRST - this is what Moon Dev wants to see immediately
    if "consensus_summary" in result:
        cprint("\n" + "─" * 170, "cyan")
        cprint("🎯 CONSENSUS RECOMMENDATION (ALL AIs AGREE):", "cyan", attrs=['bold'])
        cprint("─" * 170, "cyan")
        cprint(f"\n{result['consensus_summary']}\n", "green", attrs=['bold'])
        cprint("─" * 170 + "\n", "cyan")

    # Show individual responses - ALL OF THEM
    cprint("\n📋 INDIVIDUAL AI RECOMMENDATIONS:", "yellow", attrs=['bold'])
    cprint("─" * 170, "yellow")

    # Create reverse mapping for clean labels
    reverse_mapping = {}
    if "model_mapping" in result:
        for ai_num, provider in result["model_mapping"].items():
            reverse_mapping[provider.lower()] = ai_num

    # Sort by response time for Moon Dev to see fastest first
    sorted_responses = sorted(
        result["responses"].items(),
        key=lambda x: x[1].get("response_time", 999) if x[1].get("success") else 999
    )

    for i, (provider, data) in enumerate(sorted_responses, 1):
        if data["success"]:
            ai_label = reverse_mapping.get(provider, "")
            provider_name = provider.replace('_', ' ').upper()

            # Header for each AI
            cprint(f"\n{'═' * 170}", "yellow")
            if ai_label:
                cprint(f"💬 {ai_label}: {provider_name} (Response Time: {data['response_time']:.2f}s)", "yellow", attrs=['bold'])
            else:
                cprint(f"💬 {provider_name} (Response Time: {data['response_time']:.2f}s)", "yellow", attrs=['bold'])
            cprint(f"{'─' * 170}", "yellow")

            # The actual recommendation
            cprint(f"{data['response']}", "white")
            cprint(f"{'─' * 170}", "yellow")

    # Metadata summary
    if "metadata" in result:
        meta = result["metadata"]
        cprint(f"\n\n📊 SWARM STATS:", "blue", attrs=['bold'])
        cprint(f"   ✅ Successful Responses: {meta.get('successful_responses', 0)}/{meta.get('total_models', 0)}", "green")
        cprint(f"   ⏱️  Total Analysis Time: {meta.get('total_time', 0):.2f}s", "cyan")

    cprint("\n" + "=" * 170 + "\n", "green", attrs=['bold'])

def display_data_table(changes):
    """Display clean data table for human analysis - Moon Dev"""

    cprint("\n" + "=" * 170, "blue", attrs=['bold'])
    cprint("📊 TOP 15 DATA TABLE - RAW DATA FOR MOON DEV'S ANALYSIS 📊", "blue", attrs=['bold'])
    cprint("=" * 170, "blue", attrs=['bold'])

    # Header
    header = (
        f"\n{'RANK':<6}"
        f"{'SYMBOL':<12}"
        f"{'PRICE':<16}"
        f"{'24H VOLUME':<18}"
        f"{'4H VOL Δ':<16}"
        f"{'24H VOL Δ':<16}"
        f"{'24H PRICE Δ':<16}"
        f"{'FUNDING %':<14}"
        f"{'OPEN INT':<18}"
    )
    cprint(header, "white", attrs=['bold'])
    cprint("─" * 170, "blue")

    # Data rows
    for change in changes:
        rank = change['current_rank']
        symbol = change['symbol']
        price = f"${change['current_price']:.6f}" if change['current_price'] < 1 else f"${change['current_price']:.2f}"
        volume = format_volume(change['current_volume'])
        price_24h = change['change_24h']
        funding = change['funding_rate']
        oi = format_volume(change['open_interest'])

        # 4H Volume change
        if change['volume_change_4h'] is not None:
            vol_4h = f"{change['volume_change_4h']:+.2f}%"
        else:
            vol_4h = "NEW"

        # 24H Volume change
        if change['volume_change_24h'] is not None:
            vol_24h = f"{change['volume_change_24h']:+.2f}%"
        else:
            vol_24h = "N/A"

        # 24H Price change
        price_24h_str = f"{price_24h:+.2f}%"

        # Funding
        funding_str = f"{funding:+.4f}%"

        # Print row
        row = (
            f"{rank:<6}"
            f"{symbol:<12}"
            f"{price:<16}"
            f"{volume:<18}"
            f"{vol_4h:<16}"
            f"{vol_24h:<16}"
            f"{price_24h_str:<16}"
            f"{funding_str:<14}"
            f"{oi:<18}"
        )
        print(row)

    cprint("\n" + "=" * 170, "blue", attrs=['bold'])
    cprint("💡 Moon Dev Tip: Compare this data with AI consensus to find your edge!", "yellow", attrs=['bold'])
    cprint("=" * 170 + "\n", "blue", attrs=['bold'])

# ============================================================================
# MAIN LOOP - Moon Dev
# ============================================================================

def run_check():
    """Run one 4-hour check - Moon Dev"""

    cprint("\n" + "=" * 120, "magenta")
    cprint(f"🔄 VOLUME AGENT CHECK - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "magenta", attrs=['bold'])
    cprint("=" * 120 + "\n", "magenta")

    # 1. Fetch current top 15
    cprint("📡 Fetching Hyperliquid data...", "cyan")
    current_tokens = get_top_altcoins()

    if not current_tokens:
        cprint("❌ No data received", "red")
        return

    cprint(f"✅ Got top {len(current_tokens)} altcoins\n", "green")

    # 2. Load previous snapshots and calculate changes
    cprint("📊 Calculating 4-hour and 24-hour changes...", "cyan")
    previous_data = load_previous_snapshot()
    data_24h = load_24h_snapshot()
    changes = calculate_changes(current_tokens, previous_data, data_24h)
    cprint(f"✅ Calculated changes\n", "green")

    # 3. Display changes
    display_changes(changes)

    # 4. Run AI swarm analysis
    swarm_result = run_swarm_analysis(changes)

    # 5. Display full analysis
    display_swarm_results(swarm_result)

    # 6. Display data table for human analysis
    display_data_table(changes)

    # 7. Log everything
    cprint("💾 Logging data...", "cyan")
    log_volume_snapshot(current_tokens)
    log_agent_analysis(changes, swarm_result)
    cprint(f"✅ Logged to {DATA_DIR}/\n", "green")

    cprint("=" * 120, "magenta")
    cprint(f"✅ Check complete! Next check in 4 hours...", "green", attrs=['bold'])
    cprint("=" * 120 + "\n", "magenta")

def run_continuous():
    """Run agent every 4 hours - Moon Dev"""

    cprint("\n" + "=" * 120, "green")
    cprint("🤖 HYPERLIQUID VOLUME AGENT - SWARM EDITION 🤖", "green", attrs=['bold'])
    cprint("Made by Moon Dev", "yellow", attrs=['bold'])
    cprint("=" * 120, "green")
    cprint("\n⏰ Running every 4 hours", "cyan")
    cprint(f"💾 Data saved to: {DATA_DIR}/", "cyan")
    cprint("🎯 Goal: Catch volume pumps BEFORE Crypto Twitter!\n", "yellow")

    initialize_data_dir()

    iteration = 0

    try:
        while True:
            iteration += 1
            run_check()

            cprint(f"⏳ Sleeping for 4 hours... (Check #{iteration} complete)\n", "yellow")
            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        cprint("\n\n" + "=" * 120, "yellow")
        cprint("👋 Volume Agent stopped", "yellow", attrs=['bold'])
        cprint("=" * 120, "yellow")
        cprint(f"Total checks completed: {iteration}", "cyan")
        cprint(f"All data saved to: {DATA_DIR}/\n", "cyan")

# ============================================================================
# ENTRY POINT - Moon Dev
# ============================================================================

def main():
    """Main entry point - Moon Dev"""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        # Single run mode
        cprint("\n🤖 VOLUME AGENT - SINGLE RUN MODE 🤖\n", "cyan", attrs=['bold'])
        initialize_data_dir()
        run_check()
    else:
        # Continuous mode
        run_continuous()

if __name__ == "__main__":
    main()
