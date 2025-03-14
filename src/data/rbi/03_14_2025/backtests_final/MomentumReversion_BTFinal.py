```python
# 🌙 Moon Dev's MomentumReversion Backtest Implementation
import pandas as pd
import talib
from backtesting import Backtest, Strategy

# Data preprocessing function
def prepare_data(filepath):
    # Load lunar data 🌑
    data = pd.read_csv(filepath)
    
    # Clean column names 🌟
    data.columns = data.columns.str.strip().str.lower()
    data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
    
    # Map columns to backtesting requirements 🗺️
    data = data.rename(columns={
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume'
    })
    
    # Convert datetime 🕰️
    data['datetime'] = pd.to_datetime(data['datetime'])
    data = data.set_index('datetime')
    return data

# Lunar Strategy Core 🌙
class MomentumReversion(Strategy):
    init_size = 1000000  # 🚀 Moon-sized capital
    risk_per_trade = 0.02  # 2% risk per trade
    
    def init(self):
        # Celestial Indicators 🌌
        self.sma50 = self.I(talib.SMA, self.data.Close, timeperiod=50)
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14)
        self.volume_sma5 = self.I(talib.SMA, self.data.Volume, timeperiod=5)
        
        # All-time high calculation 🌕
        def cumulative_max(series):
            return series.expanding().max()
        self.all_time_high = self.I(cumulative_max, self.data.High)
        
    def next(self):
        price = self.data.Close[-1]
        
        # 📊 Current cosmic positioning
        current_equity = self.equity
        position_size = 0
        
        # Long Entry Constellation 🌠
        long_conditions = (
            price > self.sma50[-1] and
            self.volume_sma5[-1] > self.volume_sma5[-2] and
            not self.position
        )
        
        if long_conditions:
            # Risk management calculations 🛡️
            stop_loss = price * 0.93  # 7% stop
            take_profit = price * 1.15  # 15% target
            risk_amount = current_equity * self.risk_per_trade
            risk_per_share = price - stop_loss
            position_size = int(round(risk_amount / risk_per_share))
            
            if position_size > 0:
                self.buy(size=position_size, sl=stop_loss, tp=take_profit)
                print(f"🌙 LONG COMMAND INITIATED! 🚀 Size: {position_size} | Entry: {price:.2f} | SL: {stop_loss:.2f} | TP: {take_profit:.2f}")
        
        # Short Entry Meteor Shower ☄️
        short_conditions = (
            self.data.High[-1] >= self.all_time_high[-1] and
            self.volume_sma5[-1] < self.volume_sma5[-2] and
            not self.position
        )
        
        if short_conditions:
            # Bearish engulfing pattern detection 🐻
            engulfing = talib.CDLENGULFING(self.data.Open, self.data.High, self.data.Low, self.data.Close)[-1]
            if engulfing < 0:
                stop_loss = price * 1.05  # 5% stop
                risk_amount = current_equity * self.risk_per_trade
                risk_per_share = stop_loss - price
                position_size = int(round(risk_amount / risk_per_share))
                
                if position_size > 0:
                    self.sell(size=position_size, sl=stop_loss)
                    print(f"🌑 SHORT POSITION ACTIVATED! 💫 Size: {position_size} | Entry: {price:.2f} | SL: {stop_loss:.2f}")
        
        # Exit Conditions 🌗
        if self.position:
            if self.position.is_long:
                if price < self.sma50[-1]:
                    self.position.close()
                    print(f"🌒 LONG POSITION CLOSED! SMA50 BREACH 🌧️ | Price: {price:.2f}")
            else:
                if self.rsi[-1] < 40:
                    self.position.close()
                    print(f"🌓 SHORT COVERED! RSI BELOW 40 🌥️ | Price: {price:.2f}")

# 🌙 Moon