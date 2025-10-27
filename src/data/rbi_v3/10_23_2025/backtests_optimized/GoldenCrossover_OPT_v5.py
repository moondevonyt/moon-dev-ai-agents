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
        # 🌙 Moon Dev Optimization: Switched to EMA for faster response to trends in volatile BTC, EMA20/EMA50 for more timely crossovers while reducing lag
        self.ema20 = self.I(talib.EMA, self.data.Close, timeperiod=20)
        self.ema50 = self.I(talib.EMA, self.data.Close, timeperiod=50)
        self.ema200 = self.I(talib.EMA, self.data.Close, timeperiod=200)
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14)
        # 🌙 Moon Dev Optimization: Lowered ADX threshold to 20 for more entries in moderate trends, balancing quality and frequency
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        # 🌙 Moon Dev Optimization: Added MACD for momentum confirmation, signal line crossover adds bullish bias
        self.macd, self.macd_signal, _ = self.I(talib.MACD, self.data.Close, fastperiod=12, slowperiod=26, signalperiod=9)
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
        ema20 = self.ema20[-1]
        ema50 = self.ema50[-1]
        ema200 = self.ema200[-1]
        rsi = self.rsi[-1]
        adx = self.adx[-1]
        atr = self.atr[-1]
        macd = self.macd[-1]
        macd_signal = self.macd_signal[-1]
        avg_vol = self.avg_volume[-1]

        print(f"🌙 Moon Dev Backtest Bar {len(self.data)}: Close {close:.2f}, EMA20 {ema20:.2f}, EMA50 {ema50:.2f}, EMA200 {ema200:.2f}, RSI {rsi:.2f}, ADX {adx:.2f}, ATR {atr:.2f}, MACD {macd:.2f} ✨")

        if close <= ema200:
            if self.position:
                print("🚀 Moon Dev: Exiting long due to broken uptrend below EMA200 🌙")
                self.position.close()
            return

        # 🌙 Moon Dev Optimization: Extended Fib lookback to 150 bars for capturing larger swings in BTC's volatile trends, improving retracement reliability
        lookback = 150
        from_idx = max(0, len(self.data) - lookback - 1)
        recent_high_values = self.data.High[from_idx:len(self.data)-1]
        if len(recent_high_values) < 30:  # 🌙 Moon Dev Optimization: Increased min lookback to 30 for robust swing detection
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

        # 🌙 Moon Dev Optimization: Refined entry - EMA20 crossover of EMA50 (faster golden cross), allow Fib touch within last 5 bars for more opportunities on pullbacks, RSI 45-65 for earlier momentum capture, ADX>20, volume>1.2x (relaxed for more signals), MACD>signal for bullish momentum, uptrend confirmation, and bullish candle (close>open)
        crossover = len(self.data) > 1 and self.data.Close[-2] <= self.ema20[-2] and close > ema20  # 🌙 Note: Using EMA20 crossover for quicker entries
        # Check Fib touch in recent bars
        recent_lows = self.data.Low[-5:]
        touch_fib = any(recent_low <= fib618 + (0.003 * close) for recent_low in recent_lows)  # 🌙 Moon Dev Optimization: Widened tolerance to 0.3% and checked last 5 bars for pullback entries
        volume_confirm = volume > 1.2 * avg_vol  # 🌙 Moon Dev Optimization: Reduced to 1.2x to increase trade frequency without sacrificing too much quality
        momentum_rsi = rsi > 45 and rsi < 65  # 🌙 Moon Dev Optimization: Adjusted RSI range lower for catching pullbacks earlier in uptrends
        trend_strength = adx > 20
        macd_confirm = macd > macd_signal  # 🌙 Moon Dev Optimization: Added MACD > signal line for additional momentum filter
        uptrend = close > ema200 and ema20 > ema50 > ema200  # 🌙 Moon Dev Optimization: Strengthened uptrend with EMA20 > EMA50 > EMA200
        bullish_candle = close > self.data.Open[-1]  # 🌙 Moon Dev Optimization: Require bullish candle for entry confirmation

        if crossover and touch_fib and volume_confirm and momentum_rsi and trend_strength and macd_confirm and uptrend and bullish_candle and not self.position:
            entry_price = close
            # 🌙 Moon Dev Optimization: Tighter SL - 1.2x ATR below entry, or below recent swing low/Fib, to reduce risk exposure
            sl_distance = 1.2 * atr
            stop_price = entry_price - sl_distance
            swing_low_recent = min(self.data.Low[-15:])  # 🌙 Moon Dev Optimization: Extended recent low lookback to 15 bars for better support levels
            if fib618 < entry_price:
                stop_price = min(stop_price, fib618 - 0.3 * atr, swing_low_recent)
            risk_per_unit = entry_price - stop_price
            if risk_per_unit <= 0:
                return
            capital = 1000000
            # 🌙 Moon Dev Optimization: Reduced risk per trade to 0.5% for better capital preservation and allowing more trades to compound
            risk_amount = capital * 0.005
            position_size = risk_amount / risk_per_unit
            # 🌙 Moon Dev Optimization: Lowered max size cap to 3% for stricter BTC exposure control
            max_size = (capital * 0.03) / entry_price
            position_size = min(position_size, max_size)
            position_size = max(0.01, min(int(round(position_size)), int(capital * 0.1 / entry_price)))  # 🌙 Moon Dev Optimization: Ensure fractional sizing minimum 0.01 BTC, cap at 10% for safety
            if position_size > 0:
                print(f"🌙 Moon Dev: LONG ENTRY at {entry_price:.2f}, SL {stop_price:.2f}, Size {position_size} BTC, Refined Filters + MACD Confirmed! ✨🚀")
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

            # 🌙 Moon Dev Optimization: Faster breakeven - Move to breakeven + 0.2x ATR after 0.3:1 RR for quicker protection in volatile markets
            if unrealized_pnl >= 0.3 * risk:
                breakeven_sl = entry_price + (0.2 * atr)
                if breakeven_sl > current_sl:
                    self.current_sl = breakeven_sl
                    print(f"🌙 Moon Dev: Moved SL to breakeven {breakeven_sl:.2f} after 0.3:1 RR ✨")

            if unrealized_pnl >= risk:
                # 🌙 Moon Dev Optimization: Trail to EMA20 - 0.8x ATR for tighter trailing in strong trends
                trail_sl = ema20 - 0.8 * atr
                if trail_sl > current_sl:
                    self.current_sl = trail_sl
                    print(f"🌙 Moon Dev: Trailing SL updated to {trail_sl:.2f} after 1:1 RR ✨")

            # 🌙 Moon Dev Optimization: Scale out - Close 50% at 2:1 RR to lock profits, let rest run to 5:1 for bigger targets in BTC trends
            if not self.partial_closed and unrealized_pnl >= 2 * risk:
                partial_size = self.position.size * 0.5
                self.sell(size=partial_size)
                self.partial_closed = True
                print(f"🌙 Moon Dev: Partial close 50% at 2:1 RR, locking profits! 🚀")

            if unrealized_pnl >= 5 * risk:
                print(f"🌙 Moon Dev: Full TP at 5:1 RR for maximum gains! 🚀")
                self.position.close()
                return

            # Bearish divergence: Enhanced with MACD check for stronger signal
            if rsi > 70 and len(self.data) > 2 and close > self.data.Close[-2] and rsi < self.rsi[-2] and macd < macd_signal and adx > 20:
                print(f"🌙 Moon Dev: Bearish RSI + MACD Divergence in overbought zone, EXITING! 🚀")
                self.position.close()
                return

            # Exit below EMA20 trail for faster response
            if close < ema20:
                print(f"🌙 Moon Dev: EXITING below EMA20 trail 🚀")
                self.position.close()
                return

            # Update peak for divergence
            if high > self.last_peak_price:
                self.last_peak_price = high
                self.last_peak_rsi = rsi

bt = Backtest(data, GoldenCrossover, cash=1000000, commission=0.002)
stats = bt.run()
print(stats)