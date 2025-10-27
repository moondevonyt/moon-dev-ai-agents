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
    adx_threshold = 25  # Kept at 25 for quality trends, but added filters for better selectivity
    adx_weak = 20
    risk_per_trade = 0.015  # Increased to 1.5% to amplify returns while maintaining risk control
    atr_multiplier = 2.0
    # Added TP multiplier for 2:1 reward:risk (SL at 2 ATR, TP at 4 ATR)
    tp_atr_multiplier = 4.0

    def init(self):
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=self.adx_period)
        self.pdi = self.I(talib.PLUS_DI, self.data.High, self.data.Low, self.data.Close, timeperiod=self.adx_period)
        self.mdi = self.I(talib.MINUS_DI, self.data.High, self.data.Low, self.data.Close, timeperiod=self.adx_period)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=self.adx_period)
        # Optimized: Added EMA(50) as trend filter to ensure entries align with medium-term direction
        self.ema = self.I(talib.EMA, self.data.Close, timeperiod=50)
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
        current_ema = self.ema[-1]

        # Optimized: Long entry - tightened with EMA trend filter (close > EMA50) for better setups in uptrends
        long_entry = (prev_pdi <= prev_mdi) and (current_pdi > current_mdi) and (current_adx > self.adx_threshold) and (current_adx > prev_adx) and (current_close > current_ema)

        if long_entry and not self.position:
            risk_amount = self.risk_per_trade * self.equity
            risk_per_unit = self.atr_multiplier * current_atr
            if risk_per_unit > 0:
                position_size = risk_amount / risk_per_unit  # Optimized: Use float for fractional sizes (more precise, no int rounding)
                sl_price = current_close - risk_per_unit
                tp_price = current_close + self.tp_atr_multiplier * current_atr  # Added: Take profit at 4 ATR for improved reward:risk
                self.buy(size=position_size, sl=sl_price, tp=tp_price)
                print(f"🌙 Moon Dev: Entering LONG at {current_close:.2f} | Size: {position_size:.4f} | SL: {sl_price:.2f} | TP: {tp_price:.2f} | ADX: {current_adx:.2f} 🚀✨")

        # Optimized: Added short entry symmetrically for bidirectional trading to capture downtrends and boost returns
        short_entry = (prev_mdi <= prev_pdi) and (current_mdi > current_pdi) and (current_adx > self.adx_threshold) and (current_adx > prev_adx) and (current_close < current_ema)

        if short_entry and not self.position:
            risk_amount = self.risk_per_trade * self.equity
            risk_per_unit = self.atr_multiplier * current_atr
            if risk_per_unit > 0:
                position_size = risk_amount / risk_per_unit  # Same sizing logic for shorts
                sl_price = current_close + risk_per_unit
                tp_price = current_close - self.tp_atr_multiplier * current_atr  # TP at 4 ATR below for shorts
                self.sell(size=position_size, sl=sl_price, tp=tp_price)
                print(f"🌙 Moon Dev: Entering SHORT at {current_close:.2f} | Size: {position_size:.4f} | SL: {sl_price:.2f} | TP: {tp_price:.2f} | ADX: {current_adx:.2f} 📉✨")

        # Exit conditions - optimized for both long and short
        if self.position:
            reversal = False
            if self.position.is_long:
                reversal = (prev_mdi <= prev_pdi) and (current_mdi > current_pdi)
            else:  # is_short
                reversal = (prev_pdi <= prev_mdi) and (current_pdi > current_mdi)
            weakening = current_adx < self.adx_weak
            if reversal or weakening:
                self.position.close()
                exit_reason = "Reversal" if reversal else "Weakening Trend"
                print(f"🌙 Moon Dev: Exiting {'LONG' if self.position.is_long else 'SHORT'} at {current_close:.2f} | Reason: {exit_reason} | ADX: {current_adx:.2f} 📊💫")

# Run backtest
bt = Backtest(data, DirectionalVigor, cash=1000000, commission=0.002, exclusive_orders=True)
stats = bt.run()
print(stats)