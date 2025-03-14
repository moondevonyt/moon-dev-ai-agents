class PositionSizingMethod:
    """Fixed fractional sizing."""
    def get_size(self, account_balance, risk_free_rate):
        max_risk = 0.02  # 2% maximum daily risk
        position_size = (max_risk * account_balance) / (risk_free_rate * 100)
        return int(position_size)

# Include PSM in strategy
bt.psm = PositionSizingMethod(bt.account_balance, getcurve(bt.data, 'C', 0))

def calculate_vix(self, high_data, low_data):
    """Calculate VIX using ATR."""
    return talib.ATR(np.array(high_data), np.array(low_data), np.array(close_data))

# Slice data correctly before passing to I()
vix =bt.I('VIX', self.data, 14).get()
vix = vix[-len(data):]  # Ensure it matches the correct length

stats = bt.run()

print("🌕 MOON DEV BACKTEST RESULTS 🌕")
print(f"Total Trades: {stats.total_trades}")
print(f"Winning Ratio: {stats.winning_ratio:.2%}")
print(f"Profit Factor: {stats.profit_factor:.2f}")

# Execute starlight sequence
bt.run()
stats = bt.run()

print("🌕 MOON DEV BACKTEST RESULTS 🌕")
print(stats._strategy)

import pandas as pd
from backtrader import I, getcurve
from backtrader.dataSource import CSVSource
from backtrader.trader import Backtest
import numpy as np

class PositionSizingMethod:
    def __init__(self, account_balance, risk_free_rate):
        self.account_balance = account_balance
        self.risk_free_rate = risk_free_rate
    
    def get_size(self):
        max_risk = 0.02  # 2% maximum daily risk
        position_size = (max_risk * self.account_balance) / (self.risk_free_rate * 100)
        return int(position_size)

class CorrelationReversal(CorrelationStrategy):
    def __init__(self, data, params):
        super().__init__(data, params)
        self.vix_period = params.get('vix', 14)
        self.corr_period = params.get('corr', 20)
        self.risk_free_rate = params.get('rf', 0.02)  # Assume 2% risk-free rate

    def preinit(self):
        self.vix = None
        self.corr = None
    
    def start(self):
        super().start()
        self.psm = PositionSizingMethod(self.account_balance, self.risk_free_rate)
        
    def log_price(self, price):
        if not self.position:
            return
        
        # Calculate VIX and Correlation
        high_data, low_data, close_data = self.data.get asset_high(), self.data.asset_low(), self.data.asset_close()
        vix = talib.ATR(np.array(high_data), np.array(low_data), np.array(close_data))
        correlation = talib.CORREL(self.data(asset).get(size=self.corr_period), 
                                self.data(asset).get(size=self.corr_period -1))
        
        self.vix = pd.Series(vix, index=self.data.get_datetimelabels())
        self.corr = pd.Series(correlation, index=self.data.get_datetimelabels())

    def next(self):
        if not self.position:
            return
        
        # Check PSM
        position_size = self.psm.get_size()
        
        if len(self) >= 2 * position_size:  # Twice the position size to be safe
            self.position = self.position * (1 / (position_size * 2))
            
        # Correlation Trading Logic
        corr = self.corr[-1] if self.corr is not None else 0
        
        if corr > 0.5 and len(self) >= position_size:
            self.sell(size=position_size)
        
        elif corr < -0.5 and len(self) >= position_size:
            self.buy(size=position_size)

# Backtest parameters
params = dict(
    vix=14,
    corr=20,
    account_balance=100000,  # $100k initial capital
    risk_free_rate=0.02      # 2% annual risk-free rate
)

# Create data source
data = CSVSource(
    data='path_to_data.csv',  # Replace with your CSV path
    dt=(lambda x: pd.to_datetime(x, utc=True)),
    na='nan',
    Header=0,
    sep=','
)

# Run backtest
bt = Backtest(data, CorrelationReversal, params=params)
bt.run()

# Display results after PSM setup and execution
print("🌕 MOON DEV BACKTEST RESULTS 🌕")
print(f"Total Trades: {bt.stats.total_trades}")
print(f"Winning Ratio: {bt.stats.winning_ratio:.2%}")
print(f"Profit Factor: {bt.stats.profit_factor:.2f}")