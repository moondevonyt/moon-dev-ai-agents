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
    period = 20  # 🌙 Increased period back to 20 from 15 for more stable Donchian channels, reducing false breakouts and whipsaws while capturing reliable BTC trends on 15m
    risk_percent = 0.02  # ✨ Increased risk per trade to 2% from 1% to amplify returns in high-conviction setups, maintaining disciplined risk management
    tp_multiplier = 4.0  # 🌙 Boosted TP multiplier to 4x risk from 3x to target superior reward:risk ratios, leveraging BTC's strong directional moves for higher profitability
    time_exit_bars = 30  # ✨ Extended time exit to 30 bars from 20 to give trends more development time, avoiding premature exits in volatile crypto markets
    extended_multiplier = 1.0  # 🌙 Loosened extended filter to 1.0x from 1.2x to allow entries slightly further from equilibrium, increasing trade frequency without excessive risk
    vol_multiplier = 1.2  # ✨ Reduced volume multiplier to 1.2x from 1.5x avg for balanced confirmation, enabling more quality breakouts in varying volume regimes
    rsi_period = 14  # Retained RSI for momentum
    rsi_threshold = 60  # 🌙 Raised RSI threshold to 60 from 55 for even stronger bullish momentum, filtering out marginal setups to improve win rate
    sma_short_period = 50  # ✨ Shortened short-term SMA to 50 from 100 for quicker trend responsiveness on 15m (~12.5 hours), better aligning with BTC's fast moves
    sma_long_period = 200  # 🌙 Added long-term SMA200 filter for overall bull market confirmation, ensuring trades only in favorable uptrends to avoid counter-trend losses
    atr_period = 14  # Retained for volatility measures
    adx_period = 14  # Retained for trend strength
    adx_threshold = 20  # ✨ Lowered ADX threshold to 20 from 25 to capture emerging trends earlier, increasing opportunities while still avoiding extreme chop
    trail_atr_mult = 2.0  # 🌙 New: ATR multiplier for trailing stop (2x ATR below close), providing dynamic protection that tightens as volatility decreases

    def init(self):
        self.upper = self.I(talib.MAX, self.data.High, timeperiod=self.period)
        self.lower = self.I(talib.MIN, self.data.Low, timeperiod=self.period)
        self.middle = self.I(lambda: (self.upper + self.lower) / 2)
        self.avg_vol = self.I(talib.SMA, self.data.Volume, timeperiod=self.period)
        self.width = self.I(lambda: self.upper - self.lower)
        # ✨ Enhanced indicators: Dual SMAs for multi-timeframe-like trend confirmation, RSI, ATR, ADX
        self.sma_short = self.I(talib.SMA, self.data.Close, timeperiod=self.sma_short_period)
        self.sma_long = self.I(talib.SMA, self.data.Close, timeperiod=self.sma_long_period)  # New long-term filter for regime awareness
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=self.rsi_period)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=self.atr_period)
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=self.adx_period)
        self.entry_bar = None
        self.initial_sl = None
        self.trail_sl = None  # 🌙 New: Track trailing stop level for dynamic risk management
        print("🌙 Moon Dev Backtest Initialized: Super-Optimized DonchianAscent Strategy Loaded with Trailing Stops & Dual Trends! ✨")

    def next(self):
        current_close = self.data.Close[-1]
        current_high = self.data.High[-1]
        current_low = self.data.Low[-1]
        current_vol = self.data.Volume[-1]
        current_lower = self.lower[-1]
        current_middle = self.middle[-1]
        # ✨ Updated currents for refined multi-filter entries
        current_sma_short = self.sma_short[-1]
        current_sma_long = self.sma_long[-1]
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
            should_exit = False

            # 🌙 Enhanced exits: Retain middle band trail for channel reversion, add ATR-based trailing stop for volatility-adjusted protection
            if current_close < current_middle:
                should_exit = True
                exit_reason = "Trailing stop (middle band) hit"

            # New: Update trailing stop if position is open (start after 1 bar to avoid immediate adjustment)
            if bars_in_trade > 1 and self.trail_sl is not None:
                new_trail_sl = current_close - (self.trail_atr_mult * current_atr)
                self.trail_sl = max(self.trail_sl, new_trail_sl)
                self.position.sl = self.trail_sl  # Dynamically update SL in backtesting.py

            # Check if price hits updated trailing SL
            if current_low <= self.position.sl:
                should_exit = True
                exit_reason = f"Trailing ATR SL hit at {self.position.sl}"

            # Time-based exit (extended for better capture)
            elif bars_in_trade > self.time_exit_bars:
                should_exit = True
                exit_reason = "Time-based exit"

            if should_exit:
                self.position.close()
                print(f"🌙 Moon Dev Exit: {exit_reason} at {current_close} after {bars_in_trade} bars (Trail SL={self.trail_sl}) 🚀")
                self.entry_bar = None
                self.initial_sl = None
                self.trail_sl = None
        else:
            # Entry conditions (optimized with loosened filters for more trades, added long SMA for bull regime)
            breakout = current_close > prev_upper
            vol_confirm = current_vol > (self.vol_multiplier * prev_avg_vol)  # Balanced volume for more entries
            # 🌙 Loosened ATR width filter to 1.5x from 2x to permit entries in moderately volatile conditions, increasing frequency
            channel_too_narrow = prev_width < (1.5 * prev_atr)
            extended = (current_close - prev_middle) > (self.extended_multiplier * prev_width)  # Loosened for broader setups
            # ✨ Refined filters: Dual trends (above short & long SMA), stronger RSI>60, ADX>20, ascending channel
            short_trend_filter = current_close > current_sma_short
            long_trend_filter = current_close > current_sma_long  # New: Ensures overall uptrend, avoiding bearish regimes
            momentum_filter = current_rsi > self.rsi_threshold
            adx_filter = current_adx > self.adx_threshold
            ascending_channel = current_upper > prev_upper

            if (breakout and vol_confirm and not channel_too_narrow and not extended and
                short_trend_filter and long_trend_filter and momentum_filter and adx_filter and ascending_channel):
                sl_price = current_lower  # Channel-based initial SL
                risk_per_share = current_close - sl_price
                if risk_per_share > 0:
                    # ✨ Increased risk_percent drives larger positions for higher returns
                    position_size = (self.equity * self.risk_percent) / risk_per_share  # Use fraction for precision in crypto
                    tp_price = current_close + (self.tp_multiplier * risk_per_share)  # Amplified TP for 4:1 RR

                    self.buy(size=position_size, sl=sl_price, tp=tp_price)
                    self.entry_bar = len(self.data)
                    self.initial_sl = sl_price
                    self.trail_sl = sl_price  # Initialize trailing SL
                    print(f"🌙 Moon Dev Long Entry: Super Breakout at {current_close}, size={position_size:.4f}, SL={sl_price}, TP={tp_price} (RSI={current_rsi:.1f}, ADX={current_adx:.1f}, ShortTrend=Up, LongTrend=Up, Ascending=Yes) ✨🚀")

# Run backtest
bt = Backtest(data, DonchianAscent, cash=1000000, commission=.002)
stats = bt.run()
print(stats)