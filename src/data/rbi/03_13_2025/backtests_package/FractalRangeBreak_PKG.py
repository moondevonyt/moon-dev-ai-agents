Here is the fixed code with all `backtesting.lib` imports and functions removed, and replaced with appropriate alternatives:

```python
# 🌙 Moon Dev's FractalRangeBreak Backtest 🌙
from backtesting import Backtest, Strategy
import pandas as pd
import talib
import pandas_ta as ta
import numpy as np

# Data Preparation 🛠️
data = pd.read_csv('/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv')
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
}, inplace=True)
data['datetime'] = pd.to_datetime(data['datetime'])
data.set_index('datetime', inplace=True)

class FractalRangeBreak(Strategy):
    atr_period = 14
    range_period = 20
    fractal_lookback = 5
    risk_pct = 0.01  # 1% risk per trade
    
    def init(self):
        # Core Indicators 🌗
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, self.atr_period, name='ATR')
        self.recent_high = self.I(talib.MAX, self.data.High, self.range_period, name='RH')
        self.recent_low = self.I(talib.MIN, self.data.Low, self.range_period, name='RL')
        
        # Fractal Detection 🌌
        def calc_fh(high, low):
            df = pd.DataFrame({'high': high, 'low': low})
            f = ta.trend.fractal(high=df['high'], low=df['low'])
            return f['FH'].fillna(0).values.astype(float)
            
        def calc_fl(high, low):
            df = pd.DataFrame({'high': high, 'low': low})
            f = ta.trend.fractal(high=df['high'], low=df['low'])
            return f['FL'].fillna(0).values.astype(float)
        
        self.fh = self.I(calc_fh, self.data.High, self.data.Low, name='FH')
        self.fl = self.I(calc_fl, self.data.High, self.data.Low, name='FL')
        
        self.last_fh_price = None
        self.last_fl_price = None

    def next(self):
        # Update Fractal Levels ✨
        if self.fh[-1] == 1:
            self.last_fh_price = self.data.High[-1]
            print(f"🌕 New Resistance Fractal at {self.last_fh_price}")
        if self.fl[-1] == 1:
            self.last_fl_price = self.data.Low[-1]
            print(f"🌑 New Support Fractal at {self.last_fl_price}")
        
        # Calculate Dynamic Bands 🌓
        upper_band = self.recent_high[-1] + self.atr[-1]
        lower_band = self.recent_low[-1] - self.atr[-1]
        
        # Entry Logic 🚀
        if not self.position:
            # Long Entry 🌙
            if self.data.Close[-1] > upper_band:
                fractal_confirmed = any(self.fh[-self.fractal_lookback:])
                if fractal_confirmed and self.last_fl_price:
                    risk_distance = self.data.Close[-1] - (self.last_fl_price - 0.5*self.atr[-1])
                    if risk_distance > 0:
                        position_size = int(round((self.equity * self.risk_pct) / risk_distance))
                        position_size = min(position_size, int(self.equity // self.data.Close[-1]))
                        if position_size > 0:
                            sl = self.last_fl_price - 0.5*self.atr[-1]
                            tp = self.data.Close[-1] + 2*risk_distance
                            self.buy(size=position_size, sl=sl, tp=tp)
                            print(f"🚀🌙 LONG Signal! Size: {position_size} | Entry: {self.data.Close[-1]:.2f} | SL: {sl:.2f} | TP: {tp:.2f}")
            
            # Short Entry 🌑
            elif self.data.Close[-1] < lower_band:
                fractal_confirmed = any(self.fl[-self.fractal