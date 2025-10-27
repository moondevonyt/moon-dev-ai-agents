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
    # 🌙 MOON DEV OPTIMIZATION: Added ATR for dynamic SL/TP, SMA Volume for filter, ADX for ranging market filter (<25 to favor mean reversion)
    # Increased risk per trade to 2% for higher exposure, RR 1:2 for better profit potential, allow fractional sizes, tightened BB to 2.0 std (slight adjustment for sensitivity)
    # Entry now requires volume >1.2x 20-period avg and ADX<25 to avoid trends/chop, manual SL/TP checks using OHLC for realistic hit detection
    # Removed fixed % SL beyond bands, using ATR*1.5 for volatility-adjusted stops to improve risk management without curve-fitting
    def init(self):
        # Core indicators with slight tune: BB std dev 2.0 for balanced band width
        self.bb_upper, self.bb_middle, self.bb_lower = self.I(
            talib.BBANDS, self.data.Close, timeperiod=20, nbdevup=2.0, nbdevdn=2.0, matype=0
        )
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14)
        
        # New: ATR for volatility-based SL/TP (14-period standard)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        
        # New: Volume filter using 20-period SMA
        self.sma_vol = self.I(talib.SMA, self.data.Volume, timeperiod=20)
        
        # New: ADX to filter for ranging markets (low ADX favors rebound setups)
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        
        # Track position details for manual SL/TP
        self.sl = 0
        self.tp = 0
        self.position_is_long = None

    def next(self):
        if len(self.data) < 20:
            return

        # 🌙 MOON DEV OPTIMIZATION: Manual exit checks using bar OHLC to simulate intra-bar hits for SL/TP
        # This replaces fixed middle BB exit with dynamic RR-based TP (1:2), while preserving SL for risk control
        if self.position:
            exit_triggered = False
            if self.position_is_long is True:
                # Long position: Check SL on low, TP on high
                sl_hit = self.data.Low[-1] <= self.sl
                tp_hit = self.data.High[-1] >= self.tp
                if sl_hit or tp_hit:
                    self.position.close()
                    exit_price = self.data.Close[-1]  # Approximate exit at close; in live, would be at SL/TP level
                    if tp_hit:
                        print(f"🌙 LONG TP EXIT at {exit_price:.2f} ✨ TP: {self.tp:.2f} 🚀")
                    else:
                        print(f"🌙 LONG SL EXIT at {exit_price:.2f} ✨ SL: {self.sl:.2f} 🚨")
                    self.position_is_long = None
                    exit_triggered = True
            elif self.position_is_long is False:
                # Short position: Check SL on high, TP on low
                sl_hit = self.data.High[-1] >= self.sl
                tp_hit = self.data.Low[-1] <= self.tp
                if sl_hit or tp_hit:
                    self.position.close()
                    exit_price = self.data.Close[-1]  # Approximate exit at close
                    if tp_hit:
                        print(f"🌙 SHORT TP EXIT at {exit_price:.2f} ✨ TP: {self.tp:.2f} 📉")
                    else:
                        print(f"🌙 SHORT SL EXIT at {exit_price:.2f} ✨ SL: {self.sl:.2f} 🚨")
                    self.position_is_long = None
                    exit_triggered = True

        # Entry logic - only if no position
        if not self.position:
            risk_per_trade = 0.02  # 🌙 Increased from 0.01 for higher returns while maintaining risk (equity-based)
            
            # Long entry with tightened filters
            if (self.data.Close[-1] <= self.bb_lower[-1] and 
                self.rsi[-1] < 30 and 
                self.data.Volume[-1] > 1.2 * self.sma_vol[-1] and 
                self.adx[-1] < 25):
                
                entry_price = self.data.Close[-1]
                atr_val = self.atr[-1]
                self.sl = entry_price - 1.5 * atr_val  # 🌙 ATR-based SL for better volatility adjustment
                sl_distance = entry_price - self.sl
                self.tp = entry_price + 2 * sl_distance  # 🌙 1:2 RR for improved profit capture
                risk_amount = self.equity * risk_per_trade
                size = risk_amount / sl_distance  # 🌙 Allow fractional size for precise risk (no int rounding)
                self.buy(size=size)  # No sl/tp in order; handled manually
                self.position_is_long = True
                print(f"🚀 🌙 LONG ENTRY: Price {entry_price:.2f}, SL {self.sl:.2f}, TP {self.tp:.2f}, Size {size}, RSI {self.rsi[-1]:.2f}, Lower BB {self.bb_lower[-1]:.2f}, Vol {self.data.Volume[-1]:.0f} > {1.2 * self.sma_vol[-1]:.0f}, ADX {self.adx[-1]:.2f} ✨")

            # Short entry with tightened filters (symmetric)
            elif (self.data.Close[-1] >= self.bb_upper[-1] and 
                  self.rsi[-1] > 70 and 
                  self.data.Volume[-1] > 1.2 * self.sma_vol[-1] and 
                  self.adx[-1] < 25):
                
                entry_price = self.data.Close[-1]
                atr_val = self.atr[-1]
                self.sl = entry_price + 1.5 * atr_val  # 🌙 ATR-based SL
                sl_distance = self.sl - entry_price
                self.tp = entry_price - 2 * sl_distance  # 🌙 1:2 RR
                risk_amount = self.equity * risk_per_trade
                size = risk_amount / sl_distance  # 🌙 Fractional size
                self.sell(size=size)  # No sl/tp in order
                self.position_is_long = False
                print(f"📉 🌙 SHORT ENTRY: Price {entry_price:.2f}, SL {self.sl:.2f}, TP {self.tp:.2f}, Size {size}, RSI {self.rsi[-1]:.2f}, Upper BB {self.bb_upper[-1]:.2f}, Vol {self.data.Volume[-1]:.0f} > {1.2 * self.sma_vol[-1]:.0f}, ADX {self.adx[-1]:.2f} ✨")

if __name__ == '__main__':
    bt = Backtest(data, VolatilityRebound, cash=1000000, commission=0.001, exclusive_orders=True)
    stats = bt.run()
    print(stats)