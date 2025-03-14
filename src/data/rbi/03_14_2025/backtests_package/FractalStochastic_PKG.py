I've analyzed the code and found the `backtesting.lib` import and usage. Here's the fixed version with proper Moon Dev themed debug prints and all necessary replacements:

```python
# -*- coding: utf-8 -*-
import pandas as pd
from backtesting import Backtest, Strategy
import talib

class FractalStochastic(Strategy):
    risk_percent = 0.01  # 1% risk per trade
    
    def init(self):
        # Calculate fractal channels
        self.upper_fractal = self.I(talib.MAX, self.data.High, timeperiod=20, name='Upper Fractal 🌄')
        self.lower_fractal = self.I(talib.MIN, self.data.Low, timeperiod=20, name='Lower Fractal 🌊')
        
        # Calculate Stochastic Oscillator
        stoch_k, stoch_d = self.I(
            lambda high, low, close: talib.STOCH(high, low, close,
                                                fastk_period=14,
                                                slowk_period=3,
                                                slowk_matype=0,
                                                slowd_period=3,
                                                slowd_matype=0),
            self.data.High, self.data.Low, self.data.Close,
            name=['%K 🚀', '%D 🌙']
        )
        self.stoch_k = stoch_k
        self.stoch_d = stoch_d

    def next(self):
        # Wait for enough bars to be available
        if len(self.data) < 20:
            return

        # Get indicator values
        current_close = self.data.Close[-1]
        prev_upper = self.upper_fractal[-2]  # Previous fractal values
        prev_lower = self.lower_fractal[-2]
        
        current_k = self.stoch_k[-1]
        current_d = self.stoch_d[-1]
        prev_k = self.stoch_k[-2]
        prev_d = self.stoch_d[-2]

        # Long Entry Logic 🌙
        if (not self.position.is_long and
            current_close > prev_upper and
            current_k > current_d and
            prev_k < prev_d and
            current_k < 20):
            
            sl_price = prev_lower * 0.995  # Stop below fractal
            risk_per_share = current_close - sl_price
            if risk_per_share > 0:
                risk_amount = self.risk_percent * self.equity
                position_size = int(round(risk_amount / risk_per_share))
                if position_size > 0:
                    self.buy(size=position_size, sl=sl_price, 
                            tp=current_close + 3*risk_per_share)  # 3:1 RR
                    print(f"🌙✨🚀 BULLISH BREAKOUT! Long {position_size} @ {current_close:.2f} | SL: {sl_price:.2f}")

        # Short Entry Logic 🌙
        elif (not self.position.is_short and
              current_close < prev_lower and
              current_k < current_d and
              prev_k > prev_d and
              current_k > 80):
            
            sl_price = prev_upper * 1.005  # Stop above fractal
            risk_per_share = sl_price - current_close
            if risk_per_share > 0:
                risk_amount = self.risk_percent * self.equity
                position_size = int(round(risk_amount / risk_per_share))
                if position_size > 0:
                    self.sell(size=position_size, sl=sl_price, 
                             tp=current_close - 3*risk_per_share)  # 3:1 RR
                    print(f"🌙✨🚀 BEARISH BREAKDOWN! Short {position_size} @ {current_close:.2f} | SL: {sl_price:.2f}")

        # Close trades if opposite fractal breaks 🌙
        for trade in self.trades:
            if trade.is_long and (self.data.Low[-2] > self.lower_fractal[-2] and self.data.Low[-1] < self.lower_fractal[-1]):
                trade.close()
                print(f"🌙✨⚠️ LONG EXIT: Price hit lower fractal @ {self.data.Low[-1]:.2f}")
            elif trade.is_short and (self.upper_fractal[-2] < self.data.High[-2] and self.upper_fractal[-1] > self.data.High[-1]):
                trade.close()
                print(f"🌙✨⚠️ SHORT EXIT: Price hit upper fractal @ {self.data.High[-1]:.2f}")

# Data preparation 🌙
data = pd.read_csv('/Users/md/Dropbox