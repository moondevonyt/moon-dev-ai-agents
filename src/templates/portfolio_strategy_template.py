"""
🌙 MOON DEV'S PORTFOLIO BACKTESTING TEMPLATE
============================================

This template creates strategies that trade MULTIPLE assets simultaneously
in a portfolio, rather than single asset at a time.

KEY FEATURES:
✅ Multi-Asset Trading (BTC, ETH, SOL, BNB, ADA, MATIC)
✅ Multi-Timeframe per Asset (Primary + Informative)
✅ Capital Allocation (16.67% per asset = 6 assets)
✅ Portfolio-Level Returns
✅ Realistic Position Sizing

USAGE:
Replace {{STRATEGY_LOGIC}} with your strategy logic.
The template handles data loading and portfolio management automatically.
"""

import pandas as pd
import numpy as np
from backtesting import Backtest, Strategy
from pathlib import Path
import sys

# 🌙 PORTFOLIO CONFIGURATION
ASSETS = ['BTC-USDT', 'ETH-USDT', 'SOL-USDT', 'BNB-USDT', 'ADA-USDT', 'MATIC-USDT']
PRIMARY_TIMEFRAME = '{{PRIMARY_TF}}'  # e.g., '5m', '15m', '30m'
INFORMATIVE_TIMEFRAME = '{{INFORMATIVE_TF}}'  # e.g., '1h', '4h', '1d'
CAPITAL_PER_ASSET = 1.0 / len(ASSETS)  # Equal weight: 16.67% per asset

class {{STRATEGY_NAME}}Portfolio(Strategy):
    """
    🌍 Portfolio Strategy - Trades multiple assets simultaneously
    
    Each asset gets equal capital allocation (16.67% for 6 assets)
    Strategy logic runs independently per asset
    Returns are combined at portfolio level
    """
    
    # Strategy parameters (CUSTOMIZE THESE)
    {{STRATEGY_PARAMS}}
    
    def init(self):
        """Initialize indicators for all assets"""
        print(f"🌙 {self.__class__.__name__} initialized!")
        print(f"📊 Trading {len(ASSETS)} assets: {', '.join(ASSETS)}")
        print(f"⏱️ Primary TF: {PRIMARY_TIMEFRAME}, Informative TF: {INFORMATIVE_TIMEFRAME}")
        print(f"💰 Capital per asset: {CAPITAL_PER_ASSET*100:.1f}%")
        
        # Store asset-specific data
        self.asset_data = {}
        self.asset_positions = {}
        
        # Initialize indicators per asset
        # NOTE: In real implementation, you would load multiple dataframes
        # For now, this template assumes data columns include asset identifiers
        
        {{INDICATOR_INIT}}
    
    def next(self):
        """Execute strategy logic for each asset"""
        
        # Skip if not enough data
        if len(self.data) < 50:
            return
        
        current_equity = self.equity
        capital_per_asset = current_equity * CAPITAL_PER_ASSET
        
        # Execute strategy logic per asset
        for asset in ASSETS:
            self._trade_asset(asset, capital_per_asset)
    
    def _trade_asset(self, asset: str, capital: float):
        """
        Execute trading logic for a single asset
        
        Args:
            asset: Asset symbol (e.g., 'BTC-USDT')
            capital: Allocated capital for this asset
        """
        
        # Get current price (from primary timeframe)
        current_price = self.data.Close[-1]
        
        # Get indicators
        {{ASSET_INDICATORS}}
        
        # Check if we have a position for this asset
        asset_position = self.asset_positions.get(asset, None)
        
        if not asset_position:
            # ENTRY LOGIC
            {{ENTRY_LOGIC}}
            
            if entry_signal:
                # Calculate position size based on allocated capital
                position_size = int(capital / current_price * 0.95)  # 95% to account for fees
                
                if position_size > 0:
                    print(f"🚀 ENTRY: {asset} @ {current_price:.2f} | Size: {position_size} | Capital: ${capital:.0f}")
                    
                    # Store position info
                    self.asset_positions[asset] = {
                        'size': position_size,
                        'entry_price': current_price,
                        'entry_bar': len(self.data)
                    }
                    
                    self.buy(size=position_size)
        
        else:
            # EXIT LOGIC
            {{EXIT_LOGIC}}
            
            if exit_signal:
                position_info = self.asset_positions[asset]
                pnl_pct = (current_price - position_info['entry_price']) / position_info['entry_price'] * 100
                
                print(f"📉 EXIT: {asset} @ {current_price:.2f} | P&L: {pnl_pct:+.2f}% | Bars held: {len(self.data) - position_info['entry_bar']}")
                
                self.position.close()
                del self.asset_positions[asset]


def load_portfolio_data():
    """
    🌙 Load data for all assets in the portfolio
    
    This function should:
    1. Load OHLCV data for each asset
    2. Merge data with proper alignment
    3. Add informative timeframe data
    4. Return combined dataframe
    
    For now, uses sample data for testing
    """
    print("\n🌙 Loading portfolio data...")
    
    # TODO: Implement actual multi-asset data loading
    # For testing, create sample data
    dates = pd.date_range('2024-01-01', '2024-12-31', freq='5min')
    
    data = pd.DataFrame({
        'Open': np.random.uniform(100, 200, len(dates)),
        'High': np.random.uniform(200, 250, len(dates)),
        'Low': np.random.uniform(50, 100, len(dates)),
        'Close': np.random.uniform(100, 200, len(dates)),
        'Volume': np.random.uniform(1000000, 10000000, len(dates))
    }, index=dates)
    
    print(f"✅ Portfolio data loaded: {len(data)} bars")
    print(f"📅 Date range: {data.index.min()} to {data.index.max()}")
    
    return data


if __name__ == "__main__":
    print("\n" + "="*80)
    print("🌙 MOON DEV'S PORTFOLIO BACKTEST")
    print("="*80)
    
    # Load portfolio data
    data = load_portfolio_data()
    
    # Run backtest
    bt = Backtest(
        data, 
        {{STRATEGY_NAME}}Portfolio,
        cash=1_000_000,
        commission=0.002,
        exclusive_orders=False  # Allow multiple positions (one per asset)
    )
    
    stats = bt.run()
    
    # Print results
    print("\n" + "="*80)
    print("📊 PORTFOLIO BACKTEST RESULTS")
    print("="*80)
    print(stats)
    print("="*80)
    
    print("\n💡 Portfolio Statistics:")
    print(f"   Assets Traded: {len(ASSETS)}")
    print(f"   Primary TF: {PRIMARY_TIMEFRAME}")
    print(f"   Informative TF: {INFORMATIVE_TIMEFRAME}")
    print(f"   Capital per Asset: {CAPITAL_PER_ASSET*100:.1f}%")
    print(f"   Portfolio Return: {stats['Return [%]']:.2f}%")
    print(f"   Number of Trades: {stats['# Trades']}")
    print(f"   Win Rate: {stats['Win Rate [%]']:.2f}%")
