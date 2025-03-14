```python
# 🌙 Moon Dev's VolumeSurge Breakout Backtest 🌙
import pandas as pd
import talib
import pandas_ta as ta
from backtesting import Backtest, Strategy

# Data Preparation 🌐
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

class VolumeSurgeBreakout(Strategy):
    risk_pct = 0.01  # 1% risk per trade 🌊
    consecutive_losses = 0
    
    def init(self):
        # 🌟 Indicators Setup
        self.vwma = self.I(ta.vwma, self.data.Close, self.data.Volume, 20, name='VWMA')
        self.rsi = self.I(talib.RSI, self.data.Close, 14, name='RSI')
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, 14, name='ATR')
        self.vol_sma = self.I(talib.SMA, self.data.Volume, 20, name='VOL_SMA')
        self.daily_pnl = 0
        self.last_date = None

    def next(self):
        # 🌙 Market Hours Filter (First 2 hours)
        current_hour = self.data.index[-1].hour
        if current_hour >= 2:
            return

        # 🌪️ Risk Management Checks
        current_date = self.data.index[-1].date()
        if current_date != self.last_date:
            self.daily_pnl = 0
            self.last_date = current_date
            
        if self.daily_pnl <= -0.05 * self.equity or self.consecutive_losses >= 3:
            return

        # 🚀 Entry Conditions
        if (not self.position and
            self.rsi[-1] < 30 and
            self.data.Volume[-1] >= 2 * self.vol_sma[-1] and
            self.data.Close[-1] > self.vwma[-1] and
            (self.data.High[-1] - self.data.Low[-1]) > 1.5 * self.atr[-1]):

            # 📈 Position Sizing
            atr_value = self.atr[-1]
            risk_amount = self.risk_pct * self.equity
            position_size = int(round(risk_amount / atr_value))
            
            if position_size > 0:
                entry_price = self.data.Close[-1]
                sl = entry_price - atr_value
                tp = entry_price + 2 * atr_value
                
                self.buy(size=position_size, sl=sl, tp=tp)
                print(f"🌙✨ BUY SIGNAL | Size: {position_size} | Entry: {entry_price:.2f} 🚀")

        # 🛑 Exit Management
        for trade in self.trades:
            if trade.is_long:
                # Activate trailing after 1x ATR profit
                if self.data.Close[-1] >= trade.entry_price + trade.sl * 2:
                    new_sl = self.data.Close[-1] - 0.5 * trade.sl
                    if new_sl > trade.sl:
                        trade.sl = new_sl
                        print(f"🌙🔧 Trailing SL Updated: {new_sl:.2f}")

    def notify_trade(self, trade):
        # 🌗 Track Daily PnL & Consecutive Losses
        if trade.is_closed:
            self.daily_pnl += trade.pnl
            if trade.pnl <= 0:
                self.consecutive_losses += 1
                print(f"🌙💔 Loss Detected | Consecutive Losses: {self.consecutive_losses}")
            else:
                self.consecutive_losses = 0
                print(f"🌙💰 Profit Taken | PnL: {trade.pnl:.2f}")

# 🚨 Backtest Execution
bt = Backtest(data, VolumeSurgeBreakout, cash=10000, commission=.002)
stats = bt.run()
print("🌙✨ Backtest