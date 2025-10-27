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
    risk_percent = 0.015  # 🌙 Increased risk per trade slightly for higher potential returns while maintaining management
    tp_multiplier = 2.5  # 🌙 Adjusted TP multiplier for better reward:risk ratio
    time_exit_bars = 30  # 🌙 Extended time exit to allow trades more room to develop
    extended_multiplier = 2  # 🌙 Fine-tuned to avoid moderately extended moves
    atr_period = 14
    rsi_period = 14
    sma_period = 200
    vol_mult = 1.2  # 🌙 Lowered volume multiplier for more entry opportunities without sacrificing confirmation
    min_atr_mult = 1.0  # 🌙 Switched to ATR-based min channel width for volatility-adjusted filtering
    trail_bars_be = 5  # 🌙 Bars before trailing to breakeven
    trail_bars_profit = 10  # 🌙 Bars before trailing to profit lock-in

    def init(self):
        self.upper = self.I(talib.MAX, self.data.High, timeperiod=self.period)
        self.lower = self.I(talib.MIN, self.data.Low, timeperiod=self.period)
        self.middle = self.I(lambda: (self.upper + self.lower) / 2)
        self.avg_vol = self.I(talib.SMA, self.data.Volume, timeperiod=self.period)
        self.width = self.I(lambda: self.upper - self.lower)
        # 🌙 Added ATR for dynamic SL, channel filtering, and potential trailing
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=self.atr_period)
        # 🌙 Added RSI for momentum confirmation to tighten entries
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=self.rsi_period)
        # 🌙 Added SMA200 for trend filter to trade only in favorable uptrends
        self.sma200 = self.I(talib.SMA, self.data.Close, timeperiod=self.sma_period)
        self.entry_bar = None
        self.initial_sl = None
        self.entry_price = None
        self.risk_per_share = None
        print("🌙 Moon Dev Backtest Initialized: Optimized DonchianAscent with RSI, SMA200, ATR filters, and improved trailing! ✨")

    def next(self):
        current_close = self.data.Close[-1]
        current_high = self.data.High[-1]
        current_low = self.data.Low[-1]
        current_vol = self.data.Volume[-1]
        current_lower = self.lower[-1]
        current_middle = self.middle[-1]
        current_atr = self.atr[-1]

        prev_idx = -2 if len(self.data) > 1 else -1
        prev_upper = self.upper[prev_idx]
        prev_avg_vol = self.avg_vol[prev_idx]
        prev_width = self.width[prev_idx]
        prev_middle = self.middle[prev_idx]
        prev_atr = self.atr[prev_idx]

        if self.position:
            bars_in_trade = len(self.data) - self.entry_bar if self.entry_bar else 0
            should_exit = False
            exit_reason = ""

            # 🌙 Improved trailing SL logic: dynamic based on bars and profit levels for better risk management and profit locking
            trail_sl = self.initial_sl
            current_profit = current_close - self.entry_price
            if bars_in_trade >= self.trail_bars_be:
                if current_profit > self.risk_per_share:
                    trail_sl = max(trail_sl, self.entry_price)  # Move to breakeven
            if bars_in_trade >= self.trail_bars_profit:
                if current_profit > 2 * self.risk_per_share:
                    trail_sl = max(trail_sl, self.entry_price + 0.5 * self.risk_per_share)  # Lock in some profit
            if current_close < trail_sl:
                should_exit = True
                exit_reason = f"Trailing SL hit at {trail_sl:.2f}"

            if not should_exit and current_close < current_middle:
                should_exit = True
                exit_reason = "Trailing stop (middle band) hit"

            if not should_exit and bars_in_trade > self.time_exit_bars:
                should_exit = True
                exit_reason = "Time-based exit"

            if should_exit:
                self.position.close()
                print(f"🌙 Moon Dev Exit: {exit_reason} at {current_close} after {bars_in_trade} bars 🚀")
                self.entry_bar = None
                self.initial_sl = None
                self.entry_price = None
                self.risk_per_share = None
        else:
            # 🌙 Tightened entry: added RSI >50, trend filter, ATR-based channel width, adjusted volume
            breakout = current_close > prev_upper
            vol_confirm = current_vol > (self.vol_mult * prev_avg_vol)
            channel_too_narrow = prev_width < (self.min_atr_mult * prev_atr)
            extended = (current_close - prev_middle) > (self.extended_multiplier * prev_width)
            rsi_confirm = self.rsi[-1] > 50
            trend_confirm = current_close > self.sma200[-1]

            if breakout and vol_confirm and not channel_too_narrow and not extended and rsi_confirm and trend_confirm:
                # 🌙 Improved SL: max of Donchian lower and ATR-based to avoid overly tight stops
                atr_sl = current_close - 2 * current_atr
                sl_price = max(current_lower, atr_sl)
                risk_per_share = current_close - sl_price
                if risk_per_share > 0:
                    # 🌙 Use float position size for precision (number of BTC units)
                    position_size = (self.equity * self.risk_percent) / risk_per_share
                    tp_price = current_close + (self.tp_multiplier * risk_per_share)

                    self.buy(size=position_size, sl=sl_price, tp=tp_price)
                    self.entry_bar = len(self.data)
                    self.initial_sl = sl_price
                    self.entry_price = current_close
                    self.risk_per_share = risk_per_share
                    print(f"🌙 Moon Dev Long Entry: Breakout at {current_close}, size={position_size}, SL={sl_price}, TP={tp_price} ✨🚀")

# Run backtest
bt = Backtest(data, DonchianAscent, cash=1000000, commission=.002)
stats = bt.run()
print(stats)