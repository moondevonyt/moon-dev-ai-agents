The code you provided is already well-structured and doesn't contain any `backtesting.lib` imports or functions. However, I'll ensure that all indicators are properly wrapped in `self.I()` and that the code follows Moon Dev's best practices. Here's the cleaned-up and verified version of your code:

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
            self.trading_halted = True
            return
        
        # Skip entries if low volatility
        current_atr = self.atr[-1]
        if not self.position and current_atr < self.atr_20_avg[-1]:
            print(f"🌫️ Moon Dev: Low volatility filter active (ATR {current_atr:.2f} < 20MA)")
            return
            
        # Entry logic
        price = self.data.Close[-1]
        ema50 = self.ema50[-1]
        atr_spike = current_atr >= 1.5 * self.atr_avg[-1]
        
        if not self.position:
            # Long conditions
            if price > ema50 and atr_spike:
                bull_signal = self.engulf[-1] == 100 or self.hammer[-1] == 100
                if bull_signal:
                    self.enter_long()
            
            # Short conditions
            elif price < ema50 and atr_spike:
                bear