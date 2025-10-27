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
        
        # 🌙✨ OPTIMIZATION: Switched to faster SMAs (20/100) for more responsive signals on 15m timeframe, increasing trade frequency to boost returns without overtrading
        self.sma20 = self.I(talib.SMA, close, timeperiod=20)
        self.sma100 = self.I(talib.SMA, close, timeperiod=100)
        # Added RSI for momentum confirmation to filter out weak crossovers
        self.rsi = self.I(talib.RSI, close, timeperiod=14)
        self.atr = self.I(talib.ATR, high, long, close, timeperiod=14)
        self.sma_atr = self.I(talib.SMA, self.atr, timeperiod=20)
        self.sma_atr50 = self.I(talib.SMA, self.atr, timeperiod=50)
        self.avg_vol = self.I(talib.SMA, volume, timeperiod=20)
        
        # 🌙✨ OPTIMIZATION: Added longer-term SMA200 as a trend filter to only take longs above it and shorts below, improving directional bias and win rate
        self.sma200 = self.I(talib.SMA, close, timeperiod=200)
        
        print("🌙✨ AdaptiveAtr indicators initialized with optimizations! 🚀")

    def calculate_size(self):
        equity = self.equity
        # 🌙✨ OPTIMIZATION: Increased base risk to 2% (from 1%) for higher returns, but still reduce in low vol; caps max risk to maintain drawdown control
        risk_pct = 0.01 if self.low_vol_regime else 0.02
        risk_amount = equity * risk_pct
        atr_val = self.atr[-1]
        # 🌙✨ OPTIMIZATION: Tightened stop distance to 1.5*ATR (from 2*) for better R:R, allowing larger positions while keeping risk fixed
        stop_distance = 1.5 * atr_val
        if stop_distance == 0:
            return 0
        pos_size = risk_amount / stop_distance
        size = int(round(pos_size))
        # 🌙✨ OPTIMIZATION: In low vol, reduce size by 50% but ensure min 1; added equity-based cap to prevent oversized positions
        if self.low_vol_regime:
            size = max(int(size * 0.5), 1)
            print("🌙📉 Low volatility regime detected, reducing position size by 50%!")
        # Cap size to 10% of equity to avoid overexposure
        max_size = int(equity * 0.1 / self.data.Close[-1])
        size = min(size, max_size)
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
            print(f"🌙📊 Bar {len(self.data)}: Close={current_price:.2f}, SMA20={self.sma20[-1]:.2f}, SMA100={self.sma100[-1]:.2f}, RSI={rsi:.2f}, ATR={atr:.2f}")
        
        # 🌙✨ OPTIMIZATION: Updated crossovers to use faster SMAs for more timely entries
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
            
            # 🌙✨ OPTIMIZATION: Reduced time-based exit to 8 bars (from 10) and require profit > 0.5*ATR for quicker exits on stagnant trades
            if bars_in_trade > 8 and profit_distance < 0.5 * atr:
                self.position.close()
                print("🌙⏰ Time-based exit: Minimal progress in 8 bars!")
                return
            
            # Emergency volatility exit
            if atr > 2 * self.sma_atr50[-1]:
                self.position.close()
                print("🌙⚠️ Emergency exit: ATR spike detected!")
                return
            
            # SL/TP/Trailing
            if pos.is_long:
                # 🌙✨ OPTIMIZATION: Tightened initial SL to 1.5*ATR (from 2*) and improved trailing to start earlier at 1*ATR profit, with tighter trail (1*ATR from high)
                sl = self.entry_price - 1.5 * self.entry_atr
                profit = current_price - self.entry_price
                if profit > self.entry_atr:
                    sl = max(sl, self.entry_price + 1 * self.entry_atr)
                trail_sl = current_price - 1 * atr  # Tighter trailing for better lock-in
                sl = max(sl, trail_sl)
                
                # 🌙✨ OPTIMIZATION: Increased TP to 4*ATR (from 3*) for higher reward potential, improving overall R:R to ~2.67:1
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
                if profit > self.entry_atr:
                    sl = min(sl, self.entry_price - 1 * self.entry_atr)
                trail_sl = current_price + 1 * atr
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
            # 🌙✨ OPTIMIZATION: Stricter volume filter (1.5x avg from 1x) to ensure strong conviction entries; added RSI filter (>55 for long, <45 for short) for momentum
            vol_ok = vol > 1.5 * self.avg_vol[-1]
            atr_ok = atr > self.sma_atr[-1]
            rsi_long_ok = rsi > 55
            rsi_short_ok = rsi < 45
            
            # 🌙✨ OPTIMIZATION: Added trend filter using SMA200 - only long if price > SMA200, short if <, to align with major trend and reduce whipsaws
            trend_long_ok = current_price > self.sma200[-1]
            trend_short_ok = current_price < self.sma200[-1]
            
            if long_cross and atr_ok and vol_ok and rsi_long_ok and trend_long_ok:
                size = self.calculate_size()
                if size > 0:
                    self.buy(size=size)
                    self.entry_atr = atr
                    self.entry_price = current_price
                    self.entry_step = len(self.data) - 1
                    print(f"🌙🚀 LONG ENTRY! Price: {current_price:.2f}, Size: {size}, ATR: {atr:.2f}, RSI: {rsi:.2f}, Vol OK: {vol_ok} ✨")
                else:
                    print("🌙❌ Long signal but size=0, skipped.")
            elif short_cross and atr_ok and vol_ok and rsi_short_ok and trend_short_ok:
                size = self.calculate_size()
                if size > 0:
                    self.sell(size=size)
                    self.entry_atr = atr
                    self.entry_price = current_price
                    self.entry_step = len(self.data) - 1
                    print(f"🌙📉 SHORT ENTRY! Price: {current_price:.2f}, Size: {size}, ATR: {atr:.2f}, RSI: {rsi:.2f}, Vol OK: {vol_ok} ✨")
                else:
                    print("🌙❌ Short signal but size=0, skipped.")
            elif long_cross or short_cross:
                print(f"🌙⚠️ Crossover detected but filters failed: ATR_OK={atr_ok}, Vol_OK={vol_ok}, Trend OK (L/S)={trend_long_ok}/{trend_short_ok}, RSI={rsi:.2f}")
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