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
    # 🌙 Optimized Parameters: Reduced BB period for faster signals on 15m crypto, lowered ADX threshold for more entries,
    # tightened squeeze threshold slightly, increased RR for higher reward potential, reduced ATR mult for tighter stops
    bb_period = 14
    bb_std = 2
    adx_period = 10
    adx_threshold = 20
    bb_squeeze_threshold = 0.03
    atr_period = 14
    atr_sl_mult = 1.5
    rr_ratio = 3
    risk_per_trade = 0.015  # Slightly increased risk for higher returns while maintaining management

    # 🌙 New Indicators: Added EMA50 for trend filter (only long above, short below to align with regime),
    # RSI for oversold/overbought confirmation, Volume SMA for momentum filter (require above avg volume)
    ema_period = 50
    rsi_period = 14
    rsi_oversold = 40
    rsi_overbought = 60
    vol_sma_period = 20
    vol_mult = 1.2  # Volume must be 20% above SMA for entry
    trail_mult = 1.5  # Trailing stop multiplier

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
        # 🌙 Trend Filter
        self.ema50 = self.I(talib.EMA, self.data.Close, timeperiod=self.ema_period)
        # 🌙 Momentum Filters
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=self.rsi_period)
        self.vol_sma = self.I(talib.SMA, self.data.Volume, timeperiod=self.vol_sma_period)
        print("🌙 Moon Dev's Optimized ConfluentHarmonics Strategy Initialized: Added trend, RSI, volume filters & trailing stops ✨")

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
        ema50_val = self.ema50[-1]
        rsi_val = self.rsi[-1]
        vol_sma_val = self.vol_sma[-1]
        bb_width = (upper - lower) / middle
        prev_bb_width = (prev_upper - prev_lower) / self.bb_middle[-2]
        squeeze = bb_width < self.bb_squeeze_threshold or prev_bb_width < self.bb_squeeze_threshold
        vol_filter = self.data.Volume[-1] > vol_sma_val * self.vol_mult

        # 🌙 Enhanced Exits: Early exit on weakening ADX, plus dynamic trailing stop to capture more profits
        if self.position:
            if self.position.is_long:
                if adx_val < 20:
                    self.position.close()
                    print(f"🌙 Early Long Exit: ADX Weakening at {self.data.index[-1]} 🚀 Price: {price}")
                else:
                    # 🌙 Trailing Stop for Longs
                    trail_sl = price - (atr_val * self.trail_mult)
                    if trail_sl > self.position.sl:
                        self.position.sl = trail_sl
                        print(f"🌙 Trailing SL Updated Long at {self.data.index[-1]} 🌙 New SL: {trail_sl}")
            elif self.position.is_short:
                if adx_val < 20:
                    self.position.close()
                    print(f"🌙 Early Short Exit: ADX Weakening at {self.data.index[-1]} ✨ Price: {price}")
                else:
                    # 🌙 Trailing Stop for Shorts
                    trail_sl = price + (atr_val * self.trail_mult)
                    if trail_sl < self.position.sl:
                        self.position.sl = trail_sl
                        print(f"🌙 Trailing SL Updated Short at {self.data.index[-1]} 🌙 New SL: {trail_sl}")

        # 🌙 Entry Logic: Added trend filter (EMA50), RSI oversold/overbought, and volume confirmation for higher quality setups
        if not self.position:
            # Bullish Reversal: Previous close at/touching lower BB, current close above middle, ADX strong, +DI > -DI, squeeze, trend up, RSI oversold, volume spike
            if (prev_price <= prev_lower and
                price > middle and
                adx_val > self.adx_threshold and
                pdi_val > mdi_val and
                squeeze and
                price > ema50_val and  # 🌙 Trend filter: Only long in uptrend
                rsi_val < self.rsi_oversold and  # 🌙 Oversold confirmation
                vol_filter):  # 🌙 Volume momentum
                entry = price
                risk_dist = self.atr_sl_mult * atr_val
                sl = entry - risk_dist
                size_frac = self.risk_per_trade / (risk_dist / entry)
                size_frac = min(size_frac, 1.0)
                tp = entry + (self.rr_ratio * risk_dist)
                self.buy(size=size_frac, sl=sl, tp=tp)
                print(f"🌙 Bullish ConfluentHarmonics Entry at {self.data.index[-1]} 🚀 Size Frac: {size_frac}, Entry: {entry}, SL: {sl}, TP: {tp}, RSI: {rsi_val}, Vol Filter: {vol_filter}")

            # Bearish Reversal: Previous close at/touching upper BB, current close below middle, ADX strong, -DI > +DI, squeeze, trend down, RSI overbought, volume spike
            elif (prev_price >= prev_upper and
                  price < middle and
                  adx_val > self.adx_threshold and
                  mdi_val > pdi_val and
                  squeeze and
                  price < ema50_val and  # 🌙 Trend filter: Only short in downtrend
                  rsi_val > self.rsi_overbought and  # 🌙 Overbought confirmation
                  vol_filter):  # 🌙 Volume momentum
                entry = price
                risk_dist = self.atr_sl_mult * atr_val
                sl = entry + risk_dist
                size_frac = self.risk_per_trade / (risk_dist / entry)
                size_frac = min(size_frac, 1.0)
                tp = entry - (self.rr_ratio * risk_dist)
                self.sell(size=size_frac, sl=sl, tp=tp)
                print(f"🌙 Bearish ConfluentHarmonics Entry at {self.data.index[-1]} ✨ Size Frac: {size_frac}, Entry: {entry}, SL: {sl}, TP: {tp}, RSI: {rsi_val}, Vol Filter: {vol_filter}")

bt = Backtest(data, ConfluentHarmonics, cash=1000000, commission=0.001, exclusive_orders=True)
stats = bt.run()
print(stats)