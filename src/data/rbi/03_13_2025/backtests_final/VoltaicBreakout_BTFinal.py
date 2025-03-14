```python
# 🌙 MOON DEV BACKTESTING IMPLEMENTATION FOR VOLTAICBREAKOUT STRATEGY ✨

import pandas as pd
import talib
from backtesting import Backtest, Strategy

# =====================
# DATA PREPARATION 🌙✨
# =====================
data = pd.read_csv('/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv')

# Clean and prepare data
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

# =====================
# VOLTAICBREAKOUT STRATEGY CLASS 🌙💡
# =====================
class VoltaicBreakout(Strategy):
    risk_pct = 0.01  # 1% risk per trade 🌙
    bb_period = 20
    bb_dev = 2
    sma_short = 20
    sma_long = 50
    rsi_period = 14
    atr_period = 14
    vol_ma_period = 20
    consolidation_threshold = 0.02  # 2% BB width
    
    def init(self):
        # 🌙 INDICATORS USING TA-LIB WRAPPERS
        def bb_upper(close): return talib.BBANDS(close, self.bb_period, self.bb_dev, self.bb_dev)[0]
        def bb_middle(close): return talib.BBANDS(close, self.bb_period, self.bb_dev, self.bb_dev)[1]
        def bb_lower(close): return talib.BBANDS(close, self.bb_period, self.bb_dev, self.bb_dev)[2]
        
        self.bb_upper = self.I(bb_upper, self.data.Close)
        self.bb_middle = self.I(bb_middle, self.data.Close)
        self.bb_lower = self.I(bb_lower, self.data.Close)
        
        self.sma20 = self.I(talib.SMA, self.data.Close, self.sma_short)
        self.sma50 = self.I(talib.SMA, self.data.Close, self.sma_long)
        self.rsi = self.I(talib.RSI, self.data.Close, self.rsi_period)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, self.atr_period)
        self.vol_ma = self.I(talib.SMA, self.data.Volume, self.vol_ma_period)
        
    def next(self):
        # 🌙 MOON DEV POSITION MANAGEMENT ✨
        if self.position:
            return  # Let existing trades manage exits
            
        price = self.data.Close[-1]
        bb_width = (self.bb_upper[-1] - self.bb_lower[-1]) / self.bb_middle[-1]
        
        # 🌙 CONSOLIDATION CHECK
        if bb_width > self.consolidation_threshold:
            return
            
        # 🌙 CORE STRATEGY LOGIC 🚀
        long_cond = (
            (self.sma20[-1] > self.sma50[-1]) and
            (self._bullish_divergence()) and
            (price > self.bb_upper[-1]) and
            (self.data.Volume[-1] > self.vol_ma[-1])
        )
        
        short_cond = (
            (self.sma20[-1] < self.sma50[-1]) and
            (self._bearish_divergence()) and
            (price < self.bb_lower[-1]) and
            (self.data.Volume[-1] > self.vol_ma[-1])
        )
        
        # 🌙 EXECUTE TRADES WITH RISK MANAGEMENT 🌙
        if long_cond:
            self._enter_trade('long')
        elif short_cond:
            self._enter_trade('short')
            
    def _bullish_divergence(self):
        # 🌙 PRICE LOWER LOWS + RSI HIGHER LOWS
        if len(self.data.Close) < 3 or len(self.rsi) < 3:
            return False
        return (self.data.Close