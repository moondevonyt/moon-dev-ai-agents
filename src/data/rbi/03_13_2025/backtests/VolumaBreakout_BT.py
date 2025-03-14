```python
# moon_dev_voluma_breakout.py
import pandas as pd
import talib
from backtesting import Backtest, Strategy
from backtesting.lib import crossover

class VolumaBreakout(Strategy):
    def init(self):
        # 🌙 Moon Dev Indicators Setup
        self.sma50 = self.I(talib.SMA, self.data.Close, 50, name='SMA50')
        self.sma200 = self.I(talib.SMA, self.data.Close, 200, name='SMA200')
        self.volume_ma = self.I(talib.SMA, self.data.Volume, 20, name='Volume_MA')
        self.swing_high = self.I(talib.MAX, self.data.High, 20, name='Swing_High')
        self.swing_low = self.I(talib.MIN, self.data.Low, 20, name='Swing_Low')
        
        # 🌗 Bollinger Bands Calculation
        upper, _, _ = talib.BBANDS(self.data.Close, timeperiod=20, nbdevup=2, nbdevdn=2)
        self.upper_band = self.I(lambda: upper, name='Upper_Band')

    def next(self):
        # 🌙 Moon Dev Debug Prints
        if len(self.data) % 100 == 0:
            print(f"🌙 Moon Pulse: Bar {len(self.data)} | Close: {self.data.Close[-1]:.2f} | SMA50: {self.sma50[-1]:.2f} | SMA200: {self.sma200[-1]:.2f} ✨")

        # Entry Logic
        if not self.position:
            # Death Cross Detection
            if crossover(self.sma200, self.sma50):
                print(f"\n🌑 DEATH CROSS DETECTED! Bar {len(self.data)}")
                
                # Bearish Confirmation Checks
                price_below_ma = self.data.Close[-1] < self.sma50[-1] < self.sma200[-1]
                low_volume = self.data.Volume[-1] < self.volume_ma[-1]
                volatility_breakout = self.data.Low[-1] < self.swing_low[-1]
                
                if all([price_below_ma, low_volume, volatility_breakout]):
                    # 🚀 Risk Management Calculations
                    risk_percent = 0.01  # 1% equity risk
                    risk_amount = self.equity * risk_percent
                    entry_price = self.data.Close[-1]
                    sl_price = self.swing_high[-1] + 0.001  # Buffer for SL
                    
                    # Calculate position size
                    risk_per_share = abs(sl_price - entry_price)
                    if risk_per_share == 0:
                        print("🚨 Zero risk detected! Aborting entry")
                        return
                        
                    position_size = int(round(risk_amount / risk_per_share))
                    position_size = min(position_size, int(self.equity // entry_price))
                    
                    # Enter Short Position
                    self.sell(size=position_size, sl=sl_price)
                    print(f"🚀 SHORTING MOON ROCKET! Size: {position_size} | Entry: {entry_price:.2f} | SL: {sl_price:.2f} 🌙")

        # Exit Logic
        if self.position:
            # Bollinger Band Exit
            if self.data.Close[-1] > self.upper_band[-1]:
                self.position.close()
                print(f"🌕 UPPER BAND TOUCH! Closing at {self.data.Close[-1]:.2f} ✨")
                
            # SMA50 Exit
            if self.data.Close[-1] > self.sma50[-1]:
                self.position.close()
                print(f"🌗 PRICE ABOVE SMA50! Closing at {self.data.Close[-1]:.2f} ✨")

# 🌙 Moon Dev Data Preparation
data = pd.read_csv('/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv')

# Clean and format data
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col])
data = data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
}).ffill()

data['datetime'] = pd.to_datetime(data['datetime'])
data.set_index('datetime', inplace=True)

# 🌙 Launch Backtest
bt = Backtest(data, VolumaBreakout,