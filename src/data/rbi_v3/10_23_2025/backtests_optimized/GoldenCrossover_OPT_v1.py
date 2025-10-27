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
        # 🌙 Moon Dev Optimization: Changed SMA20 to SMA50 for fewer false crossovers in choppy markets, reducing whipsaws
        self.sma50 = self.I(talib.SMA, self.data.Close, timeperiod=50)
        self.sma200 = self.I(talib.SMA, self.data.Close, timeperiod=200)
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14)
        # 🌙 Moon Dev Optimization: Added ADX for trend strength filter (>25 indicates strong trend, avoids ranging markets)
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        # 🌙 Moon Dev Optimization: Tightened volume SMA to 10 for more responsive volume confirmation
        self.avg_volume = self.I(talib.SMA, self.data.Volume, timeperiod=10)
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
        sma50 = self.sma50[-1]
        sma200 = self.sma200[-1]
        rsi = self.rsi[-1]
        adx = self.adx[-1]
        atr = self.atr[-1]
        avg_vol = self.avg_volume[-1]

        print(f"🌙 Moon Dev Backtest Bar {len(self.data)}: Close {close:.2f}, SMA50 {sma50:.2f}, SMA200 {sma200:.2f}, RSI {rsi:.2f}, ADX {adx:.2f}, ATR {atr:.2f} ✨")

        if close <= sma200:
            if self.position:
                print("🚀 Moon Dev: Exiting long due to broken uptrend below SMA200 🌙")
                self.position.close()
            return

        # 🌙 Moon Dev Optimization: Increased Fib lookback to 100 for more reliable swing high/low identification in volatile BTC
        lookback = 100
        from_idx = max(0, len(self.data) - lookback - 1)
        recent_high_values = self.data.High[from_idx:len(self.data)-1]
        if len(recent_high_values) < 20:  # 🌙 Moon Dev Optimization: Require longer lookback minimum for better Fib accuracy
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

        # 🌙 Moon Dev Optimization: Enhanced entry conditions - Use SMA50 crossover, add RSI>50 for momentum (avoids deep oversold), ADX>25 for trend strength, volume>1.5x for stronger confirmation, ensure SMA50>SMA200 for uptrend
        crossover = len(self.data) > 1 and self.data.Close[-2] <= self.sma50[-2] and close > sma50
        touch_fib = low <= fib618 + (0.005 * close)  # 🌙 Moon Dev Optimization: Tighter tolerance (0.5%) for precise Fib touch
        volume_confirm = volume > 1.5 * avg_vol  # 🌙 Moon Dev Optimization: Increased to 1.5x for higher quality volume spikes
        momentum_rsi = rsi > 50 and rsi < 70  # 🌙 Moon Dev Optimization: RSI filter for pullback momentum without overbought entries
        trend_strength = adx > 25
        uptrend = close > sma200 and sma50 > sma200  # 🌙 Moon Dev Optimization: Added SMA50 > SMA200 for golden cross confirmation

        if crossover and touch_fib and volume_confirm and momentum_rsi and trend_strength and uptrend and not self.position:
            entry_price = close
            # 🌙 Moon Dev Optimization: Improved SL placement - Use 1.5x ATR or below swing low, whichever is tighter, for better risk control
            sl_distance = 1.5 * atr
            stop_price = entry_price - sl_distance
            swing_low_recent = min(self.data.Low[-10:])  # Recent swing low
            if fib618 < entry_price:
                stop_price = min(stop_price, fib618 - 0.5 * atr, swing_low_recent)
            risk_per_unit = entry_price - stop_price
            if risk_per_unit <= 0:
                return
            capital = 1000000
            risk_amount = capital * 0.01
            position_size = risk_amount / risk_per_unit
            # 🌙 Moon Dev Optimization: Cap position size to 5% of capital for BTC to manage leverage risk
            max_size = (capital * 0.05) / entry_price
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

            # 🌙 Moon Dev Optimization: Enhanced trailing - Move to breakeven immediately after entry + small profit (0.5:1), then trail to SMA50 - 1x ATR for better protection
            if unrealized_pnl >= 0.5 * risk:
                breakeven_sl = entry_price + (0.1 * atr)  # Slight buffer above entry
                if breakeven_sl > current_sl:
                    self.current_sl = breakeven_sl
                    print(f"🌙 Moon Dev: Moved SL to breakeven {breakeven_sl:.2f} after 0.5:1 RR ✨")

            if unrealized_pnl >= risk:
                trail_sl = sma50 - atr  # 🌙 Moon Dev Optimization: Use SMA50 for trailing in uptrend
                if trail_sl > current_sl:
                    self.current_sl = trail_sl
                    print(f"🌙 Moon Dev: Trailing SL updated to {trail_sl:.2f} after 1:1 RR ✨")

            # 🌙 Moon Dev Optimization: Increased TP to 3:1 RR to capture larger moves in trending BTC markets
            if unrealized_pnl >= 3 * risk:
                print(f"🌙 Moon Dev: Taking profits at 3:1 RR! 🚀")
                self.position.close()
                return

            # Bearish divergence approximation: overbought, price up but RSI down - Kept but added ADX check for validity
            if rsi > 70 and len(self.data) > 2 and close > self.data.Close[-2] and rsi < self.rsi[-2] and adx > 25:
                print(f"🌙 Moon Dev: Bearish RSI Divergence detected in overbought zone with strong trend, EXITING! 🚀")
                self.position.close()
                return

            # Exit below SMA50 trail - Updated to SMA50
            if close < sma50:
                print(f"🌙 Moon Dev: EXITING below SMA50 trail 🚀")
                self.position.close()
                return

            # Update peak for next divergence check
            if high > self.last_peak_price:
                self.last_peak_price = high
                self.last_peak_rsi = rsi

bt = Backtest(data, GoldenCrossover, cash=1000000, commission=0.002)
stats = bt.run()
print(stats)