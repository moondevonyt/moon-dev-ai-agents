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
        # 🌙 Moon Dev: Added RSI for momentum confirmation to filter better entries
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14)
        
        self.up_fractal = self.I(compute_up_fractals, self.data.High)
        self.down_fractal = self.I(compute_down_fractals, self.data.Low)
        self.ffill_up = self.I(compute_ffill_fractal, self.up_fractal)
        self.ffill_down = self.I(compute_ffill_fractal, self.down_fractal)

    def next(self):
        if np.isnan(self.adx[-1]) or self.adx[-1] < 30:  # 🌙 Moon Dev: Tightened ADX to 30 for stronger trend filter
            return

        # 🌙 Moon Dev: Use current equity for risk calculation to adapt to portfolio growth
        equity = self._broker.get_equity()
        risk_per_trade = 0.015  # 🌙 Moon Dev: Increased risk per trade to 1.5% for higher returns while managing risk
        risk_amount = risk_per_trade * equity
        entry_price = self.data.Close[-1]
        atr_buffer = self.atr[-1]

        if not self.position:
            # Long entry
            if (self.data.Close[-1] > self.lips[-1] and
                self.lips[-1] > self.teeth[-1] > self.jaw[-1] and
                self.ao[-1] > 0 and self.ao[-1] > self.ao[-2] and
                self.data.Volume[-1] > 1.2 * self.volume_ma[-1] and  # 🌙 Moon Dev: Stricter volume filter (1.2x) to avoid low-quality signals
                self.rsi[-1] > 50 and  # 🌙 Moon Dev: RSI >50 for bullish momentum confirmation
                self.data.Close[-1] > self.ffill_up[-1] and
                self.data.Close[-2] <= self.ffill_up[-2]):
                
                sl = self.ffill_down[-1] - atr_buffer
                if sl < entry_price:
                    risk_dist = entry_price - sl
                    size = risk_amount / risk_dist
                    size = int(round(size))
                    if size > 0:
                        # 🌙 Moon Dev: Added 2:1 RR TP to lock in profits and improve returns
                        tp = entry_price + 2 * risk_dist
                        self.buy(size=size, sl=sl, tp=tp)
                        self.current_sl = sl
                        print(f"🌙 Moon Dev: Long entry at {entry_price:.2f}, Size: {size}, SL: {sl:.2f}, TP: {tp:.2f} 🚀")

            # Short entry
            elif (self.data.Close[-1] < self.lips[-1] and
                  self.lips[-1] < self.teeth[-1] < self.jaw[-1] and
                  self.ao[-1] < 0 and self.ao[-1] < self.ao[-2] and
                  self.data.Volume[-1] > 1.2 * self.volume_ma[-1] and  # 🌙 Moon Dev: Stricter volume filter (1.2x) to avoid low-quality signals
                  self.rsi[-1] < 50 and  # 🌙 Moon Dev: RSI <50 for bearish momentum confirmation
                  self.data.Close[-1] < self.ffill_down[-1] and
                  self.data.Close[-2] >= self.ffill_down[-2]):
                
                sl = self.ffill_up[-1] + atr_buffer
                if sl > entry_price:
                    risk_dist = sl - entry_price
                    size = risk_amount / risk_dist
                    size = int(round(size))
                    if size > 0:
                        # 🌙 Moon Dev: Added 2:1 RR TP to lock in profits and improve returns
                        tp = entry_price - 2 * risk_dist
                        self.sell(size=size, sl=sl, tp=tp)
                        self.current_sl = sl
                        print(f"🌙 Moon Dev: Short entry at {entry_price:.2f}, Size: {size}, SL: {sl:.2f}, TP: {tp:.2f} 📉")

        if self.position:
            if self.position.is_long:
                # Exit conditions: Removed Teeth exit to let profits run longer, only Jaw for hard exit
                if self.data.Close[-1] < self.jaw[-1]:
                    self.position.close()
                    self.current_sl = None
                    print(f"🌙 Moon Dev: Long hard exit - below Jaw 😤")
                    return
                
                # Trail stop for long
                current_sl = self.current_sl
                if not np.isnan(self.down_fractal[-1]):
                    new_sl = self.down_fractal[-1] - atr_buffer
                    if new_sl > current_sl:
                        trade_size = self.position.size
                        self.position.close()
                        # 🌙 Moon Dev: Re-apply TP when trailing to maintain RR
                        new_tp = self.data.Close[-1] + 2 * (self.data.Close[-1] - new_sl)
                        self.buy(size=trade_size, sl=new_sl, tp=new_tp)
                        self.current_sl = new_sl
                        print(f"🌙 Moon Dev: Trailing SL long to {new_sl:.2f} ✨")
            
            elif self.position.is_short:
                # Exit conditions: Removed Teeth exit to let profits run longer, only Jaw for hard exit
                if self.data.Close[-1] > self.jaw[-1]:
                    self.position.close()
                    self.current_sl = None
                    print(f"🌙 Moon Dev: Short hard exit - above Jaw 😤")
                    return
                
                # Trail stop for short
                current_sl = self.current_sl
                if not np.isnan(self.up_fractal[-1]):
                    new_sl = self.up_fractal[-1] + atr_buffer
                    if new_sl < current_sl:
                        trade_size = abs(self.position.size)
                        self.position.close()
                        # 🌙 Moon Dev: Re-apply TP when trailing to maintain RR
                        new_tp = self.data.Close[-1] - 2 * (new_sl - self.data.Close[-1])
                        self.sell(size=trade_size, sl=new_sl, tp=new_tp)
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