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
    rsi_overbought = 75  # 🌙 Moon Dev: Tightened RSI thresholds for stronger mean-reversion signals to reduce false entries
    rsi_oversold = 25    # Improves entry quality by waiting for more extreme oversold/overbought conditions
    sma_period = 50      # 🌙 Moon Dev: Shortened SMA period from 200 to 50 for better adaptation to 15m timeframe volatility
    atr_period = 14
    atr_mult = 2.0       # 🌙 Moon Dev: Widened ATR multiplier for stop loss to give trades more breathing room, reducing premature stops
    risk_percent = 0.015 # 🌙 Moon Dev: Slightly increased risk per trade from 1% to 1.5% for higher exposure while maintaining risk management
    max_bars_in_trade = 20  # 🌙 Moon Dev: Extended time-based exit from 10 to 20 bars (5 hours on 15m) to allow more time for reversion
    vol_mult = 1.2       # 🌙 Moon Dev: Added volume multiplier for confirmation filter
    commission = 0.001   # Approximate for crypto

    def init(self):
        close = self.data.Close
        high = self.data.High
        low = self.data.Low
        
        self.bb_upper, self.bb_middle, self.bb_lower = self.I(
            talib.BBANDS, close, timeperiod=self.bb_period, 
            nbdevup=self.bb_std, nbdevdn=self.bb_std, matype=0
        )
        self.rsi = self.I(talib.RSI, close, timeperiod=self.rsi_period)
        self.sma50 = self.I(talib.SMA, close, timeperiod=self.sma_period)  # Renamed for clarity
        self.atr = self.I(talib.ATR, high, low, close, timeperiod=self.atr_period)
        self.vol_sma = self.I(talib.SMA, self.data.Volume, timeperiod=20)  # 🌙 Moon Dev: Added volume SMA for entry filter to avoid low-volume traps
        self.entry_time = None  # 🌙 Moon Dev: Track entry time safely without relying on position attributes

    def next(self):
        current_time = self.data.index[-1]
        close = self.data.Close[-1]
        upper = self.bb_upper[-1]
        middle = self.bb_middle[-1]
        lower = self.bb_lower[-1]
        rsi = self.rsi[-1]
        sma50 = self.sma50[-1]
        atr = self.atr[-1]
        vol = self.data.Volume[-1]
        vol_avg = self.vol_sma[-1]
        
        # Exit logic for existing positions
        if self.position:
            # 🌙 Moon Dev: Calculate bars in trade using self.entry_time for reliability
            bars_in_trade = 0
            if self.entry_time:
                bars_in_trade = (current_time - self.entry_time).total_seconds() / (15 * 60)
            is_long = self.position.is_long
            
            # Time-based exit only (removed RSI neutral exit to let SL/TP handle mean reversion properly)
            # 🌙 Moon Dev: Removed RSI >50/<50 exit to avoid premature closes; relies on improved SL/TP for better risk-reward
            if bars_in_trade > self.max_bars_in_trade:
                self.position.close()
                self.entry_time = None  # Reset entry time on exit
                print(f"🌙 Moon Dev: Time-Based Exit {'Long' if is_long else 'Short'} at {close} after {bars_in_trade} bars ✨")
                return
        
        # Entry logic only if no position
        if not self.position:
            vol_confirm = vol > self.vol_mult * vol_avg  # 🌙 Moon Dev: Volume filter to ensure conviction in setups, avoiding choppy low-volume entries
            
            # Long entry
            if close <= lower and rsi < self.rsi_oversold and close > sma50 and vol_confirm:
                sl = close - (self.atr_mult * atr)
                sl_dist = close - sl
                risk = self.equity * self.risk_percent
                size = risk / sl_dist  # 🌙 Moon Dev: Use float size for precise position sizing (no int rounding) to optimize capital use
                
                # 🌙 Moon Dev: Dynamic TP at 2:1 RR instead of fixed middle BB for better reward potential while maintaining risk control
                tp = close + 2 * sl_dist
                self.entry_time = current_time  # Set before trade
                self.buy(size=size, sl=sl, tp=tp)
                print(f"🌙 Moon Dev: Entering Long at {close}, Size: {size}, SL: {sl:.2f}, TP: {tp:.2f}, RSI: {rsi:.2f}, ATR: {atr:.2f}, Vol Confirm: {vol_confirm} 🚀")
            
            # Short entry
            elif close >= upper and rsi > self.rsi_overbought and close < sma50 and vol_confirm:
                sl = close + (self.atr_mult * atr)
                sl_dist = sl - close
                risk = self.equity * self.risk_percent
                size = risk / sl_dist  # Float size for precision
                
                # Dynamic TP at 2:1 RR
                tp = close - 2 * sl_dist
                self.entry_time = current_time
                self.sell(size=size, sl=sl, tp=tp)
                print(f"🌙 Moon Dev: Entering Short at {close}, Size: {size}, SL: {sl:.2f}, TP: {tp:.2f}, RSI: {rsi:.2f}, ATR: {atr:.2f}, Vol Confirm: {vol_confirm} ✨")

# Run backtest
bt = Backtest(data, AdaptiveReversion, cash=1000000, commission=0.001)
stats = bt.run()
print(stats)