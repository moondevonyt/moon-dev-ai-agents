import pandas as pd
import numpy as np
import talib
from backtesting import Backtest, Strategy
import warnings
warnings.filterwarnings('ignore')

def kalman_velocity_position(close, q=0.01, r=1.0):  # 🌙 Reduced q for smoother Kalman filter, less noise in velocity estimates
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

def fib_support(high, low, period=30):  # 🌙 Shortened period for more responsive Fibonacci levels in 15m timeframe
    high_series = pd.Series(high)
    low_series = pd.Series(low)
    hh = high_series.rolling(period).max()
    ll = low_series.rolling(period).min()
    return (hh - 0.618 * (hh - ll)).values

def fib_resistance(high, low, period=30):  # 🌙 Matching shortened period
    high_series = pd.Series(high)
    low_series = pd.Series(low)
    hh = high_series.rolling(period).max()
    ll = low_series.rolling(period).min()
    return (ll + 0.618 * (hh - ll)).values

class KalmanResonance(Strategy):
    kalman_q = 0.01  # 🌙 Optimized: Lower q for reduced noise in velocity, better signal quality
    kalman_r = 1.0
    stoch_k_period = 14
    stoch_d_period = 3
    stoch_slowd = 3
    atr_period = 20
    ema_period = 200
    fib_period = 30  # 🌙 Optimized: Shorter period for dynamic support/resistance in ranging markets
    prz_tolerance = 0.003  # 🌙 Tightened: 0.3% tolerance for closer proximity to Fib levels, fewer false entries
    ranging_threshold = 0.02  # 🌙 Tightened: 2% around EMA to focus on tighter ranging, avoid wider chop
    max_bars_in_trade = 20  # 🌙 Increased: Allow more time for trades to develop in 15m BTC volatility
    trail_atr_mult = 1.2  # 🌙 Adjusted: Slightly looser trailing to capture more profit while protecting gains

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
        self.vol_ma = self.I(talib.SMA, self.data.Volume, 20)  # 🌙 Added: Volume MA for filter to avoid low-volume fakeouts
        self.trade_bars = 0
        self.entry_price = 0.0
        self.sl_price = 0.0
        self.tp_price = 0.0
        print("🌙 Moon Dev KalmanResonance Initialized ✨")

    def next(self):
        if len(self.data) < self.ema_period + self.fib_period:
            return

        if np.isnan(self.velocity[-1]) or np.isnan(self.stoch_k[-1]) or np.isnan(self.vol_ma[-1]):
            return

        equity = self._broker._cash + self.position.pl  # 🌙 Use accurate equity for dynamic risk
        risk_per_trade = 0.015 * equity  # 🌙 Increased: 1.5% risk per trade to amplify returns while staying conservative

        # Ranging check (optimized for tighter regime)
        ema_ratio = self.data.Close[-1] / self.ema[-1]
        is_ranging = (1 - self.ranging_threshold) < ema_ratio < (1 + self.ranging_threshold)

        if self.position:
            self.trade_bars += 1
            is_long = self.position.is_long
            # Check for TP hit (SL handled by broker)
            if is_long:
                if self.data.High[-1] >= self.tp_price:
                    self.position.close()
                    print(f"🌙 Moon Dev TP Exit Long at {self.data.Close[-1]:.2f} (target {self.tp_price:.2f}) 🚀")
                    return
            else:
                if self.data.Low[-1] <= self.tp_price:
                    self.position.close()
                    print(f"🌙 Moon Dev TP Exit Short at {self.data.Close[-1]:.2f} (target {self.tp_price:.2f}) 🚀")
                    return
            # Trail exit using Kalman filtered price (looser mult for better profit capture)
            trail_level = self.filtered[-1] - self.trail_atr_mult * self.atr[-1] if is_long else self.filtered[-1] + self.trail_atr_mult * self.atr[-1]
            if (is_long and self.data.Close[-1] < trail_level) or (not is_long and self.data.Close[-1] > trail_level):
                self.position.close()
                print(f"🌙 Moon Dev Trailed Exit at {self.data.Close[-1]:.2f} 🚀")
                return
            # Time-based exit
            if self.trade_bars > self.max_bars_in_trade:
                self.position.close()
                print(f"🌙 Moon Dev Time Exit after {self.trade_bars} bars 🌙")
                return
            return

        self.trade_bars = 0

        # Long Entry (tightened conditions for higher quality setups)
        if is_ranging:
            # 🌙 Optimized velocity: Require turning up with positive momentum for stronger reversal signal
            vel_turn_up = self.velocity[-1] > self.velocity[-2] and self.velocity[-1] > 0
            # 🌙 Tightened Stoch: Oversold cross below 20 for deeper, more reliable bounces
            stoch_oversold_cross = (self.stoch_k[-2] <= self.stoch_d[-2] and
                                    self.stoch_k[-1] > self.stoch_d[-1] and
                                    self.stoch_k[-1] < 20 and self.stoch_k[-2] < 20)
            near_support = abs(self.data.Close[-1] - self.fib_support[-1]) / self.data.Close[-1] < self.prz_tolerance
            # 🌙 Added volume filter: Require above-average volume for conviction in entry
            high_volume = self.data.Volume[-1] > self.vol_ma[-1]

            if vel_turn_up and stoch_oversold_cross and near_support and high_volume:
                sl = self.fib_support[-1] - 0.5 * self.atr[-1]
                stop_distance = self.data.Close[-1] - sl
                if stop_distance > 0:
                    stop_pct = stop_distance / self.data.Close[-1]
                    size = 0.015 / stop_pct  # 🌙 Matches increased risk
                    size = min(size, 0.95)
                    tp = self.data.Close[-1] + 2 * stop_distance  # Maintain 1:2 RR for positive expectancy
                    self.buy(size=size, sl=sl, tp=None)
                    self.entry_price = self.data.Close[-1]
                    self.sl_price = sl
                    self.tp_price = tp
                    print(f"🌙 Moon Dev Long Entry: Price={self.data.Close[-1]:.2f}, Size={size}, SL={sl:.2f}, TP={tp:.2f} ✨")

        # Short Entry (symmetric optimizations)
        if is_ranging:
            # 🌙 Optimized velocity: Require turning down with negative momentum for stronger reversal
            vel_turn_down = self.velocity[-1] < self.velocity[-2] and self.velocity[-1] < 0
            # 🌙 Tightened Stoch: Overbought cross above 80 for deeper, more reliable fades
            stoch_overbought_cross = (self.stoch_k[-2] >= self.stoch_d[-2] and
                                      self.stoch_k[-1] < self.stoch_d[-1] and
                                      self.stoch_k[-1] > 80 and self.stoch_k[-2] > 80)
            near_resistance = abs(self.data.Close[-1] - self.fib_resistance[-1]) / self.data.Close[-1] < self.prz_tolerance
            # 🌙 Added volume filter
            high_volume = self.data.Volume[-1] > self.vol_ma[-1]

            if vel_turn_down and stoch_overbought_cross and near_resistance and high_volume:
                sl = self.fib_resistance[-1] + 0.5 * self.atr[-1]
                stop_distance = sl - self.data.Close[-1]
                if stop_distance > 0:
                    stop_pct = stop_distance / self.data.Close[-1]
                    size = 0.015 / stop_pct
                    size = min(size, 0.95)
                    tp = self.data.Close[-1] - 2 * stop_distance  # 1:2 RR
                    self.sell(size=size, sl=sl, tp=None)
                    self.entry_price = self.data.Close[-1]
                    self.sl_price = sl
                    self.tp_price = tp
                    print(f"🌙 Moon Dev Short Entry: Price={self.data.Close[-1]:.2f}, Size={size}, SL={sl:.2f}, TP={tp:.2f} ✨")

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