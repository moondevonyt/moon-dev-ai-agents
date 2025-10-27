import pandas as pd
import talib
from backtesting import Backtest, Strategy
import numpy as np

class AdaptiveAtr(Strategy):
    entry_atr = 0
    entry_price = 0
    low_vol_regime = False
    entry_step = 0
    scaled_out = False

    def init(self):
        close = self.data.Close
        high = self.data.High
        low = self.data.Low
        volume = self.data.Volume
        
        # 🌙✨ Optimization: Faster SMAs (20/100 instead of 50/200) for more responsive signals and increased trade frequency on 15m BTC data
        self.sma_fast = self.I(talib.SMA, close, timeperiod=20)
        self.sma_slow = self.I(talib.SMA, close, timeperiod=100)
        # 🌙✨ Optimization: Shorter ATR period (10 instead of 14) for quicker volatility adaptation
        self.atr = self.I(talib.ATR, high, low, close, timeperiod=10)
        self.sma_atr = self.I(talib.SMA, self.atr, timeperiod=20)
        self.sma_atr50 = self.I(talib.SMA, self.atr, timeperiod=50)
        self.avg_vol = self.I(talib.SMA, volume, timeperiod=20)
        # 🌙✨ Optimization: Added RSI for momentum confirmation to filter high-quality entries (avoid weak crossovers)
        self.rsi = self.I(talib.RSI, close, timeperiod=14)
        # 🌙✨ Optimization: Added ADX for trend strength filter to avoid choppy markets and only trade strong trends
        self.adx = self.I(talib.ADX, high, low, close, timeperiod=14)
        
        print("🌙✨ AdaptiveAtr indicators initialized! 🚀")

    def calculate_size(self, current_price, atr_val):
        equity = self.equity
        # 🌙✨ Optimization: Increased base risk to 2% (low vol 1%) for higher returns while maintaining risk management; cap at full equity to prevent over-leverage
        risk_pct = 0.01 if self.low_vol_regime else 0.02
        stop_distance = 2 * atr_val
        rel_stop = stop_distance / current_price
        if rel_stop == 0:
            return 0
        fraction = risk_pct / rel_stop
        fraction = min(1.0, fraction)
        if self.low_vol_regime:
            print("🌙📉 Low volatility regime detected, reducing risk!")
        return fraction

    def next(self):
        if len(self.data) < 2:
            return
        if np.isnan(self.sma_slow[-1]):
            return
        
        current_price = self.data.Close[-1]
        atr = self.atr[-1]
        vol = self.data.Volume[-1]
        
        # Debug print every 100 bars or so, but sparingly
        if len(self.data) % 100 == 0:
            print(f"🌙📊 Bar {len(self.data)}: Close={current_price:.2f}, SMA20={self.sma_fast[-1]:.2f}, SMA100={self.sma_slow[-1]:.2f}, ATR={atr:.2f}")
        
        # 🌙✨ Optimization: Updated crossovers to use faster SMAs
        long_cross = (self.sma_fast[-2] < self.sma_slow[-2] and self.sma_fast[-1] > self.sma_slow[-1])
        short_cross = (self.sma_fast[-2] > self.sma_slow[-2] and self.sma_fast[-1] < self.sma_slow[-1])
        
        # 🌙✨ Optimization: Adjusted low-vol threshold to 0.7 (less conservative) to allow more trades in mildly low vol
        self.low_vol_regime = atr < 0.7 * self.sma_atr50[-1]
        
        if self.position:
            pos = self.position
            current_bar = len(self.data.Close) - 1
            bars_in_trade = current_bar - self.entry_step
            profit_distance = abs(current_price - self.entry_price)
            is_long = pos.is_long
            profit = (current_price - self.entry_price) if is_long else (self.entry_price - current_price)
            
            # 🌙✨ Optimization: Added partial scale-out at 2*ATR profit to lock in gains while letting winners run
            if profit > 2 * self.entry_atr and not self.scaled_out:
                scale_size = abs(pos.size) * 0.5
                if is_long:
                    self.sell(size=scale_size)
                else:
                    self.buy(size=scale_size)
                self.scaled_out = True
                print("🌙📤 Scaled out 50% at 2*ATR profit!")
                return
            
            # Reversal exit
            if is_long and short_cross:
                self.position.close()
                print("🌙🔄 SMA reversal exit on long position!")
                return
            if not is_long and long_cross:
                self.position.close()
                print("🌙🔄 SMA reversal exit on short position!")
                return
            
            # 🌙✨ Optimization: Extended time-based exit to 20 bars with tighter profit check (<0.5*ATR) to give trades more room while cutting stagnant ones
            if bars_in_trade > 20 and profit_distance < 0.5 * atr:
                self.position.close()
                print("🌙⏰ Time-based exit: No progress in 20 bars!")
                return
            
            # 🌙✨ Optimization: Tightened emergency exit threshold to 1.8x for quicker response to vol spikes
            if atr > 1.8 * self.sma_atr50[-1]:
                self.position.close()
                print("🌙⚠️ Emergency exit: ATR spike detected!")
                return
            
            # SL/TP/Trailing
            if is_long:
                sl = self.entry_price - 2 * self.entry_atr
                # 🌙✨ Optimization: Start trailing earlier (after 1.5*ATR) and more aggressively (+0.75*entry_atr breakeven, trail at 1.2*current ATR) for better profit capture
                if profit > 1.5 * self.entry_atr:
                    sl = max(sl, self.entry_price + 0.75 * self.entry_atr)
                trail_sl = current_price - 1.2 * atr
                sl = max(sl, trail_sl)
                
                # 🌙✨ Optimization: Increased TP to 4*ATR for improved risk-reward (RR ~2:1)
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
                sl = self.entry_price + 2 * self.entry_atr
                if profit > 1.5 * self.entry_atr:
                    sl = min(sl, self.entry_price - 0.75 * self.entry_atr)
                trail_sl = current_price + 1.2 * atr
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
            # 🌙✨ Optimization: Tightened volume filter to 1.2x avg for stronger confirmation; relaxed ATR to >0.9x SMA_ATR for more entries
            vol_ok = vol > 1.2 * self.avg_vol[-1]
            atr_ok = atr > 0.9 * self.sma_atr[-1]
            trend_ok = self.adx[-1] > 25  # Strong trend filter
            momentum_long_ok = self.rsi[-1] > 50
            momentum_short_ok = self.rsi[-1] < 50
            
            if long_cross and atr_ok and vol_ok and trend_ok and momentum_long_ok:
                size = self.calculate_size(current_price, atr)
                if size > 0:
                    self.buy(size=size)
                    self.entry_atr = atr
                    self.entry_price = current_price
                    self.entry_step = len(self.data) - 1
                    self.scaled_out = False  # Reset for new trade
                    print(f"🌙🚀 LONG ENTRY! Price: {current_price:.2f}, Size: {size:.4f}, ATR: {atr:.2f}, Vol OK: {vol_ok}, RSI: {self.rsi[-1]:.1f}, ADX: {self.adx[-1]:.1f} ✨")
                else:
                    print("🌙❌ Long signal but size=0, skipped.")
            elif short_cross and atr_ok and vol_ok and trend_ok and momentum_short_ok:
                size = self.calculate_size(current_price, atr)
                if size > 0:
                    self.sell(size=size)
                    self.entry_atr = atr
                    self.entry_price = current_price
                    self.entry_step = len(self.data) - 1
                    self.scaled_out = False  # Reset for new trade
                    print(f"🌙📉 SHORT ENTRY! Price: {current_price:.2f}, Size: {size:.4f}, ATR: {atr:.2f}, Vol OK: {vol_ok}, RSI: {self.rsi[-1]:.1f}, ADX: {self.adx[-1]:.1f} ✨")
                else:
                    print("🌙❌ Short signal but size=0, skipped.")
            elif long_cross or short_cross:
                print(f"🌙⚠️ Crossover detected but filters failed: ATR_OK={atr_ok}, Vol_OK={vol_ok}, Trend_OK={trend_ok}, Momentum_OK={momentum_long_ok if long_cross else momentum_short_ok}")
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