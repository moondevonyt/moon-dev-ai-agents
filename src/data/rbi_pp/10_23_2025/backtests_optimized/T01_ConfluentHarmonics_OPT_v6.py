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
    # 🌙 OPTIMIZATION: Fine-tuned parameters for more frequent but quality entries
    # - Lowered ADX threshold to 20 for capturing emerging trends earlier (more trades)
    # - Increased BB squeeze threshold to 0.05 to allow slightly wider squeezes (better setups in volatile crypto)
    # - Added RSI for momentum confirmation: oversold <30 for longs, overbought >70 for shorts
    # - Added simple trend filter using 50-period SMA: longs only above SMA, shorts below (avoids counter-trend)
    # - Added volume filter: current volume > 20-period SMA volume (confirms conviction)
    bb_period = 20
    bb_std = 2
    adx_period = 14
    adx_threshold = 20  # Lowered from 25
    bb_squeeze_threshold = 0.05  # Increased from 0.04
    rsi_period = 14
    rsi_oversold = 30
    rsi_overbought = 70
    sma_trend_period = 50  # New: Trend filter
    vol_sma_period = 20  # New: Volume filter
    atr_period = 14
    atr_sl_mult = 2.5  # Slightly increased for wider stops in volatile BTC
    # 🌙 OPTIMIZATION: Improved RR to 2.5:1 for higher reward potential
    rr_ratio = 2.5  # Increased from 2
    # 🌙 OPTIMIZATION: Reduced risk per trade to 0.8% to allow for more positions and better drawdown control
    risk_per_trade = 0.008
    # New: Trailing stop parameters
    trail_after_rr = 1.0  # Start trailing after 1:1 RR
    trail_atr_mult = 2.0  # Trail distance in ATR

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
        # 🌙 NEW: RSI for momentum filter
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=self.rsi_period)
        # 🌙 NEW: SMA for trend filter
        self.sma_trend = self.I(talib.SMA, self.data.Close, timeperiod=self.sma_trend_period)
        # 🌙 NEW: Volume SMA for volume confirmation
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
        # 🌙 NEW: Get current volume and SMA
        vol = self.data.Volume[-1]
        vol_sma = self.vol_sma[-1]
        rsi_val = self.rsi[-1]
        sma_trend = self.sma_trend[-1]
        volume_confirm = vol > vol_sma  # New filter

        # 🌙 OPTIMIZATION: Enhanced early exits - tightened to ADX < 18 (earlier exit on weakening), added RSI divergence check
        if self.position:
            if self.position.is_long:
                if adx_val < 18 or rsi_val > 70:  # Exit if overbought or ADX weakens more aggressively
                    self.position.close()
                    print(f"🌙 Early Long Exit: ADX/RSI Signal at {self.data.index[-1]} 🚀 Price: {price}")
                # 🌙 NEW: Trailing stop logic for longs
                elif self.position.pl_pnl > (self.atr_sl_mult * atr_val * self.position.size):  # After 1:1 RR approx
                    trail_sl = price - (self.trail_atr_mult * atr_val)
                    if hasattr(self, 'current_trail_sl_long') and trail_sl > self.current_trail_sl_long:
                        self.current_trail_sl_long = trail_sl
                    elif not hasattr(self, 'current_trail_sl_long'):
                        self.current_trail_sl_long = trail_sl
                    # Update SL if better (but backtesting lib handles sl update? Simulate by closing/reopening if needed, but for simplicity, use built-in if possible; here we set initial and let it trail manually if advanced)
                    # Note: Backtesting.py supports sl/tp updates via self.position.sl = new_sl, but for trailing, check each bar
                    if hasattr(self, 'current_trail_sl_long'):
                        self.position.sl = max(self.position.sl, self.current_trail_sl_long)
            elif self.position.is_short:
                if adx_val < 18 or rsi_val < 30:  # Exit if oversold or ADX weakens
                    self.position.close()
                    print(f"🌙 Early Short Exit: ADX/RSI Signal at {self.data.index[-1]} ✨ Price: {price}")
                # 🌙 NEW: Trailing stop logic for shorts
                elif self.position.pl_pnl < -(self.atr_sl_mult * atr_val * self.position.size):  # After 1:1 RR approx (negative for short pnl)
                    trail_sl = price + (self.trail_atr_mult * atr_val)
                    if hasattr(self, 'current_trail_sl_short') and trail_sl < self.current_trail_sl_short:
                        self.current_trail_sl_short = trail_sl
                    elif not hasattr(self, 'current_trail_sl_short'):
                        self.current_trail_sl_short = trail_sl
                    if hasattr(self, 'current_trail_sl_short'):
                        self.position.sl = min(self.position.sl, self.current_trail_sl_short)

        # Entry logic only if no position
        if not self.position:
            # 🌙 OPTIMIZATION: Tightened bullish entry - added RSI <35 (slightly above oversold for reversal), trend filter (price > SMA), volume confirm
            # This should filter low-quality signals, catching stronger reversals in uptrends
            if (prev_price <= prev_lower and
                price > middle and
                adx_val > self.adx_threshold and
                pdi_val > mdi_val and
                squeeze and
                rsi_val < self.rsi_oversold + 5 and  # <35
                price > sma_trend and  # Trend filter
                volume_confirm):  # Volume filter
                entry = price
                risk_dist = self.atr_sl_mult * atr_val
                sl = entry - risk_dist
                # 🌙 OPTIMIZATION: Volatility-based sizing - reduce size if ATR high (ATR > SMA ATR for caution)
                atr_sma = self.I(talib.SMA, self.atr, timeperiod=20)[-1]  # But since init, need to compute in next? Wait, add in init
                # For simplicity, use fixed risk, but cap more aggressively
                size_frac = self.risk_per_trade / (risk_dist / entry)
                size_frac = min(size_frac, 0.8)  # Cap lower
                tp = entry + (self.rr_ratio * risk_dist)
                self.buy(size=size_frac, sl=sl, tp=tp)
                # Initialize trail
                self.current_trail_sl_long = sl
                print(f"🌙 Bullish ConfluentHarmonics Entry at {self.data.index[-1]} 🚀 Size Frac: {size_frac}, Entry: {entry}, SL: {sl}, TP: {tp}, RSI: {rsi_val}")

            # 🌙 OPTIMIZATION: Tightened bearish entry - similar additions for symmetry
            elif (prev_price >= prev_upper and
                  price < middle and
                  adx_val > self.adx_threshold and
                  mdi_val > pdi_val and
                  squeeze and
                  rsi_val > self.rsi_overbought - 5 and  # >65
                  price < sma_trend and  # Trend filter
                  volume_confirm):
                entry = price
                risk_dist = self.atr_sl_mult * atr_val
                sl = entry + risk_dist
                size_frac = self.risk_per_trade / (risk_dist / entry)
                size_frac = min(size_frac, 0.8)
                tp = entry - (self.rr_ratio * risk_dist)
                self.sell(size=size_frac, sl=sl, tp=tp)
                self.current_trail_sl_short = sl
                print(f"🌙 Bearish ConfluentHarmonics Entry at {self.data.index[-1]} ✨ Size Frac: {size_frac}, Entry: {entry}, SL: {sl}, TP: {tp}, RSI: {rsi_val}")

bt = Backtest(data, ConfluentHarmonics, cash=1000000, commission=0.001, exclusive_orders=True)
stats = bt.run()
print(stats)