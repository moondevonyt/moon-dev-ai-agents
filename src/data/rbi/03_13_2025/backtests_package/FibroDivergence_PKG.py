Here's the fixed code with all the necessary changes to remove any `backtesting.lib` imports and ensure proper indicator usage:

```python
from backtesting import Backtest, Strategy
import pandas as pd
import numpy as np
import talib
import os

# Data preparation
data_path = "/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv"
data = pd.read_csv(data_path)

# Clean and format data
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data = data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
})
data['datetime'] = pd.to_datetime(data['datetime'])
data = data.set_index('datetime')

class FibroDivergence(Strategy):
    risk_per_trade = 0.01  # 1% risk per trade
    atr_period = 14
    rsi_period = 14
    swing_period = 20
    divergence_window = 5

    def init(self):
        # Core indicators 🌙
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=self.rsi_period)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=self.atr_period)
        
        # Swing points for Fibonacci ✨
        self.swing_high = self.I(talib.MAX, self.data.High, timeperiod=self.swing_period)
        self.swing_low = self.I(talib.MIN, self.data.Low, timeperiod=self.swing_period)
        
        # Divergence detection indicators 🔍
        self.price_swing_high = self.I(talib.MAX, self.data.High, timeperiod=self.divergence_window)
        self.price_swing_low = self.I(talib.MIN, self.data.Low, timeperiod=self.divergence_window)
        self.rsi_swing_high = self.I(talib.MAX, self.rsi, timeperiod=self.divergence_window)
        self.rsi_swing_low = self.I(talib.MIN, self.rsi, timeperiod=self.divergence_window)

    def next(self):
        if self.position:
            return  # Hold position if already in trade 🌙

        # Current market conditions 📊
        close = self.data.Close[-1]
        prev_close = self.data.Close[-2]
        atr = self.atr[-1]
        swing_high = self.swing_high[-1]
        swing_low = self.swing_low[-1]

        # Fibonacci calculations 🔺
        fib_levels = []
        if swing_high > swing_low:
            fib_range = swing_high - swing_low
            fib_levels = [
                swing_high - fib_range * 0.382,
                swing_high - fib_range * 0.5,
                swing_high - fib_range * 0.618
            ]
        
        # Check Fib proximity (1% threshold) 📍
        near_fib = any(abs(close - level)/close < 0.01 for level in fib_levels) if fib_levels else False

        # Divergence detection logic 🤖
        bullish_div = bearish_div = False
        if len(self.rsi_swing_low) > 2 and len(self.price_swing_low) > 2:
            bullish_div = (self.price_swing_low[-1] < self.price_swing_low[-2] and 
                          self.rsi_swing_low[-1] > self.rsi_swing_low[-2])

        if len(self.rsi_swing_high) > 2 and len(self.price_swing_high) > 2:
            bearish_div = (self.price_swing_high[-1] > self.price_swing_high[-2] and 
                          self.rsi_swing_high[-1] < self.rsi_swing_high[-2])

        # Trade execution logic 🚀
        if near_fib:
            if bullish_div and close > prev_close:
                # Long entry with Moon Dev flair 🌙
                sl = close - atr * 1
                risk = close - sl
                position_size = int(round((self.risk_per_trade * self.equity) / risk))
                if position_size > 0:
                    print(f"🌙✨ BULLISH CONFIRM