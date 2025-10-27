import pandas as pd
import numpy as np
import talib
from backtesting import Backtest, Strategy

# Data loading and cleaning
path = '/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv'
data = pd.read_csv(path)
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data = data.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'})
data = data.set_index(pd.to_datetime(data['datetime']))

class ClimaxReversal(Strategy):
    rsi_period = 14
    stoch_k = 14
    stoch_d = 3
    stoch_slow = 3
    sma_period = 50
    atr_period = 14
    vol_ma_period = 20
    gap_threshold = 0.005  # 0.5%
    consec_bars = 5
    risk_per_trade = 0.01
    atr_multiplier = 1.5
    max_hold_bars = 5
    vol_spike_mult = 1.5

    def init(self):
        self.sma = self.I(talib.SMA, self.data.Close, timeperiod=self.sma_period)
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=self.rsi_period)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=self.atr_period)
        self.stoch_k, self.stoch_d = self.I(talib.STOCH, self.data.High, self.data.Low, self.data.Close,
                                            fastk_period=self.stoch_k, slowk_period=self.stoch_d, slowd_period=self.stoch_slow)
        self.vol_ma = self.I(talib.SMA, self.data.Volume, timeperiod=self.vol_ma_period)
        self.entry_bar = None
        print("🌙 Moon Dev: Initialized ClimaxReversal Strategy ✨")

    def get_consec_down(self):
        if len(self.data) < 4:
            return 0
        current_len = len(self.data)
        end_idx = current_len - 3
        count = 1
        check_idx = end_idx
        prev_idx = end_idx - 1
        while prev_idx >= 0 and self.data.Close[check_idx] < self.data.Close[prev_idx]:
            count += 1
            check_idx = prev_idx
            prev_idx -= 1
        return count

    def get_consec_up(self):
        if len(self.data) < 4:
            return 0
        current_len = len(self.data)
        end_idx = current_len - 3
        count = 1
        check_idx = end_idx
        prev_idx = end_idx - 1
        while prev_idx >= 0 and self.data.Close[check_idx] > self.data.Close[prev_idx]:
            count += 1
            check_idx = prev_idx
            prev_idx -= 1
        return count

    def next(self):
        max_period = max(self.sma_period, self.atr_period, self.vol_ma_period, self.stoch_k)
        if len(self.data) < max_period + 3:
            return

        i = len(self.data) - 1

        # Time-based exit
        if self.position and self.entry_bar is not None and (i - self.entry_bar) > self.max_hold_bars:
            self.position.close()
            print(f"🌙 Moon Dev: Time-based exit after {self.max_hold_bars} bars ⏰")
            self.entry_bar = None
            return

        # Check for entries only if no position
        if self.position:
            return

        if len(self.data) < 3:
            return

        # Gap bar is -2, prev to gap is -3, current is -1
        prev_to_gap_close = self.data.Close[-3]
        gap_open = self.data.Open[-2]
        gap_close = self.data.Close[-2]
        gap_high = self.data.High[-2]
        gap_low = self.data.Low[-2]
        gap_volume = self.data.Volume[-2]
        curr_open = self.data.Open[-1]
        curr_close = self.data.Close[-1]
        curr_volume = self.data.Volume[-1]

        gap_size_pct = abs(gap_open - prev_to_gap_close) / prev_to_gap_close
        is_gap_down = gap_open < prev_to_gap_close
        is_gap_up = gap_open > prev_to_gap_close

        vol_high_gap = gap_volume > self.vol_ma[-2] * self.vol_spike_mult
        vol_low_confirm = curr_volume < self.vol_ma[-1]

        entry_price = curr_close

        # Debug print for potential gaps
        if gap_size_pct > 0.0005:  # 0.05% threshold for debug
            stoch_cross_up = self.stoch_k[-1] > self.stoch_d[-1] and self.stoch_k[-2] <= self.stoch_d[-2]
            stoch_cross_down = self.stoch_k[-1] < self.stoch_d[-1] and self.stoch_k[-2] >= self.stoch_d[-2]
            print(f"🌙 Moon Dev Debug: Bar {i}, Gap%: {gap_size_pct*100:.3f}, Down?: {is_gap_down}, Consec down: {self.get_consec_down()}, up: {self.get_consec_up()}, "
                  f"Gap close vs SMA: {gap_close} vs {self.sma[-2]:.2f}, RSI[-2]: {self.rsi[-2]:.1f}, "
                  f"Confirm close > gap open: {curr_close > gap_open}, Bullish candle: {curr_close > curr_open}, "
                  f"Vol high gap: {vol_high_gap}, Vol low confirm: {vol_low_confirm}, Stoch cross up: {stoch_cross_up}, down: {stoch_cross_down} ✨")

        # Long Entry: Bullish Reversal in Downtrend
        if (is_gap_down and gap_size_pct > self.gap_threshold and
            self.get_consec_down() >= self.consec_bars and
            gap_close < self.sma[-2] and  # Downtrend
            self.rsi[-2] < 30 and  # Oversold at gap
            curr_close > gap_open and  # Confirmation close above gap open
            curr_close > curr_open and  # Bullish candle
            vol_high_gap and vol_low_confirm and
            self.stoch_k[-1] > self.stoch_d[-1] and self.stoch_k[-2] <= self.stoch_d[-2]):  # Stoch crossover up

            sl = gap_low - self.atr[-1] * self.atr_multiplier
            risk_dist = (entry_price - sl) / entry_price
            if risk_dist > 0:
                size = self.risk_per_trade / risk_dist
                tp = prev_to_gap_close  # Gap fill
                self.buy(size=size, sl=sl, tp=tp)
                self.entry_bar = i
                print(f"🌙 Moon Dev: LONG Entry at {entry_price:.2f}, SL: {sl:.2f}, TP: {tp:.2f}, Size: {size:.4f} 🚀💹")

        # Short Entry: Bearish Reversal in Uptrend
        elif (is_gap_up and gap_size_pct > self.gap_threshold and
              self.get_consec_up() >= self.consec_bars and
              gap_close > self.sma[-2] and  # Uptrend
              self.rsi[-2] > 70 and  # Overbought at gap
              curr_close < gap_open and  # Confirmation close below gap open
              curr_close < curr_open and  # Bearish candle
              vol_high_gap and vol_low_confirm and
              self.stoch_k[-1] < self.stoch_d[-1] and self.stoch_k[-2] >= self.stoch_d[-2]):  # Stoch crossover down

            sl = gap_high + self.atr[-1] * self.atr_multiplier
            risk_dist = (sl - entry_price) / entry_price
            if risk_dist > 0:
                size = self.risk_per_trade / risk_dist
                tp = prev_to_gap_close  # Gap fill
                self.sell(size=size, sl=sl, tp=tp)
                self.entry_bar = i
                print(f"🌙 Moon Dev: SHORT Entry at {entry_price:.2f}, SL: {sl:.2f}, TP: {tp:.2f}, Size: {size:.4f} 📉🔻")

bt = Backtest(data, ClimaxReversal, cash=1000000, commission=0.002, exclusive_orders=True)
stats = bt.run()
print(stats)
print(stats._strategy)