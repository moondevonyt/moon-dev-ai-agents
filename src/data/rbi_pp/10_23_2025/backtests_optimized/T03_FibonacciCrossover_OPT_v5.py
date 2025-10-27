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
    sma200_period = 200
    volume_ma_period = 20
    adx_period = 14  # 🌙 Moon Dev: Added ADX for trend strength filter to avoid choppy markets and improve entry quality
    adx_threshold = 25  # 🌙 Moon Dev: ADX > 25 confirms sufficient trend strength for entries
    risk_per_trade = 0.005  # 🌙 Moon Dev: Kept risk per trade at 0.005 for balanced risk management
    rr_ratio = 4  # 🌙 Moon Dev: Increased RR ratio from 3 to 4 to capture higher rewards in trending BTC moves
    atr_multiplier_sl = 2.0  # 🌙 Moon Dev: Maintained SL multiplier at 2.0 for 15m volatility tolerance
    confluence_threshold = 0.005  # 🌙 Moon Dev: Tightened confluence threshold from 0.01 to 0.005 for more precise pullback entries near EMA21 (Fib level)

    def init(self):
        close = self.data.Close
        high = self.data.High
        low = self.data.Low
        volume = self.data.Volume

        self.ema5 = self.I(talib.EMA, close, timeperiod=self.ema5_period)
        self.ema13 = self.I(talib.EMA, close, timeperiod=self.ema13_period)
        self.ema21 = self.I(talib.EMA, close, timeperiod=self.ema21_period)
        self.ema55 = self.I(talib.EMA, close, timeperiod=self.ema55_period)
        self.sma200 = self.I(talib.SMA, close, timeperiod=self.sma200_period)
        self.rsi = self.I(talib.RSI, close, timeperiod=self.rsi_period)
        self.atr = self.I(talib.ATR, high, low, close, timeperiod=self.atr_period)
        self.volume_ma = self.I(talib.SMA, volume, timeperiod=self.volume_ma_period)
        self.adx = self.I(talib.ADX, high, low, close, timeperiod=self.adx_period)  # 🌙 Moon Dev: Initialized ADX to filter for trending regimes only

        print("🌙 Moon Dev: Initialized Optimized FibonacciCrossover Strategy with ADX Trend Filter ✨")

    def next(self):
        current_close = self.data.Close[-1]
        current_high = self.data.High[-1]
        current_low = self.data.Low[-1]
        current_volume = self.data.Volume[-1]
        current_rsi = self.rsi[-1]
        current_atr = self.atr[-1]
        current_ema21 = self.ema21[-1]
        current_adx = self.adx[-1]  # 🌙 Moon Dev: Retrieve current ADX for trend strength check

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

        # Approximate harmonic confluence in next (using latest) - tightened for precision
        harmonic_long = abs(current_close - current_ema21) / current_ema21 < self.confluence_threshold
        harmonic_short = abs(current_close - current_ema21) / current_ema21 < self.confluence_threshold

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

        # Long Entry - Enhanced with ADX >25, tighter RSI (>55), EMA55 > SMA200 for long-term uptrend, and volume >2x MA
        if (not self.position and
            self.ema5[-2] < self.ema13[-2] and self.ema5[-1] > self.ema13[-1] and
            self.ema21[-1] > self.ema55[-1] and
            self.ema13[-1] > self.ema21[-1] and
            self.ema55[-1] > self.sma200[-1] and  # 🌙 Moon Dev: Added EMA55 > SMA200 filter to confirm long-term uptrend alignment, reducing counter-trend trades
            current_rsi > 55 and  # 🌙 Moon Dev: Tightened RSI from >50 to >55 for stronger bullish momentum confirmation
            current_close > self.sma200[-1] and
            current_volume > 2.0 * self.volume_ma[-1] and  # 🌙 Moon Dev: Increased volume filter from 1.5x to 2x MA for higher conviction entries with strong participation
            current_adx > self.adx_threshold and  # 🌙 Moon Dev: Added ADX filter to ensure trending market, avoiding ranging/choppy conditions
            harmonic_long):
            
            if np.isnan(current_atr) or current_atr <= 0:
                print("🌙 Moon Dev: Skipping LONG due to invalid ATR")
                return
            
            sl_distance = current_atr * self.atr_multiplier_sl
            risk_amount = self.equity * self.risk_per_trade
            position_size = risk_amount / sl_distance
            position_size = int(round(position_size))
            
            if position_size <= 0:
                print("🌙 Moon Dev: Skipping LONG due to zero size")
                return
            
            sl_price = current_close - sl_distance
            tp_distance = sl_distance * self.rr_ratio
            tp_price = current_close + tp_distance
            
            if sl_price >= current_close or tp_price <= current_close:
                print(f"🌙 Moon Dev: Skipping LONG due to invalid levels - SL:{sl_price} Entry:{current_close} TP:{tp_price}")
                return
            
            max_size = int(self.equity / current_close)
            position_size = min(position_size, max_size)
            
            if position_size <= 0:
                return
            
            self.buy(size=position_size)
            self.sl = sl_price
            self.tp = tp_price
            print(f"🌙 Moon Dev: LONG Entry at {current_close} | SL: {sl_price} | TP: {tp_price} | Size: {position_size} | ADX: {current_adx:.2f} 🚀 Enhanced Trend-Filtered Entry Confirmed ✨")

        # Short Entry - Enhanced with ADX >25, tighter RSI (<45), EMA55 < SMA200 for long-term downtrend, and volume >2x MA
        elif (not self.position and
              self.ema5[-2] > self.ema13[-2] and self.ema5[-1] < self.ema13[-1] and
              self.ema21[-1] < self.ema55[-1] and
              self.ema13[-1] < self.ema21[-1] and
              self.ema55[-1] < self.sma200[-1] and  # 🌙 Moon Dev: Added EMA55 < SMA200 filter to confirm long-term downtrend alignment, reducing counter-trend trades
              current_rsi < 45 and  # 🌙 Moon Dev: Tightened RSI from <50 to <45 for stronger bearish momentum confirmation
              current_close < self.sma200[-1] and
              current_volume > 2.0 * self.volume_ma[-1] and  # 🌙 Moon Dev: Increased volume filter from 1.5x to 2x MA for higher conviction entries with strong participation
              current_adx > self.adx_threshold and  # 🌙 Moon Dev: Added ADX filter to ensure trending market, avoiding ranging/choppy conditions
              harmonic_short):
            
            if np.isnan(current_atr) or current_atr <= 0:
                print("🌙 Moon Dev: Skipping SHORT due to invalid ATR")
                return
            
            sl_distance = current_atr * self.atr_multiplier_sl
            risk_amount = self.equity * self.risk_per_trade
            position_size = risk_amount / sl_distance
            position_size = int(round(position_size))
            
            if position_size <= 0:
                print("🌙 Moon Dev: Skipping SHORT due to zero size")
                return
            
            sl_price = current_close + sl_distance
            tp_distance = sl_distance * self.rr_ratio
            tp_price = current_close - tp_distance
            
            if sl_price <= current_close or tp_price >= current_close:
                print(f"🌙 Moon Dev: Skipping SHORT due to invalid levels - SL:{sl_price} Entry:{current_close} TP:{tp_price}")
                return
            
            max_size = int(self.equity / current_close)
            position_size = min(position_size, max_size)
            
            if position_size <= 0:
                return
            
            self.sell(size=position_size)
            self.sl = sl_price
            self.tp = tp_price
            print(f"🌙 Moon Dev: SHORT Entry at {current_close} | SL: {sl_price} | TP: {tp_price} | Size: {position_size} | ADX: {current_adx:.2f} 📉 Enhanced Trend-Filtered Entry Confirmed ✨")

# Run backtest
bt = Backtest(data, FibonacciCrossover, cash=1_000_000, commission=0.002, exclusive_orders=True)
stats = bt.run()
print(stats)