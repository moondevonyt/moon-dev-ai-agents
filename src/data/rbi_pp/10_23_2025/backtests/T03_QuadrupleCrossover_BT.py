from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import pandas as pd
import talib
import numpy as np

# Load and prepare data
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

class QuadrupleCrossover(Strategy):
    risk_per_trade = 0.01  # 1% risk
    sma1_period = 5
    sma2_period = 13
    sma3_period = 26
    sma4_period = 50
    rsi_period = 14
    atr_period = 14
    atr_sma_period = 20
    time_exit_bars = 10
    volatility_multiplier = 1.5

    def init(self):
        self.sma1 = self.I(talib.SMA, self.data.Close, timeperiod=self.sma1_period)
        self.sma2 = self.I(talib.SMA, self.data.Close, timeperiod=self.sma2_period)
        self.sma3 = self.I(talib.SMA, self.data.Close, timeperiod=self.sma3_period)
        self.sma4 = self.I(talib.SMA, self.data.Close, timeperiod=self.sma4_period)
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=self.rsi_period)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=self.atr_period)
        self.atr_sma = self.I(talib.SMA, self.atr, timeperiod=self.atr_sma_period)
        
        self.entry_bar = None
        self.breakeven_set = False

        print("🌙 Moon Dev: Initialized QuadrupleCrossover Strategy ✨")

    def next(self):
        current_bar = len(self.data) - 1
        entry_price = self.data.Close[-1]
        atr_val = self.atr[-1]
        rsi_val = self.rsi[-1]
        volatility_ok = self.atr[-1] > self.volatility_multiplier * self.atr_sma[-1]
        sma4_rising = self.sma4[-1] > self.sma4[-2]
        sma4_falling = self.sma4[-1] < self.sma4[-2]

        # Check for trailing exit with SMA3
        if self.position:
            if self.position.is_long and entry_price < self.sma3[-1]:
                self.position.close()
                print(f"🚀 Moon Dev: Long trailing exit on SMA3 at {entry_price} 🌙")
            elif self.position.is_short and entry_price > self.sma3[-1]:
                self.position.close()
                print(f"🚀 Moon Dev: Short trailing exit on SMA3 at {entry_price} 🌙")
            
            # Time-based exit
            if self.entry_bar is not None and current_bar - self.entry_bar > self.time_exit_bars:
                self.position.close()
                print(f"⏰ Moon Dev: Time-based exit after {self.time_exit_bars} bars 🌙")
                self.entry_bar = None
                self.breakeven_set = False
            
            # Breakeven adjustment
            if not self.breakeven_set:
                profit_threshold = atr_val * abs(self.position.size)
                if self.position.pl >= profit_threshold:
                    self.position.sl = self.position.entry_price
                    self.breakeven_set = True
                    print("✨ Moon Dev: Stop moved to breakeven! 🚀")

        # Entry logic only if no position
        if not self.position and volatility_ok:
            # Long entry
            long_crossover = self.sma1[-1] > self.sma2[-1] and self.sma1[-2] <= self.sma2[-2]
            long_alignment = (self.sma1[-1] > self.sma2[-1] > self.sma3[-1] > self.sma4[-1])
            long_rsi = rsi_val > 50
            long_trend = sma4_rising
            
            if long_crossover and long_alignment and long_rsi and long_trend:
                stop_distance = atr_val
                risk_amount = self.equity * self.risk_per_trade
                position_size = int(round(risk_amount / stop_distance))
                sl_price = entry_price - stop_distance
                tp_price = entry_price + 2 * stop_distance
                self.buy(size=position_size, sl=sl_price, tp=tp_price)
                self.entry_bar = current_bar
                self.breakeven_set = False
                print(f"🌙 Moon Dev: LONG ENTRY 🚀 Price: {entry_price}, Size: {position_size}, SL: {sl_price}, TP: {tp_price} ✨")

            # Short entry
            short_crossover = self.sma1[-1] < self.sma2[-1] and self.sma1[-2] >= self.sma2[-2]
            short_alignment = (self.sma1[-1] < self.sma2[-1] < self.sma3[-1] < self.sma4[-1])
            short_rsi = rsi_val < 50
            short_trend = sma4_falling
            
            if short_crossover and short_alignment and short_rsi and short_trend:
                stop_distance = atr_val
                risk_amount = self.equity * self.risk_per_trade
                position_size = int(round(risk_amount / stop_distance))
                sl_price = entry_price + stop_distance
                tp_price = entry_price - 2 * stop_distance
                self.sell(size=position_size, sl=sl_price, tp=tp_price)
                self.entry_bar = current_bar
                self.breakeven_set = False
                print(f"🌙 Moon Dev: SHORT ENTRY 🚀 Price: {entry_price}, Size: {position_size}, SL: {sl_price}, TP: {tp_price} ✨")

# Run backtest
bt = Backtest(data, QuadrupleCrossover, cash=1000000, commission=0.001, exclusive_orders=True, trade_on_close=True)
stats = bt.run()
print(stats)