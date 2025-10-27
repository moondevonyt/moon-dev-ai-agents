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
    bb_period = 21  # 🌙 Optimized: Slightly longer BB period for smoother bands and fewer false signals
    bb_std = 2.0
    adx_period = 14
    adx_threshold = 30  # 🌙 Optimized: Higher ADX threshold for stronger trend confirmation, reducing whipsaws
    bb_squeeze_threshold = 0.03  # 🌙 Optimized: Tighter squeeze threshold to catch more pronounced contractions
    atr_period = 14
    atr_sl_mult = 2.0
    rr_ratio = 3  # 🌙 Optimized: Increased RR ratio to 3:1 for higher reward potential while maintaining risk control
    risk_per_trade = 0.015  # 🌙 Optimized: Slightly higher risk per trade (1.5%) to accelerate returns without excessive drawdown
    ema_fast = 50  # New parameter for fast EMA trend filter
    ema_slow = 200  # New parameter for slow EMA trend filter
    rsi_period = 14  # New parameter for RSI momentum filter
    rsi_long_threshold = 30  # Avoid deeply oversold entries
    rsi_short_threshold = 70  # Avoid deeply overbought entries
    vol_mult = 1.5  # Volume confirmation multiplier

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
        
        # 🌙 New: Added EMA trend filter to only trade in the direction of the prevailing trend (avoids counter-trend traps)
        self.ema_fast = self.I(talib.EMA, self.data.Close, timeperiod=self.ema_fast)
        self.ema_slow = self.I(talib.EMA, self.data.Close, timeperiod=self.ema_slow)
        
        # 🌙 New: Added RSI for momentum confirmation to filter out low-momentum reversals
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=self.rsi_period)
        
        # 🌙 New: Added volume SMA filter to ensure entries on above-average volume (confirms conviction)
        self.vol_sma = self.I(talib.SMA, self.data.Volume, timeperiod=self.bb_period)
        
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
        squeeze = bb_width < self.bb_squeeze_threshold  # 🌙 Optimized: Use only current bb_width for squeeze to focus on active contractions

        # 🌙 Optimized: Tightened early exit threshold to ADX < 25 for quicker response to trend weakening
        if self.position:
            if self.position.is_long and adx_val < 25:
                self.position.close()
                print(f"🌙 Early Long Exit: ADX Weakening at {self.data.index[-1]} 🚀 Price: {price}")
            elif self.position.is_short and adx_val < 25:
                self.position.close()
                print(f"🌙 Early Short Exit: ADX Weakening at {self.data.index[-1]} ✨ Price: {price}")

        # Entry logic only if no position
        if not self.position:
            # 🌙 Optimized Bullish Entry: Added trend filter (price > EMA50 > EMA200), RSI > 30 (momentum), and volume > 1.5x SMA for higher-quality setups
            if (prev_price <= prev_lower and
                price > middle and
                adx_val > self.adx_threshold and
                pdi_val > mdi_val and
                squeeze and
                price > self.ema_fast[-1] and self.ema_fast[-1] > self.ema_slow[-1] and  # Trend filter
                self.rsi[-1] > self.rsi_long_threshold and  # Momentum filter
                self.data.Volume[-1] > self.vol_mult * self.vol_sma[-1]):  # Volume filter
                entry = price
                risk_dist = self.atr_sl_mult * atr_val
                sl = entry - risk_dist
                size_frac = self.risk_per_trade / (risk_dist / entry)
                size_frac = min(size_frac, 1.0)
                tp = entry + (self.rr_ratio * risk_dist)
                self.buy(size=size_frac, sl=sl, tp=tp)
                print(f"🌙 Bullish ConfluentHarmonics Entry at {self.data.index[-1]} 🚀 Size Frac: {size_frac}, Entry: {entry}, SL: {sl}, TP: {tp}")

            # 🌙 Optimized Bearish Entry: Added trend filter (price < EMA50 < EMA200), RSI < 70 (momentum), and volume > 1.5x SMA for higher-quality setups
            elif (prev_price >= prev_upper and
                  price < middle and
                  adx_val > self.adx_threshold and
                  mdi_val > pdi_val and
                  squeeze and
                  price < self.ema_fast[-1] and self.ema_fast[-1] < self.ema_slow[-1] and  # Trend filter
                  self.rsi[-1] < self.rsi_short_threshold and  # Momentum filter
                  self.data.Volume[-1] > self.vol_mult * self.vol_sma[-1]):  # Volume filter
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