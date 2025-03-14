I'll help fix the code by removing all `backtesting.lib` imports and replacing crossover/crossunder functions with proper implementations. Here's the corrected version with Moon Dev themed debug prints:

```python
import pandas as pd
import talib
from backtesting import Backtest, Strategy

class VolumetricDivergenceStrategy(Strategy):
    risk_per_trade = 0.01  # 1% risk per trade
    rr_ratio = 2  # 1:2 risk-reward ratio
    
    def init(self):
        # Clean and prepare data
        self.data.columns = [col.strip().lower() for col in self.data.columns]
        self.data.drop(columns=[col for col in self.data.columns if 'unnamed' in col], errors='ignore', inplace=True)
        
        # Calculate indicators using TA-Lib wrapped in self.I()
        close = self.data.Close
        volume = self.data.Volume
        
        # Volume Oscillator (14-28 SMA difference)
        sma14 = talib.SMA(volume, timeperiod=14)
        sma28 = talib.SMA(volume, timeperiod=28)
        self.volume_osc = self.I(lambda: sma14 - sma28, name='Volume Oscillator')
        self.vo_signal = self.I(talib.SMA, self.volume_osc, 9, name='VO Signal')
        
        # RSI and MACD
        self.rsi = self.I(talib.RSI, close, 14, name='RSI')
        macd, macd_signal, macd_hist = talib.MACD(close, 12, 26, 9)
        self.macd_hist = self.I(lambda: macd_hist, name='MACD Hist')
        
        # Swing high/low using rolling window
        self.swing_high = self.I(talib.MAX, self.data.High, 20, name='Swing High')
        self.swing_low = self.I(talib.MIN, self.data.Low, 20, name='Swing Low')
        
    def next(self):
        if len(self.data) < 30:  # Ensure enough data points
            return
            
        # Moon Dev Debug Prints 🌙
        print(f"\n🌙 Moon Dev Status Bar [{self.data.index[-1]}]")
        print(f"✨ Price: {self.data.Close[-1]} | VO: {self.volume_osc[-1]:.2f} | RSI: {self.rsi[-1]:.2f}")
        
        entry_price = self.data.Close[-1]
        current_position = self.position
        
        # Bullish Divergence Check
        bull_div = (
            (self.data.Low[-1] < self.data.Low[-2]) and
            (self.volume_osc[-1] > self.volume_osc[-2]) and
            (self.volume_osc[-2] < self.vo_signal[-2] and self.volume_osc[-1] > self.vo_signal[-1]) and  # Bullish crossover replacement
            (self.rsi[-1] > 30) and
            (self.macd_hist[-1] > 0)
        )
        
        # Bearish Divergence Check
        bear_div = (
            (self.data.High[-1] > self.data.High[-2]) and
            (self.volume_osc[-1] < self.volume_osc[-2]) and
            (self.volume_osc[-2] > self.vo_signal[-2] and self.volume_osc[-1] < self.vo_signal[-1]) and  # Bearish crossunder replacement
            (self.rsi[-1] < 70) and
            (self.macd_hist[-1] < 0)
        )
        
        # Risk Management Calculations
        equity = self.equity
        risk_amount = equity * self.risk_per_trade
        
        # Entry Logic with Moon Dev Flair 🌙🚀
        if not current_position:
            if bull_div:
                sl_price = entry_price * 0.99  # 1% stop loss
                tp_price = entry_price + (entry_price - sl_price) * self.rr_ratio
                position_size = int(round(risk_amount / (entry_price - sl_price)))
                
                if position_size > 0:
                    self.buy(size=position_size, sl=sl_price, tp=tp_price)
                    print(f"🚀 BULLISH DIVERGENCE DETECTED! Long {position_size} @ {entry_price}")
                    print(f"   SL: {sl_price:.2f} | TP: {tp_price:.2f}")
                    
            elif bear_div: