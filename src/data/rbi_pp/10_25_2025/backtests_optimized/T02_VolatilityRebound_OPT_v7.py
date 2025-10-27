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
        # Original indicators
        self.bb_upper, self.bb_middle, self.bb_lower = self.I(
            talib.BBANDS, self.data.Close, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0
        )
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14)
        
        # 🌙 OPTIMIZATION: Added EMA200 for trend filter to only trade in direction of longer-term trend (long above EMA, short below)
        self.ema200 = self.I(talib.EMA, self.data.Close, timeperiod=200)
        
        # 🌙 OPTIMIZATION: Added ATR for volatility-based SL/TP placement (1.5x ATR for SL, 3x ATR for TP -> 2:1 RR for better profit potential)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        
        # 🌙 OPTIMIZATION: Added volume SMA filter to confirm entries with above-average volume (>1.2x avg) for higher quality signals
        self.avg_vol = self.I(talib.SMA, self.data.Volume, timeperiod=20)

    def next(self):
        # 🌙 OPTIMIZATION: Increased lookback to 200 for EMA200 initialization
        if len(self.data) < 200:
            return

        # 🌙 OPTIMIZATION: Removed manual exit at BB middle to allow profits to run to TP (2:1 RR); SL/TP now handle exits dynamically

        # Entry logic - no position
        if not self.position:
            entry_price = self.data.Close[-1]
            
            # Long entry with tightened filters
            if (self.data.Close[-1] <= self.bb_lower[-1] and 
                self.rsi[-1] < 30 and  # Kept original RSI threshold; could tighten to 25 if needed
                self.data.Close[-1] > self.ema200[-1] and  # Trend filter: only long in uptrend
                self.data.Volume[-1] > 1.2 * self.avg_vol[-1]):  # Volume confirmation
                
                sl_price = entry_price - 1.5 * self.atr[-1]  # ATR-based SL for better risk management
                tp_price = entry_price + 3.0 * self.atr[-1]  # 2:1 RR TP for higher returns
                sl_distance = entry_price - sl_price
                if sl_distance > 0:
                    # 🌙 OPTIMIZATION: Increased risk to 1.5% equity for higher position sizes and potential returns (still controlled)
                    risk_amount = self.equity * 0.015
                    size = risk_amount / sl_distance
                    size = int(round(size))
                    if size > 0:
                        self.buy(size=size, sl=sl_price, tp=tp_price)
                        print(f"🚀 🌙 LONG ENTRY: Price {entry_price:.2f}, SL {sl_price:.2f}, TP {tp_price:.2f}, Size {size}, RSI {self.rsi[-1]:.2f}, ATR {self.atr[-1]:.2f}, Lower BB {self.bb_lower[-1]:.2f} ✨")

            # Short entry with tightened filters
            elif (self.data.Close[-1] >= self.bb_upper[-1] and 
                  self.rsi[-1] > 70 and  # Kept original RSI threshold; could tighten to 75 if needed
                  self.data.Close[-1] < self.ema200[-1] and  # Trend filter: only short in downtrend
                  self.data.Volume[-1] > 1.2 * self.avg_vol[-1]):  # Volume confirmation
                
                sl_price = entry_price + 1.5 * self.atr[-1]  # ATR-based SL
                tp_price = entry_price - 3.0 * self.atr[-1]  # 2:1 RR TP
                sl_distance = sl_price - entry_price
                if sl_distance > 0:
                    # 🌙 OPTIMIZATION: Increased risk to 1.5% equity for higher position sizes and potential returns (still controlled)
                    risk_amount = self.equity * 0.015
                    size = risk_amount / sl_distance
                    size = int(round(size))
                    if size > 0:
                        self.sell(size=size, sl=sl_price, tp=tp_price)
                        print(f"📉 🌙 SHORT ENTRY: Price {entry_price:.2f}, SL {sl_price:.2f}, TP {tp_price:.2f}, Size {size}, RSI {self.rsi[-1]:.2f}, ATR {self.atr[-1]:.2f}, Upper BB {self.bb_upper[-1]:.2f} ✨")

if __name__ == '__main__':
    bt = Backtest(data, VolatilityRebound, cash=1000000, commission=0.001, exclusive_orders=True)
    stats = bt.run()
    print(stats)