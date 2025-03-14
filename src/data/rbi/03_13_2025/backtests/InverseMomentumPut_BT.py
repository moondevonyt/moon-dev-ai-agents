# -*- coding: utf-8 -*-
import pandas as pd
import talib
from backtesting import Backtest, Strategy
from backtesting.lib import crossover

class InverseMomentumPut(Strategy):
    risk_per_trade = 0.01  # 1% of equity per trade
    stop_loss_pct = 0.02  # 2% stop loss
    
    def init(self):
        # Clean and prepare data
        self.data.df.columns = self.data.df.columns.str.strip().str.lower()
        self.data.df = self.data.df.drop(columns=[col for col in self.data.df.columns if 'unnamed' in col.lower()])
        
        # Calculate indicators using TA-Lib through self.I()
        self.sma3 = self.I(talib.SMA, self.data.Close, timeperiod=3, name='SMA3')
        self.sma9 = self.I(talib.SMA, self.data.Close, timeperiod=9, name='SMA9')
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14, name='RSI')
        
        print("🌙 Moon Dev Indicators Activated! SMA3/9 & RSI(14) Ready 🚀")

    def next(self):
        current_close = self.data.Close[-1]
        
        # Entry conditions
        if not self.position:
            # Check for bearish crossover (3SMA crosses below 9SMA)
            bearish_crossover = (self.sma3[-1] < self.sma9[-1] and 
                                self.sma3[-2] >= self.sma9[-2])
            
            # Check RSI overbought
            rsi_overbought = self.rsi[-1] > 70
            
            if bearish_crossover and rsi_overbought:
                # Risk management calculations
                equity = self.equity
                risk_amount = equity * self.risk_per_trade
                stop_loss_price = current_close * (1 + self.stop_loss_pct)
                risk_per_share = stop_loss_price - current_close
                
                if risk_per_share <= 0:
                    print("⚠️ Risk per share <=0, trade skipped")
                    return
                
                position_size = int(round(risk_amount / risk_per_share))
                
                if position_size > 0:
                    self.entry_price = current_close
                    self.stop_loss_level = stop_loss_price
                    self.sell(size=position_size)
                    print(f"🌙✨ SHORT ENTERED! Size: {position_size} @ {current_close}")
                    print(f"   🛑 Stop Loss: {self.stop_loss_level:.2f} | 📉 Risk: {self.risk_per_trade*100}%")
        
        # Exit conditions
        else:
            # Check for bullish crossover
            bullish_crossover = (self.sma3[-1] > self.sma9[-1] and 
                                 self.sma3[-2] <= self.sma9[-2])
            
            # Check RSI undersold
            rsi_undersold = self.rsi[-1] < 30
            
            # Check stop loss
            stop_hit = self.data.High[-1] >= self.stop_loss_level
            
            if bullish_crossover or rsi_undersold or stop_hit:
                self.position.close()
                print(f"🚀 EXIT TRIGGERED! Closing @ {current_close}")
                print(f"   Reason: {'Bullish crossover' if bullish_crossover else ''} "
                      f"{'RSI undersold' if rsi_undersold else ''} "
                      f"{'Stop loss hit' if stop_hit else ''}")

# Data preparation
data = pd.read_csv('/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv',
                   parse_dates=['datetime'], index_col='datetime')

# Clean columns
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
}, inplace=True)

print("🌕 Moon Dev Data Preparation Complete! Columns:")
print(data.columns)

# Initialize and run backtest
bt = Backtest(data, InverseMomentumPut, cash=1_000_000, margin=1.0)
stats = bt.run()
print("\n🌙✨ MOON DEV BACKTEST RESULTS 🚀")
print(stats)
print(stats._strategy)