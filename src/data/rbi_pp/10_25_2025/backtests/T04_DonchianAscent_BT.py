from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import talib
import pandas as pd
import numpy as np

# Load and clean data
data = pd.read_csv('/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv', parse_dates=['datetime'], index_col='datetime')
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data = data.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'})

class DonchianAscent(Strategy):
    period = 20
    risk_percent = 0.01
    tp_multiplier = 2
    time_exit_bars = 20
    min_channel_width_pct = 0.01
    extended_multiplier = 2

    def init(self):
        self.upper = self.I(talib.MAX, self.data.High, timeperiod=self.period)
        self.lower = self.I(talib.MIN, self.data.Low, timeperiod=self.period)
        self.middle = (self.upper + self.lower) / 2
        self.avg_vol = self.I(talib.SMA, self.data.Volume, timeperiod=self.period)
        self.width = self.upper - self.lower
        self.entry_bar = None
        self.initial_sl = None
        print("🌙 Moon Dev Backtest Initialized: DonchianAscent Strategy Loaded! ✨")

    def next(self):
        current_close = self.data.Close[-1]
        current_high = self.data.High[-1]
        current_low = self.data.Low[-1]
        current_vol = self.data.Volume[-1]
        current_upper = self.upper[-1]
        current_lower = self.lower[-1]
        current_middle = self.middle[-1]
        current_width = self.width[-1]
        current_avg_vol = self.avg_vol[-1]

        if self.position:
            bars_in_trade = len(self.data) - self.entry_bar if self.entry_bar else 0
            exit_reason = ""
            should_exit = False

            # Trailing exit: close below middle
            if current_close < current_middle:
                should_exit = True
                exit_reason = "Trailing stop (middle band) hit"

            # Time-based exit
            elif bars_in_trade > self.time_exit_bars:
                should_exit = True
                exit_reason = "Time-based exit"

            if should_exit:
                self.position.close()
                print(f"🌙 Moon Dev Exit: {exit_reason} at {current_close} after {bars_in_trade} bars 🚀")
                self.entry_bar = None
                self.initial_sl = None
        else:
            # Entry conditions
            breakout = current_close > current_upper
            vol_confirm = current_vol > current_avg_vol
            channel_too_narrow = (current_width / current_close) < self.min_channel_width_pct
            extended = (current_close - current_middle) > (self.extended_multiplier * current_width)

            if breakout and vol_confirm and not channel_too_narrow and not extended:
                sl_price = current_lower
                risk_per_share = current_close - sl_price
                if risk_per_share > 0:
                    position_size = int(round((self.equity * self.risk_percent) / risk_per_share))
                    tp_price = current_close + (self.tp_multiplier * risk_per_share)

                    self.buy(size=position_size, sl=sl_price, tp=tp_price)
                    self.entry_bar = len(self.data)
                    self.initial_sl = sl_price
                    print(f"🌙 Moon Dev Long Entry: Breakout at {current_close}, size={position_size}, SL={sl_price}, TP={tp_price} ✨🚀")

# Run backtest
bt = Backtest(data, DonchianAscent, cash=1000000, commission=.002)
stats = bt.run()
print(stats)
print(stats._strategy)