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
    adx_period = 14  # 🌙 Moon Dev: Added ADX for trend strength filtering to avoid choppy markets and improve signal quality
    adx_threshold = 20  # 🌙 Moon Dev: ADX > 20 ensures sufficient trend strength for entries
    sma200_period = 200
    volume_ma_period = 20
    risk_per_trade = 0.01  # 🌙 Moon Dev: Increased risk per trade from 0.005 to 0.01 to amplify returns while keeping risk managed
    rr_ratio = 4  # 🌙 Moon Dev: Increased RR ratio from 3 to 4 to capture larger profits in trending moves
    atr_multiplier_sl = 2.0  # 🌙 Moon Dev: Kept SL multiplier at 2.0 to minimize whipsaws in volatile BTC 15m
    confluence_threshold = 0.01  # 🌙 Moon Dev: Kept confluence threshold at 0.01 but made directional for better alignment with trend
    trail_trigger_mult = 1.5  # 🌙 Moon Dev: Multiplier of initial ATR to trigger trailing stop
    trail_offset_mult = 1.0  # 🌙 Moon Dev: ATR multiplier for trailing offset to lock in profits dynamically

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
        self.adx = self.I(talib.ADX, high, low, close, timeperiod=self.adx_period)
        self.plus_di = self.I(talib.PLUS_DI, high, low, close, timeperiod=self.adx_period)
        self.minus_di = self.I(talib.MINUS_DI, high, low, close, timeperiod=self.adx_period)

        print("🌙 Moon Dev: Initialized Super Optimized FibonacciCrossover with ADX, DI, Directional Confluence & Trailing Stops ✨")

    def next(self):
        current_close = self.data.Close[-1]
        current_high = self.data.High[-1]
        current_low = self.data.Low[-1]
        current_volume = self.data.Volume[-1]
        current_rsi = self.rsi[-1]
        current_atr = self.atr[-1]
        current_ema21 = self.ema21[-1]

        # Manual SL/TP/Trailing management (checked at end of bar, close at close price - approximation)
        if self.position:
            if hasattr(self, 'sl') and hasattr(self, 'tp'):
                # Trailing stop logic
                if self.position.is_long and hasattr(self, 'entry_price') and hasattr(self, 'initial_atr'):
                    unrealized_profit = current_close - self.entry_price
                    trail_trigger = self.initial_atr * self.trail_trigger_mult
                    if unrealized_profit > trail_trigger:
                        new_sl = current_close - (self.initial_atr * self.trail_offset_mult)
                        self.sl = max(self.sl, new_sl)
                        print(f"🌙 Moon Dev: LONG Trailing SL updated to {self.sl} 🚀")
                elif self.position.is_short and hasattr(self, 'entry_price') and hasattr(self, 'initial_atr'):
                    unrealized_profit = self.entry_price - current_close
                    trail_trigger = self.initial_atr * self.trail_trigger_mult
                    if unrealized_profit > trail_trigger:
                        new_sl = current_close + (self.initial_atr * self.trail_offset_mult)
                        self.sl = min(self.sl, new_sl)
                        print(f"🌙 Moon Dev: SHORT Trailing SL updated to {self.sl} 📉")

                # SL/TP checks
                if self.position.is_long:
                    if current_low <= self.sl:
                        self.position.close()
                        print(f"🌙 Moon Dev: LONG hit SL {self.sl} (low: {current_low}), closing at {current_close} 💥")
                        if hasattr(self, 'sl'): del self.sl
                        if hasattr(self, 'tp'): del self.tp
                        if hasattr(self, 'entry_price'): del self.entry_price
                        if hasattr(self, 'initial_atr'): del self.initial_atr
                        return
                    elif current_high >= self.tp:
                        self.position.close()
                        print(f"🌙 Moon Dev: LONG hit TP {self.tp} (high: {current_high}), closing at {current_close} 🎯")
                        if hasattr(self, 'sl'): del self.sl
                        if hasattr(self, 'tp'): del self.tp
                        if hasattr(self, 'entry_price'): del self.entry_price
                        if hasattr(self, 'initial_atr'): del self.initial_atr
                        return
                elif self.position.is_short:
                    if current_high >= self.sl:
                        self.position.close()
                        print(f"🌙 Moon Dev: SHORT hit SL {self.sl} (high: {current_high}), closing at {current_close} 💥")
                        if hasattr(self, 'sl'): del self.sl
                        if hasattr(self, 'tp'): del self.tp
                        if hasattr(self, 'entry_price'): del self.entry_price
                        if hasattr(self, 'initial_atr'): del self.initial_atr
                        return
                    elif current_low <= self.tp:
                        self.position.close()
                        print(f"🌙 Moon Dev: SHORT hit TP {self.tp} (low: {current_low}), closing at {current_close} 🎯")
                        if hasattr(self, 'sl'): del self.sl
                        if hasattr(self, 'tp'): del self.tp
                        if hasattr(self, 'entry_price'): del self.entry_price
                        if hasattr(self, 'initial_atr'): del self.initial_atr
                        return

        # Directional harmonic confluence (improved: allows slight deviation in trend direction)
        harmonic_long = current_close >= current_ema21 * (1 - self.confluence_threshold)
        harmonic_short = current_close <= current_ema21 * (1 + self.confluence_threshold)

        # Early exit on opposite crossover
        if self.position.is_long:
            if self.ema5[-2] > self.ema13[-2] and self.ema5[-1] < self.ema13[-1]:
                self.position.close()
                print(f"🌙 Moon Dev: Closed Long on Bearish Crossover at {self.data.index[-1]} 📉")
                if hasattr(self, 'sl'): del self.sl
                if hasattr(self, 'tp'): del self.tp
                if hasattr(self, 'entry_price'): del self.entry_price
                if hasattr(self, 'initial_atr'): del self.initial_atr
                return

        if self.position.is_short:
            if self.ema5[-2] < self.ema13[-2] and self.ema5[-1] > self.ema13[-1]:
                self.position.close()
                print(f"🌙 Moon Dev: Closed Short on Bullish Crossover at {self.data.index[-1]} 📈")
                if hasattr(self, 'sl'): del self.sl
                if hasattr(self, 'tp'): del self.tp
                if hasattr(self, 'entry_price'): del self.entry_price
                if hasattr(self, 'initial_atr'): del self.initial_atr
                return

        # Long Entry - Enhanced with ADX/DI trend confirmation, loosened RSI (>45), volume (1.2x MA), directional confluence
        if (not self.position and
            self.ema5[-2] < self.ema13[-2] and self.ema5[-1] > self.ema13[-1] and
            self.ema21[-1] > self.ema55[-1] and
            self.ema13[-1] > self.ema21[-1] and
            current_rsi > 45 and  # 🌙 Moon Dev: Loosened RSI from >50 to >45 to capture more bullish momentum setups
            current_close > self.sma200[-1] and
            current_volume > 1.2 * self.volume_ma[-1] and  # 🌙 Moon Dev: Loosened volume filter from 1.5x to 1.2x MA for more trade opportunities in active markets
            self.adx[-1] > self.adx_threshold and self.plus_di[-1] > self.minus_di[-1] and  # 🌙 Moon Dev: Added ADX >20 and +DI > -DI for strong uptrend confirmation
            harmonic_long):
            
            if np.isnan(current_atr) or current_atr <= 0:
                print("🌙 Moon Dev: Skipping LONG due to invalid ATR")
                return
            
            sl_distance = current_atr * self.atr_multiplier_sl
            risk_amount = self.equity * self.risk_per_trade
            position_size = risk_amount / sl_distance
            
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
            self.entry_price = current_close
            self.initial_atr = current_atr
            print(f"🌙 Moon Dev: LONG Entry at {current_close} | SL: {sl_price} | TP: {tp_price} | Size: {position_size} 🚀 Enhanced Trend & Confluence Confirmed with Trailing Potential ✨")

        # Short Entry - Enhanced with ADX/DI trend confirmation, loosened RSI (<55), volume (1.2x MA), directional confluence
        elif (not self.position and
              self.ema5[-2] > self.ema13[-2] and self.ema5[-1] < self.ema13[-1] and
              self.ema21[-1] < self.ema55[-1] and
              self.ema13[-1] < self.ema21[-1] and
              current_rsi < 55 and  # 🌙 Moon Dev: Loosened RSI from <50 to <55 to capture more bearish momentum setups
              current_close < self.sma200[-1] and
              current_volume > 1.2 * self.volume_ma[-1] and  # 🌙 Moon Dev: Loosened volume filter from 1.5x to 1.2x MA for more trade opportunities in active markets
              self.adx[-1] > self.adx_threshold and self.minus_di[-1] > self.plus_di[-1] and  # 🌙 Moon Dev: Added ADX >20 and -DI > +DI for strong downtrend confirmation
              harmonic_short):
            
            if np.isnan(current_atr) or current_atr <= 0:
                print("🌙 Moon Dev: Skipping SHORT due to invalid ATR")
                return
            
            sl_distance = current_atr * self.atr_multiplier_sl
            risk_amount = self.equity * self.risk_per_trade
            position_size = risk_amount / sl_distance
            
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
            self.entry_price = current_close
            self.initial_atr = current_atr
            print(f"🌙 Moon Dev: SHORT Entry at {current_close} | SL: {sl_price} | TP: {tp_price} | Size: {position_size} 📉 Enhanced Trend & Confluence Confirmed with Trailing Potential ✨")

# Run backtest
bt = Backtest(data, FibonacciCrossover, cash=1_000_000, commission=0.002, exclusive_orders=True)
stats = bt.run()
print(stats)