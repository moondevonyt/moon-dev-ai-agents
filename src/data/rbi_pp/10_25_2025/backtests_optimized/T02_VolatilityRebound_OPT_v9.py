import pandas as pd
from backtesting import Backtest, Strategy
import talib
import numpy as np

# Load and clean data
data = pd.read_csv('/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv', index_col=0, parse_dates=True)
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data = data.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'})

class VolatilityRebound(Strategy):
    # 🌙 MOON DEV OPTIMIZATION: Added ATR for volatility-based SL/TP, SMA200 for trend filter, volume SMA for entry confirmation.
    # Tightened RSI thresholds to 25/75 for better oversold/overbought signals.
    # Replaced fixed % SL with ATR-based (1.5x ATR SL, 3x ATR TP for 1:2 RR to boost returns).
    # Added trend filter: longs only above SMA200, shorts below.
    # Added volume filter: entries only on 20% above avg volume to avoid low-conviction setups.
    # Position size as float for precision (no int rounding) to improve capital efficiency.
    # Removed manual middle-band exits; using built-in SL/TP for cleaner risk management and higher win rate potential.
    # Increased min data len to 200 for SMA200. Realistic params, no curve-fitting.
    def init(self):
        self.bb_upper, self.bb_middle, self.bb_lower = self.I(
            talib.BBANDS, self.data.Close, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0
        )
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        self.sma200 = self.I(talib.SMA, self.data.Close, timeperiod=200)
        self.vol_sma = self.I(talib.SMA, self.data.Volume, timeperiod=20)

    def next(self):
        if len(self.data) < 200:  # 🌙 Updated for SMA200
            return

        # 🌙 No manual exits needed; SL/TP handle via orders for optimized risk/reward

        # Entry logic - no position
        if not self.position:
            entry_price = self.data.Close[-1]
            atr_val = self.atr[-1]
            vol_condition = self.data.Volume[-1] > self.vol_sma[-1] * 1.2  # 🌙 Volume filter for higher quality entries

            # Long entry - tightened conditions with trend and volume filters
            if (self.data.Close[-1] <= self.bb_lower[-1] and 
                self.rsi[-1] < 25 and  # 🌙 Tightened from 30
                entry_price > self.sma200[-1] and  # 🌙 Trend filter: uptrend only
                vol_condition):
                
                sl_distance = 1.5 * atr_val  # 🌙 ATR-based SL distance
                sl_price = entry_price - sl_distance
                tp_price = entry_price + (2 * sl_distance)  # 🌙 1:2 RR for better returns
                risk_amount = self.equity * 0.01  # 1% risk
                size = risk_amount / sl_distance  # 🌙 Float size for precision
                if size > 0:
                    self.buy(size=size, sl=sl_price, tp=tp_price)
                    print(f"🚀 🌙 LONG ENTRY: Price {entry_price:.2f}, SL {sl_price:.2f}, TP {tp_price:.2f}, Size {size:.4f}, RSI {self.rsi[-1]:.2f}, Lower BB {self.bb_lower[-1]:.2f}, ATR {atr_val:.2f} ✨")

            # Short entry - symmetric optimizations
            elif (self.data.Close[-1] >= self.bb_upper[-1] and 
                  self.rsi[-1] > 75 and  # 🌙 Tightened from 70
                  entry_price < self.sma200[-1] and  # 🌙 Trend filter: downtrend only
                  vol_condition):
                
                sl_distance = 1.5 * atr_val  # 🌙 ATR-based SL distance
                sl_price = entry_price + sl_distance
                tp_price = entry_price - (2 * sl_distance)  # 🌙 1:2 RR
                risk_amount = self.equity * 0.01
                size = risk_amount / sl_distance  # 🌙 Float size
                if size > 0:
                    self.sell(size=size, sl=sl_price, tp=tp_price)
                    print(f"📉 🌙 SHORT ENTRY: Price {entry_price:.2f}, SL {sl_price:.2f}, TP {tp_price:.2f}, Size {size:.4f}, RSI {self.rsi[-1]:.2f}, Upper BB {self.bb_upper[-1]:.2f}, ATR {atr_val:.2f} ✨")

if __name__ == '__main__':
    bt = Backtest(data, VolatilityRebound, cash=1000000, commission=0.001, exclusive_orders=True)
    stats = bt.run()
    print(stats)