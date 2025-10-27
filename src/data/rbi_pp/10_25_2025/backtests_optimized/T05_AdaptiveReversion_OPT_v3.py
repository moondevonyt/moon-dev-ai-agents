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
    sma_period = 100     # 🌙 Moon Dev: Reduced from 200 to 100 for more responsive trend filter
    atr_period = 14
    atr_mult = 2.0       # 🌙 Moon Dev: Increased SL multiplier to 2.0 for better risk management in volatile crypto
    risk_percent = 0.015 # 🌙 Moon Dev: Increased to 1.5% for higher exposure while maintaining control
    max_bars_in_trade = 15  # 🌙 Moon Dev: Extended to 15 bars to allow more time for reversion
    commission = 0.001  # Approximate for crypto
    vol_period = 20     # 🌙 Moon Dev: Added for volume SMA
    adx_period = 14     # 🌙 Moon Dev: Added ADX for market regime filter
    adx_threshold = 25  # 🌙 Moon Dev: Only trade in ranging markets (ADX < 25) to avoid trends where reversion fails
    max_position_fraction = 0.1  # 🌙 Moon Dev: Cap position size to 10% of equity for risk control
    rr_ratio = 1.5      # 🌙 Moon Dev: Use 1:1.5 risk-reward for TP instead of fixed middle BB for consistent profitability

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
        # 🌙 Moon Dev: Switched to EMA for faster trend detection on 15m timeframe
        self.sma200 = self.I(talib.EMA, close, timeperiod=self.sma_period)
        self.atr = self.I(talib.ATR, high, low, close, timeperiod=self.atr_period)
        # 🌙 Moon Dev: Added volume SMA for confirmation - only enter on above-average volume for better setups
        self.vol_sma = self.I(talib.SMA, volume, timeperiod=self.vol_period)
        # 🌙 Moon Dev: Added ADX to filter for ranging markets, optimizing for mean reversion
        self.adx = self.I(talib.ADX, high, low, close, timeperiod=self.adx_period)

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
        vol_sma = self.vol_sma[-1]
        adx = self.adx[-1]
        
        # Exit logic for existing positions
        if self.position:
            bars_in_trade = (current_time - self.position.entry_time).total_seconds() / (15 * 60) if hasattr(self.position, 'entry_time') else 0
            is_long = self.position.is_long
            
            # 🌙 Moon Dev: Adjusted RSI neutral exit thresholds to 60/40 for more room, allowing winners to breathe
            if (is_long and rsi > 60) or (not is_long and rsi < 40):
                self.position.close()
                print(f"🌙 Moon Dev: RSI Neutral Exit {'Long' if is_long else 'Short'} at {close} 🚀 RSI: {rsi:.2f}")
                return
            
            # Time-based exit
            if bars_in_trade > self.max_bars_in_trade:
                self.position.close()
                print(f"🌙 Moon Dev: Time-Based Exit {'Long' if is_long else 'Short'} at {close} after {bars_in_trade} bars ✨")
                return
        
        # Entry logic only if no position
        if not self.position:
            sl_dist_pct_long = self.atr_mult * atr / close  # For fraction sizing
            sl_dist_pct_short = self.atr_mult * atr / close
            
            # Long entry - 🌙 Moon Dev: Added volume > 1.2x SMA and ADX < 25 filters for higher quality setups
            if (close <= lower and rsi < self.rsi_oversold and close > sma200 and 
                vol > vol_sma * 1.2 and adx < self.adx_threshold):
                sl = close - (self.atr_mult * atr)
                sl_dist = close - sl
                # 🌙 Moon Dev: Optimized position sizing to fraction of equity based on risk percent and SL distance
                size = self.risk_percent / (sl_dist / close)
                size = min(size, self.max_position_fraction)
                
                # 🌙 Moon Dev: Dynamic TP based on 1:1.5 RR for better reward capture
                tp = close + (sl_dist * self.rr_ratio)
                self.buy(size=size, sl=sl, tp=tp)
                self.position.entry_time = current_time
                print(f"🌙 Moon Dev: Entering Long at {close}, Size: {size:.4f}, SL: {sl:.2f}, TP: {tp:.2f}, RSI: {rsi:.2f}, ATR: {atr:.2f}, ADX: {adx:.2f}, Vol Ratio: {vol/vol_sma:.2f} 🚀")
            
            # Short entry - 🌙 Moon Dev: Same filters applied to shorts for consistency
            elif (close >= upper and rsi > self.rsi_overbought and close < sma200 and 
                  vol > vol_sma * 1.2 and adx < self.adx_threshold):
                sl = close + (self.atr_mult * atr)
                sl_dist = sl - close
                # 🌙 Moon Dev: Same fraction-based sizing for shorts
                size = self.risk_percent / (sl_dist / close)
                size = min(size, self.max_position_fraction)
                
                # 🌙 Moon Dev: Dynamic TP for shorts with 1:1.5 RR
                tp = close - (sl_dist * self.rr_ratio)
                self.sell(size=size, sl=sl, tp=tp)
                self.position.entry_time = current_time
                print(f"🌙 Moon Dev: Entering Short at {close}, Size: {size:.4f}, SL: {sl:.2f}, TP: {tp:.2f}, RSI: {rsi:.2f}, ATR: {atr:.2f}, ADX: {adx:.2f}, Vol Ratio: {vol/vol_sma:.2f} ✨")

# Run backtest
bt = Backtest(data, AdaptiveReversion, cash=1000000, commission=0.001)
stats = bt.run()
print(stats)