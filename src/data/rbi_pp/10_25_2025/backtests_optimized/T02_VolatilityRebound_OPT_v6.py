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
    # 🌙 OPTIMIZATION: Added ATR for dynamic stop loss and position sizing based on volatility
    #                 Added EMA200 for trend filter to avoid counter-trend trades
    #                 Added Volume SMA for confirmation of strong moves
    #                 Tightened RSI thresholds to 25/75 for higher quality signals
    #                 Increased risk per trade to 1.5% for higher returns while maintaining control
    #                 Used 1.5*ATR for SL and 3*ATR for TP (1:2 risk-reward ratio) for better exits
    #                 Removed manual middle BB exit; now using built-in SL/TP for automatic handling
    #                 Position size as float for precision in crypto trading
    #                 Added len check for EMA200 to ensure valid signals
    def init(self):
        self.bb_upper, self.bb_middle, self.bb_lower = self.I(
            talib.BBANDS, self.data.Close, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0
        )
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14)
        # 🌙 NEW: ATR for volatility-based risk management
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        # 🌙 NEW: EMA200 for trend filter (only long above, short below)
        self.ema200 = self.I(talib.EMA, self.data.Close, timeperiod=200)
        # 🌙 NEW: Volume SMA to filter for high-volume rebounds
        self.vol_sma = self.I(talib.SMA, self.data.Volume, timeperiod=20)

    def next(self):
        # 🌙 OPTIMIZATION: Ensure sufficient data for all indicators (esp. EMA200)
        if len(self.data) < 200:
            return

        # Entry logic - no position
        if not self.position:
            atr_val = self.atr[-1]
            if np.isnan(atr_val) or atr_val == 0:
                return

            sl_distance = 1.5 * atr_val  # 🌙 Dynamic SL distance based on ATR
            risk_amount = self.equity * 0.015  # 🌙 Increased to 1.5% risk for higher returns

            # Long entry with tightened conditions and filters
            if (self.data.Close[-1] <= self.bb_lower[-1] and
                self.rsi[-1] < 25 and  # 🌙 Tightened from 30
                self.data.Close[-1] > self.ema200[-1] and  # 🌙 Trend filter: bullish regime
                self.data.Volume[-1] > self.vol_sma[-1]):  # 🌙 Volume confirmation

                entry_price = self.data.Close[-1]
                sl_price = entry_price - sl_distance
                tp_price = entry_price + 2 * sl_distance  # 🌙 1:2 RR for improved profitability
                size = risk_amount / sl_distance  # 🌙 Float size for precision, no rounding to int
                if size > 0:
                    self.buy(size=size, sl=sl_price, tp=tp_price)
                    print(f"🚀 🌙 LONG ENTRY: Price {entry_price:.2f}, SL {sl_price:.2f}, TP {tp_price:.2f}, Size {size:.4f}, RSI {self.rsi[-1]:.2f}, Lower BB {self.bb_lower[-1]:.2f}, ATR {atr_val:.2f} ✨")

            # Short entry with tightened conditions and filters
            elif (self.data.Close[-1] >= self.bb_upper[-1] and
                  self.rsi[-1] > 75 and  # 🌙 Tightened from 70
                  self.data.Close[-1] < self.ema200[-1] and  # 🌙 Trend filter: bearish regime
                  self.data.Volume[-1] > self.vol_sma[-1]):  # 🌙 Volume confirmation

                entry_price = self.data.Close[-1]
                sl_price = entry_price + sl_distance
                tp_price = entry_price - 2 * sl_distance  # 🌙 1:2 RR for improved profitability
                size = risk_amount / sl_distance  # 🌙 Float size for precision, no rounding to int
                if size > 0:
                    self.sell(size=size, sl=sl_price, tp=tp_price)
                    print(f"📉 🌙 SHORT ENTRY: Price {entry_price:.2f}, SL {sl_price:.2f}, TP {tp_price:.2f}, Size {size:.4f}, RSI {self.rsi[-1]:.2f}, Upper BB {self.bb_upper[-1]:.2f}, ATR {atr_val:.2f} ✨")

if __name__ == '__main__':
    bt = Backtest(data, VolatilityRebound, cash=1000000, commission=0.001, exclusive_orders=True)
    stats = bt.run()
    print(stats)