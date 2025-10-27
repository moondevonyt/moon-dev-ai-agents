import pandas as pd
import talib
from backtesting import Backtest, Strategy
import numpy as np

# Load and prepare data
path = '/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv'
data = pd.read_csv(path, parse_dates=['datetime'])

# Clean column names
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])

# Ensure proper column mapping
data = data.rename(columns={
    'datetime': 'Datetime',
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
})

# Set datetime as index
data = data.set_index('Datetime')

class SqueezeBreakout(Strategy):
    bb_period = 20
    bb_std = 2.0
    kc_period = 20
    kc_mult = 1.5
    vol_short = 14
    vol_long = 28
    lookback_squeeze = 12
    risk_per_trade = 0.01
    rr_ratio = 2.0

    def init(self):
        close = self.data.Close
        high = self.data.High
        low = self.data.Low
        volume = self.data.Volume

        # Bollinger Bands
        bb_upper, bb_middle, bb_lower = self.I(talib.BBANDS, close, timeperiod=self.bb_period,
                                               nbdevup=self.bb_std, nbdevdn=self.bb_std, matype=0)

        # ATR for Keltner and stops
        atr = self.I(talib.ATR, high, low, close, timeperiod=self.kc_period)

        # EMA for Keltner middle
        ema = self.I(talib.EMA, close, timeperiod=self.kc_period)

        # Keltner Channels
        kc_mult_local = self.kc_mult
        self.kc_upper = self.I(lambda e, a: e + kc_mult_local * a, ema, atr)
        self.kc_lower = self.I(lambda e, a: e - kc_mult_local * a, ema, atr)

        # BB Width
        def bb_width_func(upper, lower):
            return upper - lower
        self.bb_width = self.I(bb_width_func, bb_upper, bb_lower)

        # Volume Oscillator (short SMA - long SMA)
        vol_sma_short = self.I(talib.SMA, volume, timeperiod=self.vol_short)
        vol_sma_long = self.I(talib.SMA, volume, timeperiod=self.vol_long)
        def vol_osc_func(short, long):
            return short - long
        self.vol_osc = self.I(vol_osc_func, vol_sma_short, vol_sma_long)

        # Squeeze condition: BB inside KC
        def squeeze_func(bb_u, bb_l, kc_u, kc_l):
            return (bb_u <= kc_u) & (bb_l >= kc_l)
        self.squeeze = self.I(squeeze_func, bb_upper, bb_lower, self.kc_upper, self.kc_lower)

        # Store indicators for access
        self.bb_upper = bb_upper
        self.bb_lower = bb_lower
        self.bb_middle = bb_middle
        self.atr = atr
        self.sma20 = self.I(talib.SMA, close, timeperiod=20)  # For bias

        self.i = -1

    def next(self):
        self.i += 1
        if self.i < self.lookback_squeeze + self.kc_period:
            return

        current_price = self.data.Close[self.i]

        squeeze_val = self.squeeze[self.i]
        current_squeeze = bool(squeeze_val) if not pd.isna(squeeze_val) else False

        prev_squeeze_val = self.squeeze[self.i - 1] if self.i > 0 else np.nan
        prev_squeeze = bool(prev_squeeze_val) if not pd.isna(prev_squeeze_val) else False

        current_vol_osc = self.vol_osc[self.i]
        current_bb_width = self.bb_width[self.i]
        bb_widths = self.bb_width[max(0, self.i - self.lookback_squeeze + 1): self.i + 1]
        min_width = np.nanmin(bb_widths)
        is_lowest_width = (not pd.isna(current_bb_width) and not pd.isna(min_width) and
                           np.isclose(current_bb_width, min_width, atol=1e-10))

        # Check for squeeze end and low width
        squeeze_ended = prev_squeeze and not current_squeeze and is_lowest_width
        if squeeze_ended:
            print(f"🌙 Moon Dev: Squeeze ended detected at {current_price:.2f}, vol_osc {current_vol_osc:.2f}, bb_width {current_bb_width:.4f} 🔍✨")

        # No position
        if not self.position:
            # Long entry
            if squeeze_ended and current_price > self.bb_upper[self.i] and current_vol_osc > 0 and current_price > self.bb_middle[self.i]:
                entry_price = current_price
                sl_price = self.bb_lower[self.i]  # Beyond opposite BB
                risk_distance = entry_price - sl_price
                if risk_distance > 0:
                    equity = self.equity
                    risk_amount = self.risk_per_trade * equity
                    desired_size = risk_amount / risk_distance
                    max_affordable_size = self._broker.cash / entry_price
                    position_size = min(desired_size, max_affordable_size)
                    size = int(round(position_size))
                    if size > 0:
                        tp_price = entry_price + (self.rr_ratio * risk_distance)
                        self.buy(size=size, sl=sl_price, tp=tp_price)
                        print(f"🌙 Moon Dev: Squeeze Breakout LONG entry at {entry_price:.2f}, size {size}, SL {sl_price:.2f}, TP {tp_price:.2f} 🚀✨")
                    else:
                        print(f"🌙 Moon Dev: LONG signal but size {size} <=0, skipping 📉")

            # Short entry
            elif squeeze_ended and current_price < self.bb_lower[self.i] and current_vol_osc < 0 and current_price < self.bb_middle[self.i]:
                entry_price = current_price
                sl_price = self.bb_upper[self.i]  # Beyond opposite BB
                risk_distance = sl_price - entry_price
                if risk_distance > 0:
                    equity = self.equity
                    risk_amount = self.risk_per_trade * equity
                    position_size = risk_amount / risk_distance
                    size = int(round(position_size))
                    if size > 0:
                        tp_price = entry_price - (self.rr_ratio * risk_distance)
                        self.sell(size=size, sl=sl_price, tp=tp_price)
                        print(f"🌙 Moon Dev: Squeeze Breakout SHORT entry at {entry_price:.2f}, size {size}, SL {sl_price:.2f}, TP {tp_price:.2f} 🚀✨")
                    else:
                        print(f"🌙 Moon Dev: SHORT signal but size {size} <=0, skipping 📉")

        # Early exit if re-squeeze
        elif self.position and current_squeeze:
            self.position.close()
            print(f"🌙 Moon Dev: Early exit due to re-squeeze at {current_price:.2f} 😔")

# Run backtest
bt = Backtest(data, SqueezeBreakout, cash=1000000, commission=.002)
stats = bt.run()
print(stats)