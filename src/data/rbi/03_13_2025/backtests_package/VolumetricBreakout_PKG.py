Here's the fixed code with all backtesting.lib imports and functions removed, and replaced with proper Moon Dev themed implementations:

```python
# 🌙 Moon Dev's VolumetricBreakout Backtest 🌙
import pandas as pd
import talib
from backtesting import Backtest, Strategy

class VolumetricBreakout(Strategy):
    risk_percentage = 0.01  # 1% risk per trade
    
    def init(self):
        # 🌙 Calculate indicators using TA-Lib wrapped in self.I()
        self.volume_sma = self.I(talib.SMA, self.data.Volume, timeperiod=20, name='Volume SMA')
        self.swing_high = self.I(talib.MAX, self.data.High, timeperiod=20, name='Swing High')
        self.swing_low = self.I(talib.MIN, self.data.Low, timeperiod=20, name='Swing Low')
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14, name='RSI')
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=14, name='ATR')
        
        print("✨ Moon Dev Indicators Activated! ✨")

    def next(self):
        # 🚀 Skip if indicators not ready
        if len(self.data) < 20 or pd.isna(self.atr[-1]):
            return

        current_volume = self.data.Volume[-1]
        volume_sma = self.volume_sma[-1]
        current_high = self.data.High[-1]
        current_low = self.data.Low[-1]
        current_close = self.data.Close[-1]

        # 🌙 Volume surge condition (2x average)
        if current_volume >= 2 * volume_sma and not self.position:
            swing_high = self.swing_high[-1]
            swing_low = self.swing_low[-1]
            rsi = self.rsi[-1]
            atr = self.atr[-1]

            # 🌙 Long Entry Conditions
            if current_close > swing_high and rsi > 50:
                stop_loss = swing_high * 0.999  # 0.1% below swing high
                take_profit = current_close + 1.5 * atr
                self.calculate_position(current_close, stop_loss, take_profit, 'LONG')

            # 🌙 Short Entry Conditions
            elif current_close < swing_low and rsi < 50:
                stop_loss = swing_low * 1.001  # 0.1% above swing low
                take_profit = current_close - 1.5 * atr
                self.calculate_position(current_close, stop_loss, take_profit, 'SHORT')

    def calculate_position(self, entry_price, stop_loss, take_profit, direction):
        # 🌙 Risk management calculations
        risk_per_share = abs(entry_price - stop_loss)
        if risk_per_share == 0:
            return

        risk_amount = self.risk_percentage * self.equity
        position_size = int(round(risk_amount / risk_per_share))
        
        if position_size > 0:
            if direction == 'LONG':
                self.buy(size=position_size, sl=stop_loss, tp=take_profit)
                print(f"🚀🌙 MOON DEV LONG! Entry: {entry_price:.2f}, Size: {position_size}, SL: {stop_loss:.2f}, TP: {take_profit:.2f}")
            else:
                self.sell(size=position_size, sl=stop_loss, tp=take_profit)
                print(f"🌙🚀 MOON DEV SHORT! Entry: {entry_price:.2f}, Size: {position_size}, SL: {stop_loss:.2f}, TP: {take_profit:.2f}")

# 🌙 Data Preparation
data = pd.read_csv('/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv')
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])

# 🌙 Ensure proper column mapping
data = data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
})

# 🌙 Launch Backtest
bt = Backtest(data, VolumetricBreakout, cash=1_000_000, exclusive_orders=True)
stats = bt.run()
print("\n🌕🌖🌗