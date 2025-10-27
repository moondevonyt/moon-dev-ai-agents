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
    period = 15  # 🌙 Retained period 15 for sensitivity on 15m BTC, balancing frequency and reliability
    risk_percent = 0.02  # ✨ Increased risk per trade to 2% from 1.5% to amplify returns on filtered high-quality setups, pushing towards 50% target while monitoring drawdown
    tp_multiplier = 3.5  # 🌙 Adjusted TP multiplier down to 3.5x from 4.0 for more realistic hits in BTC volatility, combined with trailing for outsized winners
    time_exit_bars = 20  # ✨ Extended time exit to 20 bars from 15 to allow stronger trends more room, improving win rate on trending BTC moves
    min_channel_width_pct = 0.015  # Retained but now dynamically checked against price for additional narrow channel filter
    extended_multiplier = 1.5  # 🌙 Loosened extended filter to 1.5x from 1.2 to capture more valid breakouts without excessive reversal risk
    vol_multiplier = 1.5  # ✨ Tightened volume multiplier back to 1.5x avg from 1.3x for stronger confirmation, reducing false breakouts and improving signal quality
    rsi_period = 14  # Retained RSI for momentum confirmation
    rsi_threshold = 55  # 🌙 Raised RSI threshold to 55 from 50 for stronger momentum filter, ensuring entries in confirmed uptrends to boost expectancy
    sma_period = 20  # ✨ Shortened SMA period to 20 from 50 for faster trend detection on 15m (~5 hours), better aligning with BTC's short-term swings
    atr_period = 14  # Retained ATR for volatility-based adjustments
    adx_period = 14  # Retained ADX for trend strength
    adx_threshold = 25  # 🌙 Increased ADX threshold to 25 from 20 to focus on stronger trends only, filtering out weaker conditions for higher win rate and returns

    def init(self):
        self.upper = self.I(talib.MAX, self.data.High, timeperiod=self.period)
        self.lower = self.I(talib.MIN, self.data.Low, timeperiod=self.period)
        self.middle = self.I(lambda: (self.upper + self.lower) / 2)
        self.avg_vol = self.I(talib.SMA, self.data.Volume, timeperiod=self.period)
        self.width = self.I(lambda: self.upper - self.lower)
        # ✨ Optimized core indicators: Shorter SMA20 for responsive trend, RSI at 55, ADX at 25 for quality
        self.sma20 = self.I(talib.SMA, self.data.Close, timeperiod=self.sma_period)  # Renamed for new shorter period
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=self.rsi_period)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=self.atr_period)
        # 🌙 Enhanced with longer SMA200 for overall bull market regime filter to avoid counter-trend trades
        self.sma200 = self.I(talib.SMA, self.data.Close, timeperiod=200)
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=self.adx_period)
        self.entry_bar = None
        self.initial_sl = None
        # 🌙 Improved trailing SL tracking: Now uses 2x ATR trail from high for looser profit protection, allowing BTC trends to run longer
        self.trailing_sl = None
        print("🌙 Moon Dev Backtest Initialized: Optimized DonchianAscent with Regime Filter & Tighter Quality Controls for 50% Target! ✨")

    def next(self):
        current_close = self.data.Close[-1]
        current_high = self.data.High[-1]
        current_low = self.data.Low[-1]
        current_vol = self.data.Volume[-1]
        current_lower = self.lower[-1]
        current_middle = self.middle[-1]
        # ✨ Updated with new SMA20 and added SMA200
        current_sma20 = self.sma20[-1]
        current_sma200 = self.sma200[-1]
        current_rsi = self.rsi[-1]
        current_atr = self.atr[-1]
        current_adx = self.adx[-1]
        current_upper = self.upper[-1]

        prev_idx = -2 if len(self.data) > 1 else -1
        prev_upper = self.upper[prev_idx]
        prev_avg_vol = self.avg_vol[prev_idx]
        prev_width = self.width[prev_idx]
        prev_middle = self.middle[prev_idx]
        # ✨ Updated prev values including new SMAs
        prev_atr = self.atr[prev_idx]
        prev_sma20 = self.sma20[prev_idx]
        prev_sma200 = self.sma200[prev_idx]

        if self.position:
            bars_in_trade = len(self.data) - self.entry_bar if self.entry_bar else 0
            exit_reason = ""
            should_exit = False

            # 🌙 Enhanced trailing: Looser 2x ATR from high, max with previous and middle, but only if above initial SL to protect core risk
            if not self.trailing_sl:
                self.trailing_sl = self.initial_sl
            trail_candidate = current_high - (2.0 * current_atr)  # Loosened to 2x ATR for longer runs in volatile BTC uptrends
            self.trailing_sl = max(self.trailing_sl, trail_candidate, current_middle)
            # Ensure trailing doesn't go below initial SL initially
            self.trailing_sl = max(self.trailing_sl, self.initial_sl)
            
            if current_close < self.trailing_sl:
                should_exit = True
                exit_reason = f"Trailing stop ({self.trailing_sl:.2f}) hit"

            # Time-based exit extended for better trend capture
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
            # Entry conditions refined: Tighter vol/ADX/RSI, wider channel (3x ATR), added SMA200 regime filter, looser extended
            breakout = current_close > prev_upper
            vol_confirm = current_vol > (self.vol_multiplier * prev_avg_vol)  # Tightened for quality
            # 🌙 Stricter channel width: Only wide channels >=3x ATR for stronger, more reliable breakouts
            channel_too_narrow = prev_width < (3 * prev_atr)
            # Additional pct-based narrow filter using retained param
            pct_width = prev_width / prev_middle if prev_middle > 0 else 0
            pct_too_narrow = pct_width < self.min_channel_width_pct
            extended = (current_close - prev_middle) > (self.extended_multiplier * prev_width)  # Loosened for more entries
            # ✨ Enhanced filters: Short trend (above SMA20), Momentum (RSI >55), Strong ADX >25, Ascending, Long-term regime (above SMA200)
            trend_filter = current_close > current_sma20
            momentum_filter = current_rsi > self.rsi_threshold
            adx_filter = current_adx > self.adx_threshold
            ascending_channel = current_upper > prev_upper
            regime_filter = current_close > current_sma200  # New: Only in bull regime to avoid downtrend traps

            if (breakout and vol_confirm and not channel_too_narrow and not pct_too_narrow and not extended and
                trend_filter and momentum_filter and adx_filter and ascending_channel and regime_filter):
                sl_price = current_lower  # Channel-based SL with enhanced trailing protection
                risk_per_share = current_close - sl_price
                if risk_per_share > 0:
                    # 🌙 Volatility-adjusted position sizing: Incorporate ATR scaling for risk (effective risk = risk% * ATR factor)
                    atr_factor = current_atr / current_close  # Normalize ATR to price
                    adjusted_risk = self.risk_percent * (1 / (1 + atr_factor))  # Reduce size in high vol to manage risk
                    position_size = int(round((self.equity * adjusted_risk) / risk_per_share))
                    tp_price = current_close + (self.tp_multiplier * risk_per_share)  # Balanced TP for achievable targets

                    self.buy(size=position_size, sl=sl_price, tp=tp_price)
                    self.entry_bar = len(self.data)
                    self.initial_sl = sl_price
                    self.trailing_sl = sl_price
                    print(f"🌙 Moon Dev Long Entry: Quality Breakout at {current_close}, size={position_size}, SL={sl_price}, TP={tp_price} (RSI={current_rsi:.1f}, ADX={current_adx:.1f}, Trend=Up, Regime=Bull, Ascending=Yes, Width={pct_width:.3f}) ✨🚀")

# Run backtest
bt = Backtest(data, DonchianAscent, cash=1000000, commission=.002)
stats = bt.run()
print(stats)