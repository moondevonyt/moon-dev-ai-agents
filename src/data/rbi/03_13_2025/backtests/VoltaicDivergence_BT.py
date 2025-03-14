```python
# -*- coding: utf-8 -*-
import pandas as pd
import talib
import numpy as np
from backtesting import Backtest, Strategy
from backtesting.lib import crossover, crossunder

# Data preparation
data = pd.read_csv('/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv')
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
}, inplace=True)
data['datetime'] = pd.to_datetime(data['datetime'])
data.set_index('datetime', inplace=True)

class VoltaicDivergence(Strategy):
    rsi_period = 14
    atr_period = 14
    swing_period = 5
    risk_percent = 0.01
    time_exit_bars = 8  # 2 hours (15m * 8)
    
    def init(self):
        # Calculate indicators using TA-Lib
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=self.rsi_period)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=self.atr_period)
        
        # Swing points calculations
        self.price_swing_high = self.I(talib.MAX, self.data.High, timeperiod=self.swing_period, name='Price Swing High')
        self.price_swing_low = self.I(talib.MIN, self.data.Low, timeperiod=self.swing_period, name='Price Swing Low')
        self.rsi_swing_high = self.I(talib.MAX, self.rsi, timeperiod=self.swing_period, name='RSI Swing High')
        self.rsi_swing_low = self.I(talib.MIN, self.rsi, timeperiod=self.swing_period, name='RSI Swing Low')
        
        self.entry_bar = 0

    def next(self):
        if len(self.data) < self.swing_period * 2:
            return
        
        current_close = self.data.Close[-1]
        current_atr = self.atr[-1]
        volatility_ok = current_atr > 0.005 * current_close
        
        # Bullish divergence check
        bullish_div = (self.price_swing_low[-1] < self.price_swing_low[-2] and 
                      self.rsi_swing_low[-1] > self.rsi_swing_low[-2])
        
        # Bearish divergence check
        bearish_div = (self.price_swing_high[-1] > self.price_swing_high[-2] and 
                      self.rsi_swing_high[-1] < self.rsi_swing_high[-2])
        
        # Moon Dev Risk Management 🌙
        if not self.position:
            if bullish_div and volatility_ok:
                risk_amount = self.equity * self.risk_percent
                sl_atr = current_atr * 0.75
                entry_price = current_close
                sl_price = entry_price - sl_atr
                position_size = risk_amount / (sl_atr)
                position_size = int(round(position_size))
                
                if position_size > 0:
                    self.entry_bar = len(self.data)
                    self.buy(size=position_size, sl=sl_price, 
                            tp=entry_price + current_atr*1.5)
                    print(f"🌙✨ MOON DEV LONG SIGNAL: {position_size} units at {entry_price:.2f} | SL: {sl_price:.2f} | TP: {entry_price + current_atr*1.5:.2f}")
            
            elif bearish_div and volatility_ok:
                risk_amount = self.equity * self.risk_percent
                sl_atr = current_atr * 0.75
                entry_price = current_close
                sl_price = entry_price + sl_atr
                position_size = risk_amount / (sl_atr)
                position_size = int(round(position_size))
                
                if position_size > 0:
                    self.entry_bar = len(self.data)
                    self.sell(size=position_size, sl=sl_price, 
                             tp=entry_price - current_atr*1.5)
                    print(f"🌙✨ MOON DEV SHORT SIGNAL: {position_size} units at {entry_price:.2f}