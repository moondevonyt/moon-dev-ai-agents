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
    adx_threshold = 28  # 🌙 Optimization: Increased ADX threshold to 28 for stronger trend confirmation, reducing false signals
    risk_per_trade = 0.01  # 🌙 Optimization: Kept at 1% but with better filters, this allows consistent risk
    atr_multiplier_sl = 2.0  # 🌙 Optimization: Widened SL to 2x ATR to give trades more breathing room and reduce whipsaws
    rr_ratio = 3.0  # 🌙 Optimization: Increased RR to 3:1 for higher reward potential on winning trades
    adx_exit_threshold = 15  # 🌙 Optimization: Lowered emergency exit threshold to 15 to avoid closing winners prematurely

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
        # 🌙 Optimization: Added RSI for momentum filter to avoid overextended entries
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14)
        # 🌙 Optimization: Added volume SMA for confirmation of strong moves
        self.avg_vol = self.I(talib.SMA, self.data.Volume, timeperiod=20)
        # 🌙 Optimization: Added EMA trend filter to align trades with the broader trend, improving win rate
        self.ema_fast = self.I(talib.EMA, self.data.Close, timeperiod=50)
        self.ema_slow = self.I(talib.EMA, self.data.Close, timeperiod=200)

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
        # 🌙 Optimization: Added new current values for filters
        current_rsi = self.rsi[-1]
        current_vol = self.data.Volume[-1]
        current_avg_vol = self.avg_vol[-1]
        current_ema_fast = self.ema_fast[-1]
        current_ema_slow = self.ema_slow[-1]

        # Crossover detections
        macd_cross_up = current_macd > current_signal and prev_macd <= prev_signal
        macd_cross_down = current_macd < current_signal and prev_macd >= prev_signal

        # 🌙 Optimization: Added trailing stop logic to lock in profits dynamically while letting winners run
        if self.position:
            if self.position.is_long:
                trail_sl = current_close - self.atr_multiplier_sl * current_atr
                if trail_sl > self.position.sl:
                    self.position.sl = trail_sl
                    print(f"🌙 Moon Dev: Trailing SL for long to {trail_sl} at {self.data.index[-1]} 🚀")
            elif self.position.is_short:
                trail_sl = current_close + self.atr_multiplier_sl * current_atr
                if trail_sl < self.position.sl:
                    self.position.sl = trail_sl
                    print(f"🌙 Moon Dev: Trailing SL for short to {trail_sl} at {self.data.index[-1]} 🚀")

        # Check for emergency exit if ADX weakens
        if self.position and current_adx < self.adx_exit_threshold:
            self.position.close()
            print(f"🌙 Moon Dev: Emergency exit due to weak trend (ADX < {self.adx_exit_threshold}) at {self.data.index[-1]} 🚀")

        # Exit on opposite signal (kept to manage risk, but trailing helps capture more upside)
        if self.position.is_long and macd_cross_down:
            self.position.close()
            print(f"🌙 Moon Dev: Long exit on bearish MACD crossover at {self.data.index[-1]} ✨")
        elif self.position.is_short and macd_cross_up:
            self.position.close()
            print(f"🌙 Moon Dev: Short exit on bullish MACD crossover at {self.data.index[-1]} ✨")

        # Entry logic only if no position
        if not self.position:
            if (macd_cross_up and current_adx > self.adx_threshold and current_plus_di > current_minus_di and
                current_rsi > 45 and current_close > current_ema_fast and current_ema_fast > current_ema_slow and
                current_vol > current_avg_vol * 1.2):  # 🌙 Optimization: Added RSI >45, EMA trend alignment, and volume >1.2x avg for high-quality long setups
                # Long entry
                sl_price = current_close - self.atr_multiplier_sl * current_atr
                risk_dist = current_close - sl_price
                # 🌙 Optimization: Removed fixed TP to rely on trailing stops for better profit capture; initial RR used for sizing reference if needed
                # tp_dist = self.rr_ratio * risk_dist
                # tp_price = current_close + tp_dist

                # Position sizing: risk 1% of equity
                equity = self.equity
                risk_amount = equity * self.risk_per_trade
                size = risk_amount / risk_dist  # 🌙 Optimization: Simplified to direct units, allowing fractional sizes for precision

                self.buy(sl=sl_price, size=size)  # No TP, use trailing
                print(f"🌙 Moon Dev: Long entry at {current_close}, SL: {sl_price}, Size: {size} 🚀")

            elif (macd_cross_down and current_adx > self.adx_threshold and current_minus_di > current_plus_di and
                  current_rsi < 55 and current_close < current_ema_fast and current_ema_fast < current_ema_slow and
                  current_vol > current_avg_vol * 1.2):  # 🌙 Optimization: Added RSI <55, EMA trend alignment, and volume >1.2x avg for high-quality short setups
                # Short entry
                sl_price = current_close + self.atr_multiplier_sl * current_atr
                risk_dist = sl_price - current_close
                # 🌙 Optimization: Removed fixed TP to rely on trailing stops for better profit capture
                # tp_dist = self.rr_ratio * risk_dist
                # tp_price = current_close - tp_dist

                # Position sizing: risk 1% of equity
                equity = self.equity
                risk_amount = equity * self.risk_per_trade
                size = risk_amount / risk_dist  # 🌙 Optimization: Simplified to direct units, allowing fractional sizes for precision

                self.sell(sl=sl_price, size=size)  # No TP, use trailing
                print(f"🌙 Moon Dev: Short entry at {current_close}, SL: {sl_price}, Size: {size} 🚀")

        # Debug print every 100 bars or so
        if len(self.data) % 100 == 0:
            print(f"🌙 Moon Dev Backtest Progress: {self.data.index[-1]}, ADX: {current_adx:.2f}, MACD: {current_macd:.2f}, RSI: {current_rsi:.2f} ✨")  # 🌙 Optimization: Added RSI to debug for monitoring

# Run backtest
bt = Backtest(data, VigorConvergence, cash=1000000, commission=0.001, exclusive_orders=True)
stats = bt.run()
print(stats)