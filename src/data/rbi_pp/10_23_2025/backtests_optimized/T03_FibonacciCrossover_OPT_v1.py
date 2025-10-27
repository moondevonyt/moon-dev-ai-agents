from backtesting import Backtest, Strategy
import talib
import pandas as pd
import numpy as np

# Load and prepare data
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
data = data.drop(columns=['datetime'], errors='ignore')

class FibonacciCrossover(Strategy):
    ema5_period = 5
    ema13_period = 13
    ema21_period = 21
    ema55_period = 55
    rsi_period = 14
    atr_period = 14
    ema200_period = 200  # 🌙 Moon Dev: Changed from SMA to EMA for smoother long-term trend detection
    volume_ma_period = 20
    risk_per_trade = 0.005  # 🌙 Moon Dev: Reduced from 0.01 to 0.005 for tighter risk control and better capital preservation
    rr_ratio = 3  # 🌙 Moon Dev: Increased from 2 to 3 for higher reward potential on winning trades
    atr_multiplier_sl = 2.0  # 🌙 Moon Dev: Increased from 1.5 to 2.0 for wider stops to reduce whipsaws in volatile crypto
    confluence_threshold = 0.002  # 🌙 Moon Dev: Tightened from 0.005 to 0.002 for stricter harmonic approximation near EMA21
    adx_period = 14  # 🌙 Moon Dev: New parameter for ADX to filter for trending markets
    adx_threshold = 25  # 🌙 Moon Dev: ADX > 25 to ensure sufficient trend strength, avoiding choppy conditions
    volume_multiplier = 1.5  # 🌙 Moon Dev: New multiplier to require stronger volume confirmation (>1.5x MA)

    def init(self):
        close = self.data.Close
        high = self.data.High
        low = self.data.Low
        volume = self.data.Volume

        self.ema5 = self.I(talib.EMA, close, timeperiod=self.ema5_period)
        self.ema13 = self.I(talib.EMA, close, timeperiod=self.ema13_period)
        self.ema21 = self.I(talib.EMA, close, timeperiod=self.ema21_period)
        self.ema55 = self.I(talib.EMA, close, timeperiod=self.ema55_period)
        self.ema200 = self.I(talib.EMA, close, timeperiod=self.ema200_period)  # 🌙 Moon Dev: Switched to EMA200 for better responsiveness in trends
        self.rsi = self.I(talib.RSI, close, timeperiod=self.rsi_period)
        self.atr = self.I(talib.ATR, high, low, close, timeperiod=self.atr_period)
        self.volume_ma = self.I(talib.SMA, volume, timeperiod=self.volume_ma_period)
        self.adx = self.I(talib.ADX, high, low, close, timeperiod=self.adx_period)  # 🌙 Moon Dev: Added ADX for trend strength filter

        print("🌙 Moon Dev: Initialized FibonacciCrossover Strategy ✨")

    def next(self):
        current_close = self.data.Close[-1]
        current_high = self.data.High[-1]
        current_low = self.data.Low[-1]
        current_volume = self.data.Volume[-1]
        current_rsi = self.rsi[-1]
        current_atr = self.atr[-1]
        current_ema21 = self.ema21[-1]
        current_adx = self.adx[-1]  # 🌙 Moon Dev: Access current ADX value

        # Manual SL/TP management (checked at end of bar, close at close price - approximation)
        if self.position:
            if hasattr(self, 'sl') and hasattr(self, 'tp'):
                if self.position.is_long:
                    if current_low <= self.sl:
                        self.position.close()
                        print(f"🌙 Moon Dev: LONG hit SL {self.sl} (low: {current_low}), closing at {current_close} 💥")
                        if hasattr(self, 'sl'): del self.sl
                        if hasattr(self, 'tp'): del self.tp
                        return
                    elif current_high >= self.tp:
                        self.position.close()
                        print(f"🌙 Moon Dev: LONG hit TP {self.tp} (high: {current_high}), closing at {current_close} 🎯")
                        if hasattr(self, 'sl'): del self.sl
                        if hasattr(self, 'tp'): del self.tp
                        return
                elif self.position.is_short:
                    if current_high >= self.sl:
                        self.position.close()
                        print(f"🌙 Moon Dev: SHORT hit SL {self.sl} (high: {current_high}), closing at {current_close} 💥")
                        if hasattr(self, 'sl'): del self.sl
                        if hasattr(self, 'tp'): del self.tp
                        return
                    elif current_low <= self.tp:
                        self.position.close()
                        print(f"🌙 Moon Dev: SHORT hit TP {self.tp} (low: {current_low}), closing at {current_close} 🎯")
                        if hasattr(self, 'sl'): del self.sl
                        if hasattr(self, 'tp'): del self.tp
                        return

        # Approximate harmonic confluence in next (using latest) - tightened and made directional
        harmonic_long = current_close > current_ema21 * (1 - self.confluence_threshold)  # 🌙 Moon Dev: Directional for long: close not too far below EMA21 (pullback)
        harmonic_short = current_close < current_ema21 * (1 + self.confluence_threshold)  # 🌙 Moon Dev: Directional for short: close not too far above EMA21 (pullback)

        # Early exit on opposite crossover
        if self.position.is_long:
            if self.ema5[-2] > self.ema13[-2] and self.ema5[-1] < self.ema13[-1]:
                self.position.close()
                print(f"🌙 Moon Dev: Closed Long on Bearish Crossover at {self.data.index[-1]} 📉")
                return

        if self.position.is_short:
            if self.ema5[-2] < self.ema13[-2] and self.ema5[-1] > self.ema13[-1]:
                self.position.close()
                print(f"🌙 Moon Dev: Closed Short on Bullish Crossover at {self.data.index[-1]} 📈")
                return

        # Long Entry - added ADX filter, tightened RSI to >50, volume *1.5, EMA200
        if (not self.position and
            self.ema5[-2] < self.ema13[-2] and self.ema5[-1] > self.ema13[-1] and
            self.ema21[-1] > self.ema55[-1] and
            current_rsi > 50 and  # 🌙 Moon Dev: Tightened from >40 to >50 for stronger bullish momentum
            current_close > self.ema200[-1] and  # 🌙 Moon Dev: Using EMA200 instead of SMA200
            current_volume > self.volume_ma[-1] * self.volume_multiplier and  # 🌙 Moon Dev: Stronger volume requirement
            harmonic_long and
            current_adx > self.adx_threshold):  # 🌙 Moon Dev: ADX filter for trending market
            
            if np.isnan(current_atr) or current_atr <= 0:
                print("🌙 Moon Dev: Skipping LONG due to invalid ATR")
                return
            
            sl_distance = current_atr * self.atr_multiplier_sl
            risk_amount = self.equity * self.risk_per_trade
            position_size = risk_amount / sl_distance  # 🌙 Moon Dev: Changed to float for fractional BTC sizing (more precise)
            
            if position_size <= 0:
                print("🌙 Moon Dev: Skipping LONG due to zero size")
                return
            
            sl_price = current_close - sl_distance
            tp_distance = sl_distance * self.rr_ratio
            tp_price = current_close + tp_distance
            
            if sl_price >= current_close or tp_price <= current_close:
                print(f"🌙 Moon Dev: Skipping LONG due to invalid levels - SL:{sl_price} Entry:{current_close} TP:{tp_price}")
                return
            
            max_size = self.equity / current_close
            position_size = min(position_size, max_size)
            
            if position_size <= 0:
                return
            
            self.buy(size=position_size)
            self.sl = sl_price
            self.tp = tp_price
            print(f"🌙 Moon Dev: LONG Entry at {current_close} | SL: {sl_price} | TP: {tp_price} | Size: {position_size} 🚀 Harmonic Confluence Confirmed ✨")

        # Short Entry - added ADX filter, tightened RSI to <50, volume *1.5, EMA200
        elif (not self.position and
              self.ema5[-2] > self.ema13[-2] and self.ema5[-1] < self.ema13[-1] and
              self.ema21[-1] < self.ema55[-1] and
              current_rsi < 50 and  # 🌙 Moon Dev: Tightened from <60 to <50 for stronger bearish momentum
              current_close < self.ema200[-1] and  # 🌙 Moon Dev: Using EMA200 instead of SMA200
              current_volume > self.volume_ma[-1] * self.volume_multiplier and  # 🌙 Moon Dev: Stronger volume requirement
              harmonic_short and
              current_adx > self.adx_threshold):  # 🌙 Moon Dev: ADX filter for trending market
            
            if np.isnan(current_atr) or current_atr <= 0:
                print("🌙 Moon Dev: Skipping SHORT due to invalid ATR")
                return
            
            sl_distance = current_atr * self.atr_multiplier_sl
            risk_amount = self.equity * self.risk_per_trade
            position_size = risk_amount / sl_distance  # 🌙 Moon Dev: Changed to float for fractional BTC sizing (more precise)
            
            if position_size <= 0:
                print("🌙 Moon Dev: Skipping SHORT due to zero size")
                return
            
            sl_price = current_close + sl_distance
            tp_distance = sl_distance * self.rr_ratio
            tp_price = current_close - tp_distance
            
            if sl_price <= current_close or tp_price >= current_close:
                print(f"🌙 Moon Dev: Skipping SHORT due to invalid levels - SL:{sl_price} Entry:{current_close} TP:{tp_price}")
                return
            
            max_size = self.equity / current_close
            position_size = min(position_size, max_size)
            
            if position_size <= 0:
                return
            
            self.sell(size=position_size)
            self.sl = sl_price
            self.tp = tp_price
            print(f"🌙 Moon Dev: SHORT Entry at {current_close} | SL: {sl_price} | TP: {tp_price} | Size: {position_size} 📉 Harmonic Confluence Confirmed ✨")

# Run backtest
bt = Backtest(data, FibonacciCrossover, cash=1_000_000, commission=0.002, exclusive_orders=True)
stats = bt.run()
print(stats)