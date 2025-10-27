import pandas as pd
import talib
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import numpy as np

class AdaptiveAtr(Strategy):
    entry_atr = 0
    entry_price = 0
    low_vol_regime = False

    def init(self):
        close = self.data.Close
        high = self.data.High
        low = self.data.Low
        volume = self.data.Volume
        
        self.sma50 = self.I(talib.SMA, close, timeperiod=50)
        self.sma200 = self.I(talib.SMA, close, timeperiod=200)
        self.atr = self.I(talib.ATR, high, low, close, timeperiod=14)
        self.sma_atr = self.I(talib.SMA, self.atr, timeperiod=20)
        self.sma_atr50 = self.I(talib.SMA, self.atr, timeperiod=50)
        self.avg_vol = self.I(talib.SMA, volume, timeperiod=20)
        
        print("🌙✨ AdaptiveAtr indicators initialized! 🚀")

    def calculate_size(self):
        equity = self._broker.getvalue()
        risk_pct = 0.005 if self.low_vol_regime else 0.01
        risk_amount = equity * risk_pct
        atr_val = self.atr[-1]
        stop_distance = 2 * atr_val
        if stop_distance == 0:
            return 0
        pos_size = risk_amount / stop_distance
        size = int(round(pos_size))
        if self.low_vol_regime:
            print("🌙📉 Low volatility regime detected, reducing position size by 50%!")
        return max(size, 1)  # Ensure at least 1 unit

    def next(self):
        if np.isnan(self.sma200[-1]):
            return
        
        current_price = self.data.Close[-1]
        atr = self.atr[-1]
        vol = self.data.Volume[-1]
        
        # Debug print every 100 bars or so, but sparingly
        if len(self.data) % 100 == 0:
            print(f"🌙📊 Bar {len(self.data)}: Close={current_price:.2f}, SMA50={self.sma50[-1]:.2f}, SMA200={self.sma200[-1]:.2f}, ATR={atr:.2f}")
        
        long_cross = crossover(self.sma50, self.sma200)
        short_cross = crossover(self.sma200, self.sma50)
        
        self.low_vol_regime = atr < 0.5 * self.sma_atr50[-1]
        
        if self.position:
            pos = self.position
            current_bar = len(self.data.Close) - 1
            entry_bar = self.trades[-1].entry_bar
            bars_in_trade = current_bar - entry_bar
            profit_distance = abs(current_price - self.entry_price)
            
            # Reversal exit
            if pos.is_long and short_cross:
                self.position.close()
                print("🌙🔄 SMA reversal exit on long position!")
                return
            if not pos.is_long and long_cross:
                self.position.close()
                print("🌙🔄 SMA reversal exit on short position!")
                return
            
            # Time-based exit
            if bars_in_trade > 10 and profit_distance < atr:
                self.position.close()
                print("🌙⏰ Time-based exit: No progress in 10 bars!")
                return
            
            # Emergency volatility exit
            if atr > 2 * self.sma_atr50[-1]:
                self.position.close()
                print("🌙⚠️ Emergency exit: ATR spike detected!")
                return
            
            # SL/TP/Trailing
            if pos.is_long:
                sl = self.entry_price - 2 * self.entry_atr
                profit = current_price - self.entry_price
                if profit > self.entry_atr:
                    sl = max(sl, self.entry_price + 0.5 * self.entry_atr)
                trail_sl = current_price - 1.5 * atr
                sl = max(sl, trail_sl)
                
                tp = self.entry_price + 3 * self.entry_atr
                if current_price >= tp:
                    self.position.close()
                    print(f"🌙💰 Take-profit hit on long at {tp:.2f}! 🚀")
                    return
                if self.data.Low[-1] <= sl:
                    self.position.close()
                    print(f"🌙🛑 Stop-loss hit on long at {sl:.2f}! 📉")
                    return
            else:  # short
                sl = self.entry_price + 2 * self.entry_atr
                profit = self.entry_price - current_price
                if profit > self.entry_atr:
                    sl = min(sl, self.entry_price - 0.5 * self.entry_atr)
                trail_sl = current_price + 1.5 * atr
                sl = min(sl, trail_sl)
                
                tp = self.entry_price - 3 * self.entry_atr
                if current_price <= tp:
                    self.position.close()
                    print(f"🌙💰 Take-profit hit on short at {tp:.2f}! 🚀")
                    return
                if self.data.High[-1] >= sl:
                    self.position.close()
                    print(f"🌙🛑 Stop-loss hit on short at {sl:.2f}! 📉")
                    return
        
        # Entry logic
        if not self.position:
            vol_ok = vol > self.avg_vol[-1]
            atr_ok = atr > self.sma_atr[-1]
            
            if long_cross and atr_ok and vol_ok:
                size = self.calculate_size()
                if size > 0:
                    self.buy(size=size)
                    self.entry_atr = atr
                    self.entry_price = current_price
                    print(f"🌙🚀 LONG ENTRY! Price: {current_price:.2f}, Size: {size}, ATR: {atr:.2f}, Vol OK: {vol_ok} ✨")
                else:
                    print("🌙❌ Long signal but size=0, skipped.")
            elif short_cross and atr_ok and vol_ok:
                size = self.calculate_size()
                if size > 0:
                    self.sell(size=size)
                    self.entry_atr = atr
                    self.entry_price = current_price
                    print(f"🌙📉 SHORT ENTRY! Price: {current_price:.2f}, Size: {size}, ATR: {atr:.2f}, Vol OK: {vol_ok} ✨")
                else:
                    print("🌙❌ Short signal but size=0, skipped.")
            elif long_cross or short_cross:
                print(f"🌙⚠️ Crossover detected but filters failed: ATR_OK={atr_ok}, Vol_OK={vol_ok}")
            else:
                pass  # No signal

# Data loading and cleaning
path = '/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv'
data = pd.read_csv(path, parse_dates=['datetime'], index_col='datetime')

# Clean column names
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])

# Map to required columns with proper case
data = data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
})

# Ensure only required columns
data = data[['Open', 'High', 'Low', 'Close', 'Volume']]

print(f"🌙📈 Data loaded: {len(data)} bars from {data.index[0]} to {data.index[-1]}")
print(data.head())

# Run backtest
bt = Backtest(data, AdaptiveAtr, cash=1000000, commission=0.001, exclusive_orders=True)
stats = bt.run()
print(stats)
print(stats._strategy)
print("🌙✨ Backtest completed! 🚀")