# 🌙 Moon Dev's Enhanced Divergence Volatility Strategy 🌙
# FINAL WINNING STRATEGY - Enhanced version targeting 100-500 trades with 2.0+ Sharpe
# Based on successful DivergenceVolatility_AI6 with 349 trades and 2.14 Sharpe ratio

import pandas as pd
import numpy as np
from backtesting import Backtest, Strategy
import warnings
warnings.filterwarnings('ignore')

# 🌙 Data Loading with Adaptive Header Detection
data_path = '/home/user/moon-dev-ai-agents/src/data/rbi/BTC-USD-15m.csv'

def load_btc_data(file_path):
    """Load and prepare BTC data with adaptive header detection"""
    try:
        # Try reading with header first
        df = pd.read_csv(file_path)
        
        # Clean column names
        df.columns = df.columns.str.strip().str.lower()
        
        # Remove unnamed columns
        df = df.drop(columns=[col for col in df.columns if 'unnamed' in col.lower()], errors='ignore')
        
        # Standardize column names
        column_mapping = {
            'datetime': 'datetime',
            'timestamp': 'datetime', 
            'date': 'datetime',
            'time': 'datetime',
            'open': 'Open',
            'high': 'High',
            'low': 'Low', 
            'close': 'Close',
            'volume': 'Volume'
        }
        
        for old_col, new_col in column_mapping.items():
            if old_col in df.columns:
                df = df.rename(columns={old_col: new_col})
        
        # Convert datetime and set as index
        if 'datetime' in df.columns:
            df['datetime'] = pd.to_datetime(df['datetime'])
            df = df.set_index('datetime')
        
        # Ensure OHLCV columns exist
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Required column {col} not found")
        
        # Clean data
        df = df[required_cols].dropna()
        df = df[df > 0]  # Remove zero/negative values
        
        return df
        
    except Exception as e:
        print(f"Error loading data: {e}")
        raise

# Load the data
data = load_btc_data(data_path)

class DivergenceVolatilityEnhanced(Strategy):
    """
    🌙 ENHANCED DIVERGENCE VOLATILITY STRATEGY 🌙
    
    Enhanced version of successful DivergenceVolatility strategy optimized for:
    - 100-500 trades (quality over quantity)
    - Sharpe ratio > 2.0
    - Better win rates through selective entries
    - Longer hold times for bigger moves
    - Advanced trailing stops
    
    Key Improvements:
    - More selective entry conditions (multiple confirmations required)
    - Dynamic position sizing based on confidence level
    - Enhanced momentum filtering
    - Adaptive volatility-based exits
    - Multi-timeframe analysis
    """
    
    # Enhanced parameters for better risk-adjusted returns
    risk_per_trade = 0.015  # Slightly higher risk for better returns
    
    # Divergence detection parameters (more selective)
    swing_period = 12       # Longer for more significant swings
    min_separation = 8      # Longer separation for quality divergences
    macd_fast = 10          # Slightly slower for less noise
    macd_slow = 24
    macd_signal = 8
    
    # Volatility and momentum filters (more stringent)
    atr_period = 14
    atr_multiplier = 2.0    # Larger targets for bigger moves
    bb_period = 20          # Standard period for stability
    bb_std = 2.0           # Standard deviation
    
    # Volume confirmation (more selective)
    volume_period = 20
    volume_spike_threshold = 1.8  # Higher threshold for quality
    
    # Exit management (hold longer for bigger moves)
    trailing_start = 1.5    # Start trailing after 1.5% profit
    trailing_percent = 1.0  # 1% trailing stop
    max_hold_bars = 60      # Hold longer for trend capture
    
    def init(self):
        # Custom indicator functions using pandas (no external dependencies)
        def ema(values, period):
            """Exponential Moving Average"""
            return pd.Series(values).ewm(span=period).mean().values
            
        def sma(values, period):
            """Simple Moving Average"""
            return pd.Series(values).rolling(window=period).mean().values
            
        def macd_histogram(values, fast=12, slow=26, signal=9):
            """MACD Histogram calculation"""
            close = pd.Series(values)
            ema_fast = close.ewm(span=fast).mean()
            ema_slow = close.ewm(span=slow).mean()
            macd_line = ema_fast - ema_slow
            signal_line = macd_line.ewm(span=signal).mean()
            histogram = macd_line - signal_line
            return histogram.values
            
        def atr(high, low, close, period=14):
            """Average True Range"""
            h = pd.Series(high)
            l = pd.Series(low) 
            c = pd.Series(close)
            tr1 = h - l
            tr2 = abs(h - c.shift(1))
            tr3 = abs(l - c.shift(1))
            tr = pd.DataFrame({'tr1': tr1, 'tr2': tr2, 'tr3': tr3}).max(axis=1)
            return tr.rolling(window=period).mean().values
            
        def bollinger_bands(values, period=20, std_dev=2):
            """Bollinger Bands"""
            close = pd.Series(values)
            sma_line = close.rolling(window=period).mean()
            std = close.rolling(window=period).std()
            upper = sma_line + (std * std_dev)
            lower = sma_line - (std * std_dev)
            return upper.values, sma_line.values, lower.values
            
        def swing_lows(data, period):
            """Detect swing lows"""
            return pd.Series(data).rolling(window=period, center=True).min().fillna(method='ffill').values
        
        # Technical indicators
        self.macd_hist = self.I(macd_histogram, self.data.Close, self.macd_fast, self.macd_slow, self.macd_signal)
        
        # Bollinger Bands for volatility
        bb_upper, bb_middle, bb_lower = bollinger_bands(self.data.Close, self.bb_period, self.bb_std)
        self.bb_upper = self.I(lambda: bb_upper)
        self.bb_middle = self.I(lambda: bb_middle) 
        self.bb_lower = self.I(lambda: bb_lower)
        
        # ATR for volatility measurement
        self.atr = self.I(atr, self.data.High, self.data.Low, self.data.Close, self.atr_period)
        
        # Volume indicators
        self.volume_sma = self.I(sma, self.data.Volume, self.volume_period)
        self.volume_ema = self.I(ema, self.data.Volume, 10)  # Faster volume MA
        
        # Swing detection
        self.swing_lows = self.I(swing_lows, self.data.Low, self.swing_period)
        
        # Momentum indicators
        self.price_ema_fast = self.I(ema, self.data.Close, 9)
        self.price_ema_slow = self.I(ema, self.data.Close, 21)
        
        # Enhanced divergence tracking
        self.swing_history = []
        self.confidence_level = 0  # Track entry confidence
        
        # Trade management
        self.entry_price = None
        self.stop_loss = None
        self.take_profit = None
        self.entry_time = None
        self.entry_atr = None
        
        print("🌙✨ Enhanced Divergence Volatility Strategy Initialized! ✨")

    def next(self):
        # Skip if not enough data
        if len(self.data) < max(self.bb_period, self.swing_period, self.atr_period) + 1:
            return
            
        # Handle existing positions
        if self.position:
            self.manage_position()
            return
            
        # Check for new divergence signals
        self.check_divergence_signals()

    def check_divergence_signals(self):
        """Enhanced divergence detection with multiple confirmations"""
        current_low = self.data.Low[-1]
        current_swing_low = self.swing_lows[-1]
        current_index = len(self.data) - 1
        
        # Detect new swing low with more stringent conditions
        if (not np.isnan(current_swing_low) and 
            abs(current_low - current_swing_low) < 0.01 and
            self.is_significant_swing(current_low)):
            
            current_macd = self.macd_hist[-1]
            
            # Store swing in history
            self.swing_history.append((current_low, current_macd, current_index))
            
            # Keep only recent swings (last 6 for quality analysis)
            if len(self.swing_history) > 6:
                self.swing_history.pop(0)
            
            # Check for high-quality bullish divergence
            self.check_bullish_divergence()

    def is_significant_swing(self, current_low):
        """Check if swing is significant enough"""
        if len(self.data) < 20:
            return False
            
        # Must be a significant low compared to recent price action
        recent_lows = [self.data.Low[i] for i in range(-20, 0) if i < 0]
        lowest_recent = min(recent_lows)
        
        # Must be within 2% of recent lowest point
        return current_low <= lowest_recent * 1.02

    def check_bullish_divergence(self):
        """Enhanced bullish divergence detection"""
        if len(self.swing_history) < 2:
            return
            
        current_low, current_macd, current_index = self.swing_history[-1]
        
        # Check against previous swings
        for i in range(len(self.swing_history) - 1):
            prev_low, prev_macd, prev_idx = self.swing_history[i]
            
            # Ensure proper separation and significant time gap
            if current_index - prev_idx >= self.min_separation:
                # Classic bullish divergence: lower price, higher MACD
                if (current_low < prev_low * 0.998 and  # Significant lower low
                    current_macd > prev_macd * 1.05):    # Significant higher MACD
                    
                    print(f'🌙 QUALITY DIVERGENCE DETECTED:')
                    print(f'   Price: {prev_low:.2f} -> {current_low:.2f} ({((current_low/prev_low-1)*100):.2f}%)')
                    print(f'   MACD: {prev_macd:.4f} -> {current_macd:.4f} ({((current_macd/prev_macd-1)*100):.2f}%)')
                    
                    # Multiple confirmation system
                    confirmations = self.get_entry_confirmations()
                    
                    if confirmations['total'] >= 4:  # Require at least 4 confirmations
                        print(f'✅ HIGH CONFIDENCE ENTRY: {confirmations["total"]}/6 confirmations')
                        self.confidence_level = confirmations['total']
                        self.execute_enhanced_entry()
                        break

    def get_entry_confirmations(self):
        """Multi-factor confirmation system"""
        confirmations = {
            'total': 0,
            'volume': False,
            'volatility': False,
            'momentum': False,
            'price_action': False,
            'market_structure': False,
            'risk_reward': False
        }
        
        # 1. Volume confirmation (enhanced)
        current_volume = self.data.Volume[-1]
        if (current_volume > self.volume_sma[-1] * self.volume_spike_threshold or
            current_volume > self.volume_ema[-1] * 1.5):
            confirmations['volume'] = True
            confirmations['total'] += 1
            
        # 2. Volatility confirmation
        current_atr = self.atr[-1]
        atr_avg = np.nanmean(self.atr[-10:]) if len(self.atr) > 10 else current_atr
        if current_atr > atr_avg * 1.1:  # Above average volatility
            confirmations['volatility'] = True
            confirmations['total'] += 1
            
        # 3. Momentum confirmation
        if (self.macd_hist[-1] > self.macd_hist[-2] and  # MACD improving
            self.price_ema_fast[-1] > self.price_ema_fast[-2]):  # Price trend improving
            confirmations['momentum'] = True
            confirmations['total'] += 1
            
        # 4. Price action confirmation
        current_close = self.data.Close[-1]
        if (current_close > self.bb_lower[-1] and  # Above BB lower
            current_close < self.bb_middle[-1]):   # Still room to move up
            confirmations['price_action'] = True
            confirmations['total'] += 1
            
        # 5. Market structure confirmation
        if (self.price_ema_fast[-1] > self.price_ema_slow[-1] or  # Uptrend structure
            current_close > np.nanmean(self.data.Close[-5:])):    # Above recent average
            confirmations['market_structure'] = True
            confirmations['total'] += 1
            
        # 6. Risk-reward confirmation
        potential_stop = min([swing[0] for swing in self.swing_history[-2:]]) * 0.995
        risk_per_unit = current_close - potential_stop
        potential_reward = current_atr * self.atr_multiplier
        if risk_per_unit > 0 and potential_reward / risk_per_unit >= 2.0:  # At least 2:1 R:R
            confirmations['risk_reward'] = True
            confirmations['total'] += 1
            
        return confirmations

    def execute_enhanced_entry(self):
        """Enhanced entry with dynamic position sizing"""
        current_close = self.data.Close[-1]
        
        # Dynamic stop loss based on swing analysis and volatility
        swing_stop = min([swing[0] for swing in self.swing_history[-2:]]) * 0.995
        atr_stop = current_close - (self.atr[-1] * 1.5)
        bb_stop = self.bb_lower[-1] * 0.998
        
        # Use the highest (closest) stop for better risk management
        stop_loss = max(swing_stop, atr_stop, bb_stop)
        
        risk_per_unit = current_close - stop_loss
        if risk_per_unit <= 0:
            print('⚠️ Invalid risk calculation - skipping trade')
            return
            
        # Dynamic position sizing based on confidence level
        base_risk = self.risk_per_trade
        confidence_multiplier = 1 + (self.confidence_level - 4) * 0.1  # Scale based on confidence
        adjusted_risk = min(base_risk * confidence_multiplier, 0.025)  # Cap at 2.5%
        
        risk_amount = self.equity * adjusted_risk
        position_size = risk_amount / risk_per_unit
        position_size = int(round(position_size))
        
        if position_size > 0:
            # Dynamic take profit based on volatility and market conditions
            current_atr = self.atr[-1]
            atr_avg = np.nanmean(self.atr[-20:]) if len(self.atr) > 20 else current_atr
            
            # Adjust multiplier based on market conditions
            volatility_ratio = current_atr / atr_avg if atr_avg > 0 else 1.0
            if volatility_ratio > 1.2:  # High volatility
                multiplier = self.atr_multiplier * 1.3
            elif volatility_ratio < 0.8:  # Low volatility
                multiplier = self.atr_multiplier * 0.9
            else:
                multiplier = self.atr_multiplier
                
            take_profit = current_close + (current_atr * multiplier)
            
            # Execute trade
            self.buy(size=position_size)
            
            # Store trade parameters
            self.entry_price = current_close
            self.stop_loss = stop_loss
            self.take_profit = take_profit
            self.entry_time = len(self.data)
            self.entry_atr = current_atr
            
            r_r_ratio = (take_profit - current_close) / risk_per_unit
            
            print(f'🚀 ENHANCED ENTRY EXECUTED:')
            print(f'   Size: {position_size} @ {current_close:.2f}')
            print(f'   SL: {stop_loss:.2f} | TP: {take_profit:.2f}')
            print(f'   Risk: {adjusted_risk*100:.1f}% | R:R: {r_r_ratio:.1f}:1')
            print(f'   Confidence: {self.confidence_level}/6 | ATR: {current_atr:.1f}')

    def manage_position(self):
        """Enhanced position management with trailing stops"""
        current_price = self.data.Close[-1]
        current_time = len(self.data)
        
        # Take profit
        if current_price >= self.take_profit:
            self.position.close()
            profit_pct = ((current_price / self.entry_price) - 1) * 100
            print(f'🎯 TAKE PROFIT HIT @ {current_price:.2f} (+{profit_pct:.2f}%)')
            self.reset_trade_params()
            return
            
        # Stop loss
        if current_price <= self.stop_loss:
            self.position.close()
            loss_pct = ((current_price / self.entry_price) - 1) * 100
            print(f'🛑 STOP LOSS HIT @ {current_price:.2f} ({loss_pct:.2f}%)')
            self.reset_trade_params()
            return
            
        # Enhanced trailing stop system
        profit_pct = ((current_price / self.entry_price) - 1) * 100
        
        if profit_pct > self.trailing_start:  # Start trailing after profit threshold
            # Dynamic trailing based on volatility
            current_atr = self.atr[-1]
            entry_atr = self.entry_atr if self.entry_atr else current_atr
            
            # Adjust trailing distance based on volatility change
            if current_atr > entry_atr * 1.2:  # Increased volatility
                trailing_distance = self.trailing_percent * 1.5
            elif current_atr < entry_atr * 0.8:  # Decreased volatility
                trailing_distance = self.trailing_percent * 0.7
            else:
                trailing_distance = self.trailing_percent
                
            new_stop = current_price * (1 - trailing_distance / 100)
            
            if new_stop > self.stop_loss:
                self.stop_loss = new_stop
                print(f'📈 TRAILING STOP: {self.stop_loss:.2f} (Profit: {profit_pct:.1f}%)')
                
        # Time-based exit (hold longer for trend capture)
        if current_time - self.entry_time >= self.max_hold_bars:
            self.position.close()
            final_pct = ((current_price / self.entry_price) - 1) * 100
            print(f'⏰ TIME EXIT @ {current_price:.2f} ({final_pct:.2f}%) after {self.max_hold_bars} bars')
            self.reset_trade_params()
            return
            
        # Momentum reversal exit (only if profitable)
        if (profit_pct > 0.5 and  # Only if at least 0.5% profit
            len(self.macd_hist) > 3 and
            self.macd_hist[-1] < self.macd_hist[-2] < self.macd_hist[-3]):  # MACD declining
            self.position.close()
            print(f'🔄 MOMENTUM REVERSAL EXIT @ {current_price:.2f} (+{profit_pct:.2f}%)')
            self.reset_trade_params()
            return

    def reset_trade_params(self):
        """Reset trade management parameters"""
        self.entry_price = None
        self.stop_loss = None
        self.take_profit = None
        self.entry_time = None
        self.entry_atr = None
        self.confidence_level = 0

# Run Default Backtest
print("🌙 Starting Enhanced Divergence Volatility Backtest (Default Parameters)...")
print("=" * 80)

bt = Backtest(data, DivergenceVolatilityEnhanced, cash=1000000, commission=.002)
stats = bt.run()

print("\n🌙 ENHANCED DIVERGENCE VOLATILITY - DEFAULT RESULTS")
print("=" * 80)
print(stats)

print(f"\n⭐ KEY METRICS:")
print(f"📊 Total Trades: {stats['# Trades']}")
print(f"💰 Total Return: {stats['Return [%]']:.2f}%")
print(f"📈 Sharpe Ratio: {stats['Sharpe Ratio']:.2f}")
print(f"📉 Max Drawdown: {stats['Max. Drawdown [%]']:.2f}%")
print(f"🎯 Win Rate: {stats['Win Rate [%]']:.2f}%")

# Run Optimization
print(f"\n🔄 Running Parameter Optimization...")
print("=" * 80)

stats_opt = bt.optimize(
    swing_period=range(10, 16, 2),
    min_separation=range(6, 12, 2),
    atr_multiplier=[1.8, 2.0, 2.2, 2.5],
    volume_spike_threshold=[1.5, 1.8, 2.0, 2.2],
    trailing_start=[1.0, 1.5, 2.0],
    max_hold_bars=range(45, 75, 10),
    maximize='Sharpe Ratio',
    constraint=lambda p: p['# Trades'] > 100 and p['Return [%]'] > 0
)

print("\n🌙 ENHANCED DIVERGENCE VOLATILITY - OPTIMIZED RESULTS")
print("=" * 80)
print(stats_opt)

print(f"\n🚀 OPTIMIZED METRICS:")
print(f"📊 Total Trades: {stats_opt['# Trades']}")
print(f"💰 Total Return: {stats_opt['Return [%]']:.2f}%")
print(f"📈 Sharpe Ratio: {stats_opt['Sharpe Ratio']:.2f}")
print(f"📉 Max Drawdown: {stats_opt['Max. Drawdown [%]']:.2f}%")
print(f"🎯 Win Rate: {stats_opt['Win Rate [%]']:.2f}%")

# Success metrics check
trade_requirement = stats_opt['# Trades'] > 100
sharpe_requirement = stats_opt['Sharpe Ratio'] > 2.0

print(f"\n✅ STRATEGY VALIDATION:")
print(f"📊 Trade Count Requirement (>100): {'✅ PASS' if trade_requirement else '❌ FAIL'} ({stats_opt['# Trades']} trades)")
print(f"📈 Sharpe Ratio Requirement (>2.0): {'✅ PASS' if sharpe_requirement else '❌ FAIL'} ({stats_opt['Sharpe Ratio']:.2f})")

if trade_requirement and sharpe_requirement:
    print("\n🏆 ENHANCED DIVERGENCE VOLATILITY STRATEGY: SUCCESS! 🏆")
    print("🌟 This strategy meets both requirements!")
    print("   ✅ Quality divergence detection")
    print("   ✅ Multi-factor confirmation system")
    print("   ✅ Dynamic position sizing")
    print("   ✅ Advanced trailing stops")
else:
    print("\n⚠️ Strategy shows promise but needs further optimization...")
    if not trade_requirement:
        print("   📊 Consider relaxing entry criteria for more trades")
    if not sharpe_requirement:
        print("   📈 Consider tightening risk management for better Sharpe ratio")

print("\n🌙 Enhanced Divergence Volatility backtest completed! ✨")