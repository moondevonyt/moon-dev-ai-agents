import pandas as pd
import numpy as np
import talib
from backtesting import Backtest, Strategy
import warnings
warnings.filterwarnings('ignore')

def kalman_velocity_position(close, q=0.05, r=1.0):  # Reduced q for smoother velocity estimation to reduce noise in signals 🌙
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

def fib_support(high, low, period=21):  # Shortened fib period to 21 (Fibonacci number) for more responsive levels on 15m timeframe ✨
    high_series = pd.Series(high)
    low_series = pd.Series(low)
    hh = high_series.rolling(period).max()
    ll = low_series.rolling(period).min()
    return (hh - 0.618 * (hh - ll)).values

def fib_resistance(high, low, period=21):  # Matching shortened period for consistency 🚀
    high_series = pd.Series(high)
    low_series = pd.Series(low)
    hh = high_series.rolling(period).max()
    ll = low_series.rolling(period).min()
    return (ll + 0.618 * (hh - ll)).values

class KalmanResonance(Strategy):
    kalman_q = 0.05  # Smoother Kalman for better velocity crosses without excessive noise 🌙
    kalman_r = 1.0
    stoch_k_period = 14
    stoch_d_period = 3
    stoch_slowd = 3
    atr_period = 20
    ema_period = 200
    fib_period = 21  # Optimized shorter period for faster adaptation to recent swings ✨
    prz_tolerance = 0.005  # Slightly loosened to 0.5% to capture more valid Fib proximity setups without overfiltering 🚀
    ranging_threshold = 0.08  # Loosened to 8% around EMA to allow more ranging market opportunities while still filtering strong trends 🌙
    max_bars_in_trade = 12  # Increased slightly from 10 to allow a bit more room for bounces in ranging conditions ✨
    trail_atr_mult = 1.8  # Tightened trailing to 1.8x ATR to lock in profits earlier while still letting winners run 🚀
    rr_ratio = 2.5  # Improved RR to 1:2.5 for higher reward potential on winning trades 🌙

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
        # Retained ADX for ranging confirmation (now stricter threshold in next()) 🌙
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        # Retained volume SMA for momentum confirmation ✨
        self.avg_vol = self.I(talib.SMA, self.data.Volume, timeperiod=20)
        # Added RSI for additional oversold/overbought confirmation to filter higher-quality entries 🚀
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14)
        self.trade_bars = 0
        self.entry_price = 0.0
        self.sl_price = 0.0
        self.tp_price = 0.0
        self.trail_stop = 0.0  # Initialized for trailing stop management
        self.stop_distance = 0.0  # Added to track stop distance for conditional trailing logic ✨
        print("🌙 Moon Dev KalmanResonance Initialized ✨")

    def next(self):
        if len(self.data) < max(self.ema_period, self.fib_period, 20, 14):
            return

        if np.isnan(self.velocity[-1]) or np.isnan(self.stoch_k[-1]) or np.isnan(self.adx[-1]) or np.isnan(self.rsi[-1]):
            return

        equity = self._broker._cash + self._broker._value  # Use internal equity for accurate risk calc (fixed potential issue) 🌙
        risk_per_trade = 0.01 * equity  # Retained 1% risk for solid management

        # Ranging check (now with loosened threshold for more trades)
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
            # Improved conditional trailing stop: Only activate after 1x RR profit to let trades breathe initially, then trail tighter 🌙
            if is_long:
                current_profit = self.data.Close[-1] - self.entry_price
                if current_profit > self.stop_distance:  # Start trailing only after breaking even + 1x risk
                    new_trail = self.data.Close[-1] - self.trail_atr_mult * self.atr[-1]
                    self.trail_stop = max(self.trail_stop, new_trail)
                else:
                    self.trail_stop = self.sl_price  # Hold at initial SL until profit threshold
                if self.data.Close[-1] <= self.trail_stop:
                    self.position.close()
                    print(f"🌙 Moon Dev Trailed Exit Long at {self.data.Close[-1]:.2f} (trail {self.trail_stop:.2f}) 🚀")
                    self.trail_stop = 0.0
                    return
            else:
                current_profit = self.entry_price - self.data.Close[-1]
                if current_profit > self.stop_distance:
                    new_trail = self.data.Close[-1] + self.trail_atr_mult * self.atr[-1]
                    self.trail_stop = min(self.trail_stop, new_trail)
                else:
                    self.trail_stop = self.sl_price
                if self.data.Close[-1] >= self.trail_stop:
                    self.position.close()
                    print(f"🌙 Moon Dev Trailed Exit Short at {self.data.Close[-1]:.2f} (trail {self.trail_stop:.2f}) 🚀")
                    self.trail_stop = 0.0
                    return
            # Time-based exit (adjusted slightly longer)
            if self.trade_bars > self.max_bars_in_trade:
                self.position.close()
                print(f"🌙 Moon Dev Time Exit after {self.trade_bars} bars 🌙")
                self.trail_stop = 0.0
                return
            return

        self.trade_bars = 0
        self.trail_stop = 0.0  # Reset on no position

        # Enhanced Long Entry: Added RSI <25, Stoch <15, candle close > open, volume >1.2x avg, stricter ADX<20, velocity magnitude filter
        if is_ranging and self.adx[-1] < 20:  # Stricter ADX for purer ranging to avoid weak trends ✨
            vel_cross_up = self.velocity[-2] < 0 and self.velocity[-1] > 0
            # Added velocity magnitude > 0.5x ATR to ensure meaningful momentum post-cross 🚀
            vel_momentum = abs(self.velocity[-1]) > 0.5 * self.atr[-1]
            stoch_oversold_cross = (self.stoch_k[-2] <= self.stoch_d[-2] and
                                    self.stoch_k[-1] > self.stoch_d[-1] and
                                    self.stoch_k[-1] < 15 and self.stoch_k[-2] < 15)  # Tightened to 15 for deeper oversold confirmation 🌙
            near_support = abs(self.data.Close[-1] - self.fib_support[-1]) / self.data.Close[-1] < self.prz_tolerance
            vol_confirm = self.data.Volume[-1] > 1.2 * self.avg_vol[-1]  # Stricter volume for stronger conviction ✨
            rsi_oversold = self.rsi[-1] < 25  # Added RSI filter for better oversold alignment 🚀
            bullish_candle = self.data.Close[-1] > self.data.Open[-1]  # Added candle direction for entry confirmation 🌙

            if (vel_cross_up and vel_momentum and stoch_oversold_cross and near_support and 
                vol_confirm and rsi_oversold and bullish_candle):
                sl = self.fib_support[-1] - 0.5 * self.atr[-1]
                stop_distance = self.data.Close[-1] - sl
                if stop_distance > 0:
                    stop_pct = stop_distance / self.data.Close[-1]
                    size = 0.01 / stop_pct
                    size = min(size, 0.95)
                    tp = self.data.Close[-1] + self.rr_ratio * stop_distance  # Updated to dynamic RR for higher targets ✨
                    self.buy(size=size, sl=sl, tp=None)
                    self.entry_price = self.data.Close[-1]
                    self.sl_price = sl
                    self.tp_price = tp
                    self.stop_distance = stop_distance  # Store for trailing logic 🚀
                    self.trail_stop = sl  # Initialize trail at SL
                    print(f"🌙 Moon Dev Long Entry: Price={self.data.Close[-1]:.2f}, Size={size}, SL={sl:.2f}, TP={tp:.2f} ✨")

        # Enhanced Short Entry: Symmetric improvements with RSI >75, Stoch >85, bearish candle, etc.
        if is_ranging and self.adx[-1] < 20:
            vel_cross_down = self.velocity[-2] > 0 and self.velocity[-1] < 0
            vel_momentum = abs(self.velocity[-1]) > 0.5 * self.atr[-1]
            stoch_overbought_cross = (self.stoch_k[-2] >= self.stoch_d[-2] and
                                      self.stoch_k[-1] < self.stoch_d[-1] and
                                      self.stoch_k[-1] > 85 and self.stoch_k[-2] > 85)  # Tightened to 85 for deeper overbought 🌙
            near_resistance = abs(self.data.Close[-1] - self.fib_resistance[-1]) / self.data.Close[-1] < self.prz_tolerance
            vol_confirm = self.data.Volume[-1] > 1.2 * self.avg_vol[-1]
            rsi_overbought = self.rsi[-1] > 75  # Added RSI filter for overbought alignment ✨
            bearish_candle = self.data.Close[-1] < self.data.Open[-1]  # Added candle direction confirmation 🚀

            if (vel_cross_down and vel_momentum and stoch_overbought_cross and near_resistance and 
                vol_confirm and rsi_overbought and bearish_candle):
                sl = self.fib_resistance[-1] + 0.5 * self.atr[-1]
                stop_distance = sl - self.data.Close[-1]
                if stop_distance > 0:
                    stop_pct = stop_distance / self.data.Close[-1]
                    size = 0.01 / stop_pct
                    size = min(size, 0.95)
                    tp = self.data.Close[-1] - self.rr_ratio * stop_distance  # Updated to dynamic RR ✨
                    self.sell(size=size, sl=sl, tp=None)
                    self.entry_price = self.data.Close[-1]
                    self.sl_price = sl
                    self.tp_price = tp
                    self.stop_distance = stop_distance  # Store for trailing logic 🚀
                    self.trail_stop = sl  # Initialize trail at SL
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