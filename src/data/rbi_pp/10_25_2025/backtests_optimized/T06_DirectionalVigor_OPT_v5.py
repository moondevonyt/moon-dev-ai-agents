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
    adx_period = 10  # 🌙 Moon Dev: Reduced ADX period to 10 for increased sensitivity and more timely signals to capture more trends ✨
    adx_threshold = 20  # 🌙 Moon Dev: Lowered threshold to 20 to allow more entries in moderate trends, boosting trade frequency for higher returns 🚀
    adx_weak = 20  # 🌙 Moon Dev: Adjusted weakening threshold to match for consistent trend monitoring without premature exits 💫
    risk_per_trade = 0.02  # 🌙 Moon Dev: Increased risk to 2% per trade to amplify returns while still managing overall portfolio risk 📈
    atr_multiplier = 2.0
    ema_period = 50  # 🌙 Moon Dev: Shortened EMA to 50 periods for better responsiveness in 15m timeframe, reducing lag in trend detection ✨
    rsi_period = 14
    rsi_long_threshold = 50
    rsi_short_threshold = 50
    vol_ma_period = 20
    vol_multiplier = 1.1  # 🌙 Moon Dev: Added volume filter requiring 10% above average for entries to ensure conviction and avoid low-volume traps 🚀
    trail_start_mult = 2.0  # 🌙 Moon Dev: Start trailing after 2x ATR profit to let winners develop before protecting gains ✨
    trail_atr_mult = 1.5  # 🌙 Moon Dev: Trail SL at 1.5x ATR from entry to lock in profits dynamically, improving win rate and return potential 📈

    def init(self):
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=self.adx_period)
        self.pdi = self.I(talib.PLUS_DI, self.data.High, self.data.Low, self.data.Close, timeperiod=self.adx_period)
        self.mdi = self.I(talib.MINUS_DI, self.data.High, self.data.Low, self.data.Close, timeperiod=self.adx_period)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=self.adx_period)
        self.ema = self.I(talib.EMA, self.data.Close, timeperiod=self.ema_period)  # 🌙 Moon Dev: Updated to shorter EMA for faster trend alignment and more opportunities 💫
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=self.rsi_period)  # 🌙 Moon Dev: Added RSI for momentum confirmation to filter out weak signals and improve entry quality 🚀
        self.vol_ma = self.I(talib.SMA, self.data.Volume, timeperiod=self.vol_ma_period)  # 🌙 Moon Dev: Added volume moving average for liquidity filter to target high-conviction moves ✨
        self.entry_price = 0
        self.is_long_pos = False
        print("🌙 Moon Dev: Indicators initialized with RSI, Volume filter, shorter EMA/ADX, and trailing stop setup for optimized returns! 🚀✨")

    def next(self):
        if len(self.data) < 101:  # 🌙 Moon Dev: Adjusted buffer for shorter periods (ADX10 + EMA50 + others) to ensure stable initialization 💫
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
        current_rsi = self.rsi[-1]
        current_vol = self.data.Volume[-1]
        current_vol_ma = self.vol_ma[-1]

        # Long entry: +DI crosses above -DI, ADX > 20, ADX rising, above EMA50, RSI > 50, Volume > 1.1x MA
        long_signal = (prev_pdi <= prev_mdi) and (current_pdi > current_mdi) and (current_adx > self.adx_threshold) and (current_adx > prev_adx) and (current_close > current_ema) and (current_rsi > self.rsi_long_threshold) and (current_vol > current_vol_ma * self.vol_multiplier)
        # 🌙 Moon Dev: Enhanced entry with RSI momentum and volume filters to tighten quality, reducing false signals and targeting stronger moves for higher returns 📈

        if long_signal and not self.position:
            risk_amount = self.risk_per_trade * self.equity
            risk_per_unit = self.atr_multiplier * current_atr
            if risk_per_unit > 0:
                position_size = risk_amount / risk_per_unit
                position_size = int(round(position_size))  # 🌙 Moon Dev: Retained integer sizing with increased risk for balanced scaling ✨
                sl_price = current_close - risk_per_unit
                self.buy(size=position_size, sl=sl_price)  # 🌙 Moon Dev: Removed fixed TP to enable dynamic trailing for letting winners run longer 🚀
                self.entry_price = current_close
                self.is_long_pos = True
                print(f"🌙 Moon Dev: Entering LONG at {current_close:.2f} | Size: {position_size} | SL: {sl_price:.2f} | ADX: {current_adx:.2f} | RSI: {current_rsi:.2f} 🚀✨")

        # Short entry: -DI crosses above +DI, ADX > 20, ADX rising, below EMA50, RSI < 50, Volume > 1.1x MA
        short_signal = (prev_mdi <= prev_pdi) and (current_mdi > current_pdi) and (current_adx > self.adx_threshold) and (current_adx > prev_adx) and (current_close < current_ema) and (current_rsi < self.rsi_short_threshold) and (current_vol > current_vol_ma * self.vol_multiplier)
        # 🌙 Moon Dev: Symmetric enhancements for shorts with RSI and volume to capture downside with high conviction, doubling potential opportunities 💫

        if short_signal and not self.position:
            risk_amount = self.risk_per_trade * self.equity
            risk_per_unit = self.atr_multiplier * current_atr
            if risk_per_unit > 0:
                position_size = risk_amount / risk_per_unit
                position_size = int(round(position_size))
                sl_price = current_close + risk_per_unit
                self.sell(size=position_size, sl=sl_price)  # 🌙 Moon Dev: Removed fixed TP for trailing on shorts to maximize downside capture 📈
                self.entry_price = current_close
                self.is_long_pos = False
                print(f"🌙 Moon Dev: Entering SHORT at {current_close:.2f} | Size: {position_size} | SL: {sl_price:.2f} | ADX: {current_adx:.2f} | RSI: {current_rsi:.2f} 🚀✨")

        # Dynamic trailing stop and exit conditions for both long and short
        if self.position and self.entry_price > 0:
            # Trailing stop logic
            if self.is_long_pos:
                profit = current_close - self.entry_price
                if profit > self.trail_start_mult * current_atr:
                    trail_sl = self.entry_price + self.trail_atr_mult * current_atr
                    if self.position.sl is None or trail_sl > self.position.sl:
                        self.position.sl = trail_sl  # 🌙 Moon Dev: Update SL to trail profits, securing gains while allowing upside potential ✨
                reversal = (prev_mdi <= prev_pdi) and (current_mdi > current_pdi)
                weakening = current_adx < self.adx_weak
                if reversal or weakening:
                    self.position.close()
                    exit_reason = "Reversal" if reversal else "Weakening Trend"
                    print(f"🌙 Moon Dev: Exiting LONG at {current_close:.2f} | Reason: {exit_reason} | ADX: {current_adx:.2f} | Profit: {profit:.2f} 📉💫")
                    self.entry_price = 0
                    self.is_long_pos = False
            else:  # Short position
                profit = self.entry_price - current_close
                if profit > self.trail_start_mult * current_atr:
                    trail_sl = self.entry_price - self.trail_atr_mult * current_atr
                    if self.position.sl is None or trail_sl < self.position.sl:
                        self.position.sl = trail_sl  # 🌙 Moon Dev: Symmetric trailing for shorts to protect profits in downtrends 🚀
                reversal = (prev_pdi <= prev_mdi) and (current_pdi > current_mdi)
                weakening = current_adx < self.adx_weak
                if reversal or weakening:
                    self.position.close()
                    exit_reason = "Reversal" if reversal else "Weakening Trend"
                    print(f"🌙 Moon Dev: Exiting SHORT at {current_close:.2f} | Reason: {exit_reason} | ADX: {current_adx:.2f} | Profit: {profit:.2f} 📉💫")
                    self.entry_price = 0
                    self.is_long_pos = False
            # 🌙 Moon Dev: Integrated trailing stops with reversal/weakening exits to dynamically manage risk, letting winners run while cutting losers early for superior risk-adjusted returns 📈

# Run backtest
bt = Backtest(data, DirectionalVigor, cash=1000000, commission=0.002, exclusive_orders=True)
stats = bt.run()
print(stats)