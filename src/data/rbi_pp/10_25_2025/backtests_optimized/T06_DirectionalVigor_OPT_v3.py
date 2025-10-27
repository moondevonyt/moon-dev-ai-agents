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
    adx_period = 10  # 🌙 Moon Dev: Shortened ADX period from 14 to 10 for more responsive signals on 15m timeframe, capturing quicker trends without excessive noise
    adx_threshold = 20  # 🌙 Moon Dev: Lowered threshold from 25 to 20 to allow more trend-confirming entries while still filtering weak markets
    adx_weak = 15  # 🌙 Moon Dev: Adjusted weakening threshold from 20 to 15 to exit earlier on fading momentum, improving capital preservation
    risk_per_trade = 0.015  # 🌙 Moon Dev: Increased risk per trade from 1% to 1.5% to amplify returns in favorable setups, balanced with enhanced filters
    atr_multiplier = 2.0  # SL distance multiplier
    tp_multiplier = 4.0  # 🌙 Moon Dev: Added TP multiplier for 2:1 reward-to-risk ratio (TP distance = 2 * SL distance), enabling profitable exits before reversals
    sma_period = 200  # 🌙 Moon Dev: Added 200-period SMA for trend filter to ensure directional bias aligns with longer-term trend, reducing whipsaws

    def init(self):
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=self.adx_period)
        self.pdi = self.I(talib.PLUS_DI, self.data.High, self.data.Low, self.data.Close, timeperiod=self.adx_period)
        self.mdi = self.I(talib.MINUS_DI, self.data.High, self.data.Low, self.data.Close, timeperiod=self.adx_period)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=self.adx_period)
        self.sma = self.I(talib.SMA, self.data.Close, timeperiod=self.sma_period)  # 🌙 Moon Dev: Initialized SMA for market regime filter
        print("🌙 Moon Dev: Indicators initialized for DirectionalVigor strategy ✨")

    def next(self):
        if len(self.data) < max(self.adx_period, self.sma_period) + 1:  # 🌙 Moon Dev: Updated length check to account for SMA period, ensuring all indicators are valid
            return

        current_adx = self.adx[-1]
        prev_adx = self.adx[-2]
        current_pdi = self.pdi[-1]
        prev_pdi = self.pdi[-2]
        current_mdi = self.mdi[-1]
        prev_mdi = self.mdi[-2]
        current_atr = self.atr[-1]
        current_close = self.data.Close[-1]
        current_sma = self.sma[-1]

        risk_per_unit = self.atr_multiplier * current_atr
        sl_distance = risk_per_unit
        tp_distance = self.tp_multiplier * current_atr  # 🌙 Moon Dev: Dynamic TP based on ATR for consistent RR across volatility regimes
        risk_amount = self.risk_per_trade * self.equity
        if risk_per_unit > 0:
            position_size = risk_amount / risk_per_unit  # 🌙 Moon Dev: Kept volatility-based sizing but now applied to both long/short for balanced exposure

        # Long entry: +DI crosses above -DI, ADX > threshold, ADX rising, and above SMA trend filter
        long_entry = (prev_pdi <= prev_mdi) and (current_pdi > current_mdi) and (current_adx > self.adx_threshold) and (current_adx > prev_adx) and (current_close > current_sma)
        if long_entry and not self.position:
            sl_price = current_close - sl_distance
            tp_price = current_close + tp_distance
            position_size = position_size  # 🌙 Moon Dev: Use float for precise fractional sizing, improving risk accuracy over int rounding
            self.buy(size=position_size, sl=sl_price, tp=tp_price)
            print(f"🌙 Moon Dev: Entering LONG at {current_close:.2f} | Size: {position_size:.4f} | SL: {sl_price:.2f} | TP: {tp_price:.2f} | ADX: {current_adx:.2f} 🚀✨")

        # Short entry: -DI crosses above +DI, ADX > threshold, ADX rising, and below SMA trend filter
        short_entry = (prev_mdi <= prev_pdi) and (current_mdi > current_pdi) and (current_adx > self.adx_threshold) and (current_adx > prev_adx) and (current_close < current_sma)
        if short_entry and not self.position:
            sl_price = current_close + sl_distance
            tp_price = current_close - tp_distance
            position_size = position_size  # Same sizing logic
            self.sell(size=position_size, sl=sl_price, tp=tp_price)
            print(f"🌙 Moon Dev: Entering SHORT at {current_close:.2f} | Size: {position_size:.4f} | SL: {sl_price:.2f} | TP: {tp_price:.2f} | ADX: {current_adx:.2f} 📉✨")

        # Exit conditions for long positions
        if self.position and self.position.is_long:
            long_reversal = (prev_mdi <= prev_pdi) and (current_mdi > current_pdi)
            long_weakening = current_adx < self.adx_weak
            if long_reversal or long_weakening:
                self.position.close()
                exit_reason = "Reversal" if long_reversal else "Weakening Trend"
                print(f"🌙 Moon Dev: Exiting LONG at {current_close:.2f} | Reason: {exit_reason} | ADX: {current_adx:.2f} 📉💫")

        # Exit conditions for short positions
        if self.position and self.position.is_short:
            short_reversal = (prev_pdi <= prev_mdi) and (current_pdi > current_mdi)
            short_weakening = current_adx < self.adx_weak
            if short_reversal or short_weakening:
                self.position.close()
                exit_reason = "Reversal" if short_reversal else "Weakening Trend"
                print(f"🌙 Moon Dev: Exiting SHORT at {current_close:.2f} | Reason: {exit_reason} | ADX: {current_adx:.2f} 📈💫")

# Run backtest
bt = Backtest(data, DirectionalVigor, cash=1000000, commission=0.002, exclusive_orders=True)
stats = bt.run()
print(stats)