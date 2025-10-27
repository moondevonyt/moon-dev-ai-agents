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
        self.ema_short = self.I(talib.EMA, self.data.Close, timeperiod=20)  # 🌙 NEW: Short EMA for pullback confirmation (close above EMA20 after pullback)
        self.entry_bar = None  # To track for potential exits
        self.entry_price = None  # 🌙 NEW: Track entry price for trailing logic
        self.highest_since_entry = None  # 🌙 NEW: For trailing stop high

    def next(self):
        current_close = self.data.Close[-1]
        current_open = self.data.Open[-1]
        current_low = self.data.Low[-1]
        current_high = self.data.High[-1]
        
        # Debug print for trend context 🌙
        if len(self.data) % 100 == 0:
            print(f"🌙 Moon Dev Debug: Current Close {current_close:.2f}, EMA {self.ema[-1]:.2f}, ADX {self.adx[-1]:.2f} ✨")
        
        # Position management: Early exit if breaks below EMA (uptrend protection) 🌙
        if self.position:
            # 🌙 NEW: Trailing stop logic - after 1:1 RR, trail SL to lock profits
            if self.entry_price and current_close > self.entry_price + (self.entry_price - self.position.sl):
                # Update highest
                if self.highest_since_entry is None or current_high > self.highest_since_entry:
                    self.highest_since_entry = current_high
                # Trail SL to highest - 1 ATR (dynamic trailing for better profit capture in trends)
                trail_sl = self.highest_since_entry - 1.0 * self.atr[-1]
                if trail_sl > self.position.sl:
                    self.position.sl = trail_sl
                    print(f"🌙 Moon Dev Trail: Updated SL to {trail_sl:.2f} at high {self.highest_since_entry:.2f} 🚀")
            
            if current_close < self.ema[-1]:
                self.position.close()
                print(f"🌙 Moon Dev Exit: Early close below EMA at {current_close:.2f} 🚀")
            # Time-based exit after 30 bars (increased from 15 for more room in volatile crypto trends) 🌙
            if self.entry_bar and len(self.data) - self.entry_bar > 30:
                self.position.close()
                print(f"🌙 Moon Dev Exit: Time-based close after 30 bars at {current_close:.2f} ✨")
            return
        
        # Entry logic only if no position
        if self.position or len(self.data) < 200:  # 🌙 Increased from 21 to 200 for EMA200 maturity
            return
        
        # Calculate bullish candle strength 🌙
        body = current_close - current_open
        candle_range = current_high - current_low
        strong_bullish = body > 0.6 * candle_range and body > 0  # 🌙 TIGHTENED: Increased to >60% body for stronger reversal conviction
        
        # 🌙 IMPROVED: Check for 4 consecutive down bars with BOTH decreasing closes AND lower lows for clearer pullback structure
        prev_lows_decreasing = (
            len(self.data) >= 5 and
            self.data.Low[-4] < self.data.Low[-5] and
            self.data.Low[-3] < self.data.Low[-4] and
            self.data.Low[-2] < self.data.Low[-3]
        )
        prev_closes_decreasing = (
            self.data.Close[-5] < self.data.Open[-5] and
            self.data.Close[-4] < self.data.Open[-4] and
            self.data.Close[-3] < self.data.Open[-3] and
            self.data.Close[-2] < self.data.Open[-2] and
            self.data.Close[-4] < self.data.Close[-5] and
            self.data.Close[-3] < self.data.Close[-4] and
            self.data.Close[-2] < self.data.Close[-3]
        )
        
        # 🌙 ADDED: Pullback depth filter - total drop from recent high >1% but <5% to avoid deep corrections
        recent_high = max(self.data.High[-10:-1])  # Lookback 10 bars for swing high
        pullback_depth = (recent_high - current_close) / recent_high
        valid_depth = pullback_depth > 0.01 and pullback_depth < 0.05
        
        if (prev_closes_decreasing and prev_lows_decreasing and
            strong_bullish and  # Bullish confirmation candle with strength filter
            current_close > self.ema[-1] and  # Uptrend filter
            current_close > self.ema_short[-1] and  # 🌙 NEW: Above short EMA for pullback end confirmation
            self.adx[-1] > 22 and  # 🌙 ADJUSTED: Slightly raised from 20 to 22 for stronger trends, balancing signal quality
            self.rsi[-1] < 35 and  # 🌙 TIGHTENED: Lowered from 40 to 35 for deeper, higher-quality oversold pullbacks
            self.data.Volume[-1] > 2.0 * self.vol_sma[-1] and  # 🌙 TIGHTENED: Increased volume multiplier to 2x for higher conviction reversals
            valid_depth):  # 🌙 NEW: Depth filter for optimal pullback size
            
            print(f"🌙 Moon Dev Signal: 4 down bars (lower lows/closes) pullback in uptrend, strong bullish at {current_close:.2f}, depth {pullback_depth:.2%} 🚀")
            
            # Pattern details - improved min_low calculation 🌙
            pattern_lows = self.data.Low[-5:-1]  # Lows of the 4 down bars
            min_low = min(pattern_lows)
            
            # SL: below pattern low by 0.8 ATR (tightened slightly from 1.0 for better RR without too many stops) 🌙
            atr_val = self.atr[-1]
            sl_price = min_low - 0.8 * atr_val
            
            # Entry at current close (approximate)
            entry_price = current_close
            
            # IMPROVED TP: 1:3 Risk-Reward ratio (increased from 2:1 for higher returns on winners, combined with trailing) 🌙
            stop_distance = entry_price - sl_price
            if stop_distance <= 0:
                print(f"🌙 Moon Dev Skip: Zero or negative stop distance 😔")
                return
            tp_price = entry_price + 3 * stop_distance
            
            # Risk management: 1% risk, but compute as fraction of equity 🌙 (fixed position sizing to prevent overleverage)
            # 🌙 ADJUSTED: Slightly reduce risk to 0.8% for better drawdown control in optimized higher RR setup
            risk_pct = 0.008
            size_frac = risk_pct * (entry_price / stop_distance)
            size = min(size_frac, 0.4)  # 🌙 TIGHTENED: Cap at 40% from 50% for conservative exposure in volatile markets
            
            if size > 0:
                # Debug print before order 🌙
                print(f"🌙 Moon Dev Debug: Order params - Size {size:.4f}, SL {sl_price:.5f}, TP {tp_price:.5f}, Entry/Close {entry_price:.5f} ✨")
                # Removed limit=entry_price for market entry at next open (improves fill rate in gappy crypto) 🌙
                self.buy(size=size, sl=sl_price, tp=tp_price)
                self.entry_bar = len(self.data)
                self.entry_price = entry_price  # 🌙 NEW: Set for trailing
                self.highest_since_entry = current_high  # 🌙 NEW: Initialize high
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