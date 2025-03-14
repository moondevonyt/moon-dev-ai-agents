```python
from backtesting import Backtest, Strategy
from backtesting.lib import crossover, crossunder
import pandas as pd
import talib
import numpy as np

# Load and preprocess data
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

class MomentumFusion(Strategy):
    rsi_period = 14
    bb_period = 20
    bb_dev = 2
    atr_period = 14
    mom_threshold_long = 70
    mom_threshold_short = 30
    risk_pct = 0.01
    sl_mult = 2

    def init(self):
        # Core indicators
        self.rsi = self.I(talib.RSI, self.data.Close, self.rsi_period)
        
        # Bollinger Bands components
        def bb_upper(close):
            upper, _, _ = talib.BBANDS(close, timeperiod=self.bb_period, 
                                      nbdevup=self.bb_dev, nbdevdn=self.bb_dev)
            return upper
        self.upper_band = self.I(bb_upper, self.data.Close)
        
        self.middle_band = self.I(lambda close: talib.BBANDS(close, timeperiod=self.bb_period,
                                                           nbdevup=self.bb_dev, nbdevdn=self.bb_dev)[1],
                                self.data.Close)
        
        self.lower_band = self.I(lambda close: talib.BBANDS(close, timeperiod=self.bb_period,
                                                          nbdevup=self.bb_dev, nbdevdn=self.bb_dev)[2],
                               self.data.Close)
        
        # Momentum Score system
        self.pct_b = self.I(lambda c, l, u: (c - l)/(u - l + 1e-9),
                           self.data.Close, self.lower_band, self.upper_band)
        self.mom_score = self.I(lambda r, b: r * b, self.rsi, self.pct_b)
        
        # Risk management
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, self.atr_period)
        
        print("🌙✨ Moon Dev Trading System Activated! 🚀")

    def next(self):
        if len(self.data.Close) < 2:
            return

        # Divergence detection
        price_low_div = self.data.Low[-1] < self.data.Low[-2]
        rsi_low_div = self.rsi[-1] > self.rsi[-2]
        bullish_div = price_low_div and rsi_low_div

        price_high_div = self.data.High[-1] > self.data.High[-2]
        rsi_high_div = self.rsi[-1] < self.rsi[-2]
        bearish_div = price_high_div and rsi_high_div

        # Entry logic
        if not self.position:
            if (bullish_div and
                self.mom_score[-1] > self.mom_threshold_long and
                self.data.Close[-1] > self.upper_band[-1]):
                
                atr_val = self.atr[-1]
                risk_amount = self.risk_pct * self.equity
                size = int(round(risk_amount / (self.sl_mult * atr_val)))
                
                if size > 0:
                    self.buy(size=size, 
                            sl=self.data.Close[-1] - self.sl_mult * atr_val)
                    print(f"🌕🚀 BULLISH FUSION! Long {size} units at {self.data.Close[-1]:.2f}")

            elif (bearish_div and
                  self.mom_score[-1] < self.mom_threshold_short and
                  self.data.Close[-1] < self.lower_band[-1]):
                  
                atr_val = self.atr[-1]
                risk_amount = self.risk_pct * self.equity
                size = int(round(risk_amount / (self.sl_mult * atr_val)))
                
                if size > 0:
                    self.sell(size