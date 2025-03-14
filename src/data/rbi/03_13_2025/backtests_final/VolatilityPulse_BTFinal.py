I'll help fix the incomplete code while maintaining the original strategy logic. Here's the complete and debugged version with Moon Dev themed debug prints:

```python
import numpy as np
import pandas as pd
from backtesting import Strategy, Backtest
import talib
import pandas_ta as ta

# Load and prepare data
data_path = '/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv'
data = pd.read_csv(data_path, parse_dates=['datetime'], index_col='datetime')

# Clean column names
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])

# Rename columns to match backtesting requirements
data = data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
})

class VolatilityPulse(Strategy):
    risk_per_trade = 0.01
    atr_multiplier = 1.5
    trailing_init = 1.0
    trailing_improved = 0.5
    time_exit_bars = 3
    
    def init(self):
        # Calculate indicators
        h, l, c = self.data.High, self.data.Low, self.data.Close
        
        # Core indicators
        self.atr = self.I(talib.ATR, h, l, c, timeperiod=14, name='ATR_14')
        self.atr_avg = self.I(talib.SMA, self.atr, timeperiod=14, name='ATR_Avg')
        self.ema50 = self.I(talib.EMA, c, timeperiod=50, name='EMA_50')
        self.atr_20_avg = self.I(talib.SMA, self.atr, timeperiod=20, name='ATR_20_Avg')
        
        # Candlestick patterns
        self.engulf = self.I(talib.CDLENGULFING, self.data.Open, h, l, c, name='ENGULF')
        self.hammer = self.I(talib.CDLHAMMER, self.data.Open, h, l, c, name='HAMMER')
        self.shooting = self.I(talib.CDLSHOOTINGSTAR, self.data.Open, h, l, c, name='SHOOTING')
        
        # Daily tracking
        self.current_day = None
        self.consecutive_losses = 0
        self.daily_high = 0
        self.trading_halted = False

    def enter_long(self):
        price = self.data.Close[-1]
        atr = self.atr[-1]
        risk_amount = self.equity * self.risk_per_trade
        position_size = round(risk_amount / (atr * self.atr_multiplier))
        
        if position_size > 0:
            print(f"🌕 Moon Dev: Entering Long | Size: {position_size} units | Price: {price:.2f}")
            self.buy(size=position_size, sl=price - atr * self.trailing_init)
            
    def enter_short(self):
        price = self.data.Close[-1]
        atr = self.atr[-1]
        risk_amount = self.equity * self.risk_per_trade
        position_size = round(risk_amount / (atr * self.atr_multiplier))
        
        if position_size > 0:
            print(f"🌑 Moon Dev: Entering Short | Size: {position_size} units | Price: {price:.2f}")
            self.sell(size=position_size, sl=price + atr * self.trailing_init)

    def next(self):
        # Daily reset check
        current_date = self.data.index[-1].date()
        if current_date != self.current_day:
            self.current_day = current_date
            self.consecutive_losses = 0
            self.daily_high = self.equity
            self.trading_halted = False
            print(f"🌙 New Moon Day: {current_date} - Fresh trading day started!")
        
        if self.trading_halted:
            return
        
        # Update daily high watermark
        self.daily_high = max(self.daily_high, self.equity)
        
        # Check daily drawdown
        if (self.daily_high - self.equity)/self.daily_high >= 0.03:
            print(f"🌧️ Moon Dev Alert: 3% Daily Drawdown Reached! Trading halted.")
            self.trading_h