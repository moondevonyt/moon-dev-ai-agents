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
    def init(self):
        self.bb_upper, self.bb_middle, self.bb_lower = self.I(
            talib.BBANDS, self.data.Close, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0
        )
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14)

    def next(self):
        if len(self.data) < 20:
            return

        # Exit logic for existing positions
        if self.position:
            if self.position.is_long and self.data.Close[-1] >= self.bb_middle[-1]:
                self.position.close()
                print(f"🌙 LONG EXIT at {self.data.Close[-1]:.2f} ✨ TP Middle: {self.bb_middle[-1]:.2f} 🚀")
            elif self.position.is_short and self.data.Close[-1] <= self.bb_middle[-1]:
                self.position.close()
                print(f"🌙 SHORT EXIT at {self.data.Close[-1]:.2f} ✨ TP Middle: {self.bb_middle[-1]:.2f} 📉")

        # Entry logic - no position
        else:
            # Long entry
            if self.data.Close[-1] <= self.bb_lower[-1] and self.rsi[-1] < 30:
                entry_price = self.data.Close[-1]
                sl_price = self.bb_lower[-1] * 0.99  # 1% below lower band
                sl_distance = entry_price - sl_price
                if sl_distance > 0:
                    risk_amount = self.equity * 0.01
                    size = risk_amount / sl_distance
                    size = int(round(size))
                    self.buy(size=size, sl=sl_price)
                    print(f"🚀 🌙 LONG ENTRY: Price {entry_price:.2f}, SL {sl_price:.2f}, Size {size}, RSI {self.rsi[-1]:.2f}, Lower BB {self.bb_lower[-1]:.2f} ✨")

            # Short entry
            elif self.data.Close[-1] >= self.bb_upper[-1] and self.rsi[-1] > 70:
                entry_price = self.data.Close[-1]
                sl_price = self.bb_upper[-1] * 1.01  # 1% above upper band
                sl_distance = sl_price - entry_price
                if sl_distance > 0:
                    risk_amount = self.equity * 0.01
                    size = risk_amount / sl_distance
                    size = int(round(size))
                    self.sell(size=size, sl=sl_price)
                    print(f"📉 🌙 SHORT ENTRY: Price {entry_price:.2f}, SL {sl_price:.2f}, Size {size}, RSI {self.rsi[-1]:.2f}, Upper BB {self.bb_upper[-1]:.2f} ✨")

if __name__ == '__main__':
    bt = Backtest(data, VolatilityRebound, cash=1000000, commission=0.001, exclusive_orders=True)
    stats = bt.run()
    print(stats)