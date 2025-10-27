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
    adx_threshold = 20  # 🌙 Optimized: Lowered from 25 to 20 for more entry opportunities in moderate trends
    bb_squeeze_threshold = 0.05  # 🌙 Optimized: Increased from 0.04 to 0.05 for looser squeeze detection, capturing more potential breakouts
    atr_period = 14
    atr_sl_mult = 1.5  # 🌙 Optimized: Reduced from 2 to 1.5 for tighter initial stops, improving risk-reward
    trail_mult = 1.5  # 🌙 New: Trailing stop multiplier, same as SL for consistency
    rr_ratio = 3  # 🌙 Optimized: Increased from 2 to 3 for higher reward potential on winners
    risk_per_trade = 0.015  # 🌙 Optimized: Increased from 0.01 to 0.015 for slightly more aggressive sizing to boost returns
    rsi_period = 14
    rsi_long_threshold = 45  # 🌙 New: RSI filter for longs to ensure oversold reversal conditions
    rsi_short_threshold = 55  # 🌙 New: RSI filter for shorts to ensure overbought reversal conditions
    vol_sma_period = 20
    vol_mult = 1.1  # 🌙 New: Volume confirmation multiplier to filter for higher volume setups

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
        # 🌙 New: Added RSI for momentum confirmation on reversals
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=self.rsi_period)
        # 🌙 New: Added volume SMA for volume breakout filter to avoid low-quality signals
        self.vol_sma = self.I(talib.SMA, self.data.Volume, timeperiod=self.vol_sma_period)
        print("🌙 Moon Dev's Optimized ConfluentHarmonics Strategy Initialized ✨")

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
        # 🌙 New: Volume and RSI values for filters
        vol_confirm = self.data.Volume[-1] > self.vol_sma[-1] * self.vol_mult
        rsi_val = self.rsi[-1]

        # Early exits for weakening trend
        if self.position:
            if self.position.is_long and adx_val < 20:
                self.position.close()
                print(f"🌙 Early Long Exit: ADX Weakening at {self.data.index[-1]} 🚀 Price: {price}")
            elif self.position.is_short and adx_val < 20:
                self.position.close()
                print(f"🌙 Early Short Exit: ADX Weakening at {self.data.index[-1]} ✨ Price: {price}")

        # 🌙 New: Trailing stops to let winners run while protecting gains (only updates in favorable direction)
        if self.position and not self.position.sl is None:  # Ensure SL exists
            if self.position.is_long:
                trail_dist = self.trail_mult * atr_val
                new_sl = price - trail_dist
                if new_sl > self.position.sl:
                    self.position.sl = new_sl
                    print(f"🌙 Trailing SL updated to {new_sl} for long at {self.data.index[-1]} 🚀")
            elif self.position.is_short:
                trail_dist = self.trail_mult * atr_val
                new_sl = price + trail_dist
                if new_sl < self.position.sl:
                    self.position.sl = new_sl
                    print(f"🌙 Trailing SL updated to {new_sl} for short at {self.data.index[-1]} ✨")

        # Entry logic only if no position
        if not self.position:
            # Bullish Reversal Proxy: Previous close at/touching lower BB, current close above middle, ADX strong, +DI > -DI, squeeze, volume confirm, RSI oversold
            if (prev_price <= prev_lower and
                price > middle and
                adx_val > self.adx_threshold and
                pdi_val > mdi_val and
                squeeze and
                vol_confirm and
                rsi_val < self.rsi_long_threshold):
                entry = price
                risk_dist = self.atr_sl_mult * atr_val
                sl = entry - risk_dist
                size_frac = self.risk_per_trade / (risk_dist / entry)
                size_frac = min(size_frac, 1.0)
                tp = entry + (self.rr_ratio * risk_dist)
                self.buy(size=size_frac, sl=sl, tp=tp)
                print(f"🌙 Bullish ConfluentHarmonics Entry at {self.data.index[-1]} 🚀 Size Frac: {size_frac}, Entry: {entry}, SL: {sl}, TP: {tp}")

            # Bearish Reversal Proxy: Previous close at/touching upper BB, current close below middle, ADX strong, -DI > +DI, squeeze, volume confirm, RSI overbought
            elif (prev_price >= prev_upper and
                  price < middle and
                  adx_val > self.adx_threshold and
                  mdi_val > pdi_val and
                  squeeze and
                  vol_confirm and
                  rsi_val > self.rsi_short_threshold):
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