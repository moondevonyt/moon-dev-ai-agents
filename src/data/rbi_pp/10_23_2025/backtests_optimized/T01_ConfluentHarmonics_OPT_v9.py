import pandas as pd
import talib
from backtesting import Backtest, Strategy

path = '/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv'
data = pd.read_csv(path)
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data = data.rename(columns={'datetime': 'Datetime', 'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'})
data = data.set_index(pd.to_datetime(data['Datetime']))

class ConfluentHarmonics(Strategy):
    bb_period = 20
    bb_std = 2
    adx_period = 14
    adx_threshold = 20  # 🌙 Lowered from 25 to 20 for more entry opportunities while still filtering weak trends
    bb_squeeze_threshold = 0.1  # 🌙 Increased from 0.04 to 0.1 to capture more squeeze setups without being too loose
    atr_period = 14
    atr_sl_mult = 2
    rr_ratio = 3  # 🌙 Increased from 2 to 3 for higher reward potential per trade, improving overall returns
    risk_per_trade = 0.015  # 🌙 Slightly increased from 0.01 to 0.015 to allow larger positions for better compounding towards 50% target

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
        # 🌙 Added RSI for overbought/oversold confirmation to filter low-quality reversals
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14)
        # 🌙 Added volume SMA for momentum confirmation to ensure entries on volume spikes
        self.avg_vol = self.I(talib.SMA, self.data.Volume, timeperiod=20)
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
        # 🌙 Added RSI and volume checks for current bar
        rsi_prev = self.rsi[-2] if len(self.rsi) > 1 else 50
        vol_current = self.data.Volume[-1]
        avg_vol_current = self.avg_vol[-1]
        vol_confirmation = vol_current > 1.5 * avg_vol_current  # 🌙 Volume spike filter to avoid low-conviction entries

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
            # Bullish Reversal Proxy: Previous close at/touching lower BB, current close above middle, ADX strong, +DI > -DI, squeeze, RSI oversold prev, volume spike
            if (prev_price <= prev_lower and
                price > middle and
                adx_val > self.adx_threshold and
                pdi_val > mdi_val and
                squeeze and
                rsi_prev < 30 and  # 🌙 RSI filter for oversold condition on previous bar
                vol_confirmation):  # 🌙 Volume confirmation
                entry = price
                risk_dist = self.atr_sl_mult * atr_val
                sl = entry - risk_dist
                size_frac = self.risk_per_trade / (risk_dist / entry)
                size_frac = min(size_frac, 1.0)
                tp = entry + (self.rr_ratio * risk_dist)
                self.buy(size=size_frac, sl=sl, tp=tp)
                print(f"🌙 Bullish ConfluentHarmonics Entry at {self.data.index[-1]} 🚀 Size Frac: {size_frac}, Entry: {entry}, SL: {sl}, TP: {tp}")

            # Bearish Reversal Proxy: Previous close at/touching upper BB, current close below middle, ADX strong, -DI > +DI, squeeze, RSI overbought prev, volume spike
            elif (prev_price >= prev_upper and
                  price < middle and
                  adx_val > self.adx_threshold and
                  mdi_val > pdi_val and
                  squeeze and
                  rsi_prev > 70 and  # 🌙 RSI filter for overbought condition on previous bar
                  vol_confirmation):  # 🌙 Volume confirmation
                entry = price
                risk_dist = self.atr_sl_mult * atr_val
                sl = entry + risk_dist
                size_frac = self.risk_per_trade / (risk_dist / entry)
                size_frac = min(size_frac, 1.0)
                tp = entry - (self.rr_ratio * risk_dist)
                self.sell(size=size_frac, sl=sl, tp=tp)
                print(f"🌙 Bearish ConfluentHarmonics Entry at {self.data.index[-1]} ✨ Size Frac: {size_frac}, Entry: {entry}, SL: {sl}, TP: {tp}")

bt = Backtest(data, ConfluentHarmonics, cash=1000000, commission=0.001, exclusive_orders=True)
stats = bt.run()
print(stats)