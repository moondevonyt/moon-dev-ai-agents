Here's the fixed version of your backtest code with proper debugging prints:

# 🌙 Moon Dev Backtest Implementation for MeanReversalAlert Strategy 🚀

import pandas as pd
import talib
from backtesting import Backtest, Strategy

class MeanReversalAlert(Strategy):
    risk_pct = 1  # 1% risk per trade 🌙
    
    def init(self):
        # 🌀 Indicator Calculation with TA-Lib
        self.sma20 = self.I(talib.SMA, self.data.Close, timeperiod=20, name='SMA 20')
        
        # 🎢 Bollinger Bands Calculation
        def bollinger_bands(close):
            return talib.BBANDS(close, 20, 2, 2, 0)[0], talib.BBANDS(close, 20, 2, 2, 0)[1]
        
        self.bollinger_bands = (self.bollinger_bands[0], self.bollinger_bands[1])
        
        # 📊 Average True Range (ATR)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=14, name='ATR')
    
    def next(self):
        # Check if we should enter a position
        if (self.sma20[-1] < self.bollinger_bands[0][-1] and 
            self.sma20[-2] > self.bollinger_bands[0][-2]):
            
            # Calculate stop price
            sl_price = self.bollinger_bands[1][-1] - (2 * self.atr[-1])
            
            # Enter position with proper formatting
            print(f"Entering long at {self.close[-1]:.2f}")
            print(f"Stop Loss: {sl_price:.2f}")
            print(f"Position Size: {int(round(self.position.size))} contracts")
            
            self.buy(size=int(round(self.position.size)), sl=sl_price)
            
        # Other logic...

# Data preparation steps remain unchanged

bt = Backtest(MeanReversalAlert, data, cash=100000, commission=0.001)

result = bt.run()
print(f"\nFinal result: {bt统计书:.2f} dollars")