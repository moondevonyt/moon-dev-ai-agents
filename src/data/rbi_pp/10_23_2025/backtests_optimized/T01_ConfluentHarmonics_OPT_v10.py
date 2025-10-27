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
    adx_threshold = 20  # 🌙 Lowered from 25 to 20 for more trade opportunities while still filtering weak trends
    bb_squeeze_threshold = 0.05  # 🌙 Loosened from 0.04 to 0.05 to capture more squeeze setups without overtrading
    atr_period = 14
    atr_sl_mult = 2
    rr_ratio = 3  # 🌙 Increased from 2 to 3 for higher reward potential per trade, improving return asymmetry
    risk_per_trade = 0.015  # 🌙 Increased from 0.01 to 0.015 for slightly larger position exposure to accelerate returns, still conservative

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
        # 🌙 Added EMA200 for trend filter to align trades with broader market direction, reducing counter-trend losses
        self.ema200 = self.I(talib.EMA, self.data.Close, timeperiod=200)
        # 🌙 Added RSI for momentum confirmation to filter overbought/oversold reversals, improving entry quality
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14)
        # 🌙 Added volume SMA for volume confirmation to ensure entries on above-average volume, avoiding low-conviction moves
        self.vol_sma = self.I(talib.SMA, self.data.Volume, timeperiod=20)
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
        rsi_val = self.rsi[-1]
        atr_val = self.atr[-1]
        ema200_val = self.ema200[-1]
        vol_sma_val = self.vol_sma[-1]
        bb_width = (upper - lower) / middle
        prev_bb_width = (prev_upper - prev_lower) / self.bb_middle[-2]
        squeeze = bb_width < self.bb_squeeze_threshold or prev_bb_width < self.bb_squeeze_threshold
        vol_confirm = self.data.Volume[-1] > vol_sma_val * 1.2  # 🌙 Volume filter: require 20% above 20-period average for conviction
        trend_long = price > ema200_val  # 🌙 Trend filter for longs: only trade above 200 EMA
        trend_short = price < ema200_val  # 🌙 Trend filter for shorts: only trade below 200 EMA

        # 🌙 Trailing stop logic for better profit capture: update SL to current price +/- ATR multiple if it improves the stop
        if self.position:
            if self.position.is_long:
                trail_sl = price - (self.atr_sl_mult * atr_val)
                if trail_sl > self.position.sl:
                    self.position.sl = trail_sl
                    print(f"🌙 Trailing Long SL updated to {trail_sl} at {self.data.index[-1]} 🚀")
            elif self.position.is_short:
                trail_sl = price + (self.atr_sl_mult * atr_val)
                if trail_sl < self.position.sl:
                    self.position.sl = trail_sl
                    print(f"🌙 Trailing Short SL updated to {trail_sl} at {self.data.index[-1]} ✨")

            # Early exits for weakening trend - adjusted threshold
            if self.position.is_long and adx_val < 18:  # 🌙 Raised early exit threshold from 20 to 18 to allow more trend breathing room
                self.position.close()
                print(f"🌙 Early Long Exit: ADX Weakening at {self.data.index[-1]} 🚀 Price: {price}")
            elif self.position.is_short and adx_val < 18:
                self.position.close()
                print(f"🌙 Early Short Exit: ADX Weakening at {self.data.index[-1]} ✨ Price: {price}")

        # Entry logic only if no position
        if not self.position:
            # Bullish Reversal Proxy: Previous close at/touching lower BB, current close above middle, ADX strong, +DI > -DI, squeeze, plus new filters
            if (prev_price <= prev_lower and
                price > middle and
                adx_val > self.adx_threshold and
                pdi_val > mdi_val and
                squeeze and
                rsi_val < 35 and  # 🌙 RSI filter: oversold for better reversal setups
                vol_confirm and
                trend_long):
                entry = price
                risk_dist = self.atr_sl_mult * atr_val
                sl = entry - risk_dist
                size_frac = self.risk_per_trade / (risk_dist / entry)
                size_frac = min(size_frac, 1.0)
                tp = entry + (self.rr_ratio * risk_dist)
                self.buy(size=size_frac, sl=sl, tp=tp)
                print(f"🌙 Bullish ConfluentHarmonics Entry at {self.data.index[-1]} 🚀 Size Frac: {size_frac}, Entry: {entry}, SL: {sl}, TP: {tp}")

            # Bearish Reversal Proxy: Previous close at/touching upper BB, current close below middle, ADX strong, -DI > +DI, squeeze, plus new filters
            elif (prev_price >= prev_upper and
                  price < middle and
                  adx_val > self.adx_threshold and
                  mdi_val > pdi_val and
                  squeeze and
                  rsi_val > 65 and  # 🌙 RSI filter: overbought for better reversal setups
                  vol_confirm and
                  trend_short):
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