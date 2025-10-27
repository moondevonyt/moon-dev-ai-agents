from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import talib
import pandas as pd
import numpy as np

data_path = '/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv'
data = pd.read_csv(data_path, parse_dates=['datetime'], index_col='datetime')
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data = data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
})

class SynergisticOscillator(Strategy):
    risk_per_trade = 0.01
    atr_multiplier = 1.5
    partialed = False

    def init(self):
        self.sma = self.I(talib.SMA, self.data.Close, timeperiod=50)
        self.stoch_k, self.stoch_d = self.I(talib.STOCHRSI, self.data.Close, timeperiod=14, fastk_period=14, fastd_period=3)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        self.vol_short = self.I(talib.SMA, self.data.Volume, timeperiod=5)
        self.vol_long = self.I(talib.SMA, self.data.Volume, timeperiod=34)
        self.partialed = False
        print("🌙 SynergisticOscillator initialized! ✨")

    def next(self):
        if not hasattr(self, 'partialed'):
            self.partialed = False

        close = self.data.Close
        high = self.data.High
        low = self.data.Low
        vol_osc = self.vol_short - self.vol_long
        k = self.stoch_k
        d = self.stoch_d
        sma = self.sma
        atr_val = self.atr

        # Exit conditions first
        if self.position:
            if self.position.plen >= 10:
                self.position.close()
                print("🌙 Time-based exit after 10 bars! ⏰")
                self.partialed = False
                return

            if self.position.is_long:
                # SMA exit
                if close[0] < sma[0]:
                    self.position.close()
                    print("🌙 SMA crossover exit for long! 📉")
                    self.partialed = False
                    return
                # Opposite crossover exit
                if k[0] < d[0] and k[-1] >= d[-1]:
                    self.position.close()
                    print("🌙 Opposite StochRSI crossover exit for long! 🔄")
                    self.partialed = False
                    return
                # Partial profit
                if not self.partialed and k[0] >= 80:
                    self.sell(size=self.position.size / 2)
                    self.partialed = True
                    print("✨ Partial profit taken for long at StochRSI 80! 💰")
                    return

            elif self.position.is_short:
                # SMA exit
                if close[0] > sma[0]:
                    self.position.close()
                    print("🌙 SMA crossover exit for short! 📈")
                    self.partialed = False
                    return
                # Opposite crossover exit
                if k[0] > d[0] and k[-1] <= d[-1]:
                    self.position.close()
                    print("🌙 Opposite StochRSI crossover exit for short! 🔄")
                    self.partialed = False
                    return
                # Partial profit
                if not self.partialed and k[0] <= 20:
                    self.buy(size=abs(self.position.size) / 2)
                    self.partialed = True
                    print("✨ Partial profit taken for short at StochRSI 20! 💰")
                    return

        # Entry conditions only if no position
        if not self.position:
            # Long entry
            cross_up = k[0] > d[0] and k[-1] <= d[-1]
            oversold = k[-1] < 20 and d[-1] < 20
            uptrend = close[0] > sma[0]
            vol_ok_long = vol_osc[0] > 0 or vol_osc[0] > vol_osc[-1]
            if cross_up and oversold and uptrend and vol_ok_long:
                entry_price = close[0]
                stop_dist = self.atr_multiplier * atr_val[0]
                sl_price = entry_price - stop_dist
                risk_amount = self.risk_per_trade * self.equity
                size_calc = risk_amount / stop_dist
                size = int(round(size_calc))
                if size > 0:
                    self.buy(size=size, sl=sl_price)
                    print(f"🚀 Long entry at {entry_price:.2f}, size {size}, SL {sl_price:.2f}, ATR {atr_val[0]:.2f} 🌙")
                    self.partialed = False

            # Short entry
            cross_down = k[0] < d[0] and k[-1] >= d[-1]
            overbought = k[-1] > 80 and d[-1] > 80
            downtrend = close[0] < sma[0]
            vol_ok_short = vol_osc[0] < 0 or vol_osc[0] < vol_osc[-1]
            if cross_down and overbought and downtrend and vol_ok_short:
                entry_price = close[0]
                stop_dist = self.atr_multiplier * atr_val[0]
                sl_price = entry_price + stop_dist
                risk_amount = self.risk_per_trade * self.equity
                size_calc = risk_amount / stop_dist
                size = int(round(size_calc))
                if size > 0:
                    self.sell(size=size, sl=sl_price)
                    print(f"📉 Short entry at {entry_price:.2f}, size {size}, SL {sl_price:.2f}, ATR {atr_val[0]:.2f} 🌙")
                    self.partialed = False

bt = Backtest(data, SynergisticOscillator, cash=1000000, commission=0.002, exclusive_orders=True)
stats = bt.run()
print(stats)