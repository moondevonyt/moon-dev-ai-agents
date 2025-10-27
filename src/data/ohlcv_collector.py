"""
🌙 Moon Dev's OHLCV Data Collector
Collects Open-High-Low-Close-Volume data for specified tokens
Built with love by Moon Dev 🚀
"""

from src.config import *
from src import nice_funcs as n
from src import nice_funcs_hyperliquid as hl
from src import nice_funcs_aster as aster
import pandas as pd
from datetime import datetime
import os
from termcolor import colored, cprint
import time

def collect_token_data(token, days_back=DAYSBACK_4_DATA, timeframe=DATA_TIMEFRAME, exchange="SOLANA"):
    """Collect OHLCV data for a single token

    Args:
        token: Token symbol (BTC, ETH) for Aster/HyperLiquid OR contract address for Solana
        days_back: Days of historical data to fetch
        timeframe: Candle timeframe (1m, 5m, 15m, 1H, etc.)
        exchange: "SOLANA", "ASTER", or "HYPERLIQUID"
    """
    cprint(f"\n🤖 Moon Dev's AI Agent fetching data for {token}...", "white", "on_blue")

    try:
        # Calculate number of bars based on timeframe and days
        bars_per_day = {
            '1m': 1440, '3m': 480, '5m': 288, '15m': 96, '30m': 48,
            '1H': 24, '2H': 12, '4H': 6, '6H': 4, '8H': 3, '12H': 2,
            '1h': 24, '2h': 12, '4h': 6, '6h': 4, '8h': 3, '12h': 2,  # lowercase versions
            '1D': 1, '3D': 1/3, '1W': 1/7, '1M': 1/30,
            '1d': 1, '3d': 1/3, '1w': 1/7, '1month': 1/30  # lowercase versions
        }

        bars_needed = int(days_back * bars_per_day.get(timeframe, 24))  # Default to hourly if unknown
        cprint(f"📊 Calculating bars: {days_back} days × {timeframe} = {bars_needed} bars", "cyan")

        # Convert timeframe to HyperLiquid format (lowercase h for hours)
        hl_timeframe = timeframe.replace('H', 'h').replace('D', 'd').replace('W', 'w').replace('M', 'month')
        if hl_timeframe != timeframe:
            cprint(f"🔄 Converting timeframe: {timeframe} → {hl_timeframe} (for HyperLiquid)", "yellow")

        # Route to appropriate data source based on exchange
        if exchange == "HYPERLIQUID":
            # Use HyperLiquid API
            cprint(f"🏦 Using HyperLiquid API for {token}", "cyan")
            data = hl.get_data(symbol=token, timeframe=hl_timeframe, bars=bars_needed, add_indicators=True)
        elif exchange == "ASTER":
            # Use HyperLiquid API for Aster symbols too (same symbols, same data)
            cprint(f"🏦 Using HyperLiquid API for {token} (Aster symbols)", "cyan")
            data = hl.get_data(symbol=token, timeframe=hl_timeframe, bars=bars_needed, add_indicators=True)
        else:
            # Default: Use Solana/Birdeye API
            cprint(f"🏦 Using Solana/Birdeye API for {token}", "cyan")
            data = n.get_data(token, days_back, timeframe)

        if data is None or data.empty:
            cprint(f"❌ Moon Dev's AI Agent couldn't fetch data for {token}", "white", "on_red")
            return None

        cprint(f"📊 Moon Dev's AI Agent processed {len(data)} candles for analysis", "white", "on_blue")
        
        # Save data if configured
        if SAVE_OHLCV_DATA:
            save_path = f"data/{token}_latest.csv"
        else:
            save_path = f"temp_data/{token}_latest.csv"
            
        # Ensure directory exists
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        # Save to CSV
        data.to_csv(save_path)
        cprint(f"💾 Moon Dev's AI Agent cached data for {token[:4]}", "white", "on_green")
        
        return data
        
    except Exception as e:
        cprint(f"❌ Moon Dev's AI Agent encountered an error: {str(e)}", "white", "on_red")
        return None

def collect_all_tokens(tokens=None, days_back=None, timeframe=None, exchange="SOLANA"):
    """
    Collect OHLCV data for all monitored tokens

    Args:
        tokens: List of token symbols (BTC, ETH for Aster/HyperLiquid) OR addresses (for Solana)
        days_back: Days of historical data (defaults to DAYSBACK_4_DATA from config)
        timeframe: Bar timeframe (defaults to DATA_TIMEFRAME from config)
        exchange: "SOLANA", "ASTER", or "HYPERLIQUID"
    """
    market_data = {}

    # Use defaults from config if not provided
    if tokens is None:
        tokens = MONITORED_TOKENS
    if days_back is None:
        days_back = DAYSBACK_4_DATA
    if timeframe is None:
        timeframe = DATA_TIMEFRAME

    cprint("\n🔍 Moon Dev's AI Agent starting market data collection...", "white", "on_blue")
    cprint(f"🏦 Exchange: {exchange}", "cyan")
    cprint(f"📊 Settings: {days_back} days @ {timeframe} timeframe", "cyan")

    for token in tokens:
        data = collect_token_data(token, days_back, timeframe, exchange=exchange)
        if data is not None:
            market_data[token] = data

    cprint("\n✨ Moon Dev's AI Agent completed market data collection!", "white", "on_green")

    return market_data

if __name__ == "__main__":
    try:
        collect_all_tokens()
    except KeyboardInterrupt:
        print("\n👋 Moon Dev OHLCV Collector shutting down gracefully...")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("🔧 Moon Dev suggests checking the logs and trying again!") 