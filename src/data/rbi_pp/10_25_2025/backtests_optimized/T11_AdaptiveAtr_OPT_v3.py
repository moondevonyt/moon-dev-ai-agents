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
        
        # 🌙✨ Optimization: Switched to EMAs for faster signal response to capture trends earlier and reduce lag
        self.ema50 = self.I(talib.EMA, close, timeperiod=50)
        self.ema200 = self.I(talib.EMA, close, timeperiod=200)
        self.atr = self.I(talib.ATR, high, low, close, timeperiod=14)
        self.sma_atr = self.I(talib.SMA, self.atr, timeperiod=20)
        self.sma_atr50 = self.I(talib.SMA, self.atr, timeperiod=50)
        self.avg_vol = self.I(talib.SMA, volume, timeperiod=20)
        
        # 🌙✨ Optimization: Added RSI for momentum confirmation and ADX for trend strength filter to avoid choppy markets
        self.rsi = self.I(talib.RSI, close, timeperiod=14)
        self.adx = self.I(talib.ADX, high, low, close, timeperiod=14)
        
        print("🌙✨ AdaptiveAtr indicators initialized with EMA, RSI, and ADX optimizations! 🚀")

    def calculate_size(self):
        equity = self.equity
        # 🌙✨ Optimization: Increased base risk to 2% (from 1%) for higher exposure while maintaining risk management; low vol still halves it to 1%
        risk_pct = 0.01 if self.low_vol_regime else 0.02
        risk_amount = equity * risk_pct
        atr_val = self.atr[-1]
        stop_distance = 2 * atr_val
        if stop_distance == 0:
            return 0
        pos_size = risk_amount / stop_distance
        # 🌙✨ Optimization: Allow fractional sizes for more precise position sizing in volatile assets like BTC
        size = pos_size
        if self.low_vol_regime:
            print("🌙📉 Low volatility regime detected, reducing position size by 50%!")
        return max(size, 0.01) if size > 0 else 0  # Minimum fractional size to avoid zero

    def next(self):
        if len(self.data) < 2:
            return
        if np.isnan(self.ema200[-1]):
            return
        
        current_price = self.data.Close[-1]
        atr = self.atr[-1]
        vol = self.data.Volume[-1]
        
        # Debug print every 100 bars or so, but sparingly
        if len(self.data) % 100 == 0:
            print(f"🌙📊 Bar {len(self.data)}: Close={current_price:.2f}, EMA50={self.ema50[-1]:.2f}, EMA200={self.ema200[-1]:.2f}, ATR={atr:.2f}, RSI={self.rsi[-1]:.2f}, ADX={self.adx[-1]:.2f}")
        
        # 🌙✨ Optimization: Use EMA crosses for quicker entries on trend changes
        long_cross = (self.ema50[-2] < self.ema200[-2] and self.ema50[-1] > self.ema200[-1])
        short_cross = (self.ema50[-2] > self.ema200[-2] and self.ema50[-1] < self.ema200[-1])
        
        self.low_vol_regime = atr < 0.5 * self.sma_atr50[-1]
        
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
            
            # 🌙✨ Optimization: Extended time-based exit to 15 bars (from 10) to allow more room for trends to develop
            if bars_in_trade > 15 and profit_distance < atr:
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
                
                # 🌙✨ Optimization: Increased TP to 4x ATR (from 3x) for better risk-reward ratio to boost returns
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
                
                # 🌙✨ Optimization: Increased TP to 4x ATR (from 3x) for better risk-reward ratio to boost returns
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
            # 🌙✨ Optimization: Tightened filters - vol >1.2x avg (from 1x), atr >1.1x recent avg (from 1x); added RSI momentum ( >50 long/<50 short) and ADX>25 for trend strength; added price above/below EMA200 for regime alignment
            vol_ok = vol > 1.2 * self.avg_vol[-1]
            atr_ok = atr > 1.1 * self.sma_atr[-1]
            trend_ok_long = current_price > self.ema200[-1]
            trend_ok_short = current_price < self.ema200[-1]
            rsi_long_ok = self.rsi[-1] > 50
            rsi_short_ok = self.rsi[-1] < 50
            adx_ok = self.adx[-1] > 25
            
            if long_cross and atr_ok and vol_ok and trend_ok_long and rsi_long_ok and adx_ok:
                size = self.calculate_size()
                if size > 0:
                    self.buy(size=size)
                    self.entry_atr = atr
                    self.entry_price = current_price
                    self.entry_step = len(self.data) - 1
                    print(f"🌙🚀 LONG ENTRY! Price: {current_price:.2f}, Size: {size:.2f}, ATR: {atr:.2f}, Vol OK: {vol_ok}, RSI: {self.rsi[-1]:.2f}, ADX: {self.adx[-1]:.2f} ✨")
                else:
                    print("🌙❌ Long signal but size=0, skipped.")
            elif short_cross and atr_ok and vol_ok and trend_ok_short and rsi_short_ok and adx_ok:
                size = self.calculate_size()
                if size > 0:
                    self.sell(size=size)
                    self.entry_atr = atr
                    self.entry_price = current_price
                    self.entry_step = len(self.data) - 1
                    print(f"🌙📉 SHORT ENTRY! Price: {current_price:.2f}, Size: {size:.2f}, ATR: {atr:.2f}, Vol OK: {vol_ok}, RSI: {self.rsi[-1]:.2f}, ADX: {self.adx[-1]:.2f} ✨")
                else:
                    print("🌙❌ Short signal but size=0, skipped.")
            elif long_cross or short_cross:
                print(f"🌙⚠️ Crossover detected but filters failed: ATR_OK={atr_ok}, Vol_OK={vol_ok}, Trend_L={trend_ok_long}, Trend_S={trend_ok_short}, RSI_L={rsi_long_ok}, RSI_S={rsi_short_ok}, ADX={adx_ok}")
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