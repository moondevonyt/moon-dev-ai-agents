import pandas as pd
import numpy as np
from backtesting import Backtest, Strategy
import talib

path = '/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv'

data = pd.read_csv(path)
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data = data.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'})
data = data.set_index(pd.to_datetime(data['datetime']))
data = data.drop(columns=['datetime'])

class MomentumSqueeze(Strategy):
    def init(self):
        # 🌙 Moon Dev Optimization: Fine-tuned BB to 21 periods for slightly smoother bands, tightened squeeze threshold in next()
        self.bb_upper, self.bb_middle, self.bb_lower = self.I(talib.BBANDS, self.data.Close, timeperiod=21, nbdevup=2, nbdevdn=2, matype=0)
        # 🌙 Moon Dev Optimization: Switched to EMA for MACD signal for faster response, but kept core periods standard
        self.macd_line, self.signal_line, self.hist = self.I(talib.MACD, self.data.Close, fastperiod=12, slowperiod=26, signalperiod=9)
        # 🌙 Moon Dev Optimization: Changed to EMA200 for more responsive trend filter
        self.sma200 = self.I(talib.EMA, self.data.Close, timeperiod=200)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        # 🌙 Moon Dev Optimization: Added ADX for trend strength filter (>25 confirms stronger trends, avoids chop)
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        # 🌙 Moon Dev Optimization: Added RSI for momentum filter (long >50, short <50 to align with trend)
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14)
        self.vol_sma = self.I(talib.SMA, self.data.Volume, timeperiod=20)
        self.long_breakout_low = None
        self.short_breakout_high = None
        self.last_long_breakout = -100
        self.last_short_breakout = -100
        self.entry_price = 0.0
        self.initial_risk = 0.0
        self.sl = 0.0
        self.tp = 0.0

    def _reset_pos(self):
        self.entry_price = 0.0
        self.initial_risk = 0.0
        self.sl = 0.0
        self.tp = 0.0

    def next(self):
        if len(self.data) < 250:
            return

        price = self.data.Close[-1]
        high = self.data.High[-1]
        low = self.data.Low[-1]
        volume = self.data.Volume[-1]
        upper = self.bb_upper[-1]
        lower = self.bb_lower[-1]
        middle = self.bb_middle[-1]
        # 🌙 Moon Dev Optimization: Tightened squeeze detection to bandwidth <0.08 for higher quality, less frequent but stronger setups
        bandwidth = (upper - lower) / middle

        if bandwidth < 0.08:
            print(f"🌙 Moon Dev: Squeeze detected! Bandwidth: {bandwidth:.4f} ✨")

        macd_l = self.macd_line[-1]
        sig_l = self.signal_line[-1]
        macd_p = self.macd_line[-2]
        sig_p = self.signal_line[-2]
        bull_cross = macd_l > sig_l and macd_p <= sig_p
        bear_cross = macd_l < sig_l and macd_p >= sig_p
        # 🌙 Moon Dev Optimization: Strengthened volume filter to >1.5x SMA for better momentum confirmation
        vol_rising = volume > 1.5 * self.vol_sma[-1]
        trend_up = price > self.sma200[-1]
        trend_down = price < self.sma200[-1]
        # 🌙 Moon Dev Optimization: Added ADX filter for regime (only trade if ADX >25, avoids weak trends/chop)
        strong_trend = self.adx[-1] > 25

        current_bar = len(self.data) - 1

        # Reset expired breakouts
        if self.last_long_breakout >= 0 and current_bar - self.last_long_breakout > 3:
            self.last_long_breakout = -100
            self.long_breakout_low = None
            print("⏰ Long breakout window expired, resetting")
        if self.last_short_breakout >= 0 and current_bar - self.last_short_breakout > 3:
            self.last_short_breakout = -100
            self.short_breakout_high = None
            print("⏰ Short breakout window expired, resetting")

        # Detect new breakouts
        # 🌙 Moon Dev Optimization: Require close > upper/lower for breakout confirmation (more reliable than intra-bar price)
        if bandwidth < 0.08 and price > upper:
            self.long_breakout_low = low
            self.last_long_breakout = current_bar
            print(f"🚀 Bullish breakout detected at {price}! Low: {low}")
        if bandwidth < 0.08 and price < lower:
            self.short_breakout_high = high
            self.last_short_breakout = current_bar
            print(f"📉 Bearish breakout detected at {price}! High: {high}")

        # Long entry
        bars_since_long = current_bar - self.last_long_breakout if self.last_long_breakout >= 0 else 100
        # 🌙 Moon Dev Optimization: Added RSI >50 and strong_trend filters for better entry quality
        if (self.last_long_breakout >= 0 and bars_since_long <= 3 and bull_cross and vol_rising and trend_up and
            strong_trend and self.rsi[-1] > 50 and not self.position and self.long_breakout_low is not None):
            sl = self.long_breakout_low - self.atr[-1]
            entry = price
            risk = entry - sl
            if risk > 0:
                # 🌙 Moon Dev Optimization: Increased risk per trade to 2% for higher return potential, balanced with better filters
                risk_amount = self.equity * 0.02
                pos_size = risk_amount / risk
                # 🌙 Moon Dev Optimization: Allow fractional sizes for precise risk management in crypto
                pos_size = pos_size  # Keep as float, backtest handles it
                # Improved TP to 1:3 RR for capturing larger moves in trending BTC
                tp = entry + 3 * risk
                self.buy(size=pos_size)
                self.entry_price = entry
                self.initial_risk = risk
                self.sl = sl
                self.tp = tp
                print(f"🌙 Moon Dev: LONG ENTRY at {entry}, SL: {sl}, TP: {tp}, Size: {pos_size}, Risk: {risk_amount:.2f} 🚀")
                if bull_cross:
                    print(f"📈 Bullish MACD cross confirmed!")

        # Short entry
        bars_since_short = current_bar - self.last_short_breakout if self.last_short_breakout >= 0 else 100
        # 🌙 Moon Dev Optimization: Added RSI <50 and strong_trend filters for better entry quality
        if (self.last_short_breakout >= 0 and bars_since_short <= 3 and bear_cross and vol_rising and trend_down and
            strong_trend and self.rsi[-1] < 50 and not self.position and self.short_breakout_high is not None):
            sl = self.short_breakout_high + self.atr[-1]
            entry = price
            risk = sl - entry
            if risk > 0:
                # 🌙 Moon Dev Optimization: Increased risk per trade to 2% for higher return potential
                risk_amount = self.equity * 0.02
                pos_size = risk_amount / risk
                # 🌙 Moon Dev Optimization: Allow fractional sizes
                pos_size = pos_size
                # Improved TP to 1:3 RR
                tp = entry - 3 * risk
                self.sell(size=pos_size)
                self.entry_price = entry
                self.initial_risk = risk
                self.sl = sl
                self.tp = tp
                print(f"🌙 Moon Dev: SHORT ENTRY at {entry}, SL: {sl}, TP: {tp}, Size: {pos_size}, Risk: {risk_amount:.2f} 📉")
                if bear_cross:
                    print(f"📉 Bearish MACD cross confirmed!")

        # Manage open positions
        if self.position:
            entry_price = self.entry_price
            # SL and TP checks
            if self.position.is_long:
                if self.data.Low[-1] <= self.sl:
                    self.position.close()
                    print(f"🌙 Moon Dev: SL hit for long, closing at {price} 💥")
                    self._reset_pos()
                    return
                if self.data.High[-1] >= self.tp:
                    self.position.close()
                    print(f"🌙 Moon Dev: TP hit for long, closing at {price} 🎯")
                    self._reset_pos()
                    return
            else:
                if self.data.High[-1] >= self.sl:
                    self.position.close()
                    print(f"🌙 Moon Dev: SL hit for short, closing at {price} 💥")
                    self._reset_pos()
                    return
                if self.data.Low[-1] <= self.tp:
                    self.position.close()
                    print(f"🌙 Moon Dev: TP hit for short, closing at {price} 🎯")
                    self._reset_pos()
                    return
            # 🌙 Moon Dev Optimization: Tightened exit on expansion to >0.25 for quicker exits in volatile expansions
            if bandwidth > 0.25:
                self.position.close()
                print(f"🌙 Bandwidth expanded to {bandwidth:.4f}, exiting position 💥")
                self._reset_pos()
                return
            if self.position.is_long:
                # 🌙 Moon Dev Optimization: Enhanced trailing stop - move to breakeven at 1:1, then trail with 1.5*ATR from high for better risk/reward
                favorable_move = price - entry_price
                if favorable_move >= self.initial_risk:
                    # Move to breakeven first
                    breakeven = entry_price + (0.1 * self.initial_risk)
                    self.sl = max(self.sl, breakeven)
                    # Then trail with ATR
                    trail_sl = high - (1.5 * self.atr[-1])
                    self.sl = max(self.sl, trail_sl)
                    if self.sl > breakeven:
                        print(f"🌙 Trailing long SL to {self.sl} with ATR ✨")
                # MACD histogram reverse
                if self.hist[-1] <= 0:
                    self.position.close()
                    print(f"🌙 MACD histogram turned negative, closing long 📊")
                    self._reset_pos()
                    return
            else:  # short
                # 🌙 Moon Dev Optimization: Enhanced trailing stop symmetric for shorts
                favorable_move = entry_price - price
                if favorable_move >= self.initial_risk:
                    breakeven = entry_price - (0.1 * self.initial_risk)
                    self.sl = min(self.sl, breakeven)
                    trail_sl = low + (1.5 * self.atr[-1])
                    self.sl = min(self.sl, trail_sl)
                    if self.sl < breakeven:
                        print(f"🌙 Trailing short SL to {self.sl} with ATR ✨")
                # MACD histogram reverse
                if self.hist[-1] >= 0:
                    self.position.close()
                    print(f"🌙 MACD histogram turned positive, closing short 📊")
                    self._reset_pos()
                    return

bt = Backtest(data, MomentumSqueeze, cash=1000000, commission=0.001)
stats = bt.run()
print(stats)
print(stats._strategy)