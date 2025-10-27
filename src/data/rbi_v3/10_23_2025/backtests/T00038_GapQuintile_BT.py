from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import pandas as pd
import numpy as np
import talib
from collections import deque

def clean_data(path):
    data = pd.read_csv(path, parse_dates=['datetime'], index_col='datetime')
    data.columns = data.columns.str.strip().str.lower()
    data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
    data.columns = [col.capitalize() for col in data.columns]
    data = data.resample('D').agg({
        'Open': 'first',
        'High': 'max',
        'Low': 'min',
        'Close': 'last',
        'Volume': 'sum'
    }).dropna()
    return data

class GapQuintile(Strategy):
    window = 252
    min_window = 126
    risk_pct = 0.01
    stop_mult = 1.5
    tp_mult = 3.0
    vol_mult = 1.5

    def init(self):
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=10)
        self.volume_sma = self.I(talib.SMA, self.data.Volume, timeperiod=20)
        self.past_gaps = deque(maxlen=self.window)

    def calculate_size(self, stop_distance):
        if stop_distance <= 0:
            return 1000
        risk_amount = self.equity * self.risk_pct
        size = risk_amount / stop_distance
        return max(1, int(round(size)))

    def next(self):
        if len(self.data) < 20:
            return
        if np.isnan(self.atr[-1]) or np.isnan(self.volume_sma[-1]):
            return
        prev_close = self.data.Close[-2]
        if np.isnan(prev_close) or prev_close == 0:
            return
        current_open = self.data.Open[-1]
        gap_abs = current_open - prev_close
        atr = self.atr[-1]
        if atr <= 0:
            return
        norm_gap = gap_abs / atr

        if len(self.past_gaps) >= self.min_window:
            past_list = list(self.past_gaps)
            upper_th = np.percentile(past_list, 80)
            lower_th = np.percentile(past_list, 20)
        else:
            upper_th = 0.5
            lower_th = -0.5

        volume_confirm = self.data.Volume[-1] > self.vol_mult * self.volume_sma[-1]

        long_signal = (norm_gap > upper_th) and volume_confirm
        short_signal = (norm_gap < lower_th) and volume_confirm
        no_signal = not long_signal and not short_signal

        entry_price = current_open
        stop_distance = self.stop_mult * atr
        size = self.calculate_size(stop_distance)

        if no_signal and self.position:
            self.position.close()
            direction = 'long' if self.position.is_long else 'short'
            print(f"🌙 Moon Dev: Exiting {direction} position - signal reversal or no momentum 📊 at {self.data.index[-1]} ✨")

        if long_signal and not self.position.is_long:
            if self.position.is_short:
                self.position.close()
            sl = entry_price - stop_distance
            tp = entry_price + (self.tp_mult * atr)
            self.buy(size=size, sl=sl, tp=tp)
            print(f"🌙 Moon Dev: Long entry on gap up momentum! 🚀 Norm Gap: {norm_gap:.3f} > {upper_th:.3f}, Volume Confirm: ✅, Size: {size}, Entry: {entry_price:.2f}, SL: {sl:.2f}, TP: {tp:.2f} at {self.data.index[-1]} 🌙")

        if short_signal and not self.position.is_short:
            if self.position.is_long:
                self.position.close()
            sl = entry_price + stop_distance
            tp = entry_price - (self.tp_mult * atr)
            self.sell(size=size, sl=sl, tp=tp)
            print(f"🌙 Moon Dev: Short entry on gap down momentum! 📉 Norm Gap: {norm_gap:.3f} < {lower_th:.3f}, Volume Confirm: ✅, Size: {size}, Entry: {entry_price:.2f}, SL: {sl:.2f}, TP: {tp:.2f} at {self.data.index[-1]} 🌙")

        self.past_gaps.append(norm_gap)

path = '/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv'
data = clean_data(path)
bt = Backtest(data, GapQuintile, cash=1000000, commission=0.001, exclusive_orders=True)
stats = bt.run()
print(stats)