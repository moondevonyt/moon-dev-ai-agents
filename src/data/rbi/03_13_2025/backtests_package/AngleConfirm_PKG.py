# 🌙 MOON DEV BACKTESTING IMPLEMENTATION 🌙
import pandas as pd
import talib
import numpy as np
from scipy.signal import convolve2d

class AngleConfirm(Strategy):
    risk_percent = 0.01  # 1% risk per trade 
    stop_loss_pct = 0.005  # 0.5% stop loss 
    rr_ratio = 2  # Risk-reward ratio 

    def init(self):
        # 🌟 Gann Angle Indicators 🌟
        self.short_gann = self.I(talib.SMA, self.data.Close, 20, name='Short Gann')
        self.long_gann = self.I(talib.SMA, self.data.Close, 50, name='Long Gann')
        
        # 🎯 5-period SMA for trend confirmation 
        self.sma5 = self.I(talib.SMA, self.data.Close, 5, name='5 SMA')
        
        print("🌙✨ MOON DEV INDICATORS INITIALIZED ✨🌙")

    def next(self):
        # Wait for enough historical data 
        if len(self.short_gann) < 2 or len(self.sma5) < 2:
            return

        # 🌙 Trend confirmation checks 
        sma5_up = self.sma5[-1] > self.sma5[-2]
        sma5_down = self.sma5[-1] < self.sma5[-2]

        if not self.position:
            # 🚀 LONG ENTRY: Gann crossover + SMA5 up 
            if (self.short_gann[-2] < self.long_gann[-2] and self.short_gann[-1] > self.long_gann[-1]) and sma5_up:
                self.enter_trade(direction='long')
                
            # 🌧️ SHORT ENTRY: Gann crossunder + SMA5 down 
            elif (self.short_gann[-2] > self.long_gann[-2] and self.short_gann[-1] < self.long_gann[-1]) and sma5_down:
                self.enter_trade(direction='short')

    def enter_trade(self, direction):
        entry_price = self.data.Close[-1]
        risk_amount = self.equity * self.risk_percent
        
        if direction == 'long':
            sl_price = entry_price * (1 - self.stop_loss_pct)
            tp_price = entry_price * (1 + self.stop_loss_pct * self.rr_ratio)
            risk_distance = entry_price - sl_price
        else:
            sl_price = entry_price * (1 + self.stop_loss_pct)
            tp_price = entry_price * (1 - self.stop_loss_pct * self.rr_ratio)
            risk_distance = sl_price - entry_price

        if risk_distance <= 0:
            print("🌙⚠️ MOON DEV RISK CALCULATION ERROR ⚠️🌙")
            return

        position_size = int(round(risk_amount / risk_distance))
        
        if position_size <= 0:
            print(f"🌙⚠️ INVALID POSITION SIZE: {position_size} ⚠️🌙")
            return

        if direction == 'long':
            self.buy(size=position_size, sl=sl_price, tp=tp_price)
            print(f"🌙🚀 BULLISH ANGLE CONFIRMATION 🚀🌙 | Entry: {entry_price:.2f} | Size: {position_size} | SL: {sl_price:.2f} | TP: {tp_price:.2f}")
        else:
            self.sell(size=position_size, sl=sl_price, tp=tp_price)
            print(f"🌙🌧️ BEARISH ANGLE CONFIRMATION 🌧️🌙 | Entry: {entry_price:.2f} | Size: {position_size} | SL: {sl_price:.2f} | TP: {tp_price:.2f}")

    def notify_trade(self, trade):
        if trade.is_closed:
            profit = trade.pl_pct
            emoji = "🚀🌙 PROFIT MOONSHOT 🌙🚀" if profit > 0 else "🌧️🌙 RAIN CHECK 🌙🌧️"
            print(f"{emoji} | PnL: ${trade.pl:.2f} | Return: {profit:.2%}")

# 🌟 DATA PREPARATION 🌟
data = pd.read_csv('/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv')

# 