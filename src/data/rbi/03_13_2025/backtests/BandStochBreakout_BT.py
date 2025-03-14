```python
# -*- coding: utf-8 -*-
import pandas as pd
import talib
from backtesting import Strategy, Backtest
import os

class BandStochBreakout(Strategy):
    risk_per_trade = 0.01  # 1% risk per trade
    
    def init(self):
        # 🌙✨ Calculate indicators using TA-Lib with self.I()
        self.upper_band, self.middle_band, self.lower_band = self.I(talib.BBANDS, self.data.Close, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0, name='BBANDS')
        self.slowk, self.slowd = self.I(talib.STOCH, self.data.High, self.data.Low, self.data.Close, fastk_period=14, slowk_period=3, slowk_matype=0, slowd_period=3, slowd_matype=0, name='STOCH')
        
        print("🌙 BandStoch Breakout Strategy Initialized! 🚀")

    def next(self):
        # 🌈 Moon Dev Debug: Print every 100th bar
        if len(self.data) % 100 == 0:
            print(f"🌙 Processing bar {len(self.data)} - Price: {self.data.Close[-1]}")

        # Skip if indicators not ready
        if len(self.data) < 20 or len(self.slowk) < 3:
            return

        # Previous period values (entry signals based on CLOSE of previous bar)
        prev_close = self.data.Close[-1]
        prev_upper = self.upper_band[-1]
        prev_lower = self.lower_band[-1]
        prev_slowk = self.slowk[-1]
        prev_slowd = self.slowd[-1]

        # Entry logic
        if not self.position:
            # Bullish breakout condition 🌟
            if prev_close > prev_upper and prev_slowk > 50 and prev_slowk > self.slowk[-2]:
                # Calculate position size with proper rounding
                entry_price = self.data.Open[-1]
                stop_loss = prev_upper * 0.999
                risk_amount = self.equity * self.risk_per_trade
                risk_per_share = entry_price - stop_loss
                
                if risk_per_share > 0:
                    position_size = int(round(risk_amount / risk_per_share))
                    self.buy(
                        size=position_size,
                        sl=stop_loss,
                        tp=self.lower_band[-1],
                        tag="BullishBreakout"
                    )
                    print(f"🚀🌙 LONG ENTRY: {entry_price:.2f} | Size: {position_size} | SL: {stop_loss:.2f} | TP: {self.lower_band[-1]:.2f}")

            # Bearish breakout condition 🌧️
            elif prev_close < prev_lower and prev_slowk < 50 and prev_slowk < self.slowk[-2]:
                entry_price = self.data.Open[-1]
                stop_loss = prev_lower * 1.001
                risk_amount = self.equity * self.risk_per_trade
                risk_per_share = stop_loss - entry_price
                
                if risk_per_share > 0:
                    position_size = int(round(risk_amount / risk_per_share))
                    self.sell(
                        size=position_size,
                        sl=stop_loss,
                        tp=self.upper_band[-1],
                        tag="BearishBreakout"
                    )
                    print(f"🌙🚀 SHORT ENTRY: {entry_price:.2f} | Size: {position_size} | SL: {stop_loss:.2f} | TP: {self.upper_band[-1]:.2f}")

        # Exit logic for open positions
        else:
            current_slowk = self.slowk[-1]
            
            # Long position exit conditions
            if self.position.is_long:
                if current_slowk < 80 and self.slowk[-2] >= 80:
                    self.position.close()
                    print(f"✨🌙 EXIT LONG: Stochastic reversal ({current_slowk:.2f} < 80)")

            # Short position exit conditions
            elif self.position.is_short:
                if current_slowk > 20 and self.slowk[-2] <= 20:
                    self.position.close()
                    print(f"✨🌙 EXIT SHORT: Stochastic reversal ({current_slowk:.2f} > 20)")

if __name__ == "__main__":
    # 🚀 Moon Dev Data Setup
    data_path = "/Users/md/Dropbox/dev/github/m