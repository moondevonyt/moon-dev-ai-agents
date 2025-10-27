import pandas as pd
import numpy as np
import talib
from backtesting import Backtest, Strategy

path = '/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv'

data = pd.read_csv(path)
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data = data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
})
data = data.set_index(pd.to_datetime(data['datetime']))
data = data.drop(columns=['datetime'])

class AdaptiveKaufman(Strategy):
    kama_period = 10
    fast = 2
    slow = 30
    vol_short = 5
    vol_long = 20
    atr_period = 14
    avg_atr_period = 20
    risk_pct = 0.01
    sl_mult = 1.5
    trail_start = 1.0
    trail_offset = 1.0
    slope_periods = 3
    vol_osc_threshold = 0.5

    def init(self):
        self.stop_loss = None
        self.kama = self.I(talib.KAMA, self.data.Close, timeperiod=self.kama_period, fast=self.fast, slow=self.slow)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=self.atr_period)
        self.avg_atr = self.I(talib.SMA, self.atr, timeperiod=self.avg_atr_period)
        self.vol_short_ma = self.I(talib.SMA, self.data.Volume, timeperiod=self.vol_short)
        self.vol_long_ma = self.I(talib.SMA, self.data.Volume, timeperiod=self.vol_long)

    def next(self):
        close = self.data.Close[-1]
        kama = self.kama[-1]
        atr = self.atr[-1]
        avg_atr = self.avg_atr[-1]
        vol_short = self.vol_short_ma[-1]
        vol_long = self.vol_long_ma[-1]
        vol_osc = (vol_short - vol_long) / vol_long if vol_long > 0 else 0

        if len(self.kama) >= self.slope_periods + 1:
            kama_slope_up = self.kama[-1] > self.kama[-self.slope_periods]
            kama_slope_down = self.kama[-1] < self.kama[-self.slope_periods]
        else:
            kama_slope_up = kama_slope_down = False

        atr_expanding = atr > 2 * avg_atr
        vol_adjust = 0.5 if atr > 1.5 * avg_atr else 1.0

        if not self.position:
            # Long entry
            if close > kama and vol_osc > 0 and kama_slope_up and not atr_expanding:
                risk_amount = self.risk_pct * self.equity
                stop_distance = self.sl_mult * atr
                size = int(round((risk_amount / stop_distance) * vol_adjust))
                sl_price = close - stop_distance
                print(f"🌙 Moon Dev: Long signal! Price: {close:.2f}, KAMA: {kama:.2f}, Vol Osc: {vol_osc:.3f}, ATR: {atr:.2f}, Size: {size:.4f}")
                self.buy(size=size)
                self.stop_loss = sl_price
                print(f"🚀 Entering long at {close:.2f}, SL {sl_price:.2f}, Size {size:.4f} BTC ✨")

            # Short entry
            elif close < kama and vol_osc < 0 and kama_slope_down and not atr_expanding:
                risk_amount = self.risk_pct * self.equity
                stop_distance = self.sl_mult * atr
                size = int(round((risk_amount / stop_distance) * vol_adjust))
                sl_price = close + stop_distance
                print(f"🌙 Moon Dev: Short signal! Price: {close:.2f}, KAMA: {kama:.2f}, Vol Osc: {vol_osc:.3f}, ATR: {atr:.2f}, Size: {size:.4f}")
                self.sell(size=size)
                self.stop_loss = sl_price
                print(f"🔻 Entering short at {close:.2f}, SL {sl_price:.2f}, Size {size:.4f} BTC ✨")

        if self.position:
            entry_price = self.trades[-1].entry_price
            if self.position.is_long:
                # Trailing stop
                profit = close - entry_price
                if profit > self.trail_start * atr:
                    new_sl = max(self.stop_loss, self.kama[-1] - self.trail_offset * atr)
                    self.stop_loss = new_sl

                # Check SL hit
                if close < self.stop_loss:
                    self.position.close()
                    print(f"🌙 Moon Dev: Long SL hit at {close:.2f}, SL was {self.stop_loss:.2f} 💥")
                    self.stop_loss = None
                    return

                # Exit on KAMA cross
                if close < self.kama[-1]:
                    self.position.close()
                    print(f"🌙 Moon Dev: Exiting long on KAMA cross at {close:.2f} 😌")
                    self.stop_loss = None
                    return

                # Emergency exit
                if vol_osc < -self.vol_osc_threshold:
                    self.position.close()
                    print(f"⚠️ Emergency exit long on vol osc {vol_osc:.3f} 🚨")
                    self.stop_loss = None
                    return

            elif self.position.is_short:
                # Trailing stop
                profit = entry_price - close
                if profit > self.trail_start * atr:
                    new_sl = min(self.stop_loss, self.kama[-1] + self.trail_offset * atr)
                    self.stop_loss = new_sl

                # Check SL hit
                if close > self.stop_loss:
                    self.position.close()
                    print(f"🌙 Moon Dev: Short SL hit at {close:.2f}, SL was {self.stop_loss:.2f} 💥")
                    self.stop_loss = None
                    return

                # Exit on KAMA cross
                if close > self.kama[-1]:
                    self.position.close()
                    print(f"🌙 Moon Dev: Exiting short on KAMA cross at {close:.2f} 😌")
                    self.stop_loss = None
                    return

                # Emergency exit
                if vol_osc > self.vol_osc_threshold:
                    self.position.close()
                    print(f"⚠️ Emergency exit short on vol osc {vol_osc:.3f} 🚨")
                    self.stop_loss = None
                    return

bt = Backtest(data, AdaptiveKaufman, cash=1000000, commission=0.001, exclusive_orders=True)
stats = bt.run()
print(stats)