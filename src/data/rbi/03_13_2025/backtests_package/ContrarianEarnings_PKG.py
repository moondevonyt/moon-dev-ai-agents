I've fixed the code by removing the `backtesting.lib` import and ensuring all indicators are properly implemented using `talib`. Here's the corrected version:

```python
# 🌙 MOON DEV BACKTESTING IMPLEMENTATION FOR CONTRARIAN EARNINGS STRATEGY 🚀

import pandas as pd
import talib
from backtesting import Backtest, Strategy

# =====================
# DATA PREPARATION 🌌
# =====================
data_path = "/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv"
data = pd.read_csv(data_path, parse_dates=['datetime'], index_col='datetime')

# Clean and prepare data columns
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])

# Column mapping to meet backtesting.py requirements
column_mapping = {
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
}
data = data.rename(columns=column_mapping)

# Add synthetic earnings release column (every 30 days for testing)
bar_frequency = 15/(60*24)  # 15min in days
data['Earnings_Release'] = 0
data.iloc[::int(30/bar_frequency), data.columns.get_loc('Earnings_Release')] = 1

# =====================
# STRATEGY CLASS 🌠
# =====================
class ContrarianEarnings(Strategy):
    risk_pct = 0.01  # 1% risk per trade
    stop_loss_pct = 0.02
    take_profit_pct = 0.04
    holding_period = 288  # 3 days in 15min bars (3*96)

    def init(self):
        # Track earnings dates using MAX indicator
        self.earnings_dates = self.I(talib.MAX, self.data.Earnings_Release, timeperiod=1)
        self.last_earnings_idx = -1

    def next(self):
        current_idx = len(self.data) - 1
        
        # 🌙 Moon Dev Debug: Track earnings events
        if self.earnings_dates[-1] == 1:
            self.last_earnings_idx = current_idx
            print(f"🌕 NEW EARNINGS DETECTED! Index: {current_idx} | Price: {self.data.Close[-1]:.2f}")

        # Entry Logic: 4th day after earnings
        if self.last_earnings_idx != -1 and (current_idx - self.last_earnings_idx) == 384:  # 4 days in 15min bars
            # Calculate price performance
            earnings_price = self.data.Close[self.last_earnings_idx]
            current_price = self.data.Close[-1]
            
            if current_price < earnings_price:
                # 🌙 RISK MANAGEMENT CALCULATIONS
                equity = self.equity
                entry_price = self.data.Open[-1]
                stop_loss = entry_price * (1 - self.stop_loss_pct)
                take_profit = entry_price * (1 + self.take_profit_pct)
                
                # Position sizing calculation
                risk_amount = equity * self.risk_pct
                risk_per_share = entry_price - stop_loss
                position_size = risk_amount / risk_per_share
                position_size = int(round(position_size))
                
                if position_size > 0:
                    self.buy(size=position_size, 
                            sl=stop_loss,
                            tp=take_profit,
                            tag=f"🌙 Contrarian Entry")
                    print(f"🚀 ENTRY SIGNAL | Size: {position_size} | Entry: {entry_price:.2f} | SL: {stop_loss:.2f} | TP: {take_profit:.2f}")

        # Exit Logic: Time-based exit
        for trade in self.trades:
            if (current_idx - trade.entry_bar) >= self.holding_period:
                self.position.close()
                print(f"🕒 TIME EXIT | Closed position after {self.holding_period} bars")

# =====================
# BACKTEST EXECUTION ⚡
# =====================
bt = Backtest(data, 
             ContrarianEarnings, 
             cash=1_000_000, 
             exclusive_orders=True,
             trade_on_close=False)

stats = bt.run()
print(f"\n{'='*40}\nMOON DEV FINAL STATS 🌕✨")
print(stats)
print(stats._strategy)
print(f"{'='*