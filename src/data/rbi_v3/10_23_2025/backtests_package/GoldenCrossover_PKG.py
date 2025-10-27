import pandas as pd
import numpy as np
import talib
from backtesting import Backtest, Strategy

data = pd.read_csv('/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv', parse_dates=['datetime'], index_col='datetime')
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data = data.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'})

class GoldenCrossover(Strategy):
    last_peak_price = 0.0
    last_peak_rsi = 100.0
    entry_bar = 0

    def init(self):
        self.sma20 = self.I(talib.SMA, self.data.Close, timeperiod=20)
        self.sma200 = self.I(talib.SMA, self.data.Close, timeperiod=200)
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        self.avg_volume = self.I(talib.SMA, self.data.Volume, timeperiod=20)
        self.last_peak_price = 0.0
        self.last_peak_rsi = 100.0

    def next(self):
        if len(self.data) < 200:
            return

        close = self.data.Close[-1]
        low = self.data.Low[-1]
        high = self.data.High[-1]
        volume = self.data.Volume[-1]
        sma20 = self.sma20[-1]
        sma200 = self.sma200[-1]
        rsi = self.rsi[-1]
        atr = self.atr[-1]
        avg_vol = self.avg_volume[-1]

        print(f"🌙 Moon Dev Backtest Bar {len(self.data)}: Close {close:.2f}, SMA20 {sma20:.2f}, SMA200 {sma200:.2f}, RSI {rsi:.2f}, ATR {atr:.2f} ✨")

        if close <= sma200:
            if self.position:
                print("🚀 Moon Dev: Exiting long due to broken uptrend below SMA200 🌙")
                self.position.close()
            return

        # Calculate dynamic Fib 61.8% retracement
        lookback = 50
        from_idx = max(0, len(self.data) - lookback - 1)
        recent_high_values = self.data.High.iloc[from_idx:len(self.data)-1].values
        if len(recent_high_values) < 10:
            return
        rel_high_idx = np.argmax(recent_high_values)
        abs_high_idx = from_idx + rel_high_idx
        swing_high = self.data.High.iloc[abs_high_idx]

        low_values_to_high = self.data.Low.iloc[from_idx:abs_high_idx + 1].values
        rel_low_idx = np.argmin(low_values_to_high)
        abs_low_idx = from_idx + rel_low_idx
        swing_low = self.data.Low.iloc[abs_low_idx]

        fib618 = swing_high - 0.618 * (swing_high - swing_low)
        print(f"🌙 Moon Dev Fib Calc: 61.8% Level {fib618:.2f}, High {swing_high:.2f}, Low {swing_low:.2f} 🚀")

        # Entry conditions
        crossover = len(self.data) > 1 and self.data.Close[-2] <= self.sma20[-2] and close > sma20
        touch_fib = low <= fib618 + (0.01 * close)  # Tolerance for touch/wick
        volume_confirm = volume > avg_vol
        uptrend = close > sma200

        if crossover and touch_fib and volume_confirm and uptrend and not self.position:
            entry_price = close
            sl_distance = 1.2 * atr
            stop_price = entry_price - sl_distance
            if fib618 < entry_price:
                stop_price = min(stop_price, fib618 - 0.5 * atr)
            risk_per_unit = entry_price - stop_price
            if risk_per_unit <= 0:
                return
            capital = 1000000
            risk_amount = capital * 0.01
            position_size = risk_amount / risk_per_unit
            position_size = int(round(position_size))
            if position_size > 0:
                print(f"🌙 Moon Dev: LONG ENTRY at {entry_price:.2f}, SL {stop_price:.2f}, Size {position_size} BTC, Fib Touch Confirmed! ✨🚀")
                self.buy(size=position_size, sl=stop_price)
                self.entry_bar = len(self.data) - 1
                self.last_peak_price = high
                self.last_peak_rsi = rsi

        # Position management and exits
        if self.position:
            entry_price = self.position.entry_price
            current_sl = self.position.sl
            bars_since_entry = len(self.data) - 1 - self.entry_bar
            unrealized_pnl = close - entry_price
            risk = entry_price - current_sl if current_sl else sl_distance
            rr = unrealized_pnl / risk if risk > 0 else 0
            print(f"🚀 Moon Dev Position: Bars {bars_since_entry}, RR {rr:.2f}, Current SL {current_sl:.2f} 🌙")

            # Trailing stop after 1:1 RR
            if unrealized_pnl >= risk:
                trail_sl = sma20 - atr
                if trail_sl > current_sl:
                    self.position.sl = trail_sl
                    print(f"🌙 Moon Dev: Trailing SL updated to {trail_sl:.2f} after 1:1 RR ✨")

            # Profit take at 2:1 RR
            if unrealized_pnl >= 2 * risk:
                print(f"🌙 Moon Dev: Taking profits at 2:1 RR! 🚀")
                self.position.close()
                return

            # Bearish divergence approximation: overbought, price up but RSI down
            if rsi > 70 and len(self.data) > 2 and close > self.data.Close[-2] and rsi < self.rsi[-2]:
                print(f"🌙 Moon Dev: Bearish RSI Divergence detected in overbought zone, EXITING! 🚀")
                self.position.close()
                return

            # Exit below SMA20 trail
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