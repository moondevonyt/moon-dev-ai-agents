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
    adx_threshold = 20  # 🌙 Optimized: Lowered from 25 to 20 for more trend-confirming entries without excessive noise
    bb_squeeze_threshold = 0.03  # 🌙 Optimized: Tightened from 0.04 to 0.03 for stricter squeeze detection, focusing on higher-quality compressions
    atr_period = 14
    atr_sl_mult = 1.5  # 🌙 Optimized: Reduced from 2 to 1.5 for tighter stop losses, improving risk-reward by reducing risk distance
    rr_ratio = 3  # 🌙 Optimized: Increased from 2 to 3 for higher reward potential per trade, aiming for better overall returns
    risk_per_trade = 0.02  # 🌙 Optimized: Increased from 0.01 to 0.02 to scale position sizes moderately, boosting returns while keeping risk controlled

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
        # 🌙 New: Added RSI for oversold/overbought confirmation on reversals, filtering low-quality signals
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14)
        # 🌙 New: Added volume SMA for confirmation of conviction on entry bars
        self.vol_sma = self.I(talib.SMA, self.data.Volume, timeperiod=20)
        # 🌙 New: Added EMA200 as a trend filter to ensure reversals align with the broader market regime (longs above, shorts below)
        self.ema200 = self.I(talib.EMA, self.data.Close, timeperiod=200)
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
        squeeze = bb_width < self.bb_squeeze_threshold or prev_bb_width < self.bb_squeeze_threshold  # 🌙 Kept logic but with tighter threshold for better setups
        rsi_val = self.rsi[-1]
        vol_val = self.data.Volume[-1]
        vol_avg = self.vol_sma[-1]
        ema200_val = self.ema200[-1]

        # Early exits for weakening trend (unchanged, as it aids risk management)
        if self.position:
            if self.position.is_long and adx_val < 20:
                self.position.close()
                print(f"🌙 Early Long Exit: ADX Weakening at {self.data.index[-1]} 🚀 Price: {price}")
            elif self.position.is_short and adx_val < 20:
                self.position.close()
                print(f"🌙 Early Short Exit: ADX Weakening at {self.data.index[-1]} ✨ Price: {price}")

        # Entry logic only if no position
        if not self.position:
            # 🌙 Optimized Bullish: Added RSI <30 (oversold), volume > avg (conviction), price > EMA200 (uptrend regime filter)
            if (prev_price <= prev_lower and
                price > middle and
                adx_val > self.adx_threshold and
                pdi_val > mdi_val and
                squeeze and
                rsi_val < 30 and
                vol_val > vol_avg and
                price > ema200_val):
                entry = price
                risk_dist = self.atr_sl_mult * atr_val
                sl = entry - risk_dist
                size_frac = self.risk_per_trade / (risk_dist / entry)
                size_frac = min(size_frac, 1.0)
                tp = entry + (self.rr_ratio * risk_dist)
                self.buy(size=size_frac, sl=sl, tp=tp)
                print(f"🌙 Bullish ConfluentHarmonics Entry at {self.data.index[-1]} 🚀 Size Frac: {size_frac}, Entry: {entry}, SL: {sl}, TP: {tp}")

            # 🌙 Optimized Bearish: Added RSI >70 (overbought), volume > avg (conviction), price < EMA200 (downtrend regime filter)
            elif (prev_price >= prev_upper and
                  price < middle and
                  adx_val > self.adx_threshold and
                  mdi_val > pdi_val and
                  squeeze and
                  rsi_val > 70 and
                  vol_val > vol_avg and
                  price < ema200_val):
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