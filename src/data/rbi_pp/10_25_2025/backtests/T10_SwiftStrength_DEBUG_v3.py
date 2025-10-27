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
data = data.set_index(pd.to_datetime(data['datetime']))
data = data[['Open', 'High', 'Low', 'Close', 'Volume']]

class SwiftStrength(Strategy):
    adx_threshold = 25
    risk_per_trade = 0.01
    rr_ratio = 2
    atr_multiplier = 1.5
    atr_period = 14
    weak_trend_threshold = 20

    def init(self):
        close = self.data.Close
        high = self.data.High
        low = self.data.Low
        self.macd, self.macdsignal, self.macdhist = self.I(talib.MACD, close, fastperiod=8, slowperiod=17, signalperiod=9)
        self.adx = self.I(talib.ADX, high, low, close, timeperiod=14)
        self.plus_di = self.I(talib.PLUS_DI, high, low, close, timeperiod=14)
        self.minus_di = self.I(talib.MINUS_DI, high, low, close, timeperiod=14)
        self.sma200 = self.I(talib.SMA, close, timeperiod=200)
        self.atr = self.I(talib.ATR, high, low, close, timeperiod=self.atr_period)
        print("🌙 Moon Dev: Indicators initialized successfully! ✨")

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

        # Emergency exit if trend weakens
        if self.position and current_adx < self.weak_trend_threshold:
            self.position.close()
            print(f"🌙 Moon Dev: Emergency exit due to weak trend (ADX < {self.weak_trend_threshold}) 📉")
            return

        # Exit on opposite MACD crossover
        if self.position.is_long and (self.macdsignal[-2] < self.macd[-2] and self.macdsignal[-1] > self.macd[-1]):
            self.position.close()
            print(f"🌙 Moon Dev: Exit long on MACD bearish reversal 🔄")
            return
        if self.position.is_short and (self.macd[-2] < self.macdsignal[-2] and self.macd[-1] > self.macdsignal[-1]):
            self.position.close()
            print(f"🌙 Moon Dev: Exit short on MACD bullish reversal 🔄")
            return

        # Entry logic only if no position
        if len(self.trades) == 0 and not self.position:
            if np.isnan(current_atr) or current_atr <= 0:
                print("🌙 Moon Dev: Invalid ATR, skipping entry 🚫")
                return

            sl_distance = self.atr_multiplier * current_atr
            risk_amount = self.equity * self.risk_per_trade
            position_size = risk_amount / sl_distance
            position_size = int(round(position_size)) if position_size > 0 else 0

            if position_size == 0:
                print("🌙 Moon Dev: Position size too small, skipping entry 🚫")
                return

            # Long entry
            if (current_adx > self.adx_threshold and
                current_plus_di > current_minus_di and
                (self.macd[-2] < self.macdsignal[-2] and self.macd[-1] > self.macdsignal[-1]) and
                current_hist > 0 and
                current_price > current_sma):

                sl = current_price - sl_distance
                tp = current_price + (self.rr_ratio * sl_distance)
                if sl >= current_price or tp <= current_price:
                    print(f"🌙 Moon Dev: Invalid SL/TP for long, skipping 🚫")
                    return
                self.buy(size=position_size, sl=sl, tp=tp)
                print(f"🌙 Moon Dev: Long entry at {current_price:.2f}, size {position_size}, SL {sl:.2f}, TP {tp:.2f} 🚀")

            # Short entry
            elif (current_adx > self.adx_threshold and
                  current_minus_di > current_plus_di and
                  (self.macdsignal[-2] < self.macd[-2] and self.macdsignal[-1] > self.macd[-1]) and
                  current_hist < 0 and
                  current_price < current_sma):

                sl = current_price + sl_distance
                tp = current_price - (self.rr_ratio * sl_distance)
                if sl <= current_price or tp >= current_price:
                    print(f"🌙 Moon Dev: Invalid SL/TP for short, skipping 🚫")
                    return
                self.sell(size=position_size, sl=sl, tp=tp)
                print(f"🌙 Moon Dev: Short entry at {current_price:.2f}, size {position_size}, SL {sl:.2f}, TP {tp:.2f} 📉")

# Run backtest
bt = Backtest(data, SwiftStrength, cash=1000000, commission=0.002, exclusive_orders=True)
stats = bt.run()
print(stats)