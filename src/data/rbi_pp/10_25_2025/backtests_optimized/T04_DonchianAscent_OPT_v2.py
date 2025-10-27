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
    period = 15  # 🌙 Optimized: Shortened period from 20 to 15 for more responsive signals without excessive noise
    risk_percent = 0.02  # 🌙 Optimized: Increased risk per trade from 1% to 2% to amplify returns while monitoring drawdown
    tp_multiplier = 3  # 🌙 Optimized: Increased TP multiplier from 2 to 3 for higher reward-to-risk ratio
    time_exit_bars = 10  # 🌙 Optimized: Reduced time exit from 20 to 10 bars to exit stagnant trades faster
    min_channel_width_pct = 0.015  # 🌙 Optimized: Increased min width from 0.01 to 0.015 to filter out more choppy, low-volatility setups
    extended_multiplier = 1.5  # 🌙 Optimized: Reduced from 2 to 1.5 to allow slightly more extended breakouts but avoid over-chasing

    def init(self):
        self.upper = self.I(talib.MAX, self.data.High, timeperiod=self.period)
        self.lower = self.I(talib.MIN, self.data.Low, timeperiod=self.period)
        self.middle = self.I(lambda: (self.upper + self.lower) / 2)
        self.avg_vol = self.I(talib.SMA, self.data.Volume, timeperiod=self.period)
        self.width = self.I(lambda: self.upper - self.lower)
        # 🌙 New: Added SMA200 for long-term trend filter to only enter in uptrends, improving win rate
        self.sma200 = self.I(talib.SMA, self.data.Close, timeperiod=200)
        # 🌙 New: Added RSI for momentum confirmation to ensure bullish bias on entries
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14)
        # 🌙 New: Added ATR for dynamic stop loss adjustment to tighten SL when Donchian lower is too loose
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        self.entry_bar = None
        self.initial_sl = None
        print("🌙 Moon Dev Backtest Initialized: Optimized DonchianAscent Strategy Loaded! ✨")

    def next(self):
        current_close = self.data.Close[-1]
        current_high = self.data.High[-1]
        current_low = self.data.Low[-1]
        current_vol = self.data.Volume[-1]
        current_lower = self.lower[-1]
        current_middle = self.middle[-1]

        prev_idx = -2 if len(self.data) > 1 else -1
        prev_upper = self.upper[prev_idx]
        prev_avg_vol = self.avg_vol[prev_idx]
        prev_width = self.width[prev_idx]
        prev_middle = self.middle[prev_idx]
        prev_close = self.data.Close[prev_idx]  # 🌙 Added: Use previous close for consistent channel width calculation

        if self.position:
            bars_in_trade = len(self.data) - self.entry_bar if self.entry_bar else 0
            exit_reason = ""
            should_exit = False

            # 🌙 Optimized: Prioritize exits - time first, then RSI overbought, then trailing stop
            if bars_in_trade > self.time_exit_bars:
                should_exit = True
                exit_reason = "Time-based exit"
            elif self.rsi[-1] > 75:  # 🌙 New: RSI overbought exit to lock in profits before reversal
                should_exit = True
                exit_reason = "RSI overbought exit"
            elif current_close < current_middle:
                should_exit = True
                exit_reason = "Trailing stop (middle band) hit"

            if should_exit:
                self.position.close()
                print(f"🌙 Moon Dev Exit: {exit_reason} at {current_close} after {bars_in_trade} bars 🚀")
                self.entry_bar = None
                self.initial_sl = None
        else:
            # Entry conditions
            breakout = current_close > prev_upper
            vol_confirm = current_vol > 1.2 * prev_avg_vol  # 🌙 Optimized: Tightened volume filter from 1x to 1.2x for stronger confirmation
            channel_too_narrow = (prev_width / prev_close) < self.min_channel_width_pct  # 🌙 Optimized: Use prev_close for accurate width percentage
            extended = (current_close - prev_middle) > (self.extended_multiplier * prev_width)
            trend_up = current_close > self.sma200[-1]  # 🌙 New: Trend filter - only enter if above 200 SMA for favorable market regime
            momentum_ok = self.rsi[-1] > 50  # 🌙 New: RSI >50 for bullish momentum, avoiding weak breakouts

            if breakout and vol_confirm and not channel_too_narrow and not extended and trend_up and momentum_ok:
                # 🌙 Optimized: Dynamic SL - max of Donchian lower and ATR-based to prevent overly wide stops
                atr_sl = current_close - 2 * self.atr[-1]
                sl_price = max(current_lower, atr_sl)
                risk_per_share = current_close - sl_price
                if risk_per_share > 0:
                    # 🌙 Optimized: Use float for position size to allow fractional shares, improving precision
                    position_size = (self.equity * self.risk_percent) / risk_per_share
                    tp_price = current_close + (self.tp_multiplier * risk_per_share)

                    self.buy(size=position_size, sl=sl_price, tp=tp_price)
                    self.entry_bar = len(self.data)
                    self.initial_sl = sl_price
                    print(f"🌙 Moon Dev Long Entry: Breakout at {current_close}, size={position_size}, SL={sl_price}, TP={tp_price} ✨🚀")

# Run backtest
bt = Backtest(data, DonchianAscent, cash=1000000, commission=.002)
stats = bt.run()
print(stats)