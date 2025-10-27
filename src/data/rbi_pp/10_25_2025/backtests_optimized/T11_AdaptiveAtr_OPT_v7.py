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
        
        # Original indicators
        self.sma50 = self.I(talib.SMA, close, timeperiod=50)
        self.sma200 = self.I(talib.SMA, close, timeperiod=200)
        self.atr = self.I(talib.ATR, high, low, close, timeperiod=14)
        self.sma_atr = self.I(talib.SMA, self.atr, timeperiod=20)
        self.sma_atr50 = self.I(talib.SMA, self.atr, timeperiod=50)
        self.avg_vol = self.I(talib.SMA, volume, timeperiod=20)
        
        # OPTIMIZATION: Added RSI for momentum confirmation to filter low-quality crossovers
        # This ensures entries align with bullish/bearish momentum, improving win rate and reducing whipsaws
        self.rsi = self.I(talib.RSI, close, timeperiod=14)
        
        # OPTIMIZATION: Added a longer-term trend filter using EMA200 to only trade in the direction of the major trend
        # This avoids counter-trend trades in ranging or adverse markets, focusing on high-probability setups
        self.ema200 = self.I(talib.EMA, close, timeperiod=200)
        
        print("🌙✨ AdaptiveAtr indicators initialized with RSI and EMA200 filters! 🚀")

    def calculate_size(self):
        equity = self.equity
        # OPTIMIZATION: Increased base risk to 1.5% in normal regime (from 1%) and 0.75% in low vol (from 0.5%)
        # This allows larger positions to amplify returns while still managing risk; realistic as BTC can handle it on 15m
        risk_pct = 0.0075 if self.low_vol_regime else 0.015
        risk_amount = equity * risk_pct
        # OPTIMIZATION: Adjusted stop_distance to 1.5 * ATR (from 2) for tighter risk, better R:R with new TP
        atr_val = self.atr[-1]
        stop_distance = 1.5 * atr_val
        if stop_distance == 0:
            return 0
        pos_size = risk_amount / stop_distance
        size = int(round(pos_size))
        if self.low_vol_regime:
            print("🌙📉 Low volatility regime detected, reducing position size!")
        return max(size, 1)  # Ensure at least 1 unit

    def next(self):
        if len(self.data) < 2:
            return
        if np.isnan(self.sma200[-1]):
            return
        
        current_price = self.data.Close[-1]
        atr = self.atr[-1]
        vol = self.data.Volume[-1]
        rsi = self.rsi[-1]
        
        # Debug print every 100 bars or so, but sparingly
        if len(self.data) % 100 == 0:
            print(f"🌙📊 Bar {len(self.data)}: Close={current_price:.2f}, SMA50={self.sma50[-1]:.2f}, SMA200={self.sma200[-1]:.2f}, ATR={atr:.2f}, RSI={rsi:.1f}")
        
        long_cross = (self.sma50[-2] < self.sma200[-2] and self.sma50[-1] > self.sma200[-1])
        short_cross = (self.sma50[-2] > self.sma200[-2] and self.sma50[-1] < self.sma200[-1])
        
        # OPTIMIZATION: Tightened low vol regime threshold to 0.6 * SMA_ATR50 (from 0.5) to be less conservative
        # This allows more trades in mildly low vol periods without overexposing
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
            
            # OPTIMIZATION: Increased time-based exit threshold to 15 bars (from 10) and profit check to 1.5*ATR (from 1*ATR)
            # This gives trends more room to develop on 15m BTC data, reducing premature exits on potential winners
            if bars_in_trade > 15 and profit_distance < 1.5 * atr:
                self.position.close()
                print("🌙⏰ Time-based exit: Insufficient progress after 15 bars!")
                return
            
            # Emergency volatility exit
            if atr > 2 * self.sma_atr50[-1]:
                self.position.close()
                print("🌙⚠️ Emergency exit: ATR spike detected!")
                return
            
            # SL/TP/Trailing
            if pos.is_long:
                # OPTIMIZATION: Tightened initial SL to 1.5*entry_ATR (from 2) for better risk control
                sl = self.entry_price - 1.5 * self.entry_atr
                profit = current_price - self.entry_price
                # OPTIMIZATION: Start trailing earlier at 0.75*entry_ATR profit (from 1), with tighter trail 1.25*current_ATR (from 1.5)
                if profit > 0.75 * self.entry_atr:
                    sl = max(sl, self.entry_price + 0.75 * self.entry_atr)
                trail_sl = current_price - 1.25 * atr
                sl = max(sl, trail_sl)
                
                # OPTIMIZATION: Increased TP to 4.5*entry_ATR (from 3) for higher reward potential, aiming for 1:3 R:R with new SL
                tp = self.entry_price + 4.5 * self.entry_atr
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
                if profit > 0.75 * self.entry_atr:
                    sl = min(sl, self.entry_price - 0.75 * self.entry_atr)
                trail_sl = current_price + 1.25 * atr
                sl = min(sl, trail_sl)
                
                tp = self.entry_price - 4.5 * self.entry_atr
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
            # OPTIMIZATION: Tightened volume filter to 1.2 * avg_vol (from 1.0) for stronger confirmation of interest
            vol_ok = vol > 1.2 * self.avg_vol[-1]
            # OPTIMIZATION: Kept ATR filter but made it stricter: > 1.1 * SMA_ATR (from 1.0) to avoid weak volatility setups
            atr_ok = atr > 1.1 * self.sma_atr[-1]
            # OPTIMIZATION: Added RSI momentum filter: >55 for long (bullish), <45 for short (bearish) to catch stronger moves
            rsi_long_ok = rsi > 55
            rsi_short_ok = rsi < 45
            # OPTIMIZATION: Added trend filter: Long only if price > EMA200 (uptrend), short only if < EMA200 (downtrend)
            trend_long_ok = current_price > self.ema200[-1]
            trend_short_ok = current_price < self.ema200[-1]
            
            if long_cross and atr_ok and vol_ok and rsi_long_ok and trend_long_ok:
                size = self.calculate_size()
                if size > 0:
                    self.buy(size=size)
                    self.entry_atr = atr
                    self.entry_price = current_price
                    self.entry_step = len(self.data) - 1
                    print(f"🌙🚀 LONG ENTRY! Price: {current_price:.2f}, Size: {size}, ATR: {atr:.2f}, RSI: {rsi:.1f}, Vol OK: {vol_ok} ✨")
                else:
                    print("🌙❌ Long signal but size=0, skipped.")
            elif short_cross and atr_ok and vol_ok and rsi_short_ok and trend_short_ok:
                size = self.calculate_size()
                if size > 0:
                    self.sell(size=size)
                    self.entry_atr = atr
                    self.entry_price = current_price
                    self.entry_step = len(self.data) - 1
                    print(f"🌙📉 SHORT ENTRY! Price: {current_price:.2f}, Size: {size}, ATR: {atr:.2f}, RSI: {rsi:.1f}, Vol OK: {vol_ok} ✨")
                else:
                    print("🌙❌ Short signal but size=0, skipped.")
            elif long_cross or short_cross:
                print(f"🌙⚠️ Crossover detected but filters failed: ATR_OK={atr_ok}, Vol_OK={vol_ok}, RSI_L={rsi_long_ok if long_cross else 'N/A'}, Trend_L={trend_long_ok if long_cross else 'N/A'}")
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