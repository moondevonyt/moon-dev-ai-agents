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
    atr_mult = 2.0       # 🌙 Moon Dev: Increased to 2.0 for wider stops, allowing more room in volatile crypto markets
    risk_percent = 0.02  # 🌙 Moon Dev: Increased to 2% for larger positions to boost returns while maintaining risk control
    max_bars_in_trade = 20  # 🌙 Moon Dev: Extended to 20 bars (5 hours on 15m) to give trades more time to revert
    adx_period = 14
    adx_threshold = 25   # 🌙 Moon Dev: ADX < 25 filters for ranging markets ideal for mean reversion
    vol_sma_period = 20
    atr_sma_period = 20
    rsi_long_exit = 60   # 🌙 Moon Dev: Exit longs at RSI 60 to hold winners longer
    rsi_short_exit = 40  # 🌙 Moon Dev: Exit shorts at RSI 40 to hold winners longer
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
        # 🌙 Moon Dev: Added ADX for market regime filter - only trade in low trend strength (ranging) conditions
        self.adx = self.I(talib.ADX, high, low, close, timeperiod=self.adx_period)
        # 🌙 Moon Dev: Added volume SMA filter to avoid low-volume fakeouts
        self.vol_sma = self.I(talib.SMA, volume, timeperiod=self.vol_sma_period)
        # 🌙 Moon Dev: Added ATR SMA filter to trade only in higher volatility regimes for better moves
        self.atr_sma = self.I(talib.SMA, self.atr, timeperiod=self.atr_sma_period)
        
        # 🌙 Moon Dev: Initialize entry time tracker for accurate bar counting
        self.entry_time = None

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
        vol = self.data.Volume[-1]
        vol_sma = self.vol_sma[-1]
        atr_sma = self.atr_sma[-1]
        
        # 🌙 Moon Dev: Calculate bars in trade properly using self.entry_time
        bars_in_trade = 0
        if self.position and self.entry_time is not None:
            bars_in_trade = (current_time - self.entry_time).total_seconds() / (15 * 60)
        
        # Exit logic for existing positions - dynamic BB middle cross for better mean reversion targeting
        if self.position:
            is_long = self.position.is_long
            exit_reason = None
            
            if is_long:
                # 🌙 Moon Dev: Dynamic exit at current BB middle (reversion target), RSI >60, or time limit
                if close >= middle:
                    exit_reason = "BB Middle Cross"
                elif rsi > self.rsi_long_exit:
                    exit_reason = f"RSI > {self.rsi_long_exit}"
                elif bars_in_trade > self.max_bars_in_trade:
                    exit_reason = f"Time-Based ({bars_in_trade} bars)"
            else:  # short
                # 🌙 Moon Dev: Dynamic exit at current BB middle, RSI <40, or time limit
                if close <= middle:
                    exit_reason = "BB Middle Cross"
                elif rsi < self.rsi_short_exit:
                    exit_reason = f"RSI < {self.rsi_short_exit}"
                elif bars_in_trade > self.max_bars_in_trade:
                    exit_reason = f"Time-Based ({bars_in_trade} bars)"
            
            if exit_reason:
                self.position.close()
                print(f"🌙 Moon Dev: {exit_reason} Exit {'Long' if is_long else 'Short'} at {close} 🚀 RSI: {rsi:.2f}")
                self.entry_time = None  # Reset entry time on exit
                return
        
        # Entry logic only if no position
        if not self.position:
            # Common filters for quality setups
            high_vol = vol > vol_sma
            high_atr = atr > atr_sma
            ranging_market = adx < self.adx_threshold
            
            # Long entry - tightened with filters for better uptrend reversion
            if (close <= lower and rsi < self.rsi_oversold and close > sma200 and
                high_vol and high_atr and ranging_market):
                sl = close - (self.atr_mult * atr)
                sl_dist = close - sl
                risk = self.equity * self.risk_percent
                size = risk / sl_dist  # 🌙 Moon Dev: Use float for precise fractional sizing, no int rounding
                # 🌙 Moon Dev: Cap size to prevent overexposure (max 10% of equity)
                max_size = 0.1 * self.equity / close
                size = min(size, max_size)
                
                self.buy(size=size, sl=sl)  # 🌙 Moon Dev: No fixed TP - use dynamic exit for adaptability
                self.entry_time = current_time
                print(f"🌙 Moon Dev: Entering Long at {close}, Size: {size:.4f}, SL: {sl:.2f}, RSI: {rsi:.2f}, ATR: {atr:.2f}, ADX: {adx:.2f} 🚀")
            
            # Short entry - tightened with filters for better downtrend reversion
            elif (close >= upper and rsi > self.rsi_overbought and close < sma200 and
                  high_vol and high_atr and ranging_market):
                sl = close + (self.atr_mult * atr)
                sl_dist = sl - close
                risk = self.equity * self.risk_percent
                size = risk / sl_dist  # 🌙 Moon Dev: Use float for precise fractional sizing
                # 🌙 Moon Dev: Cap size to prevent overexposure
                max_size = 0.1 * self.equity / close
                size = min(size, max_size)
                
                self.sell(size=size, sl=sl)  # 🌙 Moon Dev: No fixed TP - use dynamic exit
                self.entry_time = current_time
                print(f"🌙 Moon Dev: Entering Short at {close}, Size: {size:.4f}, SL: {sl:.2f}, RSI: {rsi:.2f}, ATR: {atr:.2f}, ADX: {adx:.2f} ✨")

# Run backtest
bt = Backtest(data, AdaptiveReversion, cash=1000000, commission=0.001)
stats = bt.run()
print(stats)