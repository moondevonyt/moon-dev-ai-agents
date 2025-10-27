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
    adx_period = 10  # 🌙 Moon Dev: Reduced ADX period to 10 for faster signal detection and more responsive entries in volatile 15m BTC ✨
    adx_threshold = 20  # 🌙 Moon Dev: Lowered threshold to 20 to capture more trending opportunities without excessive noise ✨
    adx_weak = 20  # 🌙 Moon Dev: Aligned with threshold for consistent trend strength monitoring ✨
    risk_per_trade = 0.02  # 🌙 Moon Dev: Increased to 2% risk per trade to amplify returns while staying within reasonable risk limits ✨
    atr_multiplier = 1.5  # 🌙 Moon Dev: Tightened SL multiplier to 1.5 ATR for better risk control and higher win rate potential ✨
    tp_multiplier = 6.0  # 🌙 Moon Dev: Extended TP to 6 ATR for a 4:1 reward-to-risk ratio, aiming to boost profitability on winners ✨

    def init(self):
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=self.adx_period)
        self.pdi = self.I(talib.PLUS_DI, self.data.High, self.data.Low, self.data.Close, timeperiod=self.adx_period)
        self.mdi = self.I(talib.MINUS_DI, self.data.High, self.data.Low, self.data.Close, timeperiod=self.adx_period)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=self.adx_period)
        self.ema100 = self.I(talib.EMA, self.data.Close, timeperiod=100)  # 🌙 Moon Dev: Switched to 100 EMA for faster trend confirmation on 15m timeframe, reducing lag in bull/bear detection ✨
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14)  # 🌙 Moon Dev: Added RSI for momentum filter to ensure entries align with market strength and avoid weak signals ✨
        self.vol_sma = self.I(talib.SMA, self.data.Volume, timeperiod=20)  # 🌙 Moon Dev: Added volume SMA to filter for high-conviction moves, only trading on above-average volume spikes ✨
        print("🌙 Moon Dev: Indicators initialized for optimized DirectionalVigor with RSI, Volume filter, faster ADX/EMA, and enhanced RR/trailing logic ✨")

    def next(self):
        if len(self.data) < 101:  # 🌙 Moon Dev: Adjusted for EMA100 and other indicators to ensure sufficient data history ✨
            return

        current_adx = self.adx[-1]
        prev_adx = self.adx[-2]
        current_pdi = self.pdi[-1]
        prev_pdi = self.pdi[-2]
        current_mdi = self.mdi[-1]
        prev_mdi = self.mdi[-2]
        current_atr = self.atr[-1]
        current_close = self.data.Close[-1]
        current_ema = self.ema100[-1]
        current_rsi = self.rsi[-1]
        current_vol = self.data.Volume[-1]
        current_vol_sma = self.vol_sma[-1]

        # Long entry: +DI crosses above -DI, ADX > 20, ADX rising, above EMA100, RSI > 50, Volume > 1.2x SMA
        long_signal = (prev_pdi <= prev_mdi) and (current_pdi > current_mdi) and (current_adx > self.adx_threshold) and (current_adx > prev_adx) and (current_close > current_ema) and (current_rsi > 50) and (current_vol > current_vol_sma * 1.2)
        # 🌙 Moon Dev: Enhanced entry with RSI momentum (>50 for bullish bias) and volume filter (1.2x SMA) to tighten setups, reduce false signals, and focus on high-quality trends for higher returns ✨

        if long_signal and not self.position:
            risk_amount = self.risk_per_trade * self._broker.starting_cash if self._broker.starting_cash else self.risk_per_trade * self.equity  # 🌙 Moon Dev: Fallback for equity calculation ✨
            risk_per_unit = self.atr_multiplier * current_atr
            if risk_per_unit > 0:
                position_size = risk_amount / risk_per_unit  # 🌙 Moon Dev: Use float sizing for precise risk allocation, allowing fractional positions for better capital efficiency ✨
                sl_price = current_close - risk_per_unit
                tp_price = current_close + (self.tp_multiplier * current_atr)
                self.buy(size=position_size, sl=sl_price, tp=tp_price)
                self.entry_price = current_close  # 🌙 Moon Dev: Track entry price for trailing stop logic ✨
                print(f"🌙 Moon Dev: Entering LONG at {current_close:.2f} | Size: {position_size:.2f} | SL: {sl_price:.2f} | TP: {tp_price:.2f} | ADX: {current_adx:.2f} | RSI: {current_rsi:.2f} 🚀✨")

        # Short entry: -DI crosses above +DI, ADX > 20, ADX rising, below EMA100, RSI < 50, Volume > 1.2x SMA
        short_signal = (prev_mdi <= prev_pdi) and (current_mdi > current_pdi) and (current_adx > self.adx_threshold) and (current_adx > prev_adx) and (current_close < current_ema) and (current_rsi < 50) and (current_vol > current_vol_sma * 1.2)
        # 🌙 Moon Dev: Symmetric short enhancements with RSI (<50 for bearish bias) and volume filter to balance opportunities in downtrends ✨

        if short_signal and not self.position:
            risk_amount = self.risk_per_trade * self._broker.starting_cash if self._broker.starting_cash else self.risk_per_trade * self.equity
            risk_per_unit = self.atr_multiplier * current_atr
            if risk_per_unit > 0:
                position_size = risk_amount / risk_per_unit
                sl_price = current_close + risk_per_unit
                tp_price = current_close - (self.tp_multiplier * current_atr)
                self.sell(size=position_size, sl=sl_price, tp=tp_price)
                self.entry_price = current_close  # 🌙 Moon Dev: Track entry price for trailing stop logic ✨
                print(f"🌙 Moon Dev: Entering SHORT at {current_close:.2f} | Size: {position_size:.2f} | SL: {sl_price:.2f} | TP: {tp_price:.2f} | ADX: {current_adx:.2f} | RSI: {current_rsi:.2f} 🚀✨")

        # Dynamic trailing stop and exit conditions
        if self.position:
            # 🌙 Moon Dev: Implement trailing stop after 1.5 ATR profit to lock in gains, moving SL to breakeven + 0.5 ATR buffer for better risk-reward on runners ✨
            trail_threshold = 1.5 * (self.atr_multiplier * current_atr)
            trail_buffer = 0.5 * (self.atr_multiplier * current_atr)
            entry_price = self.position.entry_price  # Actual entry price from backtesting.py

            if self.position.is_long:
                profit = current_close - entry_price
                if profit > trail_threshold:
                    new_sl = entry_price + trail_buffer
                    if new_sl > self.position.sl:
                        self.position.sl = new_sl
                        print(f"🌙 Moon Dev: Trailing LONG SL to {new_sl:.2f} | Profit: {profit:.2f} 📈🔒")

                reversal = (prev_mdi <= prev_pdi) and (current_mdi > current_pdi)
                weakening = current_adx < self.adx_weak
                if reversal or weakening:
                    self.position.close()
                    exit_reason = "Reversal" if reversal else "Weakening Trend"
                    print(f"🌙 Moon Dev: Exiting LONG at {current_close:.2f} | Reason: {exit_reason} | ADX: {current_adx:.2f} 📉💫")

            elif self.position.is_short:
                profit = entry_price - current_close
                if profit > trail_threshold:
                    new_sl = entry_price - trail_buffer
                    if new_sl < self.position.sl:
                        self.position.sl = new_sl
                        print(f"🌙 Moon Dev: Trailing SHORT SL to {new_sl:.2f} | Profit: {profit:.2f} 📉🔒")

                reversal = (prev_pdi <= prev_mdi) and (current_pdi > current_mdi)
                weakening = current_adx < self.adx_weak
                if reversal or weakening:
                    self.position.close()
                    exit_reason = "Reversal" if reversal else "Weakening Trend"
                    print(f"🌙 Moon Dev: Exiting SHORT at {current_close:.2f} | Reason: {exit_reason} | ADX: {current_adx:.2f} 📉💫")
            # 🌙 Moon Dev: Retained reversal/weakening exits but enhanced with trailing to protect profits, improving overall return potential while managing drawdowns ✨

# Run backtest
bt = Backtest(data, DirectionalVigor, cash=1000000, commission=0.002, exclusive_orders=True)
stats = bt.run()
print(stats)