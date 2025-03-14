Here's the fixed code with all `backtesting.lib` imports and functions removed, and proper Moon Dev themed debug prints added:

```python
# -*- coding: utf-8 -*-
import pandas as pd
import talib
import pandas_ta as ta
import numpy as np
from backtesting import Backtest, Strategy

class DivergenceVolatility(Strategy):
    risk_per_trade = 0.01  # 1% risk per trade 🌙
    atr_multiplier = 2  # ATR multiplier for take-profit 🚀
    bb_period = 20  # Bollinger Bands period
    volume_spike_multiplier = 1.5  # 50% above average volume ✨
    swing_period = 20  # Swing high/low period
    
    def init(self):
        # Clean and prepare data 🌙
        self.data.df.columns = self.data.df.columns.str.strip().str.lower()
        self.data.df = self.data.df.drop(columns=[col for col in self.data.df.columns if 'unnamed' in col])
        
        # Calculate MACD using TA-Lib 🌌
        self.macd, self.macd_signal, self.macd_hist = self.I(talib.MACD, self.data.Close, 
                                                             fastperiod=12, slowperiod=26, signalperiod=9)
        
        # Volume indicators 📊
        self.volume_sma = self.I(talib.SMA, self.data.Volume, timeperiod=20)
        
        # Bollinger Bands 📈
        self.bb_upper, self.bb_middle, self.bb_lower = self.I(talib.BBANDS, self.data.Close, 
                                                              timeperiod=self.bb_period, nbdevup=2, nbdevdn=2)
        
        # ATR for volatility 🌊
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        
        # Swing lows using MAX/MIN 🌙
        self.swing_lows = self.I(talib.MIN, self.data.Low, timeperiod=self.swing_period)
        self.swing_highs = self.I(talib.MAX, self.data.High, timeperiod=self.swing_period)
        
        # Track entry conditions
        self.entry_price = None
        self.entry_bb_width = None
        self.take_profit = None

    def next(self):
        # Moon Dev debug prints 🌙✨
        if len(self.data) < 50:  # Wait for enough data
            return
            
        # Check if we're already in a position
        if not self.position:
            self.check_entry_conditions()
        else:
            self.check_exit_conditions()

    def check_entry_conditions(self):
        # Bullish divergence: price makes lower low, MACD makes higher low 🔼
        current_low = self.data.Low[-1]
        prev_low = self.data.Low[-2]
        current_macd = self.macd_hist[-1]
        prev_macd = self.macd_hist[-2]
        
        # Volume spike validation 🔊
        volume_spike = self.data.Volume[-1] > self.volume_sma[-1] * self.volume_spike_multiplier
        
        # Swing low calculation 🌙
        swing_low = self.swing_lows[-1]
        
        # Check divergence conditions
        bullish_divergence = (current_low < prev_low) and (current_macd > prev_macd)
        
        if bullish_divergence and volume_spike:
            # Calculate stop loss and position size 🛑
            stop_loss = swing_low * 0.995  # 0.5% below swing low
            risk_amount = self.risk_per_trade * self.equity
            risk_per_share = self.data.Close[-1] - stop_loss
            position_size = int(round(risk_amount / risk_per_share))
            
            if position_size > 0:
                # Record entry conditions 🌙
                self.entry_price = self.data.Close[-1]
                bb_width = (self.bb_upper[-1] - self.bb_lower[-1]) / self.bb_middle[-1]
                self.entry_bb_width = bb_width
                self.take_profit = self.entry_price + (self.atr[-1] * self.atr_multiplier)
                
                # Enter long position 🚀
                self.buy(size=position_size, sl=stop_loss)
                print(f"🌕 MOON DEV ALERT: Long entry at {self.entry_price:.2f}!")
                print