Here's the debugged code with Moon Dev themed debug prints and fixes applied:

```python
# 🌙 Moon Dev Backtest AI Implementation for BandwidthMomentum Strategy �

# Required imports
from backtesting import Backtest, Strategy
import pandas as pd
import talib
import numpy as np

class BandwidthMomentum(Strategy):
    risk_per_trade = 0.01  # 1% risk per trade 🌙
    
    def init(self):
        # 🌗 Calculate Bollinger Bands components
        self.middle_band = self.I(talib.SMA, self.data.Close, timeperiod=50, name='MIDDLE')
        self.std_dev = self.I(talib.STDDEV, self.data.Close, timeperiod=50, nbdev=1, name='STDDEV')
        self.upper_band = self.I(lambda m, s: m + 2*s, self.middle_band, self.std_dev, name='UPPER')
        self.lower_band = self.I(lambda m, s: m - 2*s, self.middle_band, self.std_dev, name='LOWER')
        
        # 📊 Calculate volatility and momentum indicators
        self.bb_width = self.I(lambda u, l, m: (u - l)/m, 
                              self.upper_band, self.lower_band, self.middle_band,
                              name='BB_WIDTH')
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=20, name='RSI')
        self.rsi_upper_ratio = self.I(lambda r, u: r/u, self.rsi, self.upper_band,
                                     name='RSI_UPPER_RATIO')
        
        # 🌙 Swing calculations for volatility contraction detection
        self.bb_width_min = self.I(talib.MIN, self.bb_width, timeperiod=20, name='BB_WIDTH_MIN')

    def next(self):
        price = self.data.Close[-1]
        
        # 🌌 Entry Logic: Volatility contraction followed by expansion
        if not self.position:
            # Check for squeeze breakout
            if (self.bb_width[-1] > self.bb_width[-2] and 
                self.bb_width[-2] == self.bb_width_min[-2]):
                
                # 🎯 Risk management calculations
                stop_loss = self.lower_band[-1]
                risk_amount = self.equity * self.risk_per_trade
                risk_per_share = price - stop_loss
                
                if risk_per_share > 0:
                    position_size = int(round(risk_amount / risk_per_share))
                    if position_size > 0:
                        self.buy(size=position_size, sl=stop_loss)
                        print(f"🌙✨ MOON DEV ALERT: Long Entry {price:.2f} | "
                              f"Size: {position_size} | SL: {stop_loss:.2f} �")

        # 🚪 Exit Logic: Momentum threshold
        else:
            if self.rsi_upper_ratio[-1] > 1.5:
                self.position.close()
                print(f"🌙💸 MOON DEV EXIT: Closing {price:.2f} | "
                      f"Profit: {self.position.pl:.2f} ✨")

# 🌍 Data preparation
try:
    data = pd.read_csv('/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv',
                       parse_dates=['datetime'], index_col='datetime')
    data.columns = data.columns.str.strip().str.lower()
    data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
    data.rename(columns={
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume'
    }, inplace=True)
    
    print("🌙 MOON DEV DATA LOAD: Successfully loaded and formatted data ✨")
except Exception as e:
    print(f"🌙❌ MOON DEV DATA ERROR: {str(e)}")
    raise

# 🚀 Launch backtest
try:
    bt = Backtest(data, BandwidthMomentum, cash=1_000_000, commission=.002)
    stats = bt.run()
    
    print("\n" + "="*50 + " MOON DEV FINAL STATS " + "="*50)
    print(stats)
    print(stats._strategy)
    print("="*125 + "\n")
    
    print("🌙🚀 MOON DEV BACKTEST: Completed successfully! ✨")
except Exception as e:
    print(f"