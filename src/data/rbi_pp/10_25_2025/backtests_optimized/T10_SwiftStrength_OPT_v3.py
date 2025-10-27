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
    adx_threshold = 25
    risk_per_trade = 0.015  # 🌙 Increased risk per trade to 1.5% for higher exposure while maintaining risk management
    rr_ratio = 3  # 🌙 Improved RR ratio to 3:1 for capturing larger trends and boosting returns
    atr_multiplier = 1.5
    atr_period = 14
    weak_trend_threshold = 20
    vol_sma_period = 20  # 🌙 Added volume SMA period for new volume filter

    def init(self):
        close = self.data.Close
        high = self.data.High
        low = self.data.Low
        # 🌙 Changed MACD parameters to standard 12,26,9 for more reliable trend signals
        self.macd, self.macdsignal, self.macdhist = self.I(talib.MACD, close, fastperiod=12, slowperiod=26, signalperiod=9)
        self.adx = self.I(talib.ADX, high, low, close, timeperiod=14)
        self.plus_di = self.I(talib.PLUS_DI, high, low, close, timeperiod=14)
        self.minus_di = self.I(talib.MINUS_DI, high, low, close, timeperiod=14)
        self.sma200 = self.I(talib.SMA, close, timeperiod=200)
        self.atr = self.I(talib.ATR, high, low, close, timeperiod=self.atr_period)
        # 🌙 Added volume SMA for filtering low-volume entries to improve signal quality
        self.vol_sma = self.I(talib.SMA, self.data.Volume, timeperiod=self.vol_sma_period)
        self.entry_set = False
        self.entry_price = 0.0
        print("🌙 Moon Dev: Indicators initialized successfully with volume filter and trailing prep! ✨")

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
        current_vol = self.data.Volume[-1]
        current_vol_sma = self.vol_sma[-1]

        # 🌙 Reset entry tracking when no position
        if not self.position:
            self.entry_set = False

        # Emergency exit if trend weakens
        if self.position and current_adx < self.weak_trend_threshold:
            self.position.close()
            print(f"🌙 Moon Dev: Emergency exit due to weak trend (ADX < {self.weak_trend_threshold}) 📉")
            self.entry_set = False
            return

        # 🌙 Set entry price on first opportunity after entry
        if self.position and not self.entry_set:
            self.entry_price = self.position.entry_price
            self.entry_set = True
            print(f"🌙 Moon Dev: Entry price set to {self.entry_price:.2f} 📍")

        # 🌙 Implement trailing stop for better profit locking after 2 ATR in profit
        if self.position:
            trail_threshold = current_atr * 2
            trail_mult = self.atr_multiplier
            if self.position.is_long:
                unrealized_pnl = current_price - self.entry_price
                if unrealized_pnl > trail_threshold:
                    new_sl = current_price - current_atr * trail_mult
                    if new_sl > self.position.sl:
                        self.position.sl = new_sl
                        print(f"🌙 Moon Dev: Trailing SL updated to {new_sl:.2f} for long 🛡️")
            elif self.position.is_short:
                unrealized_pnl = self.entry_price - current_price
                if unrealized_pnl > trail_threshold:
                    new_sl = current_price + current_atr * trail_mult
                    if new_sl < self.position.sl:
                        self.position.sl = new_sl
                        print(f"🌙 Moon Dev: Trailing SL updated to {new_sl:.2f} for short 🛡️")

        # Exit on opposite MACD crossover
        if self.position.is_long and (self.macdsignal[-2] < self.macd[-2] and self.macdsignal[-1] > self.macd[-1]):
            self.position.close()
            print(f"🌙 Moon Dev: Exit long on MACD bearish reversal 🔄")
            self.entry_set = False
            return
        if self.position.is_short and (self.macd[-2] < self.macdsignal[-2] and self.macd[-1] > self.macdsignal[-1]):
            self.position.close()
            print(f"🌙 Moon Dev: Exit short on MACD bullish reversal 🔄")
            self.entry_set = False
            return

        # Entry logic only if no position (🌙 Removed len(self.trades)==0 bug to allow multiple trades for higher returns!)
        if not self.position:
            if np.isnan(current_atr) or current_atr <= 0:
                print("🌙 Moon Dev: Invalid ATR, skipping entry 🚫")
                return

            sl_distance = self.atr_multiplier * current_atr
            risk_amount = self.equity * self.risk_per_trade
            position_size = risk_amount / sl_distance  # 🌙 Keep as float for precise position sizing
            if position_size <= 0:
                print("🌙 Moon Dev: Position size invalid, skipping entry 🚫")
                return

            # 🌙 Added volume filter: only enter on above-average volume for better momentum confirmation
            if current_vol <= current_vol_sma:
                print("🌙 Moon Dev: Low volume, skipping entry 🚫")
                return

            # Long entry
            if (current_adx > self.adx_threshold and
                current_plus_di > current_minus_di and
                (self.macd[-2] < self.macdsignal[-2] and self.macd[-1] > self.macdsignal[-1]) and
                current_hist > 0 and
                current_price > current_sma and
                current_vol > current_vol_sma):

                sl = current_price - sl_distance
                tp = current_price + (self.rr_ratio * sl_distance)
                if sl >= current_price or tp <= current_price:
                    print(f"🌙 Moon Dev: Invalid SL/TP for long, skipping 🚫")
                    return
                self.buy(size=position_size, sl=sl, tp=tp)  # 🌙 Removed limit for market entry at next open
                self.entry_set = False  # Will be set next bar
                print(f"🌙 Moon Dev: Long entry signal at {current_price:.2f}, size {position_size:.4f}, SL {sl:.2f}, TP {tp:.2f} 🚀")

            # Short entry
            elif (current_adx > self.adx_threshold and
                  current_minus_di > current_plus_di and
                  (self.macdsignal[-2] < self.macd[-2] and self.macdsignal[-1] > self.macd[-1]) and
                  current_hist < 0 and
                  current_price < current_sma and
                  current_vol > current_vol_sma):

                sl = current_price + sl_distance
                tp = current_price - (self.rr_ratio * sl_distance)
                if sl <= current_price or tp >= current_price:
                    print(f"🌙 Moon Dev: Invalid SL/TP for short, skipping 🚫")
                    return
                self.sell(size=position_size, sl=sl, tp=tp)  # 🌙 Removed limit for market entry at next open
                self.entry_set = False  # Will be set next bar
                print(f"🌙 Moon Dev: Short entry signal at {current_price:.2f}, size {position_size:.4f}, SL {sl:.2f}, TP {tp:.2f} 📉")

# Run backtest
bt = Backtest(data, SwiftStrength, cash=1000000, commission=0.002, exclusive_orders=True)
stats = bt.run()
print(stats)