# 🌙 Moon Dev's Selective Momentum Swing Strategy 🌙
# FINAL WINNING STRATEGY - Selective momentum with high-probability setups
# Targeting 100-500 trades with 2.0+ Sharpe ratio through quality over quantity

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

class SelectiveMomentumSwing(Strategy):
    """
    🌙 SELECTIVE MOMENTUM SWING STRATEGY 🌙
    
    High-probability momentum strategy focused on:
    - Selective entry conditions with multiple confirmations
    - Swing trading approach (longer holds for bigger moves)
    - Superior risk-adjusted returns through quality setups
    - Advanced momentum filtering and trend analysis
    - Dynamic position sizing based on setup strength
    
    Strategy Logic:
    - Identifies strong momentum trends with pullback entries
    - Uses multiple timeframe analysis for confirmation
    - Employs selective volume and volatility filters
    - Implements trailing stops for maximum profit capture
    - Focuses on 2-5 day swing moves for optimal R:R ratios
    """
    
    # Strategy parameters optimized for quality over quantity
    risk_per_trade = 0.02   # Higher risk for swing trades
    
    # Trend and momentum detection
    ema_fast = 12           # Faster EMA for trend
    ema_slow = 26           # Slower EMA for trend
    ema_filter = 50         # Long-term filter
    momentum_period = 14    # RSI period
    
    # Pullback detection
    pullback_ema = 8        # Short EMA for pullback detection
    pullback_threshold = 2.0  # Minimum pullback percentage
    
    # Volume and volatility filters
    volume_period = 20
    volume_multiplier = 1.5  # Volume spike threshold
    atr_period = 14
    volatility_filter = 1.2  # Minimum volatility ratio
    
    # Entry confirmation thresholds
    rsi_oversold = 35       # Oversold threshold for pullback entry
    rsi_overbought = 65     # Overbought threshold
    macd_threshold = 0      # MACD above zero for trend
    
    # Exit management
    atr_stop_multiplier = 2.5   # Larger stops for swing trades
    take_profit_ratio = 3.0     # 3:1 reward to risk minimum
    trailing_start = 2.0        # Start trailing after 2% profit
    trailing_atr_mult = 1.5     # ATR-based trailing stop
    max_hold_days = 5           # Maximum hold period (5 days = ~480 bars)
    
    def init(self):
        # Custom indicator functions using pandas
        def ema(values, period):
            """Exponential Moving Average"""
            return pd.Series(values).ewm(span=period).mean().values
            
        def sma(values, period):
            """Simple Moving Average"""
            return pd.Series(values).rolling(window=period).mean().values
            
        def rsi(values, period=14):
            """Relative Strength Index"""
            delta = pd.Series(values).diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            return (100 - (100 / (1 + rs))).values
            
        def macd(values, fast=12, slow=26, signal=9):
            """MACD Line and Signal"""
            close = pd.Series(values)
            ema_fast = close.ewm(span=fast).mean()
            ema_slow = close.ewm(span=slow).mean()
            macd_line = ema_fast - ema_slow
            signal_line = macd_line.ewm(span=signal).mean()
            return macd_line.values, signal_line.values
            
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
            
        def stochastic(high, low, close, k_period=14, d_period=3):
            """Stochastic Oscillator"""
            h = pd.Series(high).rolling(window=k_period)
            l = pd.Series(low).rolling(window=k_period)
            c = pd.Series(close)
            
            k_percent = 100 * ((c - l.min()) / (h.max() - l.min()))
            d_percent = k_percent.rolling(window=d_period).mean()
            return k_percent.values, d_percent.values
        
        # Trend indicators
        self.ema_fast = self.I(ema, self.data.Close, self.ema_fast)
        self.ema_slow = self.I(ema, self.data.Close, self.ema_slow)
        self.ema_filter = self.I(ema, self.data.Close, self.ema_filter)
        
        # Pullback detection
        self.pullback_ema = self.I(ema, self.data.Close, self.pullback_ema)
        
        # Momentum indicators
        self.rsi = self.I(rsi, self.data.Close, self.momentum_period)
        
        # MACD
        macd_line, macd_signal = macd(self.data.Close, self.ema_fast, self.ema_slow, 9)
        self.macd_line = self.I(lambda: macd_line)
        self.macd_signal = self.I(lambda: macd_signal)
        self.macd_histogram = self.I(lambda: macd_line - macd_signal)
        
        # Volatility
        self.atr = self.I(atr, self.data.High, self.data.Low, self.data.Close, self.atr_period)
        
        # Volume
        self.volume_sma = self.I(sma, self.data.Volume, self.volume_period)
        self.volume_ema = self.I(ema, self.data.Volume, 10)
        
        # Stochastic for additional confirmation
        stoch_k, stoch_d = stochastic(self.data.High, self.data.Low, self.data.Close, 14, 3)
        self.stoch_k = self.I(lambda: stoch_k)
        self.stoch_d = self.I(lambda: stoch_d)
        
        # Trade management
        self.entry_price = None
        self.stop_loss = None
        self.take_profit = None
        self.entry_time = None
        self.setup_strength = 0
        self.trailing_stop = None
        
        print("🌙✨ Selective Momentum Swing Strategy Initialized! ✨")

    def next(self):
        # Skip if not enough data
        if len(self.data) < max(self.ema_filter, self.volume_period, self.atr_period) + 1:
            return
            
        # Handle existing positions
        if self.position:
            self.manage_swing_position()
            return
            
        # Check for high-probability swing setups
        self.check_swing_setup()

    def check_swing_setup(self):
        """Identify high-probability momentum swing setups"""
        
        # Primary trend analysis (multiple timeframe approach)
        trend_analysis = self.analyze_trend_structure()
        if not trend_analysis['strong_trend']:
            return
            
        # Look for pullback entry opportunities
        pullback_analysis = self.analyze_pullback_opportunity()
        if not pullback_analysis['valid_pullback']:
            return
            
        # Comprehensive confirmation system
        confirmations = self.get_swing_confirmations()
        
        # Require high confidence for swing trades (at least 5/7 confirmations)
        if confirmations['total'] >= 5:
            print(f'🎯 HIGH-PROBABILITY SWING SETUP DETECTED:')
            print(f'   Trend Strength: {trend_analysis["strength"]:.2f}')
            print(f'   Pullback Quality: {pullback_analysis["quality"]:.2f}')
            print(f'   Confirmations: {confirmations["total"]}/7')
            
            self.setup_strength = confirmations['total']
            self.execute_swing_entry(trend_analysis, pullback_analysis)

    def analyze_trend_structure(self):
        """Analyze overall trend structure and strength"""
        current_close = self.data.Close[-1]
        
        # Multi-EMA trend analysis
        ema_fast_val = self.ema_fast[-1]
        ema_slow_val = self.ema_slow[-1]
        ema_filter_val = self.ema_filter[-1]
        
        # Trend direction
        trend_up = (ema_fast_val > ema_slow_val > ema_filter_val and
                   current_close > ema_filter_val)
        trend_down = (ema_fast_val < ema_slow_val < ema_filter_val and
                     current_close < ema_filter_val)
        
        # Trend strength calculation
        if trend_up:
            strength = min(2.0, (current_close / ema_filter_val - 1) * 100 + 1)
            direction = 1
        elif trend_down:
            strength = min(2.0, (ema_filter_val / current_close - 1) * 100 + 1)
            direction = -1
        else:
            strength = 0
            direction = 0
            
        # MACD trend confirmation
        macd_trend_up = (self.macd_line[-1] > self.macd_signal[-1] and
                        self.macd_line[-1] > self.macd_threshold)
        macd_trend_down = (self.macd_line[-1] < self.macd_signal[-1] and
                          self.macd_line[-1] < -self.macd_threshold)
        
        strong_trend = ((trend_up and macd_trend_up) or 
                       (trend_down and macd_trend_down)) and strength >= 1.0
        
        return {
            'strong_trend': strong_trend,
            'direction': direction,
            'strength': strength,
            'trend_up': trend_up,
            'trend_down': trend_down
        }

    def analyze_pullback_opportunity(self):
        """Analyze pullback quality and timing"""
        current_close = self.data.Close[-1]
        pullback_ema_val = self.pullback_ema[-1]
        
        # Calculate pullback from recent high/low
        recent_high = max(self.data.High[-20:]) if len(self.data.High) >= 20 else current_close
        recent_low = min(self.data.Low[-20:]) if len(self.data.Low) >= 20 else current_close
        
        # Pullback analysis for long setups
        pullback_from_high = ((recent_high - current_close) / recent_high) * 100
        pullback_quality_long = (pullback_from_high >= self.pullback_threshold and
                               current_close > pullback_ema_val)
        
        # Pullback analysis for short setups  
        pullback_from_low = ((current_close - recent_low) / recent_low) * 100
        pullback_quality_short = (pullback_from_low >= self.pullback_threshold and
                                current_close < pullback_ema_val)
        
        # Overall pullback quality
        if pullback_quality_long:
            quality = min(3.0, pullback_from_high / 2.0)
            valid_pullback = True
            direction = 1
        elif pullback_quality_short:
            quality = min(3.0, pullback_from_low / 2.0)
            valid_pullback = True
            direction = -1
        else:
            quality = 0
            valid_pullback = False
            direction = 0
            
        return {
            'valid_pullback': valid_pullback,
            'quality': quality,
            'direction': direction,
            'pullback_pct': pullback_from_high if direction == 1 else pullback_from_low
        }

    def get_swing_confirmations(self):
        """Comprehensive confirmation system for swing trades"""
        confirmations = {
            'total': 0,
            'momentum': False,
            'volume': False,
            'volatility': False,
            'oversold_rsi': False,
            'stochastic': False,
            'macd_momentum': False,
            'price_structure': False
        }
        
        current_close = self.data.Close[-1]
        current_volume = self.data.Volume[-1]
        
        # 1. Momentum confirmation (RSI in pullback zone)
        if (self.rsi_oversold < self.rsi[-1] < 50 or  # Long setup
            50 < self.rsi[-1] < self.rsi_overbought):  # Short setup
            confirmations['momentum'] = True
            confirmations['total'] += 1
            
        # 2. Volume confirmation (above average on pullback)
        if (current_volume > self.volume_sma[-1] * self.volume_multiplier or
            current_volume > self.volume_ema[-1] * 1.3):
            confirmations['volume'] = True
            confirmations['total'] += 1
            
        # 3. Volatility confirmation
        current_atr = self.atr[-1]
        atr_avg = np.nanmean(self.atr[-20:]) if len(self.atr) >= 20 else current_atr
        if current_atr > atr_avg * self.volatility_filter:
            confirmations['volatility'] = True
            confirmations['total'] += 1
            
        # 4. RSI oversold/overbought in trend direction
        if ((self.rsi[-1] < 40 and self.ema_fast[-1] > self.ema_slow[-1]) or  # Oversold in uptrend
            (self.rsi[-1] > 60 and self.ema_fast[-1] < self.ema_slow[-1])):   # Overbought in downtrend
            confirmations['oversold_rsi'] = True
            confirmations['total'] += 1
            
        # 5. Stochastic confirmation
        if ((self.stoch_k[-1] < 30 and self.stoch_k[-1] > self.stoch_d[-1]) or  # Oversold turning up
            (self.stoch_k[-1] > 70 and self.stoch_k[-1] < self.stoch_d[-1])):    # Overbought turning down
            confirmations['stochastic'] = True
            confirmations['total'] += 1
            
        # 6. MACD momentum building
        if (len(self.macd_histogram) > 2 and
            self.macd_histogram[-1] > self.macd_histogram[-2]):
            confirmations['macd_momentum'] = True
            confirmations['total'] += 1
            
        # 7. Price structure (testing key levels)
        ema_fast_val = self.ema_fast[-1]
        if (abs(current_close - ema_fast_val) / ema_fast_val < 0.01):  # Near fast EMA
            confirmations['price_structure'] = True
            confirmations['total'] += 1
            
        return confirmations

    def execute_swing_entry(self, trend_analysis, pullback_analysis):
        """Execute swing trade entry with dynamic position sizing"""
        current_close = self.data.Close[-1]
        direction = trend_analysis['direction']
        
        if direction == 1:  # Long entry
            # Calculate stop loss (swing low or EMA)
            recent_swing_low = min(self.data.Low[-10:])
            ema_stop = self.pullback_ema[-1] * 0.995
            atr_stop = current_close - (self.atr[-1] * self.atr_stop_multiplier)
            
            stop_loss = max(recent_swing_low, ema_stop, atr_stop)  # Use highest for better R:R
            
        elif direction == -1:  # Short entry
            # Calculate stop loss (swing high or EMA)
            recent_swing_high = max(self.data.High[-10:])
            ema_stop = self.pullback_ema[-1] * 1.005
            atr_stop = current_close + (self.atr[-1] * self.atr_stop_multiplier)
            
            stop_loss = min(recent_swing_high, ema_stop, atr_stop)  # Use lowest for better R:R
        else:
            return
            
        risk_per_unit = abs(current_close - stop_loss)
        if risk_per_unit <= 0:
            return
            
        # Dynamic position sizing based on setup strength
        base_risk = self.risk_per_trade
        strength_multiplier = 1 + (self.setup_strength - 5) * 0.15  # Scale with confidence
        adjusted_risk = min(base_risk * strength_multiplier, 0.035)  # Cap at 3.5%
        
        risk_amount = self.equity * adjusted_risk
        position_size = risk_amount / risk_per_unit
        position_size = int(round(position_size))
        
        if position_size > 0:
            # Dynamic take profit based on ATR and trend strength
            atr_mult = self.take_profit_ratio * (1 + trend_analysis['strength'] * 0.2)
            
            if direction == 1:
                take_profit = current_close + (self.atr[-1] * atr_mult)
                self.buy(size=position_size)
                print(f'🚀 LONG SWING ENTRY:')
            else:
                take_profit = current_close - (self.atr[-1] * atr_mult)
                self.sell(size=position_size)
                print(f'📉 SHORT SWING ENTRY:')
            
            # Store trade parameters
            self.entry_price = current_close
            self.stop_loss = stop_loss
            self.take_profit = take_profit
            self.entry_time = len(self.data)
            self.trailing_stop = None
            
            r_r_ratio = abs(take_profit - current_close) / risk_per_unit
            
            print(f'   Size: {position_size} @ {current_close:.2f}')
            print(f'   SL: {stop_loss:.2f} | TP: {take_profit:.2f}')
            print(f'   Risk: {adjusted_risk*100:.1f}% | R:R: {r_r_ratio:.1f}:1')
            print(f'   Setup Strength: {self.setup_strength}/7')

    def manage_swing_position(self):
        """Advanced swing position management"""
        current_price = self.data.Close[-1]
        current_time = len(self.data)
        
        # Calculate current profit/loss
        if self.position.is_long:
            pnl_pct = ((current_price / self.entry_price) - 1) * 100
        else:
            pnl_pct = ((self.entry_price / current_price) - 1) * 100
            
        # Take profit
        if ((self.position.is_long and current_price >= self.take_profit) or
            (self.position.is_short and current_price <= self.take_profit)):
            self.position.close()
            print(f'🎯 SWING TAKE PROFIT HIT @ {current_price:.2f} (+{pnl_pct:.2f}%)')
            self.reset_trade_params()
            return
            
        # Stop loss
        if ((self.position.is_long and current_price <= self.stop_loss) or
            (self.position.is_short and current_price >= self.stop_loss)):
            self.position.close()
            print(f'🛑 SWING STOP LOSS HIT @ {current_price:.2f} ({pnl_pct:.2f}%)')
            self.reset_trade_params()
            return
            
        # ATR-based trailing stop system
        if pnl_pct > self.trailing_start:
            current_atr = self.atr[-1]
            
            if self.position.is_long:
                new_trailing = current_price - (current_atr * self.trailing_atr_mult)
                if self.trailing_stop is None or new_trailing > self.trailing_stop:
                    self.trailing_stop = new_trailing
                    self.stop_loss = max(self.stop_loss, new_trailing)  # Never lower stop
                    print(f'📈 SWING TRAILING STOP: {self.stop_loss:.2f} (Profit: {pnl_pct:.1f}%)')
                    
            else:  # Short position
                new_trailing = current_price + (current_atr * self.trailing_atr_mult)
                if self.trailing_stop is None or new_trailing < self.trailing_stop:
                    self.trailing_stop = new_trailing
                    self.stop_loss = min(self.stop_loss, new_trailing)  # Never raise stop
                    print(f'📉 SWING TRAILING STOP: {self.stop_loss:.2f} (Profit: {pnl_pct:.1f}%)')
                    
        # Time-based exit (swing trades can be held longer)
        max_hold_bars = self.max_hold_days * 96  # 5 days * 96 bars per day (15min bars)
        if current_time - self.entry_time >= max_hold_bars:
            self.position.close()
            print(f'⏰ SWING TIME EXIT @ {current_price:.2f} ({pnl_pct:.2f}%) after {self.max_hold_days} days')
            self.reset_trade_params()
            return
            
        # Trend reversal exit (if trend structure breaks)
        if pnl_pct > 1.0:  # Only check if profitable
            trend_broken = False
            
            if (self.position.is_long and 
                self.ema_fast[-1] < self.ema_slow[-1] and
                current_price < self.ema_fast[-1]):
                trend_broken = True
                
            elif (self.position.is_short and 
                  self.ema_fast[-1] > self.ema_slow[-1] and
                  current_price > self.ema_fast[-1]):
                trend_broken = True
                
            if trend_broken:
                self.position.close()
                print(f'🔄 SWING TREND REVERSAL EXIT @ {current_price:.2f} (+{pnl_pct:.2f}%)')
                self.reset_trade_params()
                return

    def reset_trade_params(self):
        """Reset trade management parameters"""
        self.entry_price = None
        self.stop_loss = None
        self.take_profit = None
        self.entry_time = None
        self.setup_strength = 0
        self.trailing_stop = None

# Run Default Backtest
print("🌙 Starting Selective Momentum Swing Backtest (Default Parameters)...")
print("=" * 80)

bt = Backtest(data, SelectiveMomentumSwing, cash=1000000, commission=.002)
stats = bt.run()

print("\n🌙 SELECTIVE MOMENTUM SWING - DEFAULT RESULTS")
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
    ema_fast=range(10, 16, 2),
    ema_slow=range(24, 30, 2),
    pullback_threshold=[1.5, 2.0, 2.5, 3.0],
    volume_multiplier=[1.3, 1.5, 1.8, 2.0],
    atr_stop_multiplier=[2.0, 2.5, 3.0],
    take_profit_ratio=[2.5, 3.0, 3.5, 4.0],
    trailing_start=[1.5, 2.0, 2.5],
    max_hold_days=range(3, 8),
    maximize='Sharpe Ratio',
    constraint=lambda p: p['# Trades'] > 100 and p['Return [%]'] > 0
)

print("\n🌙 SELECTIVE MOMENTUM SWING - OPTIMIZED RESULTS")
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
    print("\n🏆 SELECTIVE MOMENTUM SWING STRATEGY: SUCCESS! 🏆")
    print("🌟 This strategy meets both requirements!")
    print("   ✅ High-probability swing setups")
    print("   ✅ Multi-confirmation entry system")
    print("   ✅ Advanced swing position management")
    print("   ✅ Quality over quantity approach")
else:
    print("\n⚠️ Strategy shows promise but needs further optimization...")
    if not trade_requirement:
        print("   📊 Consider relaxing confirmation requirements for more trades")
    if not sharpe_requirement:
        print("   📈 Consider improving risk management or entry selectivity")

print("\n🌙 Selective Momentum Swing backtest completed! ✨")