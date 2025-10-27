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
    adx_period = 14  # 🌙 Moon Dev: Added ADX period for trend strength filter
    adx_threshold = 25  # 🌙 Moon Dev: ADX threshold to ensure trending conditions (>25 avoids choppy markets)
    risk_per_trade = 0.005  # 🌙 Moon Dev: Reduced risk per trade from 0.01 to 0.005 to lower drawdown and improve risk management
    rr_ratio = 4  # 🌙 Moon Dev: Increased RR ratio from 3 to 4 to target larger profits in volatile BTC trends while maintaining risk-reward balance
    atr_multiplier_sl = 2.0  # 🌙 Moon Dev: Widened SL multiplier from 1.5 to 2.0 to reduce whipsaws in volatile 15m BTC
    confluence_threshold = 0.01  # 🌙 Moon Dev: Loosened confluence threshold from 0.005 to 0.01 to allow more valid entries without sacrificing quality

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
        self.adx = self.I(talib.ADX, high, low, close, timeperiod=self.adx_period)  # 🌙 Moon Dev: Added ADX indicator for market regime filtering to trade only in strong trends

        print("🌙 Moon Dev: Initialized Optimized FibonacciCrossover Strategy ✨")

    def next(self):
        current_close = self.data.Close[-1]
        current_high = self.data.High[-1]
        current_low = self.data.Low[-1]
        current_volume = self.data.Volume[-1]
        current_rsi = self.rsi[-1]
        current_atr = self.atr[-1]
        current_ema21 = self.ema21[-1]

        # Manual SL/TP management and new optimizations (partial close, breakeven) - checked at end of bar, close at close price - approximation
        if self.position:
            current_price = current_close  # For profit calculations

            if self.position.is_long:
                # 🌙 Moon Dev: Partial close at 2R to lock in profits on half position, improving returns by securing gains early
                if (not hasattr(self, 'partial_closed') and
                    hasattr(self, 'entry_price') and hasattr(self, 'initial_risk') and hasattr(self, 'initial_size')):
                    if current_high >= self.entry_price + 2 * self.initial_risk:
                        half_size = self.initial_size / 2
                        self.position.close(size=half_size)
                        self.partial_closed = True
                        print(f"🌙 Moon Dev: Partial LONG close at 2R (high: {current_high}), size {half_size} 🎂 Locking profits!")

                # 🌙 Moon Dev: Move to breakeven at 1R to protect capital once in profit, reducing risk on winning trades
                if (hasattr(self, 'entry_price') and hasattr(self, 'initial_risk')):
                    profit = current_price - self.entry_price
                    if profit > self.initial_risk and self.sl < self.entry_price:
                        old_sl = self.sl
                        self.sl = self.entry_price
                        print(f"🌙 Moon Dev: Moved LONG SL to breakeven from {old_sl} at 1R profit 🔒")

                # Original SL/TP check (now with potentially updated SL)
                if hasattr(self, 'sl') and hasattr(self, 'tp'):
                    if current_low <= self.sl:
                        self.position.close()
                        print(f"🌙 Moon Dev: LONG hit SL {self.sl} (low: {current_low}), closing at {current_close} 💥")
                        # 🌙 Moon Dev: Clean up all entry attributes on full close
                        attrs_to_del = ['sl', 'tp', 'entry_price', 'initial_risk', 'initial_size', 'partial_closed']
                        for attr in attrs_to_del:
                            if hasattr(self, attr):
                                delattr(self, attr)
                        return
                    elif current_high >= self.tp:
                        self.position.close()
                        print(f"🌙 Moon Dev: LONG hit TP {self.tp} (high: {current_high}), closing at {current_close} 🎯")
                        # Clean up
                        for attr in attrs_to_del:
                            if hasattr(self, attr):
                                delattr(self, attr)
                        return

            elif self.position.is_short:
                # Partial close at 2R for short
                if (not hasattr(self, 'partial_closed') and
                    hasattr(self, 'entry_price') and hasattr(self, 'initial_risk') and hasattr(self, 'initial_size')):
                    if current_low <= self.entry_price - 2 * self.initial_risk:
                        half_size = self.initial_size / 2
                        self.position.close(size=half_size)
                        self.partial_closed = True
                        print(f"🌙 Moon Dev: Partial SHORT close at 2R (low: {current_low}), size {half_size} 🎂 Locking profits!")

                # Breakeven for short
                if (hasattr(self, 'entry_price') and hasattr(self, 'initial_risk')):
                    profit = self.entry_price - current_price
                    if profit > self.initial_risk and self.sl > self.entry_price:
                        old_sl = self.sl
                        self.sl = self.entry_price
                        print(f"🌙 Moon Dev: Moved SHORT SL to breakeven from {old_sl} at 1R profit 🔒")

                # SL/TP check for short
                if hasattr(self, 'sl') and hasattr(self, 'tp'):
                    if current_high >= self.sl:
                        self.position.close()
                        print(f"🌙 Moon Dev: SHORT hit SL {self.sl} (high: {current_high}), closing at {current_close} 💥")
                        # Clean up
                        attrs_to_del = ['sl', 'tp', 'entry_price', 'initial_risk', 'initial_size', 'partial_closed']
                        for attr in attrs_to_del:
                            if hasattr(self, attr):
                                delattr(self, attr)
                        return
                    elif current_low <= self.tp:
                        self.position.close()
                        print(f"🌙 Moon Dev: SHORT hit TP {self.tp} (low: {current_low}), closing at {current_close} 🎯")
                        # Clean up
                        for attr in attrs_to_del:
                            if hasattr(self, attr):
                                delattr(self, attr)
                        return

        # Approximate harmonic confluence in next (using latest)
        harmonic_long = abs(current_close - current_ema21) / current_ema21 < self.confluence_threshold
        harmonic_short = abs(current_close - current_ema21) / current_ema21 < self.confluence_threshold

        # Early exit on opposite crossover (full close)
        if self.position.is_long:
            if self.ema5[-2] > self.ema13[-2] and self.ema5[-1] < self.ema13[-1]:
                self.position.close()
                print(f"🌙 Moon Dev: Closed Long on Bearish Crossover at {self.data.index[-1]} 📉")
                # Clean up on full close
                attrs_to_del = ['sl', 'tp', 'entry_price', 'initial_risk', 'initial_size', 'partial_closed']
                for attr in attrs_to_del:
                    if hasattr(self, attr):
                        delattr(self, attr)
                return

        if self.position.is_short:
            if self.ema5[-2] < self.ema13[-2] and self.ema5[-1] > self.ema13[-1]:
                self.position.close()
                print(f"🌙 Moon Dev: Closed Short on Bullish Crossover at {self.data.index[-1]} 📈")
                # Clean up
                attrs_to_del = ['sl', 'tp', 'entry_price', 'initial_risk', 'initial_size', 'partial_closed']
                for attr in attrs_to_del:
                    if hasattr(self, attr):
                        delattr(self, attr)
                return

        # Long Entry - Optimized with tighter RSI (>50), EMA13 > EMA21 filter for stronger uptrend, higher volume threshold (1.5x MA), ADX trend filter, and EMA55 > SMA200 for long-term alignment
        if (not self.position and
            self.ema5[-2] < self.ema13[-2] and self.ema5[-1] > self.ema13[-1] and
            self.ema21[-1] > self.ema55[-1] and
            self.ema13[-1] > self.ema21[-1] and  # 🌙 Moon Dev: Added EMA13 > EMA21 filter to ensure momentum aligns with medium-term trend, improving entry quality
            self.ema55[-1] > self.sma200[-1] and  # 🌙 Moon Dev: Added EMA55 > SMA200 filter for stronger long-term uptrend confirmation, filtering out counter-trend trades
            current_rsi > 50 and  # 🌙 Moon Dev: Tightened RSI from >40 to >50 to avoid weaker bullish signals
            current_close > self.sma200[-1] and
            current_volume > 1.5 * self.volume_ma[-1] and  # 🌙 Moon Dev: Increased volume filter from >MA to >1.5*MA for stronger confirmation of interest
            self.adx[-1] > self.adx_threshold and  # 🌙 Moon Dev: Added ADX > 25 filter to ensure strong trend, avoiding ranging markets for higher win rate and returns
            harmonic_long):
            
            if np.isnan(current_atr) or current_atr <= 0:
                print("🌙 Moon Dev: Skipping LONG due to invalid ATR")
                return
            
            sl_distance = current_atr * self.atr_multiplier_sl
            risk_amount = self.equity * self.risk_per_trade
            position_size = risk_amount / sl_distance  # 🌙 Moon Dev: Use float for precise position sizing without rounding loss
            if position_size <= 0:
                print("🌙 Moon Dev: Skipping LONG due to zero size")
                return
            
            sl_price = current_close - sl_distance
            tp_distance = sl_distance * self.rr_ratio
            tp_price = current_close + tp_distance
            
            if sl_price >= current_close or tp_price <= current_close:
                print(f"🌙 Moon Dev: Skipping LONG due to invalid levels - SL:{sl_price} Entry:{current_close} TP:{tp_price}")
                return
            
            max_size = self.equity / current_close  # 🌙 Moon Dev: Float max size for precision
            position_size = min(position_size, max_size)
            
            if position_size <= 0:
                return
            
            self.buy(size=position_size)
            self.sl = sl_price
            self.tp = tp_price
            self.entry_price = current_close
            self.initial_risk = sl_distance
            self.initial_size = position_size
            print(f"🌙 Moon Dev: LONG Entry at {current_close} | SL: {sl_price} | TP: {tp_price} | Size: {position_size} 🚀 Optimized Harmonic Confluence Confirmed ✨")

        # Short Entry - Optimized with tighter RSI (<50), EMA13 < EMA21 filter for stronger downtrend, higher volume threshold (1.5x MA), ADX trend filter, and EMA55 < SMA200 for long-term alignment
        elif (not self.position and
              self.ema5[-2] > self.ema13[-2] and self.ema5[-1] < self.ema13[-1] and
              self.ema21[-1] < self.ema55[-1] and
              self.ema13[-1] < self.ema21[-1] and  # 🌙 Moon Dev: Added EMA13 < EMA21 filter to ensure momentum aligns with medium-term trend, improving entry quality
              self.ema55[-1] < self.sma200[-1] and  # 🌙 Moon Dev: Added EMA55 < SMA200 filter for stronger long-term downtrend confirmation, filtering out counter-trend trades
              current_rsi < 50 and  # 🌙 Moon Dev: Tightened RSI from <60 to <50 to avoid weaker bearish signals
              current_close < self.sma200[-1] and
              current_volume > 1.5 * self.volume_ma[-1] and  # 🌙 Moon Dev: Increased volume filter from >MA to >1.5*MA for stronger confirmation of interest
              self.adx[-1] > self.adx_threshold and  # 🌙 Moon Dev: Added ADX > 25 filter to ensure strong trend, avoiding ranging markets for higher win rate and returns
              harmonic_short):
            
            if np.isnan(current_atr) or current_atr <= 0:
                print("🌙 Moon Dev: Skipping SHORT due to invalid ATR")
                return
            
            sl_distance = current_atr * self.atr_multiplier_sl
            risk_amount = self.equity * self.risk_per_trade
            position_size = risk_amount / sl_distance  # 🌙 Moon Dev: Use float for precise position sizing without rounding loss
            if position_size <= 0:
                print("🌙 Moon Dev: Skipping SHORT due to zero size")
                return
            
            sl_price = current_close + sl_distance
            tp_distance = sl_distance * self.rr_ratio
            tp_price = current_close - tp_distance
            
            if sl_price <= current_close or tp_price >= current_close:
                print(f"🌙 Moon Dev: Skipping SHORT due to invalid levels - SL:{sl_price} Entry:{current_close} TP:{tp_price}")
                return
            
            max_size = self.equity / current_close  # 🌙 Moon Dev: Float max size for precision
            position_size = min(position_size, max_size)
            
            if position_size <= 0:
                return
            
            self.sell(size=position_size)
            self.sl = sl_price
            self.tp = tp_price
            self.entry_price = current_close
            self.initial_risk = sl_distance
            self.initial_size = position_size
            print(f"🌙 Moon Dev: SHORT Entry at {current_close} | SL: {sl_price} | TP: {tp_price} | Size: {position_size} 📉 Optimized Harmonic Confluence Confirmed ✨")

# Run backtest
bt = Backtest(data, FibonacciCrossover, cash=1_000_000, commission=0.002, exclusive_orders=True)
stats = bt.run()
print(stats)