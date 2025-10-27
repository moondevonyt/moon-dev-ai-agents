from backtesting import Backtest, Strategy
import talib
import pandas as pd
import numpy as np

data_path = '/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv'
data = pd.read_csv(data_path, parse_dates=['datetime'])
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

class SynergisticOscillator(Strategy):
    risk_per_trade = 0.01
    atr_multiplier = 2.0  # 🌙 Increased ATR multiplier for wider stops to reduce whipsaws and improve risk tolerance ✨
    partialed = False
    pos_bars = 0

    def init(self):
        # 🌙 Switched to EMA(20) from SMA(50) for a faster, more responsive trend filter to catch trends earlier without lagging too much ✨
        self.ema = self.I(talib.EMA, self.data.Close, timeperiod=20)
        # 🌙 Adjusted STOCHRSI fastk_period to 5 (standard for %K on RSI) from 14 for smoother, more timely signals and better entry timing ✨
        self.stoch_k, self.stoch_d = self.I(talib.STOCHRSI, self.data.Close, timeperiod=14, fastk_period=5, fastd_period=3)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        self.vol_short = self.I(talib.SMA, self.data.Volume, timeperiod=5)
        self.vol_long = self.I(talib.SMA, self.data.Volume, timeperiod=34)
        self.partialed = False
        self.pos_bars = 0
        print("🌙 SynergisticOscillator initialized! ✨")

    def next(self):
        if self.position:
            if self.pos_bars == 0:
                self.pos_bars = 1
            else:
                self.pos_bars += 1

        close = self.data.Close
        high = self.data.High
        low = self.data.Low
        # 🌙 Simplified volume oscillator calculation but used directly in filters below ✨
        k = self.stoch_k
        d = self.stoch_d
        ema = self.ema  # 🌙 Using EMA for trend now ✨
        atr_val = self.atr

        # Exit conditions first
        if self.position:
            # 🌙 Extended time-based exit to 20 bars to allow more room for profitable moves while preventing indefinite holds ✨
            if self.pos_bars >= 20:
                self.position.close()
                print("🌙 Time-based exit after 20 bars! ⏰")
                self.partialed = False
                self.pos_bars = 0
                return

            if self.position.is_long:
                # EMA exit (updated from SMA)
                if close[-1] < ema[-1]:
                    self.position.close()
                    print("🌙 EMA crossover exit for long! 📉")
                    self.partialed = False
                    self.pos_bars = 0
                    return
                # Opposite crossover exit
                if k[-1] < d[-1] and k[-2] >= d[-2]:
                    self.position.close()
                    print("🌙 Opposite StochRSI crossover exit for long! 🔄")
                    self.partialed = False
                    self.pos_bars = 0
                    return
                # Partial profit
                if not self.partialed and k[-1] >= 80:
                    size_to_close = int(round(self.position.size / 2))
                    if size_to_close > 0:
                        self.sell(size=size_to_close)
                        self.partialed = True
                        print("✨ Partial profit taken for long at StochRSI 80! 💰")
                    return

            elif self.position.is_short:
                # EMA exit (updated from SMA)
                if close[-1] > ema[-1]:
                    self.position.close()
                    print("🌙 EMA crossover exit for short! 📈")
                    self.partialed = False
                    self.pos_bars = 0
                    return
                # Opposite crossover exit
                if k[-1] > d[-1] and k[-2] <= d[-2]:
                    self.position.close()
                    print("🌙 Opposite StochRSI crossover exit for short! 🔄")
                    self.partialed = False
                    self.pos_bars = 0
                    return
                # Partial profit
                if not self.partialed and k[-1] <= 20:
                    size_to_close = int(round(abs(self.position.size) / 2))
                    if size_to_close > 0:
                        self.buy(size=size_to_close)
                        self.partialed = True
                        print("✨ Partial profit taken for short at StochRSI 20! 💰")
                    return

        # Entry conditions only if no position
        if not self.position:
            # 🌙 Tightened oversold/overbought thresholds to 25/75 from 20/80 for more balanced entries without being too restrictive, improving signal quality ✨
            # Long entry
            cross_up = k[-1] > d[-1] and k[-2] <= d[-2]
            oversold = k[-1] < 25 and d[-1] < 25
            uptrend = close[-1] > ema[-1]  # 🌙 Updated to EMA ✨
            # 🌙 Tightened volume filter to require short-term volume > long-term volume (above average) for both directions to confirm momentum and avoid low-volume traps ✨
            vol_ok_long = self.vol_short[-1] > self.vol_long[-1]
            if cross_up and oversold and uptrend and vol_ok_long:
                entry_price = close[-1]
                stop_dist = self.atr_multiplier * atr_val[-1]
                # 🌙 Added fixed take-profit at 2x risk distance for a 1:2 risk-reward ratio to capture profits systematically and boost returns ✨
                tp_price = entry_price + (2 * stop_dist)
                sl_price = entry_price - stop_dist
                risk_amount = self.risk_per_trade * self.equity
                size_calc = risk_amount / stop_dist
                size = int(round(size_calc))
                if size > 0:
                    self.buy(size=size, sl=sl_price, tp=tp_price)
                    print(f"🚀 Long entry at {entry_price:.2f}, size {size}, SL {sl_price:.2f}, TP {tp_price:.2f}, ATR {atr_val[-1]:.2f} 🌙")
                    self.partialed = False
                    self.pos_bars = 0

            # Short entry
            cross_down = k[-1] < d[-1] and k[-2] >= d[-2]
            overbought = k[-1] > 75 and d[-1] > 75
            downtrend = close[-1] < ema[-1]  # 🌙 Updated to EMA ✨
            vol_ok_short = self.vol_short[-1] > self.vol_long[-1]  # 🌙 Same tightened volume filter for shorts to ensure momentum ✨
            if cross_down and overbought and downtrend and vol_ok_short:
                entry_price = close[-1]
                stop_dist = self.atr_multiplier * atr_val[-1]
                # 🌙 Added fixed take-profit at 2x risk distance for shorts ✨
                tp_price = entry_price - (2 * stop_dist)
                sl_price = entry_price + stop_dist
                risk_amount = self.risk_per_trade * self.equity
                size_calc = risk_amount / stop_dist
                size = int(round(size_calc))
                if size > 0:
                    self.sell(size=size, sl=sl_price, tp=tp_price)
                    print(f"📉 Short entry at {entry_price:.2f}, size {size}, SL {sl_price:.2f}, TP {tp_price:.2f}, ATR {atr_val[-1]:.2f} 🌙")
                    self.partialed = False
                    self.pos_bars = 0

bt = Backtest(data, SynergisticOscillator, cash=1000000, commission=0.002, exclusive_orders=True)
stats = bt.run()
print(stats)