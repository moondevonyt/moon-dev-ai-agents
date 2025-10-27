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
    adx_threshold = 25  # 🌙 Moon Dev: Kept at 25 to maintain trade frequency while adding filters for quality ✨
    adx_weak = 25  # 🌙 Moon Dev: Tightened to match threshold for quicker exits from weakening trends ✨
    risk_per_trade = 0.02  # 🌙 Moon Dev: Increased to 2% to amplify returns while monitoring drawdowns ✨
    atr_multiplier = 2.0
    tp_multiplier = 6.0  # 🌙 Moon Dev: Increased to 3:1 RR for higher profit potential in trending moves ✨
    trail_multiplier = 1.5  # 🌙 Moon Dev: New trailing stop multiplier for dynamic exits to capture more trend profits ✨
    rsi_period = 14
    rsi_long_min = 45  # 🌙 Moon Dev: RSI filter to ensure bullish momentum for longs ✨
    rsi_long_max = 75  # 🌙 Moon Dev: Avoid overbought entries for longs ✨
    rsi_short_min = 25  # 🌙 Moon Dev: Avoid oversold entries for shorts ✨
    rsi_short_max = 55  # 🌙 Moon Dev: Ensure bearish momentum for shorts ✨
    vol_period = 20
    vol_multiplier = 1.5  # 🌙 Moon Dev: Volume filter to confirm conviction in signals ✨
    trail_activation = 2.0  # 🌙 Moon Dev: Activate trailing after 2x ATR profit to let winners run ✨

    def init(self):
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=self.adx_period)
        self.pdi = self.I(talib.PLUS_DI, self.data.High, self.data.Low, self.data.Close, timeperiod=self.adx_period)
        self.mdi = self.I(talib.MINUS_DI, self.data.High, self.data.Low, self.data.Close, timeperiod=self.adx_period)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=self.adx_period)
        self.ema200 = self.I(talib.EMA, self.data.Close, timeperiod=200)  # 🌙 Moon Dev: Retained 200 EMA for trend filter ✨
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=self.rsi_period)  # 🌙 Moon Dev: Added RSI for momentum confirmation to filter weak entries ✨
        self.vol_sma = self.I(talib.SMA, self.data.Volume, timeperiod=self.vol_period)  # 🌙 Moon Dev: Added volume SMA for liquidity/conviction filter ✨
        self.entry_price = 0
        self.entry_atr = 0
        self.trail_sl = 0
        self.trail_active = False
        print("🌙 Moon Dev: Indicators initialized with RSI, Volume SMA, and trailing stop support for enhanced performance ✨")

    def next(self):
        if len(self.data) < 201:  # 🌙 Moon Dev: Ensures all indicators (EMA200, RSI, Vol SMA) are ready ✨
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
        vol_condition = current_vol > (self.vol_multiplier * self.vol_sma[-1])  # 🌙 Moon Dev: Volume surge filter for higher-quality setups ✨

        # Long entry: +DI crosses above -DI, ADX > 25, ADX rising, above EMA200, RSI in favorable range, volume confirmation
        long_signal = (prev_pdi <= prev_mdi) and (current_pdi > current_mdi) and (current_adx > self.adx_threshold) and (current_adx > prev_adx) and (current_close > current_ema) and vol_condition and (self.rsi_long_min < current_rsi < self.rsi_long_max)
        # 🌙 Moon Dev: Enhanced with RSI and volume filters to tighten entries, reducing false signals and improving win rate ✨

        if long_signal and not self.position:
            risk_amount = self.risk_per_trade * self.equity
            risk_per_unit = self.atr_multiplier * current_atr
            if risk_per_unit > 0:
                position_size = risk_amount / risk_per_unit  # 🌙 Moon Dev: Switched to float sizing for precise risk control and better capital efficiency ✨
                sl_price = current_close - risk_per_unit
                tp_price = current_close + (self.tp_multiplier * current_atr)
                self.buy(size=position_size, sl=sl_price, tp=tp_price)
                self.entry_price = self.position.avg_price
                self.entry_atr = current_atr
                self.trail_sl = sl_price
                self.trail_active = False
                print(f"🌙 Moon Dev: Entering LONG at {current_close:.2f} | Size: {position_size:.4f} | SL: {sl_price:.2f} | TP: {tp_price:.2f} | ADX: {current_adx:.2f} | RSI: {current_rsi:.2f} 🚀✨")

        # Short entry: -DI crosses above +DI, ADX > 25, ADX rising, below EMA200, RSI in favorable range, volume confirmation
        short_signal = (prev_mdi <= prev_pdi) and (current_mdi > current_pdi) and (current_adx > self.adx_threshold) and (current_adx > prev_adx) and (current_close < current_ema) and vol_condition and (self.rsi_short_min < current_rsi < self.rsi_short_max)
        # 🌙 Moon Dev: Symmetric enhancements with RSI and volume for shorts to capture more opportunities reliably ✨

        if short_signal and not self.position:
            risk_amount = self.risk_per_trade * self.equity
            risk_per_unit = self.atr_multiplier * current_atr
            if risk_per_unit > 0:
                position_size = risk_amount / risk_per_unit  # 🌙 Moon Dev: Float sizing for precision in shorts as well ✨
                sl_price = current_close + risk_per_unit
                tp_price = current_close - (self.tp_multiplier * current_atr)
                self.sell(size=position_size, sl=sl_price, tp=tp_price)
                self.entry_price = self.position.avg_price
                self.entry_atr = current_atr
                self.trail_sl = sl_price
                self.trail_active = False
                print(f"🌙 Moon Dev: Entering SHORT at {current_close:.2f} | Size: {position_size:.4f} | SL: {sl_price:.2f} | TP: {tp_price:.2f} | ADX: {current_adx:.2f} | RSI: {current_rsi:.2f} 🚀✨")

        # Dynamic trailing stop and exit logic for both long and short
        if self.position:
            # Update trailing stop
            if self.position.is_long:
                profit = current_close - self.entry_price
                if not self.trail_active and profit > (self.trail_activation * self.entry_atr):
                    self.trail_active = True
                if self.trail_active:
                    new_sl = current_close - (self.trail_multiplier * current_atr)
                    if new_sl > self.trail_sl:
                        self.trail_sl = new_sl
                        self.position.sl = self.trail_sl
                        print(f"🌙 Moon Dev: Trailing SL updated for LONG to {self.trail_sl:.2f} 📈✨")
            elif self.position.is_short:
                profit = self.entry_price - current_close
                if not self.trail_active and profit > (self.trail_activation * self.entry_atr):
                    self.trail_active = True
                if self.trail_active:
                    new_sl = current_close + (self.trail_multiplier * current_atr)
                    if new_sl < self.trail_sl:
                        self.trail_sl = new_sl
                        self.position.sl = self.trail_sl
                        print(f"🌙 Moon Dev: Trailing SL updated for SHORT to {self.trail_sl:.2f} 📉✨")

            # Exit conditions: reversal or weakening trend (overrides if trailed SL not hit)
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
            # 🌙 Moon Dev: Integrated trailing stops with existing exits for better risk-reward; TP/SL handle automation, trailing captures trends ✨

# Run backtest
bt = Backtest(data, DirectionalVigor, cash=1000000, commission=0.002, exclusive_orders=True)
stats = bt.run()
print(stats)