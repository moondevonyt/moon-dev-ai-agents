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
    adx_threshold = 20  # 🌙 Moon Dev: Lowered ADX threshold from 25 to 20 to capture more trending opportunities without excessive chop, increasing trade frequency realistically
    risk_per_trade = 0.01  # 🌙 Moon Dev: Increased risk per trade from 0.005 to 0.01 for more aggressive position sizing to accelerate returns toward 50% target while monitoring drawdowns
    rr_ratio = 5  # 🌙 Moon Dev: Increased RR ratio from 4 to 5 to aim for larger profit captures in BTC's volatile trends, boosting overall returns
    atr_multiplier_sl = 1.5  # 🌙 Moon Dev: Tightened SL multiplier from 2.0 to 1.5 ATR to reduce risk exposure per trade, improving risk-reward efficiency
    confluence_threshold = 0.01  # 🌙 Moon Dev: Loosened confluence threshold from 0.005 to 0.01 to allow slightly more pullback entries near EMA21, increasing valid setups without overtrading
    trailing_atr_multiplier = 1.5  # 🌙 Moon Dev: New parameter for trailing stop: lock in profits at 1.5 ATR above entry once price moves favorably, to capture extended trends

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
        self.adx = self.I(talib.ADX, high, low, close, timeperiod=self.adx_period)  # 🌙 Moon Dev: Retained ADX initialization for trending regime filter

        print("🌙 Moon Dev: Initialized Further Optimized FibonacciCrossover Strategy with Trailing Stops and Loosened Filters for Higher Returns ✨")

    def next(self):
        current_close = self.data.Close[-1]
        current_high = self.data.High[-1]
        current_low = self.data.Low[-1]
        current_volume = self.data.Volume[-1]
        current_rsi = self.rsi[-1]
        current_atr = self.atr[-1]
        current_ema21 = self.ema21[-1]
        current_adx = self.adx[-1]  # 🌙 Moon Dev: Retrieve current ADX for trend strength check

        # Manual SL/TP management with added trailing stop logic (checked at end of bar, close at close price - approximation)
        if self.position:
            if hasattr(self, 'sl') and hasattr(self, 'tp') and hasattr(self, 'entry_price'):
                if self.position.is_long:
                    # Trailing stop: If price has moved favorably by trailing_atr_multiplier * ATR, update SL to lock profits
                    favorable_move = current_close - self.entry_price
                    if favorable_move > self.trailing_atr_multiplier * current_atr:
                        new_sl = max(self.sl, self.entry_price + self.trailing_atr_multiplier * current_atr)
                        self.sl = new_sl
                        print(f"🌙 Moon Dev: Trailing SL updated for LONG to {self.sl} (favorable move: {favorable_move:.2f}) 🔒")
                    
                    if current_low <= self.sl:
                        self.position.close()
                        print(f"🌙 Moon Dev: LONG hit SL {self.sl} (low: {current_low}), closing at {current_close} 💥")
                        if hasattr(self, 'sl'): del self.sl
                        if hasattr(self, 'tp'): del self.tp
                        if hasattr(self, 'entry_price'): del self.entry_price
                        return
                    elif current_high >= self.tp:
                        self.position.close()
                        print(f"🌙 Moon Dev: LONG hit TP {self.tp} (high: {current_high}), closing at {current_close} 🎯")
                        if hasattr(self, 'sl'): del self.sl
                        if hasattr(self, 'tp'): del self.tp
                        if hasattr(self, 'entry_price'): del self.entry_price
                        return
                elif self.position.is_short:
                    # Trailing stop: If price has moved favorably by trailing_atr_multiplier * ATR, update SL to lock profits
                    favorable_move = self.entry_price - current_close
                    if favorable_move > self.trailing_atr_multiplier * current_atr:
                        new_sl = min(self.sl, self.entry_price - self.trailing_atr_multiplier * current_atr)
                        self.sl = new_sl
                        print(f"🌙 Moon Dev: Trailing SL updated for SHORT to {self.sl} (favorable move: {favorable_move:.2f}) 🔒")
                    
                    if current_high >= self.sl:
                        self.position.close()
                        print(f"🌙 Moon Dev: SHORT hit SL {self.sl} (high: {current_high}), closing at {current_close} 💥")
                        if hasattr(self, 'sl'): del self.sl
                        if hasattr(self, 'tp'): del self.tp
                        if hasattr(self, 'entry_price'): del self.entry_price
                        return
                    elif current_low <= self.tp:
                        self.position.close()
                        print(f"🌙 Moon Dev: SHORT hit TP {self.tp} (low: {current_low}), closing at {current_close} 🎯")
                        if hasattr(self, 'sl'): del self.sl
                        if hasattr(self, 'tp'): del self.tp
                        if hasattr(self, 'entry_price'): del self.entry_price
                        return

        # Approximate harmonic confluence in next (using latest) - loosened for more entries
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

        # Long Entry - Retained core conditions but loosened RSI (>50 from >55), volume (1.5x from 2x), and ADX (20 from 25) for more frequent high-quality entries
        if (not self.position and
            self.ema5[-2] < self.ema13[-2] and self.ema5[-1] > self.ema13[-1] and
            self.ema21[-1] > self.ema55[-1] and
            self.ema13[-1] > self.ema21[-1] and
            self.ema55[-1] > self.sma200[-1] and  # 🌙 Moon Dev: Retained EMA55 > SMA200 filter for long-term uptrend alignment
            current_rsi > 50 and  # 🌙 Moon Dev: Loosened RSI from >55 to >50 for broader bullish momentum capture, increasing trade opportunities
            current_close > self.sma200[-1] and
            current_volume > 1.5 * self.volume_ma[-1] and  # 🌙 Moon Dev: Reduced volume filter from 2x to 1.5x MA to include more conviction entries without sacrificing quality
            current_adx > self.adx_threshold and  # 🌙 Moon Dev: Retained ADX filter with lowered threshold for more trending setups
            harmonic_long):
            
            if np.isnan(current_atr) or current_atr <= 0:
                print("🌙 Moon Dev: Skipping LONG due to invalid ATR")
                return
            
            sl_distance = current_atr * self.atr_multiplier_sl
            risk_amount = self.equity * self.risk_per_trade
            position_size = risk_amount / sl_distance  # 🌙 Moon Dev: Changed to float for fractional sizing, allowing precise risk management in BTC trades
            
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
            self.entry_price = current_close  # 🌙 Moon Dev: Track entry price for trailing stop logic
            print(f"🌙 Moon Dev: LONG Entry at {current_close} | SL: {sl_price} | TP: {tp_price} | Size: {position_size:.4f} | ADX: {current_adx:.2f} 🚀 Optimized Entry with Trailing Potential Confirmed ✨")

        # Short Entry - Retained core conditions but loosened RSI (<50 from <45), volume (1.5x from 2x), and ADX (20 from 25) for more frequent high-quality entries
        elif (not self.position and
              self.ema5[-2] > self.ema13[-2] and self.ema5[-1] < self.ema13[-1] and
              self.ema21[-1] < self.ema55[-1] and
              self.ema13[-1] < self.ema21[-1] and
              self.ema55[-1] < self.sma200[-1] and  # 🌙 Moon Dev: Retained EMA55 < SMA200 filter for long-term downtrend alignment
              current_rsi < 50 and  # 🌙 Moon Dev: Loosened RSI from <45 to <50 for broader bearish momentum capture, increasing trade opportunities
              current_close < self.sma200[-1] and
              current_volume > 1.5 * self.volume_ma[-1] and  # 🌙 Moon Dev: Reduced volume filter from 2x to 1.5x MA to include more conviction entries without sacrificing quality
              current_adx > self.adx_threshold and  # 🌙 Moon Dev: Retained ADX filter with lowered threshold for more trending setups
              harmonic_short):
            
            if np.isnan(current_atr) or current_atr <= 0:
                print("🌙 Moon Dev: Skipping SHORT due to invalid ATR")
                return
            
            sl_distance = current_atr * self.atr_multiplier_sl
            risk_amount = self.equity * self.risk_per_trade
            position_size = risk_amount / sl_distance  # 🌙 Moon Dev: Changed to float for fractional sizing, allowing precise risk management in BTC trades
            
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
            self.entry_price = current_close  # 🌙 Moon Dev: Track entry price for trailing stop logic
            print(f"🌙 Moon Dev: SHORT Entry at {current_close} | SL: {sl_price} | TP: {tp_price} | Size: {position_size:.4f} | ADX: {current_adx:.2f} 📉 Optimized Entry with Trailing Potential Confirmed ✨")

# Run backtest
bt = Backtest(data, FibonacciCrossover, cash=1_000_000, commission=0.002, exclusive_orders=True)
stats = bt.run()
print(stats)