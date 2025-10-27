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
    # 🌙 Moon Dev Optimization: Added tp for fixed reward:risk ratio, RSI filter for momentum confirmation,
    # lips momentum check, volume multiplier, lowered ADX threshold for more trades, increased risk per trade,
    # removed early Teeth exits to let profits run longer, fixed trailing stop logic to use ffill and update on better levels,
    # added self.tp tracking for consistent take profit during trails. Target RR=2.5, risk=0.015 for higher returns with managed risk.
    def init(self):
        self.current_sl = None
        self.tp = None  # 🌙 Moon Dev: Track initial TP for trailing updates
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
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14)  # 🌙 Moon Dev: Added RSI for entry momentum filter
        
        self.up_fractal = self.I(compute_up_fractals, self.data.High)
        self.down_fractal = self.I(compute_down_fractals, self.data.Low)
        self.ffill_up = self.I(compute_ffill_fractal, self.up_fractal)
        self.ffill_down = self.I(compute_ffill_fractal, self.down_fractal)

    def next(self):
        # 🌙 Moon Dev: Lowered ADX threshold to 20 for more trading opportunities in trending markets
        if np.isnan(self.adx[-1]) or self.adx[-1] < 20:
            return

        risk_per_trade = 0.015  # 🌙 Moon Dev: Increased from 0.01 to 0.015 for higher position exposure and returns
        reward_risk = 2.5  # 🌙 Moon Dev: Added reward:risk ratio for take profit targeting higher RR
        vol_mult = 1.2  # 🌙 Moon Dev: Added volume multiplier to filter for stronger conviction entries
        risk_amount = risk_per_trade * self.initial_cash
        entry_price = self.data.Close[-1]
        atr_buffer = self.atr[-1]

        if not self.position:
            # Long entry - 🌙 Moon Dev: Tightened with RSI >50, lips momentum, volume *1.2, breakout confirmation
            if (self.data.Close[-1] > self.lips[-1] and
                self.lips[-1] > self.teeth[-1] > self.jaw[-1] and
                self.lips[-1] > self.lips[-2] and  # 🌙 Moon Dev: Added lips momentum for better trend confirmation
                self.ao[-1] > 0 and self.ao[-1] > self.ao[-2] and
                self.data.Volume[-1] > self.volume_ma[-1] * vol_mult and
                not np.isnan(self.rsi[-1]) and self.rsi[-1] > 50 and  # 🌙 Moon Dev: RSI filter to avoid weak momentum
                self.data.Close[-1] > self.ffill_up[-1] and
                self.data.Close[-2] <= self.ffill_up[-2]):
                
                sl = self.ffill_down[-1] - atr_buffer
                if not np.isnan(sl) and sl < entry_price:
                    risk_dist = entry_price - sl
                    tp = entry_price + reward_risk * risk_dist  # 🌙 Moon Dev: Calculate fixed TP based on RR
                    size = risk_amount / risk_dist
                    size = int(round(size))
                    if size > 0:
                        self.buy(size=size, sl=sl, tp=tp)
                        self.current_sl = sl
                        self.tp = tp  # 🌙 Moon Dev: Track TP for trailing
                        print(f"🌙 Moon Dev: Long entry at {entry_price:.2f}, Size: {size}, SL: {sl:.2f}, TP: {tp:.2f} 🚀")

            # Short entry - 🌙 Moon Dev: Symmetric tightening with RSI <50, lips momentum, volume *1.2
            elif (self.data.Close[-1] < self.lips[-1] and
                  self.lips[-1] < self.teeth[-1] < self.jaw[-1] and
                  self.lips[-1] < self.lips[-2] and  # 🌙 Moon Dev: Added lips momentum for better trend confirmation
                  self.ao[-1] < 0 and self.ao[-1] < self.ao[-2] and
                  self.data.Volume[-1] > self.volume_ma[-1] * vol_mult and
                  not np.isnan(self.rsi[-1]) and self.rsi[-1] < 50 and  # 🌙 Moon Dev: RSI filter to avoid weak momentum
                  self.data.Close[-1] < self.ffill_down[-1] and
                  self.data.Close[-2] >= self.ffill_down[-2]):
                
                sl = self.ffill_up[-1] + atr_buffer
                if not np.isnan(sl) and sl > entry_price:
                    risk_dist = sl - entry_price
                    tp = entry_price - reward_risk * risk_dist  # 🌙 Moon Dev: Calculate fixed TP based on RR
                    size = risk_amount / risk_dist
                    size = int(round(size))
                    if size > 0:
                        self.sell(size=size, sl=sl, tp=tp)
                        self.current_sl = sl
                        self.tp = tp  # 🌙 Moon Dev: Track TP for trailing
                        print(f"🌙 Moon Dev: Short entry at {entry_price:.2f}, Size: {size}, SL: {sl:.2f}, TP: {tp:.2f} 📉")

        if self.position:
            if self.position.is_long:
                # Exit conditions - 🌙 Moon Dev: Removed Teeth exit to let profits run to TP or trail, kept only hard Jaw exit
                if self.data.Close[-1] < self.jaw[-1]:
                    self.position.close()
                    self.current_sl = None
                    self.tp = None
                    print(f"🌙 Moon Dev: Long hard exit - below Jaw 😤")
                    return
                
                # Trail stop for long - 🌙 Moon Dev: Fixed to use ffill_down (last confirmed support) and update on better levels, pass fixed TP
                potential_sl = self.ffill_down[-1] - self.atr[-1]
                if (not np.isnan(potential_sl) and potential_sl > self.current_sl and 
                    potential_sl < self.data.Close[-1]):
                    trade_size = self.position.size
                    self.position.close()
                    self.buy(size=trade_size, sl=potential_sl, tp=self.tp)
                    self.current_sl = potential_sl
                    print(f"🌙 Moon Dev: Trailing SL long to {potential_sl:.2f} ✨")
            
            elif self.position.is_short:
                # Exit conditions - 🌙 Moon Dev: Removed Teeth exit to let profits run to TP or trail, kept only hard Jaw exit
                if self.data.Close[-1] > self.jaw[-1]:
                    self.position.close()
                    self.current_sl = None
                    self.tp = None
                    print(f"🌙 Moon Dev: Short hard exit - above Jaw 😤")
                    return
                
                # Trail stop for short - 🌙 Moon Dev: Fixed to use ffill_up (last confirmed resistance) and update on better levels, pass fixed TP
                potential_sl = self.ffill_up[-1] + self.atr[-1]
                if (not np.isnan(potential_sl) and potential_sl < self.current_sl and 
                    potential_sl > self.data.Close[-1]):
                    trade_size = abs(self.position.size)
                    self.position.close()
                    self.sell(size=trade_size, sl=potential_sl, tp=self.tp)
                    self.current_sl = potential_sl
                    print(f"🌙 Moon Dev: Trailing SL short to {potential_sl:.2f} ✨")

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