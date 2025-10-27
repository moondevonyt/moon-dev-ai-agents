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
    rsi_overbought = 75  # 🌙 Moon Dev: Tightened RSI thresholds for higher quality reversion signals
    rsi_oversold = 25
    sma_period = 200
    atr_period = 14
    atr_mult = 2.0  # 🌙 Moon Dev: Widened ATR multiplier for SL to reduce premature stops in volatile crypto
    risk_percent = 0.01
    max_bars_in_trade = 15  # 🌙 Moon Dev: Extended time limit to allow more room for mean reversion
    commission = 0.001  # Approximate for crypto
    adx_period = 14
    adx_threshold = 20  # 🌙 Moon Dev: Added ADX filter to trade only in low-trend (ranging) markets for better reversion
    vol_period = 20
    vol_mult = 1.2  # 🌙 Moon Dev: Volume filter to confirm setups with above-average volume

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
        # 🌙 Moon Dev: Added ADX for market regime filter - avoid strong trends where reversion fails
        self.adx = self.I(talib.ADX, high, low, close, timeperiod=self.adx_period)
        # 🌙 Moon Dev: Added volume SMA for confirmation - only enter on elevated volume for conviction
        self.avg_vol = self.I(talib.SMA, volume, timeperiod=self.vol_period)

    def next(self):
        current_time = self.data.index[-1]
        close = self.data.Close[-1]
        upper = self.bb_upper[-1]
        middle = self.bb_middle[-1]
        lower = self.bb_lower[-1]
        rsi = self.rsi[-1]
        sma200 = self.sma200[-1]
        atr = self.atr[-1]
        adx = self.adx[-1]
        avg_vol = self.avg_vol[-1]
        vol = self.data.Volume[-1]
        
        # Exit logic for existing positions
        if self.position:
            # 🌙 Moon Dev: Removed RSI neutral exit to allow full reversion to middle BB - reduces premature exits
            # Time-based exit only
            if hasattr(self, 'entry_time'):
                bars_in_trade = (current_time - self.entry_time).total_seconds() / (15 * 60)
                is_long = self.position.is_long
            
                if bars_in_trade > self.max_bars_in_trade:
                    self.position.close()
                    print(f"🌙 Moon Dev: Time-Based Exit {'Long' if is_long else 'Short'} at {close} after {bars_in_trade} bars ✨")
                    return
        
        # Entry logic only if no position
        if not self.position:
            # 🌙 Moon Dev: Added ADX < threshold and volume > avg * mult filters for higher quality entries
            # Long entry
            if (close <= lower and rsi < self.rsi_oversold and close > sma200 and
                adx < self.adx_threshold and vol > avg_vol * self.vol_mult):
                sl = close - (self.atr_mult * atr)
                sl_dist = close - sl
                risk = self.equity * self.risk_percent
                size = risk / sl_dist  # 🌙 Moon Dev: Use float size for precise position sizing (no int rounding)
                
                tp = middle
                self.buy(size=size, sl=sl, tp=tp)
                self.entry_time = current_time  # 🌙 Moon Dev: Store entry time on self for reliable calculation
                print(f"🌙 Moon Dev: Entering Long at {close}, Size: {size:.4f}, SL: {sl:.2f}, TP: {tp:.2f}, RSI: {rsi:.2f}, ATR: {atr:.2f}, ADX: {adx:.2f}, Vol Ratio: {vol/avg_vol:.2f} 🚀")
            
            # Short entry
            elif (close >= upper and rsi > self.rsi_overbought and close < sma200 and
                  adx < self.adx_threshold and vol > avg_vol * self.vol_mult):
                sl = close + (self.atr_mult * atr)
                sl_dist = sl - close
                risk = self.equity * self.risk_percent
                size = risk / sl_dist  # 🌙 Moon Dev: Use float size for precise position sizing (no int rounding)
                
                tp = middle
                self.sell(size=size, sl=sl, tp=tp)
                self.entry_time = current_time  # 🌙 Moon Dev: Store entry time on self for reliable calculation
                print(f"🌙 Moon Dev: Entering Short at {close}, Size: {size:.4f}, SL: {sl:.2f}, TP: {tp:.2f}, RSI: {rsi:.2f}, ATR: {atr:.2f}, ADX: {adx:.2f}, Vol Ratio: {vol/avg_vol:.2f} ✨")

# Run backtest
bt = Backtest(data, AdaptiveReversion, cash=1000000, commission=0.001)
stats = bt.run()
print(stats)