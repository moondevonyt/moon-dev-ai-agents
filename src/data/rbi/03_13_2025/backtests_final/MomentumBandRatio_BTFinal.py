Here's the fixed code with proper Moon Dev themed debug prints and technical issues resolved:

```python
from backtesting import Backtest, Strategy
import pandas as pd
import talib
import numpy as np

# 🌙 MOON DEV DATA PREPARATION
data_path = '/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv'
data = pd.read_csv(data_path)

# Clean and format data columns
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
}, inplace=True)
data['datetime'] = pd.to_datetime(data['datetime'])
data.set_index('datetime', inplace=True)

class MomentumBandRatio(Strategy):
    def init(self):
        # 🌙✨ MOON DEV INDICATORS
        self.rsi = self.I(talib.RSI, self.data.Close, 20, name='RSI 20')
        self.ma5 = self.I(talib.SMA, self.data.Close, 5, name='MA5')
        self.ema50 = self.I(talib.EMA, self.data.Close, 50, name='EMA50')
        
        # Bollinger Bands with 2 std dev
        def bb_upper(close):
            upper, _, _ = talib.BBANDS(close, timeperiod=20, nbdevup=2, nbdevdn=2)
            return upper
        self.bb_upper = self.I(bb_upper, self.data.Close, name='BB Upper')
        
        def bb_lower(close):
            _, _, lower = talib.BBANDS(close, timeperiod=20, nbdevup=2, nbdevdn=2)
            return lower
        self.bb_lower = self.I(bb_lower, self.data.Close, name='BB Lower')
        
        # Swing low for stop loss
        self.swing_low = self.I(talib.MIN, self.data.Low, 20, name='Swing Low')

    def next(self):
        # 🌙 MOON DEV TRADE LOGIC
        price = self.data.Close[-1]
        equity = self.equity
        
        # Entry conditions
        if not self.position:
            # Validate indicator data availability
            if len(self.rsi) < 20 or len(self.ma5) < 5 or len(self.ema50) < 50:
                return
                
            rsi_val = self.rsi[-1]
            ma5_val = self.ma5[-1]
            ema50_val = self.ema50[-1]
            bb_width = self.bb_upper[-1] - self.bb_lower[-1]
            
            # Calculate price position in BB
            bb_position = (price - self.bb_lower[-1])/bb_width if bb_width !=0 else 0
            
            if (rsi_val < 30 and 
                ma5_val > ema50_val and 
                bb_position <= 0.2):
                
                # 🚀 RISK MANAGEMENT CALCULATIONS
                risk_pct = 0.01  # 1% risk per trade
                stop_loss = self.swing_low[-1]
                risk_per_share = price - stop_loss
                
                if risk_per_share <= 0:
                    print("🌙🚫 Invalid SL. Trade skipped.")
                    return
                
                # Position sizing with BB width adjustment
                base_size = (equity * risk_pct) / risk_per_share
                volatility_scale = 2/(bb_width + 1e-6)  # Prevent division by zero
                position_size = int(round(base_size * volatility_scale))
                
                if position_size > 0:
                    self.buy(size=position_size, sl=stop_loss)
                    print(f"🚀🌙 LONG {position_size} @ {price:.2f} | RSI: {rsi_val:.1f} BB%: {bb_position:.2f}")

        # Exit conditions
        else:
            # Take profit on RSI crossover
            if self.rsi[-2] < 70 and self.rsi[-1] > 70:
                self.position.close()
                print(f"🌙✨ TP Hit: RSI {self.rsi[-1]:.1f} > 70")
                
            # Trailing stop on BB upper
            if price >= self.bb_upper[-1]:
                self.position.close()
                print(f"🌙🚀