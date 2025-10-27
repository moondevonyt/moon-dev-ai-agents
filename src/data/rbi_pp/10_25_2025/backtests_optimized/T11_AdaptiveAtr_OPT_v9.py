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
        
        # 🌙✨ Optimization: Faster SMAs for more responsive signals on 15m timeframe (20 ~5h, 100 ~1.25d) to capture more trends without overtrading
        self.sma20 = self.I(talib.SMA, close, timeperiod=20)
        self.sma100 = self.I(talib.SMA, close, timeperiod=100)
        self.atr = self.I(talib.ATR, high, low, close, timeperiod=14)
        self.sma_atr = self.I(talib.SMA, self.atr, timeperiod=20)
        self.sma_atr50 = self.I(talib.SMA, self.atr, timeperiod=50)
        self.avg_vol = self.I(talib.SMA, volume, timeperiod=20)
        
        # 🌙✨ Optimization: Added RSI for momentum confirmation (avoid counter-trend entries) and ADX for trend strength filter (>25 ensures trending markets, reduces choppy trades)
        self.rsi = self.I(talib.RSI, close, timeperiod=14)
        self.adx = self.I(talib.ADX, high, low, close, timeperiod=14)
        
        print("🌙✨ AdaptiveAtr indicators initialized with optimizations! 🚀")

    def calculate_size(self):
        # 🌙✨ Optimization: Fixed risk_pct to 1.5% for balanced aggression to boost returns; use float size for fractional BTC positions (realistic for crypto)
        equity = self.equity
        risk_pct = 0.015
        risk_amount = equity * risk_pct
        atr_val = self.atr[-1]
        stop_distance = 2 * atr_val
        if stop_distance == 0:
            return 0
        pos_size = risk_amount / stop_distance
        return pos_size if pos_size > 0 else 0  # Float size, no int rounding for precision

    def next(self):
        if len(self.data) < 2:
            return
        if np.isnan(self.sma100[-1]):
            return
        
        current_price = self.data.Close[-1]
        atr = self.atr[-1]
        vol = self.data.Volume[-1]
        
        # Debug print every 100 bars or so, but sparingly (updated for new SMAs)
        if len(self.data) % 100 == 0:
            print(f"🌙📊 Bar {len(self.data)}: Close={current_price:.2f}, SMA20={self.sma20[-1]:.2f}, SMA100={self.sma100[-1]:.2f}, ATR={atr:.2f}")
        
        # 🌙✨ Optimization: Use faster SMA crossovers for more entry opportunities
        long_cross = (self.sma20[-2] < self.sma100[-2] and self.sma20[-1] > self.sma100[-1])
        short_cross = (self.sma20[-2] > self.sma100[-2] and self.sma20[-1] < self.sma100[-1])
        
        # 🌙✨ Optimization: Slightly adjusted low_vol threshold to 0.6 for better regime detection; skip entries in low vol to avoid whipsaws (improves quality)
        self.low_vol_regime = atr < 0.6 * self.sma_atr50[-1]
        
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
            
            # 🌙✨ Optimization: Extended time-based exit to 15 bars with tighter profit threshold (0.5*entry_atr) to cut stagnant trades faster
            if bars_in_trade > 15 and profit_distance < 0.5 * self.entry_atr:
                self.position.close()
                print("🌙⏰ Time-based exit: No progress in 15 bars!")
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
                
                # 🌙✨ Optimization: Increased TP to 4*ATR for better R:R (2:1) to capture larger moves and boost returns
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
                profit = self.entry_price - current_price
                if profit > self.entry_atr:
                    sl = min(sl, self.entry_price - 0.5 * self.entry_atr)
                trail_sl = current_price + 1.5 * atr
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
            # 🌙✨ Optimization: Loosened ATR filter slightly (0.8*sma_atr) for more entries; added RSI momentum (>50 long/<50 short) and ADX>25 for quality; vol>1.2*avg for confirmation; skip low_vol regime
            vol_ok = vol > 1.2 * self.avg_vol[-1]
            atr_ok = atr > 0.8 * self.sma_atr[-1]
            momentum_long = self.rsi[-1] > 50
            momentum_short = self.rsi[-1] < 50
            trend_strength = self.adx[-1] > 25
            
            if (long_cross and not self.low_vol_regime and atr_ok and vol_ok and momentum_long and trend_strength):
                size = self.calculate_size()
                if size > 0:
                    self.buy(size=size)
                    self.entry_atr = atr
                    self.entry_price = current_price
                    self.entry_step = len(self.data) - 1
                    print(f"🌙🚀 LONG ENTRY! Price: {current_price:.2f}, Size: {size:.4f}, ATR: {atr:.2f}, RSI: {self.rsi[-1]:.1f}, ADX: {self.adx[-1]:.1f}, Vol OK: {vol_ok} ✨")
                else:
                    print("🌙❌ Long signal but size=0, skipped.")
            elif (short_cross and not self.low_vol_regime and atr_ok and vol_ok and momentum_short and trend_strength):
                size = self.calculate_size()
                if size > 0:
                    self.sell(size=size)
                    self.entry_atr = atr
                    self.entry_price = current_price
                    self.entry_step = len(self.data) - 1
                    print(f"🌙📉 SHORT ENTRY! Price: {current_price:.2f}, Size: {size:.4f}, ATR: {atr:.2f}, RSI: {self.rsi[-1]:.1f}, ADX: {self.adx[-1]:.1f}, Vol OK: {vol_ok} ✨")
                else:
                    print("🌙❌ Short signal but size=0, skipped.")
            elif long_cross or short_cross:
                print(f"🌙⚠️ Crossover detected but filters failed: LowVol={self.low_vol_regime}, ATR_OK={atr_ok}, Vol_OK={vol_ok}, RSI={self.rsi[-1]:.1f}, ADX={self.adx[-1]:.1f}")
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