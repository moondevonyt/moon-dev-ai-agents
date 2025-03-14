I'll help fix the code by removing any `backtesting.lib` imports and replacing the `crossover` function with the proper implementation. Here's the corrected version:

```python
from backtesting import Backtest, Strategy
import talib
import pandas as pd
import numpy as np

# Data preparation
data_path = '/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv'
data = pd.read_csv(data_path)

# Clean and format data
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data = data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume',
})
data['datetime'] = pd.to_datetime(data['datetime'])
data.set_index('datetime', inplace=True)

class VolatilityReversal(Strategy):
    risk_pct = 0.01  # 1% risk per trade
    atr_period = 14
    rsi_period = 14
    swing_period = 20
    exit_bars = 3  # Time-based exit after 3 bars

    def init(self):
        # Volatility indicators 🌪️
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, self.atr_period, name='ATR')
        self.atr_sma = self.I(talib.SMA, self.atr, 20, name='ATR_SMA')
        
        # Momentum indicators 🚀
        self.rsi = self.I(talib.RSI, self.data.Close, self.rsi_period, name='RSI')
        
        # MACD crossover indicators ⚡
        def macd_line(close):
            return talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)[0]
        def macd_signal(close):
            return talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)[1]
        
        self.macd = self.I(macd_line, self.data.Close, name='MACD')
        self.signal = self.I(macd_signal, self.data.Close, name='SIGNAL')
        
        # Price structure indicators 🌗
        self.swing_high = self.I(talib.MAX, self.data.High, self.swing_period, name='SWING_HIGH')
        self.swing_low = self.I(talib.MIN, self.data.Low, self.swing_period, name='SWING_LOW')
        
        # Engulfing pattern detector 🕯️
        self.engulfing = self.I(talib.CDLENGULFING, self.data.Open, self.data.High, self.data.Low, self.data.Close, name='ENGULFING')

        self.entry_bar = 0  # Track entry bar for time exits

    def next(self):
        if self.position:
            # Time-based exit check ⏳
            if (len(self.data) - self.entry_bar) >= self.exit_bars:
                self.position.close()
                print(f"🌙✨ Moon Dev Time Exit: Closed position after {self.exit_bars} bars")
            return

        # Current indicator values 📊
        current_close = self.data.Close[-1]
        current_atr = self.atr[-1]
        atr_sma = self.atr_sma[-1]
        current_rsi = self.rsi[-1]
        engulf_signal = self.engulfing[-1]
        swing_low = self.swing_low[-1]
        
        # MACD crossover detection without backtesting.lib
        macd_above = (self.macd[-2] < self.signal[-2] and self.macd[-1] > self.signal[-1])

        # Long entry conditions ✅
        if (current_atr > atr_sma and 
            engulf_signal == 100 and
            current_rsi < 30 and
            macd_above and
            current_close < swing_low):

            # Risk management calculations 🛡️
            stop_price = swing_low
            risk_amount = self.equity * self.risk_pct
            risk_per_share = current_close - stop_price
            
            if risk_per_share <= 0:
                print("🚨 Moon Dev Alert: Invalid stop price, trade skipped")
                return

            position_size = int(round(risk_amount / risk_per_share))
            if position_size == 0: