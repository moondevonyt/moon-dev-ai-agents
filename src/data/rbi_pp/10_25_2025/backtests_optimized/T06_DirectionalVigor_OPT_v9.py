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
    adx_threshold = 20  # 🌙 Moon Dev: Lowered ADX threshold to 20 for more trade opportunities in moderate trends, increasing signal frequency while maintaining quality ✨
    adx_weak = 20  # 🌙 Moon Dev: Adjusted weakening threshold to match new entry level for consistent trend monitoring 🚀
    risk_per_trade = 0.02  # 🌙 Moon Dev: Increased risk per trade to 2% to scale up position sizes and amplify returns without excessive drawdown 📈
    atr_multiplier = 2.0
    tp_multiplier = 5.0  # 🌙 Moon Dev: Boosted TP to 5x ATR for a 2.5:1 reward-to-risk ratio, aiming to capture larger moves and hit target returns 💥

    def init(self):
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=self.adx_period)
        self.pdi = self.I(talib.PLUS_DI, self.data.High, self.data.Low, self.data.Close, timeperiod=self.adx_period)
        self.mdi = self.I(talib.MINUS_DI, self.data.High, self.data.Low, self.data.Close, timeperiod=self.adx_period)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=self.adx_period)
        self.ema200 = self.I(talib.EMA, self.data.Close, timeperiod=200)  # 🌙 Moon Dev: Retained 200 EMA for long-term trend filter ✨
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14)  # 🌙 Moon Dev: Added RSI(14) to filter overbought/oversold conditions, improving entry timing and win rate 📊
        self.vol_ma = self.I(talib.SMA, self.data.Volume, timeperiod=20)  # 🌙 Moon Dev: Added 20-period Volume SMA for confirmation of strong moves, avoiding low-volume traps 🔊
        print("🌙 Moon Dev: Indicators initialized for optimized DirectionalVigor with RSI, Volume MA, lowered ADX threshold, increased risk/TP for 50% target push! ✨")

    def next(self):
        if len(self.data) < 201:  # 🌙 Moon Dev: Kept buffer for EMA200 and other indicators to ensure stability ✨
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
        current_rsi = self.rsi[-1]
        current_vol = self.data.Volume[-1]
        current_vol_ma = self.vol_ma[-1]

        # Long entry: +DI crosses above -DI, ADX > 20, ADX rising, above EMA200, RSI 50-80, Volume > MA
        long_signal = (prev_pdi <= prev_mdi) and (current_pdi > current_mdi) and (current_adx > self.adx_threshold) and (current_adx > prev_adx) and (current_close > current_ema) and (current_rsi > 50) and (current_rsi < 80) and (current_vol > current_vol_ma)
        # 🌙 Moon Dev: Enhanced with RSI momentum filter (bullish but not overbought) and volume surge for higher-quality entries, reducing false signals and boosting profitability 🚀

        if long_signal and not self.position:
            risk_amount = self.risk_per_trade * self.equity
            risk_per_unit = self.atr_multiplier * current_atr
            if risk_per_unit > 0:
                position_size = risk_amount / risk_per_unit  # 🌙 Moon Dev: Removed int(round()) to allow fractional sizing for precise risk control and better capital efficiency 💰
                sl_price = current_close - risk_per_unit
                tp_price = current_close + (self.tp_multiplier * current_atr)
                self.buy(size=position_size, sl=sl_price, tp=tp_price)
                print(f"🌙 Moon Dev: Entering LONG at {current_close:.2f} | Size: {position_size:.4f} | SL: {sl_price:.2f} | TP: {tp_price:.2f} | ADX: {current_adx:.2f} | RSI: {current_rsi:.2f} 🚀✨")

        # Short entry: -DI crosses above +DI, ADX > 20, ADX rising, below EMA200, RSI 20-50, Volume > MA
        short_signal = (prev_mdi <= prev_pdi) and (current_mdi > current_pdi) and (current_adx > self.adx_threshold) and (current_adx > prev_adx) and (current_close < current_ema) and (current_rsi < 50) and (current_rsi > 20) and (current_vol > current_vol_ma)
        # 🌙 Moon Dev: Symmetric enhancements for shorts with RSI (bearish but not oversold) and volume to capture more downside opportunities symmetrically 📉

        if short_signal and not self.position:
            risk_amount = self.risk_per_trade * self.equity
            risk_per_unit = self.atr_multiplier * current_atr
            if risk_per_unit > 0:
                position_size = risk_amount / risk_per_unit  # 🌙 Moon Dev: Fractional sizing applied to shorts for optimized exposure ✨
                sl_price = current_close + risk_per_unit
                tp_price = current_close - (self.tp_multiplier * current_atr)
                self.sell(size=position_size, sl=sl_price, tp=tp_price)
                print(f"🌙 Moon Dev: Entering SHORT at {current_close:.2f} | Size: {position_size:.4f} | SL: {sl_price:.2f} | TP: {tp_price:.2f} | ADX: {current_adx:.2f} | RSI: {current_rsi:.2f} 🚀✨")

        # Exit conditions for both long and short
        if self.position:
            weakening = current_adx < self.adx_weak
            if self.position.is_long:
                reversal = (prev_mdi <= prev_pdi) and (current_mdi > current_pdi)
                if reversal or weakening:
                    self.position.close()
                    exit_reason = "Reversal" if reversal else "Weakening Trend"
                    print(f"🌙 Moon Dev: Exiting LONG at {current_close:.2f} | Reason: {exit_reason} | ADX: {current_adx:.2f} | RSI: {current_rsi:.2f} 📉💫")
            elif self.position.is_short:
                reversal = (prev_pdi <= prev_mdi) and (current_pdi > current_mdi)
                if reversal or weakening:
                    self.position.close()
                    exit_reason = "Reversal" if reversal else "Weakening Trend"
                    print(f"🌙 Moon Dev: Exiting SHORT at {current_close:.2f} | Reason: {exit_reason} | ADX: {current_adx:.2f} | RSI: {current_rsi:.2f} 📉💫")
            # 🌙 Moon Dev: Retained reversal and weakening exits with added RSI print for monitoring; combined with higher TP for better profit capture while SL cuts losses early ⚡

# Run backtest
bt = Backtest(data, DirectionalVigor, cash=1000000, commission=0.002, exclusive_orders=True)
stats = bt.run()
print(stats)