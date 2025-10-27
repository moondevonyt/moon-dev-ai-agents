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
    # 🌙 Moon Dev Optimization Notes:
    # - Tightened RSI thresholds to <25 (long) / >75 (short) for stronger oversold/overbought signals
    # - Added EMA(50) trend filter: Long only if Close > EMA50, Short only if Close < EMA50 to align with market regime
    # - Added volume filter: Entry only if current Volume > SMA(Volume, 20) to confirm momentum
    # - Replaced fixed 1% SL buffer with ATR(14)-based SL (2 * ATR) for volatility-adjusted risk
    # - Increased risk per trade to 2% of equity for higher returns while maintaining sizing
    # - Added fixed TP at 2:1 RR (4 * ATR reward for 2 * ATR risk) for better profit capture
    # - Implemented manual exit checks for SL, TP, and original Middle BB to combine dynamic and fixed exits
    # - Position size now float for precision (no int rounding) - realistic for crypto
    # - Increased init length check to 50 for new indicators (EMA50)
    # - These changes aim for higher returns by filtering quality setups and optimizing RR without curve-fitting

    def init(self):
        self.bb_upper, self.bb_middle, self.bb_lower = self.I(
            talib.BBANDS, self.data.Close, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0
        )
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14)
        # 🌙 Added ATR for volatility-based SL/TP
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        # 🌙 Added EMA50 for trend filter
        self.ema50 = self.I(talib.EMA, self.data.Close, timeperiod=50)
        # 🌙 Added volume SMA for momentum confirmation
        self.avg_vol = self.I(talib.SMA, self.data.Volume, timeperiod=20)
        # 🌙 Trackers for manual exits
        self.entry_price = None
        self.sl_price = None
        self.tp_price = None

    def next(self):
        if len(self.data) < 50:  # 🌙 Increased for EMA50
            return

        current_price = self.data.Close[-1]

        # 🌙 Manual exit logic for existing positions with multiple conditions
        if self.position:
            exit_reason = None
            exit_value = None
            if self.position.is_long:
                if current_price <= self.sl_price:
                    exit_reason = "SL"
                    exit_value = self.sl_price
                elif current_price >= self.tp_price:
                    exit_reason = "TP"
                    exit_value = self.tp_price
                elif current_price >= self.bb_middle[-1]:
                    exit_reason = "Middle BB"
                    exit_value = self.bb_middle[-1]
            else:  # short
                if current_price >= self.sl_price:
                    exit_reason = "SL"
                    exit_value = self.sl_price
                elif current_price <= self.tp_price:
                    exit_reason = "TP"
                    exit_value = self.tp_price
                elif current_price <= self.bb_middle[-1]:
                    exit_reason = "Middle BB"
                    exit_value = self.bb_middle[-1]

            if exit_reason:
                self.position.close()
                pos_type = "LONG" if self.position.is_long else "SHORT"
                emoji = "🚀" if self.position.is_long else "📉"
                print(f"🌙 {pos_type} EXIT at {current_price:.2f} ✨ {exit_reason}: {exit_value:.2f} {emoji}")
                # 🌙 Reset trackers
                self.entry_price = None
                self.sl_price = None
                self.tp_price = None

        # 🌙 Entry logic - no position
        else:
            sl_distance = 0
            # Long entry with optimized filters
            if (self.data.Close[-1] <= self.bb_lower[-1] and 
                self.rsi[-1] < 25 and  # 🌙 Tightened from 30
                self.data.Close[-1] > self.ema50[-1] and  # 🌙 Trend filter: uptrend only
                self.data.Volume[-1] > self.avg_vol[-1]):  # 🌙 Volume confirmation

                entry_price = self.data.Close[-1]
                atr_val = self.atr[-1]
                self.sl_price = entry_price - 2 * atr_val  # 🌙 ATR-based SL
                sl_distance = entry_price - self.sl_price
                if sl_distance > 0:
                    risk_amount = self.equity * 0.02  # 🌙 Increased to 2% risk
                    size = risk_amount / sl_distance  # 🌙 Float size for precision
                    self.tp_price = entry_price + 2 * sl_distance  # 🌙 2:1 RR TP
                    self.buy(size=size)  # 🌙 No built-in SL/TP, manual
                    self.entry_price = entry_price
                    print(f"🚀 🌙 LONG ENTRY: Price {entry_price:.2f}, SL {self.sl_price:.2f}, TP {self.tp_price:.2f}, Size {size:.4f}, RSI {self.rsi[-1]:.2f}, Lower BB {self.bb_lower[-1]:.2f}, ATR {atr_val:.2f}, EMA50 {self.ema50[-1]:.2f}, Vol {self.data.Volume[-1]:.0f} > {self.avg_vol[-1]:.0f} ✨")

            # Short entry with optimized filters
            elif (self.data.Close[-1] >= self.bb_upper[-1] and 
                  self.rsi[-1] > 75 and  # 🌙 Tightened from 70
                  self.data.Close[-1] < self.ema50[-1] and  # 🌙 Trend filter: downtrend only
                  self.data.Volume[-1] > self.avg_vol[-1]):  # 🌙 Volume confirmation

                entry_price = self.data.Close[-1]
                atr_val = self.atr[-1]
                self.sl_price = entry_price + 2 * atr_val  # 🌙 ATR-based SL
                sl_distance = self.sl_price - entry_price
                if sl_distance > 0:
                    risk_amount = self.equity * 0.02  # 🌙 Increased to 2% risk
                    size = risk_amount / sl_distance  # 🌙 Float size for precision
                    self.tp_price = entry_price - 2 * sl_distance  # 🌙 2:1 RR TP
                    self.sell(size=size)  # 🌙 No built-in SL/TP, manual
                    self.entry_price = entry_price
                    print(f"📉 🌙 SHORT ENTRY: Price {entry_price:.2f}, SL {self.sl_price:.2f}, TP {self.tp_price:.2f}, Size {size:.4f}, RSI {self.rsi[-1]:.2f}, Upper BB {self.bb_upper[-1]:.2f}, ATR {atr_val:.2f}, EMA50 {self.ema50[-1]:.2f}, Vol {self.data.Volume[-1]:.0f} > {self.avg_vol[-1]:.0f} ✨")

if __name__ == '__main__':
    bt = Backtest(data, VolatilityRebound, cash=1000000, commission=0.001, exclusive_orders=True)
    stats = bt.run()
    print(stats)