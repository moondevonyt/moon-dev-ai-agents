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
        # 🌙 Moon Dev Optimization: Shortened SMAs to 20/100 for 15m BTC to capture more intraday trends and increase trade frequency without excessive noise
        self.sma20 = self.I(talib.SMA, self.data.Close, timeperiod=20)
        self.sma100 = self.I(talib.SMA, self.data.Close, timeperiod=100)
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14)
        # 🌙 Moon Dev Optimization: Lowered ADX threshold to >20 to allow more entries in moderately trending markets, balancing frequency and quality
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        # 🌙 Moon Dev Optimization: Kept volume SMA at 10 but will loosen multiplier in entry for more confirmations
        self.avg_volume = self.I(talib.SMA, self.data.Volume, timeperiod=10)
        self.last_peak_price = 0.0
        self.last_peak_rsi = 100.0
        self.entry_bar = 0
        self.entry_price = None
        self.current_sl = None
        self.partial_taken = False  # 🌙 Moon Dev Optimization: Track for partial exits to scale out profits

    def next(self):
        if len(self.data) < 100:  # 🌙 Moon Dev Optimization: Reduced min bars to match shorter SMA100
            return

        close = self.data.Close[-1]
        low = self.data.Low[-1]
        high = self.data.High[-1]
        volume = self.data.Volume[-1]
        sma20 = self.sma20[-1]
        sma100 = self.sma100[-1]
        rsi = self.rsi[-1]
        adx = self.adx[-1]
        atr = self.atr[-1]
        avg_vol = self.avg_volume[-1]

        print(f"🌙 Moon Dev Backtest Bar {len(self.data)}: Close {close:.2f}, SMA20 {sma20:.2f}, SMA100 {sma100:.2f}, RSI {rsi:.2f}, ADX {adx:.2f}, ATR {atr:.2f} ✨")

        if close <= sma100:
            if self.position:
                print("🚀 Moon Dev: Exiting long due to broken uptrend below SMA100 🌙")
                self.position.close()
            return

        # 🌙 Moon Dev Optimization: Reduced Fib lookback to 50 for more recent and responsive retracement levels in fast-moving 15m BTC
        lookback = 50
        from_idx = max(0, len(self.data) - lookback - 1)
        recent_high_values = self.data.High[from_idx:len(self.data)-1]
        if len(recent_high_values) < 10:  # 🌙 Moon Dev Optimization: Shortened min lookback to 10 for quicker Fib calculations
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

        # 🌙 Moon Dev Optimization: Enhanced entry - Switched to SMA20 for faster crossovers, RSI>45<80 for broader momentum window, ADX>20, volume>1.2x for more trades, SMA20>SMA100 uptrend
        crossover = len(self.data) > 1 and self.data.Close[-2] <= self.sma20[-2] and close > sma20
        # 🌙 Moon Dev Optimization: Precise Fib touch - Check if level is within the bar's range (low <= fib618 <= high) for exact retracement confirmation, no tolerance needed
        touch_fib = low <= fib618 <= high
        volume_confirm = volume > 1.2 * avg_vol  # 🌙 Moon Dev Optimization: Loosened to 1.2x for higher trade frequency while still confirming interest
        momentum_rsi = rsi > 45 and rsi < 80  # 🌙 Moon Dev Optimization: Widened RSI range to capture more pullback opportunities without missing momentum
        trend_strength = adx > 20
        uptrend = close > sma100 and sma20 > sma100

        if crossover and touch_fib and volume_confirm and momentum_rsi and trend_strength and uptrend and not self.position:
            entry_price = close
            # 🌙 Moon Dev Optimization: Kept SL at 1.5x ATR or below Fib/swing, but use recent 5-bar low for tighter protection in volatile 15m
            sl_distance = 1.5 * atr
            stop_price = entry_price - sl_distance
            swing_low_recent = min(self.data.Low[-5:])  # 🌙 Moon Dev Optimization: Tighter recent low (5 bars) for better risk in short-term trades
            if fib618 < entry_price:
                stop_price = min(stop_price, fib618 - 0.5 * atr, swing_low_recent)
            risk_per_unit = entry_price - stop_price
            if risk_per_unit <= 0:
                return
            capital = 1000000
            risk_amount = capital * 0.015  # 🌙 Moon Dev Optimization: Increased risk to 1.5% per trade to amplify returns while staying managed
            position_size = risk_amount / risk_per_unit
            # 🌙 Moon Dev Optimization: Raised cap to 10% of capital for larger positions in high-conviction BTC setups
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
                self.partial_taken = False

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

            # 🌙 Moon Dev Optimization: Breakeven at 0.5:1 remains, but trail to SMA20 - 0.5*ATR at 1:1 for tighter protection in shorter trends
            if unrealized_pnl >= 0.5 * risk:
                breakeven_sl = entry_price + (0.1 * atr)
                if breakeven_sl > current_sl:
                    self.current_sl = breakeven_sl
                    print(f"🌙 Moon Dev: Moved SL to breakeven {breakeven_sl:.2f} after 0.5:1 RR ✨")

            if unrealized_pnl >= risk:
                trail_sl = sma20 - 0.5 * atr  # 🌙 Moon Dev Optimization: Tighter trail using SMA20 and reduced ATR multiplier for better lock-in
                if trail_sl > current_sl:
                    self.current_sl = trail_sl
                    print(f"🌙 Moon Dev: Trailing SL updated to {trail_sl:.2f} after 1:1 RR ✨")

            # 🌙 Moon Dev Optimization: Added partial exit at 2:1 RR (sell 50%) to secure profits early, then full TP at 4:1 for larger upside capture
            if rr >= 2 and not self.partial_taken:
                partial_size = self.position.size * 0.5
                self.sell(size=partial_size)
                self.partial_taken = True
                print(f"🌙 Moon Dev: Partial exit (50%) at 2:1 RR! Remaining size {self.position.size} 🚀")
                # After partial, tighten SL further to protect remaining
                self.current_sl = max(self.current_sl, entry_price + 0.5 * risk)

            # 🌙 Moon Dev Optimization: Increased full TP to 4:1 RR to hold for bigger BTC moves, improving overall return potential
            if unrealized_pnl >= 4 * risk:
                print(f"🌙 Moon Dev: Taking full profits at 4:1 RR! 🚀")
                self.position.close()
                return

            # Bearish divergence: Loosened RSI>65 for earlier warning in shorter timeframe
            if rsi > 65 and len(self.data) > 2 and close > self.data.Close[-2] and rsi < self.rsi[-2] and adx > 20:
                print(f"🌙 Moon Dev: Bearish RSI Divergence detected in overbought zone with trend, EXITING! 🚀")
                self.position.close()
                return

            # Exit below SMA20 for quicker response to trend weakness
            if close < sma20:
                print(f"🌙 Moon Dev: EXITING below SMA20 trail 🚀")
                self.position.close()
                return

            # Update peak for next divergence check
            if high > self.last_peak_price:
                self.last_peak_price = high
                self.last_peak_rsi = rsi

bt = Backtest(data, GoldenCrossover, cash=1000000, commission=0.002)
stats = bt.run()
print(stats)