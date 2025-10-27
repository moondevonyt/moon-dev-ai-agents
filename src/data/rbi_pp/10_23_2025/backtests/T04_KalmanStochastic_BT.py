import pandas as pd
import numpy as np
import talib
from backtesting import Backtest, Strategy

def kalman_filter(prices, Q=0.1, R=1.0):
    prices = np.asarray(prices)
    n = len(prices)
    if n == 0:
        return np.array([])
    mu = np.zeros(n)
    sigma2 = np.zeros(n)
    mu[0] = prices[0]
    sigma2[0] = 1.0
    for t in range(1, n):
        mu_pred = mu[t-1]
        sigma2_pred = sigma2[t-1] + Q
        K = sigma2_pred / (sigma2_pred + R)
        mu[t] = mu_pred + K * (prices[t] - mu_pred)
        sigma2[t] = (1 - K) * sigma2_pred
    return mu

class KalmanStochastic(Strategy):
    kalman_length = 50  # lookback for init, but computed full
    stoch_k_period = 14
    stoch_d_period = 3
    sma_period = 5
    slope_period = 10
    atr_period = 14
    volume_sma_period = 20
    risk_percent = 0.01
    stop_multiplier = 2.0
    reward_multiplier = 2.0
    vol_threshold = 1.5
    Q = 0.1
    R = 1.0

    def init(self):
        self.kalman = self.I(kalman_filter, self.data.Close, Q=self.Q, R=self.R)
        self.stoch_k, self.stoch_d = self.I(talib.STOCH, self.data.High, self.data.Low, self.data.Close,
                                            fastk_period=self.stoch_k_period, slowk_period=self.stoch_d_period, slowd_period=self.stoch_d_period)
        self.kalman_sma = self.I(talib.SMA, self.kalman, timeperiod=self.sma_period)
        self.slope = self.I(talib.LINEARREG_SLOPE, self.kalman, timeperiod=self.slope_period)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=self.atr_period)
        self.atr_sma = self.I(talib.SMA, self.atr, timeperiod=self.atr_period)
        self.volume_sma = self.I(talib.SMA, self.data.Volume, timeperiod=self.volume_sma_period)
        🌙 self.debug_print("Moon Dev: Indicators initialized ✨")

    def next(self):
        if len(self.data) < max(self.slope_period, self.atr_period, self.volume_sma_period) + 5:
            return

        # Volume filter
        if self.data.Volume[-1] < 0.5 * self.volume_sma[-1]:
            🌙 self.debug_print("Moon Dev: Low volume, skipping entry 🚫")
            return

        # Volatility adjustment
        size_adjust = 1.0
        if self.atr[-1] > self.vol_threshold * self.atr_sma[-1]:
            size_adjust = 0.5
            🌙 self.debug_print("Moon Dev: High volatility, reducing size 📉")

        # Trailing and alternative exits
        if self.position:
            entry_price = self.position.entry_price
            if self.position.is_long:
                # Breakeven after 1:1
                if self.data.Close[-1] >= entry_price * 1.01:
                    self.position.sl = max(self.position.sl, entry_price)
                # Trail using Kalman
                trail_sl = self.kalman[-1] - self.atr[-1]
                self.position.sl = max(self.position.sl, trail_sl)
                # Stochastic exit
                if self.stoch_k[-1] > 80:
                    self.position.close()
                    🌙 self.debug_print(f"Moon Dev: Long exit on overbought Stochastic 🚀💥 Close: {self.data.Close[-1]}")
            else:  # short
                # Breakeven after 1:1
                if self.data.Close[-1] <= entry_price * 0.99:
                    self.position.sl = min(self.position.sl, entry_price)
                # Trail using Kalman
                trail_sl = self.kalman[-1] + self.atr[-1]
                self.position.sl = min(self.position.sl, trail_sl)
                # Stochastic exit
                if self.stoch_k[-1] < 20:
                    self.position.close()
                    🌙 self.debug_print(f"Moon Dev: Short exit on oversold Stochastic 🌙💥 Close: {self.data.Close[-1]}")
            # Time-based exit (10 bars)
            if hasattr(self.position, '_age') and self.position._age >= 10:
                self.position.close()
                🌙 self.debug_print("Moon Dev: Time-based exit ⏰")
            self.position._age = getattr(self.position, '_age', 0) + 1
            return

        # Long entry
        kalman_cross_up = self.kalman[-1] > self.kalman_sma[-1] and self.kalman[-2] <= self.kalman_sma[-2]
        stoch_cross_up = self.stoch_k[-1] > self.stoch_d[-1] and self.stoch_k[-2] <= self.stoch_d[-2]
        stoch_oversold = self.stoch_k[-1] < 20
        trend_up = self.slope[-1] > 0

        if kalman_cross_up and stoch_cross_up and stoch_oversold and trend_up:
            entry = self.data.Close[-1]
            stop_distance = self.stop_multiplier * self.atr[-1]
            risk_frac = stop_distance / entry
            risk_amount = self.risk_percent * self.equity
            position_value = risk_amount / risk_frac
            size = int(round((position_value / entry) * size_adjust))
            if size > 0:
                sl_price = entry - stop_distance
                self.buy(size=size, sl=sl_price)
                self.position._age = 0
                🌙 self.debug_print(f"Moon Dev: LONG entry at {entry}, size {size}, SL {sl_price} 🚀🌙")

        # Short entry
        kalman_cross_down = self.kalman[-1] < self.kalman_sma[-1] and self.kalman[-2] >= self.kalman_sma[-2]
        stoch_cross_down = self.stoch_k[-1] < self.stoch_d[-1] and self.stoch_k[-2] >= self.stoch_d[-2]
        stoch_overbought = self.stoch_k[-1] > 80
        trend_down = self.slope[-1] < 0

        if kalman_cross_down and stoch_cross_down and stoch_overbought and trend_down:
            entry = self.data.Close[-1]
            stop_distance = self.stop_multiplier * self.atr[-1]
            risk_frac = stop_distance / entry
            risk_amount = self.risk_percent * self.equity
            position_value = risk_amount / risk_frac
            size = int(round((position_value / entry) * size_adjust))
            if size > 0:
                sl_price = entry + stop_distance
                self.sell(size=size, sl=sl_price)
                self.position._age = 0
                🌙 self.debug_print(f"Moon Dev: SHORT entry at {entry}, size {size}, SL {sl_price} 🌙📉")

    def debug_print(self, msg):
        print(msg)

# Data loading and cleaning
path = '/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv'
data = pd.read_csv(path, parse_dates=['datetime'], index_col='datetime')
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data = data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
})
🌙 print("Moon Dev: Data loaded and cleaned ✨")

bt = Backtest(data, KalmanStochastic, cash=1000000, commission=0.001)
stats = bt.run()
print(stats)
print(stats._strategy)