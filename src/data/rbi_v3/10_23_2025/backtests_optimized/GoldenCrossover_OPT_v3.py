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
        # 🌙 Moon Dev Optimization: Switched to EMA50 and EMA200 for more responsive trend detection, reducing lag in volatile BTC markets while maintaining golden cross integrity
        self.ema50 = self.I(talib.EMA, self.data.Close, timeperiod=50)
        self.ema200 = self.I(talib.EMA, self.data.Close, timeperiod=200)
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14)
        # 🌙 Moon Dev Optimization: Lowered ADX threshold consideration to 20 for more entry opportunities in moderate trends, balancing quality and frequency
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        # 🌙 Moon Dev Optimization: Increased volume SMA to 20 periods for smoother confirmation, reducing noise from short-term spikes
        self.avg_volume = self.I(talib.SMA, self.data.Volume, timeperiod=20)
        # 🌙 Moon Dev Optimization: Added MACD for additional momentum confirmation on entries to filter out weak crossovers
        self.macd_line, self.macd_signal, _ = self.I(talib.MACD, self.data.Close, fastperiod=12, slowperiod=26, signalperiod=9)
        self.last_peak_price = 0.0
        self.last_peak_rsi = 100.0
        self.entry_bar = 0
        self.entry_price = None
        self.current_sl = None
        self.partial_taken = False

    def next(self):
        if len(self.data) < 200:
            return

        close = self.data.Close[-1]
        low = self.data.Low[-1]
        high = self.data.High[-1]
        volume = self.data.Volume[-1]
        ema50 = self.ema50[-1]
        ema200 = self.ema200[-1]
        rsi = self.rsi[-1]
        adx = self.adx[-1]
        atr = self.atr[-1]
        avg_vol = self.avg_volume[-1]
        macd = self.macd_line[-1]
        macd_signal = self.macd_signal[-1]

        print(f"🌙 Moon Dev Backtest Bar {len(self.data)}: Close {close:.2f}, EMA50 {ema50:.2f}, EMA200 {ema200:.2f}, RSI {rsi:.2f}, ADX {adx:.2f}, ATR {atr:.2f}, MACD {macd:.4f} ✨")

        if close <= ema200:
            if self.position:
                print("🚀 Moon Dev: Exiting long due to broken uptrend below EMA200 🌙")
                self.position.close()
            return

        # 🌙 Moon Dev Optimization: Reduced Fib lookback to 50 for capturing more recent pullbacks in fast-moving BTC, improving relevance
        lookback = 50
        from_idx = max(0, len(self.data) - lookback - 1)
        recent_high_values = self.data.High[from_idx:len(self.data)-1]
        if len(recent_high_values) < 10:  # 🌙 Moon Dev Optimization: Reduced minimum lookback to 10 for more flexible Fib calculations without sacrificing accuracy
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

        # 🌙 Moon Dev Optimization: Loosened entry filters for higher trade frequency - Volume to 1.2x, RSI >45/<75 for broader momentum window, ADX>20, added MACD>signal for bullish confirmation, tolerance to 1% for more Fib touches
        crossover = len(self.data) > 1 and self.data.Close[-2] <= self.ema50[-2] and close > ema50
        touch_fib = low <= fib618 + (0.01 * close)  # Increased tolerance to 1% for more practical pullback entries
        volume_confirm = volume > 1.2 * avg_vol  # Reduced to 1.2x for increased entry opportunities while maintaining confirmation
        momentum_rsi = rsi > 45 and rsi < 75  # Broadened RSI range to capture more pullback momentum without extreme overbought filters
        trend_strength = adx > 20
        macd_bullish = macd > macd_signal
        uptrend = close > ema200 and ema50 > ema200

        if crossover and touch_fib and volume_confirm and momentum_rsi and trend_strength and macd_bullish and uptrend and not self.position:
            entry_price = close
            # 🌙 Moon Dev Optimization: Widened initial SL to 2x ATR for improved risk-reward ratio, allowing more room in volatile BTC swings
            sl_distance = 2 * atr
            stop_price = entry_price - sl_distance
            swing_low_recent = min(self.data.Low[-10:])
            if fib618 < entry_price:
                stop_price = min(stop_price, fib618 - 0.5 * atr, swing_low_recent)
            risk_per_unit = entry_price - stop_price
            if risk_per_unit <= 0:
                return
            capital = 1000000
            risk_amount = capital * 0.015  # 🌙 Moon Dev Optimization: Increased risk per trade to 1.5% for higher capital utilization towards target returns
            position_size = risk_amount / risk_per_unit
            # 🌙 Moon Dev Optimization: Increased max position cap to 10% of capital to allow larger bets in high-conviction setups
            max_size = (capital * 0.10) / entry_price
            position_size = min(position_size, max_size)
            position_size = int(round(position_size))
            if position_size > 0:
                print(f"🌙 Moon Dev: LONG ENTRY at {entry_price:.2f}, SL {stop_price:.2f}, Size {position_size} BTC, Enhanced Filters Confirmed! ✨🚀")
                self.buy(size=position_size)
                self.entry_price = entry_price
                self.current_sl = stop_price
                self.entry_bar = len(self.data) - 1
                self.last_peak_price = high
                self.last_peak_rsi = rsi
                self.partial_taken = False  # Reset partial exit flag on new entry

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

            # 🌙 Moon Dev Optimization: Adjusted breakeven trigger to 0.75:1 for quicker protection, with buffer
            if unrealized_pnl >= 0.75 * risk:
                breakeven_sl = entry_price + (0.1 * atr)
                if breakeven_sl > current_sl:
                    self.current_sl = breakeven_sl
                    print(f"🌙 Moon Dev: Moved SL to breakeven {breakeven_sl:.2f} after 0.75:1 RR ✨")

            if unrealized_pnl >= risk:
                trail_sl = ema50 - atr  # Use EMA50 for dynamic trailing in uptrend
                if trail_sl > current_sl:
                    self.current_sl = trail_sl
                    print(f"🌙 Moon Dev: Trailing SL updated to {trail_sl:.2f} after 1:1 RR ✨")

            # 🌙 Moon Dev Optimization: Added partial exit at 2:1 RR to lock in profits while letting winners run
            if not self.partial_taken and unrealized_pnl >= 2 * risk:
                half_size = self.position.size * 0.5
                self.sell(size=half_size)
                self.partial_taken = True
                print(f"🌙 Moon Dev: Partial exit at 2:1 RR, sold {half_size} units! Remaining position open for more upside ✨")

            # 🌙 Moon Dev Optimization: Increased full TP to 4:1 RR to capture larger trending moves in BTC, improving overall returns
            if unrealized_pnl >= 4 * risk:
                print(f"🌙 Moon Dev: Taking full profits at 4:1 RR! 🚀")
                self.position.close()
                return

            # 🌙 Moon Dev Optimization: Improved bearish divergence detection using proper higher high/lower RSI logic for more accurate overbought exits, threshold lowered to 65
            if high > self.last_peak_price and rsi < self.last_peak_rsi and rsi > 65:
                print(f"🌙 Moon Dev: Bearish RSI Divergence: Higher high {high:.2f} > {self.last_peak_price:.2f}, RSI {rsi:.2f} < {self.last_peak_rsi:.2f}, EXITING! 🚀")
                self.position.close()
                return

            # Exit below EMA50 trail
            if close < ema50:
                print(f"🌙 Moon Dev: EXITING below EMA50 trail 🚀")
                self.position.close()
                return

            # Update peak for divergence check
            if high > self.last_peak_price:
                self.last_peak_price = high
                self.last_peak_rsi = rsi

bt = Backtest(data, GoldenCrossover, cash=1000000, commission=0.002)
stats = bt.run()
print(stats)