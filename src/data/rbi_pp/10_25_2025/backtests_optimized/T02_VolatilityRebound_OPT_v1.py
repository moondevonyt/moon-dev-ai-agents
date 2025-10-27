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
        # Original BB and RSI
        self.bb_upper, self.bb_middle, self.bb_lower = self.I(
            talib.BBANDS, self.data.Close, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0
        )
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14)
        
        # 🌙 OPTIMIZATION: Added ATR for better SL placement and volatility-based risk (replaces fixed 1% beyond band)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        
        # 🌙 OPTIMIZATION: Added trend filter with EMA 200 to only trade in favorable trend direction (long above EMA, short below)
        self.ema200 = self.I(talib.EMA, self.data.Close, timeperiod=200)
        
        # 🌙 OPTIMIZATION: Added volume SMA filter to confirm entries with above-average volume (avoids low-quality signals)
        self.vol_sma = self.I(talib.SMA, self.data.Volume, timeperiod=20)

    def next(self):
        if len(self.data) < 200:  # 🌙 OPTIMIZATION: Increased buffer to 200 for EMA initialization
            return

        # Exit logic for existing positions (unchanged, but now benefits from trend filter on entries)
        if self.position:
            if self.position.is_long and self.data.Close[-1] >= self.bb_middle[-1]:
                self.position.close()
                print(f"🌙 LONG EXIT at {self.data.Close[-1]:.2f} ✨ TP Middle: {self.bb_middle[-1]:.2f} 🚀")
            elif self.position.is_short and self.data.Close[-1] <= self.bb_middle[-1]:
                self.position.close()
                print(f"🌙 SHORT EXIT at {self.data.Close[-1]:.2f} ✨ TP Middle: {self.bb_middle[-1]:.2f} 📉")

        # Entry logic - no position
        else:
            # 🌙 OPTIMIZATION: Added volume filter (volume > 1.2x SMA) and trend filter (long only if above EMA200)
            vol_confirmation = self.data.Volume[-1] > 1.2 * self.vol_sma[-1]
            
            # Long entry - tightened RSI to <25 for stronger oversold, added filters
            if (self.data.Close[-1] <= self.bb_lower[-1] and 
                self.rsi[-1] < 25 and 
                self.data.Close[-1] > self.ema200[-1] and  # Trend filter
                vol_confirmation):
                entry_price = self.data.Close[-1]
                atr_value = self.atr[-1]
                sl_distance = 2 * atr_value  # 🌙 OPTIMIZATION: ATR-based SL distance (2x ATR for reasonable risk)
                sl_price = entry_price - sl_distance
                if sl_distance > 0:
                    risk_amount = self.equity * 0.01  # Keep 1% risk
                    size = risk_amount / sl_distance
                    size = max(1, int(round(size)))  # Ensure min size 1
                    self.buy(size=size, sl=sl_price)
                    print(f"🚀 🌙 LONG ENTRY: Price {entry_price:.2f}, SL {sl_price:.2f}, Size {size}, RSI {self.rsi[-1]:.2f}, Lower BB {self.bb_lower[-1]:.2f}, ATR {atr_value:.2f}, Vol Conf {vol_confirmation} ✨")

            # Short entry - tightened RSI to >75 for stronger overbought, added filters
            elif (self.data.Close[-1] >= self.bb_upper[-1] and 
                  self.rsi[-1] > 75 and 
                  self.data.Close[-1] < self.ema200[-1] and  # Trend filter
                  vol_confirmation):
                entry_price = self.data.Close[-1]
                atr_value = self.atr[-1]
                sl_distance = 2 * atr_value  # 🌙 OPTIMIZATION: ATR-based SL distance
                sl_price = entry_price + sl_distance
                if sl_distance > 0:
                    risk_amount = self.equity * 0.01  # Keep 1% risk
                    size = risk_amount / sl_distance
                    size = max(1, int(round(size)))  # Ensure min size 1
                    self.sell(size=size, sl=sl_price)
                    print(f"📉 🌙 SHORT ENTRY: Price {entry_price:.2f}, SL {sl_price:.2f}, Size {size}, RSI {self.rsi[-1]:.2f}, Upper BB {self.bb_upper[-1]:.2f}, ATR {atr_value:.2f}, Vol Conf {vol_confirmation} ✨")

if __name__ == '__main__':
    bt = Backtest(data, VolatilityRebound, cash=1000000, commission=0.001, exclusive_orders=True)
    stats = bt.run()
    print(stats)