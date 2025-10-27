import pandas as pd
from backtesting import Backtest, Strategy
import talib
import numpy as np

# Load and clean data
path = '/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv'
data = pd.read_csv(path)
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'}, inplace=True)
data = data.set_index(pd.to_datetime(data['datetime'])).sort_index()
data = data[['Open', 'High', 'Low', 'Close', 'Volume']]

class SwiftStrength(Strategy):
    adx_threshold = 20  # 🌙 Moon Dev: Lowered from 25 to capture more trending opportunities without excessive noise
    risk_per_trade = 0.02  # 🌙 Moon Dev: Increased from 0.01 to 0.02 for higher exposure and potential returns while maintaining risk control
    rr_ratio = 3  # 🌙 Moon Dev: Increased from 2 to 3 for better reward potential on winners
    atr_multiplier = 2.0  # 🌙 Moon Dev: Increased from 1.5 to 2.0 for wider initial stops and trailing to allow trends to breathe
    atr_period = 14
    weak_trend_threshold = 15  # 🌙 Moon Dev: Lowered from 20 to 15 for earlier emergency exits in weakening trends

    def _reset_trade_vars(self):
        # 🌙 Moon Dev: Reset position tracking variables after full close to prepare for next trade
        self.trailing_sl = None
        self.partial_tp = None
        self.full_tp = None
        self.partial_closed = False
        self.is_long = False

    def init(self):
        close = self.data.Close
        high = self.data.High
        low = self.data.Low
        self.macd, self.macdsignal, self.macdhist = self.I(talib.MACD, close, fastperiod=12, slowperiod=26, signalperiod=9)  # 🌙 Moon Dev: Changed to standard 12/26/9 for less noise and more reliable signals on 15m
        self.adx = self.I(talib.ADX, high, low, close, timeperiod=14)
        self.plus_di = self.I(talib.PLUS_DI, high, low, close, timeperiod=14)
        self.minus_di = self.I(talib.MINUS_DI, high, low, close, timeperiod=14)
        self.sma200 = self.I(talib.SMA, close, timeperiod=200)
        self.atr = self.I(talib.ATR, high, low, close, timeperiod=self.atr_period)
        self.rsi = self.I(talib.RSI, close, timeperiod=14)  # 🌙 Moon Dev: Added RSI for momentum confirmation to filter overbought/oversold entries
        self.vol_sma = self.I(talib.SMA, self.data.Volume, timeperiod=20)  # 🌙 Moon Dev: Added Volume SMA for volume confirmation to avoid low-conviction setups
        print("🌙 Moon Dev: Indicators including MACD(12/26/9), ADX, RSI, and Volume SMA initialized successfully! ✨")

    def next(self):
        current_price = self.data.Close[-1]
        current_adx = self.adx[-1]
        current_plus_di = self.plus_di[-1]
        current_minus_di = self.minus_di[-1]
        current_macd = self.macd[-1]
        current_signal = self.macdsignal[-1]
        current_hist = self.macdhist[-1]
        current_sma = self.sma200[-1]
        current_atr = self.atr[-1]
        current_rsi = self.rsi[-1]
        current_volume = self.data.Volume[-1]
        current_high = self.data.High[-1]
        current_low = self.data.Low[-1]

        # 🌙 Moon Dev: Position management and exits (prioritize hard stops like SL/TP before signal-based exits)
        if self.position:
            # Emergency exit if trend weakens (first check as in original)
            if current_adx < self.weak_trend_threshold:
                self.position.close()
                print(f"🌙 Moon Dev: Emergency exit due to weak trend (ADX < {self.weak_trend_threshold}) 📉")
                self._reset_trade_vars()
                return

            # Update trailing SL
            if self.is_long:
                new_trailing = current_high - self.atr_multiplier * current_atr
                self.trailing_sl = max(self.trailing_sl, new_trailing)
            else:
                new_trailing = current_low + self.atr_multiplier * current_atr
                self.trailing_sl = min(self.trailing_sl, new_trailing)

            # Check trailing SL hit (hard stop, full close)
            if (self.is_long and current_low <= self.trailing_sl) or (not self.is_long and current_high >= self.trailing_sl):
                self.position.close()
                print(f"🌙 Moon Dev: Trailing SL hit at {self.trailing_sl:.2f} 📉")
                self._reset_trade_vars()
                return

            # Check partial TP (scale out 50% at 1.5R)
            if not self.partial_closed:
                if (self.is_long and current_high >= self.partial_tp) or (not self.is_long and current_low <= self.partial_tp):
                    half_size = abs(self.position.size) / 2
                    self.position.close(size=half_size)
                    self.partial_closed = True
                    print(f"🌙 Moon Dev: Partial TP (50%) hit at {self.partial_tp:.2f} 🟡")
                    # Continue to check full TP on remaining position

            # Check full TP (close remaining at 3R)
            if (self.is_long and current_high >= self.full_tp) or (not self.is_long and current_low <= self.full_tp):
                self.position.close()
                print(f"🌙 Moon Dev: Full TP hit at {self.full_tp:.2f} 🚀")
                self._reset_trade_vars()
                return

            # Exit on opposite MACD crossover (signal-based exit)
            if self.position.is_long and (self.macdsignal[-2] < self.macd[-2] and self.macdsignal[-1] > self.macd[-1]):
                self.position.close()
                print(f"🌙 Moon Dev: Exit long on MACD bearish reversal 🔄")
                self._reset_trade_vars()
                return
            if self.position.is_short and (self.macd[-2] < self.macdsignal[-2] and self.macd[-1] > self.macdsignal[-1]):
                self.position.close()
                print(f"🌙 Moon Dev: Exit short on MACD bullish reversal 🔄")
                self._reset_trade_vars()
                return

        # Entry logic (fixed bug: changed from len(self.trades) == 0 to just not self.position for multiple trades)
        if not self.position:
            if np.isnan(current_atr) or current_atr <= 0:
                print("🌙 Moon Dev: Invalid ATR, skipping entry 🚫")
                return

            # 🌙 Moon Dev: Added volume filter to ensure entries on above-average volume for better momentum
            if np.isnan(self.vol_sma[-1]) or current_volume <= self.vol_sma[-1]:
                print("🌙 Moon Dev: Low volume, skipping entry 🚫")
                return

            if np.isnan(current_rsi):
                print("🌙 Moon Dev: Invalid RSI, skipping entry 🚫")
                return

            sl_distance = self.atr_multiplier * current_atr
            risk_amount = self.equity * self.risk_per_trade
            position_size = risk_amount / sl_distance  # 🌙 Moon Dev: Removed int(round()) to allow fractional sizes for precise risk management
            if position_size <= 0:
                print("🌙 Moon Dev: Position size too small or invalid, skipping entry 🚫")
                return

            # Long entry with tightened filters (RSI > 50 for bullish momentum)
            if (current_adx > self.adx_threshold and
                current_plus_di > current_minus_di and
                (self.macd[-2] < self.macdsignal[-2] and self.macd[-1] > self.macdsignal[-1]) and
                current_hist > 0 and
                current_price > current_sma and
                current_rsi > 50):

                self.buy(size=position_size)
                self.partial_tp = current_price + 1.5 * sl_distance
                self.full_tp = current_price + self.rr_ratio * sl_distance
                self.trailing_sl = current_price - sl_distance
                self.is_long = True
                self.partial_closed = False
                sl_price = current_price - sl_distance
                print(f"🌙 Moon Dev: Long entry at {current_price:.2f}, size {position_size:.4f}, SL {sl_price:.2f}, partial TP {self.partial_tp:.2f}, full TP {self.full_tp:.2f} 🚀")

            # Short entry with tightened filters (RSI < 50 for bearish momentum)
            elif (current_adx > self.adx_threshold and
                  current_minus_di > current_plus_di and
                  (self.macdsignal[-2] < self.macd[-2] and self.macdsignal[-1] > self.macd[-1]) and
                  current_hist < 0 and
                  current_price < current_sma and
                  current_rsi < 50):

                self.sell(size=position_size)
                self.partial_tp = current_price - 1.5 * sl_distance
                self.full_tp = current_price - self.rr_ratio * sl_distance
                self.trailing_sl = current_price + sl_distance
                self.is_long = False
                self.partial_closed = False
                sl_price = current_price + sl_distance
                print(f"🌙 Moon Dev: Short entry at {current_price:.2f}, size {position_size:.4f}, SL {sl_price:.2f}, partial TP {self.partial_tp:.2f}, full TP {self.full_tp:.2f} 📉")

# Run backtest
bt = Backtest(data, SwiftStrength, cash=1000000, commission=0.002, exclusive_orders=True)
stats = bt.run()
print(stats)