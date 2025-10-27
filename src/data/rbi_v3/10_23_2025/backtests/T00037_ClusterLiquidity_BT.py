import pandas as pd
import numpy as np
import talib
from backtesting import Backtest, Strategy

path = "/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv"
data = pd.read_csv(path, index_col=0, parse_dates=True)
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data = data.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'})

class ClusterLiquidity(Strategy):
    lookback = 100
    bins = 20
    buffer_pct = 0.002
    rr = 2
    trail_after = 1.0
    trail_distance = 1.0
    max_bars = 10
    risk_per_trade = 0.01

    def init(self):
        hi = self.data.High
        lo = self.data.Low
        cl = self.data.Close
        volu = self.data.Volume

        self.atr = self.I(talib.ATR, hi, lo, cl, timeperiod=14)
        self.avg_atr = self.I(talib.SMA, self.atr, timeperiod=20)
        self.vol_sma = self.I(talib.SMA, volu, timeperiod=10)
        bb_upper, bb_mid, bb_lower = self.I(talib.BBANDS, cl, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)
        self.bb_width = (bb_upper - bb_lower) / bb_mid
        self.avg_bb_width = self.I(talib.SMA, self.bb_width, timeperiod=20)
        self.rsi = self.I(talib.RSI, cl, timeperiod=14)
        self.ema20 = self.I(talib.EMA, cl, timeperiod=20)

        n = len(self.data)
        cluster_high = pd.Series(np.nan, index=self.data.index)
        cluster_low = pd.Series(np.nan, index=self.data.index)
        for i in range(self.lookback, n):
            window = self.data.iloc[i - self.lookback:i]
            p_min = window.Low.min()
            p_max = window.High.max()
            if p_max == p_min:
                continue
            bin_edges = np.linspace(p_min, p_max, self.bins + 1)
            vol_profile = np.zeros(self.bins)
            for j, (_, row) in enumerate(window.iterrows()):
                price = row['Close']
                v = row['Volume']
                bin_idx = np.digitize(price, bin_edges) - 1
                if 0 <= bin_idx < self.bins:
                    vol_profile[bin_idx] += v
            if vol_profile.sum() == 0:
                continue
            poc_idx = np.argmax(vol_profile)
            total_vol = vol_profile.sum()
            target = 0.7 * total_vol
            cum = vol_profile[poc_idx]
            low_idx = poc_idx
            high_idx = poc_idx
            while cum < target and (low_idx > 0 or high_idx < self.bins - 1):
                left_vol = vol_profile[low_idx - 1] if low_idx > 0 else 0
                right_vol = vol_profile[high_idx + 1] if high_idx < self.bins - 1 else 0
                if left_vol >= right_vol and low_idx > 0:
                    low_idx -= 1
                    cum += vol_profile[low_idx]
                elif high_idx < self.bins - 1:
                    high_idx += 1
                    cum += vol_profile[high_idx]
                else:
                    break
            bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
            cluster_low.iloc[i] = bin_centers[low_idx]
            cluster_high.iloc[i] = bin_centers[high_idx]
        self.data['cluster_high'] = cluster_high
        self.data['cluster_low'] = cluster_low
        self.entry_bar = None

    def next(self):
        if len(self.data) < self.lookback:
            return
        ch = self.data.cluster_high[-1]
        clu = self.data.cluster_low[-1]
        if pd.isna(ch) or pd.isna(clu):
            return
        curr_atr = self.atr[-1]
        avg_a = self.avg_atr[-1]
        curr_vol = self.data.Volume[-1]
        avg_v = self.vol_sma[-1]
        bb_w = self.bb_width[-1]
        avg_bw = self.avg_bb_width[-1]
        r = self.rsi[-1]
        buffer = self.data.Close[-1] * self.buffer_pct
        vol_surge = curr_vol > 1.5 * avg_v
        atr_expand = curr_atr > 1.5 * avg_a
        bb_expand = bb_w > 1.5 * avg_bw

        if self.position:
            current_bar = len(self.data) - 1
            # Time-based exit
            if self.entry_bar is not None and (current_bar - self.entry_bar > self.max_bars):
                self.position.close()
                print(f"🌙⏰ Time exit after {self.max_bars} bars")
                self.entry_bar = None
                return
            # Invalidate if re-enters cluster
            if self.position.is_long and self.data.Close[-1] < ch:
                self.position.close()
                print(f"🌙❌ Invalidate long: price re-entered cluster at {self.data.Close[-1]}")
                self.entry_bar = None
                return
            if not self.position.is_long and self.data.Close[-1] > clu:
                self.position.close()
                print(f"🌙❌ Invalidate short: price re-entered cluster at {self.data.Close[-1]}")
                self.entry_bar = None
                return
            # Partial exit at 1:1
            entry_p = self.position.entry_price
            sl_p = self.position.sl
            if self.position.is_long:
                risk = entry_p - sl_p
                unreal = self.data.Close[-1] - entry_p
                if unreal >= risk:
                    half = abs(self.position.size) / 2
                    if half >= 1:
                        self.position.close(size=half)
                        print(f"🌙✨ Partial close long at 1:1 RR, remaining size {abs(self.position.size)}")
            else:
                risk = sl_p - entry_p
                unreal = entry_p - self.data.Close[-1]
                if unreal >= risk:
                    half = abs(self.position.size) / 2
                    if half >= 1:
                        self.position.close(size=half)
                        print(f"🌙✨ Partial close short at 1:1 RR, remaining size {abs(self.position.size)}")
            # Trailing stop
            if self.position.is_long:
                unreal = self.data.Close[-1] - entry_p
                if unreal > self.trail_after * curr_atr:
                    trail_sl = self.ema20[-1] - self.trail_distance * curr_atr
                    if trail_sl > sl_p:
                        pos_size = abs(self.position.size)
                        tp_p = self.position.tp
                        self.position.close()
                        self.buy(size=pos_size, sl=trail_sl, tp=tp_p)
                        print(f"🌙🔄 Trailing stop updated for long to {trail_sl}")
                        self.entry_bar = current_bar
            else:
                unreal = entry_p - self.data.Close[-1]
                if unreal > self.trail_after * curr_atr:
                    trail_sl = self.ema20[-1] + self.trail_distance * curr_atr
                    if trail_sl < sl_p:
                        pos_size = abs(self.position.size)
                        tp_p = self.position.tp
                        self.position.close()
                        self.sell(size=pos_size, sl=trail_sl, tp=tp_p)
                        print(f"🌙🔄 Trailing stop updated for short to {trail_sl}")
                        self.entry_bar = current_bar

        if not self.position:
            prev_close = self.data.Close[-2]
            curr_close = self.data.Close[-1]
            # Long entry
            if (prev_close <= ch and curr_close > ch + buffer and
                vol_surge and atr_expand and bb_expand and r > 50):
                sl_price = clu - curr_atr
                stop_distance = curr_close - sl_price
                if stop_distance <= 0:
                    return
                equity = self.broker.getvalue()
                risk_amount = equity * self.risk_per_trade
                size = risk_amount / stop_distance
                size = int(round(size))
                if size < 1:
                    return
                tp_price = curr_close + self.rr * stop_distance
                self.buy(size=size, sl=sl_price, tp=tp_price)
                self.entry_bar = len(self.data) - 1
                print(f"🌙🚀 Long entry at {curr_close:.2f}, SL {sl_price:.2f}, TP {tp_price:.2f}, size {size}, cluster {clu:.2f}-{ch:.2f}")
            # Short entry
            elif (prev_close >= clu and curr_close < clu - buffer and
                  vol_surge and atr_expand and bb_expand and r < 50):
                sl_price = ch + curr_atr
                stop_distance = sl_price - curr_close
                if stop_distance <= 0:
                    return
                equity = self.broker.getvalue()
                risk_amount = equity * self.risk_per_trade
                size = risk_amount / stop_distance
                size = int(round(size))
                if size < 1:
                    return
                tp_price = curr_close - self.rr * stop_distance
                self.sell(size=size, sl=sl_price, tp=tp_price)
                self.entry_bar = len(self.data) - 1
                print(f"🌙🔻 Short entry at {curr_close:.2f}, SL {sl_price:.2f}, TP {tp_price:.2f}, size {size}, cluster {clu:.2f}-{ch:.2f}")

bt = Backtest(data, ClusterLiquidity, cash=1000000, commission=0.002, exclusive_orders=True)
stats = bt.run()
print(stats)
print(stats._strategy)