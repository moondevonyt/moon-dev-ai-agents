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
        # 🌙 Moon Dev Optimization: Kept EMA20/50/200 but tuned to EMA12/EMA50 for even faster golden cross detection in BTC's quick moves, reducing lag while maintaining trend filter
        self.ema12 = self.I(talib.EMA, self.data.Close, timeperiod=12)
        self.ema50 = self.I(talib.EMA, self.data.Close, timeperiod=50)
        self.ema200 = self.I(talib.EMA, self.data.Close, timeperiod=200)
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14)
        # 🌙 Moon Dev Optimization: Lowered ADX to 18 for more entries in emerging trends, increasing trade frequency to boost returns
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        # 🌙 Moon Dev Optimization: Kept MACD but adjusted to faster 8/21/5 for quicker momentum signals in volatile crypto
        self.macd, self.macd_signal, _ = self.I(talib.MACD, self.data.Close, fastperiod=8, slowperiod=21, signalperiod=5)
        self.avg_volume = self.I(talib.SMA, self.data.Volume, timeperiod=10)
        self.last_peak_price = 0.0
        self.last_peak_rsi = 100.0
        self.entry_bar = 0
        self.entry_price = None
        self.current_sl = None
        # 🌙 Moon Dev Optimization: Track partial profit levels for scaling out
        self.partial_closed = False

    def next(self):
        if len(self.data) < 200:
            return

        close = self.data.Close[-1]
        low = self.data.Low[-1]
        high = self.data.High[-1]
        volume = self.data.Volume[-1]
        ema12 = self.ema12[-1]
        ema50 = self.ema50[-1]
        ema200 = self.ema200[-1]
        rsi = self.rsi[-1]
        adx = self.adx[-1]
        atr = self.atr[-1]
        macd = self.macd[-1]
        macd_signal = self.macd_signal[-1]
        avg_vol = self.avg_volume[-1]

        print(f"🌙 Moon Dev Backtest Bar {len(self.data)}: Close {close:.2f}, EMA12 {ema12:.2f}, EMA50 {ema50:.2f}, EMA200 {ema200:.2f}, RSI {rsi:.2f}, ADX {adx:.2f}, ATR {atr:.2f}, MACD {macd:.2f} ✨")

        if close <= ema200:
            if self.position:
                print("🚀 Moon Dev: Exiting long due to broken uptrend below EMA200 🌙")
                self.position.close()
            return

        # 🌙 Moon Dev Optimization: Reduced Fib lookback to 100 bars for more relevant recent swings in fast-moving BTC, improving entry timing on pullbacks
        lookback = 100
        from_idx = max(0, len(self.data) - lookback - 1)
        recent_high_values = self.data.High[from_idx:len(self.data)-1]
        if len(recent_high_values) < 30:  # 🌙 Moon Dev Optimization: Kept min lookback at 30 for robust swing detection
            return
        rel_high_idx = np.argmax(recent_high_values)
        abs_high_idx = from_idx + rel_high_idx
        swing_high = self.data.High[abs_high_idx]

        low_values_to_high = self.data.Low[from_idx:abs_high_idx + 1]
        rel_low_idx = np.argmin(low_values_to_high)
        abs_low_idx = from_idx + rel_low_idx
        swing_low = self.data.Low[abs_low_idx]

        fib618 = swing_high - 0.618 * (swing_high - swing_low)
        print(f"🌙 Moon Dev Fib Calc: 61.8% Level {fib618:.2f}, High {swing_high:.2f}, Low {swing_low:.2f} 🚀")

        # 🌙 Moon Dev Optimization: Refined entry - True golden cross (EMA12 crosses EMA50), extended Fib touch to last 10 bars for more pullback opportunities, RSI 40-70 for broader momentum window, ADX>18, volume>1.0x (relaxed for higher frequency), MACD histogram >0 for building momentum, uptrend confirmation, and either bullish candle or EMA alignment
        crossover = len(self.data) > 1 and self.ema12[-2] <= ema50[-2] and ema12 > ema50  # 🌙 Moon Dev Optimization: Switched to actual EMA12/EMA50 crossover for classic golden cross signal, more reliable trend starts
        # Check Fib touch in recent bars
        recent_lows = self.data.Low[-10:]  # 🌙 Moon Dev Optimization: Extended to 10 bars to capture more valid pullback entries without missing setups
        touch_fib = any(recent_low <= fib618 + (0.005 * close) for recent_low in recent_lows)  # 🌙 Moon Dev Optimization: Increased tolerance to 0.5% for BTC volatility, allowing slight overshoots
        volume_confirm = volume > 1.0 * avg_vol  # 🌙 Moon Dev Optimization: Relaxed to 1.0x average to increase trade opportunities while still filtering extremes
        momentum_rsi = rsi > 40 and rsi < 70  # 🌙 Moon Dev Optimization: Widened RSI range to 40-70 for earlier entries and avoiding overbought traps prematurely
        trend_strength = adx > 18  # 🌙 Moon Dev Optimization: Lowered to 18 for more moderate trend entries, boosting overall return potential
        macd_confirm = macd - macd_signal > 0  # 🌙 Moon Dev Optimization: Use MACD histogram >0 for positive momentum divergence, more sensitive than line cross
        uptrend = close > ema200 and ema12 > ema50 > ema200  # 🌙 Moon Dev Optimization: Updated to use EMA12 in stack for consistency with faster signal
        entry_confirm = close > self.data.Open[-1] or ema12 > ema50  # 🌙 Moon Dev Optimization: OR condition - bullish candle OR EMA alignment to reduce false negatives in entries

        if crossover and touch_fib and volume_confirm and momentum_rsi and trend_strength and macd_confirm and uptrend and entry_confirm and not self.position:
            entry_price = close
            # 🌙 Moon Dev Optimization: Adjusted SL to 1.5x ATR for slightly wider stops in volatile BTC, but cap at swing low to maintain tight risk
            sl_distance = 1.5 * atr
            stop_price = entry_price - sl_distance
            swing_low_recent = min(self.data.Low[-20:])  # 🌙 Moon Dev Optimization: Extended lookback to 20 bars for stronger support identification
            if fib618 < entry_price:
                stop_price = min(stop_price, fib618 - 0.5 * atr, swing_low_recent)
            risk_per_unit = entry_price - stop_price
            if risk_per_unit <= 0:
                return
            capital = 1000000
            # 🌙 Moon Dev Optimization: Increased risk per trade to 1% to amplify returns towards 50% target, while still conservative for compounding
            risk_amount = capital * 0.01
            position_size = risk_amount / risk_per_unit
            # 🌙 Moon Dev Optimization: Increased max size to 5% for higher exposure in strong signals, balanced with overall cap
            max_size = (capital * 0.05) / entry_price
            position_size = min(position_size, max_size)
            position_size = max(0.01, min(int(round(position_size)), int(capital * 0.15 / entry_price)))  # 🌙 Moon Dev Optimization: Raised cap to 15% for aggressive BTC plays, but with min 0.01 for liquidity
            if position_size > 0:
                print(f"🌙 Moon Dev: LONG ENTRY at {entry_price:.2f}, SL {stop_price:.2f}, Size {position_size} BTC, Optimized Golden Cross + Relaxed Filters! ✨🚀")
                self.buy(size=position_size)
                self.entry_price = entry_price
                self.current_sl = stop_price
                self.entry_bar = len(self.data) - 1
                self.last_peak_price = high
                self.last_peak_rsi = rsi
                self.partial_closed = False

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

            # 🌙 Moon Dev Optimization: Adjusted breakeven trigger to 0.5:1 RR for better protection, +0.3x ATR buffer to account for noise
            if unrealized_pnl >= 0.5 * risk:
                breakeven_sl = entry_price + (0.3 * atr)
                if breakeven_sl > current_sl:
                    self.current_sl = breakeven_sl
                    print(f"🌙 Moon Dev: Moved SL to breakeven {breakeven_sl:.2f} after 0.5:1 RR ✨")

            if unrealized_pnl >= risk:
                # 🌙 Moon Dev Optimization: Tighter trail to EMA12 - 0.6x ATR for capturing more profits in swift uptrends
                trail_sl = ema12 - 0.6 * atr
                if trail_sl > current_sl:
                    self.current_sl = trail_sl
                    print(f"🌙 Moon Dev: Trailing SL updated to {trail_sl:.2f} after 1:1 RR ✨")

            # 🌙 Moon Dev Optimization: Earlier partial close at 1.5:1 RR (40% instead of 50%) to lock gains sooner, full TP at 4:1 to balance capture vs. let-run
            if not self.partial_closed and unrealized_pnl >= 1.5 * risk:
                partial_size = self.position.size * 0.4
                self.sell(size=partial_size)
                self.partial_closed = True
                print(f"🌙 Moon Dev: Partial close 40% at 1.5:1 RR, securing early profits! 🚀")

            if unrealized_pnl >= 4 * risk:
                print(f"🌙 Moon Dev: Full TP at 4:1 RR for optimized gains! 🚀")
                self.position.close()
                return

            # Bearish divergence: Enhanced with MACD check for stronger signal
            if rsi > 70 and len(self.data) > 2 and close > self.data.Close[-2] and rsi < self.rsi[-2] and macd < macd_signal and adx > 20:
                print(f"🌙 Moon Dev: Bearish RSI + MACD Divergence in overbought zone, EXITING! 🚀")
                self.position.close()
                return

            # Exit below EMA12 trail for faster response with quicker EMA
            if close < ema12:
                print(f"🌙 Moon Dev: EXITING below EMA12 trail 🚀")
                self.position.close()
                return

            # Update peak for divergence
            if high > self.last_peak_price:
                self.last_peak_price = high
                self.last_peak_rsi = rsi

            # 🌙 Moon Dev Optimization: Added time-based exit after 50 bars if RR < 0.5 to avoid stagnation in ranging conditions
            if bars_since_entry > 50 and rr < 0.5:
                print(f"🌙 Moon Dev: Time-based EXIT after 50 bars with low RR 🚀")
                self.position.close()
                return

bt = Backtest(data, GoldenCrossover, cash=1000000, commission=0.002)
stats = bt.run()
print(stats)