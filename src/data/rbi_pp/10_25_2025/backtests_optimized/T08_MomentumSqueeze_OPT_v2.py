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
        self.bb_upper, self.bb_middle, self.bb_lower = self.I(talib.BBANDS, self.data.Close, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)
        self.macd_line, self.signal_line, self.hist = self.I(talib.MACD, self.data.Close, fastperiod=12, slowperiod=26, signalperiod=9)
        self.sma200 = self.I(talib.SMA, self.data.Close, timeperiod=200)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        self.vol_sma = self.I(talib.SMA, self.data.Volume, timeperiod=20)
        # 🌙 Moon Dev Optimization: Added RSI for momentum confirmation and ADX for trend strength filter to improve entry quality
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14)
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
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
        bandwidth = (upper - lower) / middle

        if bandwidth < 0.10:
            print(f"🌙 Moon Dev: Squeeze detected! Bandwidth: {bandwidth:.4f} ✨")

        macd_l = self.macd_line[-1]
        sig_l = self.signal_line[-1]
        macd_p = self.macd_line[-2]
        sig_p = self.signal_line[-2]
        bull_cross = macd_l > sig_l and macd_p <= sig_p
        bear_cross = macd_l < sig_l and macd_p >= sig_p
        # 🌙 Moon Dev Optimization: Tightened volume filter to 1.2x SMA for stronger confirmation of breakout momentum
        vol_rising = volume > 1.2 * self.vol_sma[-1]
        trend_up = price > self.sma200[-1]
        trend_down = price < self.sma200[-1]

        current_bar = len(self.data) - 1

        # Reset expired breakouts
        # 🌙 Moon Dev Optimization: Extended breakout window to 5 bars to capture more valid post-squeeze moves without missing setups
        if self.last_long_breakout >= 0 and current_bar - self.last_long_breakout > 5:
            self.last_long_breakout = -100
            self.long_breakout_low = None
            print("⏰ Long breakout window expired, resetting")
        if self.last_short_breakout >= 0 and current_bar - self.last_short_breakout > 5:
            self.last_short_breakout = -100
            self.short_breakout_high = None
            print("⏰ Short breakout window expired, resetting")

        # Detect new breakouts
        # 🌙 Moon Dev Optimization: Tightened squeeze threshold to 0.08 for higher-quality, lower-noise breakout signals
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
        # 🌙 Moon Dev Optimization: Added RSI >50 and ADX >20 filters for better momentum and trend confirmation, reducing false entries
        if (self.last_long_breakout >= 0 and bars_since_long <= 5 and bull_cross and vol_rising and trend_up and
            not self.position and self.long_breakout_low is not None and self.rsi[-1] > 50 and self.adx[-1] > 20):
            sl = self.long_breakout_low - self.atr[-1]
            entry = price
            risk = entry - sl
            if risk > 0:
                # 🌙 Moon Dev Optimization: Increased risk per trade to 1.5% for higher compounding potential while keeping risk managed
                risk_amount = self.equity * 0.015
                pos_size = risk_amount / risk
                # 🌙 Moon Dev Optimization: Use float for fractional positions to improve precision and realism in sizing
                pos_size = float(pos_size)
                # 🌙 Moon Dev Optimization: Improved RR to 1:3 for capturing larger moves in volatile BTC, boosting returns
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
        # 🌙 Moon Dev Optimization: Added RSI <50 and ADX >20 filters for better momentum and trend confirmation, reducing false entries
        if (self.last_short_breakout >= 0 and bars_since_short <= 5 and bear_cross and vol_rising and trend_down and
            not self.position and self.short_breakout_high is not None and self.rsi[-1] < 50 and self.adx[-1] > 20):
            sl = self.short_breakout_high + self.atr[-1]
            entry = price
            risk = sl - entry
            if risk > 0:
                # 🌙 Moon Dev Optimization: Increased risk per trade to 1.5% for higher compounding potential while keeping risk managed
                risk_amount = self.equity * 0.015
                pos_size = risk_amount / risk
                # 🌙 Moon Dev Optimization: Use float for fractional positions to improve precision and realism in sizing
                pos_size = float(pos_size)
                # 🌙 Moon Dev Optimization: Improved RR to 1:3 for capturing larger moves in volatile BTC, boosting returns
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
            # 🌙 Moon Dev Optimization: Relaxed bandwidth exit to >0.25 to allow winners more room in expanding volatility, improving return capture
            if bandwidth > 0.25:
                self.position.close()
                print(f"🌙 Bandwidth expanded to {bandwidth:.4f}, exiting position 💥")
                self._reset_pos()
                return
            if self.position.is_long:
                # Trailing stop after 1:1
                favorable_move = price - entry_price
                if favorable_move >= self.initial_risk:
                    new_sl = max(self.sl, self.bb_middle[-1])
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
                    new_sl = min(self.sl, self.bb_middle[-1])
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