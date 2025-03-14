I've fixed the code by removing all `backtesting.lib` imports and replacing the `crossover` function with the proper implementation. Here's the corrected version with Moon Dev themed debug prints:

```python
import pandas as pd
import talib
import pandas_ta as ta
from backtesting import Backtest, Strategy

class AdaptiveSynergy(Strategy):
    def init(self):
        # Calculate indicators with Moon Dev precision 🌙
        self.macd_line, self.macd_signal_line, _ = self.I(talib.MACD, self.data.Close, 12, 26, 9)
        self.rsi_series = self.I(talib.RSI, self.data.Close, 14)
        self.upper_bb, self.middle_bb, self.lower_bb = self.I(talib.BBANDS, self.data.Close, 20, 2, 2)
        self.atr_series = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, 14)
        
        # Calculate VWAP using pandas_ta
        vwap_values = ta.vwap(
            high=self.data.High,
            low=self.data.Low,
            close=self.data.Close,
            volume=self.data.Volume
        )
        self.I(vwap_values, name='VWAP')

    def next(self):
        current_close = self.data.Close[-1]
        print(f"🌙 Moon Dev Pulse | Close: {current_close:.2f} | MACD: {self.macd_line[-1]:.2f} | RSI: {self.rsi_series[-1]:.2f}")

        if not self.position:
            # Entry conditions with Moon Dev precision 🌙
            entry_conditions = [
                (self.macd_line[-2] < self.macd_signal_line[-2] and self.macd_line[-1] > self.macd_signal_line[-1]),  # Bullish crossover
                50 < self.rsi_series[-1] < 70,
                current_close > self.upper_bb[-1],
                current_close > self.data.VWAP[-1]
            ]
            
            if all(entry_conditions):
                risk_percent = 0.01
                equity = self.broker.equity
                risk_amount = equity * risk_percent
                entry_price = self.data.Open[-1]  # Next candle's open
                atr_value = self.atr_series[-1]
                
                stop_loss = entry_price - 1.5 * atr_value
                risk_per_share = entry_price - stop_loss
                
                if risk_per_share > 0:
                    position_size = int(round(risk_amount / risk_per_share))
                    take_profit = entry_price + 2 * atr_value
                    
                    self.buy(
                        size=position_size,
                        sl=stop_loss,
                        tp=take_profit
                    )
                    print(f"🚀🌙 Moon Dev LONG Launch | Size: {position_size} | Entry: {entry_price:.2f} | SL: {stop_loss:.2f} | TP: {take_profit:.2f}")

        else:
            # Exit conditions with Moon Dev vigilance 🌙
            exit_conditions = [
                (self.macd_signal_line[-2] < self.macd_line[-2] and self.macd_signal_line[-1] > self.macd_line[-1]),  # Bearish crossover
                self.rsi_series[-1] >= 70,
                current_close < self.middle_bb[-1],
                current_close < self.data.VWAP[-1]
            ]
            
            if any(exit_conditions):
                self.position.close()
                print(f"🌑🌙 Moon Dev Exit Signal | Price: {current_close:.2f} | Equity: {self.broker.equity:.2f}")

# Moon Dev Data Preparation Ritual 🌙✨
data = pd.read_csv('/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv')
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col])
data = data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
})
data['datetime'] = pd.to_datetime(data['datetime'])
data = data.set_index('datetime')

# Execute Moon Dev Backtest Ritual 🌙💫
bt = Backtest(data, AdaptiveSynergy, cash=1_000_000, commission=.002