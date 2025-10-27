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
    # 🌙 OPTIMIZATION: Added ATR for dynamic SL/TP, EMA200 for trend filter, Volume MA for entry confirmation
    # Tightened RSI to 25/75 for stronger signals, increased risk to 2% for higher exposure, use float sizes
    # Replaced fixed % SL with 1.5*ATR, added 2:1 RR TP, added trend and volume filters to improve win rate and returns
    # Manual SL/TP checks for debug prints while maintaining structure
    def init(self):
        self.bb_upper, self.bb_middle, self.bb_lower = self.I(
            talib.BBANDS, self.data.Close, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0
        )
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        self.ema200 = self.I(talib.EMA, self.data.Close, timeperiod=200)
        self.vol_ma = self.I(talib.SMA, self.data.Volume, timeperiod=20)
        # 🌙 Store SL/TP for manual exit checks and prints
        self.sl = None
        self.tp = None

    def next(self):
        if len(self.data) < 200:  # 🌙 Increased from 20 to 200 for EMA200
            return

        # Exit logic for existing positions - manual checks for SL/TP with debug prints
        if self.position:
            if self.position.is_long:
                if self.data.Close[-1] <= self.sl:
                    self.position.close()
                    print(f"🌙 LONG EXIT SL at {self.data.Close[-1]:.2f} 💥 SL: {self.sl:.2f} 🚀")
                elif self.data.Close[-1] >= self.tp:
                    self.position.close()
                    print(f"🌙 LONG EXIT TP at {self.data.Close[-1]:.2f} 🎯 TP: {self.tp:.2f} 🚀")
            elif self.position.is_short:
                if self.data.Close[-1] >= self.sl:
                    self.position.close()
                    print(f"🌙 SHORT EXIT SL at {self.data.Close[-1]:.2f} 💥 SL: {self.sl:.2f} 📉")
                elif self.data.Close[-1] <= self.tp:
                    self.position.close()
                    print(f"🌙 SHORT EXIT TP at {self.data.Close[-1]:.2f} 🎯 TP: {self.tp:.2f} 📉")

        # Entry logic - no position
        else:
            # 🌙 Long entry: Tightened RSI<25, added trend (above EMA200) and volume (>avg) filters, ATR-based SL/TP
            if (self.data.Close[-1] <= self.bb_lower[-1] and 
                self.rsi[-1] < 25 and 
                self.data.Close[-1] > self.ema200[-1] and 
                self.data.Volume[-1] > self.vol_ma[-1]):
                entry_price = self.data.Close[-1]
                sl_distance = 1.5 * self.atr[-1]
                sl_price = entry_price - sl_distance
                tp_price = entry_price + 2 * sl_distance  # 2:1 RR
                if sl_distance > 0:
                    risk_amount = self.equity * 0.02  # Increased to 2% risk for higher returns
                    size = risk_amount / sl_distance  # Float size for precise sizing (no int rounding)
                    self.buy(size=size)
                    self.sl = sl_price
                    self.tp = tp_price
                    print(f"🚀 🌙 LONG ENTRY: Price {entry_price:.2f}, SL {sl_price:.2f}, TP {tp_price:.2f}, Size {size:.4f}, RSI {self.rsi[-1]:.2f}, Lower BB {self.bb_lower[-1]:.2f}, ATR {self.atr[-1]:.2f} ✨")

            # 🌙 Short entry: Tightened RSI>75, added trend (below EMA200) and volume (>avg) filters, ATR-based SL/TP
            elif (self.data.Close[-1] >= self.bb_upper[-1] and 
                  self.rsi[-1] > 75 and 
                  self.data.Close[-1] < self.ema200[-1] and 
                  self.data.Volume[-1] > self.vol_ma[-1]):
                entry_price = self.data.Close[-1]
                sl_distance = 1.5 * self.atr[-1]
                sl_price = entry_price + sl_distance
                tp_price = entry_price - 2 * sl_distance  # 2:1 RR
                if sl_distance > 0:
                    risk_amount = self.equity * 0.02  # Increased to 2% risk for higher returns
                    size = risk_amount / sl_distance  # Float size for precise sizing (no int rounding)
                    self.sell(size=size)
                    self.sl = sl_price
                    self.tp = tp_price
                    print(f"📉 🌙 SHORT ENTRY: Price {entry_price:.2f}, SL {sl_price:.2f}, TP {tp_price:.2f}, Size {size:.4f}, RSI {self.rsi[-1]:.2f}, Upper BB {self.bb_upper[-1]:.2f}, ATR {self.atr[-1]:.2f} ✨")

if __name__ == '__main__':
    bt = Backtest(data, VolatilityRebound, cash=1000000, commission=0.001, exclusive_orders=True)
    stats = bt.run()
    print(stats)