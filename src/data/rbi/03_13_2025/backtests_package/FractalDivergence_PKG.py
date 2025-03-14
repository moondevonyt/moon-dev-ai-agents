# 🌙 Moon Dev's FractalDivergence Backtest Implementation 🚀

# Required imports
import pandas as pd
import talib
from backtesting import Backtest, Strategy
import numpy as np

# Data preparation function
def prepare_data(filepath):
    # Load data with Moon Dev's special preprocessing 🌕
    data = pd.read_csv(filepath)
    
    # Clean column names
    data.columns = data.columns.str.strip().str.lower()
    data = data.drop(columns=[col for col in data.columns if 'unnamed' in col])
    
    # Convert to proper case for backtesting.py
    data = data.rename(columns={
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume'
    })
    
    # Convert datetime
    data['datetime'] = pd.to_datetime(data['datetime'])
    data = data.set_index('datetime')
    return data

class FractalDivergence(Strategy):
    initial_equity = 1000000  # 🌕 1M Moon Base Capital
    risk_per_trade = 0.02     # 2% Risk per trade
    sl_pct = 0.10             # 10% Stop Loss
    tp_pct = 0.15             # 15% Take Profit
    
    def init(self):
        # 🌙 Fractal Analysis Indicators
        self.swing_high = self.I(talib.MAX, self.data.High, timeperiod=5, name='SWING HIGH 🌄')
        self.swing_low = self.I(talib.MIN, self.data.Low, timeperiod=5, name='SWING LOW 🌊')
        
        # ✨ Divergence Detection Indicators
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14, name='RSI 🌀')
        self.macd = talib.MACD(self.data.Close, fastperiod=12, slowperiod=26, signalperiod=9)
        self.signal = self.I(self.macd, column=self.macd[2], name='MACD_signal 🌈')
        
        # 🏔 Fibonacci Levels Calculator
        self.max_high = self.I(talib.MAX, self.data.High, timeperiod=20, name='FIB HIGH 🏔')
        self.min_low = self.I(talib.MIN, self.data.Low, timeperiod=20, name='FIB LOW 🏝')
        
    def next(self):
        # Skip initial bars
        if len(self.data) < 20:
            return
        
        # 🌌 Current Fibonacci Levels
        fib_high = self.max_high[-1]
        fib_low = self.min_low[-1]
        fib_range = fib_high - fib_low
        
        fib_levels = {
            '0.382': fib_high - fib_range * 0.382,
            '0.500': fib_high - fib_range * 0.5,
            '0.618': fib_high - fib_range * 0.618
        }
        
        # Current price action
        current_close = self.data.Close[-1]
        current_low = self.data.Low[-1]
        current_high = self.data.High[-1]
        
        # 🌠 Moon Dev's Special Divergence Detection
        bullish_div = (
            (current_low < self.data.Low[-2]) and 
            (self.rsi[-1] > self.rsi[-2]) and 
            (self.macd[-1][0] > self.macd[-2][0])
        )
        
        bearish_div = (
            (current_high > self.data.High[-2]) and 
            (self.rsi[-1] < self.rsi[-2]) and 
            (self.macd[-1][0] < self.macd[-2][0])
        )
        
        # 🌀 Fractal Confirmation
        fractal_buy_signal = current_low == self.swing_low[-1]
        fractal_sell_signal = current_high == self.swing_high[-1]
        
        # 🚀 Entry Logic
        if not self.position:
            # Long Entry: Bullish Divergence + Fib Support + Fractal Confirmation
            if (bullish_div and
                current_close <= fib_levels['0.618'] * 1.01 and  # Within 1% of 618
                fractal_buy_signal):
                
                # 🌕 Moon Risk Management
                risk_amount = self.initial_equity * self.risk_per_trade
                entry_price = current_close
                sl_price = 