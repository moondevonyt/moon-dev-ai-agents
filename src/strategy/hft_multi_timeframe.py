"""
🌙 Moon Dev's High-Frequency Multi-Timeframe Trading Strategy

Architecture:
- 1h Timeframe: Informative (Trend Direction)
- 1m/5m Timeframe: Primary (Entry Signals)

Rules:
- 1h Bullish → Only LONG entries on 1m/5m
- 1h Bearish → Only SHORT entries on 1m/5m
- High win rate durch Trend-Alignment
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from termcolor import cprint
from pathlib import Path
import sys

# Add project root
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.trade_logger import get_trade_logger


class HFTMultiTimeframeStrategy:
    """High-Frequency Trading mit Multi-Timeframe Analysis"""
    
    def __init__(self, 
                 informative_timeframe: str = "1h",
                 primary_timeframe: str = "5m",
                 symbol: str = "BTC/USDT"):
        
        cprint("\n🚀 Initializing HFT Multi-Timeframe Strategy", "cyan", attrs=['bold'])
        
        self.informative_tf = informative_timeframe
        self.primary_tf = primary_timeframe
        self.symbol = symbol
        
        # Trade tracking
        self.trade_logger = get_trade_logger()
        self.hourly_trades = []
        
        # Current trend state
        self.current_1h_trend = None  # 'bullish', 'bearish', or None
        self.last_trend_update = None
        
        # Performance tracking
        self.hourly_stats = {
            'total_trades': 0,
            'winners': 0,
            'losers': 0,
            'total_pnl': 0.0
        }
        
        cprint(f"✅ HFT Strategy initialized", "green")
        cprint(f"   Informative: {self.informative_tf} (Trend Filter)", "white")
        cprint(f"   Primary: {self.primary_tf} (Execution)", "white")
        cprint(f"   Symbol: {self.symbol}", "white")
    
    def analyze_1h_trend(self, df_1h: pd.DataFrame) -> str:
        """
        Analyze 1h timeframe to determine trend direction
        
        Returns: 'bullish', 'bearish', or 'neutral'
        """
        
        if df_1h is None or len(df_1h) < 20:
            return 'neutral'
        
        latest = df_1h.iloc[-1]
        
        # Calculate indicators
        close = latest['close']
        
        # EMAs for trend
        ema_20 = df_1h['close'].rolling(20).mean().iloc[-1]
        ema_50 = df_1h['close'].rolling(50).mean().iloc[-1] if len(df_1h) >= 50 else ema_20
        
        # RSI
        rsi = self._calculate_rsi(df_1h['close'], period=14).iloc[-1]
        
        # Volume trend
        vol_ma = df_1h['volume'].rolling(20).mean().iloc[-1]
        current_vol = latest['volume']
        
        # Determine trend
        bullish_signals = 0
        bearish_signals = 0
        
        # 1. Price above EMAs
        if close > ema_20 and ema_20 > ema_50:
            bullish_signals += 2
        elif close < ema_20 and ema_20 < ema_50:
            bearish_signals += 2
        
        # 2. RSI
        if rsi > 55 and rsi < 75:  # Bullish but not overbought
            bullish_signals += 1
        elif rsi < 45 and rsi > 25:  # Bearish but not oversold
            bearish_signals += 1
        
        # 3. Volume confirmation
        if current_vol > vol_ma * 1.2:
            if close > df_1h['open'].iloc[-1]:
                bullish_signals += 1
            else:
                bearish_signals += 1
        
        # Decision
        if bullish_signals >= 3:
            trend = 'bullish'
        elif bearish_signals >= 3:
            trend = 'bearish'
        else:
            trend = 'neutral'
        
        # Log trend change
        if trend != self.current_1h_trend:
            color = 'green' if trend == 'bullish' else 'red' if trend == 'bearish' else 'yellow'
            cprint(f"\n📊 1H TREND CHANGED: {self.current_1h_trend or 'None'} → {trend.upper()}", color, attrs=['bold'])
            cprint(f"   Close: ${close:.2f} | EMA20: ${ema_20:.2f} | RSI: {rsi:.1f}", "white")
            
            self.current_1h_trend = trend
            self.last_trend_update = datetime.now()
        
        return trend
    
    def should_take_trade(self, 
                          signal_side: str,  # 'long' or 'short' from 1m/5m signal
                          features_1m: Dict) -> bool:
        """
        Determine if trade should be taken based on 1h trend alignment
        
        Args:
            signal_side: Trade direction from primary timeframe signal
            features_1m: Features from 1m/5m timeframe
        
        Returns:
            bool: True if trade aligns with 1h trend
        """
        
        # No trend = no trade
        if self.current_1h_trend is None or self.current_1h_trend == 'neutral':
            return False
        
        # Alignment check
        if self.current_1h_trend == 'bullish' and signal_side != 'long':
            cprint(f"   ❌ Skipped SHORT - 1h trend is BULLISH", "yellow")
            return False
        
        if self.current_1h_trend == 'bearish' and signal_side != 'short':
            cprint(f"   ❌ Skipped LONG - 1h trend is BEARISH", "yellow")
            return False
        
        # Additional filters from auto-improvements
        # AUTO-IMPROVEMENT FILTERS
        
        # 🌙 Auto-improvement: Avoid overextended entries
        rsi = features_1m.get('rsi', 50)
        if signal_side == 'long' and rsi > 75:
            cprint(f"   ❌ Skipped LONG - RSI {rsi:.1f} > 75 (overbought)", "yellow")
            return False
        if signal_side == 'short' and rsi < 25:
            cprint(f"   ❌ Skipped SHORT - RSI {rsi:.1f} < 25 (oversold)", "yellow")
            return False
        
        # 🌙 Auto-improvement: Avoid longs with high funding
        if signal_side == 'long' and features_1m.get('funding_rate', 0) > 1.0:
            cprint(f"   ❌ Skipped LONG - Funding {features_1m['funding_rate']:.2f}% > 1.0%", "yellow")
            return False
        
        # 🌙 Auto-improvement: Require stronger momentum
        if features_1m.get('momentum_zscore', 0) < 0.8:  # Lower threshold for HFT
            cprint(f"   ❌ Skipped - Momentum {features_1m['momentum_zscore']:.2f} < 0.8", "yellow")
            return False
        
        return True
    
    def generate_signal_1m(self, df_1m: pd.DataFrame) -> Optional[Tuple[str, Dict]]:
        """
        Generate trading signal from 1m/5m timeframe
        
        Returns: (side, features) or None
        """
        
        if df_1m is None or len(df_1m) < 20:
            return None
        
        latest = df_1m.iloc[-1]
        
        # Calculate features
        features = self._calculate_features_1m(df_1m)
        
        # Simple momentum breakout strategy
        # (In production, you'd have more sophisticated signals)
        
        # Check for bullish setup
        if (features['momentum_zscore'] > 1.0 and 
            features['rsi'] > 50 and features['rsi'] < 70 and
            features['volume_spike'] > 1.3):
            
            return ('long', features)
        
        # Check for bearish setup
        elif (features['momentum_zscore'] < -1.0 and 
              features['rsi'] < 50 and features['rsi'] > 30 and
              features['volume_spike'] > 1.3):
            
            return ('short', features)
        
        return None
    
    def execute_trade(self, 
                      side: str,
                      entry_price: float,
                      features: Dict,
                      reason: str = "") -> bool:
        """
        Execute a high-frequency trade
        
        Returns: True if trade was executed
        """
        
        # Position size (small for HFT)
        position_size = 0.01  # 0.01 BTC for example
        
        # Tight stop loss for HFT (0.5%)
        stop_loss_pct = 0.005
        
        # Quick take profit (1%)
        take_profit_pct = 0.01
        
        if side == 'long':
            stop_price = entry_price * (1 - stop_loss_pct)
            target_price = entry_price * (1 + take_profit_pct)
        else:
            stop_price = entry_price * (1 + stop_loss_pct)
            target_price = entry_price * (1 - take_profit_pct)
        
        cprint(f"\n🎯 EXECUTING {side.upper()}: {self.symbol}", "cyan", attrs=['bold'])
        cprint(f"   Entry: ${entry_price:.2f}", "white")
        cprint(f"   Stop: ${stop_price:.2f} | Target: ${target_price:.2f}", "white")
        cprint(f"   Size: {position_size} BTC", "white")
        
        # In production: Send order to exchange
        # For now, simulate
        
        # Add to hourly trades tracking
        self.hourly_trades.append({
            'timestamp': datetime.now(),
            'side': side,
            'entry_price': entry_price,
            'stop_price': stop_price,
            'target_price': target_price,
            'size': position_size,
            'features': features,
            'reason': reason
        })
        
        return True
    
    def _calculate_features_1m(self, df: pd.DataFrame) -> Dict:
        """Calculate features from 1m/5m data"""
        
        latest = df.iloc[-1]
        
        # Returns
        returns_5 = df['close'].pct_change(5).iloc[-1]
        returns_20 = df['close'].pct_change(20).iloc[-1]
        
        # Momentum z-score
        ret_mean = df['close'].pct_change().rolling(50).mean().iloc[-1]
        ret_std = df['close'].pct_change().rolling(50).std().iloc[-1]
        momentum_zscore = (returns_5 - ret_mean) / ret_std if ret_std > 0 else 0
        
        # RSI
        rsi = self._calculate_rsi(df['close'], period=14).iloc[-1]
        
        # Volume
        vol_ma = df['volume'].rolling(20).mean().iloc[-1]
        volume_spike = latest['volume'] / vol_ma if vol_ma > 0 else 1.0
        
        # Volatility
        volatility = df['close'].pct_change().rolling(20).std().iloc[-1]
        
        return {
            'momentum_zscore': momentum_zscore,
            'rsi': rsi,
            'volume_spike': volume_spike,
            'volatility': volatility,
            'returns_5': returns_5,
            'returns_20': returns_20,
            'funding_rate': 0.1  # Would fetch from exchange API
        }
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def check_hourly_performance(self) -> Dict:
        """
        Check performance of trades from last hour
        
        Returns: Stats dict with needs_improvement flag
        """
        
        if not self.hourly_trades:
            return {'needs_improvement': False}
        
        # Simulate exit for all trades (in production, track actual exits)
        wins = 0
        losses = 0
        total_pnl = 0.0
        
        for trade in self.hourly_trades:
            # Simulate outcome based on features
            # In production, you'd have actual exit prices
            
            # Simple simulation: Good features = likely win
            prob_win = 0.5
            if trade['features']['momentum_zscore'] > 1.5:
                prob_win = 0.7
            if trade['features']['rsi'] > 40 and trade['features']['rsi'] < 60:
                prob_win += 0.1
            
            is_winner = np.random.random() < prob_win
            
            if is_winner:
                wins += 1
                pnl = trade['size'] * trade['entry_price'] * 0.01  # 1% profit
            else:
                losses += 1
                pnl = trade['size'] * trade['entry_price'] * -0.005  # 0.5% loss
            
            total_pnl += pnl
        
        total = len(self.hourly_trades)
        win_rate = wins / total if total > 0 else 0
        
        stats = {
            'hour': datetime.now().strftime("%Y-%m-%d %H:00"),
            'total_trades': total,
            'winners': wins,
            'losers': losses,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'needs_improvement': win_rate < 0.50 or total_pnl < 0  # HFT needs >50% WR
        }
        
        cprint(f"\n{'='*60}", "cyan")
        cprint(f"📊 HOURLY PERFORMANCE REPORT", "cyan", attrs=['bold'])
        cprint(f"{'='*60}", "cyan")
        cprint(f"Time: {stats['hour']}", "white")
        cprint(f"Total Trades: {total}", "white")
        cprint(f"Win Rate: {win_rate:.1%}", "green" if win_rate >= 0.5 else "red")
        cprint(f"P&L: ${total_pnl:.2f}", "green" if total_pnl > 0 else "red")
        
        if stats['needs_improvement']:
            cprint(f"\n⚠️  POOR HOURLY PERFORMANCE - Triggering Improvement", "red", attrs=['bold'])
        else:
            cprint(f"\n✅ Good hourly performance", "green")
        
        cprint(f"{'='*60}\n", "cyan")
        
        return stats
    
    def reset_hourly(self):
        """Reset hourly tracking"""
        self.hourly_trades = []


def main():
    """Demo HFT Strategy"""
    
    strategy = HFTMultiTimeframeStrategy(
        informative_timeframe="1h",
        primary_timeframe="5m",
        symbol="BTC/USDT"
    )
    
    # Simulate 1h data (bullish trend)
    dates = pd.date_range(end=datetime.now(), periods=100, freq='1h')
    df_1h = pd.DataFrame({
        'close': np.linspace(50000, 52000, 100) + np.random.randn(100) * 100,
        'open': np.linspace(50000, 52000, 100) + np.random.randn(100) * 100,
        'volume': np.random.uniform(1000, 2000, 100)
    }, index=dates)
    
    # Analyze 1h trend
    trend = strategy.analyze_1h_trend(df_1h)
    
    # Simulate 5m signals
    df_5m = pd.DataFrame({
        'close': np.linspace(51900, 52100, 50) + np.random.randn(50) * 20,
        'open': np.linspace(51900, 52100, 50) + np.random.randn(50) * 20,
        'volume': np.random.uniform(100, 300, 50)
    })
    
    cprint(f"\n🎬 Simulating HFT trades for 1 hour...\n", "yellow")
    
    # Generate signals and trades
    for i in range(10):  # Simulate 10 potential signals
        signal = strategy.generate_signal_1m(df_5m)
        
        if signal:
            side, features = signal
            
            if strategy.should_take_trade(side, features):
                strategy.execute_trade(
                    side=side,
                    entry_price=52000 + np.random.randn() * 50,
                    features=features,
                    reason=f"HFT signal #{i+1}"
                )
    
    # Check hourly performance
    stats = strategy.check_hourly_performance()
    
    if stats['needs_improvement']:
        cprint("🔄 Would trigger hourly improvement cycle here", "cyan")


if __name__ == "__main__":
    main()
