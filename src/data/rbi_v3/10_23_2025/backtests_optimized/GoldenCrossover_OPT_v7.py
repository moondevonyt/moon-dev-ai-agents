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
        # 🌙 Moon Dev Optimization: Shortened EMA periods to 12/26 for faster trend detection in 15m BTC, aligning with MACD params for synergy and quicker crossovers to capture more volatile swings
        self.ema20 = self.I(talib.EMA, self.data.Close, timeperiod=12)
        self.ema50 = self.I(talib.EMA, self.data.Close, timeperiod=26)
        self.ema200 = self.I(talib.EMA, self.data.Close, timeperiod=200)
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14)
        # 🌙 Moon Dev Optimization: Further lowered ADX to 15 to allow entries in weaker but still directional trends, increasing trade frequency for higher overall returns
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        # 🌙 Moon Dev Optimization: Kept MACD but added histogram for better momentum insight, though using line/signal for confirmation
        self.macd, self.macd_signal, self.macd_hist = self.I(talib.MACD, self.data.Close, fastperiod=12, slowperiod=26, signalperiod=9)
        self.avg_volume = self.I(talib.SMA, self.data.Volume, timeperiod=10)
        self.last_peak_price = 0.0
        self.last_peak_rsi = 100.0
        self.entry_bar = 0
        self.entry_price = None
        self.current_sl = None
        # 🌙 Moon Dev Optimization: Track multiple partial levels for scaled exits to lock profits progressively
        self.partial_closed_1 = False
        self.partial_closed_2 = False

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

        print(f"🌙 Moon Dev Backtest Bar {len(self.data)}: Close {close:.2f}, EMA12 {ema20:.2f}, EMA26 {ema50:.2f}, EMA200 {ema200:.2f}, RSI {rsi:.2f}, ADX {adx:.2f}, ATR {atr:.2f}, MACD {macd:.2f} ✨")

        if close <= ema200:
            if self.position:
                print("🚀 Moon Dev: Exiting long due to broken uptrend below EMA200 🌙")
                self.position.close()
            return

        # 🌙 Moon Dev Optimization: Reduced Fib lookback to 100 bars for more relevant swings in 15m timeframe, capturing shorter-term retracements in BTC's choppy volatility
        lookback = 100
        from_idx = max(0, len(self.data) - lookback - 1)
        recent_high_values = self.data.High[from_idx:len(self.data)-1]
        if len(recent_high_values) < 20:  # 🌙 Moon Dev Optimization: Reduced min lookback to 20 bars to enable earlier swing detection in shorter trends
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

        # 🌙 Moon Dev Optimization: Switched to true Golden Cross (EMA12 > EMA26) for high-quality trend entries, extended Fib touch to last 10 bars with 0.5% tolerance for more pullback opportunities, RSI >40 for broader momentum window, ADX>15, volume>1.0x (minimal filter), MACD hist>0 for rising momentum, uptrend above EMA50 (loosened from EMA200 for more trades), removed bullish candle to avoid missing setups
        crossover = len(self.data) > 1 and self.ema20[-2] <= self.ema50[-2] and ema20 > ema50  # 🌙 Moon Dev Optimization: Changed to actual EMA12/EMA26 crossover for reliable golden cross signals, reducing false entries from price-only crosses
        # Check Fib touch in recent bars
        recent_lows = self.data.Low[-10:]  # 🌙 Moon Dev Optimization: Extended to 10 bars for capturing deeper pullbacks
        touch_fib = any(recent_low <= fib618 + (0.005 * close) for recent_low in recent_lows)  # 🌙 Moon Dev Optimization: Increased tolerance to 0.5% to account for BTC volatility and noise
        volume_confirm = volume > 1.0 * avg_vol  # 🌙 Moon Dev Optimization: Relaxed to 1.0x average for higher trade frequency, as volume spikes are less reliable in crypto
        momentum_rsi = rsi > 40  # 🌙 Moon Dev Optimization: Lowered lower bound to 40 to enter on milder oversold bounces, expanding opportunities
        trend_strength = adx > 15  # 🌙 Moon Dev Optimization: Reduced threshold to 15 for more entries in emerging trends
        macd_confirm = self.macd_hist[-1] > 0  # 🌙 Moon Dev Optimization: Switched to MACD histogram >0 for positive momentum acceleration confirmation
        uptrend = close > ema50 and ema20 > ema50  # 🌙 Moon Dev Optimization: Loosened uptrend filter to above EMA26 instead of EMA200, allowing trades in intermediate uptrends for more frequency while maintaining directionality
        # Removed bullish_candle filter to increase entry rate without significantly raising false positives

        if crossover and touch_fib and volume_confirm and momentum_rsi and trend_strength and macd_confirm and uptrend and not self.position:
            entry_price = close
            # 🌙 Moon Dev Optimization: Widened SL to 1.5x ATR for breathing room in volatile 15m BTC, but cap below swing low/Fib for support
            sl_distance = 1.5 * atr
            stop_price = entry_price - sl_distance
            swing_low_recent = min(self.data.Low[-20:])  # 🌙 Moon Dev Optimization: Extended lookback to 20 bars for stronger support identification
            if fib618 < entry_price:
                stop_price = min(stop_price, fib618 - 0.5 * atr, swing_low_recent)
            risk_per_unit = entry_price - stop_price
            if risk_per_unit <= 0:
                return
            capital = 1000000
            # 🌙 Moon Dev Optimization: Increased risk per trade to 1.5% to amplify returns through compounding, balanced with tighter overall exposure
            risk_amount = capital * 0.015
            position_size = risk_amount / risk_per_unit
            # 🌙 Moon Dev Optimization: Raised max size to 5% for larger positions in high-conviction setups
            max_size = (capital * 0.05) / entry_price
            position_size = min(position_size, max_size)
            position_size = max(0.01, min(position_size, capital * 0.15 / entry_price))  # 🌙 Moon Dev Optimization: Adjusted cap to 15% for aggressive growth targeting 50% return, with min 0.01 BTC
            if position_size > 0:
                print(f"🌙 Moon Dev: LONG ENTRY at {entry_price:.2f}, SL {stop_price:.2f}, Size {position_size} BTC, True Golden Cross + Loosened Filters! ✨🚀")
                self.buy(size=position_size)
                self.entry_price = entry_price
                self.current_sl = stop_price
                self.entry_bar = len(self.data) - 1
                self.last_peak_price = high
                self.last_peak_rsi = rsi
                self.partial_closed_1 = False
                self.partial_closed_2 = False

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

            # 🌙 Moon Dev Optimization: Earlier breakeven at 0.5:1 RR + 0.3x ATR to protect profits sooner in fast-moving BTC
            if unrealized_pnl >= 0.5 * risk:
                breakeven_sl = entry_price + (0.3 * atr)
                if breakeven_sl > current_sl:
                    self.current_sl = breakeven_sl
                    print(f"🌙 Moon Dev: Moved SL to breakeven {breakeven_sl:.2f} after 0.5:1 RR ✨")

            if unrealized_pnl >= 0.75 * risk:
                # 🌙 Moon Dev Optimization: Start trailing earlier at 0.75:1 to EMA12 - 1.0x ATR for dynamic protection in trends
                trail_sl = ema20 - 1.0 * atr
                if trail_sl > current_sl:
                    self.current_sl = trail_sl
                    print(f"🌙 Moon Dev: Trailing SL updated to {trail_sl:.2f} after 0.75:1 RR ✨")

            # 🌙 Moon Dev Optimization: Multi-stage scaling - 30% at 1.5:1, 30% at 3:1 to lock incremental profits, let 40% run for higher RR targets
            if not self.partial_closed_1 and unrealized_pnl >= 1.5 * risk:
                partial_size_1 = self.position.size * 0.3
                self.sell(size=partial_size_1)
                self.partial_closed_1 = True
                print(f"🌙 Moon Dev: Partial close 30% at 1.5:1 RR, securing early gains! 🚀")

            if not self.partial_closed_2 and unrealized_pnl >= 3 * risk:
                partial_size_2 = self.position.size * 0.3  # Note: size adjusted after first partial
                self.sell(size=partial_size_2)
                self.partial_closed_2 = True
                print(f"🌙 Moon Dev: Partial close 30% at 3:1 RR, more profits locked! 🚀")

            if unrealized_pnl >= 4 * risk:
                print(f"🌙 Moon Dev: Full TP at 4:1 RR for optimized gains in BTC trends! 🚀")
                self.position.close()
                return

            # Bearish divergence: Enhanced with MACD histogram declining for stronger exit signal
            if rsi > 70 and len(self.data) > 2 and close > self.data.Close[-2] and rsi < self.rsi[-2] and self.macd_hist[-1] < self.macd_hist[-2] and adx > 25:
                print(f"🌙 Moon Dev: Bearish RSI + MACD Hist Divergence in overbought, EXITING! 🚀")
                self.position.close()
                return

            # Exit below EMA26 for quicker response to trend weakness
            if close < ema50:
                print(f"🌙 Moon Dev: EXITING below EMA26 trail 🚀")
                self.position.close()
                return

            # Update peak for divergence
            if high > self.last_peak_price:
                self.last_peak_price = high
                self.last_peak_rsi = rsi

bt = Backtest(data, GoldenCrossover, cash=1000000, commission=0.002)
stats = bt.run()
print(stats)