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
        
        # 🌙 Moon Dev: Added trail ATR multiplier for dynamic trailing stops
        self.trail_atr_mult = 3.0
        # 🌙 Moon Dev: Added RR for take profit
        self.rr_ratio = 2.0

    def next(self):
        if np.isnan(self.adx[-1]) or self.adx[-1] < 20:
            return
        # 🌙 Moon Dev: Relaxed ADX threshold to 20 for more trading opportunities in moderate trends

        risk_per_trade = 0.02
        # 🌙 Moon Dev: Increased risk per trade to 2% for higher returns while maintaining management
        current_equity = self._broker.getvalue()
        # 🌙 Moon Dev: Use current equity instead of initial cash for dynamic position sizing as equity grows
        risk_amount = risk_per_trade * current_equity
        entry_price = self.data.Close[-1]
        atr_buffer = self.atr[-1]
        vol_threshold = 1.2 * self.volume_ma[-1]
        # 🌙 Moon Dev: Increased volume filter threshold to 1.2x MA for higher quality entries

        if not self.position:
            # Long entry
            if (self.data.Close[-1] > self.lips[-1] and
                self.lips[-1] > self.teeth[-1] > self.jaw[-1] and
                self.ao[-1] > 0 and self.ao[-1] > self.ao[-2] and
                self.data.Volume[-1] > vol_threshold and
                self.data.Close[-1] > self.ffill_up[-1] and
                self.data.Close[-2] <= self.ffill_up[-2]):
                
                sl = self.ffill_down[-1] - atr_buffer
                if sl < entry_price:
                    risk_dist = entry_price - sl
                    tp = entry_price + self.rr_ratio * risk_dist
                    # 🌙 Moon Dev: Added take profit at 2:1 RR to capture profits systematically
                    size = risk_amount / risk_dist
                    # 🌙 Moon Dev: Removed int(round()) to allow fractional sizes for precision
                    if size > 0:
                        self.buy(size=size, sl=sl, tp=tp)
                        self.current_sl = sl
                        print(f"🌙 Moon Dev: Long entry at {entry_price:.2f}, Size: {size:.4f}, SL: {sl:.2f}, TP: {tp:.2f} 🚀")

            # Short entry
            elif (self.data.Close[-1] < self.lips[-1] and
                  self.lips[-1] < self.teeth[-1] < self.jaw[-1] and
                  self.ao[-1] < 0 and self.ao[-1] < self.ao[-2] and
                  self.data.Volume[-1] > vol_threshold and
                  self.data.Close[-1] < self.ffill_down[-1] and
                  self.data.Close[-2] >= self.ffill_down[-2]):
                
                sl = self.ffill_up[-1] + atr_buffer
                if sl > entry_price:
                    risk_dist = sl - entry_price
                    tp = entry_price - self.rr_ratio * risk_dist
                    # 🌙 Moon Dev: Added take profit at 2:1 RR for shorts
                    size = risk_amount / risk_dist
                    if size > 0:
                        self.sell(size=size, sl=sl, tp=tp)
                        self.current_sl = sl
                        print(f"🌙 Moon Dev: Short entry at {entry_price:.2f}, Size: {size:.4f}, SL: {sl:.2f}, TP: {tp:.2f} 📉")

        if self.position:
            if self.position.is_long:
                # Exit conditions first
                if self.data.Close[-1] < self.teeth[-1]:
                    self.position.close()
                    self.current_sl = None
                    print(f"🌙 Moon Dev: Long exit - below Teeth 📉")
                    return
                elif self.data.Close[-1] < self.jaw[-1]:
                    self.position.close()
                    self.current_sl = None
                    print(f"🌙 Moon Dev: Long hard exit - below Jaw 😤")
                    return
                
                # Trail stop for long - improved to dynamic ATR-based trailing every bar
                current_sl = self.current_sl
                potential_sl = self.data.Close[-1] - self.trail_atr_mult * self.atr[-1]
                # 🌙 Moon Dev: Switched from fractal-only trailing to close - 3*ATR for more responsive profit locking
                if potential_sl > current_sl:
                    trade_size = self.position.size
                    new_entry_approx = self.data.Close[-1]
                    new_risk_dist = new_entry_approx - potential_sl
                    new_tp = new_entry_approx + self.rr_ratio * new_risk_dist
                    # 🌙 Moon Dev: Update TP on trail to maintain RR based on new effective entry/SL
                    self.position.close()
                    self.buy(size=trade_size, sl=potential_sl, tp=new_tp)
                    self.current_sl = potential_sl
                    print(f"🌙 Moon Dev: Trailing SL long to {potential_sl:.2f}, new TP: {new_tp:.2f} ✨")
            
            elif self.position.is_short:
                # Exit conditions first
                if self.data.Close[-1] > self.teeth[-1]:
                    self.position.close()
                    self.current_sl = None
                    print(f"🌙 Moon Dev: Short exit - above Teeth 📈")
                    return
                elif self.data.Close[-1] > self.jaw[-1]:
                    self.position.close()
                    self.current_sl = None
                    print(f"🌙 Moon Dev: Short hard exit - above Jaw 😤")
                    return
                
                # Trail stop for short - improved to dynamic ATR-based trailing every bar
                current_sl = self.current_sl
                potential_sl = self.data.Close[-1] + self.trail_atr_mult * self.atr[-1]
                if potential_sl < current_sl:
                    trade_size = abs(self.position.size)
                    new_entry_approx = self.data.Close[-1]
                    new_risk_dist = potential_sl - new_entry_approx
                    new_tp = new_entry_approx - self.rr_ratio * new_risk_dist
                    self.position.close()
                    self.sell(size=trade_size, sl=potential_sl, tp=new_tp)
                    self.current_sl = potential_sl
                    print(f"🌙 Moon Dev: Trailing SL short to {potential_sl:.2f}, new TP: {new_tp:.2f} ✨")

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