I'll help fix the code by removing the `backtesting.lib` import and ensuring proper indicator usage. Here's the corrected version:

```python
# 🌙 MOON DEV BACKTESTING IMPLEMENTATION FOR VOLATILITYMOMENTUM STRATEGY 🚀

import pandas as pd
import talib
from backtesting import Backtest, Strategy

# =====================
# DATA PREPARATION 🌐
# =====================
data = pd.read_csv('/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv', parse_dates=['datetime'], index_col='datetime')

# Clean column names and handle data
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])

# Ensure proper column mapping 🌙
data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
}, inplace=True)

# =====================
# STRATEGY CLASS ✨
# =====================
class VolatilityMomentum(Strategy):
    vix_lookback = 252 * 96  # 1-year lookback in 15m intervals
    gamma_ma_period = 90 * 96  # 3-month MA in 15m intervals
    risk_pct = 0.02  # 2% risk per trade 🌙
    stop_loss = 0.05  # 5% SL
    take_profit = 0.20  # 20% TP
    
    def init(self):
        # VIX calculations 🛡️
        self.vix_sma = self.I(talib.SMA, self.data.df['vix'], timeperiod=self.vix_lookback, name='VIX SMA')
        self.vix_threshold = self.I(lambda x: x * 0.8, self.vix_sma, name='VIX Threshold')
        
        # Gamma Skew calculations ✨
        self.gamma_ma = self.I(talib.SMA, self.data.df['gamma_skew'], 
                              timeperiod=self.gamma_ma_period, name='Gamma MA')
        
        # Track previous values for crossover detection
        self.prev_gamma = None
        self.prev_gamma_ma = None

    def next(self):
        # Wait for indicators to warm up 🌙
        if len(self.data) < max(self.vix_lookback, self.gamma_ma_period):
            return
            
        current_vix = self.data.df['vix'][-1]
        current_threshold = self.vix_threshold[-1]
        current_gamma = self.data.df['gamma_skew'][-1]
        current_gamma_ma = self.gamma_ma[-1]
        
        # =====================
        # ENTRY LOGIC 🚀
        # =====================
        if not self.position:
            # Check VIX condition 🌙
            vix_condition = current_vix < current_threshold
            
            # Gamma Skew crossover detection ✨
            gamma_crossover = False
            if self.prev_gamma is not None and self.prev_gamma_ma is not None:
                gamma_crossover = (self.prev_gamma <= self.prev_gamma_ma) and (current_gamma > current_gamma_ma)
            
            if vix_condition and gamma_crossover:
                # Risk management calculations 🛡️
                equity = self.equity
                entry_price = self.data.Close[-1]
                sl_price = entry_price * (1 - self.stop_loss)
                tp_price = entry_price * (1 + self.take_profit)
                
                # Position sizing calculation 🌙
                risk_amount = equity * self.risk_pct
                risk_per_unit = entry_price - sl_price
                position_size = int(round(risk_amount / risk_per_unit))
                
                if position_size > 0:
                    self.buy(size=position_size, sl=sl_price, tp=tp_price)
                    print(f"🌙🚀 MOON DEV ENTRY: {position_size} units @ {entry_price:.2f} | SL: {sl_price:.2f} | TP: {tp_price:.2f} ✨")

        # =====================
        # EXIT LOGIC 🛑
        # =====================
        else:
            exit_condition = False
            
            # VIX reversion check 🌙
            if current_vix >= self.vix_sma[-1]:
                exit_condition = True
                print(f"🌙🛑 VIX REVERSION