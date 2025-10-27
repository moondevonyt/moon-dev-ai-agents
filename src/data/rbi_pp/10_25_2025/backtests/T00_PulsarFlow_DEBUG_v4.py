import pandas as pd
from backtesting import Backtest, Strategy
import talib
import numpy as np

# Load and clean data
data = pd.read_csv('/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv')
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data = data.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'})
data = data.set_index(pd.to_datetime(data['datetime'])).drop('datetime', axis=1)

class PulsarFlow(Strategy):
    mfi_period = 14
    ema_period = 50
    atr_period = 14
    adx_period = 14
    atr20_period = 20
    overbought = 80
    oversold = 20
    risk_per_trade = 0.01
    rr_ratio = 2
    sl_percent = 0.02
    trail_multiplier = 1.5
    lookback = 20

    def init(self):
        print("🌙 Moon Dev: Initializing PulsarFlow Strategy ✨")
        self.bar_index = 0
        self.mfi = self.I(talib.MFI, self.data.High, self.data.Low, self.data.Close, self.data.Volume, timeperiod=self.mfi_period)
        self.ema = self.I(talib.EMA, self.data.Close, timeperiod=self.ema_period)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=self.atr_period)
        self.atr20 = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=self.atr20_period)
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=self.adx_period)
        self.avg_volume = self.I(talib.SMA, self.data.Volume, timeperiod=20)
        self.entry_price = None
        self.stop_loss = None
        self.take_profit = None

    def get_bullish_div_info(self, current_i):
        N = current_i + 1
        if N < self.lookback * 2 + 10:
            return False, None
        start_recent = max(0, N - self.lookback)
        recent_lows = self.data.Low[start_recent : N]
        if len(recent_lows) == 0:
            return False, None
        idx_rel = np.argmin(recent_lows)
        recent_low_idx = start_recent + idx_rel
        recent_low_price = self.data.Low[recent_low_idx]
        recent_mfi = self.mfi[recent_low_idx]
        
        start_prev = max(0, N - self.lookback * 2)
        end_prev = N - self.lookback
        prev_lows = self.data.Low[start_prev : end_prev]
        if len(prev_lows) < self.lookback // 2:
            return False, None
        idx_rel_prev = np.argmin(prev_lows)
        prev_low_idx = start_prev + idx_rel_prev
        prev_low_price = self.data.Low[prev_low_idx]
        prev_mfi = self.mfi[prev_low_idx]
        
        div = (recent_low_price < prev_low_price) and (recent_mfi > prev_mfi) and not np.isnan(recent_mfi) and not np.isnan(prev_mfi)
        return div, recent_low_price

    def get_bearish_div_info(self, current_i):
        N = current_i + 1
        if N < self.lookback * 2 + 10:
            return False, None
        start_recent = max(0, N - self.lookback)
        recent_highs = self.data.High[start_recent : N]
        if len(recent_highs) == 0:
            return False, None
        idx_rel = np.argmax(recent_highs)
        recent_high_idx = start_recent + idx_rel
        recent_high_price = self.data.High[recent_high_idx]
        recent_mfi = self.mfi[recent_high_idx]
        
        start_prev = max(0, N - self.lookback * 2)
        end_prev = N - self.lookback
        prev_highs = self.data.High[start_prev : end_prev]
        if len(prev_highs) < self.lookback // 2:
            return False, None
        idx_rel_prev = np.argmax(prev_highs)
        prev_high_idx = start_prev + idx_rel_prev
        prev_high_price = self.data.High[prev_high_idx]
        prev_mfi = self.mfi[prev_high_idx]
        
        div = (recent_high_price > prev_high_price) and (recent_mfi < prev_mfi) and not np.isnan(recent_mfi) and not np.isnan(prev_mfi)
        return div, recent_high_price

    def next(self):
        current_i = self.bar_index
        self.bar_index += 1
        if current_i < 60:
            return
        
        close = self.data.Close[current_i]
        high = self.data.High[current_i]
        low = self.data.Low[current_i]
        volume = self.data.Volume[current_i]
        print(f"🌙 Moon Dev: Bar update - Close: {close:.2f}, MFI: {self.mfi[current_i]:.2f}, ADX: {self.adx[current_i]:.2f} 📊")
        
        # Exit logic first
        if self.position:
            if self.position.size > 0:
                # Hard SL
                if low <= self.stop_loss:
                    self.position.close()
                    print(f"🌙 Moon Dev: STOP LOSS hit for LONG at {low:.2f} 💥")
                    self.entry_price = None
                    self.stop_loss = None
                    self.take_profit = None
                    return
                # TP
                if high >= self.take_profit:
                    self.position.close()
                    print(f"🌙 Moon Dev: TAKE PROFIT hit for LONG at {high:.2f} 🎉")
                    self.entry_price = None
                    self.stop_loss = None
                    self.take_profit = None
                    return
                # MFI exit
                if self.mfi[current_i] >= self.overbought:
                    self.position.close()
                    print(f"🌙 Moon Dev: MFI OVERBOUGHT exit for LONG at {close:.2f} 🌕")
                    self.entry_price = None
                    self.stop_loss = None
                    self.take_profit = None
                    return
                # Trailing stop
                if self.position.pl_pct > 0.01:
                    new_trail = close - self.trail_multiplier * self.atr20[current_i]
                    self.stop_loss = max(self.stop_loss, new_trail)
                    print(f"🌙 Moon Dev: Trailing SL updated for LONG to {self.stop_loss:.2f} 🔄")
            else:  # short
                # Hard SL
                if high >= self.stop_loss:
                    self.position.close()
                    print(f"🌙 Moon Dev: STOP LOSS hit for SHORT at {high:.2f} 💥")
                    self.entry_price = None
                    self.stop_loss = None
                    self.take_profit = None
                    return
                # TP
                if low <= self.take_profit:
                    self.position.close()
                    print(f"🌙 Moon Dev: TAKE PROFIT hit for SHORT at {low:.2f} 🎉")
                    self.entry_price = None
                    self.stop_loss = None
                    self.take_profit = None
                    return
                # MFI exit
                if self.mfi[current_i] <= self.oversold:
                    self.position.close()
                    print(f"🌙 Moon Dev: MFI OVERSOLD exit for SHORT at {close:.2f} 🌑")
                    self.entry_price = None
                    self.stop_loss = None
                    self.take_profit = None
                    return
                # Trailing stop
                if self.position.pl_pct > 0.01:
                    new_trail = close + self.trail_multiplier * self.atr20[current_i]
                    self.stop_loss = min(self.stop_loss, new_trail)
                    print(f"🌙 Moon Dev: Trailing SL updated for SHORT to {self.stop_loss:.2f} 🔄")
        
        # Entry logic if no position
        if not self.position:
            # Filters
            if volume < 0.5 * self.avg_volume[current_i]:
                print(f"🌙 Moon Dev: Volume too low, skipping entry 📉")
                return
            if self.adx[current_i] < 20:
                print(f"🌙 Moon Dev: ADX too low ({self.adx[current_i]:.2f}), choppy market, skipping 🚫")
                return
            
            # Long entry
            if close > self.ema[current_i] and self.mfi[current_i] <= self.oversold:
                print(f"🌙 Moon Dev: Potential LONG: MFI {self.mfi[current_i]:.2f} <= {self.oversold}, Close {close:.2f} > EMA {self.ema[current_i]:.2f} 🔍")
                div, swing_low = self.get_bullish_div_info(current_i)
                if div and swing_low is not None and close > swing_low:
                    entry_price = close
                    sl = max(entry_price * (1 - self.sl_percent), swing_low)
                    risk = entry_price - sl
                    if risk > 0:
                        risk_amount = self.equity * self.risk_per_trade
                        size = int(round(risk_amount / risk))
                        if size > 0:
                            self.buy(size=size)
                            self.entry_price = entry_price
                            self.stop_loss = sl
                            self.take_profit = entry_price + self.rr_ratio * risk
                            print(f"🌙 Moon Dev: LONG entry at {entry_price:.2f}, size {size}, SL {sl:.2f}, TP {self.take_profit:.2f} 🚀")
                            return
                else:
                    print(f"🌙 Moon Dev: No bullish divergence for LONG entry 🚫")
            
            # Short entry
            if close < self.ema[current_i] and self.mfi[current_i] >= self.overbought:
                print(f"🌙 Moon Dev: Potential SHORT: MFI {self.mfi[current_i]:.2f} >= {self.overbought}, Close {close:.2f} < EMA {self.ema[current_i]:.2f} 🔍")
                div, swing_high = self.get_bearish_div_info(current_i)
                if div and swing_high is not None and close < swing_high:
                    entry_price = close
                    sl = min(entry_price * (1 + self.sl_percent), swing_high)
                    risk = sl - entry_price
                    if risk > 0:
                        risk_amount = self.equity * self.risk_per_trade
                        size = int(round(risk_amount / risk))
                        if size > 0:
                            self.sell(size=size)
                            self.entry_price = entry_price
                            self.stop_loss = sl
                            self.take_profit = entry_price - self.rr_ratio * risk
                            print(f"🌙 Moon Dev: SHORT entry at {entry_price:.2f}, size {size}, SL {sl:.2f}, TP {self.take_profit:.2f} 📉")
                            return
                else:
                    print(f"🌙 Moon Dev: No bearish divergence for SHORT entry 🚫")

bt = Backtest(data, PulsarFlow, cash=1000000, commission=0.001, exclusive_orders=True)
stats = bt.run()
print(stats)