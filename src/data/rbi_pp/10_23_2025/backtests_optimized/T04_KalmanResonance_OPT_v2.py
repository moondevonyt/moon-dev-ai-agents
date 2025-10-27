import pandas as pd
import numpy as np
import talib
from backtesting import Backtest, Strategy
import warnings
warnings.filterwarnings('ignore')

def kalman_velocity_position(close, q=0.05, r=0.5):
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

def fib_support(high, low, period=20):
    high_series = pd.Series(high)
    low_series = pd.Series(low)
    hh = high_series.rolling(period).max()
    ll = low_series.rolling(period).min()
    return (hh - 0.618 * (hh - ll)).values

def fib_resistance(high, low, period=20):
    high_series = pd.Series(high)
    low_series = pd.Series(low)
    hh = high_series.rolling(period).max()
    ll = low_series.rolling(period).min()
    return (ll + 0.618 * (hh - ll)).values

class KalmanResonance(Strategy):
    kalman_q = 0.05
    kalman_r = 0.5
    stoch_k_period = 14
    stoch_d_period = 3
    stoch_slowd = 3
    atr_period = 20
    ema_period = 200
    fib_period = 20
    rsi_period = 14
    prz_tolerance = 0.002  # Tightened to 0.2% for better precision on fib levels 🌙
    ranging_threshold = 0.05  # Tightened to 5% around EMA to focus on true ranging conditions ✨
    max_bars_in_trade = 10  # Reduced time in trade to exit faster and reduce exposure 🚀
    trail_atr_mult = 1.5  # Increased trailing multiplier for more breathing room in winners

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
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=self.rsi_period)  # Added RSI for oversold/overbought confirmation 🌙
        self.vol_sma = self.I(talib.SMA, self.data.Volume, timeperiod=20)  # Added volume SMA for confirmation filter ✨
        self.trade_bars = 0
        self.entry_price = 0.0
        self.sl_price = 0.0
        self.tp_price = 0.0
        print("🌙 Moon Dev KalmanResonance Initialized ✨")

    def next(self):
        if len(self.data) < self.ema_period + self.fib_period:
            return

        if np.isnan(self.velocity[-1]) or np.isnan(self.stoch_k[-1]):
            return

        # Added volatility filter to avoid low-vol choppy conditions (ATR < 0.2% of price) 🚀
        if self.atr[-1] < 0.002 * self.data.Close[-1]:
            return

        equity = self.equity
        risk_per_trade = 0.02 * equity  # Increased risk per trade to 2% to amplify returns while sizing dynamically 🌙

        # Ranging check
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
            # Trail exit using Kalman filtered price
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

        # Long Entry - Tightened: only velocity zero-cross up (removed loose decel), stoch <20, added RSI<35 & volume > SMA
        if is_ranging:
            vel_cross_up = self.velocity[-2] < 0 and self.velocity[-1] >= 0
            stoch_oversold_cross = (self.stoch_k[-2] <= self.stoch_d[-2] and
                                    self.stoch_k[-1] > self.stoch_d[-1] and
                                    self.stoch_k[-1] < 20)  # Tightened to <20 for stronger oversold ✨
            near_support = abs(self.data.Close[-1] - self.fib_support[-1]) / self.data.Close[-1] < self.prz_tolerance
            rsi_oversold = self.rsi[-1] < 35  # Added RSI filter for better oversold confirmation 🌙
            vol_confirm = self.data.Volume[-1] > 1.1 * self.vol_sma[-1]  # Added volume surge filter to avoid weak signals 🚀

            if vel_cross_up and stoch_oversold_cross and near_support and rsi_oversold and vol_confirm:
                sl = self.fib_support[-1] - 0.5 * self.atr[-1]
                stop_distance = self.data.Close[-1] - sl
                if stop_distance > 0:
                    stop_pct = stop_distance / self.data.Close[-1]
                    size = risk_per_trade / (equity * stop_pct)  # Corrected sizing formula for 2% risk
                    size = min(size, 0.8)  # Capped at 80% for risk management
                    tp = self.data.Close[-1] + 3 * stop_distance  # Improved to 1:3 RR for higher reward potential ✨
                    self.buy(size=size, sl=sl, tp=None)
                    self.entry_price = self.data.Close[-1]
                    self.sl_price = sl
                    self.tp_price = tp
                    print(f"🌙 Moon Dev Long Entry: Price={self.data.Close[-1]:.2f}, Size={size}, SL={sl:.2f}, TP={tp:.2f} ✨")

        # Short Entry - Symmetric tightening: only velocity zero-cross down (removed loose accel), stoch >80, added RSI>65 & volume
        if is_ranging:
            vel_cross_down = self.velocity[-2] > 0 and self.velocity[-1] <= 0
            stoch_overbought_cross = (self.stoch_k[-2] >= self.stoch_d[-2] and
                                      self.stoch_k[-1] < self.stoch_d[-1] and
                                      self.stoch_k[-1] > 80)  # Tightened to >80 for stronger overbought 🚀
            near_resistance = abs(self.data.Close[-1] - self.fib_resistance[-1]) / self.data.Close[-1] < self.prz_tolerance
            rsi_overbought = self.rsi[-1] > 65  # Added RSI filter for better overbought confirmation 🌙
            vol_confirm = self.data.Volume[-1] > 1.1 * self.vol_sma[-1]  # Added volume surge filter

            if vel_cross_down and stoch_overbought_cross and near_resistance and rsi_overbought and vol_confirm:
                sl = self.fib_resistance[-1] + 0.5 * self.atr[-1]
                stop_distance = sl - self.data.Close[-1]
                if stop_distance > 0:
                    stop_pct = stop_distance / self.data.Close[-1]
                    size = risk_per_trade / (equity * stop_pct)  # Corrected sizing formula for 2% risk
                    size = min(size, 0.8)  # Capped at 80% for risk management
                    tp = self.data.Close[-1] - 3 * stop_distance  # Improved to 1:3 RR for higher reward potential ✨
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