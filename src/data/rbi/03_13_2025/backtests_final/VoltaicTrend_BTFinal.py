I'll help fix the code while maintaining the strategy logic. Here's the corrected version with Moon Dev themed debug prints and proper position sizing:

```python
# 🌙 Moon Dev's VoltaicTrend Backtest Implementation ✨
import pandas as pd
import numpy as np
import talib
from backtesting import Backtest, Strategy

class VoltaicTrend(Strategy):
    ema_short = 20
    ema_long = 50
    bb_period = 20
    bb_dev = 2
    rsi_period = 14
    risk_pct = 0.01  # 1% risk per trade
    
    def init(self):
        # 🌟 Trend Identification
        self.ema20 = self.I(talib.EMA, self.data.Close, timeperiod=self.ema_short)
        self.ema50 = self.I(talib.EMA, self.data.Close, timeperiod=self.ema_long)
        
        # 🌪️ Volatility Filter
        self.bb_upper, self.bb_middle, self.bb_lower = self.I(
            self._bollinger_bands, name=['BB_Upper', 'BB_Middle', 'BB_Lower']
        )
        self.bbw = self.I(self._bb_width)
        
        # 💪 Momentum Confirmation
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=self.rsi_period)
        
        # 🏔️ Swing Lows for Stop Loss
        self.swing_low = self.I(talib.MIN, self.data.Low, timeperiod=20)
        
        print("✨ Moon Dev Indicators Activated! ✨")

    def _bollinger_bands(self, close):
        upper, middle, lower = talib.BBANDS(
            close, timeperiod=self.bb_period,
            nbdevup=self.bb_dev, nbdevdn=self.bb_dev
        )
        return upper, middle, lower

    def _bb_width(self, close):
        upper, middle, lower = talib.BBANDS(
            close, timeperiod=self.bb_period,
            nbdevup=self.bb_dev, nbdevdn=self.bb_dev
        )
        return (upper - lower) / middle

    def next(self):
        # 🌙 Debug Dashboard
        print(f"🌙 Close: {self.data.Close[-1]:.2f} | EMA20/50: {self.ema20[-1]:.2f}/{self.ema50[-1]:.2f} | RSI: {self.rsi[-1]:.2f} | BWW: {self.bbw[-1]:.4f}")

        if not self.position:
            # 🚀 Entry Logic
            if (self.ema20[-2] < self.ema50[-2] and self.ema20[-1] > self.ema50[-1] and  # Bullish EMA crossover
                self.bbw[-1] > self.bbw[-2] and
                self.rsi[-1] > 50):
                
                # 🛑 Risk Calculation
                stop_price = min(self.swing_low[-1], self.bb_lower[-1])
                risk_amount = self.equity * self.risk_pct
                risk_per_share = self.data.Close[-1] - stop_price
                
                if risk_per_share <= 0:
                    print("🌑 Abort Launch! Negative risk detected")
                    return
                
                position_size = int(round(risk_amount / risk_per_share))
                
                # 🚀 Execute Launch
                self.buy(size=position_size, sl=stop_price)
                print(f"🚀 LIFTOFF! Long {position_size} shares at {self.data.Close[-1]:.2f}")
        
        else:
            # 🛬 Exit Logic
            exit_trade = False
            
            # 📉 BWW Contraction
            if self.bbw[-1] < self.bbw[-2]:
                exit_trade = True
                print("🌒 BWW Shrinking!")
                
            # 📉 RSI Divergence
            if (self.data.High[-1] > self.data.High[-2] and
                self.rsi[-1] < self.rsi[-2]):
                exit_trade = True
                print("🌓 RSI Divergence Detected!")
                
            # 📉 EMA Crossover
            if self.ema50[-2] > self.ema20[-2] and self.ema50[-1] < self.ema20[-1]:  # Bearish EMA crossover
                exit_trade = True
                print("🌔 EMA Death Cross!")
                
            # 🛑 Trailing Stop
            trailing_stop = max