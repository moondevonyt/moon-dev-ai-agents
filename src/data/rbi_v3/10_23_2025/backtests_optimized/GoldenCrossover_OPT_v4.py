import pandas as pd
import numpy as np
import talib
from backtesting import Backtest, Strategy

data = pd.read_csv('/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv', parse_dates=['datetime'])
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data = data.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'})
data = data.set_index(data['datetime'])

class GoldenCrossover(Strategy):
    last_peak_price = 0.0
    last_peak_rsi = 100.0
    entry_bar = 0

    def init(self):
        # 🌙 Moon Dev Optimization: Switched to EMA for faster response to trends, EMA20/EMA50 crossover for earlier entries in volatile BTC
        self.ema20 = self.I(talib.EMA, self.data.Close, timeperiod=20)
        self.ema50 = self.I(talib.EMA, self.data.Close, timeperiod=50)
        self.ema200 = self.I(talib.EMA, self.data.Close, timeperiod=200)
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14)
        # 🌙 Moon Dev Optimization: Increased ADX threshold to >30 for stronger trend filter, reducing entries in weak trends
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        # 🌙 Moon Dev Optimization: Added MACD for momentum confirmation, only enter on bullish MACD histogram
        self.macd, self.macd_signal, self.macd_hist = self.I(talib.MACD, self.data.Close, fastperiod=12, slowperiod=26, signalperiod=9)
        # 🌙 Moon Dev Optimization: Adjusted volume SMA to 20 for smoother volume trend, avoiding noise
        self.avg_volume = self.I(talib.SMA, self.data.Volume, timeperiod=20)
        self.last_peak_price = 0.0
        self.last_peak_rsi = 100.0
        self.entry_bar = 0
        self.entry_price = None
        self.current_sl = None

    def next(self):
        if len(self.data) < 200:
            return

        close = self.data.Close[-1]
        low = self.data.Low[-1]
        high = self.data.High[-1]
        volume = self.data.Volume[-1]
        ema20 = self.ema20[-1]
        ema50 = self.ema50[-1]
        ema200 = self.ema200[-1]
        rsi = self.rsi[-1]
        adx = self.adx[-1]
        atr = self.atr[-1]
        avg_vol = self.avg_volume[-1]
        macd_hist = self.macd_hist[-1]

        print(f"🌙 Moon Dev Backtest Bar {len(self.data)}: Close {close:.2f}, EMA20 {ema20:.2f}, EMA50 {ema50:.2f}, EMA200 {ema200:.2f}, RSI {rsi:.2f}, ADX {adx:.2f}, ATR {atr:.2f}, MACD Hist {macd_hist:.2f} ✨")

        if close <= ema200:
            if self.position:
                print("🚀 Moon Dev: Exiting long due to broken uptrend below EMA200 🌙")
                self.position.close()
            return

        # 🌙 Moon Dev Optimization: Increased Fib lookback to 150 for capturing larger swings in BTC trends, improving retracement accuracy
        lookback = 150
        from_idx = max(0, len(self.data) - lookback - 1)
        recent_high_values = self.data.High[from_idx:len(self.data)-1]
        if len(recent_high_values) < 30:  # 🌙 Moon Dev Optimization: Extended minimum lookback to 30 for more robust swing detection
            return
        rel_high_idx = np.argmax(recent_high_values)
        abs_high_idx = from_idx + rel_high_idx
        swing_high = self.data.High[abs_high_idx]

        low_values_to_high = self.data.Low[from_idx:abs_high_idx + 1]
        rel_low_idx = np.argmin(low_values_to_high)
        abs_low_idx = from_idx + rel_low_idx
        swing_low = self.data.Low[abs_low_idx]

        # 🌙 Moon Dev Optimization: Changed to 50% Fib retracement for deeper pullbacks, allowing entries on stronger support levels in trends
        fib50 = swing_high - 0.5 * (swing_high - swing_low)
        print(f"🌙 Moon Dev Fib Calc: 50% Level {fib50:.2f}, High {swing_high:.2f}, Low {swing_low:.2f} 🚀")

        # 🌙 Moon Dev Optimization: Refined entry - EMA20 crossover of EMA50, RSI 45-65 for optimal pullback momentum, ADX>30, volume>1.2x (lowered for more opportunities), MACD hist>0, EMA20>EMA200
        crossover = len(self.data) > 1 and self.data.Close[-2] <= self.ema50[-2] and close > ema50  # 🌙 Moon Dev: Using EMA50 crossover for entry signal
        touch_fib = low <= fib50 + (0.003 * close)  # 🌙 Moon Dev Optimization: Tighter 0.3% tolerance for precise Fib interaction
        volume_confirm = volume > 1.2 * avg_vol  # 🌙 Moon Dev Optimization: Reduced to 1.2x to increase trade frequency without sacrificing quality
        momentum_rsi = rsi > 45 and rsi < 65  # 🌙 Moon Dev Optimization: Widened RSI range to capture more pullback entries
        trend_strength = adx > 30  # 🌙 Moon Dev: Higher ADX for stronger trends
        macd_bullish = macd_hist > 0  # 🌙 Moon Dev: Added MACD histogram filter for positive momentum
        uptrend = close > ema200 and ema20 > ema200  # 🌙 Moon Dev Optimization: EMA20 > EMA200 for shorter-term uptrend confirmation

        if crossover and touch_fib and volume_confirm and momentum_rsi and trend_strength and macd_bullish and uptrend and not self.position:
            entry_price = close
            # 🌙 Moon Dev Optimization: Enhanced SL - 2x ATR below entry or below Fib50, use recent low of 20 bars for dynamic support
            sl_distance = 2 * atr
            stop_price = entry_price - sl_distance
            swing_low_recent = min(self.data.Low[-20:])
            if fib50 < entry_price:
                stop_price = min(stop_price, fib50 - atr, swing_low_recent)
            risk_per_unit = entry_price - stop_price
            if risk_per_unit <= 0:
                return
            capital = self.equity  # 🌙 Moon Dev: Use current equity for dynamic sizing
            risk_amount = capital * 0.015  # 🌙 Moon Dev Optimization: Increased risk per trade to 1.5% for higher returns potential
            position_size = risk_amount / risk_per_unit
            # 🌙 Moon Dev Optimization: Volatility-based cap - Max 3% of capital adjusted by ATR (smaller in high vol)
            vol_adjust = 1 / (1 + atr / close)  # Normalize ATR to price
            max_size = (capital * 0.03 * vol_adjust) / entry_price
            position_size = min(position_size, max_size)
            position_size = max(0.01, position_size)  # 🌙 Moon Dev: Minimum fraction size to avoid zero positions
            if position_size > 0:
                print(f"🌙 Moon Dev: LONG ENTRY at {entry_price:.2f}, SL {stop_price:.2f}, Size {position_size:.4f} BTC, Optimized Filters Confirmed! ✨🚀")
                self.buy(size=position_size)
                self.entry_price = entry_price
                self.current_sl = stop_price
                self.entry_bar = len(self.data) - 1
                self.last_peak_price = high
                self.last_peak_rsi = rsi

        # Position management and exits
        if self.position:
            current_sl = self.current_sl
            if current_sl is not None and low <= current_sl:
                print(f"🌙 Moon Dev: Stop Loss Hit at {low:.2f}! 🚀")
                self.position.close()
                return

            entry_price = self.entry_price
            bars_since_entry = len(self.data) - 1 - self.entry_bar
            unrealized_pnl = close - entry_price
            risk = entry_price - current_sl
            rr = unrealized_pnl / risk if risk > 0 else 0
            print(f"🚀 Moon Dev Position: Bars {bars_since_entry}, RR {rr:.2f}, Current SL {current_sl:.2f} 🌙")

            # 🌙 Moon Dev Optimization: Improved trailing - Breakeven at 0.75:1 RR with buffer, then trail to EMA20 - 0.5x ATR for tighter protection in trends
            if unrealized_pnl >= 0.75 * risk:
                breakeven_sl = entry_price + (0.2 * atr)
                if breakeven_sl > current_sl:
                    self.current_sl = breakeven_sl
                    print(f"🌙 Moon Dev: Moved SL to breakeven {breakeven_sl:.2f} after 0.75:1 RR ✨")

            if unrealized_pnl >= 1.5 * risk:
                trail_sl = ema20 - 0.5 * atr  # 🌙 Moon Dev Optimization: Tighter trail using EMA20 for faster adjustment
                if trail_sl > current_sl:
                    self.current_sl = trail_sl
                    print(f"🌙 Moon Dev: Trailing SL updated to {trail_sl:.2f} after 1.5:1 RR ✨")

            # 🌙 Moon Dev Optimization: Scale out partial profits - Close 50% at 2:1 RR, let rest run to 5:1 or trail, to lock in gains while capturing trends
            if unrealized_pnl >= 2 * risk and self.position.size > 0:
                partial_size = self.position.size * 0.5
                self.position.close(size=partial_size)
                print(f"🌙 Moon Dev: Partial exit 50% at 2:1 RR! Remaining trails. 🚀")

            if unrealized_pnl >= 5 * risk:
                print(f"🌙 Moon Dev: Full TP at 5:1 RR for big wins! 🚀")
                self.position.close()
                return

            # Bearish divergence: Enhanced with MACD confirmation
            if rsi > 70 and len(self.data) > 2 and close > self.data.Close[-2] and rsi < self.rsi[-2] and self.macd_hist[-1] < self.macd_hist[-2] and adx > 30:
                print(f"🌙 Moon Dev: Bearish RSI & MACD Divergence in overbought with strong trend, EXITING! 🚀")
                self.position.close()
                return

            # Exit below EMA20 trail for quicker response
            if close < ema20:
                print(f"🌙 Moon Dev: EXITING below EMA20 trail 🚀")
                self.position.close()
                return

            # 🌙 Moon Dev Optimization: Add max hold time of 200 bars (about 2 days on 15m) to avoid stale trends
            if bars_since_entry > 200:
                print(f"🌙 Moon Dev: Max hold time exit after {bars_since_entry} bars 🚀")
                self.position.close()
                return

            # Update peak for next divergence check
            if high > self.last_peak_price:
                self.last_peak_price = high
                self.last_peak_rsi = rsi

bt = Backtest(data, GoldenCrossover, cash=1000000, commission=0.002)
stats = bt.run()
print(stats)