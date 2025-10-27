import numpy as np
import pandas as pd
from backtesting import Backtest, Strategy
import talib

def compute_up_fractals(high):
    up = np.full(len(high), np.nan)
    n = len(high)
    for i in range(2, n - 2):
        h2 = high[i]
        if (h2 > high[i - 1] and h2 > high[i - 2] and
            h2 > high[i + 1] and h2 > high[i + 2]):
            up[i] = h2
    return up

def compute_down_fractals(low):
    down = np.full(len(low), np.nan)
    n = len(low)
    for i in range(2, n - 2):
        l2 = low[i]
        if (l2 < low[i - 1] and l2 < low[i - 2] and
            l2 < low[i + 1] and l2 < low[i + 2]):
            down[i] = l2
    return down

def compute_ffill_fractal(fractal):
    filled = np.full(len(fractal), np.nan)
    prev = np.nan
    for i in range(len(fractal)):
        if not np.isnan(fractal[i]):
            prev = fractal[i]
        filled[i] = prev
    return filled

def compute_shifted_ema(s, period, shift):
    ema = talib.EMA(s, timeperiod=period)
    shifted = np.full_like(ema, np.nan)
    if len(ema) > shift:
        shifted[shift:] = ema[:len(ema) - shift]
    return shifted

class FractalCascade(Strategy):
    def init(self):
        self.current_sl = None
        self.current_tp = None
        self.initial_cash = self._broker._cash
        median = (self.data.High + self.data.Low) / 2
        
        jaw_period = 13
        self.jaw = self.I(compute_shifted_ema, median, jaw_period, 8)
        
        teeth_period = 8
        self.teeth = self.I(compute_shifted_ema, median, teeth_period, 5)
        
        lips_period = 5
        self.lips = self.I(compute_shifted_ema, median, lips_period, 3)
        
        ao_fast = 5
        ao_slow = 34
        smma_fast = self.I(talib.EMA, median, timeperiod=ao_fast)
        smma_slow = self.I(talib.EMA, median, timeperiod=ao_slow)
        self.ao = smma_fast - smma_slow
        
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        self.volume_ma = self.I(talib.SMA, self.data.Volume, timeperiod=20)
        
        self.up_fractal = self.I(compute_up_fractals, self.data.High)
        self.down_fractal = self.I(compute_down_fractals, self.data.Low)
        self.ffill_up = self.I(compute_ffill_fractal, self.up_fractal)
        self.ffill_down = self.I(compute_ffill_fractal, self.down_fractal)

    def next(self):
        if np.isnan(self.adx[-1]) or self.adx[-1] < 20:  # 🌙 Moon Dev: Lowered ADX threshold to 20 for more trading opportunities in moderate trends
            return

        risk_per_trade = 0.02  # 🌙 Moon Dev: Increased risk per trade to 2% to amplify returns while keeping risk managed
        risk_amount = risk_per_trade * self.initial_cash
        entry_price = self.data.Close[-1]
        atr_buffer = self.atr[-1]

        if not self.position:
            # Long entry
            if (self.data.Close[-1] > self.lips[-1] and
                self.lips[-1] > self.teeth[-1] > self.jaw[-1] and
                self.ao[-1] > 0 and self.ao[-1] > self.ao[-2] and
                self.data.Volume[-1] > 1.2 * self.volume_ma[-1] and  # 🌙 Moon Dev: Tightened volume filter to 1.2x MA for higher quality breakouts
                self.data.Close[-1] > self.ffill_up[-1] and
                self.data.Close[-2] <= self.ffill_up[-2]):
                
                sl = self.ffill_down[-1] - atr_buffer
                if sl < entry_price:
                    risk_dist = entry_price - sl
                    tp = entry_price + 2.5 * risk_dist  # 🌙 Moon Dev: Added 2.5:1 RR take profit to capture larger wins
                    size = risk_amount / risk_dist
                    size = int(round(size))
                    if size > 0:
                        self.buy(size=size, sl=sl, tp=tp)
                        self.current_sl = sl
                        self.current_tp = tp
                        print(f"🌙 Moon Dev: Long entry at {entry_price:.2f}, Size: {size}, SL: {sl:.2f}, TP: {tp:.2f} 🚀")

            # Short entry
            elif (self.data.Close[-1] < self.lips[-1] and
                  self.lips[-1] < self.teeth[-1] < self.jaw[-1] and
                  self.ao[-1] < 0 and self.ao[-1] < self.ao[-2] and
                  self.data.Volume[-1] > 1.2 * self.volume_ma[-1] and  # 🌙 Moon Dev: Tightened volume filter to 1.2x MA for higher quality breakouts
                  self.data.Close[-1] < self.ffill_down[-1] and
                  self.data.Close[-2] >= self.ffill_down[-2]):
                
                sl = self.ffill_up[-1] + atr_buffer
                if sl > entry_price:
                    risk_dist = sl - entry_price
                    tp = entry_price - 2.5 * risk_dist  # 🌙 Moon Dev: Added 2.5:1 RR take profit to capture larger wins
                    size = risk_amount / risk_dist
                    size = int(round(size))
                    if size > 0:
                        self.sell(size=size, sl=sl, tp=tp)
                        self.current_sl = sl
                        self.current_tp = tp
                        print(f"🌙 Moon Dev: Short entry at {entry_price:.2f}, Size: {size}, SL: {sl:.2f}, TP: {tp:.2f} 📉")

        if self.position:
            if self.position.is_long:
                # Exit conditions first - removed teeth exit to let winners run longer 🌙 Moon Dev: Rely on TP, trailing, and jaw for better return potential
                if self.data.Close[-1] < self.jaw[-1]:
                    self.position.close()
                    self.current_sl = None
                    self.current_tp = None
                    print(f"🌙 Moon Dev: Long hard exit - below Jaw 😤")
                    return
                
                # Fractal trail for long
                current_sl = self.current_sl
                if not np.isnan(self.down_fractal[-1]):
                    new_sl = self.down_fractal[-1] - atr_buffer
                    if new_sl > current_sl:
                        trade_size = self.position.size
                        self.position.close()
                        self.buy(size=trade_size, sl=new_sl, tp=self.current_tp)
                        self.current_sl = new_sl
                        print(f"🌙 Moon Dev: Fractal trailing SL long to {new_sl:.2f} ✨")
                
                # Dynamic ATR trail using recent lows for more frequent adjustments 🌙 Moon Dev: Added min low over last 4 bars - 1.5 ATR for tighter profit locking
                if len(self.data.Low) >= 5:
                    recent_low = np.min(self.data.Low[-5:-1])
                    new_trail_sl = recent_low - 1.5 * self.atr[-1]
                    if new_trail_sl > self.current_sl:
                        trade_size = self.position.size
                        self.position.close()
                        self.buy(size=trade_size, sl=new_trail_sl, tp=self.current_tp)
                        self.current_sl = new_trail_sl
                        print(f"🌙 Moon Dev: Dynamic trail SL long to {new_trail_sl:.2f} ✨")
            
            elif self.position.is_short:
                # Exit conditions first - removed teeth exit to let winners run longer 🌙 Moon Dev: Rely on TP, trailing, and jaw for better return potential
                if self.data.Close[-1] > self.jaw[-1]:
                    self.position.close()
                    self.current_sl = None
                    self.current_tp = None
                    print(f"🌙 Moon Dev: Short hard exit - above Jaw 😤")
                    return
                
                # Fractal trail for short
                current_sl = self.current_sl
                if not np.isnan(self.up_fractal[-1]):
                    new_sl = self.up_fractal[-1] + atr_buffer
                    if new_sl < current_sl:
                        trade_size = abs(self.position.size)
                        self.position.close()
                        self.sell(size=trade_size, sl=new_sl, tp=self.current_tp)
                        self.current_sl = new_sl
                        print(f"🌙 Moon Dev: Fractal trailing SL short to {new_sl:.2f} ✨")
                
                # Dynamic ATR trail using recent highs for more frequent adjustments 🌙 Moon Dev: Added max high over last 4 bars + 1.5 ATR for tighter profit locking
                if len(self.data.High) >= 5:
                    recent_high = np.max(self.data.High[-5:-1])
                    new_trail_sl = recent_high + 1.5 * self.atr[-1]
                    if new_trail_sl < self.current_sl:
                        trade_size = abs(self.position.size)
                        self.position.close()
                        self.sell(size=trade_size, sl=new_trail_sl, tp=self.current_tp)
                        self.current_sl = new_trail_sl
                        print(f"🌙 Moon Dev: Dynamic trail SL short to {new_trail_sl:.2f} ✨")

if __name__ == '__main__':
    data_path = '/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv'
    data = pd.read_csv(data_path)
    data.columns = data.columns.str.strip().str.lower()
    data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
    data = data.rename(columns={
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume'
    })
    data['datetime'] = pd.to_datetime(data['datetime'])
    data = data.set_index(data['datetime'])
    bt = Backtest(data, FractalCascade, cash=1000000, commission=0.001)
    stats = bt.run()
    print(stats)