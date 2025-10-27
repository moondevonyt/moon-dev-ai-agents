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
        # 🌙 Moon Dev Optimization: Retained EMA setup but added a longer-term filter with EMA100 for better trend confirmation, reducing false signals in choppy conditions
        self.ema20 = self.I(talib.EMA, self.data.Close, timeperiod=20)
        self.ema50 = self.I(talib.EMA, self.data.Close, timeperiod=50)
        self.ema100 = self.I(talib.EMA, self.data.Close, timeperiod=100)  # 🌙 New: EMA100 for intermediate trend filter
        self.ema200 = self.I(talib.EMA, self.data.Close, timeperiod=200)
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14)
        # 🌙 Moon Dev Optimization: Increased ADX threshold to 25 to focus on stronger trends, improving entry quality and reducing whipsaws for higher win rate
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        # 🌙 Moon Dev Optimization: Fine-tuned MACD to faster periods (8,17,6) for quicker momentum detection in 15m BTC, enhancing confirmation without lag
        self.macd, self.macd_signal, _ = self.I(talib.MACD, self.data.Close, fastperiod=8, slowperiod=17, signalperiod=6)
        self.avg_volume = self.I(talib.SMA, self.data.Volume, timeperiod=10)
        # 🌙 Moon Dev Optimization: Added average ATR filter to avoid low-volatility periods where trends are weak
        self.avg_atr = self.I(talib.SMA, self.atr, timeperiod=20)
        self.last_peak_price = 0.0
        self.last_peak_rsi = 100.0
        self.entry_bar = 0
        self.entry_price = None
        self.current_sl = None
        # 🌙 Moon Dev Optimization: Track partial profit levels for scaling out, added second partial for better profit locking
        self.partial_closed = False
        self.second_partial = False

    def next(self):
        if len(self.data) < 200:
            return

        close = self.data.Close[-1]
        low = self.data.Low[-1]
        high = self.data.High[-1]
        volume = self.data.Volume[-1]
        ema20 = self.ema20[-1]
        ema50 = self.ema50[-1]
        ema100 = self.ema100[-1]
        ema200 = self.ema200[-1]
        rsi = self.rsi[-1]
        adx = self.adx[-1]
        atr = self.atr[-1]
        macd = self.macd[-1]
        macd_signal = self.macd_signal[-1]
        avg_vol = self.avg_volume[-1]
        avg_atr_val = self.avg_atr[-1]

        print(f"🌙 Moon Dev Backtest Bar {len(self.data)}: Close {close:.2f}, EMA20 {ema20:.2f}, EMA50 {ema50:.2f}, EMA200 {ema200:.2f}, RSI {rsi:.2f}, ADX {adx:.2f}, ATR {atr:.2f}, MACD {macd:.2f} ✨")

        if close <= ema200:
            if self.position:
                print("🚀 Moon Dev: Exiting long due to broken uptrend below EMA200 🌙")
                self.position.close()
            return

        # 🌙 Moon Dev Optimization: Reduced Fib lookback to 100 bars for more relevant recent swings in fast-moving BTC 15m, with min 50 bars for stability
        lookback = 100
        from_idx = max(0, len(self.data) - lookback - 1)
        recent_high_values = self.data.High[from_idx:len(self.data)-1]
        if len(recent_high_values) < 50:
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

        # 🌙 Moon Dev Optimization: Fixed entry to true Golden Cross (EMA20 crosses above EMA50) for better trend capture; tightened Fib touch to last 3 bars with 0.2% tolerance for precise pullback entries; RSI 50-70 for stronger uptrend momentum; ADX>25; volume>1.5x for quality confirmation; MACD histogram positive for building momentum; added EMA100 alignment and volatility filter (ATR > avg ATR); require larger bullish candle (close > open + 0.1% close)
        crossover = len(self.data) > 1 and self.ema20[-2] <= self.ema50[-2] and ema20 > ema50  # 🌙 Fixed: Actual EMA20/50 golden cross for timely trend starts
        # Check Fib touch in recent bars
        recent_lows = self.data.Low[-3:]  # 🌙 Tightened to last 3 bars for fresher pullbacks
        touch_fib = any(recent_low <= fib618 + (0.002 * close) for recent_low in recent_lows)  # 🌙 Reduced tolerance to 0.2% for stricter Fib bounce
        volume_confirm = volume > 1.5 * avg_vol  # 🌙 Increased to 1.5x for higher quality volume spikes, reducing noise entries
        momentum_rsi = rsi > 50 and rsi < 70  # 🌙 Adjusted RSI to 50-70 to capture building strength in uptrends, avoiding early exhaustion
        trend_strength = adx > 25  # 🌙 Raised to 25 for stronger trend filter, improving signal quality
        macd_hist = macd - macd_signal > 0  # 🌙 Changed to positive MACD histogram for accelerating bullish momentum
        uptrend = close > ema200 and ema20 > ema50 > ema100 > ema200  # 🌙 Added EMA100 to uptrend for multi-EMA confirmation, ensuring robust bull bias
        volatility_filter = atr > avg_atr_val  # 🌙 New: Only enter in higher volatility regimes for trend-following edge
        bullish_candle = close > self.data.Open[-1] + (0.001 * close)  # 🌙 Strengthened to > open + 0.1% for decisive bullish action

        if crossover and touch_fib and volume_confirm and momentum_rsi and trend_strength and macd_hist and uptrend and volatility_filter and bullish_candle and not self.position:
            entry_price = close
            # 🌙 Moon Dev Optimization: Tighter SL - 1.0x ATR below entry (reduced from 1.2x) or below Fib/swing low, with 10-bar recent low for better structure-based stops
            sl_distance = 1.0 * atr  # 🌙 Reduced multiplier for tighter risk control, allowing higher RR potential
            stop_price = entry_price - sl_distance
            swing_low_recent = min(self.data.Low[-10:])  # 🌙 Reduced lookback to 10 bars for more relevant support
            if fib618 < entry_price:
                stop_price = min(stop_price, fib618 - 0.2 * atr, swing_low_recent)  # 🌙 Tighter buffer below Fib
            risk_per_unit = entry_price - stop_price
            if risk_per_unit <= 0:
                return
            capital = 1000000
            # 🌙 Moon Dev Optimization: Increased risk per trade to 1% for more aggressive compounding towards 50% target, balanced by tighter filters
            risk_amount = capital * 0.01
            position_size = risk_amount / risk_per_unit
            # 🌙 Moon Dev Optimization: Raised max size to 5% for larger exposure in high-conviction setups
            max_size = (capital * 0.05) / entry_price
            position_size = min(position_size, max_size)
            position_size = max(0.01, min(int(round(position_size)), int(capital * 0.15 / entry_price)))  # 🌙 Increased cap to 15% for BTC leverage potential, min 0.01
            if position_size > 0:
                print(f"🌙 Moon Dev: LONG ENTRY at {entry_price:.2f}, SL {stop_price:.2f}, Size {position_size} BTC, True Golden Cross + Enhanced Filters! ✨🚀")
                self.buy(size=position_size)
                self.entry_price = entry_price
                self.current_sl = stop_price
                self.entry_bar = len(self.data) - 1
                self.last_peak_price = high
                self.last_peak_rsi = rsi
                self.partial_closed = False
                self.second_partial = False

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

            # 🌙 Moon Dev Optimization: Moved breakeven trigger to 0.5:1 RR (from 0.3:1) for better protection after confirmed profits, +0.3x ATR buffer
            if unrealized_pnl >= 0.5 * risk:
                breakeven_sl = entry_price + (0.3 * atr)  # 🌙 Increased buffer slightly for volatility cushion
                if breakeven_sl > current_sl:
                    self.current_sl = breakeven_sl
                    print(f"🌙 Moon Dev: Moved SL to breakeven {breakeven_sl:.2f} after 0.5:1 RR ✨")

            if unrealized_pnl >= risk:
                # 🌙 Moon Dev Optimization: Tighter trail to EMA50 - 0.5x ATR (changed from EMA20/0.8x) for earlier profit securing in volatile swings
                trail_sl = ema50 - 0.5 * atr  # 🌙 Switched to EMA50 for more conservative trailing, reduced multiplier
                if trail_sl > current_sl:
                    self.current_sl = trail_sl
                    print(f"🌙 Moon Dev: Trailing SL updated to {trail_sl:.2f} after 1:1 RR ✨")

            # 🌙 Moon Dev Optimization: Adjusted scaling - 30% at 1.5:1 (earlier than 2:1), 30% more at 3:1, let 40% run to 4:1 TP for balanced profit taking and higher RR hits
            if not self.partial_closed and unrealized_pnl >= 1.5 * risk:
                partial_size = self.position.size * 0.3
                self.sell(size=partial_size)
                self.partial_closed = True
                print(f"🌙 Moon Dev: Partial close 30% at 1.5:1 RR, early profit lock! 🚀")

            if self.partial_closed and not self.second_partial and unrealized_pnl >= 3 * risk:
                partial_size = self.position.size * 0.5  # 50% of remaining
                self.sell(size=partial_size)
                self.second_partial = True
                print(f"🌙 Moon Dev: Second partial 30% at 3:1 RR, scaling out! 🚀")

            if unrealized_pnl >= 4 * risk:  # 🌙 Reduced full TP from 5:1 to 4:1 for more frequent larger wins, realistic for BTC trends
                print(f"🌙 Moon Dev: Full TP at 4:1 RR for optimized gains! 🚀")
                self.position.close()
                return

            # Bearish divergence: Tightened with RSI>65 (from 70), added volume fade check, and stricter MACD for reliable tops
            if rsi > 65 and len(self.data) > 2 and close > self.data.Close[-2] and rsi < self.rsi[-2] and macd < macd_signal and volume < avg_vol and adx > 25:
                print(f"🌙 Moon Dev: Enhanced Bearish RSI/MACD/Volume Divergence, EXITING! 🚀")
                self.position.close()
                return

            # Exit below EMA50 (from EMA20) for earlier trend break detection, reducing drawdowns
            if close < ema50:  # 🌙 Changed to EMA50 for proactive exits on trend weakness
                print(f"🌙 Moon Dev: EXITING below EMA50 trend break 🚀")
                self.position.close()
                return

            # 🌙 Moon Dev Optimization: New exit if ADX weakens below 20 after entry, to avoid fading trends
            if adx < 20 and bars_since_entry > 10:
                print(f"🌙 Moon Dev: EXITING due to weakening ADX <20 🚀")
                self.position.close()
                return

            # Update peak for divergence
            if high > self.last_peak_price:
                self.last_peak_price = high
                self.last_peak_rsi = rsi

bt = Backtest(data, GoldenCrossover, cash=1000000, commission=0.002)
stats = bt.run()
print(stats)