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
        
        # 🌙 OPTIMIZATION: Added ATR for dynamic SL placement based on volatility (better risk management, avoids tight 1% band SL that stops out prematurely)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        
        # 🌙 OPTIMIZATION: Added ADX to filter for ranging markets (ADX < 25) - ideal for mean reversion strategies like BB rebounds, avoids trending losses
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        
        # 🌙 OPTIMIZATION: Added volume SMA filter to ensure entries on higher-than-average volume (confirms conviction, filters weak signals)
        self.vol_sma = self.I(talib.SMA, self.data.Volume, timeperiod=20)

    def next(self):
        if len(self.data) < 20:  # 🌙 Keep buffer for indicators
            return

        # Exit logic for existing positions (unchanged: exit at middle BB for mean reversion target)
        if self.position:
            if self.position.is_long and self.data.Close[-1] >= self.bb_middle[-1]:
                self.position.close()
                print(f"🌙 LONG EXIT at {self.data.Close[-1]:.2f} ✨ TP Middle: {self.bb_middle[-1]:.2f} 🚀")
            elif self.position.is_short and self.data.Close[-1] <= self.bb_middle[-1]:
                self.position.close()
                print(f"🌙 SHORT EXIT at {self.data.Close[-1]:.2f} ✨ TP Middle: {self.bb_middle[-1]:.2f} 📉")

        # Entry logic - no position
        else:
            current_close = self.data.Close[-1]
            current_volume = self.data.Volume[-1]
            
            # 🌙 OPTIMIZATION: Long entry - tightened RSI to <25 (stricter oversold), added ADX <25 (ranging filter), volume > SMA (conviction)
            if (current_close <= self.bb_lower[-1] and 
                self.rsi[-1] < 25 and 
                self.adx[-1] < 25 and 
                current_volume > self.vol_sma[-1]):
                
                entry_price = current_close
                # 🌙 OPTIMIZATION: SL now 2*ATR below entry (volatility-adjusted, wider than 1% band for better survival in noise)
                sl_price = entry_price - 2 * self.atr[-1]
                sl_distance = entry_price - sl_price
                if sl_distance > 0:
                    risk_amount = self.equity * 0.01
                    size = risk_amount / sl_distance  # 🌙 Allow float size for precise risking (no int rounding)
                    self.buy(size=size, sl=sl_price)
                    print(f"🚀 🌙 LONG ENTRY: Price {entry_price:.2f}, SL {sl_price:.2f}, Size {size:.4f}, RSI {self.rsi[-1]:.2f}, Lower BB {self.bb_lower[-1]:.2f}, ATR {self.atr[-1]:.2f}, ADX {self.adx[-1]:.2f}, Vol > SMA ✨")

            # 🌙 OPTIMIZATION: Short entry - symmetric changes: RSI >75, ADX <25, volume filter
            elif (current_close >= self.bb_upper[-1] and 
                  self.rsi[-1] > 75 and 
                  self.adx[-1] < 25 and 
                  current_volume > self.vol_sma[-1]):
                
                entry_price = current_close
                # 🌙 OPTIMIZATION: SL now 2*ATR above entry
                sl_price = entry_price + 2 * self.atr[-1]
                sl_distance = sl_price - entry_price
                if sl_distance > 0:
                    risk_amount = self.equity * 0.01
                    size = risk_amount / sl_distance  # Float size
                    self.sell(size=size, sl=sl_price)
                    print(f"📉 🌙 SHORT ENTRY: Price {entry_price:.2f}, SL {sl_price:.2f}, Size {size:.4f}, RSI {self.rsi[-1]:.2f}, Upper BB {self.bb_upper[-1]:.2f}, ATR {self.atr[-1]:.2f}, ADX {self.adx[-1]:.2f}, Vol > SMA ✨")

if __name__ == '__main__':
    bt = Backtest(data, VolatilityRebound, cash=1000000, commission=0.001, exclusive_orders=True)
    stats = bt.run()
    print(stats)