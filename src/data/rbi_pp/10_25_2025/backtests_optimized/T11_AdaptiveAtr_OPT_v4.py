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
        
        # 🌙✨ OPTIMIZATION: Changed to faster SMAs (20/100) for more responsive signals on 15m timeframe, increasing trade frequency realistically
        self.sma20 = self.I(talib.SMA, close, timeperiod=20)
        self.sma100 = self.I(talib.SMA, close, timeperiod=100)
        # Kept SMA200 for potential trend filter if needed, but using SMA100 as primary long-term
        self.sma200 = self.I(talib.SMA, close, timeperiod=200)
        self.atr = self.I(talib.ATR, high, low, close, timeperiod=14)
        self.sma_atr = self.I(talib.SMA, self.atr, timeperiod=20)
        self.sma_atr50 = self.I(talib.SMA, self.atr, timeperiod=50)
        self.avg_vol = self.I(talib.SMA, volume, timeperiod=20)
        
        # 🌙✨ OPTIMIZATION: Added ADX for trend strength filter to avoid choppy markets, and RSI for momentum confirmation
        self.adx = self.I(talib.ADX, high, low, close, timeperiod=14)
        self.rsi = self.I(talib.RSI, close, timeperiod=14)
        
        print("🌙✨ AdaptiveAtr indicators initialized with optimizations! 🚀")

    def calculate_size(self):
        equity = self.equity
        # 🌙✨ OPTIMIZATION: Increased base risk to 0.015 for higher exposure to achieve target returns, while still managing risk
        risk_pct = 0.015
        risk_amount = equity * risk_pct
        atr_val = self.atr[-1]
        stop_distance = 1.5 * atr_val  # Align with updated SL distance
        if stop_distance == 0:
            return 0
        pos_size = risk_amount / stop_distance
        size = int(round(pos_size))
        # 🌙✨ Since low_vol_regime now skips entries, removed the 50% reduction logic here
        return max(size, 1)  # Ensure at least 1 unit

    def next(self):
        if len(self.data) < 2:
            return
        if np.isnan(self.sma100[-1]):
            return
        
        current_price = self.data.Close[-1]
        atr = self.atr[-1]
        vol = self.data.Volume[-1]
        
        # Debug print every 100 bars or so, but sparingly
        if len(self.data) % 100 == 0:
            print(f"🌙📊 Bar {len(self.data)}: Close={current_price:.2f}, SMA20={self.sma20[-1]:.2f}, SMA100={self.sma100[-1]:.2f}, ATR={atr:.2f}")
        
        # 🌙✨ OPTIMIZATION: Updated crossovers to use faster SMA20/SMA100 for more timely entries on 15m data
        long_cross = (self.sma20[-2] < self.sma100[-2] and self.sma20[-1] > self.sma100[-1])
        short_cross = (self.sma20[-2] > self.sma100[-2] and self.sma20[-1] < self.sma100[-1])
        
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
            
            # 🌙✨ OPTIMIZATION: Extended time-based exit to 15 bars to allow more room for trends to develop without premature exits
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
                # 🌙✨ OPTIMIZATION: Tightened initial SL to 1.5 ATR and improved TP to 4 ATR for better 2.67:1 RR; adjusted trailing to start after 2 ATR profit and trail at 2 ATR for better profit capture
                sl = self.entry_price - 1.5 * self.entry_atr
                profit = current_price - self.entry_price
                if profit > 2 * self.entry_atr:
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
            # 🌙✨ OPTIMIZATION: Skip entries in low volatility regime to avoid whipsaws and focus on high-quality trending setups
            if self.low_vol_regime:
                return
            
            # 🌙✨ OPTIMIZATION: Tightened volume filter to 1.2x average for stronger confirmation; added RSI momentum ( >50 for long, <50 for short) and ADX >25 for trend strength; added trend filter (price above SMA100 for long, below for short) to align with regime
            vol_ok = vol > 1.2 * self.avg_vol[-1]
            atr_ok = atr > self.sma_atr[-1]
            adx_ok = self.adx[-1] > 25
            
            if long_cross and atr_ok and vol_ok and adx_ok:
                rsi_ok = self.rsi[-1] > 50
                trend_ok = current_price > self.sma100[-1]
                if rsi_ok and trend_ok:
                    size = self.calculate_size()
                    if size > 0:
                        self.buy(size=size)
                        self.entry_atr = atr
                        self.entry_price = current_price
                        self.entry_step = len(self.data) - 1
                        print(f"🌙🚀 LONG ENTRY! Price: {current_price:.2f}, Size: {size}, ATR: {atr:.2f}, Vol OK: {vol_ok}, RSI: {self.rsi[-1]:.1f}, ADX: {self.adx[-1]:.1f} ✨")
                    else:
                        print("🌙❌ Long signal but size=0, skipped.")
                else:
                    print(f"🌙⚠️ Long crossover but momentum/trend failed: RSI_OK={rsi_ok}, Trend_OK={trend_ok}")
            elif short_cross and atr_ok and vol_ok and adx_ok:
                rsi_ok = self.rsi[-1] < 50
                trend_ok = current_price < self.sma100[-1]
                if rsi_ok and trend_ok:
                    size = self.calculate_size()
                    if size > 0:
                        self.sell(size=size)
                        self.entry_atr = atr
                        self.entry_price = current_price
                        self.entry_step = len(self.data) - 1
                        print(f"🌙📉 SHORT ENTRY! Price: {current_price:.2f}, Size: {size}, ATR: {atr:.2f}, Vol OK: {vol_ok}, RSI: {self.rsi[-1]:.1f}, ADX: {self.adx[-1]:.1f} ✨")
                    else:
                        print("🌙❌ Short signal but size=0, skipped.")
                else:
                    print(f"🌙⚠️ Short crossover but momentum/trend failed: RSI_OK={rsi_ok}, Trend_OK={trend_ok}")
            elif long_cross or short_cross:
                print(f"🌙⚠️ Crossover detected but filters failed: ATR_OK={atr_ok}, Vol_OK={vol_ok}, ADX_OK={adx_ok}")
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