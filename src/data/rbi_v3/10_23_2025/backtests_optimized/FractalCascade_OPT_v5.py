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
    # 🌙 Moon Dev Optimization: Enhanced strategy for higher returns (target 50%) with better risk management
    # Key improvements:
    # - Added SMA200 trend filter to ensure trades align with long-term trend (market regime filter)
    # - Added RSI(14) momentum confirmation (>50 for long, <50 for short) to tighten entries
    # - Increased volume filter to >1.5x MA for higher conviction setups
    # - Switched to volatility-adjusted position sizing: risks fixed % of equity based on stop distance (improved risk management)
    # - Increased risk per trade to 1.5% to amplify returns while maintaining control
    # - Added take-profit at 2:1 reward-to-risk ratio to lock in profits (exit optimization)
    # - Removed early exit on Teeth crossing to let winners run longer (improves return potential)
    # - Enhanced trailing stops: re-positions with updated size, SL, and TP based on new risk distance (dynamic exits)
    # - All changes focus on realistic enhancements without curve-fitting; keeps original structure intact
    def init(self):
        self.current_sl = None
        # Removed initial_cash - now using dynamic equity-based sizing
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
        
        # 🌙 Moon Dev: Added complementary indicators for optimization
        self.sma200 = self.I(talib.SMA, self.data.Close, timeperiod=200)  # Long-term trend filter
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14)  # Momentum filter
        
        self.up_fractal = self.I(compute_up_fractals, self.data.High)
        self.down_fractal = self.I(compute_down_fractals, self.data.Low)
        self.ffill_up = self.I(compute_ffill_fractal, self.up_fractal)
        self.ffill_down = self.I(compute_ffill_fractal, self.down_fractal)

    def next(self):
        if np.isnan(self.adx[-1]) or self.adx[-1] < 25:
            return

        risk_per_trade = 0.015  # 🌙 Moon Dev: Increased from 1% to 1.5% for higher returns with controlled risk
        atr_buffer = self.atr[-1]
        entry_price = self.data.Close[-1]

        if not self.position:
            # Long entry - tightened with new filters
            if (self.data.Close[-1] > self.lips[-1] and
                self.lips[-1] > self.teeth[-1] > self.jaw[-1] and
                self.ao[-1] > 0 and self.ao[-1] > self.ao[-2] and
                self.data.Volume[-1] > 1.5 * self.volume_ma[-1] and  # 🌙 Moon Dev: Tightened volume filter for better setups
                self.data.Close[-1] > self.ffill_up[-1] and
                self.data.Close[-2] <= self.ffill_up[-2] and
                self.data.Close[-1] > self.sma200[-1] and  # 🌙 Moon Dev: Trend filter - only long in uptrend
                self.rsi[-1] > 50):  # 🌙 Moon Dev: RSI momentum confirmation
                
                sl = self.ffill_down[-1] - atr_buffer
                if sl < entry_price:
                    risk_dist = entry_price - sl
                    stop_pct = risk_dist / entry_price
                    pos_size = risk_per_trade / stop_pct
                    if pos_size > 1:
                        pos_size = 1
                    tp = entry_price + 2 * risk_dist  # 🌙 Moon Dev: Added 2:1 RR take profit
                    self.buy(size=pos_size, sl=sl, tp=tp)
                    self.current_sl = sl
                    print(f"🌙 Moon Dev: Long entry at {entry_price:.2f}, Size: {pos_size:.4f} (fraction), SL: {sl:.2f}, TP: {tp:.2f} 🚀")

            # Short entry - tightened with new filters
            elif (self.data.Close[-1] < self.lips[-1] and
                  self.lips[-1] < self.teeth[-1] < self.jaw[-1] and
                  self.ao[-1] < 0 and self.ao[-1] < self.ao[-2] and
                  self.data.Volume[-1] > 1.5 * self.volume_ma[-1] and  # 🌙 Moon Dev: Tightened volume filter
                  self.data.Close[-1] < self.ffill_down[-1] and
                  self.data.Close[-2] >= self.ffill_down[-2] and
                  self.data.Close[-1] < self.sma200[-1] and  # 🌙 Moon Dev: Trend filter - only short in downtrend
                  self.rsi[-1] < 50):  # 🌙 Moon Dev: RSI momentum confirmation
                
                sl = self.ffill_up[-1] + atr_buffer
                if sl > entry_price:
                    risk_dist = sl - entry_price
                    stop_pct = risk_dist / entry_price
                    pos_size = risk_per_trade / stop_pct
                    if pos_size > 1:
                        pos_size = 1
                    tp = entry_price - 2 * risk_dist  # 🌙 Moon Dev: Added 2:1 RR take profit
                    self.sell(size=pos_size, sl=sl, tp=tp)
                    self.current_sl = sl
                    print(f"🌙 Moon Dev: Short entry at {entry_price:.2f}, Size: {pos_size:.4f} (fraction), SL: {sl:.2f}, TP: {tp:.2f} 📉")

        if self.position:
            if self.position.is_long:
                # 🌙 Moon Dev: Removed early exit below Teeth to let winners run; kept hard exit below Jaw
                if self.data.Close[-1] < self.jaw[-1]:
                    self.position.close()
                    self.current_sl = None
                    print(f"🌙 Moon Dev: Long hard exit - below Jaw 😤")
                    return
                
                # Trail stop for long - enhanced with re-positioning
                current_sl = self.current_sl
                if not np.isnan(self.down_fractal[-1]):
                    new_sl = self.down_fractal[-1] - atr_buffer
                    if new_sl > current_sl and new_sl < entry_price:
                        self.position.close()
                        new_entry = self.data.Close[-1]
                        new_risk_dist = new_entry - new_sl
                        if new_risk_dist > 0:
                            new_stop_pct = new_risk_dist / new_entry
                            new_pos_size = risk_per_trade / new_stop_pct
                            if new_pos_size > 1:
                                new_pos_size = 1
                            new_tp = new_entry + 2 * new_risk_dist
                            self.buy(size=new_pos_size, sl=new_sl, tp=new_tp)
                            self.current_sl = new_sl
                            print(f"🌙 Moon Dev: Trailing SL long to {new_sl:.2f}, Size: {new_pos_size:.4f}, TP: {new_tp:.2f} ✨")
            
            elif self.position.is_short:
                # 🌙 Moon Dev: Removed early exit above Teeth to let winners run; kept hard exit above Jaw
                if self.data.Close[-1] > self.jaw[-1]:
                    self.position.close()
                    self.current_sl = None
                    print(f"🌙 Moon Dev: Short hard exit - above Jaw 😤")
                    return
                
                # Trail stop for short - enhanced with re-positioning
                current_sl = self.current_sl
                if not np.isnan(self.up_fractal[-1]):
                    new_sl = self.up_fractal[-1] + atr_buffer
                    if new_sl < current_sl and new_sl > entry_price:
                        self.position.close()
                        new_entry = self.data.Close[-1]
                        new_risk_dist = new_sl - new_entry
                        if new_risk_dist > 0:
                            new_stop_pct = new_risk_dist / new_entry
                            new_pos_size = risk_per_trade / new_stop_pct
                            if new_pos_size > 1:
                                new_pos_size = 1
                            new_tp = new_entry - 2 * new_risk_dist
                            self.sell(size=new_pos_size, sl=new_sl, tp=new_tp)
                            self.current_sl = new_sl
                            print(f"🌙 Moon Dev: Trailing SL short to {new_sl:.2f}, Size: {new_pos_size:.4f}, TP: {new_tp:.2f} ✨")

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