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

def fib_support(high, low, period=34):  # Changed to 34 for golden ratio alignment, better Fib levels 🌙
    high_series = pd.Series(high)
    low_series = pd.Series(low)
    hh = high_series.rolling(period).max()
    ll = low_series.rolling(period).min()
    return (hh - 0.618 * (hh - ll)).values

def fib_resistance(high, low, period=34):  # Matching period change for consistency ✨
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
    atr_period = 20
    ema_period = 200
    fib_period = 34  # Optimized Fib period for more accurate support/resistance in BTC volatility 🚀
    prz_tolerance = 0.002  # Tightened further to 0.2% for higher precision entries near key levels 🌙
    ranging_threshold = 0.06  # Loosened to 6% to capture more ranging opportunities without excessive noise ✨
    max_bars_in_trade = 20  # Increased to 20 bars to allow more room for profitable moves in ranges
    trail_atr_mult = 1.8  # Adjusted to 1.8x ATR for balanced profit locking - tighter than 2.0 but not too aggressive

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
        # Retained ADX, tightened threshold in entries
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        # Retained volume SMA
        self.avg_vol = self.I(talib.SMA, self.data.Volume, timeperiod=20)
        # Added RSI for complementary oversold/overbought confirmation to filter better setups 🌙
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

        equity = self.equity
        risk_per_trade = 0.015 * equity  # Increased to 1.5% risk per trade for higher return potential while managing drawdown 🚀

        # Ranging check (adjusted threshold)
        ema_ratio = self.data.Close[-1] / self.ema[-1]
        is_ranging = (1 - self.ranging_threshold) < ema_ratio < (1 + self.ranging_threshold)

        if self.position:
            self.trade_bars += 1
            is_long = self.position.is_long
            # Check for TP hit (SL handled by broker) - now at improved RR
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
            # Time-based exit (extended)
            if self.trade_bars > self.max_bars_in_trade:
                self.position.close()
                print(f"🌙 Moon Dev Time Exit after {self.trade_bars} bars 🌙")
                self.trail_stop = 0.0
                return
            return

        self.trade_bars = 0
        self.trail_stop = 0.0  # Reset on no position

        # Enhanced Long Entry: Added RSI <25, tightened Stoch <15, ADX<22, vol>1.1x, stricter velocity cross
        if is_ranging and self.adx[-1] < 22:  # Tightened ADX for purer ranging conditions ✨
            vel_cross_up = self.velocity[-2] < 0 and self.velocity[-1] > 0  # Strict cross to positive velocity
            stoch_oversold_cross = (self.stoch_k[-2] <= self.stoch_d[-2] and
                                    self.stoch_k[-1] > self.stoch_d[-1] and
                                    self.stoch_k[-1] < 15 and self.stoch_k[-2] < 15)  # Deepened to 15 for stronger oversold signals 🌙
            near_support = abs(self.data.Close[-1] - self.fib_support[-1]) / self.data.Close[-1] < self.prz_tolerance
            vol_confirm = self.data.Volume[-1] > 1.1 * self.avg_vol[-1]  # Slightly higher volume threshold for better momentum filter
            rsi_oversold = self.rsi[-1] < 25  # Added RSI confirmation for deeper oversold to reduce false signals 🚀

            if vel_cross_up and stoch_oversold_cross and near_support and vol_confirm and rsi_oversold:
                sl = self.fib_support[-1] - 0.5 * self.atr[-1]
                stop_distance = self.data.Close[-1] - sl
                if stop_distance > 0:
                    stop_pct = stop_distance / self.data.Close[-1]
                    size = risk_per_trade / (self.data.Close[-1] * stop_pct) / self.data.Close[-1]  # Corrected size calc for % risk
                    size = min(size, 0.95)
                    tp = self.data.Close[-1] + 2.5 * stop_distance  # Improved to 1:2.5 RR for higher reward potential without overreaching
                    self.buy(size=size, sl=sl, tp=None)
                    self.entry_price = self.data.Close[-1]
                    self.sl_price = sl
                    self.tp_price = tp
                    self.trail_stop = sl  # Initialize trail at SL for upward movement
                    print(f"🌙 Moon Dev Long Entry: Price={self.data.Close[-1]:.2f}, Size={size}, SL={sl:.2f}, TP={tp:.2f} ✨")

        # Enhanced Short Entry: Matching improvements for symmetry
        if is_ranging and self.adx[-1] < 22:
            vel_cross_down = self.velocity[-2] > 0 and self.velocity[-1] < 0  # Strict cross to negative velocity
            stoch_overbought_cross = (self.stoch_k[-2] >= self.stoch_d[-2] and
                                      self.stoch_k[-1] < self.stoch_d[-1] and
                                      self.stoch_k[-1] > 85 and self.stoch_k[-2] > 85)  # Deepened to 85 for stronger overbought signals 🌙
            near_resistance = abs(self.data.Close[-1] - self.fib_resistance[-1]) / self.data.Close[-1] < self.prz_tolerance
            vol_confirm = self.data.Volume[-1] > 1.1 * self.avg_vol[-1]  # Matching volume filter
            rsi_overbought = self.rsi[-1] > 75  # Added RSI confirmation for deeper overbought 🚀

            if vel_cross_down and stoch_overbought_cross and near_resistance and vol_confirm and rsi_overbought:
                sl = self.fib_resistance[-1] + 0.5 * self.atr[-1]
                stop_distance = sl - self.data.Close[-1]
                if stop_distance > 0:
                    stop_pct = stop_distance / self.data.Close[-1]
                    size = risk_per_trade / (self.data.Close[-1] * stop_pct) / self.data.Close[-1]  # Corrected size calc
                    size = min(size, 0.95)
                    tp = self.data.Close[-1] - 2.5 * stop_distance  # Matching 1:2.5 RR
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