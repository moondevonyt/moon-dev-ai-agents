import pandas as pd
import talib
from backtesting import Backtest, Strategy

class QuadrupleHarmonic(Strategy):
    def init(self):
        self.ema = self.I(talib.EMA, self.data.Close, timeperiod=200)
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14)  # 🌙 Added RSI for oversold filter in pullbacks
        self.vol_sma = self.I(talib.SMA, self.data.Volume, timeperiod=20)  # 🌙 Added volume SMA for confirmation filter
        self.plus_di = self.I(talib.PLUS_DI, self.data.High, self.data.Low, self.data.Close, timeperiod=14)  # 🌙 New: +DI for uptrend strength filter
        self.minus_di = self.I(talib.MINUS_DI, self.data.High, self.data.Low, self.data.Close, timeperiod=14)  # 🌙 New: -DI for uptrend strength filter
        self.entry_bar = None  # To track for potential exits
        self.entry_price = None  # 🌙 New: Track entry for trailing stop
        self.initial_sl = None  # 🌙 New: Track initial SL for RR calculations in trailing

    def next(self):
        current_close = self.data.Close[-1]
        current_open = self.data.Open[-1]
        current_low = self.data.Low[-1]
        current_high = self.data.High[-1]
        
        # Debug print for trend context 🌙
        if len(self.data) % 100 == 0:
            print(f"🌙 Moon Dev Debug: Current Close {current_close:.2f}, EMA {self.ema[-1]:.2f}, ADX {self.adx[-1]:.2f} ✨")
        
        # Position management with trailing stop 🌙
        if self.position:
            # Early exit if breaks below EMA (uptrend protection)
            if current_close < self.ema[-1]:
                self.position.close()
                print(f"🌙 Moon Dev Exit: Early close below EMA at {current_close:.2f} 🚀")
                self.entry_bar = None
                self.entry_price = None
                self.initial_sl = None
                return
            # Time-based exit after 20 bars (extended for more room in crypto swings) 🌙
            if self.entry_bar and len(self.data) - self.entry_bar > 20:
                self.position.close()
                print(f"🌙 Moon Dev Exit: Time-based close after 20 bars at {current_close:.2f} ✨")
                self.entry_bar = None
                self.entry_price = None
                self.initial_sl = None
                return
            # 🌙 New: Trailing stop logic - activate after 1R profit
            if self.entry_price and self.initial_sl:
                profit = current_close - self.entry_price
                risk = self.entry_price - self.initial_sl
                if profit > risk:  # Reached 1R
                    trail_sl = current_close - 1.5 * self.atr[-1]  # Trail by 1.5 ATR behind current price
                    if trail_sl > self.position.sl:
                        self.position.sl = trail_sl
                        print(f"🌙 Moon Dev Trail: Updated SL to {trail_sl:.2f} at {current_close:.2f} 🚀")
            return
        
        # Reset trackers when no position 🌙
        if not self.position:
            self.entry_bar = None
            self.entry_price = None
            self.initial_sl = None
        
        # Entry logic only if no position
        if self.position or len(self.data) < 200:  # 🌙 Keep 200 for EMA maturity
            return
        
        # Calculate bullish candle strength 🌙
        body = current_close - current_open
        candle_range = current_high - current_low
        strong_bullish = body > 0.7 * candle_range and body > 0  # 🌙 Tightened to 70% of range for stronger conviction entries
        
        # 🌙 Optimized: Reduced to 3 consecutive down bars (from 4) for more frequent quality pullback signals in uptrends
        # Check for previous 3 consecutive down bars and current bullish confirmation
        if (len(self.data) >= 4 and
            self.data.Close[-4] < self.data.Open[-4] and  # First down bar
            self.data.Close[-3] < self.data.Open[-3] and  # Second
            self.data.Close[-2] < self.data.Open[-2] and  # Third
            self.data.Close[-3] < self.data.Close[-4] and  # Strictly decreasing closes
            self.data.Close[-2] < self.data.Close[-3] and
            strong_bullish and  # Strong bullish reversal
            current_close > self.ema[-1] and  # Uptrend filter
            self.adx[-1] > 22 and  # 🌙 Adjusted ADX to 22 for balanced trend strength (more than 20, less restrictive than 25)
            self.rsi[-1] < 45 and  # 🌙 Loosened RSI to <45 for capturing shallower pullbacks with potential
            self.data.Volume[-1] > 1.3 * self.vol_sma[-1] and  # 🌙 Adjusted volume to 1.3x for more signals while keeping conviction
            self.plus_di[-1] > self.minus_di[-1]):  # 🌙 New: +DI > -DI for confirmed uptrend regime filter
            
            print(f"🌙 Moon Dev Signal: 3 down bars pullback in uptrend, strong bullish at {current_close:.2f} 🚀")
            
            # Pattern details - updated for 3 down bars 🌙
            pattern_lows = self.data.Low[-4:-1]  # Lows of the 3 down bars
            min_low = min(pattern_lows)
            
            # SL: below pattern low by 1 ATR (conservative)
            atr_val = self.atr[-1]
            sl_price = min_low - 1.0 * atr_val
            
            # Entry at current close
            entry_price = current_close
            
            # 🌙 Optimized: Improved TP to 1:3 RR for higher return potential, combined with trailing for risk control
            stop_distance = entry_price - sl_price
            if stop_distance <= 0:
                print(f"🌙 Moon Dev Skip: Zero or negative stop distance 😔")
                return
            tp_price = entry_price + 3 * stop_distance
            
            # Risk management: 1% risk, fraction of equity 🌙
            risk_pct = 0.01
            size_frac = risk_pct * (entry_price / stop_distance)
            size = min(size_frac, 0.4)  # 🌙 Reduced cap to 40% for tighter risk in volatile markets
            
            if size > 0:
                # Debug print before order 🌙
                print(f"🌙 Moon Dev Debug: Order params - Size {size:.4f}, SL {sl_price:.5f}, TP {tp_price:.5f}, Entry/Close {entry_price:.5f} ✨")
                # Market entry for better fills in crypto 🌙
                self.buy(size=size, sl=sl_price, tp=tp_price)
                self.entry_bar = len(self.data)
                self.entry_price = entry_price  # 🌙 Set for trailing
                self.initial_sl = sl_price  # 🌙 Set for RR calc
                print(f"🌙 Moon Dev Entry: Long {size:.4f} fraction at ~{entry_price:.2f}, SL {sl_price:.2f}, TP {tp_price:.2f} (Min Low {min_low:.2f}) 🚀✨")

# Data loading and cleaning
data_path = '/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv'
data = pd.read_csv(data_path)
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data = data.set_index(pd.to_datetime(data['datetime']))
data = data.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'})

# Ensure required columns exist
required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
for col in required_cols:
    if col not in data.columns:
        print(f"Warning: Column {col} missing!")

# Run backtest
bt = Backtest(data, QuadrupleHarmonic, cash=1000000, commission=0.002, exclusive_orders=True)
stats = bt.run()
print(stats)
print(stats._strategy)