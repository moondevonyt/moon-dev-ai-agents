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
    adx_period = 10  # 🌙 Moon Dev: Reduced ADX period to 10 for faster signal detection and more trading opportunities while maintaining trend strength ✨
    adx_threshold = 20  # 🌙 Moon Dev: Lowered threshold to 20 to capture more emerging trends, increasing trade frequency for higher returns 🚀
    adx_weak = 20  # 🌙 Moon Dev: Adjusted to match new threshold for consistent weakening detection 💫
    risk_per_trade = 0.015  # 🌙 Moon Dev: Increased to 1.5% risk per trade to amplify returns while still managing drawdown 📈
    atr_multiplier = 2.0
    tp_multiplier = 6.0  # 🌙 Moon Dev: Boosted to 3:1 reward-to-risk ratio to capture larger moves in trending markets for target return push ✨
    trail_activation = 2.0  # ATR multiple to activate trailing
    trail_distance = 1.5  # ATR multiple for trailing stop distance

    def init(self):
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=self.adx_period)
        self.pdi = self.I(talib.PLUS_DI, self.data.High, self.data.Low, self.data.Close, timeperiod=self.adx_period)
        self.mdi = self.I(talib.MINUS_DI, self.data.High, self.data.Low, self.data.Close, timeperiod=self.adx_period)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=self.adx_period)
        self.ema200 = self.I(talib.EMA, self.data.Close, timeperiod=200)  # 🌙 Moon Dev: Retained 200 EMA for robust trend filtering ✨
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14)  # 🌙 Moon Dev: Added RSI for momentum confirmation to filter high-quality entries and avoid overextended moves 📊
        self.avg_vol = self.I(talib.SMA, self.data.Volume, timeperiod=20)  # 🌙 Moon Dev: Added volume SMA for liquidity filter to ensure entries on supported volume spikes 🚀
        self.entry_price = 0
        self.breakeven = False
        self.initial_sl = 0
        print("🌙 Moon Dev: Enhanced DirectionalVigor with RSI, volume filters, faster ADX, higher RR, and trailing stops for optimized returns! ✨")

    def next(self):
        if len(self.data) < 201:  # 🌙 Moon Dev: Kept buffer for EMA200 and added indicators initialization safety ✨
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
        avg_vol = self.avg_vol[-1]

        # Long entry: +DI crosses above -DI, ADX > 20, ADX rising, above EMA200, RSI > 45 (momentum), volume > 1.2x avg
        long_signal = (prev_pdi <= prev_mdi) and (current_pdi > current_mdi) and (current_adx > self.adx_threshold) and (current_adx > prev_adx) and (current_close > current_ema) and (current_rsi > 45) and (current_vol > avg_vol * 1.2)
        # 🌙 Moon Dev: Integrated RSI and volume filters to tighten entries, reducing false signals and focusing on strong, liquid momentum setups for better win rate and returns ✨

        if long_signal and not self.position:
            risk_amount = self.risk_per_trade * self._broker.starting_cash if self._broker.starting_cash else self.risk_per_trade * self.equity  # 🌙 Moon Dev: Use starting cash for consistent risk calc in backtest 📊
            risk_per_unit = self.atr_multiplier * current_atr
            if risk_per_unit > 0:
                position_size = risk_amount / risk_per_unit
                max_size = (self.equity / current_close) * 0.95  # 🌙 Moon Dev: Cap size to 95% of available equity to prevent over-leveraging in spot trading 💰
                position_size = min(position_size, max_size)
                position_size = max(0.01, round(position_size, 2))  # 🌙 Moon Dev: Allow fractional sizes for precision in crypto trading, min 0.01 to avoid zero trades ✨
                sl_price = current_close - risk_per_unit
                tp_price = current_close + (self.tp_multiplier * current_atr)
                self.buy(size=position_size, sl=sl_price, tp=tp_price)
                self.entry_price = current_close
                self.breakeven = False
                self.initial_sl = sl_price
                print(f"🌙 Moon Dev: Entering LONG at {current_close:.2f} | Size: {position_size} | SL: {sl_price:.2f} | TP: {tp_price:.2f} | ADX: {current_adx:.2f} | RSI: {current_rsi:.2f} 🚀✨")

        # Short entry: -DI crosses above +DI, ADX > 20, ADX rising, below EMA200, RSI < 55, volume > 1.2x avg
        short_signal = (prev_mdi <= prev_pdi) and (current_mdi > current_pdi) and (current_adx > self.adx_threshold) and (current_adx > prev_adx) and (current_close < current_ema) and (current_rsi < 55) and (current_vol > avg_vol * 1.2)
        # 🌙 Moon Dev: Symmetric enhancements for shorts with RSI/volume to balance opportunities in downtrends 📉

        if short_signal and not self.position:
            risk_amount = self.risk_per_trade * self._broker.starting_cash if self._broker.starting_cash else self.risk_per_trade * self.equity
            risk_per_unit = self.atr_multiplier * current_atr
            if risk_per_unit > 0:
                position_size = risk_amount / risk_per_unit
                max_size = (self.equity / current_close) * 0.95
                position_size = min(position_size, max_size)
                position_size = max(0.01, round(position_size, 2))
                sl_price = current_close + risk_per_unit
                tp_price = current_close - (self.tp_multiplier * current_atr)
                self.sell(size=position_size, sl=sl_price, tp=tp_price)
                self.entry_price = current_close
                self.breakeven = False
                self.initial_sl = sl_price
                print(f"🌙 Moon Dev: Entering SHORT at {current_close:.2f} | Size: {position_size} | SL: {sl_price:.2f} | TP: {tp_price:.2f} | ADX: {current_adx:.2f} | RSI: {current_rsi:.2f} 🚀✨")

        # Trailing stop and breakeven logic for both long and short
        if self.position:
            activation_level = self.trail_activation * current_atr
            trail_level = self.trail_distance * current_atr

            if self.position.is_long:
                profit_distance = current_close - self.entry_price
                if profit_distance > activation_level:
                    if not self.breakeven:
                        # Move to breakeven
                        self.position.sl = max(self.position.sl, self.entry_price)
                        self.breakeven = True
                        print(f"🌙 Moon Dev: LONG breakeven activated at {self.entry_price:.2f} | Profit: {profit_distance:.2f} 💫")
                    else:
                        # Trail stop
                        new_sl = current_close - trail_level
                        if new_sl > self.position.sl:
                            self.position.sl = new_sl
                            print(f"🌙 Moon Dev: LONG trailing SL updated to {new_sl:.2f} | Current: {current_close:.2f} 📈✨")
            elif self.position.is_short:
                profit_distance = self.entry_price - current_close
                if profit_distance > activation_level:
                    if not self.breakeven:
                        # Move to breakeven
                        self.position.sl = min(self.position.sl, self.entry_price)
                        self.breakeven = True
                        print(f"🌙 Moon Dev: SHORT breakeven activated at {self.entry_price:.2f} | Profit: {profit_distance:.2f} 💫")
                    else:
                        # Trail stop
                        new_sl = current_close + trail_level
                        if new_sl < self.position.sl:
                            self.position.sl = new_sl
                            print(f"🌙 Moon Dev: SHORT trailing SL updated to {new_sl:.2f} | Current: {current_close:.2f} 📉✨")

            # Existing exit conditions for reversal or weakening
            weakening = current_adx < self.adx_weak
            if self.position.is_long:
                reversal = (prev_mdi <= prev_pdi) and (current_mdi > current_pdi)
                if reversal or weakening:
                    self.position.close()
                    exit_reason = "Reversal" if reversal else "Weakening Trend"
                    print(f"🌙 Moon Dev: Exiting LONG at {current_close:.2f} | Reason: {exit_reason} | ADX: {current_adx:.2f} | Trailing integrated 📊💫")
                    self.breakeven = False  # Reset for next trade
            elif self.position.is_short:
                reversal = (prev_pdi <= prev_mdi) and (current_pdi > current_mdi)
                if reversal or weakening:
                    self.position.close()
                    exit_reason = "Reversal" if reversal else "Weakening Trend"
                    print(f"🌙 Moon Dev: Exiting SHORT at {current_close:.2f} | Reason: {exit_reason} | ADX: {current_adx:.2f} | Trailing integrated 📊💫")
                    self.breakeven = False  # Reset for next trade
            # 🌙 Moon Dev: Enhanced with trailing stops to lock in profits during strong trends, boosting overall returns while protecting gains 🚀

# Run backtest
bt = Backtest(data, DirectionalVigor, cash=1000000, commission=0.002, exclusive_orders=True)
stats = bt.run()
print(stats)