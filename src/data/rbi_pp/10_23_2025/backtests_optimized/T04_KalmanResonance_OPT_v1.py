import pandas as pd
import numpy as np
import talib
from backtesting import Backtest, Strategy
import warnings
warnings.filterwarnings('ignore')

def kalman_velocity_position(close, q=0.1, r=1.0):
    close = close.astype(float)
    n = len(close)
    if n == 0:
        return np.array([]), np.array([])
    filtered = np.full(n, np.nan)
    velocity = np.full(n, np.nan)
    x = np.array([close[0], 0.0])
    P_mat = np.eye(2) * 1000.0
    dt = 1.0
    F = np.array([[1.0, dt], [0.0, 1.0]])
    H = np.array([1.0, 0.0])
    Q_base = np.array([[dt**3 / 3, dt**2 / 2], [dt**2 / 2, dt]])
    for i in range(n):
        # Predict
        x = F @ x
        P_mat = F @ P_mat @ F.T + Q_base * q
        # Update
        y = close[i] - H @ x
        S = H @ P_mat @ H + r
        K = (P_mat @ H) / S
        x = x + K * y
        P_mat = (np.eye(2) - np.outer(K, H)) @ P_mat
        filtered[i] = x[0]
        velocity[i] = x[1]
    return filtered, velocity

def fib_support(high, low, period=50):
    high_series = pd.Series(high)
    low_series = pd.Series(low)
    hh = high_series.rolling(period).max()
    ll = low_series.rolling(period).min()
    return (hh - 0.618 * (hh - ll)).values

def fib_resistance(high, low, period=50):
    high_series = pd.Series(high)
    low_series = pd.Series(low)
    hh = high_series.rolling(period).max()
    ll = low_series.rolling(period).min()
    return (ll + 0.618 * (hh - ll)).values

class KalmanResonance(Strategy):
    kalman_q = 0.2  # 🌙 Moon Dev: Increased q for more responsive velocity detection to catch turns earlier
    kalman_r = 0.5  # 🌙 Moon Dev: Decreased r to trust price more, reducing lag in filtered velocity
    stoch_k_period = 14
    stoch_d_period = 3
    stoch_slowd = 3
    stoch_oversold = 25  # 🌙 Moon Dev: Tightened oversold level from 30 to 25 for higher quality bounce signals
    stoch_overbought = 75  # 🌙 Moon Dev: Tightened overbought level from 70 to 75 for better short setups
    atr_period = 20
    ema_period = 200
    fib_period = 50
    adx_period = 14  # 🌙 Moon Dev: Added ADX for better ranging market detection (replaces loose EMA ratio)
    prz_tolerance = 0.003  # 🌙 Moon Dev: Tightened tolerance from 0.005 to 0.003 for closer fib proximity, reducing false entries
    ranging_threshold_adx = 25  # 🌙 Moon Dev: ADX < 25 indicates ranging/choppy conditions ideal for resonance bounces
    max_bars_in_trade = 20  # 🌙 Moon Dev: Extended from 15 to 20 bars to allow more room for bounces in 15m timeframe
    trail_atr_mult = 1.5  # 🌙 Moon Dev: Increased trailing multiplier from 1.0 to 1.5 for looser trailing, letting winners run longer
    rr_ratio = 3  # 🌙 Moon Dev: Improved RR from 2:1 to 3:1 for higher reward potential per trade
    risk_per_trade_pct = 0.01  # 1% risk, but now properly used in sizing

    def init(self):
        self.filtered, self.velocity = self.I(kalman_velocity_position, self.data.Close, self.kalman_q, self.kalman_r)
        slowk, slowd = self.I(talib.STOCH, self.data.High, self.data.Low, self.data.Close,
                               fastk_period=self.stoch_k_period, slowk_period=self.stoch_d_period, slowd_period=self.stoch_slowd)
        self.stoch_k = slowk
        self.stoch_d = slowd
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=self.atr_period)
        self.ema = self.I(talib.EMA, self.data.Close, timeperiod=self.ema_period)
        self.fib_support = self.I(fib_support, self.data.High, self.data.Low, self.fib_period)
        self.fib_resistance = self.I(fib_resistance, self.data.High, self.data.Low, self.fib_period)
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=self.adx_period)  # 🌙 Moon Dev: New ADX indicator for regime filter
        self.trade_bars = 0
        self.entry_price = 0.0
        self.sl_price = 0.0
        self.tp_price = 0.0
        print("🌙 Moon Dev KalmanResonance Optimized: Enhanced filters, proper sizing, and trailing for 50% target! ✨")

    def next(self):
        if len(self.data) < max(self.ema_period, self.fib_period, self.adx_period):
            return

        if np.isnan(self.velocity[-1]) or np.isnan(self.stoch_k[-1]) or np.isnan(self.adx[-1]):
            return

        # 🌙 Moon Dev: Improved regime filter using ADX < 25 for true ranging markets, avoiding trend traps
        is_ranging = self.adx[-1] < self.ranging_threshold_adx

        if self.position:
            self.trade_bars += 1
            is_long = self.position.is_long

            # 🌙 Moon Dev: Manual initial SL check (since sl=None to allow trailing updates)
            if is_long:
                if self.data.Low[-1] <= self.sl_price:
                    self.position.close()
                    print(f"🌙 Moon Dev SL Exit Long at {self.data.Close[-1]:.2f} (SL {self.sl_price:.2f}) 💥")
                    self.trade_bars = 0
                    if hasattr(self, 'highest'):
                        delattr(self, 'highest')
                    return
            else:
                if self.data.High[-1] >= self.sl_price:
                    self.position.close()
                    print(f"🌙 Moon Dev SL Exit Short at {self.data.Close[-1]:.2f} (SL {self.sl_price:.2f}) 💥")
                    self.trade_bars = 0
                    if hasattr(self, 'lowest'):
                        delattr(self, 'lowest')
                    return

            # 🌙 Moon Dev: Manual TP check for 3:1 RR
            if is_long:
                if self.data.High[-1] >= self.tp_price:
                    self.position.close()
                    print(f"🌙 Moon Dev TP Exit Long at {self.data.Close[-1]:.2f} (target {self.tp_price:.2f}) 🚀")
                    self.trade_bars = 0
                    if hasattr(self, 'highest'):
                        delattr(self, 'highest')
                    return
            else:
                if self.data.Low[-1] <= self.tp_price:
                    self.position.close()
                    print(f"🌙 Moon Dev TP Exit Short at {self.data.Close[-1]:.2f} (target {self.tp_price:.2f}) 🚀")
                    self.trade_bars = 0
                    if hasattr(self, 'lowest'):
                        delattr(self, 'lowest')
                    return

            # 🌙 Moon Dev: Improved trailing stop using running high/low + ATR, starts immediately but tightens as profit grows
            if is_long:
                if not hasattr(self, 'highest'):
                    self.highest = self.data.High[-1]
                self.highest = max(self.highest, self.data.High[-1])
                trail_stop = self.highest - self.trail_atr_mult * self.atr[-1]
                if self.data.Low[-1] <= trail_stop:
                    self.position.close()
                    print(f"🌙 Moon Dev Trailing Exit Long at {self.data.Close[-1]:.2f} (trail {trail_stop:.2f}) 🌙")
                    self.trade_bars = 0
                    delattr(self, 'highest')
                    return
            else:
                if not hasattr(self, 'lowest'):
                    self.lowest = self.data.Low[-1]
                self.lowest = min(self.lowest, self.data.Low[-1])
                trail_stop = self.lowest + self.trail_atr_mult * self.atr[-1]
                if self.data.High[-1] >= trail_stop:
                    self.position.close()
                    print(f"🌙 Moon Dev Trailing Exit Short at {self.data.Close[-1]:.2f} (trail {trail_stop:.2f}) 🌙")
                    self.trade_bars = 0
                    delattr(self, 'lowest')
                    return

            # Time-based exit
            if self.trade_bars > self.max_bars_in_trade:
                self.position.close()
                print(f"🌙 Moon Dev Time Exit after {self.trade_bars} bars 🌙")
                self.trade_bars = 0
                if hasattr(self, 'highest'):
                    delattr(self, 'highest')
                if hasattr(self, 'lowest'):
                    delattr(self, 'lowest')
                return
            return

        self.trade_bars = 0

        if not is_ranging:  # Only trade in ranging conditions
            return

        equity = self._broker._cash + self.position.pl  # Approximate current equity for sizing
        risk_per_trade = self.risk_per_trade_pct * equity

        close_price = self.data.Close[-1]

        # 🌙 Moon Dev: Long Entry - Tightened to velocity cross only (removed loose decel), stricter stoch, fib filter
        vel_cross_up = self.velocity[-2] < 0 and self.velocity[-1] > 0  # Strict cross up for momentum confirmation
        stoch_oversold_cross = (self.stoch_k[-2] <= self.stoch_d[-2] and
                                self.stoch_k[-1] > self.stoch_d[-1] and
                                self.stoch_k[-1] < self.stoch_oversold and self.stoch_k[-2] < self.stoch_oversold)
        near_support = abs(close_price - self.fib_support[-1]) / close_price < self.prz_tolerance

        if vel_cross_up and stoch_oversold_cross and near_support:
            sl = self.fib_support[-1] - 0.5 * self.atr[-1]
            stop_distance = close_price - sl
            if stop_distance > 0:
                # 🌙 Moon Dev: Fixed position sizing bug - now properly risks 1% of equity based on stop distance
                size = risk_per_trade / stop_distance
                # Cap exposure at 95% of equity
                max_size = (equity * 0.95) / close_price
                size = min(size, max_size)
                tp = close_price + self.rr_ratio * stop_distance  # 1:3 RR for better returns
                self.buy(size=size, sl=None, tp=None)  # Manual exits for trailing
                self.entry_price = close_price
                self.sl_price = sl
                self.tp_price = tp
                print(f"🌙 Moon Dev Long Entry: Price={close_price:.2f}, Size={size:.4f}, SL={sl:.2f}, TP={tp:.2f} ✨")

        # 🌙 Moon Dev: Short Entry - Symmetric improvements
        vel_cross_down = self.velocity[-2] > 0 and self.velocity[-1] < 0  # Strict cross down
        stoch_overbought_cross = (self.stoch_k[-2] >= self.stoch_d[-2] and
                                  self.stoch_k[-1] < self.stoch_d[-1] and
                                  self.stoch_k[-1] > self.stoch_overbought and self.stoch_k[-2] > self.stoch_overbought)
        near_resistance = abs(close_price - self.fib_resistance[-1]) / close_price < self.prz_tolerance

        if vel_cross_down and stoch_overbought_cross and near_resistance:
            sl = self.fib_resistance[-1] + 0.5 * self.atr[-1]
            stop_distance = sl - close_price
            if stop_distance > 0:
                size = risk_per_trade / stop_distance
                max_size = (equity * 0.95) / close_price
                size = min(size, max_size)
                tp = close_price - self.rr_ratio * stop_distance  # 1:3 RR
                self.sell(size=size, sl=None, tp=None)
                self.entry_price = close_price
                self.sl_price = sl
                self.tp_price = tp
                print(f"🌙 Moon Dev Short Entry: Price={close_price:.2f}, Size={size:.4f}, SL={sl:.2f}, TP={tp:.2f} ✨")

if __name__ == '__main__':
    data_path = '/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv'
    data = pd.read_csv(data_path)
    data.columns = data.columns.str.strip().str.lower()
    data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
    data = data.rename(columns={
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume'
    })
    data = data.set_index(pd.to_datetime(data['datetime']))
    data = data.drop('datetime', axis=1)
    data = data[['Open', 'High', 'Low', 'Close', 'Volume']]
    print(f"🌙 Moon Dev Data Loaded: {len(data)} bars 🚀")
    bt = Backtest(data, KalmanResonance, cash=1000000, commission=0.002, exclusive_orders=True)
    stats = bt.run()
    print(stats)