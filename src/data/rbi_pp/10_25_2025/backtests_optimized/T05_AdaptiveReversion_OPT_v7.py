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
    sma_period = 200
    atr_period = 14
    atr_mult = 1.5
    risk_percent = 0.01
    max_bars_in_trade = 20  # 🌙 Moon Dev: Increased to 20 bars (5 hours on 15m) to allow more time for reversion
    adx_threshold = 25      # 🌙 Moon Dev: New ADX threshold for low trend strength, favoring ranging markets for reversion
    vol_ma_period = 20      # 🌙 Moon Dev: New volume MA period for volume confirmation filter
    rr_ratio = 2.0          # 🌙 Moon Dev: Risk-reward ratio for dynamic TP, aiming for 1:2 to boost returns
    commission = 0.001  # Approximate for crypto

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
        self.sma200 = self.I(talib.SMA, close, timeperiod=self.sma_period)
        self.atr = self.I(talib.ATR, high, low, close, timeperiod=self.atr_period)
        # 🌙 Moon Dev: Added ADX indicator to filter for low-trend (ranging) markets where mean reversion works best
        self.adx = self.I(talib.ADX, high, low, close, timeperiod=14)
        # 🌙 Moon Dev: Added volume MA for confirmation, ensuring entries on higher-than-average volume for conviction
        self.vol_ma = self.I(talib.SMA, volume, timeperiod=self.vol_ma_period)

    def next(self):
        current_time = self.data.index[-1]
        close = self.data.Close[-1]
        high_price = self.data.High[-1]
        low_price = self.data.Low[-1]
        upper = self.bb_upper[-1]
        middle = self.bb_middle[-1]
        lower = self.bb_lower[-1]
        rsi = self.rsi[-1]
        sma200 = self.sma200[-1]
        atr = self.atr[-1]
        adx = self.adx[-1]
        vol = self.data.Volume[-1]
        vol_ma = self.vol_ma[-1]
        
        # Exit logic for existing positions (only time-based to avoid premature exits)
        if self.position:
            bars_in_trade = (current_time - self.position.entry_time).total_seconds() / (15 * 60) if hasattr(self.position, 'entry_time') else 0
            is_long = self.position.is_long
            
            # Removed RSI neutral exit to let positions run to TP/SL for higher reward capture
            # 🌙 Moon Dev: Relies on fixed SL/TP and time exit for better risk-reward balance
            
            # Time-based exit
            if bars_in_trade > self.max_bars_in_trade:
                self.position.close()
                print(f"🌙 Moon Dev: Time-Based Exit {'Long' if is_long else 'Short'} at {close} after {bars_in_trade} bars ✨")
                return
        
        # Entry logic only if no position
        if not self.position:
            sl_dist = 0
            size = 0
            # Long entry: Improved with Low touch on BB lower, tighter RSI, trend filter, volume, and ADX
            if low_price <= lower and rsi < self.rsi_oversold and close > sma200 and vol > vol_ma and adx < self.adx_threshold:
                sl = close - (self.atr_mult * atr)
                sl_dist = close - sl
                risk = self.equity * self.risk_percent
                size = risk / sl_dist  # 🌙 Moon Dev: Allow fractional sizing for precise risk management (no int rounding)
                
                tp_dist = self.rr_ratio * sl_dist  # 🌙 Moon Dev: Dynamic TP based on RR ratio instead of fixed middle BB for consistent reward
                tp = close + tp_dist
                self.buy(size=size, sl=sl, tp=tp)
                self.position.entry_time = current_time
                print(f"🌙 Moon Dev: Entering Long at {close}, Size: {size:.4f}, SL: {sl:.2f}, TP: {tp:.2f}, RSI: {rsi:.2f}, ATR: {atr:.2f}, ADX: {adx:.2f}, Vol>MA: {vol>vol_ma} 🚀")
            
            # Short entry: Improved with High touch on BB upper, tighter RSI, trend filter, volume, and ADX
            elif high_price >= upper and rsi > self.rsi_overbought and close < sma200 and vol > vol_ma and adx < self.adx_threshold:
                sl = close + (self.atr_mult * atr)
                sl_dist = sl - close
                risk = self.equity * self.risk_percent
                size = risk / sl_dist  # 🌙 Moon Dev: Allow fractional sizing for precise risk management (no int rounding)
                
                tp_dist = self.rr_ratio * sl_dist  # 🌙 Moon Dev: Dynamic TP based on RR ratio instead of fixed middle BB for consistent reward
                tp = close - tp_dist
                self.sell(size=size, sl=sl, tp=tp)
                self.position.entry_time = current_time
                print(f"🌙 Moon Dev: Entering Short at {close}, Size: {size:.4f}, SL: {sl:.2f}, TP: {tp:.2f}, RSI: {rsi:.2f}, ATR: {atr:.2f}, ADX: {adx:.2f}, Vol>MA: {vol>vol_ma} ✨")

# Run backtest
bt = Backtest(data, AdaptiveReversion, cash=1000000, commission=0.001)
stats = bt.run()
print(stats)