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
        
        # 🌙✨ OPTIMIZATION: Switched from SMA to EMA for faster trend detection, allowing earlier entries to capture more of the move while reducing lag.
        self.ema50 = self.I(talib.EMA, close, timeperiod=50)
        self.ema200 = self.I(talib.EMA, close, timeperiod=200)
        # 🌙✨ OPTIMIZATION: Added RSI indicator for momentum confirmation to filter out weak crossovers and improve entry quality.
        self.rsi = self.I(talib.RSI, close, timeperiod=14)
        self.atr = self.I(talib.ATR, high, low, close, timeperiod=14)
        # 🌙✨ OPTIMIZATION: Shortened SMA_ATR to 20 periods for more responsive volatility regime detection, avoiding overly conservative filters.
        self.sma_atr = self.I(talib.SMA, self.atr, timeperiod=20)
        self.sma_atr50 = self.I(talib.SMA, self.atr, timeperiod=50)
        self.avg_vol = self.I(talib.SMA, volume, timeperiod=20)
        
        print("🌙✨ AdaptiveAtr indicators initialized with optimizations! 🚀")

    def calculate_size(self):
        equity = self.equity
        # 🌙✨ OPTIMIZATION: Increased base risk to 1.5% (from 1%) for higher position exposure to boost returns, while keeping low-vol adjustment for risk control.
        risk_pct = 0.0075 if self.low_vol_regime else 0.015
        risk_amount = equity * risk_pct
        atr_val = self.atr[-1]
        # 🌙✨ OPTIMIZATION: Tightened stop distance to 1.5*ATR (from 2*ATR) for better risk-reward, allowing larger positions without excessive risk.
        stop_distance = 1.5 * atr_val
        if stop_distance == 0:
            return 0
        pos_size = risk_amount / stop_distance
        size = pos_size  # 🌙✨ OPTIMIZATION: Use fractional sizes (0-1 relative to equity implied) for precision in volatile assets like BTC.
        if self.low_vol_regime:
            print("🌙📉 Low volatility regime detected, reducing position size by 50%!")
        return max(size, 0.01)  # Ensure at least minimal position

    def next(self):
        if len(self.data) < 2:
            return
        if np.isnan(self.ema200[-1]):
            return
        
        current_price = self.data.Close[-1]
        atr = self.atr[-1]
        vol = self.data.Volume[-1]
        rsi = self.rsi[-1]
        
        # Debug print every 100 bars or so, but sparingly
        if len(self.data) % 100 == 0:
            print(f"🌙📊 Bar {len(self.data)}: Close={current_price:.2f}, EMA50={self.ema50[-1]:.2f}, EMA200={self.ema200[-1]:.2f}, ATR={atr:.2f}, RSI={rsi:.2f}")
        
        # 🌙✨ OPTIMIZATION: Updated crossovers to use EMA for quicker signal generation.
        long_cross = (self.ema50[-2] < self.ema200[-2] and self.ema50[-1] > self.ema200[-1])
        short_cross = (self.ema50[-2] > self.ema200[-2] and self.ema50[-1] < self.ema200[-1])
        
        # 🌙✨ OPTIMIZATION: Adjusted low-vol threshold to 0.7 (from 0.5) using shorter SMA_ATR for less frequent conservative mode, allowing more trades.
        self.low_vol_regime = atr < 0.7 * self.sma_atr[-1]
        
        if self.position:
            pos = self.position
            current_bar = len(self.data.Close) - 1
            bars_in_trade = current_bar - self.entry_step
            profit_distance = abs(current_price - self.entry_price)
            
            # Reversal exit
            if pos.is_long and short_cross:
                self.position.close()
                print("🌙🔄 EMA reversal exit on long position!")
                return
            if not pos.is_long and long_cross:
                self.position.close()
                print("🌙🔄 EMA reversal exit on short position!")
                return
            
            # 🌙✨ OPTIMIZATION: Extended time-based exit to 15 bars (from 10) and require profit <1.5*ATR (from ATR) to hold winners longer for bigger returns.
            if bars_in_trade > 15 and profit_distance < 1.5 * atr:
                self.position.close()
                print("🌙⏰ Time-based exit: Insufficient progress in 15 bars!")
                return
            
            # Emergency volatility exit
            if atr > 2 * self.sma_atr50[-1]:
                self.position.close()
                print("🌙⚠️ Emergency exit: ATR spike detected!")
                return
            
            # SL/TP/Trailing
            if pos.is_long:
                # 🌙✨ OPTIMIZATION: Initial SL to 1.5*ATR (from 2*ATR), TP to 4*ATR (from 3*ATR) for improved 2.67:1 R:R to target higher returns.
                sl = self.entry_price - 1.5 * self.entry_atr
                profit = current_price - self.entry_price
                # 🌙✨ OPTIMIZATION: Trailing activates after 2*ATR profit (from 1*ATR), moves to +1*ATR (from 0.5), trails at 2*ATR (from 1.5) to lock in more gains.
                if profit > 2 * self.entry_atr:
                    sl = max(sl, self.entry_price + 1 * self.entry_atr)
                trail_sl = current_price - 2 * atr
                sl = max(sl, trail_sl)
                
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
                    sl = min(sl, self.entry_price - 1 * self.entry_atr)
                trail_sl = current_price + 2 * atr
                sl = min(sl, trail_sl)
                
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
            # 🌙✨ OPTIMIZATION: Tightened filters - vol >1.2*avg (from 1*), ATR >1.1*sma_atr (from 1*) for higher quality setups, reducing false signals.
            vol_ok = vol > 1.2 * self.avg_vol[-1]
            atr_ok = atr > 1.1 * self.sma_atr[-1]
            # 🌙✨ OPTIMIZATION: Added RSI momentum filter (long: RSI>50, short: RSI<50) and trend filter (long: close>EMA200, short: close<EMA200) to align with prevailing trend and momentum.
            rsi_long_ok = rsi > 50
            rsi_short_ok = rsi < 50
            trend_long_ok = current_price > self.ema200[-1]
            trend_short_ok = current_price < self.ema200[-1]
            
            if long_cross and atr_ok and vol_ok and rsi_long_ok and trend_long_ok:
                size = self.calculate_size()
                if size > 0:
                    self.buy(size=size)
                    self.entry_atr = atr
                    self.entry_price = current_price
                    self.entry_step = len(self.data) - 1
                    print(f"🌙🚀 LONG ENTRY! Price: {current_price:.2f}, Size: {size}, ATR: {atr:.2f}, Vol OK: {vol_ok}, RSI: {rsi:.2f} ✨")
                else:
                    print("🌙❌ Long signal but size=0, skipped.")
            elif short_cross and atr_ok and vol_ok and rsi_short_ok and trend_short_ok:
                size = self.calculate_size()
                if size > 0:
                    self.sell(size=size)
                    self.entry_atr = atr
                    self.entry_price = current_price
                    self.entry_step = len(self.data) - 1
                    print(f"🌙📉 SHORT ENTRY! Price: {current_price:.2f}, Size: {size}, ATR: {atr:.2f}, Vol OK: {vol_ok}, RSI: {rsi:.2f} ✨")
                else:
                    print("🌙❌ Short signal but size=0, skipped.")
            elif long_cross or short_cross:
                print(f"🌙⚠️ Crossover detected but filters failed: ATR_OK={atr_ok}, Vol_OK={vol_ok}, RSI={rsi:.2f}, Trend OK={trend_long_ok if long_cross else trend_short_ok}")
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
print("🌙✨ Optimized Backtest completed! 🚀")