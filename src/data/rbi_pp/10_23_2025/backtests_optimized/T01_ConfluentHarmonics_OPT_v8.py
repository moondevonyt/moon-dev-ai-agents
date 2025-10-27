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
    adx_threshold = 20  # 🌙 OPTIMIZATION: Lowered from 25 to 20 to capture more trending opportunities without excessive noise
    bb_squeeze_threshold = 0.03  # 🌙 OPTIMIZATION: Tightened from 0.04 to 0.03 for higher-quality squeeze setups
    atr_period = 14
    atr_sl_mult = 1.5  # 🌙 OPTIMIZATION: Reduced from 2 to 1.5 for tighter stops, improving risk-reward while allowing more room than 1x ATR
    rr_ratio = 3  # 🌙 OPTIMIZATION: Increased from 2 to 3 for higher reward potential per trade, targeting better returns
    risk_per_trade = 0.015  # 🌙 OPTIMIZATION: Increased from 0.01 to 0.015 (1.5%) to amplify returns while keeping risk controlled
    rsi_period = 14
    rsi_oversold = 40  # 🌙 NEW: RSI threshold for oversold confirmation in bullish setups
    rsi_overbought = 60  # 🌙 NEW: RSI threshold for overbought confirmation in bearish setups
    vol_ma_period = 20  # 🌙 NEW: Volume moving average period for confirmation filter
    ema_trend_period = 200  # 🌙 NEW: EMA for trend filter to avoid counter-trend trades in weak regimes
    early_exit_adx = 15  # 🌙 OPTIMIZATION: Lowered early exit threshold from 20 to 15 to hold winners longer in mildly weakening trends

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
        # 🌙 NEW: RSI indicator for momentum confirmation to filter low-quality reversals
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=self.rsi_period)
        # 🌙 NEW: Volume MA for confirmation that entries occur on above-average volume (avoids low-conviction moves)
        self.vol_ma = self.I(talib.SMA, self.data.Volume, timeperiod=self.vol_ma_period)
        # 🌙 NEW: EMA trend filter to ensure trades align with higher-timeframe trend (reduces whipsaws in ranging markets)
        self.ema_trend = self.I(talib.EMA, self.data.Close, timeperiod=self.ema_trend_period)
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
        rsi_val = self.rsi[-1]
        vol_val = self.data.Volume[-1]
        vol_ma_val = self.vol_ma[-1]
        ema_val = self.ema_trend[-1]
        bb_width = (upper - lower) / middle
        prev_bb_width = (prev_upper - prev_lower) / self.bb_middle[-2]
        squeeze = bb_width < self.bb_squeeze_threshold or prev_bb_width < self.bb_squeeze_threshold
        vol_confirm = vol_val > vol_ma_val  # 🌙 NEW: Volume filter for stronger entry conviction
        trend_long = price > ema_val  # 🌙 NEW: Bullish trend filter
        trend_short = price < ema_val  # 🌙 NEW: Bearish trend filter

        # Early exits for weakening trend (optimized threshold)
        if self.position:
            if self.position.is_long and adx_val < self.early_exit_adx:
                self.position.close()
                print(f"🌙 Early Long Exit: ADX Weakening at {self.data.index[-1]} 🚀 Price: {price}")
            elif self.position.is_short and adx_val < self.early_exit_adx:
                self.position.close()
                print(f"🌙 Early Short Exit: ADX Weakening at {self.data.index[-1]} ✨ Price: {price}")

        # Entry logic only if no position
        if not self.position:
            # Bullish Reversal Proxy: Previous close at/touching lower BB, current close above middle, ADX strong, +DI > -DI, squeeze, RSI oversold, volume confirm, trend filter
            if (prev_price <= prev_lower and
                price > middle and
                adx_val > self.adx_threshold and
                pdi_val > mdi_val and
                squeeze and
                rsi_val < self.rsi_oversold and  # 🌙 NEW: RSI filter for oversold confirmation
                vol_confirm and  # 🌙 NEW: Volume filter
                trend_long):  # 🌙 NEW: Trend alignment filter
                entry = price
                risk_dist = self.atr_sl_mult * atr_val
                sl = entry - risk_dist
                size_frac = self.risk_per_trade / (risk_dist / entry)
                size_frac = min(size_frac, 1.0)
                tp = entry + (self.rr_ratio * risk_dist)
                self.buy(size=size_frac, sl=sl, tp=tp)
                print(f"🌙 Bullish ConfluentHarmonics Entry at {self.data.index[-1]} 🚀 Size Frac: {size_frac}, Entry: {entry}, SL: {sl}, TP: {tp}")

            # Bearish Reversal Proxy: Previous close at/touching upper BB, current close below middle, ADX strong, -DI > +DI, squeeze, RSI overbought, volume confirm, trend filter
            elif (prev_price >= prev_upper and
                  price < middle and
                  adx_val > self.adx_threshold and
                  mdi_val > pdi_val and
                  squeeze and
                  rsi_val > self.rsi_overbought and  # 🌙 NEW: RSI filter for overbought confirmation
                  vol_confirm and  # 🌙 NEW: Volume filter
                  trend_short):  # 🌙 NEW: Trend alignment filter
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