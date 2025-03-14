```python
# -*- coding: utf-8 -*-
import pandas as pd
import talib
from backtesting import Backtest, Strategy
from backtesting.lib import crossover

# Moon Dev Data Preparation 🌙
def prepare_data(filepath):
    # Load data with Moon Dev precision
    data = pd.read_csv(filepath)
    
    # Clean column names
    data.columns = data.columns.str.strip().str.lower()
    data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
    
    # Map to backtesting.py column names
    column_map = {
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume'
    }
    data = data.rename(columns=column_map)
    data['DateTime'] = pd.to_datetime(data['datetime'])
    data = data.set_index('DateTime').drop(columns=['datetime'])
    return data

class ReversalBandTrigger(Strategy):
    risk_per_trade = 0.01  # 1% risk per trade 🌙
    trailing_stop_multiplier = 3  # 3x ATR for trailing stop 🚀
    
    def init(self):
        # Moon Dev Indicator Setup 🌙✨
        self.close = self.data.Close
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        
        # Core Indicators
        self.sma50 = self.I(talib.SMA, self.close, timeperiod=50, name='SMA50')
        self.sma200 = self.I(talib.SMA, self.close, timeperiod=200, name='SMA200')
        self.rsi = self.I(talib.RSI, self.close, timeperiod=14, name='RSI14')
        
        # Bollinger Bands (20 period, 2 std)
        self.bb_upper, self.bb_mid, self.bb_lower = [
            self.I(talib.BBANDS, self.close, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)[i]
            for i in range(3)
        ]
        
        # Swing low detection
        self.swing_low = self.I(talib.MIN, self.data.Low, timeperiod=20, name='Swing Low')
        
        print("🌙 Lunar indicators initialized! Ready for launch! 🚀")

    def next(self):
        price = self.data.Close[-1]
        
        # Moon Dev Position Management 🌙
        if self.position:
            # Trailing stop calculation
            trailing_stop = price - self.trailing_stop_multiplier * self.atr[-1]
            self.position.set_trailing_sl(trailing_stop)
            
            # Exit conditions
            if self.rsi[-1] < 40:
                print(f"🌙 Bearish RSI reset! Closing position at {price:.2f} ✨")
                self.position.close()
            elif self.data.Close[-1] < self.sma50[-1]:
                print(f"🌙 Price closed below SMA50! Exiting at {price:.2f} 💎")
                self.position.close()
        
        # Entry conditions
        else:
            ma_crossover = (self.sma50[-2] > self.sma200[-2]) and (self.sma50[-1] < self.sma200[-1])
            rsi_condition = self.rsi[-1] > 40
            bb_condition = price > self.bb_upper[-1]
            
            if ma_crossover and rsi_condition and bb_condition:
                # Risk management calculations 🌙
                sl_level = min(self.swing_low[-1], price * 0.97)  # 3% stop or swing low
                risk_amount = self.risk_per_trade * self.equity
                risk_per_share = price - sl_level
                
                if risk_per_share <= 0:
                    return  # Avoid division by zero
                
                position_size = int(round(risk_amount / risk_per_share))
                position_size = min(position_size, int(self.available_margin // price))
                
                if position_size > 0:
                    print(f"🚀 BULLISH REVERSAL CONFIRMED! 🌙")
                    print(f"Entry: {price:.2f} | Size: {position_size} ✨")
                    print(f"Stop Loss: {sl_level:.2f} | RSI: {self.rsi[-1]:.2f} 💎")
                    self.buy(size=position_size, sl=sl_level)

# Moon Dev