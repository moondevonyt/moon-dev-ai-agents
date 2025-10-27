import talib
from backtesting import Backtest, Strategy
import pandas as pd
import numpy as np

class VolatilityReversion(Strategy):
    bb_period = 20
    bb_std = 2
    rsi_period = 14
    adx_period = 14
    rsi_low = 25  # Optimized: Tightened RSI low threshold for stronger oversold signals
    rsi_high = 75  # Optimized: Tightened RSI high threshold for stronger overbought signals
    adx_max = 20  # Optimized: Reduced ADX max for even stronger ranging market filter
    risk_pct = 0.015  # Optimized: Slightly increased risk per trade to boost returns while maintaining control
    atr_mult = 2.0  # New: ATR multiplier for stop distance (volatility-based stops)
    rr = 3.0  # New: Risk-reward ratio for take profit (1:3 for better expectancy)
    vol_period = 20  # New: Volume SMA period for entry filter
    ema_period = 200  # New: EMA period for trend filter to align with market regime

    def init(self):
        bb = self.I(talib.BBANDS, self.data.Close, timeperiod=self.bb_period,
                    nbdevup=self.bb_std, nbdevdn=self.bb_std, matype=0)
        self.bb_upper = bb[0]
        self.bb_middle = bb[1]
        self.bb_lower = bb[2]
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=self.rsi_period)
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=self.adx_period)
        # Optimized: Added ATR for volatility-based stop losses and position sizing
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        # New: Added volume SMA filter to avoid low-volume false signals
        self.vol_sma = self.I(talib.SMA, self.data.Volume, timeperiod=self.vol_period)
        # New: Added EMA trend filter to only take longs in uptrend and shorts in downtrend (improves regime alignment)
        self.ema200 = self.I(talib.EMA, self.data.Close, timeperiod=self.ema_period)
        print("🌙 Moon Dev: Indicators initialized for optimized VolatilityReversion strategy (ATR, Volume, EMA added) ✨")

    def next(self):
        current_close = self.data.Close[-1]
        current_volume = self.data.Volume[-1]
        
        # No manual exit logic needed - relying on SL/TP for optimized risk management
        # (Previous reversion exit removed to allow for higher RR targets)
        
        # Entry logic
        if not self.position:
            risk_amount = self.equity * self.risk_pct
            stop_distance = self.atr_mult * self.atr[-1]
            
            if stop_distance > 0:
                size = risk_amount / stop_distance  # Optimized: Float size for precise fractional BTC positioning
                
                # Long entry - Optimized: Added volume and EMA filters for higher quality setups
                if (current_close < self.bb_lower[-1] and
                    self.rsi[-1] < self.rsi_low and
                    self.adx[-1] < self.adx_max and
                    current_volume > self.vol_sma[-1] and  # New: Volume confirmation
                    current_close > self.ema200[-1]):  # New: Uptrend filter
                    
                    entry_price = current_close
                    stop_price = entry_price - stop_distance
                    tp_price = entry_price + self.rr * stop_distance  # New: Fixed RR take profit for better returns
                    
                    if size > 0:
                        self.buy(size=size, sl=stop_price, tp=tp_price)
                        print(f"🚀 Moon Dev: Long entry at {entry_price:.2f}, size {size:.6f} BTC, stop {stop_price:.2f}, tp {tp_price:.2f}, risk {risk_amount:.2f} USD 🌙")
                
                # Short entry - Optimized: Added volume and EMA filters for higher quality setups
                elif (current_close > self.bb_upper[-1] and
                      self.rsi[-1] > self.rsi_high and
                      self.adx[-1] < self.adx_max and
                      current_volume > self.vol_sma[-1] and  # New: Volume confirmation
                      current_close < self.ema200[-1]):  # New: Downtrend filter
                    
                    entry_price = current_close
                    stop_price = entry_price + stop_distance
                    tp_price = entry_price - self.rr * stop_distance  # New: Fixed RR take profit for better returns
                    
                    if size > 0:
                        self.sell(size=size, sl=stop_price, tp=tp_price)
                        print(f"🚀 Moon Dev: Short entry at {entry_price:.2f}, size {size:.6f} BTC, stop {stop_price:.2f}, tp {tp_price:.2f}, risk {risk_amount:.2f} USD 🌙")

path = "/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv"
df = pd.read_csv(path, parse_dates=['datetime'], index_col='datetime')

# Clean column names
df.columns = df.columns.str.strip().str.lower()
df = df.drop(columns=[col for col in df.columns if 'unnamed' in col.lower()])

# Ensure proper column mapping
df = df.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
})

print(f"🌙 Moon Dev: Data loaded and cleaned. Shape: {df.shape} ✨")

bt = Backtest(df, VolatilityReversion, cash=1000000, commission=0.002, exclusive_orders=True)
stats = bt.run()
print(stats)
print(stats._strategy)
print("🌙 Moon Dev Backtest Complete! 🚀")