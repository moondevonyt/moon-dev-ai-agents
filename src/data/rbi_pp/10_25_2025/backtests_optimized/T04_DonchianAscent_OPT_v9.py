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
    period = 15  # 🌙 Retained period 15 for sensitivity, balancing trade frequency and reliability on 15m BTC
    risk_percent = 0.015  # ✨ Increased risk per trade from 1% to 1.5% to amplify returns on high-quality setups while keeping risk controlled
    tp_multiplier = 4.0  # 🌙 Boosted TP multiplier from 3.0 to 4.0 to target even higher reward:risk ratios, capitalizing on BTC's strong trends for 50%+ goal
    time_exit_bars = 15  # ✨ Reduced time exit from 20 to 15 bars to exit non-performers faster, improving capital efficiency and reducing drag on returns
    min_channel_width_pct = 0.015  # Retained but enhanced via ATR for dynamic filtering
    extended_multiplier = 1.2  # 🌙 Kept tight extended filter to avoid overextended entries, minimizing reversal risks
    vol_multiplier = 1.3  # ✨ Slightly reduced volume multiplier from 1.5 to 1.3x avg to allow more valid breakouts, increasing trade opportunities without sacrificing quality
    rsi_period = 14  # Retained RSI for momentum
    rsi_threshold = 50  # 🌙 Lowered RSI threshold from 55 to 50 to capture earlier momentum shifts, boosting entry frequency in uptrends
    sma_period = 50  # ✨ Further reduced SMA period from 100 to 50 for quicker trend detection on 15m (~12.5 hours), aligning better with BTC's intra-day swings
    atr_period = 14  # Retained ATR for volatility adjustments
    adx_period = 14  # Retained ADX for trend strength
    adx_threshold = 20  # 🌙 Lowered ADX threshold from 25 to 20 to include moderately trending conditions, increasing trade count while filtering extreme chop

    def init(self):
        self.upper = self.I(talib.MAX, self.data.High, timeperiod=self.period)
        self.lower = self.I(talib.MIN, self.data.Low, timeperiod=self.period)
        self.middle = self.I(lambda: (self.upper + self.lower) / 2)
        self.avg_vol = self.I(talib.SMA, self.data.Volume, timeperiod=self.period)
        self.width = self.I(lambda: self.upper - self.lower)
        # ✨ Retained core indicators with optimized params: Shorter SMA50 for responsive trend, RSI at 50, ATR, ADX at 20
        self.sma50 = self.I(talib.SMA, self.data.Close, timeperiod=self.sma_period)  # Renamed for clarity on new period
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=self.rsi_period)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=self.atr_period)
        # 🌙 Retained ADX for regime filter, now with lower threshold for more entries in building trends
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=self.adx_period)
        self.entry_bar = None
        self.initial_sl = None
        # 🌙 New: Track trailing SL for dynamic exits based on ATR to protect profits better
        self.trailing_sl = None
        print("🌙 Moon Dev Backtest Initialized: Further Optimized DonchianAscent Strategy Loaded for 50% Target! ✨")

    def next(self):
        current_close = self.data.Close[-1]
        current_high = self.data.High[-1]
        current_low = self.data.Low[-1]
        current_vol = self.data.Volume[-1]
        current_lower = self.lower[-1]
        current_middle = self.middle[-1]
        # ✨ Updated current values with new SMA50
        current_sma50 = self.sma50[-1]
        current_rsi = self.rsi[-1]
        current_atr = self.atr[-1]
        current_adx = self.adx[-1]
        current_upper = self.upper[-1]  # Retained for ascending filter

        prev_idx = -2 if len(self.data) > 1 else -1
        prev_upper = self.upper[prev_idx]
        prev_avg_vol = self.avg_vol[prev_idx]
        prev_width = self.width[prev_idx]
        prev_middle = self.middle[prev_idx]
        # ✨ Updated prev values
        prev_atr = self.atr[prev_idx]
        prev_sma50 = self.sma50[prev_idx]  # New for potential trailing

        if self.position:
            bars_in_trade = len(self.data) - self.entry_bar if self.entry_bar else 0
            exit_reason = ""
            should_exit = False

            # 🌙 Enhanced trailing: Use max of initial SL, middle band, or ATR-based trail (1.5x ATR below current high) for better profit locking
            if not self.trailing_sl:
                self.trailing_sl = self.initial_sl
            trail_candidate = current_high - (1.5 * current_atr)
            self.trailing_sl = max(self.trailing_sl, trail_candidate, current_middle)
            
            if current_close < self.trailing_sl:
                should_exit = True
                exit_reason = f"Trailing stop ({self.trailing_sl:.2f}) hit"

            # Time-based exit (tightened to 15 bars for quicker turnover)
            elif bars_in_trade > self.time_exit_bars:
                should_exit = True
                exit_reason = "Time-based exit"

            if should_exit:
                self.position.close()
                print(f"🌙 Moon Dev Exit: {exit_reason} at {current_close} after {bars_in_trade} bars 🚀")
                self.entry_bar = None
                self.initial_sl = None
                self.trailing_sl = None
        else:
            # Entry conditions (refined with looser filters for more opportunities: vol 1.3x, RSI 50, ADX 20, SMA50)
            breakout = current_close > prev_upper
            vol_confirm = current_vol > (self.vol_multiplier * prev_avg_vol)  # Loosened for higher frequency
            # 🌙 Retained ATR width filter at 2x but with more entries via other loosens
            channel_too_narrow = prev_width < (2 * prev_atr)
            extended = (current_close - prev_middle) > (self.extended_multiplier * prev_width)  # Tight to avoid extremes
            # ✨ Filters: Trend (above SMA50), Momentum (RSI > 50), ADX > 20, Ascending channel
            trend_filter = current_close > current_sma50
            momentum_filter = current_rsi > self.rsi_threshold
            adx_filter = current_adx > self.adx_threshold
            ascending_channel = current_upper > prev_upper  # Retained for uptrend alignment

            if (breakout and vol_confirm and not channel_too_narrow and not extended and
                trend_filter and momentum_filter and adx_filter and ascending_channel):
                sl_price = current_lower  # Channel-based SL, now protected by enhanced trailing
                risk_per_share = current_close - sl_price
                if risk_per_share > 0:
                    # 🌙 Position sizing with increased risk% for higher returns
                    position_size = int(round((self.equity * self.risk_percent) / risk_per_share))
                    tp_price = current_close + (self.tp_multiplier * risk_per_share)  # Higher TP for 50% push

                    self.buy(size=position_size, sl=sl_price, tp=tp_price)
                    self.entry_bar = len(self.data)
                    self.initial_sl = sl_price
                    self.trailing_sl = sl_price  # Initialize trailing
                    print(f"🌙 Moon Dev Long Entry: Enhanced Breakout at {current_close}, size={position_size}, SL={sl_price}, TP={tp_price} (RSI={current_rsi:.1f}, ADX={current_adx:.1f}, Trend=Up, Ascending=Yes) ✨🚀")

# Run backtest
bt = Backtest(data, DonchianAscent, cash=1000000, commission=.002)
stats = bt.run()
print(stats)