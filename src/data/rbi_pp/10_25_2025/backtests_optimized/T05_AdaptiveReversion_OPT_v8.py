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
    max_bars_in_trade = 20  # 🌙 Moon Dev: Increased to 20 bars to allow more time for mean reversion while managing risk
    commission = 0.001  # Approximate for crypto
    vol_period = 20     # 🌙 Moon Dev: New parameter for volume SMA
    vol_mult = 1.1      # 🌙 Moon Dev: Require 10% above average volume for entry confirmation

    def init(self):
        close = self.data.Close
        high = self.data.High
        low = self.data.Low
        volume = self.data.Volume  # 🌙 Moon Dev: Added volume data for new filter
        
        self.bb_upper, self.bb_middle, self.bb_lower = self.I(
            talib.BBANDS, close, timeperiod=self.bb_period, 
            nbdevup=self.bb_std, nbdevdn=self.bb_std, matype=0
        )
        self.rsi = self.I(talib.RSI, close, timeperiod=self.rsi_period)
        self.sma200 = self.I(talib.SMA, close, timeperiod=self.sma_period)
        self.atr = self.I(talib.ATR, high, low, close, timeperiod=self.atr_period)
        # 🌙 Moon Dev: Added volume SMA for high-volume confirmation to filter low-quality setups
        self.vol_sma = self.I(talib.SMA, volume, timeperiod=self.vol_period)

    def next(self):
        current_time = self.data.index[-1]
        close = self.data.Close[-1]
        upper = self.bb_upper[-1]
        middle = self.bb_middle[-1]
        lower = self.bb_lower[-1]
        rsi = self.rsi[-1]
        sma200 = self.sma200[-1]
        atr = self.atr[-1]
        vol = self.data.Volume[-1]
        vol_avg = self.vol_sma[-1]
        # 🌙 Moon Dev: Added trend slope confirmation using SMA200 direction for better regime filtering
        sma_uptrend = len(self.sma200) >= 2 and self.sma200[-1] > self.sma200[-2]
        sma_downtrend = len(self.sma200) >= 2 and self.sma200[-1] < self.sma200[-2]
        
        # Exit logic for existing positions (improved with breakeven trailing)
        if self.position:
            entry_price = getattr(self.position, 'entry_price', close)
            
            # 🌙 Moon Dev: Added breakeven adjustment for better risk management - move SL to entry when in profit
            if self.position.is_long:
                if close > entry_price:
                    new_sl = max(self.position.sl, entry_price)
                    if new_sl > self.position.sl:  # Only update and print if improved
                        old_sl = self.position.sl
                        self.position.sl = new_sl
                        print(f"🌙 Moon Dev: Breakeven SL Adjustment Long from {old_sl:.2f} to {new_sl:.2f} at {close} 🚀")
            else:
                if close < entry_price:
                    new_sl = min(self.position.sl, entry_price)
                    if new_sl < self.position.sl:  # Only update and print if improved
                        old_sl = self.position.sl
                        self.position.sl = new_sl
                        print(f"🌙 Moon Dev: Breakeven SL Adjustment Short from {old_sl:.2f} to {new_sl:.2f} at {close} ✨")
            
            # Time-based exit (no RSI neutral exit - removed to allow full TP potential with 1:2 RR)
            if hasattr(self.position, 'entry_time'):
                bars_in_trade = (current_time - self.position.entry_time).total_seconds() / (15 * 60)
                if bars_in_trade > self.max_bars_in_trade:
                    is_long = self.position.is_long
                    self.position.close()
                    print(f"🌙 Moon Dev: Time-Based Exit {'Long' if is_long else 'Short'} at {close} after {bars_in_trade:.1f} bars ✨")
                    return
        
        # Entry logic only if no position
        if not self.position:
            # 🌙 Moon Dev: Added volume and trend slope filters for higher-quality entries; changed to 1:2 RR for TP to improve returns
            # Long entry
            if (close <= lower and rsi < self.rsi_oversold and close > sma200 and 
                sma_uptrend and vol > vol_avg * self.vol_mult):
                sl = close - (self.atr_mult * atr)
                sl_dist = close - sl
                risk = self.equity * self.risk_percent
                size = risk / sl_dist  # 🌙 Moon Dev: Use float size for precise position sizing (allows fractions 0-1)
                tp = close + 2 * sl_dist  # 🌙 Moon Dev: Set TP at 1:2 risk-reward for better profit potential
                entry_price = close
                self.buy(size=size, sl=sl, tp=tp)
                self.position.entry_price = entry_price
                self.position.entry_time = current_time
                print(f"🌙 Moon Dev: Entering Long at {close}, Size: {size:.4f}, SL: {sl:.2f}, TP: {tp:.2f}, RSI: {rsi:.2f}, ATR: {atr:.2f}, Vol Mult: {vol/vol_avg:.2f} 🚀")
            
            # Short entry
            elif (close >= upper and rsi > self.rsi_overbought and close < sma200 and 
                  sma_downtrend and vol > vol_avg * self.vol_mult):
                sl = close + (self.atr_mult * atr)
                sl_dist = sl - close
                risk = self.equity * self.risk_percent
                size = risk / sl_dist  # 🌙 Moon Dev: Use float size for precise position sizing
                tp = close - 2 * sl_dist  # 🌙 Moon Dev: Set TP at 1:2 risk-reward for better profit potential
                entry_price = close
                self.sell(size=size, sl=sl, tp=tp)
                self.position.entry_price = entry_price
                self.position.entry_time = current_time
                print(f"🌙 Moon Dev: Entering Short at {close}, Size: {size:.4f}, SL: {sl:.2f}, TP: {tp:.2f}, RSI: {rsi:.2f}, ATR: {atr:.2f}, Vol Mult: {vol/vol_avg:.2f} ✨")

# Run backtest
bt = Backtest(data, AdaptiveReversion, cash=1000000, commission=0.001)
stats = bt.run()
print(stats)