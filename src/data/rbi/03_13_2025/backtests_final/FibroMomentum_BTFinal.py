I've fixed the code and completed the missing print statement. Here's the corrected version with Moon Dev themed debug prints and proper position sizing:

```python
import pandas as pd
import talib
from backtesting import Backtest, Strategy

# 🌙 MOON DEV DATA PREP ✨
data_path = "/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv"
data = pd.read_csv(data_path)
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

class FibroMomentum(Strategy):
    risk_per_trade = 0.01  # 🌙 1% risk per trade
    
    def init(self):
        # 🚀 MOON DEV INDICATORS ✨
        self.swing_high = self.I(talib.MAX, self.data.High, timeperiod=20)
        self.swing_low = self.I(talib.MIN, self.data.Low, timeperiod=20)
        self.ema50 = self.I(talib.EMA, self.data.Close, timeperiod=50)
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14)
        
    def next(self):
        # 🌙 MOON DEV TRACKING ✨
        if len(self.data) < 50 or len(self.position.trades) > 0:
            return
            
        current_close = self.data.Close[-1]
        current_low = self.data.Low[-1]
        current_high = self.data.High[-1]
        
        # 🚀 FIB CALCULATIONS ✨
        sh = self.swing_high[-1]
        sl = self.swing_low[-1]
        fib_range = sh - sl
        fib_levels = {
            '38': sh - fib_range * 0.382,
            '50': sh - fib_range * 0.5,
            '61': sh - fib_range * 0.618
        }
        
        # 🌙 TREND ANALYSIS ✨
        ema_trend = self.ema50[-1] > self.ema50[-2]
        rsi_bull = self.rsi[-1] > 50
        rsi_bear = self.rsi[-1] < 50
        
        # 🚀 ENTRY LOGIC ✨
        for level in fib_levels.values():
            if ema_trend and rsi_bull and (current_low <= level <= current_high):
                # 🌙 BULLISH SETUP ✨
                risk_amount = self.equity * self.risk_per_trade
                sl_price = level * 0.998
                risk_per_share = current_close - sl_price
                
                if risk_per_share <= 0:
                    continue
                    
                position_size = int(round(risk_amount / risk_per_share))
                tp_price = current_close + 2*(current_close - sl_price)
                
                if position_size > 0:
                    self.buy(size=position_size, 
                            sl=sl_price,
                            tp=tp_price,
                            tag=f"🌙 BULLISH FIB {level:.1f}")
                    print(f"🚀🌙✨ Moon Dev LONG! Entry: {current_close:.2f} | Size: {position_size} | SL: {sl_price:.2f} | TP: {tp_price:.2f}")
                    break
                    
            elif not ema_trend and rsi_bear and (current_low <= level <= current_high):
                # 🌙 BEARISH SETUP ✨
                risk_amount = self.equity * self.risk_per_trade
                sl_price = level * 1.002
                risk_per_share = sl_price - current_close
                
                if risk_per_share <= 0:
                    continue
                    
                position_size = int(round(risk_amount / risk_per_share))
                tp_price = current_close - 2*(sl_price - current_close)
                
                if position_size > 0:
                    self.sell(size=position_size,
                             sl=sl_price,
                             tp=tp_price,
                             tag=f"🌙 BEARISH FIB {level:.1f}")
                    print(f"🚀🌙✨ Moon Dev SHORT! Entry: {current_close:.2f} | Size: {position_size