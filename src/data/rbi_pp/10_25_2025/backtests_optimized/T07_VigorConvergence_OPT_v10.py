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
    adx_threshold = 30  # 🌙 Moon Dev: Increased from 25 to 30 for stronger trend confirmation to reduce false entries in choppy markets
    risk_per_trade = 0.005  # 🌙 Moon Dev: Reduced from 0.01 to 0.005 to improve risk management and lower drawdown while scaling up winners
    atr_multiplier_sl = 1.5
    rr_ratio = 3.0  # 🌙 Moon Dev: Increased from 2.0 to 3.0 for better reward-to-risk, aiming to boost overall returns without overextending
    adx_exit_threshold = 15  # 🌙 Moon Dev: Lowered from 20 to 15 for quicker emergency exits in weakening trends

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
        # 🌙 Moon Dev: Added EMA 200 for long-term trend filter to only trade in favorable market regimes (long above EMA, short below)
        self.ema200 = self.I(talib.EMA, self.data.Close, timeperiod=200)
        # 🌙 Moon Dev: Added Volume SMA 20 filter to avoid low-volume setups, ensuring momentum confirmation
        self.volume_sma = self.I(talib.SMA, self.data.Volume, timeperiod=20)
        # 🌙 Moon Dev: Added RSI 14 filter to avoid counter-trend entries (RSI >50 for longs, <50 for shorts)
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14)

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
        current_ema = self.ema200[-1]
        current_volume = self.data.Volume[-1]
        current_volume_sma = self.volume_sma[-1]
        current_rsi = self.rsi[-1]

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
            # 🌙 Moon Dev: Added multi-filter entry: trend (EMA), volume, RSI for higher quality setups to improve win rate and reduce whipsaws
            if (macd_cross_up and current_adx > self.adx_threshold and current_plus_di > current_minus_di and
                current_close > current_ema and current_volume > current_volume_sma and current_rsi > 50):
                # Long entry
                sl_price = current_close - self.atr_multiplier_sl * current_atr
                risk_dist = current_close - sl_price
                tp_dist = self.rr_ratio * risk_dist
                tp_price = current_close + tp_dist

                # Position sizing: risk fixed % of equity, simplified and allow fractional sizes for precision
                equity = self.equity
                risk_amount = equity * self.risk_per_trade
                size = risk_amount / risk_dist  # 🌙 Moon Dev: Simplified sizing formula, allows float for fractional BTC units

                self.buy(sl=sl_price, tp=tp_price, size=size)
                print(f"🌙 Moon Dev: Long entry at {current_close}, SL: {sl_price}, TP: {tp_price}, Size: {size} 🚀")

            elif (macd_cross_down and current_adx > self.adx_threshold and current_minus_di > current_plus_di and
                  current_close < current_ema and current_volume > current_volume_sma and current_rsi < 50):
                # Short entry
                sl_price = current_close + self.atr_multiplier_sl * current_atr
                risk_dist = sl_price - current_close
                tp_dist = self.rr_ratio * risk_dist
                tp_price = current_close - tp_dist

                # Position sizing: risk fixed % of equity, simplified and allow fractional sizes for precision
                equity = self.equity
                risk_amount = equity * self.risk_per_trade
                size = risk_amount / risk_dist  # 🌙 Moon Dev: Simplified sizing formula, allows float for fractional BTC units

                self.sell(sl=sl_price, tp=tp_price, size=size)
                print(f"🌙 Moon Dev: Short entry at {current_close}, SL: {sl_price}, TP: {tp_price}, Size: {size} 🚀")

        # Debug print every 100 bars or so
        if len(self.data) % 100 == 0:
            print(f"🌙 Moon Dev Backtest Progress: {self.data.index[-1]}, ADX: {current_adx:.2f}, MACD: {current_macd:.2f}, RSI: {current_rsi:.2f} ✨")

# Run backtest
bt = Backtest(data, VigorConvergence, cash=1000000, commission=0.001, exclusive_orders=True)
stats = bt.run()
print(stats)