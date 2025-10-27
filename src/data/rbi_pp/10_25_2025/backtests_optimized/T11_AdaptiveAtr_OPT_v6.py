import pandas as pd
import talib
from backtesting import Backtest, Strategy
import numpy as np

class AdaptiveAtr(Strategy):
    entry_atr = 0
    entry_price = 0
    low_vol_regime = False
    entry_step = 0

    def init(self):
        close = self.data.Close
        high = self.data.High
        low = self.data.Low
        volume = self.data.Volume
        
        # 🌙✨ Optimization: Faster SMAs (20/50) for more responsive signals on 15m timeframe to capture shorter trends and increase trade frequency
        self.sma20 = self.I(talib.SMA, close, timeperiod=20)
        self.sma50 = self.I(talib.SMA, close, timeperiod=50)
        # Keep SMA200 for long-term trend filter
        self.sma200 = self.I(talib.SMA, close, timeperiod=200)
        self.atr = self.I(talib.ATR, high, low, close, timeperiod=14)
        self.sma_atr = self.I(talib.SMA, self.atr, timeperiod=20)
        self.sma_atr50 = self.I(talib.SMA, self.atr, timeperiod=50)
        self.avg_vol = self.I(talib.SMA, volume, timeperiod=20)
        
        # 🌙✨ Optimization: Add RSI for momentum confirmation to filter out weak crossovers and improve entry quality
        self.rsi = self.I(talib.RSI, close, timeperiod=14)
        
        print("🌙✨ AdaptiveAtr indicators initialized! 🚀")

    def calculate_size(self):
        equity = self._broker.get_cash()  # Use broker cash for more accurate equity
        # 🌙✨ Optimization: Increase base risk to 2% for higher returns, but reduce to 1% in low vol regime; allow fractional sizes for precision
        risk_pct = 0.01 if self.low_vol_regime else 0.02
        risk_amount = equity * risk_pct
        atr_val = self.atr[-1]
        # 🌙✨ Optimization: Adjust stop distance to 1.5 ATR for tighter risk management while allowing room for volatility
        stop_distance = 1.5 * atr_val
        if stop_distance == 0:
            return 0
        pos_size = risk_amount / stop_distance
        # 🌙✨ Optimization: Return fractional size for better position sizing in crypto (allows sub-unit BTC trades)
        if self.low_vol_regime:
            print("🌙📉 Low volatility regime detected, reducing position size!")
        return max(pos_size, 0.01)  # Minimum size to avoid zero

    def next(self):
        if len(self.data) < 2:
            return
        if np.isnan(self.sma200[-1]) or np.isnan(self.rsi[-1]):
            return
        
        current_price = self.data.Close[-1]
        atr = self.atr[-1]
        vol = self.data.Volume[-1]
        rsi = self.rsi[-1]
        
        # Debug print every 100 bars or so, but sparingly
        if len(self.data) % 100 == 0:
            print(f"🌙📊 Bar {len(self.data)}: Close={current_price:.2f}, SMA20={self.sma20[-1]:.2f}, SMA50={self.sma50[-1]:.2f}, SMA200={self.sma200[-1]:.2f}, RSI={rsi:.2f}, ATR={atr:.2f}")
        
        # 🌙✨ Optimization: Use faster SMA20/50 crossover for more timely entries
        long_cross = (self.sma20[-2] < self.sma50[-2] and self.sma20[-1] > self.sma50[-1])
        short_cross = (self.sma20[-2] > self.sma50[-2] and self.sma20[-1] < self.sma50[-1])
        
        self.low_vol_regime = atr < 0.5 * self.sma_atr50[-1]
        
        if self.position:
            pos = self.position
            current_bar = len(self.data.Close) - 1
            bars_in_trade = current_bar - self.entry_step
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
            
            # 🌙✨ Optimization: Extend time-based exit to 15 bars to allow more time for trends to develop
            if bars_in_trade > 15 and profit_distance < atr:
                self.position.close()
                print("🌙⏰ Time-based exit: No progress in 15 bars!")
                return
            
            # 🌙✨ Optimization: Tighten emergency exit threshold to 2.5x for quicker response to volatility spikes
            if atr > 2.5 * self.sma_atr50[-1]:
                self.position.close()
                print("🌙⚠️ Emergency exit: ATR spike detected!")
                return
            
            # SL/TP/Trailing
            if pos.is_long:
                # 🌙✨ Optimization: Tighter initial SL at 1.5 ATR; improved trailing after 2 ATR profit, trail by 1 ATR for better profit locking
                sl = self.entry_price - 1.5 * self.entry_atr
                profit = current_price - self.entry_price
                if profit > 2 * self.entry_atr:
                    trail_sl = current_price - 1 * atr
                    sl = max(sl, trail_sl)
                elif profit > self.entry_atr:
                    sl = max(sl, self.entry_price + 0.5 * self.entry_atr)
                
                # 🌙✨ Optimization: Extend TP to 4 ATR for improved risk-reward ratio (1.5:4 ~ 1:2.67)
                tp = self.entry_price + 4 * self.entry_atr
                if current_price >= tp:
                    self.position.close()
                    print(f"🌙💰 Take-profit hit on long at {tp:.2f}! 🚀")
                    return
                if self.data.Low[-1] <= sl:
                    self.position.close()
                    print(f"🌙🛑 Stop-loss hit on long at {sl:.2f}! 📉")
                    return
            else:  # short
                sl = self.entry_price + 1.5 * self.entry_atr
                profit = self.entry_price - current_price
                if profit > 2 * self.entry_atr:
                    trail_sl = current_price + 1 * atr
                    sl = min(sl, trail_sl)
                elif profit > self.entry_atr:
                    sl = min(sl, self.entry_price - 0.5 * self.entry_atr)
                
                tp = self.entry_price - 4 * self.entry_atr
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
            # 🌙✨ Optimization: Skip entries in low vol regime to avoid choppy markets and focus on high-vol opportunities
            if self.low_vol_regime:
                return
            
            vol_ok = vol > self.avg_vol[-1]
            atr_ok = atr > self.sma_atr[-1]
            
            # 🌙✨ Optimization: Add trend filter using SMA200 - only long if above, short if below for regime alignment
            trend_long = current_price > self.sma200[-1]
            trend_short = current_price < self.sma200[-1]
            
            # 🌙✨ Optimization: Add RSI momentum filter (>50 for long, <50 for short) to confirm strength and reduce false signals
            rsi_long_ok = rsi > 50
            rsi_short_ok = rsi < 50
            
            if long_cross and atr_ok and vol_ok and trend_long and rsi_long_ok:
                size = self.calculate_size()
                if size > 0:
                    self.buy(size=size)
                    self.entry_atr = atr
                    self.entry_price = current_price
                    self.entry_step = len(self.data) - 1
                    print(f"🌙🚀 LONG ENTRY! Price: {current_price:.2f}, Size: {size}, ATR: {atr:.2f}, Vol OK: {vol_ok}, RSI: {rsi:.2f}, Trend OK ✨")
                else:
                    print("🌙❌ Long signal but size=0, skipped.")
            elif short_cross and atr_ok and vol_ok and trend_short and rsi_short_ok:
                size = self.calculate_size()
                if size > 0:
                    self.sell(size=size)
                    self.entry_atr = atr
                    self.entry_price = current_price
                    self.entry_step = len(self.data) - 1
                    print(f"🌙📉 SHORT ENTRY! Price: {current_price:.2f}, Size: {size}, ATR: {atr:.2f}, Vol OK: {vol_ok}, RSI: {rsi:.2f}, Trend OK ✨")
                else:
                    print("🌙❌ Short signal but size=0, skipped.")
            elif long_cross or short_cross:
                print(f"🌙⚠️ Crossover detected but filters failed: ATR_OK={atr_ok}, Vol_OK={vol_ok}, Trend_L={trend_long}, RSI_L={rsi_long_ok if long_cross else rsi_short_ok}")
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