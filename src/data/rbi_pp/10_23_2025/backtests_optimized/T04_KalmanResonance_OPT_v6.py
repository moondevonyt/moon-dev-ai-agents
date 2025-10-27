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

def fib_support(high, low, period=20):  # Shortened period to 20 for more dynamic Fib levels in 15m timeframe 🌙
    high_series = pd.Series(high)
    low_series = pd.Series(low)
    hh = high_series.rolling(period).max()
    ll = low_series.rolling(period).min()
    return (hh - 0.618 * (hh - ll)).values

def fib_resistance(high, low, period=20):  # Matching shortened period for consistency ✨
    high_series = pd.Series(high)
    low_series = pd.Series(low)
    hh = high_series.rolling(period).max()
    ll = low_series.rolling(period).min()
    return (ll + 0.618 * (hh - ll)).values

class KalmanResonance(Strategy):
    kalman_q = 0.1
    kalman_r = 1.0
    stoch_k_period = 14
    stoch_d_period = 3
    stoch_slowd = 3
    atr_period = 14  # Standardized to 14 for better alignment with other indicators 🚀
    ema_period = 50  # Reduced from 200 to 50 for faster ranging detection on 15m charts, capturing more setups 🌙
    fib_period = 20  # Already adjusted in functions
    prz_tolerance = 0.003  # Kept tight for precision near Fib levels
    ranging_threshold = 0.08  # Relaxed slightly to 8% for more ranging opportunities without excessive noise ✨
    max_bars_in_trade = 8  # Reduced from 10 to exit non-performers quicker, improving capital turnover
    trail_atr_mult = 1.8  # Adjusted to 1.8x ATR: tighter than 2.0 to lock profits sooner while allowing some room

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
        # Kept ADX for ranging confirmation
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        # Kept volume SMA for momentum
        self.avg_vol = self.I(talib.SMA, self.data.Volume, timeperiod=20)
        # Added RSI for additional oversold/overbought confirmation to filter better entries 🌙
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14)
        self.trade_bars = 0
        self.entry_price = 0.0
        self.sl_price = 0.0
        self.tp_price = 0.0
        self.trail_stop = 0.0  # Initialized for trailing stop management
        print("🌙 Moon Dev KalmanResonance Initialized ✨")

    def next(self):
        if len(self.data) < max(self.ema_period, self.fib_period, 20, 14):
            return

        if np.isnan(self.velocity[-1]) or np.isnan(self.stoch_k[-1]) or np.isnan(self.adx[-1]) or np.isnan(self.rsi[-1]):
            return

        equity = self._broker._cash  # Use broker cash for accurate equity in position sizing
        risk_per_trade = 0.02 * equity  # Increased to 2% risk per trade to amplify returns while staying managed 🚀

        # Ranging check (relaxed threshold)
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
                    self.trail_stop = 0.0
                    return
            else:
                if self.data.Low[-1] <= self.tp_price:
                    self.position.close()
                    print(f"🌙 Moon Dev TP Exit Short at {self.data.Close[-1]:.2f} (target {self.tp_price:.2f}) 🚀")
                    self.trail_stop = 0.0
                    return
            # Improved trailing stop: persistent, updates based on close -/+ ATR, starts at SL
            if is_long:
                new_trail = self.data.Close[-1] - self.trail_atr_mult * self.atr[-1]
                self.trail_stop = max(self.trail_stop, new_trail)
                if self.data.Close[-1] <= self.trail_stop:
                    self.position.close()
                    print(f"🌙 Moon Dev Trailed Exit Long at {self.data.Close[-1]:.2f} (trail {self.trail_stop:.2f}) 🚀")
                    self.trail_stop = 0.0
                    return
            else:
                new_trail = self.data.Close[-1] + self.trail_atr_mult * self.atr[-1]
                self.trail_stop = min(self.trail_stop, new_trail)
                if self.data.Close[-1] >= self.trail_stop:
                    self.position.close()
                    print(f"🌙 Moon Dev Trailed Exit Short at {self.data.Close[-1]:.2f} (trail {self.trail_stop:.2f}) 🚀")
                    self.trail_stop = 0.0
                    return
            # Time-based exit (shortened)
            if self.trade_bars > self.max_bars_in_trade:
                self.position.close()
                print(f"🌙 Moon Dev Time Exit after {self.trade_bars} bars 🌙")
                self.trail_stop = 0.0
                return
            return

        self.trade_bars = 0
        self.trail_stop = 0.0  # Reset on no position

        # Enhanced Long Entry: Relaxed velocity to positive and accelerating (more setups), Stoch <30, RSI<35, near support, ADX<25, volume > avg
        if is_ranging and self.adx[-1] < 25:
            vel_positive_accel = self.velocity[-1] > 0 and self.velocity[-1] > self.velocity[-2]  # Changed to positive and increasing for broader momentum capture ✨
            stoch_oversold_cross = (self.stoch_k[-2] <= self.stoch_d[-2] and
                                    self.stoch_k[-1] > self.stoch_d[-1] and
                                    self.stoch_k[-1] < 30 and self.stoch_k[-2] < 30)  # Relaxed to 30 for more oversold opportunities
            rsi_oversold = self.rsi[-1] < 35  # Added RSI <35 for stronger oversold confirmation without over-filtering
            near_support = abs(self.data.Close[-1] - self.fib_support[-1]) / self.data.Close[-1] < self.prz_tolerance
            vol_confirm = self.data.Volume[-1] > self.avg_vol[-1]  # Kept for momentum

            if vel_positive_accel and stoch_oversold_cross and near_support and vol_confirm and rsi_oversold:
                sl = self.fib_support[-1] - 0.5 * self.atr[-1]
                stop_distance = self.data.Close[-1] - sl
                if stop_distance > 0:
                    stop_pct = stop_distance / self.data.Close[-1]
                    size = risk_per_trade / (self.data.Close[-1] * stop_pct) / self.data.Close[-1]  # Corrected sizing: risk / (price * stop_pct) for shares, but normalized
                    size = min(size, 0.95)  # Ensure fraction 0-1
                    tp = self.data.Close[-1] + 2 * stop_distance  # Keep 1:2 RR
                    self.buy(size=size, sl=sl, tp=None)
                    self.entry_price = self.data.Close[-1]
                    self.sl_price = sl
                    self.tp_price = tp
                    self.trail_stop = sl  # Initialize trail at SL for upward movement
                    print(f"🌙 Moon Dev Long Entry: Price={self.data.Close[-1]:.2f}, Size={size}, SL={sl:.2f}, TP={tp:.2f} ✨")

        # Enhanced Short Entry: Similar relaxations for shorts
        if is_ranging and self.adx[-1] < 25:
            vel_negative_decel = self.velocity[-1] < 0 and self.velocity[-1] < self.velocity[-2]  # Negative and accelerating downward
            stoch_overbought_cross = (self.stoch_k[-2] >= self.stoch_d[-2] and
                                      self.stoch_k[-1] < self.stoch_d[-1] and
                                      self.stoch_k[-1] > 70 and self.stoch_k[-2] > 70)  # Relaxed to 70
            rsi_overbought = self.rsi[-1] > 65  # Added RSI >65 for overbought
            near_resistance = abs(self.data.Close[-1] - self.fib_resistance[-1]) / self.data.Close[-1] < self.prz_tolerance
            vol_confirm = self.data.Volume[-1] > self.avg_vol[-1]  # Volume spike

            if vel_negative_decel and stoch_overbought_cross and near_resistance and vol_confirm and rsi_overbought:
                sl = self.fib_resistance[-1] + 0.5 * self.atr[-1]
                stop_distance = sl - self.data.Close[-1]
                if stop_distance > 0:
                    stop_pct = stop_distance / self.data.Close[-1]
                    size = risk_per_trade / (self.data.Close[-1] * stop_pct) / self.data.Close[-1]
                    size = min(size, 0.95)
                    tp = self.data.Close[-1] - 2 * stop_distance  # Keep 1:2 RR
                    self.sell(size=size, sl=sl, tp=None)
                    self.entry_price = self.data.Close[-1]
                    self.sl_price = sl
                    self.tp_price = tp
                    self.trail_stop = sl  # Initialize trail at SL for downward movement
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