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
    adx_weak = 25  # 🌙 Moon Dev: Tightened to match threshold for quicker exits from weakening trends ✨
    risk_per_trade = 0.01  # 1% risk
    atr_multiplier = 2.0
    tp_multiplier = 4.0  # 🌙 Moon Dev: Added 2:1 reward-to-risk ratio for better profitability ✨

    def init(self):
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=self.adx_period)
        self.pdi = self.I(talib.PLUS_DI, self.data.High, self.data.Low, self.data.Close, timeperiod=self.adx_period)
        self.mdi = self.I(talib.MINUS_DI, self.data.High, self.data.Low, self.data.Close, timeperiod=self.adx_period)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=self.adx_period)
        self.ema200 = self.I(talib.EMA, self.data.Close, timeperiod=200)  # 🌙 Moon Dev: Added 200 EMA for trend filter to avoid counter-trend trades ✨
        print("🌙 Moon Dev: Indicators initialized for DirectionalVigor strategy with EMA200 and TP optimization ✨")

    def next(self):
        if len(self.data) < 201:  # 🌙 Moon Dev: Adjusted for EMA200 initialization to ensure data availability ✨
            return

        current_adx = self.adx[-1]
        prev_adx = self.adx[-2]
        current_pdi = self.pdi[-1]
        prev_pdi = self.pdi[-2]
        current_mdi = self.mdi[-1]
        prev_mdi = self.mdi[-2]
        current_atr = self.atr[-1]
        current_close = self.data.Close[-1]
        current_ema = self.ema200[-1]

        # Long entry: +DI crosses above -DI, ADX > 25, ADX rising, above EMA200
        long_signal = (prev_pdi <= prev_mdi) and (current_pdi > current_mdi) and (current_adx > self.adx_threshold) and (current_adx > prev_adx) and (current_close > current_ema)
        # 🌙 Moon Dev: Added EMA filter for trend confirmation to improve entry quality and reduce whipsaws ✨

        if long_signal and not self.position:
            risk_amount = self.risk_per_trade * self.equity
            risk_per_unit = self.atr_multiplier * current_atr
            if risk_per_unit > 0:
                position_size = risk_amount / risk_per_unit
                position_size = int(round(position_size))  # 🌙 Moon Dev: Kept integer sizing for consistency, but risk-based for optimization ✨
                sl_price = current_close - risk_per_unit
                tp_price = current_close + (self.tp_multiplier * current_atr)
                self.buy(size=position_size, sl=sl_price, tp=tp_price)
                print(f"🌙 Moon Dev: Entering LONG at {current_close:.2f} | Size: {position_size} | SL: {sl_price:.2f} | TP: {tp_price:.2f} | ADX: {current_adx:.2f} 🚀✨")

        # Short entry: -DI crosses above +DI, ADX > 25, ADX rising, below EMA200
        short_signal = (prev_mdi <= prev_pdi) and (current_mdi > current_pdi) and (current_adx > self.adx_threshold) and (current_adx > prev_adx) and (current_close < current_ema)
        # 🌙 Moon Dev: Added symmetric short entries to capture downside moves and double trading opportunities ✨

        if short_signal and not self.position:
            risk_amount = self.risk_per_trade * self.equity
            risk_per_unit = self.atr_multiplier * current_atr
            if risk_per_unit > 0:
                position_size = risk_amount / risk_per_unit
                position_size = int(round(position_size))
                sl_price = current_close + risk_per_unit
                tp_price = current_close - (self.tp_multiplier * current_atr)
                self.sell(size=position_size, sl=sl_price, tp=tp_price)
                print(f"🌙 Moon Dev: Entering SHORT at {current_close:.2f} | Size: {position_size} | SL: {sl_price:.2f} | TP: {tp_price:.2f} | ADX: {current_adx:.2f} 🚀✨")

        # Exit conditions for both long and short
        if self.position:
            weakening = current_adx < self.adx_weak
            if self.position.is_long:
                reversal = (prev_mdi <= prev_pdi) and (current_mdi > current_pdi)
                if reversal or weakening:
                    self.position.close()
                    exit_reason = "Reversal" if reversal else "Weakening Trend"
                    print(f"🌙 Moon Dev: Exiting LONG at {current_close:.2f} | Reason: {exit_reason} | ADX: {current_adx:.2f} 📉💫")
            elif self.position.is_short:
                reversal = (prev_pdi <= prev_mdi) and (current_pdi > current_mdi)
                if reversal or weakening:
                    self.position.close()
                    exit_reason = "Reversal" if reversal else "Weakening Trend"
                    print(f"🌙 Moon Dev: Exiting SHORT at {current_close:.2f} | Reason: {exit_reason} | ADX: {current_adx:.2f} 📉💫")
            # 🌙 Moon Dev: Added symmetric reversal logic for shorts and integrated TP/SL for automated exits to lock in profits and cut losses ✨

# Run backtest
bt = Backtest(data, DirectionalVigor, cash=1000000, commission=0.002, exclusive_orders=True)
stats = bt.run()
print(stats)