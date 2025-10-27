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
    period = 15  # 🌙 Reduced period from 20 to 15 for increased sensitivity to breakouts on 15m timeframe, capturing more opportunities while maintaining reliability
    risk_percent = 0.01  # 🌙 Maintained 1% risk per trade for consistent risk management
    tp_multiplier = 3.0  # ✨ Increased TP multiplier from 2.5 to 3.0 to further enhance reward:risk ratio, targeting higher returns in trending BTC moves
    time_exit_bars = 20  # 🌙 Adjusted time exit from 15 to 20 bars to allow more room for profitable trends to develop without premature exits
    min_channel_width_pct = 0.015  # ✨ Kept min width threshold but now using enhanced ATR filter for better adaptation
    extended_multiplier = 1.2  # 🌙 Further tightened extended filter from 1.5 to 1.2 to ensure entries closer to channel equilibrium, reducing reversal risk
    vol_multiplier = 1.5  # ✨ Increased volume confirmation multiplier from 1.2 to 1.5x avg for stricter entry quality, filtering out weaker breakouts
    rsi_period = 14  # Kept RSI period for momentum filter
    rsi_threshold = 55  # ✨ Raised RSI threshold from 50 to 55 for stronger bullish momentum confirmation, avoiding neutral/weak setups
    sma_period = 100  # ✨ Reduced SMA period from 200 to 100 for a more responsive trend filter on 15m (about 25 hours), better suiting BTC's volatility
    atr_period = 14  # Kept ATR period for volatility-based channel width filter
    adx_period = 14  # New: ADX period for trend strength filter
    adx_threshold = 25  # New: Minimum ADX for confirming trending market conditions, avoiding choppy ranges

    def init(self):
        self.upper = self.I(talib.MAX, self.data.High, timeperiod=self.period)
        self.lower = self.I(talib.MIN, self.data.Low, timeperiod=self.period)
        self.middle = self.I(lambda: (self.upper + self.lower) / 2)
        self.avg_vol = self.I(talib.SMA, self.data.Volume, timeperiod=self.period)
        self.width = self.I(lambda: self.upper - self.lower)
        # ✨ Retained and enhanced indicators: Trend filter (shorter SMA100), Momentum (RSI), Volatility (ATR)
        self.sma100 = self.I(talib.SMA, self.data.Close, timeperiod=self.sma_period)  # Renamed for clarity
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=self.rsi_period)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=self.atr_period)
        # 🌙 New indicator: ADX for market regime filter to ensure strong trends before entering
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=self.adx_period)
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
        # ✨ Updated current values for refined filters
        current_sma100 = self.sma100[-1]
        current_rsi = self.rsi[-1]
        current_atr = self.atr[-1]
        current_adx = self.adx[-1]
        current_upper = self.upper[-1]  # 🌙 Added for ascending channel filter

        prev_idx = -2 if len(self.data) > 1 else -1
        prev_upper = self.upper[prev_idx]
        prev_avg_vol = self.avg_vol[prev_idx]
        prev_width = self.width[prev_idx]
        prev_middle = self.middle[prev_idx]
        # ✨ Updated prev values for filters
        prev_atr = self.atr[prev_idx]

        if self.position:
            bars_in_trade = len(self.data) - self.entry_bar if self.entry_bar else 0
            exit_reason = ""
            should_exit = False

            # Trailing exit: close below middle (retained for dynamic protection, now with higher quality entries)
            if current_close < current_middle:
                should_exit = True
                exit_reason = "Trailing stop (middle band) hit"

            # Time-based exit (adjusted to 20 bars for better trend capture)
            elif bars_in_trade > self.time_exit_bars:
                should_exit = True
                exit_reason = "Time-based exit"

            if should_exit:
                self.position.close()
                print(f"🌙 Moon Dev Exit: {exit_reason} at {current_close} after {bars_in_trade} bars 🚀")
                self.entry_bar = None
                self.initial_sl = None
        else:
            # Entry conditions (enhanced with ascending channel and ADX filters for superior setup quality)
            breakout = current_close > prev_upper
            vol_confirm = current_vol > (self.vol_multiplier * prev_avg_vol)  # ✨ Stricter volume confirmation for higher conviction breakouts
            # 🌙 Enhanced ATR-based width filter: Increased to 2x ATR for stricter low-vol chop avoidance
            channel_too_narrow = prev_width < (2 * prev_atr)
            extended = (current_close - prev_middle) > (self.extended_multiplier * prev_width)  # Tighter multiplier for improved equilibrium
            # ✨ Refined filters: Trend (above SMA100), Momentum (RSI > 55), New: ADX > 25 for trend strength, New: Ascending channel (upper rising)
            trend_filter = current_close > current_sma100
            momentum_filter = current_rsi > self.rsi_threshold
            adx_filter = current_adx > self.adx_threshold
            ascending_channel = current_upper > prev_upper  # 🌙 New: Only enter in ascending Donchian channels to align with uptrend momentum

            if (breakout and vol_confirm and not channel_too_narrow and not extended and
                trend_filter and momentum_filter and adx_filter and ascending_channel):
                sl_price = current_lower  # Retained channel-based SL, enhanced by filtered entries for lower risk
                risk_per_share = current_close - sl_price
                if risk_per_share > 0:
                    position_size = int(round((self.equity * self.risk_percent) / risk_per_share))
                    tp_price = current_close + (self.tp_multiplier * risk_per_share)  # Higher TP for amplified RR in optimized setups

                    self.buy(size=position_size, sl=sl_price, tp=tp_price)
                    self.entry_bar = len(self.data)
                    self.initial_sl = sl_price
                    print(f"🌙 Moon Dev Long Entry: Optimized Breakout at {current_close}, size={position_size}, SL={sl_price}, TP={tp_price} (RSI={current_rsi:.1f}, ADX={current_adx:.1f}, Trend=Up, Ascending=Yes) ✨🚀")

# Run backtest
bt = Backtest(data, DonchianAscent, cash=1000000, commission=.002)
stats = bt.run()
print(stats)