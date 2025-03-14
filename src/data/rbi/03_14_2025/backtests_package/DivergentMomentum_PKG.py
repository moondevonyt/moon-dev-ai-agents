Here's the fixed code with all backtesting.lib references removed and proper Moon Dev themed debug prints added:

```python
# 🌙 Moon Dev's DivergentMomentum Backtest 🌙
from backtesting import Backtest, Strategy
import pandas as pd
import talib
import numpy as np

# 📁 Data Preparation 📁
data_path = "/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv"
data = pd.read_csv(data_path, parse_dates=['datetime'], index_col='datetime')

# 🧹 Data Cleaning Magic 🧹
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col])
data = data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
})

class DivergentMomentum(Strategy):
    # 🎚 Strategy Parameters 🎚
    rsi_period = 14
    adx_period = 14
    swing_period = 20
    risk_percent = 0.01
    
    def init(self):
        # 📈 Indicator Calculation 📈
        self.rsi = self.I(talib.RSI, self.data.Close, self.rsi_period)
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, self.adx_period)
        self.swing_high = self.I(talib.MAX, self.data.High, self.swing_period)
        self.swing_low = self.I(talib.MIN, self.data.Low, self.swing_period)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, 14)
        
        # 📍 Track swing highs for divergence detection
        self.last_swing_high_price = None
        self.last_swing_high_rsi = None
        
    def next(self):
        # ⚠️ Skip initial candles
        if len(self.rsi) < 30 or len(self.adx) < 30:
            return
            
        # 💹 Entry Logic 💹
        if not self.position:
            # RSI crosses above 70
            rsi_cross = self.rsi[-2] < 70 and self.rsi[-1] >= 70
            # ADX > 25 and rising
            adx_strong = self.adx[-1] > 25 and self.adx[-1] > self.adx[-2]
            
            if rsi_cross and adx_strong:
                # 🛑 Risk Management Calculations 🛑
                equity = self.equity
                risk_amount = equity * self.risk_percent
                stop_price = self.swing_low[-1] - 0.5 * self.atr[-1]
                risk_per_share = self.data.Close[-1] - stop_price
                
                if risk_per_share > 0:
                    position_size = int(round(risk_amount / risk_per_share))
                    if position_size > 0:
                        self.buy(size=position_size, sl=stop_price)
                        print(f"🌕 MOON DEV ALERT: LONG ENTRY 🚀\nPrice: {self.data.Close[-1]:.2f} | RSI: {self.rsi[-1]:.1f} | ADX: {self.adx[-1]:.1f} | Size: {position_size} shares")
        
        # 🏁 Exit Logic 🏁
        else:
            # 🚨 Emergency Stop Check 🚨
            if self.data.Low[-1] < self.swing_low[-1]:
                self.position.close()
                print(f"🚨 MOON DEV STOP: PRICE COLLAPSE 🌋\nExit Price: {self.data.Close[-1]:.2f} | Swing Low: {self.swing_low[-1]:.2f}")
                return
                
            # 📉 Bearish Divergence Detection 📉
            current_swing_high = self.swing_high[-1]
            if self.data.High[-1] == current_swing_high:
                if self.last_swing_high_price is not None:
                    if (current_swing_high > self.last_swing_high_price and 
                        self.rsi[-1] < self.last_swing_high_rsi):
                        self.position.close()
                        print(f"🌑 MOON DEV DIVERGENCE DETECTED 📉\nPrice High: {current_swing_high:.2