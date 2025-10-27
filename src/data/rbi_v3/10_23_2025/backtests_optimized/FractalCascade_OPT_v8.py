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
        # 🌙 Moon Dev: Added current_tp for take profit management
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
        # 🌙 Moon Dev: Added RSI for momentum confirmation in entries
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14)
        
        self.up_fractal = self.I(compute_up_fractals, self.data.High)
        self.down_fractal = self.I(compute_down_fractals, self.data.Low)
        self.ffill_up = self.I(compute_ffill_fractal, self.up_fractal)
        self.ffill_down = self.I(compute_ffill_fractal, self.down_fractal)

    def next(self):
        # 🌙 Moon Dev: Lowered ADX threshold to 20 for more trading opportunities while maintaining trend filter
        if np.isnan(self.adx[-1]) or self.adx[-1] < 20:
            return

        # 🌙 Moon Dev: Increased risk per trade to 2% and use current cash for compounding risk management
        risk_per_trade = 0.02
        risk_amount = risk_per_trade * self._broker.cash
        entry_price = self.data.Close[-1]
        atr_buffer = self.atr[-1]

        if not self.position:
            # Long entry
            # 🌙 Moon Dev: Added RSI > 50 filter for bullish momentum; tightened volume to 1.5x MA for stronger confirmation
            if (self.data.Close[-1] > self.lips[-1] and
                self.lips[-1] > self.teeth[-1] > self.jaw[-1] and
                self.ao[-1] > 0 and self.ao[-1] > self.ao[-2] and
                self.data.Volume[-1] > 1.5 * self.volume_ma[-1] and
                self.rsi[-1] > 50 and
                self.data.Close[-1] > self.ffill_up[-1] and
                self.data.Close[-2] <= self.ffill_up[-2]):
                
                sl = self.ffill_down[-1] - atr_buffer
                if not np.isnan(sl) and sl < entry_price:
                    risk_dist = entry_price - sl
                    size = risk_amount / risk_dist
                    if size > 0:
                        self.buy(size=size, sl=sl)
                        self.current_sl = sl
                        # 🌙 Moon Dev: Added 2:1 R:R take profit for better reward capture
                        self.current_tp = entry_price + 2 * risk_dist
                        print(f"🌙 Moon Dev: Long entry at {entry_price:.2f}, Size: {size}, SL: {sl:.2f}, TP: {self.current_tp:.2f} 🚀")

            # Short entry
            elif (self.data.Close[-1] < self.lips[-1] and
                  self.lips[-1] < self.teeth[-1] < self.jaw[-1] and
                  self.ao[-1] < 0 and self.ao[-1] < self.ao[-2] and
                  self.data.Volume[-1] > 1.5 * self.volume_ma[-1] and
                  self.rsi[-1] < 50 and
                  self.data.Close[-1] < self.ffill_down[-1] and
                  self.data.Close[-2] >= self.ffill_down[-2]):
                
                sl = self.ffill_up[-1] + atr_buffer
                if not np.isnan(sl) and sl > entry_price:
                    risk_dist = sl - entry_price
                    size = risk_amount / risk_dist
                    if size > 0:
                        self.sell(size=size, sl=sl)
                        self.current_sl = sl
                        self.current_tp = entry_price - 2 * risk_dist
                        print(f"🌙 Moon Dev: Short entry at {entry_price:.2f}, Size: {size}, SL: {sl:.2f}, TP: {self.current_tp:.2f} 📉")

        if self.position:
            if self.position.is_long:
                # 🌙 Moon Dev: Check TP first for profit taking
                if not np.isnan(self.current_tp) and self.data.Close[-1] >= self.current_tp:
                    self.position.close()
                    self.current_sl = self.current_tp = None
                    print(f"🌙 Moon Dev: Long exit - TP hit 🚀")
                    return
                
                # Exit conditions
                if self.data.Close[-1] < self.teeth[-1]:
                    self.position.close()
                    self.current_sl = self.current_tp = None
                    print(f"🌙 Moon Dev: Long exit - below Teeth 📉")
                    return
                elif self.data.Close[-1] < self.jaw[-1]:
                    self.position.close()
                    self.current_sl = self.current_tp = None
                    print(f"🌙 Moon Dev: Long hard exit - below Jaw 😤")
                    return
                
                # 🌙 Moon Dev: Added ATR-based trailing stop for more frequent profit locking (Chandelier-style)
                potential_sl = self.data.Close[-1] - 2 * self.atr[-1]
                if potential_sl > self.current_sl and potential_sl < self.data.Close[-1]:
                    trade_size = self.position.size
                    self.position.close()
                    self.buy(size=trade_size, sl=potential_sl)
                    self.current_sl = potential_sl
                    # 🌙 Moon Dev: Update TP based on new SL for adjusted R:R
                    self.current_tp = self.data.Close[-1] + 2 * (self.data.Close[-1] - potential_sl)
                    print(f"🌙 Moon Dev: ATR Trailing SL long to {potential_sl:.2f}, TP: {self.current_tp:.2f} ✨")
                
                # Original fractal trailing
                current_sl = self.current_sl
                if not np.isnan(self.down_fractal[-1]):
                    new_sl = self.down_fractal[-1] - atr_buffer
                    if new_sl > current_sl:
                        trade_size = self.position.size
                        self.position.close()
                        self.buy(size=trade_size, sl=new_sl)
                        self.current_sl = new_sl
                        self.current_tp = self.data.Close[-1] + 2 * (self.data.Close[-1] - new_sl)
                        print(f"🌙 Moon Dev: Fractal Trailing SL long to {new_sl:.2f}, TP: {self.current_tp:.2f} ✨")
            
            elif self.position.is_short:
                # 🌙 Moon Dev: Check TP first for profit taking
                if not np.isnan(self.current_tp) and self.data.Close[-1] <= self.current_tp:
                    self.position.close()
                    self.current_sl = self.current_tp = None
                    print(f"🌙 Moon Dev: Short exit - TP hit 📉")
                    return
                
                # Exit conditions
                if self.data.Close[-1] > self.teeth[-1]:
                    self.position.close()
                    self.current_sl = self.current_tp = None
                    print(f"🌙 Moon Dev: Short exit - above Teeth 📈")
                    return
                elif self.data.Close[-1] > self.jaw[-1]:
                    self.position.close()
                    self.current_sl = self.current_tp = None
                    print(f"🌙 Moon Dev: Short hard exit - above Jaw 😤")
                    return
                
                # 🌙 Moon Dev: Added ATR-based trailing stop for shorts
                potential_sl = self.data.Close[-1] + 2 * self.atr[-1]
                if potential_sl < self.current_sl and potential_sl > self.data.Close[-1]:
                    trade_size = abs(self.position.size)
                    self.position.close()
                    self.sell(size=trade_size, sl=potential_sl)
                    self.current_sl = potential_sl
                    self.current_tp = self.data.Close[-1] - 2 * (potential_sl - self.data.Close[-1])
                    print(f"🌙 Moon Dev: ATR Trailing SL short to {potential_sl:.2f}, TP: {self.current_tp:.2f} ✨")
                
                # Original fractal trailing
                current_sl = self.current_sl
                if not np.isnan(self.up_fractal[-1]):
                    new_sl = self.up_fractal[-1] + atr_buffer
                    if new_sl < current_sl:
                        trade_size = abs(self.position.size)
                        self.position.close()
                        self.sell(size=trade_size, sl=new_sl)
                        self.current_sl = new_sl
                        self.current_tp = self.data.Close[-1] - 2 * (new_sl - self.data.Close[-1])
                        print(f"🌙 Moon Dev: Fractal Trailing SL short to {new_sl:.2f}, TP: {self.current_tp:.2f} ✨")

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