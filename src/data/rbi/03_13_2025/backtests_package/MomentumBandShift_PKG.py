Here's the fixed code with all `backtesting.lib` references removed and proper Moon Dev themed debug prints added:

```python
# 🌙 Moon Dev's MomentumBandShift Backtest 🌙
import pandas as pd
import talib
from backtesting import Backtest, Strategy

# Clean and prepare data
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

class MomentumBandShift(Strategy):
    risk_percent = 0.01  # 1% risk per trade 🌙
    
    def init(self):
        # ✨ Indicator Calculation ✨
        self.rsi5 = self.I(talib.RSI, self.data.Close, timeperiod=5)
        self.min_rsi_3 = self.I(talib.MIN, self.rsi5, timeperiod=3)
        self.ma10 = self.I(talib.SMA, self.data.Close, timeperiod=10)
        
        # 🎢 Bollinger Bands Calculation
        def bb_upper(close): return talib.BBANDS(close, timeperiod=20, nbdevup=2, nbdevdn=2)[0]
        def bb_middle(close): return talib.BBANDS(close, timeperiod=20, nbdevup=2, nbdevdn=2)[1]
        self.bb_mid = self.I(bb_middle, self.data.Close)
        
        # 🌗 Swing High/Low for Stops
        self.swing_low = self.I(talib.MIN, self.data.Low, timeperiod=20)
        self.swing_high = self.I(talib.MAX, self.data.High, timeperiod=20)
        
    def next(self):
        # Skip early bars without sufficient data
        if len(self.data.Close) < 20:
            return
        
        # 🌙 Current Values
        price = self.data.Close[-1]
        rsi = self.rsi5[-1]
        ma10 = self.ma10[-1]
        bb_mid = self.bb_mid[-1]
        
        # 🚀 Long Entry Logic
        if not self.position:
            # RSI below prior 3-period RSI low + price above MA10
            if (rsi < self.min_rsi_3[-2] and price > ma10):
                sl = self.swing_low[-1]
                risk_amount = self.equity * self.risk_percent
                risk_per_share = price - sl
                if risk_per_share > 0:
                    size = int(round(risk_amount / risk_per_share))
                    self.buy(size=size, sl=sl)
                    print(f"🌙✨ BUY SIGNAL ✨\nEntry: {price:.2f} | Size: {size} | SL: {sl:.2f} | RSI: {rsi:.1f} 🌟")
            
            # Short Entry: MA10 > declining BB Middle + price < MA10
            elif (ma10 > bb_mid and 
                  self.bb_mid[-1] < self.bb_mid[-2] and 
                  price < ma10):
                sl = self.swing_high[-1]
                risk_amount = self.equity * self.risk_percent
                risk_per_share = sl - price
                if risk_per_share > 0:
                    size = int(round(risk_amount / risk_per_share))
                    self.sell(size=size, sl=sl)
                    print(f"🌙✨ SELL SIGNAL ✨\nEntry: {price:.2f} | Size: {size} | SL: {sl:.2f} | MA10: {ma10:.2f} 🌟")
        
        # 💫 Exit Conditions
        else:
            if self.position.is_long:
                if rsi > 70 or price < ma10:
                    self.position.close()
                    print(f"🌙💫 CLOSE LONG | Price: {price:.2f} | RSI: {rsi:.1f} 🌌")
                    
            elif self.position.is_short:
                if ma10 < bb_mid or price > ma10:
                    self.position.close()
                    print(f"🌙