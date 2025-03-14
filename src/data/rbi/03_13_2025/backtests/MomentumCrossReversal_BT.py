# 🌙 Moon Dev Backtest AI Implementation 🚀
import pandas as pd
import talib
import numpy as np
from backtesting import Backtest, Strategy
from backtesting.lib import crossover

class MomentumCrossReversal(Strategy):
    risk_pct = 0.01  # 1% risk per trade
    rr_ratio = 2      # Risk-reward ratio
    
    def init(self):
        # 🌙 Moon Dev Indicator Setup ✨
        self.ma50 = self.I(talib.SMA, self.data.Close, 50, name='MA50')
        self.ma200 = self.I(talib.SMA, self.data.Close, 200, name='MA200')
        self.ema20 = self.I(talib.EMA, self.data.Close, 20, name='EMA20')
        self.swing_low = self.I(talib.MIN, self.data.Low, 20, name='Swing Low')
        print("🌙 Moon Dev Indicators Initialized! MA50/MA200/EMA20/Swing Low Ready ✨")

    def next(self):
        # 🌙 Current Values Calculation
        price = self.data.Close[-1]
        ma_diff = self.ma50[-1] - self.ma200[-1]
        prev_ma_diff = self.ma50[-2] - self.ma200[-2]
        ema20_val = self.ema20[-1]
        
        # 🚀 Long Entry Conditions
        if not self.position:
            if (crossover(ma_diff, ema20_val) and 
                price > ema20_val and 
                ma_diff > 0):
                
                # 🌙 Risk Management Calculations
                stop_loss = min(self.swing_low[-1], self.ema20[-1])
                risk_per_unit = price - stop_loss
                
                if risk_per_unit <= 0:
                    print("🌧️ Moon Dev Risk Alert! Invalid SL Calculation")
                    return
                
                # 🌙 Position Sizing
                risk_amount = self.risk_pct * self.equity
                position_size = int(round(risk_amount / risk_per_unit))
                take_profit = price + (risk_per_unit * self.rr_ratio)
                
                if position_size > 0:
                    self.buy(size=position_size, 
                            sl=stop_loss,
                            tp=take_profit,
                            tag="Moon Dev Long Entry 🚀")
                    print(f"🚀 Moon Dev Signal: LONG {position_size} units | "
                          f"Entry: {price:.2f} | SL: {stop_loss:.2f} | TP: {take_profit:.2f}")

    def notify_trade(self, trade):
        if trade.is_closed:
            emoji = "🎉" if trade.pl > 0 else "🌧️"
            print(f"{emoji} Moon Dev Trade Closed | PL: ${trade.pl:.2f} "
                  f"({trade.pl_pct:.2%}) {'✨' if trade.pl > 0 else '🌙'}")

# 🌙 Data Preparation Section
data = pd.read_csv('/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv')

# 🧹 Data Cleaning
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

# 🌙 Backtest Execution
bt = Backtest(data, MomentumCrossReversal, cash=1_000_000, margin=1.0)
stats = bt.run()
print("\n🌕🌖🌗🌘🌑🌒🌓🌔🌕")
print("Moon Dev Backtest Results:")
print(stats)
print(stats._strategy)
print("Moon Dev Mission Complete! 🚀🌙")