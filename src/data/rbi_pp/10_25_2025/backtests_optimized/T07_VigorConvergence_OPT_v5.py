import pandas as pd
import talib
from backtesting import Backtest, Strategy
import numpy as np

# Load and clean data
path = '/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv'
data = pd.read_csv(path, parse_dates=['datetime'], index_col='datetime')
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data = data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
})
data = data[['Open', 'High', 'Low', 'Close', 'Volume']]

class VigorConvergence(Strategy):
    adx_threshold = 30  # 🌙 Moon Dev: Increased from 25 to 30 for stronger trend confirmation, reducing false signals
    risk_per_trade = 0.015  # 🌙 Moon Dev: Slightly increased from 0.01 to 0.015 to amplify returns while keeping risk managed
    atr_multiplier_sl = 2.0  # 🌙 Moon Dev: Widened from 1.5 to 2.0 to give trades more room in volatile crypto markets
    rr_ratio = 3.0  # 🌙 Moon Dev: Increased from 2.0 to 3.0 for higher reward potential per trade
    adx_exit_threshold = 20  # Kept as is for emergency exits on weakening trends

    def init(self):
        # MACD
        self.macd_line, self.macd_signal, self.macd_hist = self.I(
            talib.MACD, self.data.Close, fastperiod=12, slowperiod=26, signalperiod=9
        )
        # ADX and DMI
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        self.plus_di = self.I(talib.PLUS_DI, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        self.minus_di = self.I(talib.MINUS_DI, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        # ATR for stops
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        # 🌙 Moon Dev: Added EMA50 for trend filter to only trade in direction of medium-term trend
        self.ema50 = self.I(talib.EMA, self.data.Close, timeperiod=50)
        # 🌙 Moon Dev: Added RSI to avoid overbought/oversold entries, improving entry quality
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14)
        # 🌙 Moon Dev: Added volume SMA for filter to ensure entries on above-average volume (momentum confirmation)
        self.vol_sma = self.I(talib.SMA, self.data.Volume, timeperiod=20)

    def next(self):
        # Current values
        current_close = self.data.Close[-1]
        current_atr = self.atr[-1]
        current_adx = self.adx[-1]
        current_plus_di = self.plus_di[-1]
        current_minus_di = self.minus_di[-1]
        current_macd = self.macd_line[-1]
        prev_macd = self.macd_line[-2]
        current_signal = self.macd_signal[-1]
        prev_signal = self.macd_signal[-2]
        current_rsi = self.rsi[-1]
        current_ema50 = self.ema50[-1]
        current_volume = self.data.Volume[-1]
        current_vol_sma = self.vol_sma[-1]

        # Crossover detections
        macd_cross_up = current_macd > current_signal and prev_macd <= prev_signal
        macd_cross_down = current_macd < current_signal and prev_macd >= prev_signal

        # Check for emergency exit if ADX weakens
        if self.position and current_adx < self.adx_exit_threshold:
            self.position.close()
            print(f"🌙 Moon Dev: Emergency exit due to weak trend (ADX < {self.adx_exit_threshold}) at {self.data.index[-1]} 🚀")

        # Exit on opposite signal
        if self.position.is_long and macd_cross_down:
            self.position.close()
            print(f"🌙 Moon Dev: Long exit on bearish MACD crossover at {self.data.index[-1]} ✨")
        elif self.position.is_short and macd_cross_up:
            self.position.close()
            print(f"🌙 Moon Dev: Short exit on bullish MACD crossover at {self.data.index[-1]} ✨")

        # Entry logic only if no position
        if not self.position:
            if (macd_cross_up and 
                current_adx > self.adx_threshold and 
                current_plus_di > current_minus_di and
                current_close > current_ema50 and  # 🌙 Moon Dev: Trend filter - only long above EMA50
                current_rsi < 70 and  # 🌙 Moon Dev: Avoid overbought longs
                current_volume > current_vol_sma):  # 🌙 Moon Dev: Volume filter for momentum confirmation
                # Long entry
                sl_price = current_close - self.atr_multiplier_sl * current_atr
                risk_dist = current_close - sl_price
                tp_dist = self.rr_ratio * risk_dist
                tp_price = current_close + tp_dist

                # Position sizing: risk fixed % of equity, size as float for fractional BTC
                equity = self._broker.get_cash() + self._broker.get_value()  # 🌙 Moon Dev: Accurate equity calculation
                risk_amount = equity * self.risk_per_trade
                size = risk_amount / risk_dist  # 🌙 Moon Dev: Simplified to float size for precise risk (no int rounding)

                self.buy(sl=sl_price, tp=tp_price, size=size)
                print(f"🌙 Moon Dev: Long entry at {current_close}, SL: {sl_price}, TP: {tp_price}, Size: {size} 🚀")

            elif (macd_cross_down and 
                  current_adx > self.adx_threshold and 
                  current_minus_di > current_plus_di and
                  current_close < current_ema50 and  # 🌙 Moon Dev: Trend filter - only short below EMA50
                  current_rsi > 30 and  # 🌙 Moon Dev: Avoid oversold shorts
                  current_volume > current_vol_sma):  # 🌙 Moon Dev: Volume filter for momentum confirmation
                # Short entry
                sl_price = current_close + self.atr_multiplier_sl * current_atr
                risk_dist = sl_price - current_close
                tp_dist = self.rr_ratio * risk_dist
                tp_price = current_close - tp_dist

                # Position sizing: risk fixed % of equity, size as float for fractional BTC
                equity = self._broker.get_cash() + self._broker.get_value()  # 🌙 Moon Dev: Accurate equity calculation
                risk_amount = equity * self.risk_per_trade
                size = risk_amount / risk_dist  # 🌙 Moon Dev: Simplified to float size for precise risk (no int rounding)

                self.sell(sl=sl_price, tp=tp_price, size=size)
                print(f"🌙 Moon Dev: Short entry at {current_close}, SL: {sl_price}, TP: {tp_price}, Size: {size} 🚀")

        # Debug print every 100 bars or so
        if len(self.data) % 100 == 0:
            print(f"🌙 Moon Dev Backtest Progress: {self.data.index[-1]}, ADX: {current_adx:.2f}, MACD: {current_macd:.2f} ✨")

# Run backtest
bt = Backtest(data, VigorConvergence, cash=1000000, commission=0.001, exclusive_orders=True)
stats = bt.run()
print(stats)