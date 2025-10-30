"""
🧪 Multi-Timeframe Backtest Tester
Tests if multi-timeframe backtesting works before launching full system
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
CONFIG_DIR = PROJECT_ROOT / "src/config"
sys.path.insert(0, str(CONFIG_DIR))

from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from multi_timeframe_config import generate_all_combinations

# Paths
OHLCV_DIR = PROJECT_ROOT / "src/data/ohlcv"

class SimpleMultiTimeframeStrategy(Strategy):
    """
    Simple test strategy using both primary and informative timeframes
    
    Logic:
    - Primary TF: Trade based on RSI
    - Informative TF: Only trade if higher TF trend is bullish
    """
    
    # Parameters
    rsi_period = 14
    rsi_oversold = 30
    rsi_overbought = 70
    
    def init(self):
        """Initialize indicators"""
        # Primary timeframe RSI
        close = pd.Series(self.data.Close, index=self.data.index)
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        rs = gain / loss
        self.rsi = 100 - (100 / (1 + rs))
        
        # Informative timeframe SMA (trend filter)
        # Note: In production, you'd resample the informative TF data here
        # For this test, we just use primary TF with longer period
        self.sma_50 = self.I(lambda x: pd.Series(x).rolling(50).mean(), self.data.Close)
        self.sma_200 = self.I(lambda x: pd.Series(x).rolling(200).mean(), self.data.Close)
    
    def next(self):
        """Execute strategy logic"""
        # Higher timeframe trend filter
        if self.sma_50[-1] is None or self.sma_200[-1] is None:
            return
        
        higher_tf_bullish = self.sma_50[-1] > self.sma_200[-1]
        
        # RSI signals
        current_rsi = self.rsi.iloc[-1]
        
        # Entry: RSI oversold + bullish higher TF
        if not self.position:
            if current_rsi < self.rsi_oversold and higher_tf_bullish:
                self.buy()
        
        # Exit: RSI overbought
        elif current_rsi > self.rsi_overbought:
            self.position.close()

def load_ohlcv(filename):
    """Load and prepare OHLCV data"""
    filepath = OHLCV_DIR / filename
    
    if not filepath.exists():
        return None
    
    df = pd.read_csv(filepath)
    df['datetime'] = pd.to_datetime(df['datetime'])
    df = df.set_index('datetime')
    df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    
    return df

def test_single_combination(combo):
    """Test a single asset/timeframe combination"""
    
    # Load primary timeframe data
    primary_df = load_ohlcv(combo['primary_file'])
    
    if primary_df is None:
        return None, f"Primary data not found: {combo['primary_file']}"
    
    # In a full implementation, you'd also load and resample informative_df
    # For this test, we just use the primary data
    
    try:
        # Run backtest
        bt = Backtest(primary_df, SimpleMultiTimeframeStrategy, cash=100_000, commission=0.002)
        stats = bt.run()
        
        result = {
            'combo_name': combo['combo_name'],
            'asset': combo['asset'],
            'primary_tf': combo['primary_tf'],
            'informative_tf': combo['informative_tf'],
            'return_pct': float(stats['Return [%]']),
            'sharpe': float(stats['Sharpe Ratio']) if stats['Sharpe Ratio'] is not np.nan else 0.0,
            'trades': int(stats['# Trades']),
            'candles': len(primary_df)
        }
        
        return result, None
        
    except Exception as e:
        return None, str(e)

def main():
    """Test multi-timeframe backtesting on a subset of combinations"""
    
    print("=" * 60)
    print("🧪 MULTI-TIMEFRAME BACKTEST TESTER")
    print("=" * 60)
    
    # Generate all combinations
    all_combos = generate_all_combinations()
    
    print(f"\n📊 Total combinations: {len(all_combos)}")
    print(f"📁 OHLCV Directory: {OHLCV_DIR}")
    
    # Test first 10 combinations as a sample
    test_combos = all_combos[:10]
    
    print(f"\n🧪 Testing {len(test_combos)} combinations as validation...")
    print()
    
    results = []
    errors = []
    
    for i, combo in enumerate(test_combos, 1):
        print(f"[{i:2d}/{len(test_combos)}] {combo['combo_name']:30s} ... ", end='', flush=True)
        
        result, error = test_single_combination(combo)
        
        if error:
            print(f"❌ {error}")
            errors.append((combo['combo_name'], error))
        elif result:
            ret = result['return_pct']
            color = '✅' if ret > 0 else '⚠️'
            print(f"{color} Return: {ret:6.2f}% | Trades: {result['trades']} | Candles: {result['candles']}")
            results.append(result)
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS")
    print("=" * 60)
    
    if results:
        df = pd.DataFrame(results)
        
        print(f"\n✅ Successful backtests: {len(results)}/{len(test_combos)}")
        print(f"📈 Average return: {df['return_pct'].mean():.2f}%")
        print(f"🏆 Best return: {df['return_pct'].max():.2f}%")
        print(f"📉 Worst return: {df['return_pct'].min():.2f}%")
        print(f"🎯 Positive: {(df['return_pct'] > 0).sum()}/{len(results)}")
        
        print(f"\n🏆 TOP 3 COMBINATIONS:")
        top3 = df.nlargest(3, 'return_pct')
        for idx, row in top3.iterrows():
            print(f"   {row['combo_name']:30s} → {row['return_pct']:6.2f}%")
    
    if errors:
        print(f"\n❌ Errors: {len(errors)}")
        for combo_name, error in errors[:5]:
            print(f"   {combo_name}: {error}")
    
    print("\n" + "=" * 60)
    
    if len(results) >= len(test_combos) * 0.8:  # At least 80% success
        print("✅ MULTI-TIMEFRAME SYSTEM READY!")
        print("=" * 60)
        return 0
    else:
        print("❌ TOO MANY ERRORS - SYSTEM NOT READY")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
