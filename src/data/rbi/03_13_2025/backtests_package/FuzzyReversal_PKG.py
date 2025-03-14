Here's the fixed code with all `backtesting.lib` imports and functions removed, and proper Moon Dev themed debug prints added:

```python
# 🌙 Moon Dev's FuzzyReversal Backtest Implementation 🚀

import os
import pandas as pd
import numpy as np
import talib
from backtesting import Backtest, Strategy

# ======================
# DATA PREPARATION 🌌
# ======================
data_path = "/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv"

# Load and clean data
data = pd.read_csv(data_path)
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
}, inplace=True)

# ======================
# FUZZY REVERSAL STRATEGY 🌗
# ======================
class FuzzyReversal(Strategy):
    # Strategy parameters ✨
    atr_period = 14
    rsi_period = 14
    swing_period = 20
    risk_pct = 0.01  # 1% risk per trade
    atr_multiplier = 1.5
    rsi_oversold = 30
    rsi_overbought = 70
    
    def init(self):
        # 🌙 Core Indicators Calculation
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=self.atr_period)
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=self.rsi_period)
        self.swing_high = self.I(talib.MAX, self.data.High, timeperiod=self.swing_period)
        self.swing_low = self.I(talib.MIN, self.data.Low, timeperiod=self.swing_period)
        
        # 🌌 Volatility Filter (ATR moving average)
        self.atr_ma = self.I(talib.SMA, self.atr, timeperiod=self.atr_period)

    def next(self):
        # Skip if indicators not ready 🌊
        if len(self.data) < self.swing_period or len(self.rsi) < self.rsi_period:
            return

        current_price = self.data.Close[-1]
        current_atr = self.atr[-1]
        current_rsi = self.rsi[-1]
        
        # 🌙 Moon Dev's Fuzzy Logic Conditions 🌗
        bullish_cond = (
            (current_price <= self.swing_low[-1] + current_atr * self.atr_multiplier) and
            (current_rsi < self.rsi_oversold) and
            (current_atr > self.atr_ma[-1])
        )
        
        bearish_cond = (
            (current_price >= self.swing_high[-1] - current_atr * self.atr_multiplier) and
            (current_rsi > self.rsi_overbought) and
            (current_atr > self.atr_ma[-1])
        )

        # ======================
        # RISK MANAGEMENT 🌑
        # ======================
        if not self.position:
            if bullish_cond:
                # 🌙 Bullish Reversal Entry
                sl = self.swing_low[-1] - current_atr * 0.5
                risk_per_share = current_price - sl
                if risk_per_share > 0:
                    position_size = int(round((self.risk_pct * self.equity) / risk_per_share))
                    if position_size > 0:
                        self.buy(size=position_size, sl=sl, tp=current_price + 2*risk_per_share)
                        print(f"🌕 MOON SHOT! LONG @ {current_price:.2f} | Size: {position_size} | SL: {sl:.2f} | TP: {current_price + 2*risk_per_share:.2f} 🚀")
                        
            elif bearish_cond:
                # 🌑 Bearish Reversal Entry
                sl = self.swing_high[-1] + current_atr * 0.5
                risk_per_share = sl - current_price
                if risk_per_share > 0:
                    position_size = int(round((self.risk_pct * self.equity) / risk_per_share))
                    if position_size > 0:
                        self.sell(size=position_size, sl=sl, tp=current_price