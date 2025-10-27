from backtesting import Backtest, Strategy
import talib
import pandas as pd
import numpy as np

# Load and clean data
data = pd.read_csv('/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv')
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data = data.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'})
data = data.set_index(pd.to_datetime(data['datetime']))

class DonchianAscent(Strategy):
    period = 20
    risk_percent = 0.02  # 🌙 Increased from 0.01 to 0.02 for higher exposure and potential returns while keeping risk managed
    tp_multiplier = 3  # 🌙 Increased from 2 to 3 to capture larger profits on winning breakouts
    time_exit_bars = 10  # 🌙 Reduced from 20 to 10 to exit faster and reduce time in choppy conditions
    min_channel_width_pct = 0.02  # 🌙 Increased from 0.01 to 0.02 to filter out narrower, lower-quality channels and avoid noise
    extended_multiplier = 2

    def init(self):
        self.upper = self.I(talib.MAX, self.data.High, timeperiod=self.period)
        self.lower = self.I(talib.MIN, self.data.Low, timeperiod=self.period)
        self.middle = self.I(lambda: (self.upper + self.lower) / 2)
        self.avg_vol = self.I(talib.SMA, self.data.Volume, timeperiod=self.period)
        self.width = self.I(lambda: self.upper - self.lower)
        # 🌙 Added RSI for momentum confirmation to tighten entries and avoid weak breakouts
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14)
        # 🌙 Added SMA200 as a trend filter to only trade in uptrends, improving win rate
        self.sma200 = self.I(talib.SMA, self.data.Close, timeperiod=200)
        self.entry_bar = None
        print("🌙 Moon Dev Backtest Initialized: Optimized DonchianAscent Strategy Loaded! ✨")

    def next(self):
        current_close = self.data.Close[-1]
        current_high = self.data.High[-1]
        current_low = self.data.Low[-1]
        current_vol = self.data.Volume[-1]
        current_lower = self.lower[-1]
        current_middle = self.middle[-1]
        current_rsi = self.rsi[-1]
        current_sma200 = self.sma200[-1]

        prev_idx = -2 if len(self.data) > 1 else -1
        prev_upper = self.upper[prev_idx]
        prev_avg_vol = self.avg_vol[prev_idx]
        prev_width = self.width[prev_idx]
        prev_middle = self.middle[prev_idx]

        if self.position:
            bars_in_trade = len(self.data) - self.entry_bar if self.entry_bar else 0
            entry_price = self.position.avg_price

            # 🌙 Improved trailing stop: Only update SL to middle band when profitable, allowing better risk-reward by locking in gains dynamically
            if current_close > entry_price:
                new_sl = current_middle
                if new_sl > self.position.sl:
                    old_sl = self.position.sl
                    self.position.sl = new_sl
                    print(f"🌙 Moon Dev Trailing SL updated to {new_sl} from {old_sl} 🌙")

            # Time-based exit
            if bars_in_trade >= self.time_exit_bars:
                self.position.close()
                print(f"🌙 Moon Dev Exit: Time-based exit at {current_close} after {bars_in_trade} bars 🚀")
                self.entry_bar = None
        else:
            # 🌙 Entry conditions optimized: Added trend filter (above SMA200) and RSI > 55 for stronger bullish confirmation
            # Tightened volume confirmation to 1.2x average for higher conviction breakouts
            breakout = current_close > prev_upper
            vol_confirm = current_vol > (1.2 * prev_avg_vol)
            channel_too_narrow = (prev_width / current_close) < self.min_channel_width_pct
            extended = (current_close - prev_middle) > (self.extended_multiplier * prev_width)
            trend_up = current_close > current_sma200
            rsi_bullish = current_rsi > 55

            if breakout and vol_confirm and not channel_too_narrow and not extended and trend_up and rsi_bullish:
                sl_price = current_lower
                risk_per_share = current_close - sl_price
                if risk_per_share > 0:
                    position_size = int(round((self.equity * self.risk_percent) / risk_per_share))
                    tp_price = current_close + (self.tp_multiplier * risk_per_share)

                    self.buy(size=position_size, sl=sl_price, tp=tp_price)
                    self.entry_bar = len(self.data)
                    print(f"🌙 Moon Dev Long Entry: Breakout at {current_close}, size={position_size}, SL={sl_price}, TP={tp_price} ✨🚀")

# Run backtest
bt = Backtest(data, DonchianAscent, cash=1000000, commission=.002)
stats = bt.run()
print(stats)