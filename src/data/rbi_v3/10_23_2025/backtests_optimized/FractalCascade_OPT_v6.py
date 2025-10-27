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
        # 🌙 Moon Dev: Removed initial_cash as we now use current portfolio value for compounding risk
        median = (self.data.High + self.data.Low) / 2
        
        jaw_period = 13
        self.jaw = self.I(compute_shifted_ema, median, jaw_period, 8)
        
        teeth_period = 8
        self.teeth = self.I(compute_shifted_ema, median, teeth_period, 5)
        
        lips_period = 5
        self.lips = self.I(compute_shifted_ema, median, lips_period, 3)
        
        # 🌙 Moon Dev: Changed AO to use SMA for more standard Bill Williams implementation - improves signal quality
        ao_fast = 5
        ao_slow = 34
        smma_fast = self.I(talib.SMA, median, timeperiod=ao_fast)
        smma_slow = self.I(talib.SMA, median, timeperiod=ao_slow)
        self.ao = smma_fast - smma_slow
        
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        self.volume_ma = self.I(talib.SMA, self.data.Volume, timeperiod=20)
        
        # 🌙 Moon Dev: Added RSI for momentum confirmation - filters out weak entries
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14)
        
        # 🌙 Moon Dev: Added EMA50 trend filter - ensures entries align with intermediate trend, avoids chop
        self.ema50 = self.I(talib.EMA, self.data.Close, timeperiod=50)
        
        self.up_fractal = self.I(compute_up_fractals, self.data.High)
        self.down_fractal = self.I(compute_down_fractals, self.data.Low)
        self.ffill_up = self.I(compute_ffill_fractal, self.up_fractal)
        self.ffill_down = self.I(compute_ffill_fractal, self.down_fractal)

    def next(self):
        # 🌙 Moon Dev: Reset SL if no position to avoid stale values
        if not self.position:
            self.current_sl = None
        
        # 🌙 Moon Dev: Tightened ADX threshold to 30 for stronger trend filter - reduces false signals in weak markets
        if np.isnan(self.adx[-1]) or self.adx[-1] < 30:
            return

        # 🌙 Moon Dev: Increased risk per trade to 2% and use current portfolio value for compounding - boosts returns while managing risk
        risk_per_trade = 0.02
        risk_amount = risk_per_trade * self._broker.getvalue()
        entry_price = self.data.Close[-1]
        atr_buffer = self.atr[-1]

        if not self.position:
            # Long entry - added RSI >50 and Close > EMA50 for better momentum and trend alignment
            if (self.data.Close[-1] > self.lips[-1] and
                self.lips[-1] > self.teeth[-1] > self.jaw[-1] and
                self.ao[-1] > 0 and self.ao[-1] > self.ao[-2] and
                self.data.Volume[-1] > 1.2 * self.volume_ma[-1] and  # 🌙 Moon Dev: Tightened volume filter to 1.2x for higher conviction setups
                self.rsi[-1] > 50 and
                self.data.Close[-1] > self.ema50[-1] and
                self.data.Close[-1] > self.ffill_up[-1] and
                self.data.Close[-2] <= self.ffill_up[-2]):
                
                sl = self.ffill_down[-1] - atr_buffer
                if sl < entry_price and not np.isnan(sl):
                    risk_dist = entry_price - sl
                    size = risk_amount / risk_dist
                    size = int(round(size))
                    if size > 0:
                        # 🌙 Moon Dev: Added 2:1 RR take profit for quicker wins and better risk-reward
                        tp = entry_price + 2 * risk_dist
                        self.buy(size=size, sl=sl, tp=tp)
                        self.current_sl = sl
                        print(f"🌙 Moon Dev: Long entry at {entry_price:.2f}, Size: {size}, SL: {sl:.2f}, TP: {tp:.2f} 🚀")

            # Short entry - added RSI <50 and Close < EMA50 for better momentum and trend alignment
            elif (self.data.Close[-1] < self.lips[-1] and
                  self.lips[-1] < self.teeth[-1] < self.jaw[-1] and
                  self.ao[-1] < 0 and self.ao[-1] < self.ao[-2] and
                  self.data.Volume[-1] > 1.2 * self.volume_ma[-1] and  # 🌙 Moon Dev: Tightened volume filter to 1.2x for higher conviction setups
                  self.rsi[-1] < 50 and
                  self.data.Close[-1] < self.ema50[-1] and
                  self.data.Close[-1] < self.ffill_down[-1] and
                  self.data.Close[-2] >= self.ffill_down[-2]):
                
                sl = self.ffill_up[-1] + atr_buffer
                if sl > entry_price and not np.isnan(sl):
                    risk_dist = sl - entry_price
                    size = risk_amount / risk_dist
                    size = int(round(size))
                    if size > 0:
                        # 🌙 Moon Dev: Added 2:1 RR take profit for quicker wins and better risk-reward
                        tp = entry_price - 2 * risk_dist
                        self.sell(size=size, sl=sl, tp=tp)
                        self.current_sl = sl
                        print(f"🌙 Moon Dev: Short entry at {entry_price:.2f}, Size: {size}, SL: {sl:.2f}, TP: {tp:.2f} 📉")

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
                
                # Trail stop for long - no TP on re-entry to allow runners in trends
                current_sl = self.current_sl
                if not np.isnan(self.down_fractal[-1]):
                    new_sl = self.down_fractal[-1] - atr_buffer
                    if new_sl > current_sl:
                        trade_size = self.position.size
                        self.position.close()
                        self.buy(size=trade_size, sl=new_sl)
                        self.current_sl = new_sl
                        print(f"🌙 Moon Dev: Trailing SL long to {new_sl:.2f} ✨")
            
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
                
                # Trail stop for short - no TP on re-entry to allow runners in trends
                current_sl = self.current_sl
                if not np.isnan(self.up_fractal[-1]):
                    new_sl = self.up_fractal[-1] + atr_buffer
                    if new_sl < current_sl:
                        trade_size = abs(self.position.size)
                        self.position.close()
                        self.sell(size=trade_size, sl=new_sl)
                        self.current_sl = new_sl
                        print(f"🌙 Moon Dev: Trailing SL short to {new_sl:.2f} ✨")

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