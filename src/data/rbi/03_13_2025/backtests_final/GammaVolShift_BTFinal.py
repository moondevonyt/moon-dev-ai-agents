Here's the debugged version of your backtest code with Moon Dev themed debug prints and technical fixes:

```python
# 🌙 Moon Dev's GammaVolShift Backtest Implementation ✨

# Required imports
import pandas as pd
import talib
from backtesting import Backtest, Strategy

# Data preparation
data_path = '/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv'
data = pd.read_csv(data_path, parse_dates=['datetime'], index_col='datetime')

# 🌙 Data Cleaning Ritual
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])

# Proper column mapping
data = data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
})

# 🚀 GammaVolShift Strategy Class
class GammaVolShift(Strategy):
    risk_pct = 0.01  # 1% risk per trade
    trailing_stop_pct = 0.05
    vix_entry_threshold = 20
    vix_exit_threshold = 25
    gamma_entry = 1.2
    gamma_exit = 0.8
    
    def init(self):
        # 🌌 Cosmic Indicator Setup
        self.highest_high = None
        
        # Verify required data columns exist
        if 'vix' not in self.data.df.columns:
            raise ValueError("VIX data missing - needs cosmic wisdom 🌙")
        if 'gamma_hedge_ratio' not in self.data.df.columns:
            raise ValueError("Gamma Hedge Ratio missing - quantum imbalance detected! ⚛️")

    def next(self):
        current_close = self.data.Close[-1]
        current_vix = self.data.df['vix'][-1]
        current_gamma = self.data.df['gamma_hedge_ratio'][-1]

        # 🌙 Position Sizing Calculations
        position_size = 0  # Initialize position size
        if not self.position:
            # Calculate risk-based position size
            equity = self.equity
            risk_amount = equity * self.risk_pct
            price_risk = current_close * self.trailing_stop_pct
            
            # 🪐 Moon Dev Position Sizing Rule
            position_size = risk_amount / price_risk
            position_size = int(round(position_size))  # Round to whole units
            max_possible = int(self.cash // current_close)
            position_size = min(position_size, max_possible)
            
            print(f"🌕 Position size calculated: {position_size} units")
            print(f"   🌙 Available cash: {self.cash:.2f}")
            print(f"   🚀 Max possible units: {max_possible}")

        # 🚀 Entry Logic
        if not self.position and position_size > 0:
            if (current_gamma > self.gamma_entry and 
                current_vix < self.vix_entry_threshold):
                
                stop_loss = current_close * (1 - self.trailing_stop_pct)
                self.buy(size=position_size, 
                        sl=stop_loss,
                        tag="GammaVolEntry")
                print(f"🚀 MOON LAUNCH! Entering {position_size} units at {current_close:.2f}")
                print(f"   🌌 Gamma: {current_gamma:.2f}, VIX: {current_vix:.2f}")
                print(f"   🛡️ Stop Loss set at: {stop_loss:.2f}")

        # 🌑 Exit Logic
        if self.position:
            # Cosmic stop-loss updates
            current_high = self.data.High[-1]
            self.highest_high = max(self.highest_high or current_high, current_high)
            new_sl = self.highest_high * (1 - self.trailing_stop_pct)
            
            # Update trailing stop
            if new_sl > self.position.sl:
                self.position.sl = new_sl
                print(f"✨ Trailing Stop updated to {new_sl:.2f}")

            # Exit conditions
            if (current_vix > self.vix_exit_threshold or 
                current_gamma < self.gamma_exit):
                self.position.close()
                print(f"🌑 BLACK HOLE EXIT! VIX: {current_vix:.2f}, Gamma: {current_gamma:.2f}")

# 🌕 Backtest Execution
print("🌙 Initializing Moon Dev Backtest...")
bt = Backtest(data, GammaVol