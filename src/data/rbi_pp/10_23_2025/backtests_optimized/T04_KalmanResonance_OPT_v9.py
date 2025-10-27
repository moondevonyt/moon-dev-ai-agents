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
    kalman_q = 0.05  # Smoothed Kalman for better velocity detection in ranging markets 🌙
    kalman_r = 1.0
    stoch_k_period = 14
    stoch_d_period = 3
    stoch_slowd = 3
    stoch_oversold_level = 25  # Loosened for more quality oversold signals without too many false positives ✨
    stoch_overbought_level = 75
    atr_period = 14  # Standard ATR period for more responsive volatility on 15m timeframe 🚀
    ema_period = 200
    fib_period = 30  # Shorter Fib period for quicker adaptation to recent swings in ranging conditions
    prz_tolerance = 0.005  # Slightly loosened to 0.5% to capture more precise but feasible Fib bounces
    ranging_threshold = 0.07  # Expanded to 7% around EMA to allow more ranging opportunities while filtering trends
    adx_threshold = 22  # Tightened ADX for stricter ranging confirmation (lower trend strength) 🌙
    vol_mult = 1.5  # Require stronger volume spike for momentum confirmation on entries ✨
    rsi_oversold = 35
    rsi_overbought = 65
    risk_pct = 0.01  # 1% risk per trade based on equity (fixed critical bug in prior sizing) 🚀
    max_bars_in_trade = 15  # Extended to allow time for 1:3 RR targets with trailing
    trail_atr_mult = 2.5  # Loosened trailing to let profits run further towards higher RR goals

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
        # Added ADX for ranging confirmation (ADX < 25 indicates low trend strength) 🌙
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        # Added volume SMA for momentum confirmation on entries ✨
        self.avg_vol = self.I(talib.SMA, self.data.Volume, timeperiod=20)
        # Added RSI for complementary oversold/overbought filter to improve entry quality 🚀
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14)
        self.trade_bars = 0
        self.entry_price = 0.0
        self.sl_price = 0.0
        self.tp_price = 0.0
        self.trail_stop = 0.0  # Initialized for trailing stop management
        self.initial_risk = 0.0
        self.be_moved = False
        print("🌙 Moon Dev KalmanResonance Initialized ✨")

    def reset_trade_vars(self):
        self.trade_bars = 0
        self.entry_price = 0.0
        self.sl_price = 0.0
        self.tp_price = 0.0
        self.trail_stop = 0.0
        self.initial_risk = 0.0
        self.be_moved = False

    def next(self):
        if len(self.data) < max(self.ema_period, self.fib_period, 20, 14):
            return

        if np.isnan(self.velocity[-1]) or np.isnan(self.stoch_k[-1]) or np.isnan(self.adx[-1]) or np.isnan(self.rsi[-1]):
            return

        equity = self.equity
        risk_per_trade = self.risk_pct * equity

        # Ranging check (adjusted for more opportunities)
        ema_ratio = self.data.Close[-1] / self.ema[-1]
        is_ranging = (1 - self.ranging_threshold) < ema_ratio < (1 + self.ranging_threshold)

        if self.position:
            self.trade_bars += 1
            is_long = self.position.is_long
            # Enhanced exit management: manual stops for BE move + trailing (set sl=None in orders) 🌙
            if is_long:
                # Move to breakeven after 1R
                if not self.be_moved and self.data.Close[-1] >= self.entry_price + self.initial_risk:
                    self.sl_price = self.entry_price
                    self.be_moved = True
                    print(f"🌙 Moon Dev Moved SL to Breakeven Long at {self.data.Close[-1]:.2f} 🚀")
                # Update trailing stop
                new_trail = self.data.Close[-1] - self.trail_atr_mult * self.atr[-1]
                self.trail_stop = max(self.trail_stop, new_trail)
                effective_stop = max(self.sl_price, self.trail_stop)
                # Check SL/Trail hit
                if self.data.Low[-1] <= effective_stop:
                    self.position.close()
                    print(f"🌙 Moon Dev SL/Trail Exit Long at {self.data.Close[-1]:.2f} (stop {effective_stop:.2f}) 🚀")
                    self.reset_trade_vars()
                    return
                # Check TP hit (improved to 1:3 RR for higher returns) ✨
                if self.data.High[-1] >= self.tp_price:
                    self.position.close()
                    print(f"🌙 Moon Dev TP Exit Long at {self.data.Close[-1]:.2f} (target {self.tp_price:.2f}) 🚀")
                    self.reset_trade_vars()
                    return
            else:  # Short
                # Move to breakeven after 1R
                if not self.be_moved and self.data.Close[-1] <= self.entry_price - self.initial_risk:
                    self.sl_price = self.entry_price
                    self.be_moved = True
                    print(f"🌙 Moon Dev Moved SL to Breakeven Short at {self.data.Close[-1]:.2f} 🚀")
                # Update trailing stop
                new_trail = self.data.Close[-1] + self.trail_atr_mult * self.atr[-1]
                self.trail_stop = min(self.trail_stop, new_trail)
                effective_stop = min(self.sl_price, self.trail_stop)
                # Check SL/Trail hit
                if self.data.High[-1] >= effective_stop:
                    self.position.close()
                    print(f"🌙 Moon Dev SL/Trail Exit Short at {self.data.Close[-1]:.2f} (stop {effective_stop:.2f}) 🚀")
                    self.reset_trade_vars()
                    return
                # Check TP hit
                if self.data.Low[-1] <= self.tp_price:
                    self.position.close()
                    print(f"🌙 Moon Dev TP Exit Short at {self.data.Close[-1]:.2f} (target {self.tp_price:.2f}) 🚀")
                    self.reset_trade_vars()
                    return
            # Time-based exit (extended for 1:3 RR potential)
            if self.trade_bars > self.max_bars_in_trade:
                self.position.close()
                print(f"🌙 Moon Dev Time Exit after {self.trade_bars} bars 🌙")
                self.reset_trade_vars()
                return
            return

        self.reset_trade_vars()

        # Enhanced Long Entry: Strict conditions + RSI filter + volume mult + equity-based sizing 🌙
        if is_ranging and self.adx[-1] < self.adx_threshold:
            vel_cross_up = self.velocity[-2] < 0 and self.velocity[-1] > 0  # Strict cross to positive velocity
            stoch_oversold_cross = (self.stoch_k[-2] <= self.stoch_d[-2] and
                                    self.stoch_k[-1] > self.stoch_d[-1] and
                                    self.stoch_k[-1] < self.stoch_oversold_level and self.stoch_k[-2] < self.stoch_oversold_level)
            near_support = abs(self.data.Close[-1] - self.fib_support[-1]) / self.data.Close[-1] < self.prz_tolerance
            vol_confirm = self.data.Volume[-1] > self.vol_mult * self.avg_vol[-1]  # Stronger volume requirement
            rsi_confirm = self.rsi[-1] < self.rsi_oversold  # Complementary RSI oversold filter

            if vel_cross_up and stoch_oversold_cross and near_support and vol_confirm and rsi_confirm:
                sl = self.fib_support[-1] - 0.5 * self.atr[-1]
                stop_distance = self.data.Close[-1] - sl
                if stop_distance > 0:
                    size = risk_per_trade / stop_distance  # Fixed: Proper equity-based position sizing for 1% risk 🚀
                    size = min(size, (self.equity / self.data.Close[-1]) * 0.95)
                    tp = self.data.Close[-1] + 3 * stop_distance  # Improved to 1:3 RR for higher returns ✨
                    self.buy(size=size, sl=None, tp=None)
                    self.entry_price = self.data.Close[-1]
                    self.sl_price = sl
                    self.initial_risk = stop_distance
                    self.tp_price = tp
                    self.trail_stop = sl  # Initialize trail at SL
                    self.be_moved = False
                    print(f"🌙 Moon Dev Long Entry: Price={self.data.Close[-1]:.2f}, Size={size}, SL={sl:.2f}, TP={tp:.2f} ✨")

        # Enhanced Short Entry: Similar strict conditions + RSI + equity sizing
        if is_ranging and self.adx[-1] < self.adx_threshold:
            vel_cross_down = self.velocity[-2] > 0 and self.velocity[-1] < 0  # Strict cross to negative velocity
            stoch_overbought_cross = (self.stoch_k[-2] >= self.stoch_d[-2] and
                                      self.stoch_k[-1] < self.stoch_d[-1] and
                                      self.stoch_k[-1] > self.stoch_overbought_level and self.stoch_k[-2] > self.stoch_overbought_level)
            near_resistance = abs(self.data.Close[-1] - self.fib_resistance[-1]) / self.data.Close[-1] < self.prz_tolerance
            vol_confirm = self.data.Volume[-1] > self.vol_mult * self.avg_vol[-1]  # Stronger volume
            rsi_confirm = self.rsi[-1] > self.rsi_overbought  # RSI overbought filter

            if vel_cross_down and stoch_overbought_cross and near_resistance and vol_confirm and rsi_confirm:
                sl = self.fib_resistance[-1] + 0.5 * self.atr[-1]
                stop_distance = sl - self.data.Close[-1]
                if stop_distance > 0:
                    size = risk_per_trade / stop_distance  # Proper equity-based sizing
                    size = min(size, (self.equity / self.data.Close[-1]) * 0.95)
                    tp = self.data.Close[-1] - 3 * stop_distance  # 1:3 RR
                    self.sell(size=size, sl=None, tp=None)
                    self.entry_price = self.data.Close[-1]
                    self.sl_price = sl
                    self.initial_risk = stop_distance
                    self.tp_price = tp
                    self.trail_stop = sl  # Initialize trail at SL
                    self.be_moved = False
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