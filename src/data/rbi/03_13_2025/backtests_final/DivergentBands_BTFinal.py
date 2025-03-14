I'll help you complete and debug the code while maintaining the original strategy logic. Here's the fixed and completed version with Moon Dev themed debug prints:

```python
import pandas as pd
import talib
import pandas_ta as pta
from backtesting import Strategy, Backtest

# Load and preprocess data 🌙
data = pd.read_csv(
    '/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv',
    parse_dates=['datetime'],
    index_col='datetime'
)
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data = data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
})

class DivergentBands(Strategy):
    bb_length = 20
    bb_std = 2
    rsi_period = 14
    volume_ma_period = 20
    atr_period = 14
    risk_pct = 0.01
    sl_multiplier = 1.5
    tp_multiplier = 2

    def init(self):
        # 🌙✨ Cosmic Indicators Setup
        # Bollinger Bands
        self.bb_upper = self.I(lambda close: pta.bbands(close, length=self.bb_length, std=self.bb_std)['BBU_20_2.0'], self.data.Close)
        self.bb_lower = self.I(lambda close: pta.bbands(close, length=self.bb_length, std=self.bb_std)['BBL_20_2.0'], self.data.Close)
        
        # RSI
        self.rsi = self.I(talib.RSI, self.data.Close, self.rsi_period)
        
        # Volume MA
        self.volume_ma = self.I(talib.SMA, self.data.Volume, self.volume_ma_period)
        
        # ATR
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, self.atr_period)

    def next(self):
        # 🌙🚀 Orbital Data Check
        if len(self.data) < max(self.bb_length, self.atr_period) + 2:
            return

        # Lunar Price Action
        current_close = self.data.Close[-1]
        current_low = self.data.Low[-1]
        current_high = self.data.High[-1]
        current_volume = self.data.Volume[-1]
        prev_low = self.data.Low[-2]
        prev_high = self.data.High[-2]
        current_rsi = self.rsi[-1]
        prev_rsi = self.rsi[-2]

        # 🌙✨ Gravitational Indicators
        bb_lower = self.bb_lower[-1]
        bb_upper = self.bb_upper[-1]
        volume_ma = self.volume_ma[-1]
        atr_value = self.atr[-1]

        # 🌙💧 Volume Surge Check
        volume_ok = current_volume > volume_ma

        # Long Entry Constellation 🌙➡️🚀
        if (current_low <= bb_lower and
            current_low < prev_low and
            current_rsi > prev_rsi and
            volume_ok and
            not self.position):
            
            sl = current_close - self.sl_multiplier * atr_value
            risk_amount = self.equity * self.risk_pct
            position_size = int(round(risk_amount / (current_close - sl)))
            
            if position_size > 0:
                tp = current_close + self.tp_multiplier * atr_value
                self.buy(size=position_size, sl=sl, tp=tp)
                print(f"🌙✨🚀 MOON BLASTOFF LONG! | Price: {current_close:.2f} | Size: {position_size} | SL: {sl:.2f} | TP: {tp:.2f}")

        # Short Entry Black Hole 🌙⬅️🕳️
        elif (current_high >= bb_upper and
              current_high > prev_high and
              current_rsi < prev_rsi and
              volume_ok and
              not self.position):
            
            sl = current_close + self.sl_multiplier * atr_value
            risk_amount = self.equity * self.risk_pct
            position_size = int(round(risk