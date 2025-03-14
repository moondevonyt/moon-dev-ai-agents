```python
# 🌙 MOON DEV BACKTESTING IMPLEMENTATION FOR VOLATILEREVERSION STRATEGY 🚀✨

import pandas as pd
import talib
import pandas_ta as ta
from backtesting import Backtest, Strategy

class VolatileReversion(Strategy):
    risk_per_trade = 0.01  # 1% risk per trade
    max_exposure = 0.05    # 5% maximum exposure
    daily_loss_limit = 0.03
    weekly_dd_limit = 0.07
    
    def init(self):
        # 🌙 INDICATORS USING TA-LIB WITH SELF.I() WRAPPER
        self.rsi = self.I(talib.RSI, self.data.Close, 14, name='RSI')
        
        # MACD components
        self.macd, self.macd_signal, self.macd_hist = (
            self.I(lambda c: talib.MACD(c, 12, 26, 9)[i], self.data.Close, 
                  name=['MACD', 'SIGNAL', 'HIST'][i]) 
            for i in range(3)
        )
        
        # Volatility indicators
        self.vix = self.I(ta.vix, self.data.High, self.data.Low, self.data.Close, 20, name='VIX')
        self.vix_sma = self.I(talib.SMA, self.vix, 20, name='VIX_SMA')
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, 14, name='ATR')
        
        # Swing detection
        self.price_swing_high = self.I(talib.MAX, self.data.High, 20, name='SWING_HIGH')
        self.price_swing_low = self.I(talib.MIN, self.data.Low, 20, name='SWING_LOW')
        self.macd_swing_high = self.I(talib.MAX, self.macd_hist, 20, name='MACD_HIGH')
        self.macd_swing_low = self.I(talib.MIN, self.macd_hist, 20, name='MACD_LOW')
        
        # Risk management trackers
        self.daily_high = self.weekly_high = self.equity

    def next(self):
        # 🌙 RISK MANAGEMENT CHECKS FIRST
        current_date = self.data.index[-1].date()
        current_week = current_date.isocalendar()[1]
        
        # Update equity highs
        self.daily_high = max(self.daily_high, self.equity)
        self.weekly_high = max(self.weekly_high, self.equity)
        
        # Check daily loss limit
        if (self.daily_high - self.equity)/self.daily_high >= self.daily_loss_limit:
            self.position.close()
            print(f"🌙🚨 DAILY LOSS LIMIT HIT! {self.equity:.2f}")
            return
            
        # Check weekly drawdown
        if (self.weekly_high - self.equity)/self.weekly_high >= self.weekly_dd_limit:
            self.position.close()
            print(f"🌙🚨 WEEKLY DRAWDOWN LIMIT! {self.equity:.2f}")
            return
            
        # 🌙 EXIT CONDITIONS
        if self.position:
            vix_spike = self.vix[-1] > self.vix_sma[-1]*1.15
            rsi_exit_long = (self.rsi[-2] < 40 and self.rsi[-1] > 40)  # Replaced crossover
            rsi_exit_short = (60 < self.rsi[-2] and 60 > self.rsi[-1])  # Replaced crossover
            
            if vix_spike:
                self.position.close()
                print(f"🌙✨ VIX SPIKE EXIT | Equity: {self.equity:.2f}")
            elif self.position.is_long and rsi_exit_long:
                self.position.close()
                print(f"🌙🌟 RSI NEUTRAL EXIT | Equity: {self.equity:.2f}")
            elif self.position.is_short and rsi_exit_short:
                self.position.close()
                print(f"🌙🌟 RSI NEUTRAL EXIT | Equity: {self.equity:.2f}")

        # 🌙 ENTRY CONDITIONS
        if not self.position:
            # Long Entry Conditions
            rsi_long = self.rsi[-1] < 30
            macd_div_long