Here's the fixed and complete backtest code with Moon Dev themed debug prints and proper position sizing implementation:

```python
# 🌙 MOON DEV BACKTESTING IMPLEMENTATION FOR DIVERGENTCONVERGENCE STRATEGY ✨

import pandas as pd
import talib
from backtesting import Backtest, Strategy

class DivergentConvergence(Strategy):
    # Strategy parameters
    rsi_period = 14
    stoch_fastk = 14
    stoch_slowk = 3
    stoch_slowd = 3
    swing_period = 20
    risk_pct = 0.01  # 1% risk per trade
    rr_ratio = 2
    
    def init(self):
        # 🌙 Calculate indicators using TA-Lib with self.I()
        self.rsi = self.I(talib.RSI, self.data.Close, self.rsi_period)
        
        # Calculate Stochastic values
        def stoch(h, l, c):
            k, d = talib.STOCH(h, l, c,
                              fastk_period=self.stoch_fastk,
                              slowk_period=self.stoch_slowk,
                              slowd_period=self.stoch_slowd)
            return k, d
        
        self.stoch_k, self.stoch_d = self.I(stoch, self.data.High, self.data.Low, self.data.Close)
        
        # Swing high/low calculations
        self.swing_high = self.I(talib.MAX, self.data.High, self.swing_period)
        self.swing_low = self.I(talib.MIN, self.data.Low, self.swing_period)
        
    def next(self):
        # Wait until we have enough historical data
        if len(self.data) < self.swing_period + 2:
            return
            
        # 🌙 MOON DEV DEBUG: Print current candle status 🕯️
        print(f"\n🌙 Processing {self.data.index[-1]} | Close: {self.data.Close[-1]:.2f} 🌈")
        
        # Check for existing positions
        if self.position:
            return
            
        # Calculate current indicator values
        current_close = self.data.Close[-1]
        current_rsi = self.rsi[-1]
        prev_rsi = self.rsi[-2]
        
        # 🚀 Detect RSI divergence
        price_lower_low = (self.data.Low[-1] < self.data.Low[-2]) and (self.data.Close[-1] < self.data.Close[-2])
        rsi_higher_low = current_rsi > prev_rsi
        bullish_div = price_lower_low and rsi_higher_low
        
        price_higher_high = (self.data.High[-1] > self.data.High[-2]) and (self.data.Close[-1] > self.data.Close[-2])
        rsi_lower_high = current_rsi < prev_rsi
        bearish_div = price_higher_high and rsi_lower_high
        
        # 🌟 Detect Stochastic convergence
        stoch_oversold = (self.stoch_k[-1] < 20) and (self.stoch_d[-1] < 20)
        stoch_overbought = (self.stoch_k[-1] > 80) and (self.stoch_d[-1] > 80)
        
        # ✨ Replace crossover with manual detection
        stoch_bullish = (self.stoch_k[-2] < self.stoch_d[-2]) and (self.stoch_k[-1] > self.stoch_d[-1])
        stoch_bearish = (self.stoch_k[-2] > self.stoch_d[-2]) and (self.stoch_k[-1] < self.stoch_d[-1])
        
        # ✨ Entry conditions
        if bullish_div and stoch_bullish and stoch_oversold:
            self.enter_long()
        elif bearish_div and stoch_bearish and stoch_overbought:
            self.enter_short()
            
    def enter_long(self):
        # 🌙 Calculate risk parameters
        sl_price = self.swing_low[-1]
        entry_price = self.data.Close[-1]
        risk_per_share = entry_price - sl_price
        
        if risk_per_share <= 0:
            print("🌙 Invalid SL for long entry, skipping 🌌")
            return
            
        # 🚀 Position sizing calculation
        risk_amount = self.risk_pct * self.equity
        position_size = int(round(risk_amount / risk_per_share))
        position_size = min(position_size, int(self.equity // entry_price))
        
        if position_size > 0:
            tp_price = entry_price + (self