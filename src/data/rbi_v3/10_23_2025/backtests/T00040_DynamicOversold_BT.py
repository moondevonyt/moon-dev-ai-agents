from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import pandas as pd
import talib
import numpy as np

# Load and prepare data
path = '/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv'
data = pd.read_csv(path, index_col=0, parse_dates=True)
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data = data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
})
print(f"🌙 Moon Dev: Data loaded with shape {data.shape} ✨")

class DynamicOversold(Strategy):
    rsi_period = 20
    sma_short = 5
    ema_long = 50
    bb_period = 20
    bb_std = 2
    risk_pct_full = 0.02
    risk_pct_partial = 0.015
    stop_pct = 0.02
    swing_period = 5
    width_period = 20
    time_exit_bars = 10
    max_trades = 5  # Approximate max exposure

    def init(self):
        print(f"🌙 Moon Dev: Initializing DynamicOversold strategy 🚀")
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=self.rsi_period)
        self.sma5 = self.I(talib.SMA, self.data.Close, timeperiod=self.sma_short)
        self.ema50 = self.I(talib.EMA, self.data.Close, timeperiod=self.ema_long)
        self.bb_upper, self.bb_middle, self.bb_lower = self.I(
            talib.BBANDS, self.data.Close, timeperiod=self.bb_period,
            nbdevup=self.bb_std, nbdevdn=self.bb_std, matype=0
        )
        self.bb_width = self.bb_upper - self.bb_lower
        self.avg_width = self.I(talib.SMA, self.bb_width, timeperiod=self.width_period)
        self.swing_low = self.I(talib.MIN, self.data.Low, timeperiod=self.swing_period)
        print(f"🌙 Moon Dev: Indicators initialized successfully ✨")

    def next(self):
        if len(self.rsi) < self.ema_long:
            return

        # Calculate current ratio
        current_ratio = ((self.data.Close[-1] - self.bb_lower[-1]) / (self.bb_upper[-1] - self.bb_lower[-1])) * 100

        # Volatility adjustment
        vol_adjust = 1.0
        if self.bb_width[-1] > 2 * self.avg_width[-1]:
            vol_adjust = 0.5
            print(f"🌙 Moon Dev: High volatility detected, adjusting size by {vol_adjust} 🛡️")

        # Invalidation for existing position
        if self.position:
            if self.sma5[-1] < self.ema50[-1]:
                self.sell()
                print(f"🌙 Moon Dev: Trend invalidation exit at {self.data.Close[-1]} ❌")
                return

            # Time-based exit
            bars_in_trade = len(self.data) - self.position.entry_bar
            if bars_in_trade > self.time_exit_bars:
                self.sell()
                print(f"🌙 Moon Dev: Time-based exit after {bars_in_trade} bars at {self.data.Close[-1]} ⏰")
                return

            # Profit target: partial exit 50%
            if (self.rsi[-1] >= 70 or self.data.Close[-1] >= self.bb_upper[-1]) and self.position.size > 0:
                partial_size = self.position.size / 2
                self.sell(size=partial_size)
                print(f"🌙 Moon Dev: Partial profit exit (50%) at {self.data.Close[-1]}, ratio {current_ratio:.1f}% 💰")
                return

            # Trailing stop for remaining position
            if self.data.Close[-1] < self.sma5[-1]:
                self.sell()
                print(f"🌙 Moon Dev: Trailing stop hit at {self.data.Close[-1]} 📉")
                return

            # Dynamic stop adjustment
            if current_ratio > 80:
                new_sl = max(self.position.sl, self.bb_middle[-1])
                self.position.sl = new_sl
                print(f"🌙 Moon Dev: Tightened stop to middle BB {new_sl} at ratio {current_ratio:.1f}% 🔒")

        # Entry logic
        if (self.rsi[-1] < 30 and
            self.sma5[-1] > self.ema50[-1] and
            current_ratio <= 40 and
            len(self.trades) < self.max_trades):

            # Determine risk pct based on ratio
            if current_ratio < 20:
                risk_pct = self.risk_pct_full
                size_scale = 1.0
            elif current_ratio < 40:
                risk_pct = self.risk_pct_partial
                size_scale = 0.75  # 50-75%, approx
            else:
                return

            risk_pct *= vol_adjust * size_scale

            # Calculate stop price
            recent_low = min(self.swing_low[-1], self.bb_lower[-1])
            stop_price = recent_low * (1 - self.stop_pct)

            entry_price = self.data.Close[-1]
            risk_per_unit = entry_price - stop_price

            if risk_per_unit <= 0:
                print(f"🌙 Moon Dev: Invalid stop, skipping entry ⚠️")
                return

            risk_amount = self.equity * risk_pct
            size = risk_amount / risk_per_unit
            size = int(round(size))  # Ensure integer units

            if size > 0:
                self.buy(size=size, sl=stop_price)
                print(f"🌙 Moon Dev: Long entry at {entry_price}, size {size}, stop {stop_price}, ratio {current_ratio:.1f}%, risk {risk_pct*100}% 🚀")

bt = Backtest(data, DynamicOversold, cash=1000000, commission=0.001, exclusive_orders=False)
stats = bt.run()
print(stats)