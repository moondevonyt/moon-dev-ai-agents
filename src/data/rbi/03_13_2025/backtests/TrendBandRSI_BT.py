import pandas as pd
from backtesting import Backtest, Strategy
import talib

# Clean and prepare data
data = pd.read_csv('/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv')
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

class TrendBandRSI(Strategy):
    rsi_period = 14
    bb_period = 20
    bb_std = 2
    sma_period = 50
    risk_pct = 0.02
    
    def init(self):
        self.rsi = self.I(talib.RSI, self.data.Close, self.rsi_period)
        self.sma_rsi = self.I(talib.SMA, self.rsi, self.bb_period)
        self.std_rsi = self.I(talib.STDDEV, self.rsi, self.bb_period)
        self.sma50 = self.I(talib.SMA, self.data.Close, self.sma_period)
        
    def next(self):
        if len(self.rsi) < 3 or len(self.sma50) < 1:
            return
        
        # Calculate dynamic bands
        current_upper = self.sma_rsi[-1] + self.bb_std * self.std_rsi[-1]
        previous_upper = self.sma_rsi[-2] + self.bb_std * self.std_rsi[-2]
        current_lower = self.sma_rsi[-1] - self.bb_std * self.std_rsi[-1]
        previous_lower = self.sma_rsi[-2] - self.bb_std * self.std_rsi[-2]
        
        current_close = self.data.Close[-1]
        current_rsi = self.rsi[-1]
        previous_rsi = self.rsi[-2]
        
        # Moon Dev Risk Management 🌙
        equity = self.broker.getvalue()
        if not self.position:
            # Long entry logic
            if (previous_rsi <= previous_upper) and (current_rsi > current_upper) and (current_close > self.sma50[-1]):
                sl = current_close * 0.99
                risk_amount = equity * self.risk_pct
                position_size = int(round(risk_amount / (current_close - sl)))
                if position_size > 0:
                    self.buy(size=position_size, sl=sl, tp=current_close*1.02)
                    print(f"🌙✨ Moon Rocket LONG! 🚀 Size: {position_size} @ {current_close:.2f}")
            
            # Short entry logic
            elif (previous_rsi >= previous_lower) and (current_rsi < current_lower) and (current_close < self.sma50[-1]):
                sl = current_close * 1.01
                risk_amount = equity * self.risk_pct
                position_size = int(round(risk_amount / (sl - current_close)))
                if position_size > 0:
                    self.sell(size=position_size, sl=sl, tp=current_close*0.98)
                    print(f"🌙✨ Moon Dive SHORT! 🌑 Size: {position_size} @ {current_close:.2f}")

# Launch Moon Dev Backtest 🌙
bt = Backtest(data, TrendBandRSI, cash=1_000_000, commission=.002)
stats = bt.run()
print(stats)
print(stats._strategy)