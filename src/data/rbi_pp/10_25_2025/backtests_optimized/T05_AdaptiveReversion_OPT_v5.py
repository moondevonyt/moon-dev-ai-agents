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
    bb_std = 2.5  # 🌙 Moon Dev: Widened BB std dev for stronger mean reversion signals, reducing false entries
    rsi_period = 14
    rsi_overbought = 75  # 🌙 Moon Dev: Tightened RSI thresholds for higher quality oversold/overbought conditions
    rsi_oversold = 25
    sma_period = 100  # 🌙 Moon Dev: Shortened SMA period for more responsive trend filter in volatile crypto markets
    atr_period = 14
    atr_mult = 2.0  # 🌙 Moon Dev: Increased ATR multiplier for wider stops, allowing more room in volatile conditions
    risk_percent = 0.02  # 🌙 Moon Dev: Increased risk per trade to 2% for higher exposure and potential returns while maintaining management
    max_bars_in_trade = 20  # 🌙 Moon Dev: Extended time limit to let winners breathe longer
    adx_threshold = 25  # 🌙 Moon Dev: ADX filter for ranging markets (low ADX) to favor mean reversion
    vol_mult = 1.2  # 🌙 Moon Dev: Volume confirmation multiplier to filter low-conviction setups
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
        self.sma200 = self.I(talib.SMA, close, timeperiod=self.sma_period)
        self.atr = self.I(talib.ATR, high, low, close, timeperiod=self.atr_period)
        # 🌙 Moon Dev: Added volume SMA for confirmation - only trade on above-average volume for better momentum
        self.vol_sma = self.I(talib.SMA, volume, timeperiod=20)
        # 🌙 Moon Dev: Added ADX to filter for ranging markets where mean reversion shines (ADX < 25)
        self.adx = self.I(talib.ADX, high, low, close, timeperiod=14)

    def next(self):
        current_time = self.data.index[-1]
        close = self.data.Close[-1]
        upper = self.bb_upper[-1]
        middle = self.bb_middle[-1]
        lower = self.bb_lower[-1]
        rsi = self.rsi[-1]
        sma200 = self.sma200[-1]
        atr = self.atr[-1]
        vol = self.data.Volume[-1]  # 🌙 Moon Dev: Current volume for filter
        vol_sma = self.vol_sma[-1]
        adx = self.adx[-1]  # 🌙 Moon Dev: Current ADX for regime filter
        
        # Exit logic for existing positions
        if self.position:
            bars_in_trade = (current_time - self.position.entry_time).total_seconds() / (15 * 60) if hasattr(self.position, 'entry_time') else 0
            is_long = self.position.is_long
            
            # Adjusted RSI exit for better win retention - exit only if strongly reversed
            if (is_long and rsi > 60) or (not is_long and rsi < 40):
                self.position.close()
                print(f"🌙 Moon Dev: RSI Reversal Exit {'Long' if is_long else 'Short'} at {close} 🚀 RSI: {rsi:.2f}")
                return
            
            # Time-based exit
            if bars_in_trade > self.max_bars_in_trade:
                self.position.close()
                print(f"🌙 Moon Dev: Time-Based Exit {'Long' if is_long else 'Short'} at {close} after {bars_in_trade} bars ✨")
                return
        
        # Entry logic only if no position
        if not self.position:
            # 🌙 Moon Dev: Added volume and ADX filters to both entries for higher quality setups
            vol_confirm = vol > vol_sma * self.vol_mult
            range_confirm = adx < self.adx_threshold
            
            # Long entry
            if close <= lower and rsi < self.rsi_oversold and close > sma200 and vol_confirm and range_confirm:
                sl = close - (self.atr_mult * atr)
                sl_dist = close - sl
                price_risk = sl_dist / close  # 🌙 Moon Dev: Calculate % price risk for proper fractional sizing
                size = self.risk_percent / price_risk  # 🌙 Moon Dev: Fraction of equity to risk exact % - ensures consistent risk regardless of price level
                tp_dist = 2 * sl_dist  # 🌙 Moon Dev: Dynamic 2:1 RR TP instead of fixed middle for better reward potential
                tp = close + tp_dist
                
                self.buy(size=size, sl=sl, tp=tp)
                self.position.entry_time = current_time
                print(f"🌙 Moon Dev: Entering Long at {close}, Size: {size:.4f}, SL: {sl:.2f}, TP: {tp:.2f}, RSI: {rsi:.2f}, ATR: {atr:.2f}, ADX: {adx:.2f}, Vol Confirm: {vol_confirm} 🚀")
            
            # Short entry
            elif close >= upper and rsi > self.rsi_overbought and close < sma200 and vol_confirm and range_confirm:
                sl = close + (self.atr_mult * atr)
                sl_dist = sl - close
                price_risk = sl_dist / close  # 🌙 Moon Dev: Calculate % price risk for proper fractional sizing
                size = self.risk_percent / price_risk  # 🌙 Moon Dev: Fraction of equity to risk exact % - ensures consistent risk regardless of price level
                tp_dist = 2 * sl_dist  # 🌙 Moon Dev: Dynamic 2:1 RR TP instead of fixed middle for better reward potential
                tp = close - tp_dist
                
                self.sell(size=size, sl=sl, tp=tp)
                self.position.entry_time = current_time
                print(f"🌙 Moon Dev: Entering Short at {close}, Size: {size:.4f}, SL: {sl:.2f}, TP: {tp:.2f}, RSI: {rsi:.2f}, ATR: {atr:.2f}, ADX: {adx:.2f}, Vol Confirm: {vol_confirm} ✨")

# Run backtest
bt = Backtest(data, AdaptiveReversion, cash=1000000, commission=0.001)
stats = bt.run()
print(stats)