from backtesting import Backtest, Strategy
import talib
import pandas as pd
import numpy as np

# Load and prepare data
data_path = '/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv'
data = pd.read_csv(data_path, parse_dates=['datetime'], index_col='datetime')

# Clean column names
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])

# Ensure proper column mapping
data = data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
})

class FibonacciCrossover(Strategy):
    ema5_period = 5
    ema13_period = 13
    ema21_period = 21
    ema55_period = 55
    rsi_period = 14
    atr_period = 14
    sma200_period = 200
    volume_ma_period = 20
    risk_per_trade = 0.01
    rr_ratio = 2
    atr_multiplier_sl = 1.5
    confluence_threshold = 0.005  # 0.5% near EMA21 for harmonic approximation

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

        print("🌙 Moon Dev: Initialized FibonacciCrossover Strategy ✨")

    def next(self):
        current_close = self.data.Close[-1]
        current_high = self.data.High[-1]
        current_low = self.data.Low[-1]
        current_volume = self.data.Volume[-1]
        current_rsi = self.rsi[-1]
        current_atr = self.atr[-1]
        current_ema21 = self.ema21[-1]

        # Approximate harmonic confluence in next (using latest)
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

        # Long Entry
        if (not self.position and
            self.ema5[-2] < self.ema13[-2] and self.ema5[-1] > self.ema13[-1] and
            self.ema21[-1] > self.ema55[-1] and
            current_rsi > 40 and
            current_close > self.sma200[-1] and
            current_volume > self.volume_ma[-1] and
            harmonic_long):
            
            sl_distance = current_atr * self.atr_multiplier_sl
            risk_amount = self.equity * self.risk_per_trade
            position_size = risk_amount / sl_distance
            position_size = int(round(position_size))
            
            sl_price = current_close - sl_distance
            tp_distance = sl_distance * self.rr_ratio
            tp_price = current_close + tp_distance
            
            self.buy(size=position_size, sl=sl_price, tp=tp_price)
            print(f"🌙 Moon Dev: LONG Entry at {current_close} | SL: {sl_price} | TP: {tp_price} | Size: {position_size} 🚀 Harmonic Confluence Confirmed ✨")

        # Short Entry
        elif (not self.position and
              self.ema5[-2] > self.ema13[-2] and self.ema5[-1] < self.ema13[-1] and
              self.ema21[-1] < self.ema55[-1] and
              current_rsi < 60 and
              current_close < self.sma200[-1] and
              current_volume > self.volume_ma[-1] and
              harmonic_short):
            
            sl_distance = current_atr * self.atr_multiplier_sl
            risk_amount = self.equity * self.risk_per_trade
            position_size = risk_amount / sl_distance
            position_size = int(round(position_size))
            
            sl_price = current_close + sl_distance
            tp_distance = sl_distance * self.rr_ratio
            tp_price = current_close - tp_distance
            
            self.sell(size=position_size, sl=sl_price, tp=tp_price)
            print(f"🌙 Moon Dev: SHORT Entry at {current_close} | SL: {sl_price} | TP: {tp_price} | Size: {position_size} 📉 Harmonic Confluence Confirmed ✨")

# Run backtest
bt = Backtest(data, FibonacciCrossover, cash=1_000_000, commission=0.002, exclusive_orders=True)
stats = bt.run()
print(stats)