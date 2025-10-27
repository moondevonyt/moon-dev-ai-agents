import pandas as pd
import talib
import numpy as np
from backtesting import Backtest, Strategy
from datetime import datetime

# Load and clean data
path = '/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv'
data = pd.read_csv(path, parse_dates=True, index_col=0)
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
data = data[['Open', 'High', 'Low', 'Close', 'Volume']]

class AdaptiveReversion(Strategy):
    bb_period = 20
    bb_std = 2.0
    rsi_period = 14
    rsi_overbought = 75  # 🌙 Moon Dev: Tightened to 75 for stronger overbought signals, reducing false entries
    rsi_oversold = 25    # 🌙 Moon Dev: Tightened to 25 for stronger oversold signals, improving entry quality
    atr_period = 14
    atr_mult = 2.0       # 🌙 Moon Dev: Increased ATR multiplier for wider stops, allowing more room in volatile crypto markets
    tp_rr = 2.0          # 🌙 Moon Dev: Added risk-reward ratio for dynamic TP (1:2), aiming for higher returns per trade
    risk_percent = 0.02  # 🌙 Moon Dev: Increased risk per trade to 2% to amplify returns while maintaining sizing discipline
    max_bars_in_trade = 20  # 🌙 Moon Dev: Extended time limit to 20 bars, giving trades more time to revert without early exits
    adx_threshold = 25   # 🌙 Moon Dev: Added ADX filter for ranging markets (low trend strength), ideal for mean reversion
    vol_mult = 1.0       # 🌙 Moon Dev: Volume confirmation multiplier, ensuring entries on above-average volume for better setups
    commission = 0.001   # Approximate for crypto

    def init(self):
        close = self.data.Close
        high = self.data.High
        low = self.data.Low
        volume = self.data.Volume
        
        self.bb_upper, self.bb_middle, self.bb_lower = self.I(
            talib.BBANDS, close, timeperiod=self.bb_period, 
            nbdevup=self.bb_std, nbdevdn=self.bb_std, matype=0
        )
        self.rsi = self.I(talib.RSI, close, timeperiod=self.rsi_period)
        # 🌙 Moon Dev: Removed SMA200 trend filter to allow more mean reversion trades in ranging conditions, increasing trade frequency
        self.atr = self.I(talib.ATR, high, low, close, timeperiod=self.atr_period)
        # 🌙 Moon Dev: Added ADX for market regime filter - only trade in low-trend (ranging) markets where reversion shines
        self.adx = self.I(talib.ADX, high, low, close, timeperiod=14)
        # 🌙 Moon Dev: Added volume MA for confirmation - avoids low-volume fakeouts, filtering for higher-quality signals
        self.vol_ma = self.I(talib.SMA, volume, timeperiod=20)

    def next(self):
        current_time = self.data.index[-1]
        close = self.data.Close[-1]
        upper = self.bb_upper[-1]
        middle = self.bb_middle[-1]
        lower = self.bb_lower[-1]
        rsi = self.rsi[-1]
        atr = self.atr[-1]
        adx = self.adx[-1]
        volume = self.data.Volume[-1]
        
        # 🌙 Moon Dev: Simplified exit logic - removed premature RSI neutral exits to let winners run to TP or time limit
        # This improves return potential by avoiding cutting trades too early
        if self.position:
            if hasattr(self.position, 'entry_time'):
                bars_in_trade = (current_time - self.position.entry_time).total_seconds() / (15 * 60)
                # Time-based exit only
                if bars_in_trade > self.max_bars_in_trade:
                    is_long = self.position.is_long
                    self.position.close()
                    print(f"🌙 Moon Dev: Time-Based Exit {'Long' if is_long else 'Short'} at {close} after {bars_in_trade} bars ✨")
                    return
        
        # Entry logic only if no position and in favorable regime
        if not self.position:
            # 🌙 Moon Dev: Added regime filters (ADX < threshold for ranging, volume > MA) to avoid choppy/low-conviction setups
            if adx < self.adx_threshold and volume > self.vol_ma[-1] * self.vol_mult:
                # Long entry: Mean reversion in oversold ranging conditions
                if close <= lower and rsi < self.rsi_oversold:
                    sl = close - (self.atr_mult * atr)
                    sl_dist = close - sl
                    if sl_dist <= 0:
                        return
                    risk = self.equity * self.risk_percent
                    size = risk / sl_dist
                    # 🌙 Moon Dev: Added max position sizing to prevent overleverage when SL is tight relative to equity
                    max_size = self.equity * 0.95 / close
                    size = min(size, max_size)
                    # 🌙 Moon Dev: Dynamic TP based on 1:2 RR using SL distance, for better risk-adjusted returns over fixed BB middle
                    tp = close + (sl_dist * self.tp_rr)
                    
                    self.buy(size=size, sl=sl, tp=tp)
                    self.position.entry_time = current_time
                    print(f"🌙 Moon Dev: Entering Long at {close}, Size: {size:.4f}, SL: {sl:.2f}, TP: {tp:.2f}, RSI: {rsi:.2f}, ATR: {atr:.2f}, ADX: {adx:.2f} 🚀")
                
                # Short entry: Mean reversion in overbought ranging conditions
                elif close >= upper and rsi > self.rsi_overbought:
                    sl = close + (self.atr_mult * atr)
                    sl_dist = sl - close
                    if sl_dist <= 0:
                        return
                    risk = self.equity * self.risk_percent
                    size = risk / sl_dist
                    # 🌙 Moon Dev: Added max position sizing to prevent overleverage when SL is tight relative to equity
                    max_size = self.equity * 0.95 / close
                    size = min(size, max_size)
                    # 🌙 Moon Dev: Dynamic TP based on 1:2 RR using SL distance, for better risk-adjusted returns over fixed BB middle
                    tp = close - (sl_dist * self.tp_rr)
                    
                    self.sell(size=size, sl=sl, tp=tp)
                    self.position.entry_time = current_time
                    print(f"🌙 Moon Dev: Entering Short at {close}, Size: {size:.4f}, SL: {sl:.2f}, TP: {tp:.2f}, RSI: {rsi:.2f}, ATR: {atr:.2f}, ADX: {adx:.2f} ✨")

# Run backtest
bt = Backtest(data, AdaptiveReversion, cash=1000000, commission=0.001)
stats = bt.run()
print(stats)