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
    risk_percent = 0.02  # 🌙 Increased risk per trade to 2% to allow for higher potential returns while scaling towards 50% target
    tp_multiplier = 3  # 🌙 Improved reward:risk ratio to 1:3 for better profitability on winners
    time_exit_bars = 15  # 🌙 Slightly shortened time exit to 15 bars to reduce holding in non-trending periods
    min_channel_width_pct = 0.015  # 🌙 Tightened minimum channel width to 1.5% to filter out more low-volatility whipsaw setups
    extended_multiplier = 1.5  # 🌙 Reduced extension multiplier to allow slightly more aggressive entries without overextension
    atr_period = 14
    atr_sl_mult = 1.5  # 🌙 ATR-based SL multiplier for dynamic, volatility-adjusted stop losses
    vol_multiplier = 1.2  # 🌙 Added volume confirmation multiplier to require stronger volume surge
    rsi_period = 14
    rsi_lower = 50
    rsi_upper = 75  # 🌙 RSI filters: enter only if RSI between 50-75 to catch momentum without overbought entries

    def init(self):
        self.upper = self.I(talib.MAX, self.data.High, timeperiod=self.period)
        self.lower = self.I(talib.MIN, self.data.Low, timeperiod=self.period)
        self.middle = self.I(lambda: (self.upper + self.lower) / 2)
        self.avg_vol = self.I(talib.SMA, self.data.Volume, timeperiod=self.period)
        self.width = self.I(lambda: self.upper - self.lower)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=self.atr_period)  # 🌙 Added ATR for volatility-based risk management
        self.sma200 = self.I(talib.SMA, self.data.Close, timeperiod=200)  # 🌙 Added long-term SMA trend filter to only trade in uptrends
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=self.rsi_period)  # 🌙 Added RSI for momentum confirmation and overbought avoidance
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
        current_atr = self.atr[-1]
        current_sma200 = self.sma200[-1]
        current_rsi = self.rsi[-1]

        prev_idx = -2 if len(self.data) > 1 else -1
        prev_upper = self.upper[prev_idx]
        prev_avg_vol = self.avg_vol[prev_idx]
        prev_width = self.width[prev_idx]
        prev_middle = self.middle[prev_idx]

        if self.position:
            bars_in_trade = len(self.data) - self.entry_bar if self.entry_bar else 0
            exit_reason = ""
            should_exit = False

            # Trailing exit: close below middle (kept for simplicity, but now with better entries it should hold longer)
            if current_close < current_middle:
                should_exit = True
                exit_reason = "Trailing stop (middle band) hit"

            # Time-based exit (adjusted to shorter period for quicker turnover in ranging markets)
            elif bars_in_trade > self.time_exit_bars:
                should_exit = True
                exit_reason = "Time-based exit"

            if should_exit:
                self.position.close()
                print(f"🌙 Moon Dev Exit: {exit_reason} at {current_close} after {bars_in_trade} bars 🚀")
                self.entry_bar = None
                self.initial_sl = None
        else:
            # Entry conditions with optimizations
            breakout = current_close > prev_upper  # Conservative close-based breakout
            vol_confirm = current_vol > (self.vol_multiplier * prev_avg_vol)  # 🌙 Strengthened volume filter for higher quality breakouts
            channel_too_narrow = (prev_width / current_close) < self.min_channel_width_pct  # Tighter filter to avoid chop
            extended = (current_close - prev_middle) > (self.extended_multiplier * prev_width)  # Adjusted to filter climactic moves
            uptrend = current_close > current_sma200  # 🌙 Trend filter: only long in overall uptrend to avoid counter-trend trades
            rsi_confirm = current_rsi > self.rsi_lower and current_rsi < self.rsi_upper  # 🌙 RSI filter for momentum without overbought

            if breakout and vol_confirm and not channel_too_narrow and not extended and uptrend and rsi_confirm:
                # 🌙 Dynamic ATR-based SL and risk calculation for better risk management
                risk_per_share = self.atr_sl_mult * current_atr
                sl_price = current_close - risk_per_share
                if risk_per_share > 0:
                    position_size = int(round((self.equity * self.risk_percent) / risk_per_share))  # Position sizing based on equity risk
                    tp_price = current_close + (self.tp_multiplier * risk_per_share)  # Higher RR for improved returns

                    self.buy(size=position_size, sl=sl_price, tp=tp_price)
                    self.entry_bar = len(self.data)
                    self.initial_sl = sl_price
                    print(f"🌙 Moon Dev Long Entry: Optimized Breakout at {current_close}, size={position_size}, SL={sl_price}, TP={tp_price} ✨🚀")

# Run backtest
bt = Backtest(data, DonchianAscent, cash=1000000, commission=.002)
stats = bt.run()
print(stats)