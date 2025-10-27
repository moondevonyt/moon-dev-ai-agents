import pandas as pd
import talib
from backtesting import Backtest, Strategy

class QuadrupleHarmonic(Strategy):
    def init(self):
        self.ema = self.I(talib.EMA, self.data.Close, timeperiod=200)
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        self.entry_bar = None  # To track for potential exits

    def next(self):
        current_close = self.data.Close[-1]
        current_open = self.data.Open[-1]
        current_low = self.data.Low[-1]
        current_high = self.data.High[-1]
        
        # Debug print for trend context 🌙
        if len(self.data) % 100 == 0:
            print(f"🌙 Moon Dev Debug: Current Close {current_close:.2f}, EMA {self.ema[-1]:.2f}, ADX {self.adx[-1]:.2f} ✨")
        
        # Early exit if position and breaks below EMA (post-entry filter)
        if self.position:
            if current_close < self.ema[-1]:
                self.position.close()
                print(f"🌙 Moon Dev Exit: Early close below EMA at {current_close:.2f} 🚀")
            # Time-based exit after 10 bars
            if self.entry_bar and len(self.data) - self.entry_bar > 10:
                self.position.close()
                print(f"🌙 Moon Dev Exit: Time-based close after 10 bars at {current_close:.2f} ✨")
            return
        
        # Entry logic only if no position
        if self.position or len(self.data) < 21:
            return
        
        # Check for previous 4 consecutive down bars and current bullish confirmation
        if (len(self.data) >= 5 and
            self.data.Close[-5] < self.data.Open[-5] and
            self.data.Close[-4] < self.data.Open[-4] and
            self.data.Close[-3] < self.data.Open[-3] and
            self.data.Close[-2] < self.data.Open[-2] and
            self.data.Close[-4] < self.data.Close[-5] and
            self.data.Close[-3] < self.data.Close[-4] and
            self.data.Close[-2] < self.data.Close[-3] and
            current_close > current_open and  # Bullish confirmation candle
            current_close < self.ema[-1] and  # Downtrend filter
            self.adx[-1] > 25):  # Trending market
            
            print(f"🌙 Moon Dev Signal: 4 down bars detected, bullish confirmation at {current_close:.2f} 🚀")
            
            # Pattern details
            pattern_low = self.data.Low[-2]  # Low of the 4th down bar
            prev_lows = [self.data.Low[-5], self.data.Low[-4], self.data.Low[-3], self.data.Low[-2]]
            min_low = min(prev_lows)
            
            # Approximate XA: max high in previous 20 bars (before current)
            prev_highs = self.data.High[-21:-1]
            swing_high = max(prev_highs) if len(prev_highs) > 0 else current_high
            
            # SL: below pattern low by 1 ATR
            atr_val = self.atr[-1]
            sl_price = pattern_low - 1.0 * atr_val
            
            # Entry at current close
            entry_price = current_close
            
            # TP: 0.618 retracement of approximate XA leg
            xa_length = swing_high - min_low
            tp_price = min_low + 0.618 * xa_length
            
            # Validate prices
            if tp_price <= entry_price or sl_price >= entry_price or xa_length <= 0:
                print(f"🌙 Moon Dev Skip: Invalid TP/SL - TP {tp_price:.2f}, Entry {entry_price:.2f}, SL {sl_price:.2f} 😔")
                return
            
            # Risk management: 1% risk
            risk_amount = self.equity * 0.01
            stop_distance = entry_price - sl_price
            if stop_distance <= 0:
                print(f"🌙 Moon Dev Skip: Zero or negative stop distance 😔")
                return
            
            position_size = risk_amount / stop_distance
            size = int(round(position_size))
            
            if size > 0:
                self.buy(size=size, sl=sl_price, tp=tp_price)
                self.entry_bar = len(self.data)
                print(f"🌙 Moon Dev Entry: Long {size} units at {entry_price:.2f}, SL {sl_price:.2f}, TP {tp_price:.2f} (XA High {swing_high:.2f}, Min Low {min_low:.2f}) 🚀✨")

# Data loading and cleaning
data_path = '/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv'
data = pd.read_csv(data_path, parse_dates=['datetime'], index_col='datetime')

# Clean column names
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])

# Map to required columns with proper case
data = data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
})

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