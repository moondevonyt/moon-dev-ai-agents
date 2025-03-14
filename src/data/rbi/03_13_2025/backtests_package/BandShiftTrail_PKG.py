import pandas as pd
from backtesting import Backtest, Strategy
import talib

# Moon Dev Data Preparation 🌙✨
def load_data(path):
    data = pd.read_csv(path)
    # Clean column names
    data.columns = data.columns.str.strip().str.lower()
    # Drop unnamed columns
    data = data.drop(columns=[col for col in data.columns if 'unnamed' in col])
    # Rename columns to match backtesting requirements
    data = data.rename(columns={
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume'
    })
    # Convert datetime
    data['datetime'] = pd.to_datetime(data['datetime'])
    data = data.set_index('datetime')
    return data

# Load BTC-USD data 🚀
DATA_PATH = '/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv'
data = load_data(DATA_PATH)

class BandShiftTrail(Strategy):
    timeperiod = 50
    risk_percent = 0.01  # 1% risk per trade
    
    def init(self):
        # Moon Dev Indicator Setup 🌙📈
        self.sma = self.I(talib.SMA, self.data.Close, self.timeperiod, name='SMA_50')
        self.std_dev = self.I(talib.STDDEV, self.data.Close, self.timeperiod, nbdev=1, name='STDDEV_50')
        
        # Calculate Bollinger Bands components
        self.upper = self.I(lambda: self.sma.array + 2*self.std_dev.array, name='UpperBand')
        self.lower = self.I(lambda: self.sma.array - 2*self.std_dev.array, name='LowerBand')
        self.bbmp = self.I(lambda: (self.upper.array + self.lower.array)/2, name='BBMP')
        
        print("🌙 Moon Dev Indicators Activated! SMA(50), BBMP(50), STDDEV(50) ✨")

    def next(self):
        # Moon Dev Signal Detection 🌙🔍
        current_close = self.data.Close[-1]
        current_lower = self.lower[-1]
        
        if len(self.data) < self.timeperiod:
            return

        # Entry Logic 🚀
        if not self.position:
            # Bullish crossover detection (BBMP crossing above SMA)
            if (self.bbmp[-2] < self.sma[-2] and self.bbmp[-1] > self.sma[-1]) and current_close > self.sma[-1]:
                # Risk Management Calculations 💰
                equity = self.equity
                risk_amount = equity * self.risk_percent
                risk_per_share = current_close - current_lower
                
                if risk_per_share > 0:
                    position_size = int(round(risk_amount / risk_per_share))
                    if position_size > 0:
                        self.buy(size=position_size, sl=current_lower)
                        print(f"🌙 MOON DEV LONG SIGNAL 🚀 | Size: {position_size} | Entry: {current_close:.2f} | SL: {current_lower:.2f}")

        # Exit Logic ✨
        else:
            # Trailing Stop Update
            updated_sl = max(self.lower[-1], self.position.sl)
            self.position.sl = updated_sl
            
            # Bearish crossover detection (SMA crossing above BBMP)
            if (self.sma[-2] < self.bbmp[-2] and self.sma[-1] > self.bbmp[-1]):
                self.position.close()
                print(f"🌙 MOON DEV EXIT SIGNAL ✨ | SMA Crossunder at {current_close:.2f}")

# Moon Dev Backtest Execution 🌙🚀
bt = Backtest(data, BandShiftTrail, cash=1_000_000, exclusive_orders=True)

# Run initial backtest with default parameters
stats = bt.run()
print("\n🌕🌖🌗🌘🌑🌒🌓🌔🌕 MOON DEV BACKTEST RESULTS 🌕🌖🌗🌘🌑🌒🌓🌔🌕")
print(stats)
print(stats._strategy)