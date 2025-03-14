I'll help fix the code by removing any `backtesting.lib` imports and replacing crossover logic. Here's the corrected version:

```python
# 🌙 Moon Dev's OvernightErod Backtest Implementation 🚀

import pandas as pd
import talib
from backtesting import Backtest, Strategy
import datetime

# ========================
# DATA PREPARATION 🌍📊
# ========================
data_path = "/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv"

# Load and clean data
data = pd.read_csv(data_path, parse_dates=['datetime'], index_col='datetime')
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])

# Column mapping with Moon Dev precision 🌙🎯
required_columns = {
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
}
data = data.rename(columns=required_columns)

# Convert to Eastern Time Zone 🕒
data = data.tz_localize('UTC').tz_convert('US/Eastern')

# ========================
# STRATEGY IMPLEMENTATION 🚀📈
# ========================
class OvernightErod(Strategy):
    time_window = (18, 6)  # 6PM to 6AM EST
    
    def init(self):
        # 🌙 Core Indicators
        self.high_60m = self.I(talib.MAX, self.data.High, timeperiod=4)  # 4*15min = 60min
        self.low_60m = self.I(talib.MIN, self.data.Low, timeperiod=4)
        
        # 📊 EROD System (assuming EROD column exists in data)
        self.erod_ma = self.I(talib.SMA, self.data.df['erod'], timeperiod=20*96)  # 20-day MA
        
        # 🌊 Volatility Management
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, 14)
        
        # 🔊 Volume Validation
        self.volume_ma = self.I(talib.SMA, self.data.Volume, 10*96)  # 10-day MA
        
    def next(self):
        current_time = self.data.index[-1].time()
        entry_zone = (current_time >= datetime.time(18)) or (current_time <= datetime.time(6))
        
        # 🛑 Pre-Market Exit
        if self.position and current_time >= datetime.time(6):
            self.position.close()
            print(f"🌙 Moon Dev Exit: Sunrise flush at 6AM EST 🌅")
            return
            
        if not entry_zone:
            return
            
        # 🚀 Long Entry Logic
        if not self.position and \
            self.data.Close[-1] > self.high_60m[-1] and \
            self.data.df['erod'][-1] > self.erod_ma[-1] and \
            self.data.Volume[-1] > 1.2 * self.volume_ma[-1]:
            
            # 🛡 Risk Management
            entry_price = self.data.Close[-1]
            atr_value = self.atr[-1]
            
            # 🔥 Dynamic Stop Calculation
            stop_5pct = entry_price * 0.95
            stop_atr = entry_price - 1.5 * atr_value
            stop_price = max(stop_5pct, stop_atr)
            
            # 💰 Position Sizing
            risk_amount = 0.01 * self.equity
            risk_per_share = entry_price - stop_price
            position_size = int(round(risk_amount / risk_per_share))
            
            # 🌙 Exposure Limit
            max_size = int((0.05 * self.equity) // entry_price)
            position_size = min(position_size, max_size)
            
            if position_size > 0:
                self.buy(
                    size=position_size,
                    sl=stop_price,
                    tp=entry_price + 2*(entry_price - stop_price)
                )
                print(f"🚀 Moon Dev LONG Signal: {position_size} units @ {entry_price} ✨")
                
        # 🛑 Swing Low Exit
        if self.position and self.data.Low[-1] < self.low_60m[-1]:
            self.position.close()
            print(f"🌙 Moon Dev Exit: Swing low breach 🚨")

# =======================