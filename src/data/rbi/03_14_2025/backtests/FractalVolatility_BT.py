```python
import pandas as pd
import talib
from backtesting import Backtest, Strategy
from backtesting.lib import crossover, crossunder

# Load and prepare data
data = pd.read_csv('/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv')
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col])
data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
}, inplace=True)
data['datetime'] = pd.to_datetime(data['datetime'])
data.set_index('datetime', inplace=True)

class FractalVolatility(Strategy):
    risk_pct = 0.01
    atr_period = 14
    bb_period = 20
    
    def init(self):
        # Fractal indicators
        self.fractal_high = self.I(talib.MAX, self.data.High, timeperiod=5, name='🌙 Fractal High')
        self.fractal_low = self.I(talib.MIN, self.data.Low, timeperiod=5, name='🌙 Fractal Low')
        
        # Bollinger Bands
        self.bb_upper, self.bb_middle, self.bb_lower = self.I(
            talib.BBANDS, self.data.Close, timeperiod=self.bb_period, 
            nbdevup=2, nbdevdn=2, name=['BB_Upper', 'BB_Mid', 'BB_Lower']
        )
        
        # Volatility measurements
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, 
                         timeperiod=self.atr_period, name='✨ ATR')
        
        # Swing points
        self.swing_high = self.I(talib.MAX, self.data.High, timeperiod=20, name='🚀 Swing High')
        self.swing_low = self.I(talib.MIN, self.data.Low, timeperiod=20, name='🚀 Swing Low')
        
        self.last_fractal_high = None
        self.prev_fractal_high = None
        self.last_fractal_low = None
        self.prev_fractal_low = None

    def next(self):
        if len(self.data) < 20:
            return
        
        # Detect fractal signals
        current_high = self.data.High[-1]
        current_low = self.data.Low[-1]
        current_close = self.data.Close[-1]
        
        # Check for new fractal high (2 bars ago)
        if len(self.data) >= 3 and self.data.High[-3] == self.fractal_high[-1]:
            self.prev_fractal_high, self.last_fractal_high = self.last_fractal_high, self.data.High[-3]
            print(f"🌙 New Fractal High at {self.last_fractal_high}")
            
        # Check for new fractal low (2 bars ago)
        if len(self.data) >= 3 and self.data.Low[-3] == self.fractal_low[-1]:
            self.prev_fractal_low, self.last_fractal_low = self.last_fractal_low, self.data.Low[-3]
            print(f"🌙 New Fractal Low at {self.last_fractal_low}")
            
        # Divergence detection
        bullish_div = (self.last_fractal_low and self.prev_fractal_low and
                      (self.last_fractal_low > self.prev_fractal_low) and
                      (self.data.Low[-3] < self.data.Low[-3-(len(self.data)-self.prev_fractal_low)]))
        
        bearish_div = (self.last_fractal_high and self.prev_fractal_high and
                      (self.last_fractal_high < self.prev_fractal_high) and
                      (self.data.High[-3] > self.data.High[-3-(len(self.data)-self.prev_fractal_high)]))
        
        # Bollinger confirmation
        near_bb_lower = current_close <= self.bb_lower[-1] * 1.01
        near_bb_upper = current_close >= self.bb_upper[-1] * 0.99
        
        # Entry conditions
        if not self.position:
            # Long setup
            if bullish_div and near_bb_lower and current_close > self.swing_high[-1]:
                at