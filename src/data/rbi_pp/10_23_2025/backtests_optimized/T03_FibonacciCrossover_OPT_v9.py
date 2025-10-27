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
    adx_period = 14  # 🌙 Moon Dev: ADX for trend strength filter to avoid choppy markets
    adx_threshold = 25  # 🌙 Moon Dev: Kept ADX >25 for strong trends, but added rising ADX filter below for better entry timing
    risk_per_trade = 0.01  # 🌙 Moon Dev: Increased from 0.005 to 0.01 (1%) to scale up position sizes and potential returns while monitoring drawdown
    rr_ratio = 5  # 🌙 Moon Dev: Increased from 4 to 5 for larger reward capture in BTC trends
    atr_multiplier_sl = 1.5  # 🌙 Moon Dev: Tightened from 2.0 to 1.5 ATR for closer stops, allowing larger positions for the same risk % and better risk-reward
    confluence_threshold = 0.01  # 🌙 Moon Dev: Loosened from 0.005 to 0.01 for more pullback entries near EMA21 without sacrificing quality
    volume_multiplier = 1.5  # 🌙 Moon Dev: Reduced from 2.0 to 1.5x volume MA to allow more high-conviction entries in varying volume regimes
    trail_profit_threshold_rr = 2  # 🌙 Moon Dev: Start trailing after 2R profit to lock in gains
    trail_offset_atr = 1.5  # 🌙 Moon Dev: Trail by 1.5 ATR behind current close for dynamic stop adjustment in trends

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
        self.adx = self.I(talib.ADX, high, low, close, timeperiod=self.adx_period)  # 🌙 Moon Dev: Initialized ADX

        print("🌙 Moon Dev: Initialized Enhanced FibonacciCrossover with Trailing Stops, Looser Filters & Rising ADX for 50% Target 🚀")

    def next(self):
        current_close = self.data.Close[-1]
        current_high = self.data.High[-1]
        current_low = self.data.Low[-1]
        current_volume = self.data.Volume[-1]
        current_rsi = self.rsi[-1]
        current_atr = self.atr[-1]
        current_ema21 = self.ema21[-1]
        current_adx = self.adx[-1]

        # 🌙 Moon Dev: Manual SL/TP and Trailing management (updated dynamically)
        if self.position:
            # Update trailing stop if in profit threshold
            if self.position.is_long and hasattr(self, 'entry_price') and hasattr(self, 'sl_distance'):
                profit_threshold = self.entry_price + (self.sl_distance * self.trail_profit_threshold_rr)
                if current_close > profit_threshold:
                    if not np.isnan(current_atr) and current_atr > 0:
                        trail_offset = self.trail_offset_atr * current_atr
                        new_sl = current_close - trail_offset
                        if new_sl > self.sl:
                            old_sl = self.sl
                            self.sl = new_sl
                            print(f"🌙 Moon Dev: LONG Trailing SL updated from {old_sl:.2f} to {self.sl:.2f} (Close: {current_close:.2f}) 🔄")
            elif self.position.is_short and hasattr(self, 'entry_price') and hasattr(self, 'sl_distance'):
                profit_threshold = self.entry_price - (self.sl_distance * self.trail_profit_threshold_rr)
                if current_close < profit_threshold:
                    if not np.isnan(current_atr) and current_atr > 0:
                        trail_offset = self.trail_offset_atr * current_atr
                        new_sl = current_close + trail_offset
                        if new_sl < self.sl:
                            old_sl = self.sl
                            self.sl = new_sl
                            print(f"🌙 Moon Dev: SHORT Trailing SL updated from {old_sl:.2f} to {self.sl:.2f} (Close: {current_close:.2f}) 🔄")

            # Check SL/TP after potential trailing update
            if hasattr(self, 'sl') and hasattr(self, 'tp'):
                if self.position.is_long:
                    if current_low <= self.sl:
                        self.position.close()
                        print(f"🌙 Moon Dev: LONG hit SL {self.sl} (low: {current_low}), closing at {current_close} 💥")
                        if hasattr(self, 'sl'): del self.sl
                        if hasattr(self, 'tp'): del self.tp
                        if hasattr(self, 'entry_price'): del self.entry_price
                        if hasattr(self, 'sl_distance'): del self.sl_distance
                        return
                    elif current_high >= self.tp:
                        self.position.close()
                        print(f"🌙 Moon Dev: LONG hit TP {self.tp} (high: {current_high}), closing at {current_close} 🎯")
                        if hasattr(self, 'sl'): del self.sl
                        if hasattr(self, 'tp'): del self.tp
                        if hasattr(self, 'entry_price'): del self.entry_price
                        if hasattr(self, 'sl_distance'): del self.sl_distance
                        return
                elif self.position.is_short:
                    if current_high >= self.sl:
                        self.position.close()
                        print(f"🌙 Moon Dev: SHORT hit SL {self.sl} (high: {current_high}), closing at {current_close} 💥")
                        if hasattr(self, 'sl'): del self.sl
                        if hasattr(self, 'tp'): del self.tp
                        if hasattr(self, 'entry_price'): del self.entry_price
                        if hasattr(self, 'sl_distance'): del self.sl_distance
                        return
                    elif current_low <= self.tp:
                        self.position.close()
                        print(f"🌙 Moon Dev: SHORT hit TP {self.tp} (low: {current_low}), closing at {current_close} 🎯")
                        if hasattr(self, 'sl'): del self.sl
                        if hasattr(self, 'tp'): del self.tp
                        if hasattr(self, 'entry_price'): del self.entry_price
                        if hasattr(self, 'sl_distance'): del self.sl_distance
                        return

        # Approximate harmonic confluence - loosened for more setups
        harmonic_long = abs(current_close - current_ema21) / current_ema21 < self.confluence_threshold
        harmonic_short = abs(current_close - current_ema21) / current_ema21 < self.confluence_threshold

        # 🌙 Moon Dev: Removed early exit on opposite crossover to let winners run longer with trailing stops, improving return potential

        # ADX rising filter for strengthening trends
        adx_rising = True
        if len(self.adx) > 1:
            adx_rising = current_adx > self.adx[-2]

        # Long Entry - Loosened RSI to >50, volume to 1.5x, added rising ADX, kept long-term trend filter
        if (not self.position and
            self.ema5[-2] < self.ema13[-2] and self.ema5[-1] > self.ema13[-1] and
            self.ema21[-1] > self.ema55[-1] and
            self.ema13[-1] > self.ema21[-1] and
            self.ema55[-1] > self.sma200[-1] and  # 🌙 Moon Dev: Retained EMA55 > SMA200 for uptrend confirmation
            current_rsi > 50 and  # 🌙 Moon Dev: Loosened from >55 to >50 for more bullish momentum opportunities
            current_close > self.sma200[-1] and
            current_volume > self.volume_multiplier * self.volume_ma[-1] and  # 🌙 Moon Dev: Loosened to 1.5x for increased trade frequency
            current_adx > self.adx_threshold and  # 🌙 Moon Dev: ADX trend filter
            adx_rising and  # 🌙 Moon Dev: Added rising ADX for better entry in accelerating trends
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
            self.sl_distance = sl_distance
            print(f"🌙 Moon Dev: LONG Entry at {current_close} | SL: {sl_price} | TP: {tp_price} | Size: {position_size} | ADX: {current_adx:.2f} (Rising: {adx_rising}) 🚀 Trailing-Ready Enhanced Entry ✨")

        # Short Entry - Symmetric enhancements: Loosened RSI to <50, volume to 1.5x, added rising ADX
        elif (not self.position and
              self.ema5[-2] > self.ema13[-2] and self.ema5[-1] < self.ema13[-1] and
              self.ema21[-1] < self.ema55[-1] and
              self.ema13[-1] < self.ema21[-1] and
              self.ema55[-1] < self.sma200[-1] and  # 🌙 Moon Dev: Retained EMA55 < SMA200 for downtrend confirmation
              current_rsi < 50 and  # 🌙 Moon Dev: Loosened from <45 to <50 for more bearish momentum opportunities
              current_close < self.sma200[-1] and
              current_volume > self.volume_multiplier * self.volume_ma[-1] and  # 🌙 Moon Dev: Loosened to 1.5x for increased trade frequency
              current_adx > self.adx_threshold and  # 🌙 Moon Dev: ADX trend filter
              adx_rising and  # 🌙 Moon Dev: Added rising ADX for better entry in accelerating trends
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
            self.sl_distance = sl_distance
            print(f"🌙 Moon Dev: SHORT Entry at {current_close} | SL: {sl_price} | TP: {tp_price} | Size: {position_size} | ADX: {current_adx:.2f} (Rising: {adx_rising}) 📉 Trailing-Ready Enhanced Entry ✨")

# Run backtest
bt = Backtest(data, FibonacciCrossover, cash=1_000_000, commission=0.002, exclusive_orders=True)
stats = bt.run()
print(stats)