import pandas as pd
import talib
from backtesting import Backtest, Strategy

# Load and prepare data
path = '/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv'
data = pd.read_csv(path, parse_dates=['datetime'], index_col='datetime')

# Clean column names
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])

# Rename to match backtesting.py requirements
data = data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
})

class DirectionalVigor(Strategy):
    adx_period = 14
    adx_threshold = 25
    adx_weak = 20
    risk_per_trade = 0.01  # 1% risk
    atr_multiplier = 2.0

    def init(self):
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=self.adx_period)
        self.pdi = self.I(talib.PLUS_DI, self.data.High, self.data.Low, self.data.Close, timeperiod=self.adx_period)
        self.mdi = self.I(talib.MINUS_DI, self.data.High, self.data.Low, self.data.Close, timeperiod=self.adx_period)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=self.adx_period)
        print("🌙 Moon Dev: Indicators initialized for DirectionalVigor strategy ✨")

    def next(self):
        if len(self.data) < self.adx_period + 1:
            return

        current_adx = self.adx[-1]
        prev_adx = self.adx[-2]
        current_pdi = self.pdi[-1]
        prev_pdi = self.pdi[-2]
        current_mdi = self.mdi[-1]
        prev_mdi = self.mdi[-2]
        current_atr = self.atr[-1]
        current_close = self.data.Close[-1]

        # Entry condition: +DI crosses above -DI, ADX > 25, ADX rising
        entry_signal = (prev_pdi <= prev_mdi) and (current_pdi > current_mdi) and (current_adx > self.adx_threshold) and (current_adx > prev_adx)

        if entry_signal and not self.position:
            risk_amount = self.risk_per_trade * self.equity
            risk_per_unit = self.atr_multiplier * current_atr
            if risk_per_unit > 0:
                position_size = risk_amount / risk_per_unit
                position_size = int(round(position_size))
                sl_price = current_close - risk_per_unit
                self.buy(size=position_size, sl=sl_price)
                print(f"🌙 Moon Dev: Entering LONG at {current_close:.2f} | Size: {position_size} | SL: {sl_price:.2f} | ADX: {current_adx:.2f} 🚀✨")

        # Exit conditions
        if self.position:
            reversal = (prev_mdi <= prev_pdi) and (current_mdi > current_pdi)
            weakening = current_adx < self.adx_weak
            if reversal or weakening:
                self.position.close()
                exit_reason = "Reversal" if reversal else "Weakening Trend"
                print(f"🌙 Moon Dev: Exiting LONG at {current_close:.2f} | Reason: {exit_reason} | ADX: {current_adx:.2f} 📉💫")

# Run backtest
bt = Backtest(data, DirectionalVigor, cash=1000000, commission=0.002, exclusive_orders=True)
stats = bt.run()
print(stats)