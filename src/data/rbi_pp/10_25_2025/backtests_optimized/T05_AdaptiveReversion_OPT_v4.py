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
    bb_std = 2.5  # 🌙 Moon Dev: Widened std dev for rarer, higher-quality mean reversion signals
    rsi_period = 14
    rsi_overbought = 75  # 🌙 Moon Dev: Tightened RSI thresholds for stronger overbought/oversold conditions
    rsi_oversold = 25
    sma_period = 100  # 🌙 Moon Dev: Shortened SMA for more responsive trend filter in volatile crypto
    atr_period = 14
    atr_mult = 2.0  # 🌙 Moon Dev: Widened ATR multiplier for SL to reduce whipsaws
    risk_percent = 0.02  # 🌙 Moon Dev: Increased risk per trade to 2% for higher potential returns while maintaining management
    max_bars_in_trade = 20  # 🌙 Moon Dev: Extended time limit to allow more room for reversion in 15m timeframe
    commission = 0.001  # Approximate for crypto
    rr_ratio = 2.0  # 🌙 Moon Dev: Added risk-reward ratio for dynamic TP calculation

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
        # 🌙 Moon Dev: Added volume SMA filter to confirm entries on above-average volume for better setups
        self.vol_sma = self.I(talib.SMA, volume, timeperiod=20)

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
        
        # 🌙 Moon Dev: Trailing stop logic to lock in profits after breaking even + ATR buffer
        if self.position and hasattr(self, 'entry_price') and self.entry_price is not None:
            if self.position.is_long:
                if close > self.entry_price + atr:
                    new_sl = close - self.atr_mult * atr
                    if new_sl > self.position.sl:
                        self.position.sl = new_sl
                        print(f"🌙 Moon Dev: Trailing SL Long to {new_sl:.2f} at {close} 🚀")
            else:  # short
                if close < self.entry_price - atr:
                    new_sl = close + self.atr_mult * atr
                    if new_sl < self.position.sl:
                        self.position.sl = new_sl
                        print(f"🌙 Moon Dev: Trailing SL Short to {new_sl:.2f} at {close} ✨")
        
        # Exit logic for existing positions
        if self.position:
            # 🌙 Moon Dev: Removed RSI neutral exit to allow trades to run to TP/SL or trailing stop for better returns
            # Time-based exit as safety net
            if hasattr(self, 'entry_time'):
                bars_in_trade = (current_time - self.entry_time).total_seconds() / (15 * 60)
                if bars_in_trade > self.max_bars_in_trade:
                    self.position.close()
                    is_long = self.position.is_long
                    print(f"🌙 Moon Dev: Time-Based Exit {'Long' if is_long else 'Short'} at {close} after {bars_in_trade:.1f} bars ✨")
                    return
        
        # Entry logic only if no position
        if not self.position:
            # Long entry with tightened conditions and volume filter
            if close <= lower and rsi < self.rsi_oversold and close > sma200 and vol > vol_avg:
                sl = close - (self.atr_mult * atr)
                sl_dist = close - sl
                # 🌙 Moon Dev: Use fraction sizing for precise risk management (0-1 fraction of equity)
                size = self.risk_percent / (sl_dist / close)
                # 🌙 Moon Dev: Dynamic TP based on RR ratio instead of fixed middle BB for improved reward potential
                tp_dist = self.rr_ratio * sl_dist
                tp = close + tp_dist
                self.buy(size=size, sl=sl, tp=tp)
                self.entry_price = close
                self.entry_time = current_time
                print(f"🌙 Moon Dev: Entering Long at {close}, Size: {size:.4f}, SL: {sl:.2f}, TP: {tp:.2f}, RSI: {rsi:.2f}, ATR: {atr:.2f}, Vol: {vol:.0f} > {vol_avg:.0f} 🚀")
            
            # Short entry with tightened conditions and volume filter
            elif close >= upper and rsi > self.rsi_overbought and close < sma200 and vol > vol_avg:
                sl = close + (self.atr_mult * atr)
                sl_dist = sl - close
                # 🌙 Moon Dev: Use fraction sizing for precise risk management (0-1 fraction of equity)
                size = self.risk_percent / (sl_dist / close)
                # 🌙 Moon Dev: Dynamic TP based on RR ratio instead of fixed middle BB for improved reward potential
                tp_dist = self.rr_ratio * sl_dist
                tp = close - tp_dist
                self.sell(size=size, sl=sl, tp=tp)
                self.entry_price = close
                self.entry_time = current_time
                print(f"🌙 Moon Dev: Entering Short at {close}, Size: {size:.4f}, SL: {sl:.2f}, TP: {tp:.2f}, RSI: {rsi:.2f}, ATR: {atr:.2f}, Vol: {vol:.0f} > {vol_avg:.0f} ✨")

# Run backtest
bt = Backtest(data, AdaptiveReversion, cash=1000000, commission=0.001)
stats = bt.run()
print(stats)