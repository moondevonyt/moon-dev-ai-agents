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
    # 🌙 OPTIMIZATION: Added EMA200 for trend filter to only take longs in uptrends and shorts in downtrends - avoids counter-trend trades for higher win rate.
    # 🌙 OPTIMIZATION: Added ATR(14) for dynamic SL placement (2x ATR) instead of fixed 1% - better adapts to volatility in BTC 15m for realistic risk.
    # 🌙 OPTIMIZATION: Added Volume SMA(20) filter - only enter on above-average volume for stronger conviction signals, reducing false entries.
    # 🌙 OPTIMIZATION: Tightened RSI thresholds to <25/>75 - rarer but higher-quality oversold/overbought conditions for better rebounds.
    # 🌙 OPTIMIZATION: Increased risk per trade to 2% of equity - amplifies returns while keeping risk managed; allows float sizes for precision in crypto.
    # 🌙 OPTIMIZATION: For exits, added breakeven trail: Move SL to entry after reaching middle BB - protects profits without cutting too early.
    # 🌙 OPTIMIZATION: Added partial scale-out at middle BB (close 50%) and let remainder trail to capture bigger moves toward opposite band.
    def init(self):
        self.bb_upper, self.bb_middle, self.bb_lower = self.I(
            talib.BBANDS, self.data.Close, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0
        )
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14)
        self.ema200 = self.I(talib.EMA, self.data.Close, timeperiod=200)  # Trend filter
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=14)  # Volatility-based SL
        self.vol_sma = self.I(talib.SMA, self.data.Volume, timeperiod=20)  # Volume confirmation

    def next(self):
        if len(self.data) < 200:  # 🌙 OPTIMIZATION: Wait for EMA200 to initialize properly
            return

        # 🌙 OPTIMIZATION: Track entry price and initial SL for trailing logic
        if not hasattr(self, 'entry_price'):
            self.entry_price = None
        if not hasattr(self, 'initial_sl'):
            self.initial_sl = None
        if not hasattr(self, 'has_moved_to_be'):
            self.has_moved_to_be = False

        # Exit/Scale-out logic for existing positions with trailing
        if self.position:
            current_price = self.data.Close[-1]
            if self.position.is_long:
                # Scale out 50% at middle BB
                if not self.has_moved_to_be and current_price >= self.bb_middle[-1]:
                    self.position.close(size=self.position.size * 0.5)  # Close half
                    self.has_moved_to_be = True
                    self.initial_sl = current_price  # Move remaining SL to breakeven (entry approx)
                    print(f"🌙 LONG PARTIAL EXIT at {current_price:.2f} ✨ Scale-out Middle: {self.bb_middle[-1]:.2f}, Trailing to BE 🚀")
                
                # Trail remaining SL to breakeven or better if already scaled
                if self.has_moved_to_be and self.initial_sl is not None:
                    self.position.sl = max(self.position.sl or 0, self.entry_price)  # Breakeven trail
                
                # Full exit if hits opposite band or strong RSI (to capture full rebound)
                if current_price >= self.bb_upper[-1] or self.rsi[-1] > 75:
                    self.position.close()
                    print(f"🌙 LONG FULL EXIT at {current_price:.2f} ✨ TP Upper/RSI: {self.bb_upper[-1]:.2f}/{self.rsi[-1]:.2f} 🚀")
            
            elif self.position.is_short:
                # Scale out 50% at middle BB
                if not self.has_moved_to_be and current_price <= self.bb_middle[-1]:
                    self.position.close(size=self.position.size * 0.5)  # Close half (note: size positive for short)
                    self.has_moved_to_be = True
                    self.initial_sl = current_price  # Move remaining SL to breakeven
                    print(f"🌙 SHORT PARTIAL EXIT at {current_price:.2f} ✨ Scale-out Middle: {self.bb_middle[-1]:.2f}, Trailing to BE 📉")
                
                # Trail remaining SL to breakeven or better
                if self.has_moved_to_be and self.initial_sl is not None:
                    self.position.sl = min(self.position.sl or float('inf'), self.entry_price)  # Breakeven trail for short
                
                # Full exit if hits opposite band or strong RSI
                if current_price <= self.bb_lower[-1] or self.rsi[-1] < 25:
                    self.position.close()
                    print(f"🌙 SHORT FULL EXIT at {current_price:.2f} ✨ TP Lower/RSI: {self.bb_lower[-1]:.2f}/{self.rsi[-1]:.2f} 📉")

        # Entry logic - no position
        else:
            # Reset flags for new entry
            self.has_moved_to_be = False
            current_price = self.data.Close[-1]
            vol_confirm = self.data.Volume[-1] > self.vol_sma[-1]

            # Long entry with optimizations
            if (current_price <= self.bb_lower[-1] and 
                self.rsi[-1] < 25 and 
                current_price > self.ema200[-1] and  # Uptrend filter
                vol_confirm):  # Volume filter

                self.entry_price = current_price
                atr_value = self.atr[-1]
                sl_price = current_price - 2 * atr_value  # Dynamic SL
                sl_distance = current_price - sl_price
                if sl_distance > 0:
                    risk_amount = self.equity * 0.02  # 2% risk
                    size = risk_amount / sl_distance  # Float for precision
                    self.buy(size=size, sl=sl_price)
                    print(f"🚀 🌙 LONG ENTRY: Price {current_price:.2f}, SL {sl_price:.2f}, Size {size:.4f}, RSI {self.rsi[-1]:.2f}, Lower BB {self.bb_lower[-1]:.2f}, ATR {atr_value:.2f}, Vol Confirm ✨")

            # Short entry with optimizations
            elif (current_price >= self.bb_upper[-1] and 
                  self.rsi[-1] > 75 and 
                  current_price < self.ema200[-1] and  # Downtrend filter
                  vol_confirm):  # Volume filter

                self.entry_price = current_price
                atr_value = self.atr[-1]
                sl_price = current_price + 2 * atr_value  # Dynamic SL
                sl_distance = sl_price - current_price
                if sl_distance > 0:
                    risk_amount = self.equity * 0.02  # 2% risk
                    size = risk_amount / sl_distance  # Float for precision
                    self.sell(size=size, sl=sl_price)
                    print(f"📉 🌙 SHORT ENTRY: Price {current_price:.2f}, SL {sl_price:.2f}, Size {size:.4f}, RSI {self.rsi[-1]:.2f}, Upper BB {self.bb_upper[-1]:.2f}, ATR {atr_value:.2f}, Vol Confirm ✨")

if __name__ == '__main__':
    bt = Backtest(data, VolatilityRebound, cash=1000000, commission=0.001, exclusive_orders=True)
    stats = bt.run()
    print(stats)