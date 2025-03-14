```python
# 🌙 Moon Dev's VolClusterBreakout Backtest 🌙
import pandas as pd
from backtesting import Backtest, Strategy
import talib
import numpy as np

class VolClusterBreakout(Strategy):
    atr_period = 14
    volume_window = 20
    swing_period = 20
    risk_pct = 0.01  # 1% risk per trade
    rr_ratio = 2
    
    def init(self):
        # 🌗 Calculate indicators using TA-Lib
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, self.atr_period)
        self.volume_sma = self.I(talib.SMA, self.data.Volume, self.volume_window)
        self.volume_std = self.I(talib.STDDEV, self.data.Volume, self.volume_window)
        self.swing_high = self.I(talib.MAX, self.data.High, self.swing_period)
        self.swing_low = self.I(talib.MIN, self.data.Low, self.swing_period)
        self.atr_ma = self.I(talib.SMA, self.atr, self.atr_period)
        
        print("🌕 Moon Dev Indicators Initialized! ATR | Volume Clusters | Swing Levels |")

    def next(self):
        if len(self.data) < max(self.swing_period, self.atr_period) + 1:
            return

        # 🌓 Current market conditions
        close = self.data.Close[-1]
        volume = self.data.Volume[-1]
        volume_threshold = self.volume_sma[-1] + 1.5*self.volume_std[-1]
        atr = self.atr[-1]
        atr_ma = self.atr_ma[-1]
        
        # 🌑 Volatility filter condition
        volatility_ok = atr > 1.5*atr_ma
        
        # 🌒 Volume cluster detection
        volume_cluster = volume > volume_threshold
        
        # 🌔 Entry logic
        if not self.position:
            if volume_cluster and volatility_ok:
                # Long entry
                if close > self.swing_high[-1]:
                    sl = close - 2*atr
                    risk_per_share = close - sl
                    position_size = int(round((self.equity * self.risk_pct) / risk_per_share))
                    
                    if position_size > 0:
                        self.buy(size=position_size, sl=sl, 
                                tp=close + self.rr_ratio*risk_per_share)
                        print(f"🚀🌕 LONG! {close:.2f} | Size: {position_size} | SL: {sl:.2f} | ATR: {atr:.2f}")

                # Short entry        
                elif close < self.swing_low[-1]:
                    sl = close + 2*atr
                    risk_per_share = sl - close
                    position_size = int(round((self.equity * self.risk_pct) / risk_per_share))
                    
                    if position_size > 0:
                        self.sell(size=position_size, sl=sl, 
                                 tp=close - self.rr_ratio*risk_per_share)
                        print(f"🌑🌕 SHORT! {close:.2f} | Size: {position_size} | SL: {sl:.2f} | ATR: {atr:.2f}")

        # 🌗 Moon-themed trailing stop (optional)
        elif self.position.is_long and close > self.position.entry_price + atr:
            self.position.sl = max(self.position.sl, close - 1.5*atr)
        elif self.position.is_short and close < self.position.entry_price - atr:
            self.position.sl = min(self.position.sl, close + 1.5*atr)

# 🌙 Data Preparation Magic
data_path = "/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv"
data = pd.read_csv(data_path)

# 🌓 Cleanse and align cosmic data
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col])
data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
}, inplace=True)

# 🌔 Convert to datetime and set as index
data['date'] = pd.to_datetime(data['date'])
data.set_index('