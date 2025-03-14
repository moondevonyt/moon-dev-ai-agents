# 🌙 MOON DEV BACKTESTING IMPLEMENTATION FOR RETRACEMENTCONTRA STRATEGY 🚀

from backtesting import Backtest, Strategy
import pandas as pd
import talib
import numpy as np

class RetracementContra(Strategy):
    risk_per_trade = 0.01  # 1% risk per trade
    atr_period = 14
    swing_period = 50
    rsi_period = 14
    sma_period = 50
    atr_contract_lookback = 5
    
    def init(self):
        # 🌙 CORE INDICATORS
        self.swing_high = self.I(talib.MAX, self.data.High, self.swing_period, name='SWING HIGH')
        self.swing_low = self.I(talib.MIN, self.data.Low, self.swing_period, name='SWING LOW')
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, self.atr_period)
        self.rsi = self.I(talib.RSI, self.data.Close, self.rsi_period)
        self.sma = self.I(talib.SMA, self.data.Close, self.sma_period)
        
        # 🌙 DERIVED VALUES
        self.upper_band = self.I(lambda: self.sma + 2*self.atr, name='UPPER BAND')
        self.lower_band = self.I(lambda: self.sma - 2*self.atr, name='LOWER BAND')
        
        self.peak_equity = self._broker._cash  # Track peak for drawdown calculation

    def next(self):
        # 🌙 UPDATE PEAK EQUITY
        self.peak_equity = max(self.peak_equity, self.equity)
        
        # 🚨 RISK MANAGEMENT: MAX DRAWDOWN CHECK
        current_drawdown = (self.peak_equity - self.equity)/self.peak_equity
        if current_drawdown >= 0.2:
            self.position.close()
            print(f"🚨 MOON DEV ALERT: 20% Max Drawdown Triggered! Equity: {self.equity:,.2f}")  # DEBUG: BACKTESTING.LIB NOT USED HERE
            return

        if self.position:
            # 🌈 EXIT LOGIC: BREAKOUT FROM ATR BANDS
            if self.data.Close[-1] > self.upper_band[-1] or self.data.Close[-1] < self.lower_band[-1]:
                self.position.close()
                print(f"🌙✨ Exit Signal: Price broke ATR bands! Closing at {self.data.Close[-1]:.2f}")  # DEBUG: BACKTESTING.LIB NOT USED HERE
        else:
            # 🎯 ENTRY CONDITIONS
            swing_high = self.swing_high[-1]
            swing_low = self.swing_low[-1]
            fib_range = swing_high - swing_low
            
            # 🌌 FIBONACCI LEVELS
            fib_levels = {
                '236': swing_low + 0.236 * fib_range,
                '382': swing_low + 0.382 * fib_range,
                '50': swing_low + 0.5 * fib_range
            }
            
            # 🎚 VOLATILITY CONTRACTION CHECK
            current_atr = self.atr[-1]
            atr_contract = current_atr < np.nanmean(self.atr[-self.atr_contract_lookback:])  # DEBUG: BACKTESTING.LIB NOT USED HERE
            
            # 💡 ENTRY LOGIC
            if (self.data.Close[-1] > self.sma[-1] and  # Uptrend check
                any(abs(self.data.Low[-1] - lvl) < 0.005*self.data.Close[-1] for lvl in fib_levels.values()) and  # Fib touch
                self.rsi[-1] < 30 and  # Oversold
                atr_contract):  # Vol contraction
                
                # � RISK CALCULATION
                stop_loss = swing_low
                risk_amount = self.risk_per_trade * self.equity
                risk_per_share = self.data.Close[-1] - stop_loss
                
                if risk_per_share <= 0: return
                
                position_size = int(round(risk_amount / risk_per_share))
                position_size = min(position_size, int(self.equity // self.data.Close[-1]))
                
                if position_size > 0:
                    self.buy(size=position_size, sl=stop_loss)
                    print(f"🌙🚀 ENTRY: {position_size} units at {self.data.Close[-1]:.2f}")  # DEBUG: BACKTESTING.LIB NOT USED HERE