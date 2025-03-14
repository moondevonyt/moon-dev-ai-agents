```python
import pandas as pd
import talib
from backtesting import Backtest, Strategy
from backtesting.lib import TrailingStop
import numpy as np

# Load and preprocess data
data_path = "/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv"
data = pd.read_csv(data_path, parse_dates=['datetime'], index_col='datetime')

# Clean column names
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col])

# Rename columns to backtesting.py format
data = data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
})

class MomentumReversion(Strategy):
    ema_period = 50
    sma_period = 50
    macd_fast = 12
    macd_slow = 26
    macd_signal = 9
    atr_period = 14
    delta_ma_period = 20
    atr_sma_period = 20
    
    def init(self):
        # Core indicators
        self.ema = self.I(talib.EMA, self.data.Close, timeperiod=self.ema_period, name='EMA 50')
        self.sma = self.I(talib.SMA, self.data.Close, timeperiod=self.sma_period, name='SMA 50')
        
        # MACD components
        macd, macd_signal, _ = talib.MACD(self.data.Close, 
                                         fastperiod=self.macd_fast,
                                         slowperiod=self.macd_slow,
                                         signalperiod=self.macd_signal)
        self.macd_line = self.I(lambda: macd, name='MACD')
        self.macd_signal = self.I(lambda: macd_signal, name='MACD Signal')
        self.macd_delta = self.I(lambda: macd - macd_signal, name='MACD Delta')
        self.macd_delta_ma = self.I(talib.SMA, self.macd_delta, timeperiod=self.delta_ma_period, name='Delta MA')
        
        # Volatility indicators
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=self.atr_period, name='ATR')
        self.atr_sma = self.I(talib.SMA, self.atr, timeperiod=self.atr_sma_period, name='ATR SMA')
        self.atr_ratio = self.I(lambda: self.atr / self.atr_sma, name='ATR Ratio')
        
        # Trailing stop tracking
        self.trailing_stop_distance = None
        self.highest_high = None
        self.lowest_low = None

    def next(self):
        current_close = self.data.Close[-1]
        current_atr = self.atr[-1]
        atr_ratio = self.atr_ratio[-1]
        
        # Moon Dev debug prints 🌙
        print(f"🌙 Current Close: {current_close:.2f} | ATR: {current_atr:.2f} | ATR Ratio: {atr_ratio:.2f}")
        
        if not self.position:
            # Long entry conditions
            ema_cross_above = (self.ema[-1] > self.sma[-1]) and (self.ema[-2] <= self.sma[-2])
            macd_delta_below = self.macd_delta[-1] < self.macd_delta_ma[-1]
            atr_ratio_rising = self.atr_ratio[-1] > self.atr_ratio[-2]
            
            # Short entry conditions
            ema_cross_below = (self.ema[-1] < self.sma[-1]) and (self.ema[-2] >= self.sma[-2])
            macd_delta_above = self.macd_delta[-1] > self.macd_delta_ma[-1]
            
            if ema_cross_above and macd_delta_below and atr_ratio_rising:
                risk_percent = 0.01 if atr_ratio > 1 else 0.02
                risk_amount = self.equity * risk_percent
                stop_loss = 1.5 * current_atr
                position_size = int(round(risk_amount / stop_loss))
                
                self.buy(size=position