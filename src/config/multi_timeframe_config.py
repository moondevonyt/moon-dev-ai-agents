"""
🌍 Multi-Timeframe Backtest Configuration
BB1151's Advanced Multi-Asset Multi-Timeframe Setup
"""

# 6 Assets to test
ASSETS = [
    'BTC-USDT',
    'ETH-USDT',
    'SOL-USDT',
    'ADA-USDT',
    'XRP-USDT',
    'SUI-USDT'
]

# 4 Primary Timeframes (main chart)
PRIMARY_TIMEFRAMES = [
    '1m',   # 1 minute
    '5m',   # 5 minutes
    '15m',  # 15 minutes
    '30m',  # 30 minutes
]

# 5 Informative Timeframes (higher timeframe context)
INFORMATIVE_TIMEFRAMES = [
    '1h',    # 1 hour
    '2h',    # 2 hours
    '4h',    # 4 hours
    '1d',    # Daily
    '1w',    # Weekly
]

def generate_all_combinations():
    """
    Generate all 120 combinations of Asset × Primary TF × Informative TF
    
    Returns:
        list: List of dicts with keys: asset, primary_tf, informative_tf, filename
    """
    combinations = []
    
    for asset in ASSETS:
        for primary_tf in PRIMARY_TIMEFRAMES:
            for informative_tf in INFORMATIVE_TIMEFRAMES:
                combo = {
                    'asset': asset,
                    'primary_tf': primary_tf,
                    'informative_tf': informative_tf,
                    'primary_file': f"{asset}-{primary_tf}.csv",
                    'informative_file': f"{asset}-{informative_tf}.csv",
                    'combo_name': f"{asset}-{primary_tf}-{informative_tf}"
                }
                combinations.append(combo)
    
    return combinations

def get_all_required_files():
    """
    Get unique list of all OHLCV files needed
    
    Returns:
        set: Set of unique filenames
    """
    files = set()
    
    for asset in ASSETS:
        for tf in PRIMARY_TIMEFRAMES + INFORMATIVE_TIMEFRAMES:
            files.add(f"{asset}-{tf}.csv")
    
    return sorted(files)

def print_configuration():
    """Print configuration summary"""
    combos = generate_all_combinations()
    files = get_all_required_files()
    
    print("=" * 60)
    print("🌍 MULTI-TIMEFRAME CONFIGURATION")
    print("=" * 60)
    print(f"\n📊 Assets: {len(ASSETS)}")
    for asset in ASSETS:
        print(f"   - {asset}")
    
    print(f"\n⏱️  Primary Timeframes: {len(PRIMARY_TIMEFRAMES)}")
    for tf in PRIMARY_TIMEFRAMES:
        print(f"   - {tf}")
    
    print(f"\n📈 Informative Timeframes: {len(INFORMATIVE_TIMEFRAMES)}")
    for tf in INFORMATIVE_TIMEFRAMES:
        print(f"   - {tf}")
    
    print(f"\n🧪 Total Combinations per Strategy: {len(combos)}")
    print(f"   = {len(ASSETS)} assets × {len(PRIMARY_TIMEFRAMES)} primary × {len(INFORMATIVE_TIMEFRAMES)} informative")
    
    print(f"\n💾 Unique OHLCV Files Required: {len(files)}")
    print(f"   = {len(ASSETS)} assets × {len(PRIMARY_TIMEFRAMES) + len(INFORMATIVE_TIMEFRAMES)} timeframes")
    
    print(f"\n📋 Example Combinations:")
    for i, combo in enumerate(combos[:5], 1):
        print(f"   #{i}: {combo['combo_name']}")
    print(f"   ... and {len(combos) - 5} more")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    print_configuration()
    
    # Show all required files
    print("\n💾 ALL REQUIRED FILES:")
    for f in get_all_required_files():
        print(f"   - {f}")
