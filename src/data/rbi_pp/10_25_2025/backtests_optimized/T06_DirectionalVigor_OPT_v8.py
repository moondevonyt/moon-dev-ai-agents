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
    adx_weak = 25  # 🌙 Moon Dev: Kept ADX weak threshold aligned for trend strength monitoring ✨
    risk_per_trade = 0.01  # 1% risk, balanced for growth without excessive drawdown
    atr_multiplier = 2.0
    tp_multiplier = 6.0  # 🌙 Moon Dev: Increased to 3:1 RR for capturing larger trends and boosting returns ✨
    ema_period = 50  # 🌙 Moon Dev: Shortened from 200 to 50 for faster trend response on 15m timeframe ✨
    rsi_period = 14
    vol_period = 20

    def init(self):
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=self.adx_period)
        self.pdi = self.I(talib.PLUS_DI, self.data.High, self.data.Low, self.data.Close, timeperiod=self.adx_period)
        self.mdi = self.I(talib.MINUS_DI, self.data.High, self.data.Low, self.data.Close, timeperiod=self.adx_period)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=self.adx_period)
        self.ema50 = self.I(talib.EMA, self.data.Close, timeperiod=self.ema_period)  # 🌙 Moon Dev: Switched to EMA50 for quicker trend confirmation ✨
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=self.rsi_period)  # 🌙 Moon Dev: Added RSI for momentum filter to avoid weak entries ✨
        self.vol_ma = self.I(talib.SMA, self.data.Volume, timeperiod=self.vol_period)  # 🌙 Moon Dev: Added Volume MA for confirming conviction in signals ✨
        self.entry_price = 0
        self.position_type = None
        print("🌙 Moon Dev: Indicators initialized with EMA50, RSI, Volume MA, and trailing stop setup for optimized returns ✨")

    def next(self):
        if len(self.data) < 51:  # 🌙 Moon Dev: Adjusted for EMA50 and other indicators to ensure sufficient data ✨
            return

        current_adx = self.adx[-1]
        prev_adx = self.adx[-2]
        current_pdi = self.pdi[-1]
        prev_pdi = self.pdi[-2]
        current_mdi = self.mdi[-1]
        prev_mdi = self.mdi[-2]
        current_atr = self.atr[-1]
        current_close = self.data.Close[-1]
        current_ema = self.ema50[-1]
        current_rsi = self.rsi[-1]
        current_vol = self.data.Volume[-1]
        current_vol_ma = self.vol_ma[-1]

        # Long entry: +DI crosses above -DI, ADX > 25, ADX rising, above EMA50, RSI > 50, Volume > MA
        long_signal = (prev_pdi <= prev_mdi) and (current_pdi > current_mdi) and (current_adx > self.adx_threshold) and (current_adx > prev_adx) and (current_close > current_ema) and (current_rsi > 50) and (current_vol > current_vol_ma)
        # 🌙 Moon Dev: Enhanced with RSI >50 and Volume filter for higher-quality, momentum-backed entries to reduce false signals ✨

        if long_signal and not self.position:
            risk_amount = self.risk_per_trade * self.equity
            risk_per_unit = self.atr_multiplier * current_atr
            if risk_per_unit > 0:
                position_size = risk_amount / risk_per_unit  # 🌙 Moon Dev: Allow fractional sizing for precise risk allocation and better capital efficiency ✨
                sl_price = current_close - risk_per_unit
                tp_price = current_close + (self.tp_multiplier * current_atr)
                self.buy(size=position_size, sl=sl_price, tp=tp_price)
                self.entry_price = current_close  # Approximate entry for trailing
                self.position_type = 'long'
                print(f"🌙 Moon Dev: Entering LONG at {current_close:.2f} | Size: {position_size:.4f} | SL: {sl_price:.2f} | TP: {tp_price:.2f} | ADX: {current_adx:.2f} | RSI: {current_rsi:.2f} 🚀✨")

        # Short entry: -DI crosses above +DI, ADX > 25, ADX rising, below EMA50, RSI < 50, Volume > MA
        short_signal = (prev_mdi <= prev_pdi) and (current_mdi > current_pdi) and (current_adx > self.adx_threshold) and (current_adx > prev_adx) and (current_close < current_ema) and (current_rsi < 50) and (current_vol > current_vol_ma)
        # 🌙 Moon Dev: Symmetric enhancements with RSI <50 and Volume for robust short opportunities ✨

        if short_signal and not self.position:
            risk_amount = self.risk_per_trade * self.equity
            risk_per_unit = self.atr_multiplier * current_atr
            if risk_per_unit > 0:
                position_size = risk_amount / risk_per_unit  # 🌙 Moon Dev: Fractional sizing for shorts as well ✨
                sl_price = current_close + risk_per_unit
                tp_price = current_close - (self.tp_multiplier * current_atr)
                self.sell(size=position_size, sl=sl_price, tp=tp_price)
                self.entry_price = current_close  # Approximate entry for trailing
                self.position_type = 'short'
                print(f"🌙 Moon Dev: Entering SHORT at {current_close:.2f} | Size: {position_size:.4f} | SL: {sl_price:.2f} | TP: {tp_price:.2f} | ADX: {current_adx:.2f} | RSI: {current_rsi:.2f} 🚀✨")

        # Trailing stop logic for both long and short
        if self.position and self.entry_price > 0:
            if self.position_type == 'long':
                profit_dist = current_close - self.entry_price
                if profit_dist > self.atr_multiplier * current_atr:
                    trail_sl = current_close - self.atr_multiplier * current_atr
                    if self.position.sl is None or trail_sl > self.position.sl:
                        self.position.sl = trail_sl
                        print(f"🌙 Moon Dev: Trailing LONG SL to {trail_sl:.2f} | Profit Dist: {profit_dist:.2f} ✨")
            elif self.position_type == 'short':
                profit_dist = self.entry_price - current_close
                if profit_dist > self.atr_multiplier * current_atr:
                    trail_sl = current_close + self.atr_multiplier * current_atr
                    if self.position.sl is None or trail_sl < self.position.sl:
                        self.position.sl = trail_sl
                        print(f"🌙 Moon Dev: Trailing SHORT SL to {trail_sl:.2f} | Profit Dist: {profit_dist:.2f} ✨")
            # 🌙 Moon Dev: Added ATR-based trailing stops after initial profit threshold to lock in gains during strong trends ✨

        # Exit conditions for both long and short
        if self.position:
            weakening = current_adx < self.adx_weak
            if self.position.is_long:
                reversal = (prev_mdi <= prev_pdi) and (current_mdi > current_pdi)
                if reversal or weakening:
                    self.position.close()
                    exit_reason = "Reversal" if reversal else "Weakening Trend"
                    print(f"🌙 Moon Dev: Exiting LONG at {current_close:.2f} | Reason: {exit_reason} | ADX: {current_adx:.2f} 📉💫")
                    self.entry_price = 0
                    self.position_type = None
            elif self.position.is_short:
                reversal = (prev_pdi <= prev_mdi) and (current_pdi > current_mdi)
                if reversal or weakening:
                    self.position.close()
                    exit_reason = "Reversal" if reversal else "Weakening Trend"
                    print(f"🌙 Moon Dev: Exiting SHORT at {current_close:.2f} | Reason: {exit_reason} | ADX: {current_adx:.2f} 📉💫")
                    self.entry_price = 0
                    self.position_type = None
            # 🌙 Moon Dev: Retained reversal and weakening exits, now integrated with trailing for comprehensive profit protection ✨

# Run backtest
bt = Backtest(data, DirectionalVigor, cash=1000000, commission=0.002, exclusive_orders=True)
stats = bt.run()
print(stats)