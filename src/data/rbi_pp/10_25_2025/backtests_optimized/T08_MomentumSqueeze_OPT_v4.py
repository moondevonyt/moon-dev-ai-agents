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
        # 🌙 Moon Dev: Slightly loosened BB squeeze threshold to 0.09 for more quality setups without sacrificing too much (Entry Optimization - realistic increase in opportunities)
        self.bb_upper, self.bb_middle, self.bb_lower = self.I(talib.BBANDS, self.data.Close, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)
        self.macd_line, self.signal_line, self.hist = self.I(talib.MACD, self.data.Close, fastperiod=12, slowperiod=26, signalperiod=9)
        # 🌙 Moon Dev: Retained EMAs and added EMA200 for stronger trend confirmation (Indicator Optimization & Market Regime Filters)
        self.ema20 = self.I(talib.EMA, self.data.Close, timeperiod=20)
        self.ema50 = self.I(talib.EMA, self.data.Close, timeperiod=50)
        self.ema200 = self.I(talib.EMA, self.data.Close, timeperiod=200)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        # 🌙 Moon Dev: Retained RSI and added ADX for trend strength filter to avoid weak markets (Entry Optimization & Market Regime Filters)
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14)
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
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
        if len(self.data) < 300:  # 🌙 Moon Dev: Increased to 300 to accommodate EMA200 initialization safely
            return

        price = self.data.Close[-1]
        high = self.data.High[-1]
        low = self.data.Low[-1]
        volume = self.data.Volume[-1]
        upper = self.bb_upper[-1]
        lower = self.bb_lower[-1]
        middle = self.bb_middle[-1]
        bandwidth = (upper - lower) / middle

        # 🌙 Moon Dev: Adjusted print threshold to match new squeeze (0.09)
        if bandwidth < 0.09:
            print(f"🌙 Moon Dev: Squeeze detected! Bandwidth: {bandwidth:.4f} ✨")

        macd_l = self.macd_line[-1]
        sig_l = self.signal_line[-1]
        macd_p = self.macd_line[-2]
        sig_p = self.signal_line[-2]
        bull_cross = macd_l > sig_l and macd_p <= sig_p
        bear_cross = macd_l < sig_l and macd_p >= sig_p
        # 🌙 Moon Dev: Adjusted volume filter to 1.3x for balanced confirmation (Entry Optimization - slight loosening for more trades)
        vol_rising = volume > 1.3 * self.vol_sma[-1]
        # 🌙 Moon Dev: Enhanced trend filter with EMA200 for stronger regime detection (Market Regime Filters)
        trend_up = self.ema20[-1] > self.ema50[-1] and self.ema20[-1] > self.ema200[-1]
        trend_down = self.ema20[-1] < self.ema50[-1] and self.ema20[-1] < self.ema200[-1]
        # 🌙 Moon Dev: Loosened RSI filters slightly to 45/55 for more momentum opportunities (Indicator Optimization)
        rsi_long_ok = self.rsi[-1] > 45
        rsi_short_ok = self.rsi[-1] < 55
        # 🌙 Moon Dev: Added ADX filter >20 for trending conditions only (Market Regime Filters - avoids choppy markets)
        adx_strong = self.adx[-1] > 20

        current_bar = len(self.data) - 1

        # Reset expired breakouts
        # 🌙 Moon Dev: Extended window to 7 bars for capturing delayed breakouts realistically (Entry Optimization)
        if self.last_long_breakout >= 0 and current_bar - self.last_long_breakout > 7:
            self.last_long_breakout = -100
            self.long_breakout_low = None
            print("⏰ Long breakout window expired, resetting")
        if self.last_short_breakout >= 0 and current_bar - self.last_short_breakout > 7:
            self.last_short_breakout = -100
            self.short_breakout_high = None
            print("⏰ Short breakout window expired, resetting")

        # Detect new breakouts
        # 🌙 Moon Dev: Improved breakout detection using High/Low for more accurate crosses and loosened threshold to 0.09 (Entry Optimization)
        squeeze_threshold = 0.09
        if bandwidth < squeeze_threshold and high > upper:
            self.long_breakout_low = low
            self.last_long_breakout = current_bar
            print(f"🚀 Bullish breakout detected at {price}! Low: {low}")
        if bandwidth < squeeze_threshold and low < lower:
            self.short_breakout_high = high
            self.last_short_breakout = current_bar
            print(f"📉 Bearish breakout detected at {price}! High: {high}")

        # Long entry
        bars_since_long = current_bar - self.last_long_breakout if self.last_long_breakout >= 0 else 100
        if (self.last_long_breakout >= 0 and bars_since_long <= 7 and bull_cross and vol_rising and trend_up and rsi_long_ok and adx_strong and
            not self.position and self.long_breakout_low is not None):
            sl = self.long_breakout_low - self.atr[-1]
            entry = price
            risk = entry - sl
            if risk > 0:
                # 🌙 Moon Dev: Increased risk to 2.5% for higher returns while keeping drawdown manageable (Risk Management)
                risk_amount = self.equity * 0.025
                pos_size = risk_amount / risk
                # 🌙 Moon Dev: Allow fractional sizes for precise risk control in crypto (Risk Management)
                if pos_size > 0:
                    # 🌙 Moon Dev: Improved RR to 3.5:1 for enhanced profitability without over-optimization (Exit Optimization)
                    tp = entry + 3.5 * risk
                    self.buy(size=pos_size)
                    self.entry_price = entry
                    self.initial_risk = risk
                    self.sl = sl
                    self.tp = tp
                    print(f"🌙 Moon Dev: LONG ENTRY at {entry}, SL: {sl}, TP: {tp}, Size: {pos_size:.2f}, Risk: {risk_amount:.2f} 🚀")
                    if bull_cross:
                        print(f"📈 Bullish MACD cross confirmed!")

        # Short entry
        bars_since_short = current_bar - self.last_short_breakout if self.last_short_breakout >= 0 else 100
        if (self.last_short_breakout >= 0 and bars_since_short <= 7 and bear_cross and vol_rising and trend_down and rsi_short_ok and adx_strong and
            not self.position and self.short_breakout_high is not None):
            sl = self.short_breakout_high + self.atr[-1]
            entry = price
            risk = sl - entry
            if risk > 0:
                # 🌙 Moon Dev: Increased risk to 2.5% for higher returns while keeping drawdown manageable (Risk Management)
                risk_amount = self.equity * 0.025
                pos_size = risk_amount / risk
                # 🌙 Moon Dev: Allow fractional sizes for precise risk control in crypto (Risk Management)
                if pos_size > 0:
                    # 🌙 Moon Dev: Improved RR to 3.5:1 for enhanced profitability without over-optimization (Exit Optimization)
                    tp = entry - 3.5 * risk
                    self.sell(size=pos_size)
                    self.entry_price = entry
                    self.initial_risk = risk
                    self.sl = sl
                    self.tp = tp
                    print(f"🌙 Moon Dev: SHORT ENTRY at {entry}, SL: {sl}, TP: {tp}, Size: {pos_size:.2f}, Risk: {risk_amount:.2f} 📉")
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
            # 🌙 Moon Dev: Relaxed bandwidth exit to 0.3 to give trades more breathing room (Exit Optimization)
            if bandwidth > 0.3:
                self.position.close()
                print(f"🌙 Bandwidth expanded to {bandwidth:.4f}, exiting position 💥")
                self._reset_pos()
                return
            if self.position.is_long:
                # Trailing stop after 1:1
                favorable_move = price - entry_price
                if favorable_move >= self.initial_risk:
                    # 🌙 Moon Dev: Tightened trailing offset to 0.3 ATR for better profit locking (Exit Optimization)
                    new_sl = max(self.sl, self.ema20[-1] - 0.3 * self.atr[-1])
                    if new_sl > self.sl:
                        self.sl = new_sl
                        print(f"🌙 Trailing long SL to {new_sl} ✨")
                # MACD histogram reverse
                if self.hist[-1] <= 0:
                    self.position.close()
                    print(f"🌙 MACD histogram turned negative, closing long 📊")
                    self._reset_pos()
                    return
            else:  # short
                # Trailing stop after 1:1
                favorable_move = entry_price - price
                if favorable_move >= self.initial_risk:
                    # 🌙 Moon Dev: Tightened trailing offset to 0.3 ATR for better profit locking (Exit Optimization)
                    new_sl = min(self.sl, self.ema20[-1] + 0.3 * self.atr[-1])
                    if new_sl < self.sl:
                        self.sl = new_sl
                        print(f"🌙 Trailing short SL to {new_sl} ✨")
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