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
    period = 20  # 🌙 Kept period at 20 for balanced channel sensitivity on 15m BTC
    risk_percent = 0.01  # 🌙 Maintained 1% risk per trade for consistent risk management
    tp_multiplier = 2.5  # ✨ Increased TP multiplier from 2 to 2.5 to improve reward:risk ratio for higher returns
    time_exit_bars = 15  # 🌙 Reduced time exit from 20 to 15 bars to exit stagnant trades faster and free up capital
    min_channel_width_pct = 0.015  # ✨ Increased min width threshold from 0.01 to 0.015 to filter out more noise/low-volatility setups
    extended_multiplier = 1.5  # 🌙 Tightened extended filter from 2 to 1.5 to avoid entries too far from channel equilibrium
    vol_multiplier = 1.2  # ✨ Added volume confirmation multiplier to require stronger volume surge (1.2x avg) for better entry quality
    rsi_period = 14  # New: RSI period for momentum filter
    rsi_threshold = 50  # New: Minimum RSI for bullish momentum confirmation
    sma_period = 200  # New: Longer SMA for overall trend filter to only trade in uptrends
    atr_period = 14  # New: ATR period for volatility-based channel width filter (absolute terms for better adaptation to BTC volatility)

    def init(self):
        self.upper = self.I(talib.MAX, self.data.High, timeperiod=self.period)
        self.lower = self.I(talib.MIN, self.data.Low, timeperiod=self.period)
        self.middle = self.I(lambda: (self.upper + self.lower) / 2)
        self.avg_vol = self.I(talib.SMA, self.data.Volume, timeperiod=self.period)
        self.width = self.I(lambda: self.upper - self.lower)
        # ✨ New indicators for optimization: Trend filter (SMA200), Momentum (RSI), Volatility (ATR)
        self.sma200 = self.I(talib.SMA, self.data.Close, timeperiod=self.sma_period)
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=self.rsi_period)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=self.atr_period)
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
        # ✨ Added current values for new filters
        current_sma200 = self.sma200[-1]
        current_rsi = self.rsi[-1]
        current_atr = self.atr[-1]

        prev_idx = -2 if len(self.data) > 1 else -1
        prev_upper = self.upper[prev_idx]
        prev_avg_vol = self.avg_vol[prev_idx]
        prev_width = self.width[prev_idx]
        prev_middle = self.middle[prev_idx]
        # ✨ Added prev values for new filters
        prev_atr = self.atr[prev_idx]

        if self.position:
            bars_in_trade = len(self.data) - self.entry_bar if self.entry_bar else 0
            exit_reason = ""
            should_exit = False

            # Trailing exit: close below middle (kept as is, but now entries are higher quality)
            if current_close < current_middle:
                should_exit = True
                exit_reason = "Trailing stop (middle band) hit"

            # Time-based exit (tuned to 15 bars)
            elif bars_in_trade > self.time_exit_bars:
                should_exit = True
                exit_reason = "Time-based exit"

            if should_exit:
                self.position.close()
                print(f"🌙 Moon Dev Exit: {exit_reason} at {current_close} after {bars_in_trade} bars 🚀")
                self.entry_bar = None
                self.initial_sl = None
        else:
            # Entry conditions (optimized with new filters)
            breakout = current_close > prev_upper
            vol_confirm = current_vol > (self.vol_multiplier * prev_avg_vol)  # ✨ Stricter volume confirmation for higher conviction breakouts
            # 🌙 Switched to ATR-based width filter for volatility-adjusted quality (avoids % bias in high-price BTC)
            channel_too_narrow = prev_width < (1.5 * prev_atr)  # New: Use 1.5x ATR for min width to filter low-vol chop
            extended = (current_close - prev_middle) > (self.extended_multiplier * prev_width)  # Tuned multiplier for better equilibrium check
            # ✨ New filters: Trend (above SMA200) and Momentum (RSI > 50) to avoid counter-trend/false breakouts and ensure bullish bias
            trend_filter = current_close > current_sma200
            momentum_filter = current_rsi > self.rsi_threshold

            if (breakout and vol_confirm and not channel_too_narrow and not extended and
                trend_filter and momentum_filter):
                sl_price = current_lower  # Kept channel-based SL, but now with better entries reduces risk exposure
                risk_per_share = current_close - sl_price
                if risk_per_share > 0:
                    position_size = int(round((self.equity * self.risk_percent) / risk_per_share))
                    tp_price = current_close + (self.tp_multiplier * risk_per_share)  # Higher TP for improved RR

                    self.buy(size=position_size, sl=sl_price, tp=tp_price)
                    self.entry_bar = len(self.data)
                    self.initial_sl = sl_price
                    print(f"🌙 Moon Dev Long Entry: Optimized Breakout at {current_close}, size={position_size}, SL={sl_price}, TP={tp_price} (RSI={current_rsi:.1f}, Trend=Up) ✨🚀")

# Run backtest
bt = Backtest(data, DonchianAscent, cash=1000000, commission=.002)
stats = bt.run()
print(stats)