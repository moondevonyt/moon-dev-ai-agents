import pandas as pd
import talib
import numpy as np
from backtesting import Backtest, Strategy
from backtesting.lib import crossover

path = '/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv'
data = pd.read_csv(path)
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data['date'] = pd.to_datetime(data['datetime'])
data = data.drop('datetime', axis=1)
data = data.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'})
data.set_index('date', inplace=True)
data = data[['Open', 'High', 'Low', 'Close', 'Volume']]

class DynamicHarmonics(Strategy):
    bb_period = 20
    bb_std = 2
    adx_period = 14
    atr_period = 14
    swing_period = 10
    risk_per_trade = 0.01
    rr_ratio = 2
    squeeze_threshold = 0.8
    adx_threshold = 20
    lookback = 50

    def init(self):
        close = self.data.Close
        high = self.data.High
        low = self.data.Low
        self.bb = self.I(talib.BBANDS, close, timeperiod=self.bb_period, nbdevup=self.bb_std, nbdevdn=self.bb_std, matype=0)
        self.bb_upper = self.bb[0]
        self.bb_middle = self.bb[1]
        self.bb_lower = self.bb[2]
        self.bb_width = self.I(lambda u, l, m: (u - l) / m, self.bb_upper, self.bb_lower, self.bb_middle)
        self.avg_bb_width = self.I(talib.SMA, self.bb_width, timeperiod=20)
        self.adx = self.I(talib.ADX, high, low, close, timeperiod=self.adx_period)
        self.pdi = self.I(talib.PLUS_DI, high, low, close, timeperiod=self.adx_period)
        self.mdi = self.I(talib.MINUS_DI, high, low, close, timeperiod=self.adx_period)
        self.atr = self.I(talib.ATR, high, low, close, timeperiod=self.atr_period)
        self.swing_high = self.I(talib.MAX, high, timeperiod=self.swing_period)
        self.swing_low = self.I(talib.MIN, low, timeperiod=self.swing_period)
        self.moon_dev_entry_long = 0
        self.moon_dev_entry_short = 0
        self.moon_dev_exit_long = 0
        self.moon_dev_exit_short = 0

    def next(self):
        if len(self.data) < self.lookback:
            return

        current_idx = len(self.data) - 1
        close = self.data.Close[-1]
        high = self.data.High[-1]
        low = self.data.Low[-1]
        prev_close = self.data.Close[-2]

        # Approximate BB squeeze
        is_squeeze = self.bb_width[-1] < self.squeeze_threshold * self.avg_bb_width[-1]

        # ADX conditions
        adx_rising = self.adx[-1] > self.adx[-2]
        adx_strong = self.adx[-1] > self.adx_threshold
        pdi_above_mdi = self.pdi[-1] > self.mdi[-1]
        mdi_above_pdi = self.mdi[-1] > self.pdi[-1]

        # Approximate Harmonic Pattern completion via price touching BB and simple swing retracement proxy
        # For long: price near lower BB, and recent low near 0.618 retrace of prior swing
        recent_swing_high_idx = None
        recent_swing_low_idx = None
        for i in range(max(0, current_idx - self.lookback), current_idx):
            if high == self.swing_high[i] and (i == 0 or self.data.High[i-1] < self.data.High[i]):
                recent_swing_high_idx = i
                break
        for i in range(max(0, current_idx - self.lookback), current_idx):
            if low == self.swing_low[i] and (i == 0 or self.data.Low[i-1] > self.data.Low[i]):
                recent_swing_low_idx = i
                break

        harmonic_long_approx = False
        harmonic_short_approx = False
        if recent_swing_high_idx is not None and recent_swing_low_idx is not None and recent_swing_high_idx > recent_swing_low_idx:
            xa_range = self.data.High[recent_swing_high_idx] - self.data.Low[recent_swing_low_idx]
            retrace_level = self.data.Low[recent_swing_low_idx] + 0.618 * xa_range
            if abs(close - retrace_level) / close < 0.01 and close <= self.bb_lower[-1]:
                harmonic_long_approx = True
        if recent_swing_low_idx is not None and recent_swing_high_idx is not None and recent_swing_low_idx > recent_swing_high_idx:
            xa_range = self.data.Low[recent_swing_low_idx] - self.data.High[recent_swing_high_idx]
            retrace_level = self.data.High[recent_swing_high_idx] + 0.618 * xa_range
            if abs(close - retrace_level) / close < 0.01 and close >= self.bb_upper[-1]:
                harmonic_short_approx = True

        # Additional filter: BB expansion starting for entry confirmation
        bb_expanding_up = self.bb_upper[-1] > self.bb_upper[-2] and close > self.bb_middle[-1]
        bb_expanding_down = self.bb_lower[-1] < self.bb_lower[-2] and close < self.bb_middle[-1]

        # Long entry conditions (approximating harmonic with touch + fib proxy)
        long_condition = (
            not self.position,
            harmonic_long_approx or (close <= self.bb_lower[-1] and is_squeeze),
            is_squeeze or bb_expanding_up,
            adx_strong and adx_rising and pdi_above_mdi
        )
        if all(long_condition):
            entry_price = close
            sl = min(self.bb_lower[-1], self.data.Low[recent_swing_low_idx] if recent_swing_low_idx else self.bb_lower[-1]) - self.atr[-1]
            sl_distance = entry_price - sl
            risk_amount = self.risk_per_trade * self.equity
            position_size = risk_amount / sl_distance
            position_size = int(round(position_size))
            self.buy(size=position_size, sl=sl, tp=entry_price + self.rr_ratio * sl_distance)
            self.moon_dev_entry_long += 1
            self.log(f'🌙 Moon Dev: 🚀 Long Entry at {entry_price:.2f}! Size: {position_size}, SL: {sl:.2f}, TP: {self.tp:.2f} ✨')

        # Short entry conditions
        short_condition = (
            not self.position,
            harmonic_short_approx or (close >= self.bb_upper[-1] and is_squeeze),
            is_squeeze or bb_expanding_down,
            adx_strong and adx_rising and mdi_above_pdi
        )
        if all(short_condition):
            entry_price = close
            sl = max(self.bb_upper[-1], self.data.High[recent_swing_high_idx] if recent_swing_high_idx else self.bb_upper[-1]) + self.atr[-1]
            sl_distance = sl - entry_price
            risk_amount = self.risk_per_trade * self.equity
            position_size = risk_amount / sl_distance
            position_size = int(round(position_size))
            self.sell(size=position_size, sl=sl, tp=entry_price - self.rr_ratio * sl_distance)
            self.moon_dev_entry_short += 1
            self.log(f'🌙 Moon Dev: 🚀 Short Entry at {entry_price:.2f}! Size: {position_size}, SL: {sl:.2f}, TP: {self.tp:.2f} ✨')

        # Early exit if ADX weakens
        if self.position and self.adx[-1] < self.adx_threshold:
            self.position.close()
            if self.position.is_long:
                self.moon_dev_exit_long += 1
                self.log('🌙 Moon Dev: 😔 Early Long Exit - ADX Weakened')
            else:
                self.moon_dev_exit_short += 1
                self.log('🌙 Moon Dev: 😔 Early Short Exit - ADX Weakened')

        # Debug prints
        self.log(f'🌙 Moon Dev Debug: ADX={self.adx[-1]:.2f} (Rising: {adx_rising}), Squeeze: {is_squeeze}, PDI>{self.pdi[-1]:.2f}>{self.mdi[-1]:.2f}, Close: {close:.2f} vs BB Lower: {self.bb_lower[-1]:.2f} Upper: {self.bb_upper[-1]:.2f} 🚀')

bt = Backtest(data, DynamicHarmonics, cash=1000000, commission=0.002, exclusive_orders=True)
stats = bt.run()
print(stats)
print(stats._strategy)