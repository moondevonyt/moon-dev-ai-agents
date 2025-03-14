Here's the fixed code with all `backtesting.lib` imports and functions removed, and replaced with appropriate alternatives:

```python
# 🌙 MOON DEV BACKTESTING SCRIPT FOR LIQUIDATIONZONER STRATEGY 🚀

# Import necessary libraries
import pandas as pd
import talib
from backtesting import Backtest, Strategy

# Data preprocessing function
def prepare_data(filepath):
    # Load and clean data
    data = pd.read_csv(filepath)
    
    # Clean column names
    data.columns = data.columns.str.strip().str.lower()
    
    # Drop unnamed columns
    data = data.drop(columns=[col for col in data.columns if 'unnamed' in col])
    
    # Rename columns to match backtesting requirements
    data.rename(columns={
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume'
    }, inplace=True)
    
    # Convert datetime index
    data.index = pd.to_datetime(data['datetime'])
    data = data[['Open', 'High', 'Low', 'Close', 'Volume']]
    
    return data

# Load and prepare data 🌙
DATA_PATH = "/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv"
data = prepare_data(DATA_PATH)

class LiquidationZoner(Strategy):
    risk_percent = 0.01  # 1% risk per trade 🌟
    rr_ratio = 2  # Risk-reward ratio
    swing_period = 20  # Swing high/low calculation period
    
    def init(self):
        # 🌙 Swing High/Low Indicators
        self.swing_high = self.I(talib.MAX, self.data.High, timeperiod=self.swing_period)
        self.swing_low = self.I(talib.MIN, self.data.Low, timeperiod=self.swing_period)
        
        # ✨ Candlestick Pattern Indicators
        self.hammer = self.I(talib.CDLHAMMER, self.data.Open, self.data.High, self.data.Low, self.data.Close)
        self.shooting_star = self.I(talib.CDLSHOOTINGSTAR, self.data.Open, self.data.High, self.data.Low, self.data.Close)
        
        # 🚀 Additional Patterns (Uncomment to add more)
        # self.bullish_engulf = self.I(talib.CDLENGULFING, self.data.Open, self.data.High, self.data.Low, self.data.Close)
        # self.bearish_engulf = self.I(talib.CDLENGULFING, self.data.Open, self.data.High, self.data.Low, self.data.Close)

    def next(self):
        price = self.data.Close[-1]
        
        # 🌙 MOON DEV TRADE LOGIC STARTS HERE 🌟
        if not self.position:
            # Long Entry Conditions
            if (price <= self.swing_high[-1] * 1.01 and
                self.hammer[-1] == 100):
                self.enter_long()
            
            # Short Entry Conditions
            elif (price >= self.swing_low[-1] * 0.99 and
                  self.shooting_star[-1] == 100):
                self.enter_short()

    def enter_long(self):
        # 🌙 RISK MANAGEMENT CALCULATIONS
        entry_price = self.data.Close[-1]
        stop_loss = self.swing_low[-1] * 0.99  # 1% below swing low
        risk_per_unit = entry_price - stop_loss
        
        if risk_per_unit <= 0:
            return  # Invalid stop loss
        
        # 🚀 Position sizing calculation
        position_size = (self.equity * self.risk_percent) / risk_per_unit
        position_size = int(round(position_size))
        
        # Take profit calculation
        take_profit = entry_price + (risk_per_unit * self.rr_ratio)
        
        # 🌟 Execute trade
        self.buy(size=position_size, 
                sl=stop_loss,
                tp=take_profit)
        
        print(f"🌙 MOON DEV LONG SIGNAL 🌕 | Entry: {entry_price:.2f} | Size: {position_size} | SL: {stop_loss:.2f} | TP: {take_profit:.2f}")

    def enter_short(self):
        # 🌙 RISK MANAGEMENT CALCULATIONS
        entry_price = self.data.Close[-1]
        stop_loss = self.swing_high[-1] * 1.01  # 1% above swing high
        risk_per_unit