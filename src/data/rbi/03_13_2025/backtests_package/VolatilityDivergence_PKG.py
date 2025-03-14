I'll help you fix the code by removing the `backtesting.lib` import and ensuring proper indicator usage. Here's the corrected version:

```python
# -*- coding: utf-8 -*-
import pandas as pd
import talib
from backtesting import Backtest, Strategy

# Data preparation
data = pd.read_csv('/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv')
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data = data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume',
})

class VolatilityDivergence(Strategy):
    risk_per_trade = 0.01  # 1% risk per trade
    
    def init(self):
        # Calculate indicators using talib
        self.macd, self.macd_signal, self.macd_hist = self.I(talib.MACD, self.data.Close, fastperiod=12, slowperiod=26, signalperiod=9)
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        self.atr_ma = self.I(talib.SMA, self.atr, timeperiod=20)
        
        # Swing detection
        self.swing_period = 5
        self.price_swing_high = self.I(talib.MAX, self.data.High, timeperiod=self.swing_period)
        self.price_swing_low = self.I(talib.MIN, self.data.Low, timeperiod=self.swing_period)
        self.macd_swing_high = self.I(talib.MAX, self.macd, timeperiod=self.swing_period)
        self.macd_swing_low = self.I(talib.MIN, self.macd, timeperiod=self.swing_period)
        self.rsi_swing_high = self.I(talib.MAX, self.rsi, timeperiod=self.swing_period)
        self.rsi_swing_low = self.I(talib.MIN, self.rsi, timeperiod=self.swing_period)

        # Track swing points
        self.price_lows = []
        self.macd_lows = []
        self.rsi_lows = []
        self.price_highs = []
        self.macd_highs = []
        self.rsi_highs = []

    def next(self):
        if len(self.data.Close) < 20:
            return

        # Detect new swing points
        current_price = self.data.Close[-1]
        current_low = self.data.Low[-1]
        current_high = self.data.High[-1]
        current_macd = self.macd[-1]
        current_rsi = self.rsi[-1]

        # Price swing low detection
        if current_low == self.price_swing_low[-1]:
            self.price_lows.append((len(self.data)-1, current_low))
            if len(self.price_lows) > 2:
                self.price_lows.pop(0)

        # MACD swing low detection
        if current_macd == self.macd_swing_low[-1]:
            self.macd_lows.append((len(self.data)-1, current_macd))
            if len(self.macd_lows) > 2:
                self.macd_lows.pop(0)

        # RSI swing low detection
        if current_rsi == self.rsi_swing_low[-1]:
            self.rsi_lows.append((len(self.data)-1, current_rsi))
            if len(self.rsi_lows) > 2:
                self.rsi_lows.pop(0)

        # Price swing high detection
        if current_high == self.price_swing_high[-1]:
            self.price_highs.append((len(self.data)-1, current_high))
            if len(self.price_highs) > 2:
                self.price_highs.pop(0)

        # MACD swing high detection
        if current_macd == self.macd_swing_high[-1]:
            self.macd_highs.append((len(self.data)-1, current_macd))
            if len(self.macd_highs) > 2:
                self.macd_highs.pop(0)

        # RSI swing high detection
        if