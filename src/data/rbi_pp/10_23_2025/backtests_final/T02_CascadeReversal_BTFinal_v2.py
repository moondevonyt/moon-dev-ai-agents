import pandas as pd
import talib
from backtesting import Backtest, Strategy
import warnings
warnings.filterwarnings('ignore')

# Load and prepare data
path = '/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv'
data = pd.read_csv(path)
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data = data.set_index(pd.to_datetime(data['datetime']))
data = data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
})

class CascadeReversal(Strategy):
    atr_period = 14
    sma_period = 20
    risk_percent = 0.01
    max_bars_in_trade = 10

    def init(self):
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=self.atr_period)
        self.sma = self.I(talib.SMA, self.data.Close, timeperiod=self.sma_period)
        self.down_streak = 0
        self.post_down_streak = 0
        self.entry_bar = None
        self.fourth_close = None

    def next(self):
        current_close = self.data.Close[-1]
        prev_close = self.data.Close[-2] if len(self.data) > 1 else current_close

        # Update down streak (always, to build from start)
        if current_close < prev_close:
            self.down_streak += 1
            if self.down_streak == 1:
                print("🌙 Moon Dev: Down streak started! 1 📉")
            elif self.down_streak == 2:
                print("🌙 Moon Dev: Down streak: 2 📉📉")
            elif self.down_streak == 3:
                print("🌙 Moon Dev: Down streak: 3 📉📉📉")
            elif self.down_streak == 4:
                print("🌙 Moon Dev: Four consecutive down bars detected! Checking filters... 🔍")
        else:
            self.down_streak = 0
            print("🌙 Moon Dev: Down streak reset. Up bar! 📈")

        if len(self.data) < self.sma_period + 5:
            return

        # Invalidation check for fifth bar
        if self.position and self.fourth_close is not None:
            if current_close < self.fourth_close:
                self.sell()
                print(f"🌙 Moon Dev: Pattern invalidated - fifth bar closed down at {current_close}! Exiting. ❌")
                self.fourth_close = None
                self.post_down_streak = 0
                self.entry_bar = None
            else:
                print("🌙 Moon Dev: Fifth bar confirmed up! Pattern valid. ✅")
                self.fourth_close = None
                self.post_down_streak = 0
                self.entry_bar = len(self.data) - 1  # Adjust for entry bar count

        # Post-entry down streak management
        if self.position:
            if current_close < prev_close:
                self.post_down_streak += 1
                print(f"🌙 Moon Dev: Post-entry down bar #{self.post_down_streak} 📉")
                if self.post_down_streak >= 2:
                    self.sell()
                    print("🌙 Moon Dev: New down streak post-entry (2+ bars)! Exiting. ⚠️")
                    self.fourth_close = None
                    self.post_down_streak = 0
                    self.entry_bar = None
            else:
                self.post_down_streak = 0
                print("🌙 Moon Dev: Post-entry up bar, streak reset. 📈")

        # SMA trailing exit (crossover)
        if self.position and current_close < self.sma[-1] and prev_close >= self.sma[-2]:
            self.sell()
            print(f"🌙 Moon Dev: Price crossed below SMA({self.sma_period}) at {current_close}! Trailing exit. 📉")
            self.fourth_close = None
            self.post_down_streak = 0
            self.entry_bar = None

        # Time-based exit
        if self.position and self.entry_bar is not None and len(self.data) - self.entry_bar >= self.max_bars_in_trade:
            self.sell()
            print(f"🌙 Moon Dev: Time-based exit after {self.max_bars_in_trade} bars. ⏰")
            self.fourth_close = None
            self.post_down_streak = 0
            self.entry_bar = None

        # Entry logic
        if self.down_streak == 4 and not self.position:
            print("🌙 Moon Dev: Evaluating entry filters for CascadeReversal... ✨")

            # Volume filter
            if len(self.data) >= 4:
                avg_prior_vol = (self.data.Volume[-4] + self.data.Volume[-3] + self.data.Volume[-2]) / 3
                vol_filter = self.data.Volume[-1] < avg_prior_vol
                if not vol_filter:
                    print("🌙 Moon Dev: Volume filter failed - fourth bar volume too high! 🚫")
                    return
                print("🌙 Moon Dev: Volume filter passed - waning seller interest. 📊✅")
            else:
                vol_filter = True

            # Body size filter (progressively smaller)
            if len(self.data) >= 4:
                body1 = abs(self.data.Close[-4] - self.data.Open[-4])
                body2 = abs(self.data.Close[-3] - self.data.Open[-3])
                body3 = abs(self.data.Close[-2] - self.data.Open[-2])
                body4 = abs(self.data.Close[-1] - self.data.Open[-1])
                body_filter = (body4 < body3) and (body3 < body2) and (body2 < body1)
                if not body_filter:
                    print(f"🌙 Moon Dev: Body filter failed - bodies not progressively smaller (b1:{body1:.2f}, b2:{body2:.2f}, b3:{body3:.2f}, b4:{body4:.2f})! 🚫")
                    return
                print("🌙 Moon Dev: Body filter passed - decreasing momentum! 💪✅")
            else:
                body_filter = True

            # Trend filter (pre-streak close above SMA)
            if len(self.data) >= 5:
                pre_streak_close = self.data.Close[-5]
                pre_streak_sma = self.sma[-5]
                trend_filter = pre_streak_close > pre_streak_sma
                if not trend_filter:
                    print(f"🌙 Moon Dev: Trend filter failed - pre-streak close {pre_streak_close} <= SMA {pre_streak_sma}! 🚫")
                    return
                print(f"🌙 Moon Dev: Trend filter passed - bullish bias pre-streak! 📈✅")
            else:
                trend_filter = True

            if vol_filter and body_filter and trend_filter:
                # Calculate SL and TP
                min_low = min(self.data.Low[-4:])
                sl_price = min_low - 0.5 * self.atr[-1]
                approx_entry = self.data.Close[-1]
                risk_per_unit = approx_entry - sl_price
                if risk_per_unit <= 0:
                    print("🌙 Moon Dev: Invalid risk per unit, skipping entry. ⚠️")
                    return

                risk_amount = self.equity * self.risk_percent
                size = int(round(risk_amount / risk_per_unit))
                if size <= 0:
                    print("🌙 Moon Dev: Calculated size <=0, skipping entry. ⚠️")
                    return

                tp_price = approx_entry + 2 * risk_per_unit

                self.buy(size=size, sl=sl_price, tp=tp_price)
                self.fourth_close = self.data.Close[-1]
                self.entry_bar = len(self.data)
                self.post_down_streak = 0
                print(f"🌙 Moon Dev: Entering LONG CascadeReversal! Entry ~{approx_entry}, SL {sl_price:.2f}, TP {tp_price:.2f}, Size {size}, Risk {risk_amount:.2f} USD 🚀💰")

bt = Backtest(data, CascadeReversal, cash=1000000, commission=0.001)
stats = bt.run()
print(stats)