import pandas as pd
import numpy as np
import talib
from backtesting import Backtest, Strategy

# Load and clean data
data_path = '/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv'
data = pd.read_csv(data_path, parse_dates=['datetime'], index_col='datetime')
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data = data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
})

class DivergentVolatility(Strategy):
    def init(self):
        self.SMA50 = self.I(talib.SMA, self.data.Close, timeperiod=50)
        self.SMA200 = self.I(talib.SMA, self.data.Close, timeperiod=200)
        self.vol_avg = self.I(talib.SMA, self.data.Volume, timeperiod=20)
        self.RSI = self.I(talib.RSI, self.data.Close, timeperiod=14)
        self.bb_upper, self.bb_middle, self.bb_lower = self.I(
            talib.BBANDS, self.data.Close, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0
        )
        self.bb_width = (self.bb_upper - self.bb_lower) / self.bb_middle
        self.avg_bb_width = self.I(talib.SMA, self.bb_width, timeperiod=20)
        self.ATR = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=14)

        # State variables
        self.death_cross_bar = -1
        self.state = None
        self.lowest_since_cross = np.inf
        self.rsi_at_lowest = -1
        self.divergence_confirmed = False
        self.div_bar = -1
        self.entry_bar = -1
        self.stop_price = 0
        self.entry_price = 0

    def next(self):
        i = len(self.data) - 1
        if i < 200:
            return
        close = self.data.Close[-1]
        high = self.data.High[-1]
        low = self.data.Low[-1]
        volume = self.data.Volume[-1]

        # Check for death cross if not detected
        if self.death_cross_bar == -1 and i >= 1:
            prev_sma50 = self.SMA50[-2]
            curr_sma50 = self.SMA50[-1]
            prev_sma200 = self.SMA200[-2]
            curr_sma200 = self.SMA200[-1]
            if (not np.isnan(prev_sma50) and not np.isnan(prev_sma200) and
                not np.isnan(curr_sma50) and not np.isnan(curr_sma200) and
                prev_sma50 > prev_sma200 and curr_sma50 <= curr_sma200 and
                close < curr_sma200 and volume < 0.8 * self.vol_avg[-1]):
                self.death_cross_bar = i
                self.state = 'post_cross'
                self.lowest_since_cross = low
                self.rsi_at_lowest = self.RSI[-1]
                print(f"🌙 Death Cross detected at bar {i} on low volume! Waiting for divergence... ✨")

        # Post-cross logic: check for divergence
        if self.state == 'post_cross' and self.death_cross_bar != -1:
            bars_since_cross = i - self.death_cross_bar
            if bars_since_cross > 10:
                print(f"🌙 No divergence within 10 bars, resetting... 😔")
                self.reset_state()
                return

            # Update lowest low
            if low < self.lowest_since_cross:
                if self.RSI[-1] > self.rsi_at_lowest:
                    self.divergence_confirmed = True
                    self.div_bar = i
                    print(f"🚀 Bullish Divergence confirmed at bar {i}! Price: {low}, RSI: {self.RSI[-1]:.2f} > prev {self.rsi_at_lowest:.2f} 🌙")
                self.lowest_since_cross = low
                self.rsi_at_lowest = self.RSI[-1]

            # If divergence confirmed and within 5-10 bars, move to waiting breakout
            if self.divergence_confirmed and 5 <= bars_since_cross <= 10:
                self.state = 'waiting_breakout'
                print(f"✨ Divergence confirmed, now waiting for volatility breakout! 🌙")

        # Waiting for breakout after divergence
        elif self.state == 'waiting_breakout' and self.divergence_confirmed:
            # Consolidation high: max high of last 10 bars
            consol_high = max(self.data.High[-10:]) if i >= 9 else max(self.data.High[self.death_cross_bar:i+1])
            # BB squeeze breakout
            bb_w = (self.bb_upper[-1] - self.bb_lower[-1]) / self.bb_middle[-1]
            squeeze = bb_w < self.avg_bb_width[-1]
            breakout1 = close > consol_high
            breakout2 = squeeze and close > self.bb_upper[-1]
            if (breakout1 or breakout2) and close < self.SMA200[-1] and not self.position:
                atr_val = self.ATR[-1]
                swing_low = self.lowest_since_cross
                self.stop_price = swing_low - 1.5 * atr_val
                risk_per_unit = close - self.stop_price
                if risk_per_unit > 0:
                    equity = self._broker.getcash()  # Fixed: Use self._broker.getcash() for equity approximation
                    risk_amount = 0.01 * equity
                    size = risk_amount / risk_per_unit
                    size = int(round(size))
                    if size > 0:
                        self.buy(size=size)
                        self.entry_price = close
                        self.entry_bar = i
                        self.state = 'in_position'
                        print(f"🌙 Long Entry at {close:.2f}, size {size}, stop {self.stop_price:.2f}, risk 1% 🚀")

        # Position management
        if self.position and self.position.is_long:
            bars_in_trade = i - self.entry_bar if self.entry_bar != -1 else 0

            # Primary exit: close below middle BB
            if close < self.bb_middle[-1]:
                self.position.close()
                print(f"✨ Exit on close below middle BB at {close:.2f} 🌙")
                self.reset_state()
                return

            # Exit on upper BB touch with overbought RSI
            if close >= self.bb_upper[-1] and self.RSI[-1] > 70:
                self.position.close()
                print(f"🌙 Exit on upper BB overbought RSI at {close:.2f} 🚀")
                self.reset_state()
                return

            # Time-based exit
            if bars_in_trade > 20:
                self.position.close()
                print(f"⏰ Time-based exit after 20 bars at {close:.2f} 🌙")
                self.reset_state()
                return

            # Emergency exit
            if close < self.SMA200[-1] and volume > 1.2 * self.vol_avg[-1]:
                self.position.close()
                print(f"🚨 Emergency exit on renewed bearish volume at {close:.2f}! 💥")
                self.reset_state()
                return

            # Stop loss check
            if close < self.stop_price:
                self.position.close()
                print(f"💥 Stop loss hit at {close:.2f} (stop: {self.stop_price:.2f}) 🌙")
                self.reset_state()
                return

            # Trailing stop after 2:1 RR
            if self.entry_price > 0 and self.stop_price > 0:
                unrealized_risk = self.entry_price - self.stop_price
                unrealized_profit = close - self.entry_price
                if unrealized_profit > 2 * unrealized_risk:
                    new_trail = self.bb_middle[-1]
                    if new_trail > self.stop_price:
                        self.stop_price = new_trail
                        print(f"🔄 Trailing stop updated to middle BB: {self.stop_price:.2f} ✨")

    def reset_state(self):
        self.death_cross_bar = -1
        self.state = None
        self.divergence_confirmed = False
        self.div_bar = -1
        self.lowest_since_cross = np.inf
        self.rsi_at_lowest = -1
        self.entry_bar = -1
        self.stop_price = 0
        self.entry_price = 0

# Run backtest
bt = Backtest(data, DivergentVolatility, cash=1000000, commission=0.001, exclusive_orders=True)
stats = bt.run()
print(stats)