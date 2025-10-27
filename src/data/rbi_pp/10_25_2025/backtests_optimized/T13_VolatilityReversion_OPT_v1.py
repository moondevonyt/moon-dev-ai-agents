import talib
from backtesting import Backtest, Strategy
import pandas as pd
import numpy as np

class VolatilityReversion(Strategy):
    bb_period = 20
    bb_std = 2.0  # 🌙 Moon Dev: Kept at 2.0 for balanced band width; wider (e.g., 2.5) reduces signals, narrower increases noise
    rsi_period = 14
    adx_period = 14
    rsi_low = 25  # 🌙 Moon Dev: Tightened from 30 to 25 for more extreme oversold conditions, improving entry quality
    rsi_high = 75  # 🌙 Moon Dev: Tightened from 70 to 75 for more extreme overbought conditions
    adx_max = 20  # 🌙 Moon Dev: Reduced from 25 to 20 to focus on stronger ranging (low trend) regimes, avoiding weak trends
    risk_pct = 0.02  # 🌙 Moon Dev: Increased from 0.01 to 0.02 to amplify returns while monitoring drawdown; balances aggression with risk
    atr_period = 14  # 🌙 Moon Dev: New ATR period for volatility-based stops and sizing

    def init(self):
        bb = self.I(talib.BBANDS, self.data.Close, timeperiod=self.bb_period,
                    nbdevup=self.bb_std, nbdevdn=self.bb_std, matype=0)
        self.bb_upper = bb[0]
        self.bb_middle = bb[1]
        self.bb_lower = bb[2]
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=self.rsi_period)
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=self.adx_period)
        # 🌙 Moon Dev: Added ATR for dynamic, volatility-adjusted stop losses and position sizing to better handle varying market conditions
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=self.atr_period)
        # 🌙 Moon Dev: Added volume SMA filter to confirm entries with above-average volume, avoiding low-conviction setups
        self.vol_sma = self.I(talib.SMA, self.data.Volume, timeperiod=20)
        # 🌙 Moon Dev: Added 200-period SMA as a trend filter; only long above it (bull bias for BTC), short below to align with regime and reduce counter-trend losses
        self.sma200 = self.I(talib.SMA, self.data.Close, timeperiod=200)
        print("🌙 Moon Dev: Indicators initialized for VolatilityReversion strategy ✨")

    def next(self):
        current_close = self.data.Close[-1]
        
        # Exit logic - unchanged: Revert to middle band for mean reversion capture
        if self.position:
            if self.position.is_long and current_close > self.bb_middle[-1]:
                self.position.close()
                print(f"🌙 Moon Dev: Exiting long position at {current_close:.2f} - Reversion to middle band achieved! ✨")
            elif self.position.is_short and current_close < self.bb_middle[-1]:
                self.position.close()
                print(f"🌙 Moon Dev: Exiting short position at {current_close:.2f} - Reversion to middle band achieved! ✨")
        
        # Entry logic
        if not self.position:
            risk_amount = self.equity * self.risk_pct
            atr = self.atr[-1]
            vol_confirm = self.data.Volume[-1] > self.vol_sma[-1]
            trend_long = current_close > self.sma200[-1]
            trend_short = current_close < self.sma200[-1]
            
            # Long entry - Added volume and trend filters for higher-quality setups
            if (current_close < self.bb_lower[-1] and
                self.rsi[-1] < self.rsi_low and
                self.adx[-1] < self.adx_max and
                vol_confirm and
                trend_long):
                
                stop_price = current_close - 2 * atr  # 🌙 Moon Dev: Volatility-based SL (2x ATR below entry) for tighter, adaptive risk control vs. fixed band extension
                entry_price = current_close
                stop_distance = entry_price - stop_price
                
                if stop_distance > 0:
                    size = risk_amount / stop_distance
                    if size > 0:
                        self.buy(size=size, sl=stop_price)  # 🌙 Moon Dev: Removed int(round()) for precise fractional sizing in BTC
                        print(f"🚀 Moon Dev: Long entry at {entry_price:.2f}, size {size:.6f} BTC, stop {stop_price:.2f}, risk {risk_amount:.2f} USD 🌙")
            
            # Short entry - Added volume and trend filters for higher-quality setups
            elif (current_close > self.bb_upper[-1] and
                  self.rsi[-1] > self.rsi_high and
                  self.adx[-1] < self.adx_max and
                  vol_confirm and
                  trend_short):
                
                stop_price = current_close + 2 * atr  # 🌙 Moon Dev: Volatility-based SL (2x ATR above entry)
                entry_price = current_close
                stop_distance = stop_price - entry_price
                
                if stop_distance > 0:
                    size = risk_amount / stop_distance
                    if size > 0:
                        self.sell(size=size, sl=stop_price)  # 🌙 Moon Dev: Removed int(round()) for precise fractional sizing
                        print(f"🚀 Moon Dev: Short entry at {entry_price:.2f}, size {size:.6f} BTC, stop {stop_price:.2f}, risk {risk_amount:.2f} USD 🌙")

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