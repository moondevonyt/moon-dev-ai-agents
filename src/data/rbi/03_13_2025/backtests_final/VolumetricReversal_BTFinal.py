The code is mostly correct, but I found a few technical issues that need to be fixed. Here's the debugged version with Moon Dev themed prints:

```python
import pandas as pd
import talib
from backtesting import Backtest, Strategy

class VolumetricReversal(Strategy):
    risk_percent = 0.01  # 1% risk per trade
    
    def init(self):
        # Bollinger Bands components
        self.middle_band = self.I(talib.SMA, self.data.Close, timeperiod=20)
        self.std_dev = self.I(talib.STDDEV, self.data.Close, timeperiod=20)
        self.upper_band = self.I(lambda mid, std: mid + 2*std, self.middle_band, self.std_dev)
        self.lower_band = self.I(lambda mid, std: mid - 2*std, self.middle_band, self.std_dev)
        
        # Stochastic Oscillator
        self.stoch_k = self.I(lambda h,l,c: talib.STOCHF(h,l,c,14,3)[0], 
                            self.data.High, self.data.Low, self.data.Close)
        self.stoch_d = self.I(lambda h,l,c: talib.STOCHF(h,l,c,14,3)[1], 
                            self.data.High, self.data.Low, self.data.Close)
        
        # Volume analysis
        self.vol_sma = self.I(talib.SMA, self.data.Volume, timeperiod=20)
        
        print("🌙✨ Moon Dev Indicators Activated! BBANDS | STOCH | VOL SMA Loaded 🚀")
        print("🌌 Lunar Trading System Initialized Successfully 🌌")

    def next(self):
        if len(self.data) < 20:  # Wait for indicators to warm up
            return
            
        current_close = self.data.Close[-1]
        current_vol = self.data.Volume[-1]
        upper = self.upper_band[-1]
        lower = self.lower_band[-1]
        middle = self.middle_band[-1]
        stoch_k = self.stoch_k[-1]
        stoch_d = self.stoch_d[-1]
        vol_sma = self.vol_sma[-1]
        
        # Moon Dev Volume Spike Detection 🌊
        vol_spike = current_vol > 1.5 * vol_sma if vol_sma else False
        
        if not self.position:
            # Long Entry: Break upper BB + volume spike + Stoch confirmation
            if (current_close > upper and vol_spike and stoch_k > 80):
                risk_amount = self.equity() * self.risk_percent
                risk_per_unit = current_close - middle
                
                if risk_per_unit > 0:
                    size = int(round(risk_amount / risk_per_unit))
                    if size > 0:
                        tp_price = current_close + (upper - lower)
                        self.buy(size=size, sl=middle, tp=tp_price)
                        print(f"🌙🚀 MOON BLASTOFF! LONG {size} units @ {current_close:.2f}")
                        print(f"   🛡️ SL: {middle:.2f} | 🎯 TP: {tp_price:.2f}")
            
            # Short Entry: Break lower BB + volume spike + Stoch confirmation
            elif (current_close < lower and vol_spike and stoch_k < 20):
                risk_amount = self.equity() * self.risk_percent
                risk_per_unit = middle - current_close
                
                if risk_per_unit > 0:
                    size = int(round(risk_amount / risk_per_unit))
                    if size > 0:
                        tp_price = current_close - (upper - lower)
                        self.sell(size=size, sl=middle, tp=tp_price)
                        print(f"🌙📉 COMET CRASH! SHORT {size} units @ {current_close:.2f}")
                        print(f"   🛡️ SL: {middle:.2f} | 🎯 TP: {tp_price:.2f}")
        else:
            # Exit on Stochastic reversal
            if self.position.is_long and stoch_k < stoch_d and stoch_k < 80:
                self.position.close()
                print(f"🌙✨ LUNAR ECLIPSE! Closing Long | K:{stoch_k:.1f} D:{stoch_d:.1f}")
            elif self.position.is_short and stoch_k > stoch_d and stoch_k > 20:
                self.position.close()
                print(f"🌙✨ STAR RECOVERY! Closing Short | K:{stoch_k:.1f} D:{stoch_d:.1f}")

# Moon Dev