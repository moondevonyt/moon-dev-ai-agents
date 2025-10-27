import pandas as pd
from backtesting import Backtest, Strategy
import talib
import numpy as np

# Load and clean data
data = pd.read_csv('/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv', index_col=0, parse_dates=True)
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data = data.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'})

class VolatilityRebound(Strategy):
    def init(self):
        # Original BB and RSI
        self.bb_upper, self.bb_middle, self.bb_lower = self.I(
            talib.BBANDS, self.data.Close, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0
        )
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14)
        
        # 🌙 OPTIMIZATION: Added ATR for volatility-based SL/TP distances (1.5x ATR for SL, 2:1 RR for TP)
        # This makes stops dynamic to market volatility, improving risk-adjusted returns without fixed %.
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        
        # 🌙 OPTIMIZATION: Added volume SMA filter to enter only on above-average volume spikes (>1.2x SMA)
        # Filters out low-conviction rebounds, catching stronger momentum setups for higher win rate.
        self.vol_sma = self.I(talib.SMA, self.data.Volume, timeperiod=20)
        
        # 🌙 OPTIMIZATION: Added ADX to filter for ranging markets (ADX < 30), ideal for mean-reversion BB strategy
        # Avoids trending regimes where rebounds fail, reducing false signals and drawdowns.
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=14)

    def next(self):
        # 🌙 OPTIMIZATION: Increased buffer to max indicator period (ADX/BB/Vol ~20-30) for stability
        if len(self.data) < 30:
            return

        # 🌙 OPTIMIZATION: Removed manual exit logic; now using built-in SL/TP with 1:2 RR for consistent profit taking
        # This locks in gains dynamically based on ATR, aiming for higher returns while capping losses.

        # Entry logic - no position
        if not self.position:
            # 🌙 OPTIMIZATION: Tightened RSI to <25/>75 for stronger oversold/overbought signals
            # Added volume and ADX filters for higher-quality entries only in favorable (ranging, high-volume) conditions
            
            # Long entry
            if (self.data.Close[-1] <= self.bb_lower[-1] and 
                self.rsi[-1] < 25 and
                self.data.Volume[-1] > 1.2 * self.vol_sma[-1] and
                self.adx[-1] < 30):
                
                entry_price = self.data.Close[-1]
                atr_val = self.atr[-1]
                sl_distance = 1.5 * atr_val  # Volatility-based SL distance
                sl_price = entry_price - sl_distance
                tp_price = entry_price + 2 * sl_distance  # 1:2 RR for improved expectancy
                
                if sl_distance > 0:
                    # 🌙 OPTIMIZATION: Increased risk per trade to 2% equity for higher returns (from 1%)
                    # Position sizing remains ATR-based, but capped implicitly by equity
                    risk_amount = self.equity * 0.02
                    size = risk_amount / sl_distance
                    size = int(round(size))  # Keep as int for share-like sizing
                    self.buy(size=size, sl=sl_price, tp=tp_price)
                    print(f"🚀 🌙 LONG ENTRY: Price {entry_price:.2f}, SL {sl_price:.2f}, TP {tp_price:.2f}, Size {size}, RSI {self.rsi[-1]:.2f}, Lower BB {self.bb_lower[-1]:.2f}, ATR {atr_val:.2f}, ADX {self.adx[-1]:.2f}, Vol Filter OK ✨")

            # Short entry
            elif (self.data.Close[-1] >= self.bb_upper[-1] and 
                  self.rsi[-1] > 75 and
                  self.data.Volume[-1] > 1.2 * self.vol_sma[-1] and
                  self.adx[-1] < 30):
                
                entry_price = self.data.Close[-1]
                atr_val = self.atr[-1]
                sl_distance = 1.5 * atr_val  # Volatility-based SL distance
                sl_price = entry_price + sl_distance
                tp_price = entry_price - 2 * sl_distance  # 1:2 RR for improved expectancy
                
                if sl_distance > 0:
                    # 🌙 OPTIMIZATION: Increased risk per trade to 2% equity for higher returns (from 1%)
                    risk_amount = self.equity * 0.02
                    size = risk_amount / sl_distance
                    size = int(round(size))  # Keep as int for share-like sizing
                    self.sell(size=size, sl=sl_price, tp=tp_price)
                    print(f"📉 🌙 SHORT ENTRY: Price {entry_price:.2f}, SL {sl_price:.2f}, TP {tp_price:.2f}, Size {size}, RSI {self.rsi[-1]:.2f}, Upper BB {self.bb_upper[-1]:.2f}, ATR {atr_val:.2f}, ADX {self.adx[-1]:.2f}, Vol Filter OK ✨")

if __name__ == '__main__':
    bt = Backtest(data, VolatilityRebound, cash=1000000, commission=0.001, exclusive_orders=True)
    stats = bt.run()
    print(stats)