import pandas as pd
import numpy as np
from backtesting import Backtest, Strategy
import talib

path = '/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv'

data = pd.read_csv(path)
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data = data.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'})
data = data.set_index(pd.to_datetime(data['datetime']))
data = data.drop(columns=['datetime'])

class MomentumSqueeze(Strategy):
    def init(self):
        # 🌙 Moon Dev: Tightened BB squeeze threshold to 0.07 for even higher quality setups, reducing false signals (Entry Optimization)
        self.bb_upper, self.bb_middle, self.bb_lower = self.I(talib.BBANDS, self.data.Close, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)
        self.macd_line, self.signal_line, self.hist = self.I(talib.MACD, self.data.Close, fastperiod=12, slowperiod=26, signalperiod=9)
        # 🌙 Moon Dev: Switched to EMAs for faster trend detection (Indicator Optimization)
        self.ema20 = self.I(talib.EMA, self.data.Close, timeperiod=20)
        self.ema50 = self.I(talib.EMA, self.data.Close, timeperiod=50)
        # 🌙 Moon Dev: Added longer-term EMA200 for stronger trend regime filter (Market Regime Filters)
        self.ema200 = self.I(talib.EMA, self.data.Close, timeperiod=200)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        # 🌙 Moon Dev: Tightened RSI period to 10 and thresholds for sharper momentum signals (Indicator Optimization)
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=10)
        # 🌙 Moon Dev: Added ADX for trend strength filter to avoid choppy markets (Market Regime Filters)
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        self.vol_sma = self.I(talib.SMA, self.data.Volume, timeperiod=20)
        self.long_breakout_low = None
        self.short_breakout_high = None
        self.last_long_breakout = -100
        self.last_short_breakout = -100
        self.entry_price = 0.0
        self.initial_risk = 0.0
        self.sl = 0.0
        self.tp = 0.0
        self.partial_closed = False  # 🌙 Moon Dev: Flag for scaling out once (Exit Optimization)
        self.partial2_closed = False  # 🌙 Moon Dev: New flag for second partial scale-out at 4R (Exit Optimization)

    def _reset_pos(self):
        self.entry_price = 0.0
        self.initial_risk = 0.0
        self.sl = 0.0
        self.tp = 0.0
        self.partial_closed = False  # 🌙 Moon Dev: Reset scaling flag
        self.partial2_closed = False  # 🌙 Moon Dev: Reset second scaling flag

    def next(self):
        if len(self.data) < 250:
            return

        price = self.data.Close[-1]
        high = self.data.High[-1]
        low = self.data.Low[-1]
        volume = self.data.Volume[-1]
        upper = self.bb_upper[-1]
        lower = self.bb_lower[-1]
        middle = self.bb_middle[-1]
        bandwidth = (upper - lower) / middle

        # 🌙 Moon Dev: Adjusted print threshold to match new squeeze (0.07)
        if bandwidth < 0.07:
            print(f"🌙 Moon Dev: Squeeze detected! Bandwidth: {bandwidth:.4f} ✨")

        macd_l = self.macd_line[-1]
        sig_l = self.signal_line[-1]
        macd_p = self.macd_line[-2]
        sig_p = self.signal_line[-2]
        bull_cross = macd_l > sig_l and macd_p <= sig_p
        bear_cross = macd_l < sig_l and macd_p >= sig_p
        # 🌙 Moon Dev: Increased volume filter to 2x for even stronger confirmation, filtering out weaker breakouts (Entry Optimization)
        vol_rising = volume > 2.0 * self.vol_sma[-1]
        # 🌙 Moon Dev: Enhanced trend filter with EMA20 > EMA50 > EMA200 for bullish regime only (Market Regime Filters)
        trend_up = self.ema20[-1] > self.ema50[-1] > self.ema200[-1]
        trend_down = self.ema20[-1] < self.ema50[-1] < self.ema200[-1]
        # 🌙 Moon Dev: Tightened RSI filters to >60/<40 with shorter period for stronger, quicker momentum confirmation (Indicator Optimization)
        rsi_long_ok = self.rsi[-1] > 60
        rsi_short_ok = self.rsi[-1] < 40
        # 🌙 Moon Dev: Raised ADX threshold to >30 for very strong trends, avoiding marginal setups (Market Regime Filters)
        adx_strong = self.adx[-1] > 30

        current_bar = len(self.data) - 1

        # Reset expired breakouts
        # 🌙 Moon Dev: Extended window to 10 bars for more entry opportunities while keeping discipline (Entry Optimization)
        if self.last_long_breakout >= 0 and current_bar - self.last_long_breakout > 10:
            self.last_long_breakout = -100
            self.long_breakout_low = None
            print("⏰ Long breakout window expired, resetting")
        if self.last_short_breakout >= 0 and current_bar - self.last_short_breakout > 10:
            self.last_short_breakout = -100
            self.short_breakout_high = None
            print("⏰ Short breakout window expired, resetting")

        # Detect new breakouts
        # 🌙 Moon Dev: Tightened breakout detection to new squeeze threshold (0.07)
        if bandwidth < 0.07 and price > upper:
            self.long_breakout_low = low
            self.last_long_breakout = current_bar
            print(f"🚀 Bullish breakout detected at {price}! Low: {low}")
        if bandwidth < 0.07 and price < lower:
            self.short_breakout_high = high
            self.last_short_breakout = current_bar
            print(f"📉 Bearish breakout detected at {price}! High: {high}")

        # Long entry
        bars_since_long = current_bar - self.last_long_breakout if self.last_long_breakout >= 0 else 100
        if (self.last_long_breakout >= 0 and bars_since_long <= 10 and bull_cross and vol_rising and trend_up and rsi_long_ok and adx_strong and
            not self.position and self.long_breakout_low is not None):
            sl = self.long_breakout_low - self.atr[-1]
            entry = price
            risk = entry - sl
            if risk > 0:
                # 🌙 Moon Dev: Increased risk to 4% for amplified returns with volatility-adjusted sizing (Risk Management)
                risk_amount = self.equity * 0.04
                pos_size = risk_amount / risk
                # 🌙 Moon Dev: Allow fractional position sizes for precise risk control (Risk Management)
                pos_size = pos_size  # Keep as float
                # 🌙 Moon Dev: Boosted RR to 5:1 to capture larger trends and drive higher profitability (Exit Optimization)
                tp = entry + 5 * risk
                self.buy(size=pos_size)
                self.entry_price = entry
                self.initial_risk = risk
                self.sl = sl
                self.tp = tp
                print(f"🌙 Moon Dev: LONG ENTRY at {entry}, SL: {sl}, TP: {tp}, Size: {pos_size}, Risk: {risk_amount:.2f} 🚀")
                if bull_cross:
                    print(f"📈 Bullish MACD cross confirmed!")

        # Short entry
        bars_since_short = current_bar - self.last_short_breakout if self.last_short_breakout >= 0 else 100
        if (self.last_short_breakout >= 0 and bars_since_short <= 10 and bear_cross and vol_rising and trend_down and rsi_short_ok and adx_strong and
            not self.position and self.short_breakout_high is not None):
            sl = self.short_breakout_high + self.atr[-1]
            entry = price
            risk = sl - entry
            if risk > 0:
                # 🌙 Moon Dev: Increased risk to 4% for amplified returns with volatility-adjusted sizing (Risk Management)
                risk_amount = self.equity * 0.04
                pos_size = risk_amount / risk
                # 🌙 Moon Dev: Allow fractional position sizes for precise risk control (Risk Management)
                pos_size = pos_size  # Keep as float
                # 🌙 Moon Dev: Boosted RR to 5:1 to capture larger trends and drive higher profitability (Exit Optimization)
                tp = entry - 5 * risk
                self.sell(size=pos_size)
                self.entry_price = entry
                self.initial_risk = risk
                self.sl = sl
                self.tp = tp
                print(f"🌙 Moon Dev: SHORT ENTRY at {entry}, SL: {sl}, TP: {tp}, Size: {pos_size}, Risk: {risk_amount:.2f} 📉")
                if bear_cross:
                    print(f"📉 Bearish MACD cross confirmed!")

        # Manage open positions
        if self.position:
            entry_price = self.entry_price
            # SL and TP checks
            if self.position.is_long:
                if self.data.Low[-1] <= self.sl:
                    self.position.close()
                    print(f"🌙 Moon Dev: SL hit for long, closing at {price} 💥")
                    self._reset_pos()
                    return
                if self.data.High[-1] >= self.tp:
                    self.position.close()
                    print(f"🌙 Moon Dev: TP hit for long, closing at {price} 🎯")
                    self._reset_pos()
                    return
            else:
                if self.data.High[-1] >= self.sl:
                    self.position.close()
                    print(f"🌙 Moon Dev: SL hit for short, closing at {price} 💥")
                    self._reset_pos()
                    return
                if self.data.Low[-1] <= self.tp:
                    self.position.close()
                    print(f"🌙 Moon Dev: TP hit for short, closing at {price} 🎯")
                    self._reset_pos()
                    return
            # 🌙 Moon Dev: Relaxed bandwidth exit to 0.4 to allow positions to run longer in volatile expansions (Exit Optimization)
            if bandwidth > 0.4:
                self.position.close()
                print(f"🌙 Bandwidth expanded to {bandwidth:.4f}, exiting position 💥")
                self._reset_pos()
                return
            # 🌙 Moon Dev: Enhanced scaling out: 50% at 2R and 25% at 4R to lock profits progressively (Exit Optimization)
            if self.position.is_long:
                favorable_move = price - entry_price
                if favorable_move >= 2 * self.initial_risk and not self.partial_closed:
                    partial_size = abs(self.position.size) * 0.5
                    self.sell(size=partial_size)
                    self.partial_closed = True
                    print(f"🌙 Moon Dev: Scaled out 50% of long at 2R, remaining size: {self.position.size} 💰")
                if favorable_move >= 4 * self.initial_risk and not self.partial2_closed and self.partial_closed:
                    partial_size2 = abs(self.position.size) * 0.5  # 50% of remaining (25% of original)
                    self.sell(size=partial_size2)
                    self.partial2_closed = True
                    print(f"🌙 Moon Dev: Scaled out additional 25% of original long at 4R, remaining size: {self.position.size} 💰")
                # Trailing stop after 1:1
                if favorable_move >= self.initial_risk:
                    # 🌙 Moon Dev: Adjusted trailing to EMA50 ± ATR for smoother trailing with less noise (Exit Optimization)
                    new_sl = max(self.sl, self.ema50[-1] - self.atr[-1])
                    if new_sl > self.sl:
                        self.sl = new_sl
                        print(f"🌙 Trailing long SL to {new_sl} ✨")
                # MACD histogram reverse
                if self.hist[-1] <= 0:
                    self.position.close()
                    print(f"🌙 MACD histogram turned negative, closing long 📊")
                    self._reset_pos()
                    return
            else:  # short
                favorable_move = entry_price - price
                if favorable_move >= 2 * self.initial_risk and not self.partial_closed:
                    partial_size = abs(self.position.size) * 0.5
                    self.buy(size=partial_size)
                    self.partial_closed = True
                    print(f"🌙 Moon Dev: Scaled out 50% of short at 2R, remaining size: {self.position.size} 💰")
                if favorable_move >= 4 * self.initial_risk and not self.partial2_closed and self.partial_closed:
                    partial_size2 = abs(self.position.size) * 0.5  # 50% of remaining (25% of original)
                    self.buy(size=partial_size2)
                    self.partial2_closed = True
                    print(f"🌙 Moon Dev: Scaled out additional 25% of original short at 4R, remaining size: {self.position.size} 💰")
                # Trailing stop after 1:1
                if favorable_move >= self.initial_risk:
                    # 🌙 Moon Dev: Adjusted trailing to EMA50 ± ATR for smoother trailing with less noise (Exit Optimization)
                    new_sl = min(self.sl, self.ema50[-1] + self.atr[-1])
                    if new_sl < self.sl:
                        self.sl = new_sl
                        print(f"🌙 Trailing short SL to {new_sl} ✨")
                # MACD histogram reverse
                if self.hist[-1] >= 0:
                    self.position.close()
                    print(f"🌙 MACD histogram turned positive, closing short 📊")
                    self._reset_pos()
                    return

bt = Backtest(data, MomentumSqueeze, cash=1000000, commission=0.001)
stats = bt.run()
print(stats)
print(stats._strategy)