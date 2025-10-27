import talib
from backtesting import Backtest, Strategy
import pandas as pd
import numpy as np

class VolatilityReversion(Strategy):
    bb_period = 20
    bb_std = 2
    rsi_period = 14
    adx_period = 14
    rsi_low = 30
    rsi_high = 70
    adx_max = 25
    risk_pct = 0.01

    def init(self):
        bb = self.I(talib.BBANDS, self.data.Close, timeperiod=self.bb_period,
                    nbdevup=self.bb_std, nbdevdn=self.bb_std, matype=0)
        self.bb_upper = bb[0]
        self.bb_middle = bb[1]
        self.bb_lower = bb[2]
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=self.rsi_period)
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=self.adx_period)
        print("🌙 Moon Dev: Indicators initialized for VolatilityReversion strategy ✨")

    def next(self):
        current_close = self.data.Close[-1]
        
        # Exit logic
        if self.position:
            if self.position.is_long and current_close > self.bb_middle[-1]:
                self.position.close()
                print(f"🌙 Moon Dev: Exiting long position at {current_close:.2f} - Reversion to middle band achieved! ✨")
            elif self.position.is_short and current_close < self.bb_middle[-1]:
                self.position.close()
                print(f"🌙 Moon Dev: Exiting short position at {current_close:.2f} - Reversion to middle band achieved! ✨")
        
        # Entry logic
        if not self.position:
            risk_amount = self.equity * self.risk_pct
            
            # Long entry
            if (current_close < self.bb_lower[-1] and
                self.rsi[-1] < self.rsi_low and
                self.adx[-1] < self.adx_max):
                
                distance = self.bb_middle[-1] - self.bb_lower[-1]
                stop_price = self.bb_lower[-1] - 1.5 * distance
                entry_price = current_close
                stop_distance = entry_price - stop_price
                
                if stop_distance > 0:
                    size = risk_amount / stop_distance
                    if size > 0:
                        self.buy(size=int(round(size)), sl=stop_price)
                        print(f"🚀 Moon Dev: Long entry at {entry_price:.2f}, size {size:.6f} BTC, stop {stop_price:.2f}, risk {risk_amount:.2f} USD 🌙")
            
            # Short entry
            elif (current_close > self.bb_upper[-1] and
                  self.rsi[-1] > self.rsi_high and
                  self.adx[-1] < self.adx_max):
                
                distance = self.bb_upper[-1] - self.bb_middle[-1]
                stop_price = self.bb_upper[-1] + 1.5 * distance
                entry_price = current_close
                stop_distance = stop_price - entry_price
                
                if stop_distance > 0:
                    size = risk_amount / stop_distance
                    if size > 0:
                        self.sell(size=int(round(size)), sl=stop_price)
                        print(f"🚀 Moon Dev: Short entry at {entry_price:.2f}, size {size:.6f} BTC, stop {stop_price:.2f}, risk {risk_amount:.2f} USD 🌙")

path = "/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv"
df = pd.read_csv(path, parse_dates=['datetime'], index_col='datetime')

# Clean column names
df.columns = df.columns.str.strip().str.lower()
df = df.drop(columns=[col for col in df.columns if 'unnamed' in col.lower()])

# Ensure proper column mapping
df = df.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
})

print(f"🌙 Moon Dev: Data loaded and cleaned. Shape: {df.shape} ✨")

bt = Backtest(df, VolatilityReversion, cash=1000000, commission=0.002, exclusive_orders=True)
stats = bt.run()
print(stats)
print(stats._strategy)
print("🌙 Moon Dev Backtest Complete! 🚀")