Here's the debugged and fixed version of your backtest code with Moon Dev themed debug prints and proper position sizing:

```python
import pandas as pd
import numpy as np
import talib
from backtesting import Backtest, Strategy

class HarmonicConvergence(Strategy):
    n_period = 14
    risk_percent = 0.01
    rr_ratio = 2
    swing_period = 20

    def init(self):
        # Clean and map data columns
        self.data.df.columns = self.data.df.columns.str.strip().str.lower()
        self.data.df = self.data.df.drop(columns=[col for col in self.data.df.columns if 'unnamed' in col])
        
        # Calculate indicators
        self.sma50 = self.I(talib.SMA, self.data.Close, timeperiod=50)
        self.sma200 = self.I(talib.SMA, self.data.Close, timeperiod=200)
        self.swing_low = self.I(talib.MIN, self.data.Low, timeperiod=self.swing_period)
        self.swing_high = self.I(talib.MAX, self.data.High, timeperiod=self.swing_period)
        self.ema = self.I(talib.EMA, self.data.Close, timeperiod=self.n_period)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=self.n_period)
        
        # Initialize HO tracking
        self.prev_ho = 0

    def next(self):
        # Wait for all indicators to be ready
        if len(self.data) < 200 or np.isnan([self.sma50[-1], self.sma200[-1], self.swing_low[-1], self.ema[-1], self.atr[-1]]).any():
            return

        # Calculate Harmonic Oscillator
        current_close = self.data.Close[-1]
        current_ema = self.ema[-1]
        current_atr = self.atr[-1] if self.atr[-1] > 0 else 1
        current_ho = (current_close - current_ema) / current_atr * 100

        # Entry/exit logic
        if not self.position:
            # Long entry conditions
            if self.sma50[-1] > self.sma200[-1] and current_ho > 0 and self.prev_ho <= 0:
                sl_price = self.swing_low[-1]
                risk_per_share = current_close - sl_price
                if risk_per_share > 0:
                    position_size = int(round((self.risk_percent * self.equity) / risk_per_share))
                    tp_price = current_close + self.rr_ratio * risk_per_share
                    if position_size > 0:
                        self.buy(size=position_size, sl=sl_price, tp=tp_price)
                        print(f"🌙🚀 BULLISH CONVERGENCE! LONG {position_size} @ {current_close:.2f}")
                        print(f"   🛡️ SL: {sl_price:.2f}, 🎯 TP: {tp_price:.2f}")

            # Short entry conditions
            elif self.sma50[-1] < self.sma200[-1] and current_ho < 0 and self.prev_ho >= 0:
                sl_price = self.swing_high[-1]
                risk_per_share = sl_price - current_close
                if risk_per_share > 0:
                    position_size = int(round((self.risk_percent * self.equity) / risk_per_share))
                    tp_price = current_close - self.rr_ratio * risk_per_share
                    if position_size > 0:
                        self.sell(size=position_size, sl=sl_price, tp=tp_price)
                        print(f"🌙🌒 BEARISH DIVERGENCE! SHORT {position_size} @ {current_close:.2f}")
                        print(f"   🛡️ SL: {sl_price:.2f}, 🎯 TP: {tp_price:.2f}")

        else:
            # Exit conditions
            if self.position.is_long:
                if current_ho < 0 or self.sma50[-1] < self.sma200[-1]:
                    self.position.close()
                    print(f"🌙✨ CLOSING LONG @ {current_close:.2f} - {'HO Reversal' if current_ho < 0 else 'MA Bearish Flip'}")

            elif self.position.is_short:
                if current_ho > 0 or self.sma50[-1] > self.sma200[-1]:
                    self.position.close()
                    print(f"🌙✨ CLOSING SHORT