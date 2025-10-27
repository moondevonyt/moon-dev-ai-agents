import numpy as np
import pandas as pd
from backtesting import Backtest, Strategy
import talib

def compute_up_fractals(high):
    up = pd.Series(np.nan, index=high.index)
    n = len(high)
    for i in range(2, n - 2):
        h2 = high.iloc[i]
        if (h2 > high.iloc[i - 1] and h2 > high.iloc[i - 2] and
            h2 > high.iloc[i + 1] and h2 > high.iloc[i + 2]):
            up.iloc[i] = h2
    return up

def compute_down_fractals(low):
    down = pd.Series(np.nan, index=low.index)
    n = len(low)
    for i in range(2, n - 2):
        l2 = low.iloc[i]
        if (l2 < low.iloc[i - 1] and l2 < low.iloc[i - 2] and
            l2 < low.iloc[i + 1] and l2 < low.iloc[i + 2]):
            down.iloc[i] = l2
    return down

class FractalCascade(Strategy):
    def init(self):
        median = (self.data.High + self.data.Low) / 2
        
        jaw_period = 13
        self.jaw = self.I(lambda s: s.ewm(alpha=1/jaw_period, adjust=False).mean(), median).shift(8)
        
        teeth_period = 8
        self.teeth = self.I(lambda s: s.ewm(alpha=1/teeth_period, adjust=False).mean(), median).shift(5)
        
        lips_period = 5
        self.lips = self.I(lambda s: s.ewm(alpha=1/lips_period, adjust=False).mean(), median).shift(3)
        
        ao_fast = 5
        ao_slow = 34
        smma_fast = self.I(lambda s: s.ewm(alpha=1/ao_fast, adjust=False).mean(), median)
        smma_slow = self.I(lambda s: s.ewm(alpha=1/ao_slow, adjust=False).mean(), median)
        self.ao = smma_fast - smma_slow
        
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        self.volume_ma = self.I(talib.SMA, self.data.Volume, timeperiod=20)
        
        self.up_fractal = self.I(compute_up_fractals, self.data.High)
        self.down_fractal = self.I(compute_down_fractals, self.data.Low)
        self.ffill_up = self.up_fractal.ffill()
        self.ffill_down = self.down_fractal.ffill()

    def next(self):
        if np.isnan(self.adx[-1]) or self.adx[-1] < 25:
            return

        risk_per_trade = 0.01
        risk_amount = risk_per_trade * self._broker.starting_cash
        entry_price = self.data.Close[-1]
        atr_buffer = self.atr[-1]

        if not self.position:
            # Long entry
            if (self.data.Close[-1] > self.lips[-1] and
                self.lips[-1] > self.teeth[-1] > self.jaw[-1] and
                self.ao[-1] > 0 and self.ao[-1] > self.ao[-2] and
                self.data.Volume[-1] > self.volume_ma[-1] and
                self.data.Close[-1] > self.ffill_up[-1] and
                self.data.Close[-2] <= self.ffill_up[-2]):
                
                sl = self.ffill_down[-1] - atr_buffer
                if sl < entry_price:
                    risk_dist = entry_price - sl
                    size = risk_amount / risk_dist
                    size = int(round(size))
                    if size > 0:
                        self.buy(size=size, sl=sl)
                        print(f"🌙 Moon Dev: Long entry at {entry_price:.2f}, Size: {size}, SL: {sl:.2f} 🚀")

            # Short entry
            elif (self.data.Close[-1] < self.lips[-1] and
                  self.lips[-1] < self.teeth[-1] < self.jaw[-1] and
                  self.ao[-1] < 0 and self.ao[-1] < self.ao[-2] and
                  self.data.Volume[-1] > self.volume_ma[-1] and
                  self.data.Close[-1] < self.ffill_down[-1] and
                  self.data.Close[-2] >= self.ffill_down[-2]):
                
                sl = self.ffill_up[-1] + atr_buffer
                if sl > entry_price:
                    risk_dist = sl - entry_price
                    size = risk_amount / risk_dist
                    size = int(round(size))
                    if size > 0:
                        self.sell(size=size, sl=sl)
                        print(f"🌙 Moon Dev: Short entry at {entry_price:.2f}, Size: {size}, SL: {sl:.2f} 📉")

        else:
            if self.position.is_long:
                # Trail stop for long
                if not np.isnan(self.down_fractal[-1]):
                    new_sl = self.down_fractal[-1] - atr_buffer
                    if new_sl > self.position.sl:
                        self.position.sl = new_sl
                        print(f"🌙 Moon Dev: Trailing SL long to {new_sl:.2f} ✨")
                
                # Exit conditions
                if self.data.Close[-1] < self.teeth[-1]:
                    self.position.close()
                    print(f"🌙 Moon Dev: Long exit - below Teeth 📉")
                elif self.data.Close[-1] < self.jaw[-1]:
                    self.position.close()
                    print(f"🌙 Moon Dev: Long hard exit - below Jaw 😤")
            
            elif self.position.is_short:
                # Trail stop for short
                if not np.isnan(self.up_fractal[-1]):
                    new_sl = self.up_fractal[-1] + atr_buffer
                    if new_sl < self.position.sl:
                        self.position.sl = new_sl
                        print(f"🌙 Moon Dev: Trailing SL short to {new_sl:.2f} ✨")
                
                # Exit conditions
                if self.data.Close[-1] > self.teeth[-1]:
                    self.position.close()
                    print(f"🌙 Moon Dev: Short exit - above Teeth 📈")
                elif self.data.Close[-1] > self.jaw[-1]:
                    self.position.close()
                    print(f"🌙 Moon Dev: Short hard exit - above Jaw 😤")

if __name__ == '__main__':
    data_path = '/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv'
    data = pd.read_csv(data_path, parse_dates=['datetime'], index_col='datetime')
    data.columns = data.columns.str.strip().str.lower()
    data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
    data = data.rename(columns={
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume'
    })
    bt = Backtest(data, FractalCascade, cash=1000000, commission=0.001)
    stats = bt.run()
    print(stats)