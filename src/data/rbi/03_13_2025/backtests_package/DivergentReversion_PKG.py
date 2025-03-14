I've fixed the code by removing all `backtesting.lib` imports and replacing the crossover logic with proper array indexing comparisons. Here's the corrected version with Moon Dev themed debug prints:

```python
# 🌙 Moon Dev's Divergent Reversion Backtest 🌙
import pandas as pd
import talib
from backtesting import Backtest, Strategy

# Load and prepare cosmic data 🌌
data = pd.read_csv('/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv')
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data = data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
})

class DivergentReversion(Strategy):
    risk_pct = 0.02  # 2% risk per trade 🌕
    stop_loss_pct = 0.03  # 3% stop loss 🛑
    rsi_period = 20
    stoch_period = 8
    
    def init(self):
        # Celestial Indicators 🌠
        self.rsi = self.I(talib.RSI, self.data.Close, self.rsi_period)
        self.rsi_ma = self.I(talib.SMA, self.rsi, self.rsi_period)
        self.stoch_k, self.stoch_d = self.I(talib.STOCH, self.data.High, self.data.Low, self.data.Close,
                                           fastk_period=self.stoch_period, slowk_period=3, slowk_matype=0,
                                           slowd_period=3, slowd_matype=0)
        self.stoch_ma = self.I(talib.SMA, self.stoch_k, self.rsi_period)
        
    def next(self):
        # Require enough stardust for calculations ✨
        if len(self.rsi) < 30 or len(self.stoch_k) < 30:
            return

        # Current constellation positions 🌃
        current_rsi = self.rsi[-1]
        rsi_ma = self.rsi_ma[-1]
        current_stoch = self.stoch_k[-1]
        stoch_ma = self.stoch_ma[-1]

        # Lunar Debug Console 🌙📊
        print(f"🌙 RSI: {current_rsi:.1f} vs MA: {rsi_ma:.1f}")
        print(f"✨ Stoch: {current_stoch:.1f} vs MA: {stoch_ma:.1f}")

        # Calculate cosmic position size 🌠
        equity = self.equity
        risk_amount = equity * self.risk_pct
        price = self.data.Close[-1]
        stop_distance = price * self.stop_loss_pct
        position_size = int(round(risk_amount / stop_distance))

        # Short Entry: Overbought Divergence 🌑
        if not self.position and current_rsi > rsi_ma and current_stoch < stoch_ma:
            self.sell(size=position_size,
                     sl=price * 1.03,
                     tp=price - 10)
            print(f"🚀🌒 SHORT LAUNCH! Size: {position_size} @ {price:.2f}")

        # Long Entry: Oversold Divergence 🌕
        elif not self.position and current_rsi < rsi_ma and current_stoch > stoch_ma:
            self.buy(size=position_size,
                    sl=price * 0.97,
                    tp=price + 50)
            print(f"🚀🌕 LONG LAUNCH! Size: {position_size} @ {price:.2f}")

        # Galactic Exit Conditions 🌌
        if self.position:
            # Reversion Exit Criteria
            if (self.position.is_short and 
                ((self.rsi[-2] < self.rsi_ma[-2] and self.rsi[-1] > self.rsi_ma[-1]) or 
                 (self.stoch_k[-2] < self.stoch_ma[-2] and self.stoch_k[-1] > self.stoch_ma[-1]))) or \
               (self.position.is_long and 
                ((self.rsi_ma[-2] < self.rsi[-2] and self.rsi_ma[-1] > self.rsi[-1]) or 
                 (self.stoch_ma[-2] < self.stoch_k[-2] and self.stoch_ma[-1] > self.stoch_k[-1