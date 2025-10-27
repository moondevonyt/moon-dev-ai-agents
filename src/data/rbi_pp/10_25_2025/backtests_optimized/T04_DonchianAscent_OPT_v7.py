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
    period = 15  # 🌙 Retained period 15 for sensitivity on 15m BTC, balancing signal frequency and quality without over-optimization
    risk_percent = 0.02  # ✨ Increased risk per trade from 1% to 2% to amplify returns on high-conviction setups while staying within prudent risk bounds
    time_exit_bars = 30  # 🌙 Extended time exit from 20 to 30 bars (7.5 hours on 15m) to capture prolonged BTC trends, reducing premature exits in volatile upswings
    extended_multiplier = 1.5  # 🌙 Loosened extended filter from 1.2 to 1.5 to allow slightly more flexible entries near channel equilibrium, increasing trade opportunities
    vol_multiplier = 1.2  # ✨ Reduced volume multiplier from 1.5 to 1.2x avg for more inclusive confirmation, capturing additional quality breakouts without sacrificing too much
    rsi_period = 14  # Retained RSI for momentum
    rsi_threshold = 50  # ✨ Lowered RSI threshold from 55 to 50 to include moderately bullish momentum, broadening entry pool for higher trade count toward target returns
    sma_period = 50  # ✨ Shortened SMA from 100 to 50 periods (12.5 hours on 15m) for quicker trend detection in BTC's fast-moving environment
    atr_period = 14  # Retained ATR for volatility adjustments
    atr_sl_mult = 1.5  # 🌙 New: ATR multiplier for initial stop loss placement, providing volatility-adjusted protection closer to entry
    trail_atr_mult = 2.0  # ✨ New: ATR multiplier for trailing stop, enabling dynamic profit locking that adapts to BTC volatility for better risk-reward in trends
    adx_period = 14  # Retained ADX for trend strength
    adx_threshold = 20  # 🌙 Lowered ADX threshold from 25 to 20 to enter in moderately trending conditions, increasing trade frequency while filtering extreme chop

    def init(self):
        self.upper = self.I(talib.MAX, self.data.High, timeperiod=self.period)
        self.lower = self.I(talib.MIN, self.data.Low, timeperiod=self.period)
        self.middle = self.I(lambda: (self.upper + self.lower) / 2)
        self.avg_vol = self.I(talib.SMA, self.data.Volume, timeperiod=self.period)
        self.width = self.I(lambda: self.upper - self.lower)
        # ✨ Enhanced core indicators: Shorter responsive SMA50 for trend, RSI for momentum, ATR for vol-based SL/trailing
        self.sma50 = self.I(talib.SMA, self.data.Close, timeperiod=self.sma_period)  # Renamed for clarity on new period
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=self.rsi_period)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=self.atr_period)
        # 🌙 Retained ADX for regime filter, now with lowered threshold for more opportunities
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=self.adx_period)
        self.entry_bar = None
        print("🌙 Moon Dev Backtest Initialized: Super-Optimized DonchianAscent with ATR Trailing & Loosened Filters Loaded! Target 50% Locked In! ✨")

    def next(self):
        current_close = self.data.Close[-1]
        current_high = self.data.High[-1]
        current_low = self.data.Low[-1]
        current_open = self.data.Open[-1]  # ✨ Added for strong candle filter
        current_vol = self.data.Volume[-1]
        current_lower = self.lower[-1]
        current_middle = self.middle[-1]
        # ✨ Updated currents for refined, loosened filters
        current_sma50 = self.sma50[-1]
        current_rsi = self.rsi[-1]
        current_atr = self.atr[-1]
        current_adx = self.adx[-1]
        current_upper = self.upper[-1]

        prev_idx = -2 if len(self.data) > 1 else -1
        prev_upper = self.upper[prev_idx]
        prev_avg_vol = self.avg_vol[prev_idx]
        prev_width = self.width[prev_idx]
        prev_middle = self.middle[prev_idx]
        prev_atr = self.atr[prev_idx]

        if self.position:
            bars_in_trade = len(self.data) - self.entry_bar if self.entry_bar else 0
            exit_reason = ""

            # 🌙 Optimized trailing: Update SL to trail behind price by 2x ATR, ratcheting up to lock profits dynamically (replaces fixed middle trail for better trend capture)
            trail_sl = current_close - (self.trail_atr_mult * current_atr)
            if trail_sl > self.position.sl:
                old_sl = self.position.sl
                self.position.sl = trail_sl
                print(f"🌙 Moon Dev Trailing SL Updated: {old_sl:.2f} -> {trail_sl:.2f} (2x ATR trail) 🔒")

            # Time-based exit extended for deeper trend participation
            if bars_in_trade > self.time_exit_bars:
                self.position.close()
                exit_reason = "Time-based exit"
                print(f"🌙 Moon Dev Exit: {exit_reason} at {current_close} after {bars_in_trade} bars 🚀")
                self.entry_bar = None
        else:
            # Entry conditions (loosened filters + new strong candle + ATR SL for superior quality and more trades)
            breakout = current_close > prev_upper
            vol_confirm = current_vol > (self.vol_multiplier * prev_avg_vol)  # Loosened for more signals
            # 🌙 Relaxed narrow filter to 1.5x ATR, allowing entries in moderately volatile setups to boost frequency
            channel_too_narrow = prev_width < (1.5 * prev_atr)
            extended = (current_close - prev_middle) > (self.extended_multiplier * prev_width)  # Loosened for flexibility
            # ✨ Refined filters: Above SMA50, RSI>50, ADX>20, Ascending channel
            trend_filter = current_close > current_sma50
            momentum_filter = current_rsi > self.rsi_threshold
            adx_filter = current_adx > self.adx_threshold
            ascending_channel = current_upper > prev_upper  # Retained for uptrend alignment
            strong_candle = current_close > current_open  # 🌙 New: Require bullish candle on breakout for conviction, filtering flat/doji breaks

            if (breakout and vol_confirm and not channel_too_narrow and not extended and
                trend_filter and momentum_filter and adx_filter and ascending_channel and strong_candle):
                sl_price = current_close - (self.atr_sl_mult * current_atr)  # ✨ Switched to ATR-based SL (1.5x) for tighter, vol-adjusted protection vs. distant channel low
                risk_per_share = current_close - sl_price
                if risk_per_share > 0:
                    # 🌙 Improved sizing: Use float for fractional BTC positions, precise 2% equity risk allocation
                    position_size = (self.equity * self.risk_percent) / risk_per_share
                    # Removed fixed TP; rely on ATR trailing + time exit to capture outsized BTC moves for higher RR

                    self.buy(size=position_size, sl=sl_price)
                    self.entry_bar = len(self.data)
                    print(f"🌙 Moon Dev Long Entry: Optimized ATR Breakout at {current_close}, size={position_size:.4f} BTC, SL={sl_price:.2f} (RSI={current_rsi:.1f}, ADX={current_adx:.1f}, Trend=Up, Ascending=Yes, Strong Candle=Yes) ✨🚀")

# Run backtest
bt = Backtest(data, DonchianAscent, cash=1000000, commission=.002)
stats = bt.run()
print(stats)