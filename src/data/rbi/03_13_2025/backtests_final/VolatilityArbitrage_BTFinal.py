# 🌙 MOON DEV BACKTESTING IMPLEMENTATION FOR VOLATILITY ARBITRAGE STRATEGY 🚀

import pandas as pd
import talib
from backtesting import Backtest, Strategy

# 🌌 DATA PREPARATION
data = pd.read_csv('/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv')
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data = data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
})

class VolatilityArbitrage(Strategy):
    risk_percent = 0.01  # 1% risk per trade 🌕
    atr_period = 14
    sma_period = 50
    entry_ratio = 1.2  # Entry when volatility ratio exceeds ±20% 🌗
    stop_loss_multiplier = 2

    def init(self):
        # 🌠 VOLATILITY INDICATORS
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, self.atr_period)
        self.atr_sma = self.I(talib.SMA, self.atr, timeperiod=self.sma_period)
        
        # ✨ MEAN REVERSION RATIO
        self.vol_ratio = self.I(lambda: self.atr/self.atr_sma if self.atr_sma != 0 else 1)

    def next(self):
        price = self.data.Close[-1]
        equity = self.equity
        
        # 🌑 CALCULATE CURRENT VOLATILITY RATIO
        current_ratio = self.vol_ratio[-1]
        atr_value = self.atr[-1]
        
        # 🛑 RISK MANAGEMENT CALCULATIONS
        stop_loss_distance = self.stop_loss_multiplier * atr_value
        risk_amount = equity * self.risk_percent
        position_size = int(round(risk_amount / stop_loss_distance))

        if not self.position:
            # 🚀 ENTRY LOGIC: VOLATILITY DISCREPANCY DETECTED
            if current_ratio > self.entry_ratio:
                stop_price = price + stop_loss_distance
                if position_size > 0:
                    self.sell(size=position_size, sl=stop_price)
                    print(f"🌘 MOONSHOT SHORT! {position_size} units @ {price:.2f} | SL: {stop_price:.2f} 🌗")
                    
            elif current_ratio < (1/self.entry_ratio):
                stop_price = price - stop_loss_distance
                if position_size > 0:
                    self.buy(size=position_size, sl=stop_price)
                    print(f"🌖 LUNAR LONG! {position_size} units @ {price:.2f} | SL: {stop_price:.2f} 🌔")
        else:
            # 🌕 EXIT LOGIC: MEAN REVERSION ACHIEVED
            if (self.position.is_short and current_ratio < 1) or \
               (self.position.is_long and current_ratio > 1):
                self.position.close()
                print(f"🌑 MOON CYCLE COMPLETE! Closing position @ {price:.2f} 🌓")

# 🚀 BACKTEST EXECUTION
bt = Backtest(data, VolatilityArbitrage, cash=1_000_000, commission=.002)
stats = bt.run()

# 🌕 PRINT FULL STATS
print("\n" + "="*55 + " MOON DEV FINAL STATS " + "="*55)
print(stats)
print(stats._strategy)
print("="*140 + "\n")