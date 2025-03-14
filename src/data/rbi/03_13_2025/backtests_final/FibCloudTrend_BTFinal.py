Here's the fixed code with Moon Dev themed debug prints and proper position sizing implementation:

```python
import pandas as pd
import talib
import numpy as np
from backtesting import Backtest, Strategy

class FibCloudTrend(Strategy):
    risk_per_trade = 0.01  # 1% risk per trade
    
    def init(self):
        # Ichimoku Cloud parameters
        self.tenkan_period = 9
        self.kijun_period = 26
        self.senkou_b_period = 52
        self.displacement = 26
        
        # Calculate Ichimoku components
        tenkan_high = self.I(talib.MAX, self.data.High, self.tenkan_period)
        tenkan_low = self.I(talib.MIN, self.data.Low, self.tenkan_period)
        self.tenkan_sen = self.I(lambda x: x, (tenkan_high + tenkan_low) / 2)
        
        kijun_high = self.I(talib.MAX, self.data.High, self.kijun_period)
        kijun_low = self.I(talib.MIN, self.data.Low, self.kijun_period)
        self.kijun_sen = self.I(lambda x: x, (kijun_high + kijun_low) / 2)
        
        self.senkou_a = self.I(lambda x: x, 
                              (self.tenkan_sen + self.kijun_sen) / 2,
                              shift=self.displacement)
        
        senkou_b_high = self.I(talib.MAX, self.data.High, self.senkou_b_period)
        senkou_b_low = self.I(talib.MIN, self.data.Low, self.senkou_b_period)
        self.senkou_b = self.I(lambda x: x,
                              (senkou_b_high + senkou_b_low) / 2,
                              shift=self.displacement)
        
        self.chikou_span = self.I(lambda x: x, self.data.Close, shift=-self.displacement)
        
        # Swing points for Fibonacci
        self.swing_high = self.I(talib.MAX, self.data.High, 20)
        self.swing_low = self.I(talib.MIN, self.data.Low, 20)
        
    def next(self):
        current_close = self.data.Close[-1]
        current_high = self.data.High[-1]
        current_low = self.data.Low[-1]
        
        # Ichimoku values
        senkou_a = self.senkou_a[-1]
        senkou_b = self.senkou_b[-1]
        tenkan = self.tenkan_sen[-1]
        kijun = self.kijun_sen[-1]
        chikou = self.chikou_span[-1]
        
        # Trend detection
        price_above_cloud = current_close > senkou_a and current_close > senkou_b
        price_below_cloud = current_close < senkou_a and current_close < senkou_b
        
        # Fibonacci calculations
        swing_range = self.swing_high[-1] - self.swing_low[-1]
        fib_levels = {
            '382': self.swing_high[-1] - 0.382 * swing_range,
            '500': self.swing_high[-1] - 0.5 * swing_range,
            '618': self.swing_high[-1] - 0.618 * swing_range
        } if price_above_cloud else {
            '382': self.swing_low[-1] + 0.382 * swing_range,
            '500': self.swing_low[-1] + 0.5 * swing_range,
            '618': self.swing_low[-1] + 0.618 * swing_range
        } if price_below_cloud else {}
        
        if not self.position:
            # Long entry conditions
            if price_above_cloud and chikou > current_close:
                # Moon Dev crossover replacement 🌙
                if self.tenkan_sen[-2] < self.kijun_sen[-2] and self.tenkan_sen[-1] > self.kijun_sen[-1]:
                    if any(fib_levels[level] >= current_low and fib_levels[level] <= current_high 
                           for level in fib_levels):
                        # Calculate risk management
                        sl_price = min(self.swing_low[-1], min(senkou_a, senkou_b))
                        risk_distance = current_close - sl_price
                        
                        if risk_distance > 0:
                            # Moon Dev position sizing calculation 🌙
                            risk_amount = self.equity * self