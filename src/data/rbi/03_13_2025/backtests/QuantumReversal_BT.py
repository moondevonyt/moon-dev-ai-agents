```python
# 🌙 QuantumReversal Backtest by Moon Dev AI 🌙
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import pandas as pd
import talib
import numpy as np

# ========================
# 🌌 DATA PREPARATION
# ========================
data_path = "/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv"
data = pd.read_csv(data_path, parse_dates=['datetime'], index_col='datetime')

# 🧹 Cleanse cosmic dust from column names
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])

# 🌌 Align celestial coordinates (column mapping)
data = data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
})

# ========================
# 🚀 QUANTUM REVERSAL STRATEGY
# ========================
class QuantumReversal(Strategy):
    risk_percent = 0.01  # 1% risk per trade 🌕
    bb_period = 20
    rsi_period = 14
    macd_fast = 12
    macd_slow = 26
    macd_signal = 9
    volume_sma_period = 20

    def init(self):
        # 🌠 Cosmic Indicators Configuration
        close = self.data.Close
        volume = self.data.Volume
        
        # 🌗 Bollinger Bands
        upper, _, lower = talib.BBANDS(close, timeperiod=self.bb_period, nbdevup=2, nbdevdn=2)
        self.I(lambda: upper, name='BB_upper')
        self.I(lambda: lower, name='BB_lower')
        
        # 🌓 RSI
        self.I(talib.RSI, close, self.rsi_period, name='RSI')
        
        # 🌍 MACD
        macd, signal, _ = talib.MACD(close, self.macd_fast, self.macd_slow, self.macd_signal)
        self.I(lambda: macd, name='MACD')
        self.I(lambda: signal, name='MACD_signal')
        
        # 🌊 Volume Momentum
        self.I(talib.SMA, volume, self.volume_sma_period, name='Volume_SMA')

    def next(self):
        # 🛑 Check for existing quantum entanglement (open positions)
        if self.position:
            return

        # 🌠 Current celestial alignment
        price = self.data.Close[-1]
        bb_lower = self.data.BB_lower[-1]
        bb_upper = self.data.BB_upper[-1]
        rsi = self.data.RSI[-1]
        macd = self.data.MACD[-1]
        macd_prev = self.data.MACD[-2]
        signal = self.data.MACD_signal[-1]
        signal_prev = self.data.MACD_signal[-2]
        volume = self.data.Volume[-1]
        vol_sma = self.data.Volume_SMA[-1]

        # 🌌 LONG Entry: Quantum Fluctuation Detected!
        if (price <= bb_lower and 
            rsi < 30 and 
            crossover(macd, signal) and 
            volume > vol_sma):
            
            # 🎯 Risk Management Calculations
            sl = bb_lower * 0.995  # 0.5% quantum shield
            tp = price + 2*(price - sl)  # 1:2 star alignment
            
            risk_amount = self.equity * self.risk_percent
            position_size = int(round(risk_amount / (price - sl)))
            
            # 🚀 Engage Hyperdrive (Long)
            self.buy(size=position_size, sl=sl, tp=tp)
            print(f"🌙✨🚀 LONG SIGNAL: Price {price:.2f} | Size {position_size} | Shield {sl:.2f} | Target {tp:.2f}")

        # 🌌 SHORT Entry: Cosmic Overextension!
        elif (price >= bb_upper and 
              rsi > 70 and 
              crossover(signal, macd) and 
              volume > vol_sma):
            
            # 🎯 Risk Management Calculations
            sl = bb_upper * 1.005  # 0.5% event horizon
            tp = price - 2*(sl - price)  # 1:2 black hole