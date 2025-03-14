I've analyzed the code and found that it uses `backtesting.lib.crossover` which needs to be removed. Here's the fixed code with proper Moon Dev themed debug prints and all necessary replacements:

```python
from backtesting import Backtest, Strategy
import pandas as pd
import talib
import numpy as np

# Load and preprocess data
data = pd.read_csv(
    '/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv',
    parse_dates=['datetime'],
    index_col='datetime'
)
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
}, inplace=True)

class FractalTrender(Strategy):
    risk_percent = 0.01  # 1% risk per trade
    
    def init(self):
        # Moon-powered indicators initialization
        self.sma50 = self.I(talib.SMA, self.data.Close, timeperiod=50, name='SMA 50')
        self.fractal_high = self.I(talib.MAX, self.data.High, timeperiod=5, name='Fractal High')
        self.fractal_low = self.I(talib.MIN, self.data.Low, timeperiod=5, name='Fractal Low')
        print("🌙✨ Moon Indicators Activated! SMA 50, Fractal High/Low Online!")
        
    def next(self):
        current_idx = len(self.data) - 1
        if current_idx < 4:
            return  # Not enough data for fractals
        
        # Bullish entry check
        fractal_low_bar = self.data.Low[current_idx-2]
        if (fractal_low_bar == self.fractal_low[current_idx-2] and
            not self.position and
            self.data.Close[-1] > self.sma50[-1]):
            
            entry_price = self.data.Close[-1]
            sl_price = fractal_low_bar
            risk_per_share = entry_price - sl_price
            
            if risk_per_share > 0:
                risk_amount = self.equity * self.risk_percent
                position_size = int(round(risk_amount / risk_per_share))
                
                if position_size > 0:
                    tp_price = entry_price + 2*risk_per_share
                    self.buy(size=position_size, sl=sl_price, tp=tp_price)
                    print(f"🚀🌙 LONG ENTRY: {entry_price:.2f} | Size: {position_size} | Risk: {risk_per_share:.2f} | Moon Power Activated!")
        
        # Bearish entry check
        fractal_high_bar = self.data.High[current_idx-2]
        if (fractal_high_bar == self.fractal_high[current_idx-2] and
            not self.position and
            self.data.Close[-1] < self.sma50[-1]):
            
            entry_price = self.data.Close[-1]
            sl_price = fractal_high_bar
            risk_per_share = sl_price - entry_price
            
            if risk_per_share > 0:
                risk_amount = self.equity * self.risk_percent
                position_size = int(round(risk_amount / risk_per_share))
                
                if position_size > 0:
                    tp_price = entry_price - 2*risk_per_share
                    self.sell(size=position_size, sl=sl_price, tp=tp_price)
                    print(f"🌙🐻 SHORT ENTRY: {entry_price:.2f} | Size: {position_size} | Risk: {risk_per_share:.2f} | Bearish Moon Gravity!")
        
        # Fractal exit checks
        if self.position.is_long and current_idx >= 2:
            if self.data.High[current_idx-2] == self.fractal_high[current_idx-2]:
                self.position.close()
                print(f"🌙✨ Closing LONG at {self.data.Close[-1]:.2f} | Bearish Fractal Detected! Moon Shield Activated!")
                
        if self.position.is_short and current_idx >= 2:
            if self.data.Low[current_idx-2] == self.fractal_low[current_idx-2]:
                self.position.close()
                print(f"🌙✨ Closing SHORT at {self.data.Close[-1]:.2f} | Bullish Fractal Detected! Moon Defense Protocol!")

# Run backtest with 1M capital
print("