"""
🌙 MOON DEV'S PORTFOLIO BACKTESTING CONFIGURATION
=================================================

Configuration for multi-asset portfolio backtesting.

PORTFOLIO COMPOSITION:
- 6 Assets: BTC, ETH, SOL, BNB, ADA, MATIC
- Equal weight allocation: 16.67% per asset
- Multi-timeframe support per asset

TIMEFRAME COMBINATIONS:
- Primary: Fast execution timeframe (1m, 5m, 15m, 30m)
- Informative: Trend/filter timeframe (1h, 2h, 4h, 1d, 1w)
"""

# 🌍 PORTFOLIO ASSETS
PORTFOLIO_ASSETS = [
    'BTC-USDT',
    'ETH-USDT', 
    'SOL-USDT',
    'BNB-USDT',
    'ADA-USDT',
    'MATIC-USDT'
]

# ⏱️ PRIMARY TIMEFRAMES (Fast execution)
PRIMARY_TIMEFRAMES = [
    '1m',
    '5m',
    '15m',
    '30m'
]

# 📊 INFORMATIVE TIMEFRAMES (Trend filters)
INFORMATIVE_TIMEFRAMES = [
    '1h',
    '2h',
    '4h',
    '1d',
    '1w'
]

# 💰 CAPITAL ALLOCATION
EQUAL_WEIGHT = True  # If True, each asset gets equal weight
CUSTOM_WEIGHTS = {
    'BTC-USDT': 0.30,   # 30%
    'ETH-USDT': 0.25,   # 25%
    'SOL-USDT': 0.15,   # 15%
    'BNB-USDT': 0.15,   # 15%
    'ADA-USDT': 0.075,  # 7.5%
    'MATIC-USDT': 0.075 # 7.5%
}

# 🎯 PORTFOLIO TESTING MODES
PORTFOLIO_MODE = 'full'  # 'full' or 'single' or 'hybrid'
# - 'full': Only test full portfolio (all 6 assets)
# - 'single': Only test single assets (existing behavior)
# - 'hybrid': Test both full portfolio AND individual assets

# 🧪 BACKTEST DURATION OPTIONS
BACKTEST_DURATIONS = {
    'short': 90,      # 90 days (3 months)
    'medium': 180,    # 180 days (6 months)
    'long': 365,      # 365 days (1 year)
    'extended': 730   # 730 days (2 years)
}

DEFAULT_DURATION = 'long'  # Default: 1 year

def get_portfolio_combinations():
    """
    Generate all portfolio + timeframe combinations
    
    Returns list of dicts with:
    - assets: List of asset symbols
    - primary_tf: Primary timeframe
    - informative_tf: Informative timeframe
    - weights: Capital allocation weights
    - name: Combination name
    """
    combinations = []
    
    for primary_tf in PRIMARY_TIMEFRAMES:
        for info_tf in INFORMATIVE_TIMEFRAMES:
            # Skip if informative TF <= primary TF
            tf_order = ['1m', '5m', '15m', '30m', '1h', '2h', '4h', '1d', '1w']
            if tf_order.index(info_tf) <= tf_order.index(primary_tf):
                continue
            
            combo = {
                'assets': PORTFOLIO_ASSETS,
                'primary_tf': primary_tf,
                'informative_tf': info_tf,
                'weights': get_weights(),
                'name': f"Portfolio_{primary_tf}_{info_tf}",
                'num_assets': len(PORTFOLIO_ASSETS)
            }
            combinations.append(combo)
    
    return combinations

def get_weights():
    """Get capital allocation weights"""
    if EQUAL_WEIGHT:
        weight = 1.0 / len(PORTFOLIO_ASSETS)
        return {asset: weight for asset in PORTFOLIO_ASSETS}
    else:
        return CUSTOM_WEIGHTS

def get_duration_days(duration_key=None):
    """
    Get backtest duration in days
    
    Args:
        duration_key: 'short', 'medium', 'long', or 'extended'
    
    Returns:
        Number of days
    """
    if duration_key is None:
        duration_key = DEFAULT_DURATION
    
    return BACKTEST_DURATIONS.get(duration_key, 365)

# 📊 SUMMARY
if __name__ == "__main__":
    print("\n" + "="*80)
    print("🌙 MOON DEV'S PORTFOLIO CONFIGURATION")
    print("="*80)
    
    print(f"\n📊 Portfolio Composition:")
    print(f"   Assets: {len(PORTFOLIO_ASSETS)}")
    for asset in PORTFOLIO_ASSETS:
        weight = get_weights()[asset]
        print(f"   - {asset}: {weight*100:.2f}%")
    
    print(f"\n⏱️ Timeframe Options:")
    print(f"   Primary TFs: {', '.join(PRIMARY_TIMEFRAMES)}")
    print(f"   Informative TFs: {', '.join(INFORMATIVE_TIMEFRAMES)}")
    
    combos = get_portfolio_combinations()
    print(f"\n🔢 Total Combinations: {len(combos)}")
    print(f"   Example: {combos[0]['name']}")
    
    print(f"\n📅 Duration Options:")
    for key, days in BACKTEST_DURATIONS.items():
        months = days / 30
        print(f"   {key}: {days} days ({months:.1f} months)")
    
    print("\n" + "="*80)
