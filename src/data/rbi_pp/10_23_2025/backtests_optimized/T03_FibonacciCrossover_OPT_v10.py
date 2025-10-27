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
    adx_period = 14  # 🌙 Moon Dev: Retained ADX for trend strength filter to avoid choppy markets and improve entry quality
    adx_threshold = 22  # 🌙 Moon Dev: Lowered ADX threshold from 25 to 22 to capture more moderate trends, increasing trade frequency without excessive noise
    risk_per_trade = 0.008  # 🌙 Moon Dev: Increased risk per trade from 0.005 to 0.008 to amplify returns on winning trades while still managing drawdown
    rr_ratio = 3.5  # 🌙 Moon Dev: Adjusted RR ratio from 4 to 3.5 for a balance between ambitious targets and higher hit rate in volatile BTC 15m swings
    atr_multiplier_sl = 2.0  # 🌙 Moon Dev: Maintained SL multiplier at 2.0 for appropriate 15m volatility tolerance
    confluence_threshold = 0.007  # 🌙 Moon Dev: Loosened confluence threshold from 0.005 to 0.007 to allow slightly broader pullback entries near EMA21 (Fib level), boosting trade opportunities
    volume_multiplier = 1.5  # 🌙 Moon Dev: Reduced volume filter from 2.0x to 1.5x MA to include more high-conviction entries without overly restricting volume surges
    rsi_long_threshold = 52  # 🌙 Moon Dev: Loosened RSI long threshold from 55 to 52 for earlier bullish momentum capture
    rsi_short_threshold = 48  # 🌙 Moon Dev: Loosened RSI short threshold from 45 to 48 for earlier bearish momentum capture
    trail_trigger_rr = 2.0  # 🌙 Moon Dev: New: Trigger trailing stop after reaching 2R profit to lock in gains during extended trends
    trail_atr_multiplier = 1.5  # 🌙 Moon Dev: New: Trail SL at 1.5x ATR behind current price once triggered, improving profit retention in trending moves

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
        self.adx = self.I(talib.ADX, high, low, close, timeperiod=self.adx_period)  # 🌙 Moon Dev: Retained ADX to filter for trending regimes only

        print("🌙 Moon Dev: Initialized Enhanced FibonacciCrossover Strategy with Loosened Filters, Adjusted Risk, and Trailing Stops for Higher Returns ✨")

    def next(self):
        current_close = self.data.Close[-1]
        current_high = self.data.High[-1]
        current_low = self.data.Low[-1]
        current_volume = self.data.Volume[-1]
        current_rsi = self.rsi[-1]
        current_atr = self.atr[-1]
        current_ema21 = self.ema21[-1]
        current_adx = self.adx[-1]  # 🌙 Moon Dev: Retrieve current ADX for trend strength check

        # Manual SL/TP management with trailing stop integration (checked at end of bar, close at close price - approximation)
        if self.position:
            if not hasattr(self, 'sl') or not hasattr(self, 'tp') or not hasattr(self, 'entry_price') or not hasattr(self, 'risk_distance'):
                # Safety check if attributes missing
                self.position.close()
                return

            # 🌙 Moon Dev: New Trailing Stop Logic - Update SL dynamically after trail trigger
            if self.position.is_long:
                profit_rr = (current_close - self.entry_price) / self.risk_distance
                if profit_rr >= self.trail_trigger_rr:
                    trail_sl = current_close - (self.trail_atr_multiplier * current_atr)
                    self.sl = max(self.sl, trail_sl)
                    print(f"🌙 Moon Dev: LONG Trailing SL Updated to {self.sl:.2f} (Profit RR: {profit_rr:.2f}, ATR: {current_atr:.2f}) 🔒 Locking Profits")

                if current_low <= self.sl:
                    self.position.close()
                    print(f"🌙 Moon Dev: LONG hit SL {self.sl} (low: {current_low}), closing at {current_close} 💥")
                    if hasattr(self, 'sl'): del self.sl
                    if hasattr(self, 'tp'): del self.tp
                    if hasattr(self, 'entry_price'): del self.entry_price
                    if hasattr(self, 'risk_distance'): del self.risk_distance
                    return
                elif current_high >= self.tp:
                    self.position.close()
                    print(f"🌙 Moon Dev: LONG hit TP {self.tp} (high: {current_high}), closing at {current_close} 🎯")
                    if hasattr(self, 'sl'): del self.sl
                    if hasattr(self, 'tp'): del self.tp
                    if hasattr(self, 'entry_price'): del self.entry_price
                    if hasattr(self, 'risk_distance'): del self.risk_distance
                    return

            elif self.position.is_short:
                profit_rr = (self.entry_price - current_close) / self.risk_distance
                if profit_rr >= self.trail_trigger_rr:
                    trail_sl = current_close + (self.trail_atr_multiplier * current_atr)
                    self.sl = min(self.sl, trail_sl)
                    print(f"🌙 Moon Dev: SHORT Trailing SL Updated to {self.sl:.2f} (Profit RR: {profit_rr:.2f}, ATR: {current_atr:.2f}) 🔒 Locking Profits")

                if current_high >= self.sl:
                    self.position.close()
                    print(f"🌙 Moon Dev: SHORT hit SL {self.sl} (high: {current_high}), closing at {current_close} 💥")
                    if hasattr(self, 'sl'): del self.sl
                    if hasattr(self, 'tp'): del self.tp
                    if hasattr(self, 'entry_price'): del self.entry_price
                    if hasattr(self, 'risk_distance'): del self.risk_distance
                    return
                elif current_low <= self.tp:
                    self.position.close()
                    print(f"🌙 Moon Dev: SHORT hit TP {self.tp} (low: {current_low}), closing at {current_close} 🎯")
                    if hasattr(self, 'sl'): del self.sl
                    if hasattr(self, 'tp'): del self.tp
                    if hasattr(self, 'entry_price'): del self.entry_price
                    if hasattr(self, 'risk_distance'): del self.risk_distance
                    return

        # Approximate harmonic confluence in next (using latest) - loosened for more opportunities
        harmonic_long = abs(current_close - current_ema21) / current_ema21 < self.confluence_threshold
        harmonic_short = abs(current_close - current_ema21) / current_ema21 < self.confluence_threshold

        # Early exit on opposite crossover
        if self.position.is_long:
            if self.ema5[-2] > self.ema13[-2] and self.ema5[-1] < self.ema13[-1]:
                self.position.close()
                print(f"🌙 Moon Dev: Closed Long on Bearish Crossover at {self.data.index[-1]} 📉")
                if hasattr(self, 'sl'): del self.sl
                if hasattr(self, 'tp'): del self.tp
                if hasattr(self, 'entry_price'): del self.entry_price
                if hasattr(self, 'risk_distance'): del self.risk_distance
                return

        if self.position.is_short:
            if self.ema5[-2] < self.ema13[-2] and self.ema5[-1] > self.ema13[-1]:
                self.position.close()
                print(f"🌙 Moon Dev: Closed Short on Bullish Crossover at {self.data.index[-1]} 📈")
                if hasattr(self, 'sl'): del self.sl
                if hasattr(self, 'tp'): del self.tp
                if hasattr(self, 'entry_price'): del self.entry_price
                if hasattr(self, 'risk_distance'): del self.risk_distance
                return

        # Long Entry - Enhanced with loosened ADX (22), RSI (>52), volume (1.5x), confluence (0.007), and retained trend filters
        if (not self.position and
            self.ema5[-2] < self.ema13[-2] and self.ema5[-1] > self.ema13[-1] and
            self.ema21[-1] > self.ema55[-1] and
            self.ema13[-1] > self.ema21[-1] and
            self.ema55[-1] > self.sma200[-1] and  # 🌙 Moon Dev: Retained EMA55 > SMA200 filter to confirm long-term uptrend alignment, reducing counter-trend trades
            current_rsi > self.rsi_long_threshold and  # 🌙 Moon Dev: Loosened RSI to >52 for more bullish setups
            current_close > self.sma200[-1] and
            current_volume > self.volume_multiplier * self.volume_ma[-1] and  # 🌙 Moon Dev: Loosened volume filter to 1.5x MA for increased entry frequency with solid participation
            current_adx > self.adx_threshold and  # 🌙 Moon Dev: Loosened ADX to 22 to include more trending conditions
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
            self.entry_price = current_close
            self.risk_distance = sl_distance
            print(f"🌙 Moon Dev: LONG Entry at {current_close} | SL: {sl_price} | TP: {tp_price} | Size: {position_size} | ADX: {current_adx:.2f} | RSI: {current_rsi:.2f} 🚀 Optimized Entry with Trailing Potential Confirmed ✨")

        # Short Entry - Enhanced with loosened ADX (22), RSI (<48), volume (1.5x), confluence (0.007), and retained trend filters
        elif (not self.position and
              self.ema5[-2] > self.ema13[-2] and self.ema5[-1] < self.ema13[-1] and
              self.ema21[-1] < self.ema55[-1] and
              self.ema13[-1] < self.ema21[-1] and
              self.ema55[-1] < self.sma200[-1] and  # 🌙 Moon Dev: Retained EMA55 < SMA200 filter to confirm long-term downtrend alignment, reducing counter-trend trades
              current_rsi < self.rsi_short_threshold and  # 🌙 Moon Dev: Loosened RSI to <48 for more bearish setups
              current_close < self.sma200[-1] and
              current_volume > self.volume_multiplier * self.volume_ma[-1] and  # 🌙 Moon Dev: Loosened volume filter to 1.5x MA for increased entry frequency with solid participation
              current_adx > self.adx_threshold and  # 🌙 Moon Dev: Loosened ADX to 22 to include more trending conditions
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
            self.entry_price = current_close
            self.risk_distance = sl_distance
            print(f"🌙 Moon Dev: SHORT Entry at {current_close} | SL: {sl_price} | TP: {tp_price} | Size: {position_size} | ADX: {current_adx:.2f} | RSI: {current_rsi:.2f} 📉 Optimized Entry with Trailing Potential Confirmed ✨")

# Run backtest
bt = Backtest(data, FibonacciCrossover, cash=1_000_000, commission=0.002, exclusive_orders=True)
stats = bt.run()
print(stats)