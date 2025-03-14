# -*- coding: utf-8 -*-
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import pandas as pd
import talib

# Load and preprocess data
data = pd.read_csv('/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv')

# Clean column names
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col])

# Format columns for backtesting.py
data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
}, inplace=True)

# Set datetime index
data['datetime'] = pd.to_datetime(data['datetime'])
data = data.set_index('datetime')

class MomentumBreakout(Strategy):
    rsi_period = 50
    ma_period = 20
    atr_period = 14
    risk_pct = 0.01  # 1% risk per trade
    atr_multiplier = 0.2

    def init(self):
        # Moon Dev Indicator Suite 🌙
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=self.rsi_period, name='🌙 RSI 50')
        self.ma = self.I(talib.SMA, self.data.Close, timeperiod=self.ma_period, name='🌙 MA 20')
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, 
                         timeperiod=self.atr_period, name='🌙 ATR 14')
        self.resistance = self.I(talib.MAX, self.data.High, timeperiod=20, name='🌙 Resistance')

    def next(self):
        price = self.data.Close[-1]
        ma_value = self.ma[-1]
        atr_value = self.atr[-1]
        
        # Moon Dev Debug Dashboard ✨
        print((f"🌙 Moon Dev System Status | RSI: {self.rsi[-1]:.1f} | "
               f"Resistance: {self.resistance[-1]:.1f} | MA: {ma_value:.1f} | "
               f"ATR: {atr_value:.1f} | Price: {price:.1f}"))

        if not self.position:
            # Entry Logic: RSI Oversold + Breakout 🌌
            if (self.rsi[-1] < 30 and 
                price > self.resistance[-1] and 
                self.data.Close[-2] <= self.resistance[-2]):
                
                # Risk Management Calculation 🔒
                entry_price = self.data.Close[-1]
                sl_price = entry_price - (atr_value * self.atr_multiplier)
                risk_per_share = entry_price - sl_price
                
                if risk_per_share > 0:
                    risk_amount = self.risk_pct * self.equity
                    position_size = int(round(risk_amount / risk_per_share))
                    
                    if position_size > 0:
                        print((f"🚀🌕 MOON SHOT! Entering {position_size} units at {entry_price:.1f} | "
                               f"SL: {sl_price:.1f} ({self.atr_multiplier*100}% ATR)"))
                        self.buy(size=position_size, sl=sl_price)
        else:
            # Exit Logic: MA Trailing Stop 🌈
            if price < ma_value:
                print(f"🌙💫 STARDUST EXIT! Closing at MA: {ma_value:.1f}")
                self.position.close()

# Launch Moon Dev Backtest 🚀
bt = Backtest(data, MomentumBreakout, cash=1_000_000, exclusive_orders=True)
stats = bt.run()

# Print Moon Dev Performance Report 🌕
print("\n" + "="*55 + " MOON DEV FINAL REPORT " + "="*55)
print(stats)
print(stats._strategy)
print("="*130 + "\n")