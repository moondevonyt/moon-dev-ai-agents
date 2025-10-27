import pandas as pd
import talib
from backtesting import Backtest, Strategy

path = '/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv'
data = pd.read_csv(path)
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data = data.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'})
data = data.set_index(pd.to_datetime(data['datetime']))

class ConfluentHarmonics(Strategy):
    bb_period = 20
    bb_std = 2
    adx_period = 14
    adx_threshold = 25
    bb_squeeze_threshold = 0.04
    atr_period = 14
    atr_sl_mult = 2
    rr_ratio = 2
    risk_per_trade = 0.01

    def init(self):
        self.closes = self.I(lambda c: c, self.data.Close)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=self.atr_period)
        bb_upper, bb_middle, bb_lower = self.I(talib.BBANDS, self.data.Close, timeperiod=self.bb_period, nbdevup=self.bb_std, nbdevdn=self.bb_std, matype=0)
        self.bb_upper = bb_upper
        self.bb_middle = bb_middle
        self.bb_lower = bb_lower
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=self.adx_period)
        self.pdi = self.I(talib.PLUS_DI, self.data.High, self.data.Low, self.data.Close, timeperiod=self.adx_period)
        self.mdi = self.I(talib.MINUS_DI, self.data.High, self.data.Low, self.data.Close, timeperiod=self.adx_period)
        print("🌙 Moon Dev's ConfluentHarmonics Strategy Initialized ✨")

    def next(self):
        price = self.closes[-1]
        prev_price = self.closes[-2]
        upper = self.bb_upper[-1]
        middle = self.bb_middle[-1]
        lower = self.bb_lower[-1]
        prev_lower = self.bb_lower[-2]
        prev_upper = self.bb_upper[-2]
        adx_val = self.adx[-1]
        pdi_val = self.pdi[-1]
        mdi_val = self.mdi[-1]
        atr_val = self.atr[-1]
        bb_width = (upper - lower) / middle
        prev_bb_width = (prev_upper - prev_lower) / self.bb_middle[-2]
        squeeze = bb_width < self.bb_squeeze_threshold or prev_bb_width < self.bb_squeeze_threshold

        # Early exits for weakening trend
        if self.position:
            if self.position.is_long and adx_val < 20:
                self.position.close()
                print(f"🌙 Early Long Exit: ADX Weakening at {self.data.index[-1]} 🚀 Price: {price}")
            elif self.position.is_short and adx_val < 20:
                self.position.close()
                print(f"🌙 Early Short Exit: ADX Weakening at {self.data.index[-1]} ✨ Price: {price}")

        # Entry logic only if no position
        if not self.position:
            # Bullish Reversal Proxy: Previous close at/touching lower BB, current close above middle, ADX strong, +DI > -DI, squeeze
            if (prev_price <= prev_lower and
                price > middle and
                adx_val > self.adx_threshold and
                pdi_val > mdi_val and
                squeeze):
                entry = price
                sl = entry - (self.atr_sl_mult * atr_val)
                risk_dist = entry - sl
                size = (self.equity * self.risk_per_trade) / risk_dist
                size = int(round(size))
                tp = entry + (self.rr_ratio * risk_dist)
                self.buy(size=size, sl=sl, tp=tp)
                print(f"🌙 Bullish ConfluentHarmonics Entry at {self.data.index[-1]} 🚀 Size: {size}, Entry: {entry}, SL: {sl}, TP: {tp}")

            # Bearish Reversal Proxy: Previous close at/touching upper BB, current close below middle, ADX strong, -DI > +DI, squeeze
            elif (prev_price >= prev_upper and
                  price < middle and
                  adx_val > self.adx_threshold and
                  mdi_val > pdi_val and
                  squeeze):
                entry = price
                sl = entry + (self.atr_sl_mult * atr_val)
                risk_dist = sl - entry
                size = (self.equity * self.risk_per_trade) / risk_dist
                size = int(round(size))
                tp = entry - (self.rr_ratio * risk_dist)
                self.sell(size=size, sl=sl, tp=tp)
                print(f"🌙 Bearish ConfluentHarmonics Entry at {self.data.index[-1]} ✨ Size: {size}, Entry: {entry}, SL: {sl}, TP: {tp}")

bt = Backtest(data, ConfluentHarmonics, cash=1000000, commission=0.001, exclusive_orders=True)
stats = bt.run()
print(stats)