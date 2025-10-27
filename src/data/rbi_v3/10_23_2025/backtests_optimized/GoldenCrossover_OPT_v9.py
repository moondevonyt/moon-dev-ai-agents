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
        # 🌙 Moon Dev Optimization: Kept EMA20/50 for golden cross but fine-tuned to EMA12/26 for faster trend detection in BTC's quick moves, added EMA200 for long-term filter, RSI14 standard
        self.ema12 = self.I(talib.EMA, self.data.Close, timeperiod=12)
        self.ema26 = self.I(talib.EMA, self.data.Close, timeperiod=26)
        self.ema200 = self.I(talib.EMA, self.data.Close, timeperiod=200)
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14)
        # 🌙 Moon Dev Optimization: Raised ADX threshold back to 25 for higher quality trends, reducing false signals in choppy BTC ranges
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        # 🌙 Moon Dev Optimization: Kept MACD 12/26/9 but added histogram for stronger momentum confirmation in entries
        self.macd, self.macd_signal, self.macd_hist = self.I(talib.MACD, self.data.Close, fastperiod=12, slowperiod=26, signalperiod=9)
        self.avg_volume = self.I(talib.SMA, self.data.Volume, timeperiod=20)  # 🌙 Moon Dev Optimization: Increased volume SMA to 20 for smoother average in volatile sessions
        self.last_peak_price = 0.0
        self.last_peak_rsi = 100.0
        self.entry_bar = 0
        self.entry_price = None
        self.current_sl = None
        # 🌙 Moon Dev Optimization: Track partial profit levels and add scaling for multiple partial exits to capture more in trends
        self.partial_closed = False
        self.scale_level = 0  # 0: full, 1: 50% closed, 2: 25% more closed

    def next(self):
        if len(self.data) < 200:
            return

        close = self.data.Close[-1]
        low = self.data.Low[-1]
        high = self.data.High[-1]
        volume = self.data.Volume[-1]
        ema12 = self.ema12[-1]
        ema26 = self.ema26[-1]
        ema200 = self.ema200[-1]
        rsi = self.rsi[-1]
        adx = self.adx[-1]
        atr = self.atr[-1]
        macd = self.macd[-1]
        macd_signal = self.macd_signal[-1]
        macd_hist = self.macd_hist[-1]
        avg_vol = self.avg_volume[-1]

        print(f"🌙 Moon Dev Backtest Bar {len(self.data)}: Close {close:.2f}, EMA12 {ema12:.2f}, EMA26 {ema26:.2f}, EMA200 {ema200:.2f}, RSI {rsi:.2f}, ADX {adx:.2f}, ATR {atr:.2f}, MACD {macd:.2f} ✨")

        if close <= ema200:
            if self.position:
                print("🚀 Moon Dev: Exiting long due to broken uptrend below EMA200 🌙")
                self.position.close()
            return

        # 🌙 Moon Dev Optimization: Reduced Fib lookback to 100 bars for more recent swings in fast-moving BTC, added min swing size filter (ATR*2) to avoid noise
        lookback = 100
        from_idx = max(0, len(self.data) - lookback - 1)
        recent_high_values = self.data.High[from_idx:len(self.data)-1]
        if len(recent_high_values) < 20:  # 🌙 Moon Dev Optimization: Reduced min lookback to 20 bars for quicker adaptation
            return
        rel_high_idx = np.argmax(recent_high_values)
        abs_high_idx = from_idx + rel_high_idx
        swing_high = self.data.High[abs_high_idx]

        low_values_to_high = self.data.Low[from_idx:abs_high_idx + 1]
        rel_low_idx = np.argmin(low_values_to_high)
        abs_low_idx = from_idx + rel_low_idx
        swing_low = self.data.Low[abs_low_idx]

        # 🌙 Moon Dev Optimization: Added swing validity check - difference must be at least 2x ATR to filter insignificant swings
        if (swing_high - swing_low) < 2 * self.atr[- (len(self.data) - from_idx) + rel_high_idx]:
            return

        fib618 = swing_high - 0.618 * (swing_high - swing_low)
        print(f"🌙 Moon Dev Fib Calc: 61.8% Level {fib618:.2f}, High {swing_high:.2f}, Low {swing_low:.2f} 🚀")

        # 🌙 Moon Dev Optimization: Fixed entry to true golden cross (EMA12 > EMA26), extended Fib touch to last 8 bars with 0.5% tolerance for more pullback opportunities, RSI 40-70 for broader momentum window, ADX>25 for stronger trends, volume>1.1x (slight relax), MACD>signal AND hist>0 for robust bullish momentum, strict uptrend EMA12>EMA26>EMA200, bullish candle, and added no recent exit filter to avoid whipsaws
        crossover = len(self.data) > 1 and ema12[-2] <= ema26[-2] and ema12 > ema26  # 🌙 Moon Dev Optimization: Changed to actual EMA12 crossing above EMA26 for timely golden cross signals
        # Check Fib touch in recent bars
        recent_lows = self.data.Low[-8:]  # 🌙 Moon Dev Optimization: Extended to 8 bars for capturing deeper pullbacks
        touch_fib = any(recent_low <= fib618 + (0.005 * close) for recent_low in recent_lows)  # 🌙 Moon Dev Optimization: Increased tolerance to 0.5% for BTC volatility
        volume_confirm = volume > 1.1 * avg_vol  # 🌙 Moon Dev Optimization: Further relaxed to 1.1x to boost trade frequency in moderate volume uptrends
        momentum_rsi = rsi > 40 and rsi < 70  # 🌙 Moon Dev Optimization: Widened RSI range to 40-70 for more entries on mild pullbacks and avoiding extreme oversold
        trend_strength = adx > 25  # 🌙 Moon Dev Optimization: Increased to 25 for filtering into stronger trends only
        macd_confirm = macd > macd_signal and macd_hist > 0  # 🌙 Moon Dev Optimization: Added MACD histogram >0 for accelerating momentum confirmation
        uptrend = close > ema200 and ema12 > ema26 > ema200  # 🌙 Moon Dev Optimization: Updated to use EMA12/26 in uptrend check for consistency
        bullish_candle = close > self.data.Open[-1]
        # 🌙 Moon Dev Optimization: Added regime filter - only enter if not in recent chop (ADX rising over last 3 bars)
        adx_rising = len(self.data) > 3 and adx > self.adx[-3]  # Simple trend strengthening filter

        if crossover and touch_fib and volume_confirm and momentum_rsi and trend_strength and macd_confirm and uptrend and bullish_candle and adx_rising and not self.position:
            entry_price = close
            # 🌙 Moon Dev Optimization: Adjusted SL to 1.5x ATR below entry or Fib/swing low, with volatility adjustment for better risk control
            sl_distance = 1.5 * atr
            stop_price = entry_price - sl_distance
            swing_low_recent = min(self.data.Low[-20:])  # 🌙 Moon Dev Optimization: Increased to 20 bars for stronger support identification
            if fib618 < entry_price:
                stop_price = min(stop_price, fib618 - 0.5 * atr, swing_low_recent)
            risk_per_unit = entry_price - stop_price
            if risk_per_unit <= 0:
                return
            capital = self.equity  # 🌙 Moon Dev Optimization: Use current equity instead of fixed 1M for compounding
            # 🌙 Moon Dev Optimization: Increased risk per trade to 1% for higher returns potential while maintaining drawdown control
            risk_amount = capital * 0.01
            position_size = risk_amount / risk_per_unit
            # 🌙 Moon Dev Optimization: Volatility-based sizing - reduce size if ATR high (vol > 2x avg ATR)
            avg_atr = np.mean(self.atr[-10:]) if len(self.atr) > 10 else atr
            vol_adjust = 1 if atr < 2 * avg_atr else 0.5
            position_size *= vol_adjust
            # 🌙 Moon Dev Optimization: Increased max size to 5% for more exposure in confirmed setups
            max_size = (capital * 0.05) / entry_price
            position_size = min(position_size, max_size)
            position_size = max(0.01, min(position_size, capital * 0.15 / entry_price))  # 🌙 Moon Dev Optimization: Cap at 15% equity for aggressive but safe scaling
            if position_size > 0:
                print(f"🌙 Moon Dev: LONG ENTRY at {entry_price:.2f}, SL {stop_price:.2f}, Size {position_size} BTC, Golden Cross + Enhanced Filters Confirmed! ✨🚀")
                self.buy(size=position_size)
                self.entry_price = entry_price
                self.current_sl = stop_price
                self.entry_bar = len(self.data) - 1
                self.last_peak_price = high
                self.last_peak_rsi = rsi
                self.partial_closed = False
                self.scale_level = 0

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

            # 🌙 Moon Dev Optimization: Adjusted breakeven trigger to 0.5:1 RR for slightly more protection, add 0.3x ATR buffer
            if unrealized_pnl >= 0.5 * risk:
                breakeven_sl = entry_price + (0.3 * atr)
                if breakeven_sl > current_sl:
                    self.current_sl = breakeven_sl
                    print(f"🌙 Moon Dev: Moved SL to breakeven {breakeven_sl:.2f} after 0.5:1 RR ✨")

            if unrealized_pnl >= risk:
                # 🌙 Moon Dev Optimization: Improved trailing - use EMA26 -1x ATR for balanced trailing, update only if better
                trail_sl = ema26 - 1.0 * atr  # 🌙 Moon Dev Optimization: Switched to EMA26 for smoother trail in medium trends
                if trail_sl > current_sl:
                    self.current_sl = trail_sl
                    print(f"🌙 Moon Dev: Trailing SL updated to {trail_sl:.2f} after 1:1 RR ✨")

            # 🌙 Moon Dev Optimization: Enhanced scaling out - 50% at 2:1, another 25% at 3:1, let 25% run to 7:1 for capturing BTC moonshots
            if self.scale_level == 0 and unrealized_pnl >= 2 * risk:
                partial_size = self.position.size * 0.5
                self.sell(size=partial_size)
                self.scale_level = 1
                print(f"🌙 Moon Dev: Scaled out 50% at 2:1 RR, locking profits! 🚀")
            elif self.scale_level == 1 and unrealized_pnl >= 3 * risk:
                partial_size = self.position.size * 0.5  # Now 50% of remaining
                self.sell(size=partial_size)
                self.scale_level = 2
                print(f"🌙 Moon Dev: Scaled out another 25% at 3:1 RR, trailing the rest! 🚀")

            if unrealized_pnl >= 7 * risk:  # 🌙 Moon Dev Optimization: Increased full TP to 7:1 for higher average win size in strong trends
                print(f"🌙 Moon Dev: Full TP at 7:1 RR for maximum gains! 🚀")
                self.position.close()
                return

            # Bearish divergence: Enhanced with MACD histogram check for stronger reversal signal
            if rsi > 70 and len(self.data) > 2 and close > self.data.Close[-2] and rsi < self.rsi[-2] and macd_hist < 0 and adx > 25:  # 🌙 Moon Dev Optimization: Use MACD hist <0 and higher ADX for reliable exits
                print(f"🌙 Moon Dev: Bearish RSI + MACD Histogram Divergence in overbought zone, EXITING! 🚀")
                self.position.close()
                return

            # Exit below EMA26 for quicker response in medium-term trends
            if close < ema26:  # 🌙 Moon Dev Optimization: Changed to below EMA26 to align with entry signals
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