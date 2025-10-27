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
        # 🌙 Moon Dev Optimization: Retained EMA periods but ensured they align with BTC volatility; added a longer-term EMA for regime filter
        self.ema20 = self.I(talib.EMA, self.data.Close, timeperiod=20)
        self.ema50 = self.I(talib.EMA, self.data.Close, timeperiod=50)
        self.ema200 = self.I(talib.EMA, self.data.Close, timeperiod=200)
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14)
        # 🌙 Moon Dev Optimization: Increased ADX threshold slightly to 25 to filter for stronger trends, reducing whipsaws in BTC's choppy periods
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        # 🌙 Moon Dev Optimization: Adjusted MACD to faster periods (8,17,9) for quicker momentum signals in 15m BTC, improving entry timing
        self.macd, self.macd_signal, _ = self.I(talib.MACD, self.data.Close, fastperiod=8, slowperiod=17, signalperiod=9)
        self.avg_volume = self.I(talib.SMA, self.data.Volume, timeperiod=10)
        self.last_peak_price = 0.0
        self.last_peak_rsi = 100.0
        self.entry_bar = 0
        self.entry_price = None
        self.current_sl = None
        # 🌙 Moon Dev Optimization: Enhanced scaling with multiple levels tracking for better profit locking
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

        print(f"🌙 Moon Dev Backtest Bar {len(self.data)}: Close {close:.2f}, EMA20 {ema20:.2f}, EMA50 {ema50:.2f}, EMA200 {ema200:.2f}, RSI {rsi:.2f}, ADX {adx:.2f}, ATR {atr:.2f}, MACD {macd:.2f} ✨")

        if close <= ema200:
            if self.position:
                print("🚀 Moon Dev: Exiting long due to broken uptrend below EMA200 🌙")
                self.position.close()
            return

        # 🌙 Moon Dev Optimization: Reduced Fib lookback to 100 bars for more frequent swing detection in shorter-term BTC pullbacks, improving entry opportunities
        lookback = 100
        from_idx = max(0, len(self.data) - lookback - 1)
        recent_high_values = self.data.High[from_idx:len(self.data)-1]
        if len(recent_high_values) < 20:  # 🌙 Moon Dev Optimization: Reduced min lookback to 20 bars for faster adaptation to recent swings
            return
        rel_high_idx = np.argmax(recent_high_values)
        abs_high_idx = from_idx + rel_high_idx
        swing_high = self.data.High[abs_high_idx]

        low_values_to_high = self.data.Low[from_idx:abs_high_idx + 1]
        rel_low_idx = np.argmin(low_values_to_high)
        abs_low_idx = from_idx + rel_low_idx
        swing_low = self.data.Low[abs_low_idx]

        # 🌙 Moon Dev Optimization: Adjusted to 50% Fib level for shallower pullbacks, capturing higher probability entries in strong uptrends
        fib_level = 0.5
        fib618 = swing_high - fib_level * (swing_high - swing_low)
        print(f"🌙 Moon Dev Fib Calc: {fib_level*100}% Level {fib618:.2f}, High {swing_high:.2f}, Low {swing_low:.2f} 🚀")

        # 🌙 Moon Dev Optimization: Fixed to true Golden Cross (EMA20 > EMA50 crossover) for reliable trend signals; extended Fib touch to last 10 bars with 0.5% tolerance for more pullback entries; widened RSI to 40-70 to catch broader momentum; ADX>25 for quality; volume>1.0x avg to allow normal volume entries; MACD histogram positive for momentum; strict uptrend; added open < close for bullish candle
        crossover = len(self.data) > 1 and self.ema20[-2] <= self.ema50[-2] and ema20 > ema50  # 🌙 Moon Dev Optimization: Changed to actual EMA20/EMA50 crossover for classic Golden Cross, reducing false signals from price-only crosses
        # Check Fib touch in recent bars
        recent_lows = self.data.Low[-10:]  # 🌙 Moon Dev Optimization: Extended to 10 bars for capturing recent pullbacks more effectively
        touch_fib = any(recent_low <= fib618 + (0.005 * close) for recent_low in recent_lows)  # 🌙 Moon Dev Optimization: Increased tolerance to 0.5% to account for BTC volatility, allowing near-touches
        volume_confirm = volume > 1.0 * avg_vol  # 🌙 Moon Dev Optimization: Reduced threshold to 1.0x to increase trade frequency in varying volume conditions
        momentum_rsi = rsi > 40 and rsi < 70  # 🌙 Moon Dev Optimization: Widened RSI range to include more neutral momentum, enabling entries on dips without overbought restriction
        trend_strength = adx > 25  # 🌙 Moon Dev Optimization: Raised to 25 for stronger trend filter, avoiding weak markets
        macd_confirm = macd > macd_signal and (macd - macd_signal) > 0  # 🌙 Moon Dev Optimization: Added positive histogram for accelerating momentum confirmation
        uptrend = close > ema200 and ema20 > ema50 > ema200  # Retained strengthened uptrend filter
        bullish_candle = close > self.data.Open[-1]  # Retained bullish candle confirmation

        if crossover and touch_fib and volume_confirm and momentum_rsi and trend_strength and macd_confirm and uptrend and bullish_candle and not self.position:
            entry_price = close
            # 🌙 Moon Dev Optimization: Widened initial SL to 1.5x ATR for breathing room in volatile BTC, but cap below swing low/Fib to maintain support-based stops
            sl_distance = 1.5 * atr
            stop_price = entry_price - sl_distance
            swing_low_recent = min(self.data.Low[-20:])  # 🌙 Moon Dev Optimization: Increased recent low lookback to 20 bars for more conservative support
            if fib618 < entry_price:
                stop_price = min(stop_price, fib618 - 0.5 * atr, swing_low_recent)
            risk_per_unit = entry_price - stop_price
            if risk_per_unit <= 0:
                return
            capital = 1000000
            # 🌙 Moon Dev Optimization: Increased risk per trade to 1% to amplify returns towards 50% target while still managing drawdowns
            risk_amount = capital * 0.01
            position_size = risk_amount / risk_per_unit
            # 🌙 Moon Dev Optimization: Raised max exposure to 5% for larger positions in high-conviction setups, balanced with risk sizing
            max_size = (capital * 0.05) / entry_price
            position_size = min(position_size, max_size)
            position_size = max(0.01, min(int(round(position_size)), int(capital * 0.15 / entry_price)))  # 🌙 Moon Dev Optimization: Increased cap to 15% for aggressive compounding in bull runs
            if position_size > 0:
                print(f"🌙 Moon Dev: LONG ENTRY at {entry_price:.2f}, SL {stop_price:.2f}, Size {position_size} BTC, True Golden Cross + Enhanced Filters! ✨🚀")
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

            # 🌙 Moon Dev Optimization: Adjusted breakeven trigger to 0.5:1 RR with +0.3x ATR buffer for better protection without premature exits
            if unrealized_pnl >= 0.5 * risk:
                breakeven_sl = entry_price + (0.3 * atr)
                if breakeven_sl > current_sl:
                    self.current_sl = breakeven_sl
                    print(f"🌙 Moon Dev: Moved SL to breakeven {breakeven_sl:.2f} after 0.5:1 RR ✨")

            if unrealized_pnl >= risk:
                # 🌙 Moon Dev Optimization: Improved trailing to EMA50 - 1.0x ATR for looser trail, allowing more room in trending BTC moves
                trail_sl = ema50 - 1.0 * atr
                if trail_sl > current_sl:
                    self.current_sl = trail_sl
                    print(f"🌙 Moon Dev: Trailing SL updated to {trail_sl:.2f} after 1:1 RR ✨")

            # 🌙 Moon Dev Optimization: Multi-stage scaling - 30% at 1.5:1, 30% at 3:1 to lock incremental profits, let 40% run to higher RR for target amplification
            remaining_size = self.position.size
            if not self.partial_closed_1 and unrealized_pnl >= 1.5 * risk:
                partial_size_1 = remaining_size * 0.3
                self.sell(size=partial_size_1)
                self.partial_closed_1 = True
                print(f"🌙 Moon Dev: Partial close 30% at 1.5:1 RR, securing early gains! 🚀")
            if not self.partial_closed_2 and unrealized_pnl >= 3 * risk:
                partial_size_2 = remaining_size * 0.3
                self.sell(size=partial_size_2)
                self.partial_closed_2 = True
                print(f"🌙 Moon Dev: Partial close 30% at 3:1 RR, building profits! 🚀")

            if unrealized_pnl >= 8 * risk:
                print(f"🌙 Moon Dev: Full TP at 8:1 RR for outsized BTC trend gains! 🚀")
                self.position.close()
                return

            # Bearish divergence: Retained with MACD for confirmation
            if rsi > 70 and len(self.data) > 2 and close > self.data.Close[-2] and rsi < self.rsi[-2] and macd < macd_signal and adx > 25:
                print(f"🌙 Moon Dev: Bearish RSI + MACD Divergence in overbought zone, EXITING! 🚀")
                self.position.close()
                return

            # 🌙 Moon Dev Optimization: Changed exit to below EMA50 for longer holds in minor pullbacks, reducing premature exits
            if close < ema50:
                print(f"🌙 Moon Dev: EXITING below EMA50 trend line 🚀")
                self.position.close()
                return

            # Update peak for divergence
            if high > self.last_peak_price:
                self.last_peak_price = high
                self.last_peak_rsi = rsi

bt = Backtest(data, GoldenCrossover, cash=1000000, commission=0.002)
stats = bt.run()
print(stats)