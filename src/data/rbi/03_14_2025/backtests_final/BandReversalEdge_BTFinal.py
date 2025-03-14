I've fixed the code with proper formatting, position sizing, and Moon Dev themed debug prints. Here's the complete corrected version:

```python
import numpy as np
import pandas as pd
import talib
from backtesting import Backtest, Strategy
from pathlib import Path

# Data handling
data_path = "/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv"
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

class BandReversalEdge(Strategy):
    risk_percentage = 0.01
    atr_period = 14
    bb_period_20 = 20
    bb_std_20 = 2
    bb_period_50 = 50
    bb_std_50 = 2
    exit_bars = 3
    
    def init(self):
        # Calculate indicators using TA-Lib
        # 20-period Bollinger Bands
        upper_20, mid_20, lower_20 = talib.BBANDS(
            self.data.Close, 
            timeperiod=self.bb_period_20,
            nbdevup=self.bb_std_20,
            nbdevdn=self.bb_std_20
        )
        self.bb_upper_20 = self.I(lambda: upper_20, name='BB_U20')
        self.bb_lower_20 = self.I(lambda: lower_20, name='BB_L20')
        
        # 50-period Bollinger Bands
        upper_50, mid_50, lower_50 = talib.BBANDS(
            self.data.Close,
            timeperiod=self.bb_period_50,
            nbdevup=self.bb_std_50,
            nbdevdn=self.bb_std_50
        )
        self.bb_lower_50 = self.I(lambda: lower_50, name='BB_L50')
        
        # ATR for stop loss
        self.atr = self.I(talib.ATR,
                         self.data.High,
                         self.data.Low,
                         self.data.Close,
                         self.atr_period,
                         name='ATR')
        
        self.entry_bar = 0
        self.stop_loss_price = 0

    def next(self):
        if not self.position:
            # Entry conditions
            price = self.data.Close[-1]
            bb_l20 = self.bb_lower_20[-1]
            bb_l50 = self.bb_lower_50[-1]
            
            if (price < bb_l20) and (price < bb_l50):
                # Calculate position size
                equity = self.equity
                risk_amount = equity * self.risk_percentage
                atr_value = self.atr[-1]
                sl_distance = 0.5 * atr_value
                risk_per_share = sl_distance
                
                if risk_per_share == 0:
                    print("🌙 Moon Dev Warning: Risk per share is zero, skipping trade")
                    return
                
                position_size = risk_amount / risk_per_share
                position_size = int(round(position_size))
                
                if position_size > 0:
                    self.buy(size=position_size)
                    self.entry_bar = len(self.data)
                    self.stop_loss_price = price - sl_distance
                    print(f"🌙 Moon Dev Entry Signal 🚀 | Price: {price:.2f} | Size: {position_size} | SL: {self.stop_loss_price:.2f} | Equity: {equity:.2f}")
        else:
            # Exit conditions
            exit_price = None
            current_bar = len(self.data)
            
            # Profit target check
            if self.data.High[-1] >= self.bb_upper_20[-1]:
                self.position.close()
                print(f"🎯 Moon Dev Profit Target Hit! | Close: {self.data.Close[-1]:.2f}")
                return
                
            # Stop loss check
            if self.data.Low[-1] <= self.stop_loss_price:
                self.position.close()
                print(f"🛑 Moon Dev Stop Loss Triggered! | Close: {self.data.Close[-1]:.2f}")
                return
                
            # Time-based exit
            if current_bar - self.entry_bar >= self.exit_bars: