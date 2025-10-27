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
    bb_std = 2.0  # 🌙 Moon Dev: Kept at 2.0 for balanced signal frequency in volatile crypto markets
    rsi_period = 14
    rsi_overbought = 75  # 🌙 Moon Dev: Tightened from 70 to 75 for fewer but higher-quality overbought signals
    rsi_oversold = 25  # 🌙 Moon Dev: Tightened from 30 to 25 for fewer but higher-quality oversold signals
    ema_period = 200  # 🌙 Moon Dev: Changed from SMA 200 to EMA for faster trend response
    atr_period = 14
    atr_mult = 2.0  # 🌙 Moon Dev: Increased from 1.5 to 2.0 for wider stops, reducing whipsaws
    risk_percent = 0.015  # 🌙 Moon Dev: Slightly increased from 0.01 to 0.015 for higher position exposure while maintaining risk control
    max_bars_in_trade = 20  # 🌙 Moon Dev: Increased from 10 to 20 (5 hours on 15m) to allow more room for reversion
    vol_ma_period = 20  # 🌙 Moon Dev: New parameter for volume moving average
    vol_mult = 1.2  # 🌙 Moon Dev: Volume must exceed 1.2x MA for entry confirmation to filter low-volume fakeouts
    rr_ratio = 2.0  # 🌙 Moon Dev: New risk-reward ratio for dynamic TP (2:1) instead of fixed middle BB for better profitability
    commission = 0.001  # Approximate for crypto

    def init(self):
        close = self.data.Close
        high = self.data.High
        low = self.data.Low
        volume = self.data.Volume  # 🌙 Moon Dev: Added volume data reference
        
        self.bb_upper, self.bb_middle, self.bb_lower = self.I(
            talib.BBANDS, close, timeperiod=self.bb_period, 
            nbdevup=self.bb_std, nbdevdn=self.bb_std, matype=0
        )
        self.rsi = self.I(talib.RSI, close, timeperiod=self.rsi_period)
        self.ema200 = self.I(talib.EMA, close, timeperiod=self.ema_period)  # 🌙 Moon Dev: Switched to EMA for improved trend detection
        self.atr = self.I(talib.ATR, high, low, close, timeperiod=self.atr_period)
        self.vol_ma = self.I(talib.SMA, volume, timeperiod=self.vol_ma_period)  # 🌙 Moon Dev: Added volume MA filter for entry quality

    def next(self):
        current_time = self.data.index[-1]
        close = self.data.Close[-1]
        upper = self.bb_upper[-1]
        middle = self.bb_middle[-1]
        lower = self.bb_lower[-1]
        rsi = self.rsi[-1]
        ema200 = self.ema200[-1]
        atr = self.atr[-1]
        vol = self.data.Volume[-1]  # 🌙 Moon Dev: Current volume for filter
        vol_ma = self.vol_ma[-1]  # 🌙 Moon Dev: Volume MA for comparison
        
        # Exit logic for existing positions
        if self.position:
            bars_in_trade = (current_time - self.position.entry_time).total_seconds() / (15 * 60) if hasattr(self.position, 'entry_time') else 0
            is_long = self.position.is_long
            
            # Improved RSI extreme exit for mean reversion (exit only at opposite extremes, not neutral 50)
            # 🌙 Moon Dev: Changed from RSI >50/<50 to extremes (75/25) to preserve winners longer and exit on full reversion
            if (is_long and rsi >= self.rsi_overbought) or (not is_long and rsi <= self.rsi_oversold):
                self.position.close()
                print(f"🌙 Moon Dev: RSI Extreme Exit {'Long' if is_long else 'Short'} at {close} 🚀 RSI: {rsi:.2f}")
                return
            
            # Time-based exit
            if bars_in_trade > self.max_bars_in_trade:
                self.position.close()
                print(f"🌙 Moon Dev: Time-Based Exit {'Long' if is_long else 'Short'} at {close} after {bars_in_trade} bars ✨")
                return
        
        # Entry logic only if no position and volume confirmation
        # 🌙 Moon Dev: Added volume filter to ensure entries occur on above-average volume for stronger signals
        if not self.position and vol > vol_ma * self.vol_mult:
            # Long entry with tightened conditions and dynamic TP
            if close <= lower and rsi < self.rsi_oversold and close > ema200:
                sl = close - (self.atr_mult * atr)
                sl_dist = close - sl
                risk = self.equity * self.risk_percent
                size = risk / sl_dist
                size = max(0.01, min(100.0, size))  # 🌙 Moon Dev: Allow fractional sizes (0.01 min, 100 max BTC cap for realism), no int rounding to enable precise sizing
                
                # Dynamic TP based on RR ratio instead of middle BB
                # 🌙 Moon Dev: Improved TP to 2:1 RR for higher returns while keeping risk fixed
                tp = close + (self.rr_ratio * sl_dist)
                self.buy(size=size, sl=sl, tp=tp)
                self.position.entry_time = current_time
                print(f"🌙 Moon Dev: Entering Long at {close}, Size: {size:.4f}, SL: {sl:.2f}, TP: {tp:.2f}, RSI: {rsi:.2f}, ATR: {atr:.2f}, Vol Mult: {vol/vol_ma:.2f} 🚀")
            
            # Short entry with tightened conditions and dynamic TP
            elif close >= upper and rsi > self.rsi_overbought and close < ema200:
                sl = close + (self.atr_mult * atr)
                sl_dist = sl - close
                risk = self.equity * self.risk_percent
                size = risk / sl_dist
                size = max(0.01, min(100.0, size))  # 🌙 Moon Dev: Allow fractional sizes (0.01 min, 100 max BTC cap for realism), no int rounding to enable precise sizing
                
                # Dynamic TP based on RR ratio
                # 🌙 Moon Dev: Improved TP to 2:1 RR for higher returns while keeping risk fixed
                tp = close - (self.rr_ratio * sl_dist)
                self.sell(size=size, sl=sl, tp=tp)
                self.position.entry_time = current_time
                print(f"🌙 Moon Dev: Entering Short at {close}, Size: {size:.4f}, SL: {sl:.2f}, TP: {tp:.2f}, RSI: {rsi:.2f}, ATR: {atr:.2f}, Vol Mult: {vol/vol_ma:.2f} ✨")

# Run backtest
bt = Backtest(data, AdaptiveReversion, cash=1000000, commission=0.001)
stats = bt.run()
print(stats)