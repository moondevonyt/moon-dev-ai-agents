import pandas as pd
import talib
import numpy as np
from backtesting import Backtest, Strategy
import warnings
warnings.filterwarnings('ignore')

# Load and clean data
path = '/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv'
data = pd.read_csv(path)
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data = data.set_index(pd.to_datetime(data['datetime']))
data = data.rename(columns={
    'open': 'Open', 'high': 'High', 'low': 'Low', 
    'close': 'Close', 'volume': 'Volume'
})

class SqueezeValidation(Strategy):
    bb_period = 20
    bb_std = 2.0
    adx_period = 14
    adx_threshold = 25
    squeeze_threshold = 0.005  # 0.5% band width
    squeeze_bars = 5
    vol_multiplier = 1.5
    atr_period = 14
    risk_pct = 0.01
    rr_ratio = 1.0
    max_hold_bars = 4  # ~60 min on 15m

    def init(self):
        upper, middle, lower = self.I(talib.BBANDS, self.data.Close, timeperiod=self.bb_period,
                                      nbdevup=self.bb_std, nbdevdn=self.bb_std, matype=0)
        self.bb_upper = upper
        self.bb_lower = lower
        self.bb_middle = middle
        
        self.band_width = (self.bb_upper - self.bb_lower) / self.bb_middle
        
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=self.adx_period)
        self.plus_di = self.I(talib.PLUS_DI, self.data.High, self.data.Low, self.data.Close, timeperiod=self.adx_period)
        self.minus_di = self.I(talib.MINUS_DI, self.data.High, self.data.Low, self.data.Close, timeperiod=self.adx_period)
        
        self.vol_avg = self.I(talib.SMA, self.data.Volume, timeperiod=self.bb_period)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=self.atr_period)
        
        self.bar_count = 0
        self.entry_bar = -1
        print("🌙 Moon Dev: Initialized SqueezeValidation Strategy ✨")

    def next(self):
        self.bar_count += 1
        min_bars = max(self.bb_period, self.adx_period, self.atr_period) + self.squeeze_bars
        if self.bar_count < min_bars:
            return
        
        current_price = self.data.Close[-1]
        current_volume = self.data.Volume[-1]
        current_bw = self.band_width[-1]
        
        # Check for squeeze in previous bars (before current)
        in_squeeze = False
        if self.bar_count >= self.squeeze_bars + 1:
            prev_bw = self.band_width[-self.squeeze_bars-1 : -1]
            if not np.isnan(prev_bw.max()):
                in_squeeze = prev_bw.max() < self.squeeze_threshold
                if in_squeeze:
                    print(f"🌙 Moon Dev: Squeeze detected! Bar: {self.bar_count}, Max BW in prev {self.squeeze_bars} bars: {prev_bw.max():.4f} ✨")
        
        # Long Entry
        if not self.position and in_squeeze:
            if (current_price > self.bb_upper[-1] and
                self.adx[-1] > self.adx_threshold and self.adx[-1] > self.adx[-2] and
                self.plus_di[-1] > self.minus_di[-1] and
                current_volume > self.vol_multiplier * self.vol_avg[-1]):
                
                print(f"🌙 Moon Dev: Long ENTRY SIGNAL at bar {self.bar_count}! ADX: {self.adx[-1]:.2f}, +DI: {self.plus_di[-1]:.2f}, -DI: {self.minus_di[-1]:.2f}, Vol ratio: {current_volume / self.vol_avg[-1]:.2f} ✨")
                
                entry_price = current_price
                stop_distance = self.atr[-1]
                sl_price = entry_price - stop_distance
                tp_price = entry_price + (stop_distance * self.rr_ratio)
                
                relative_risk = stop_distance / entry_price
                size = self.risk_pct / relative_risk
                size = min(1.0, size)
                self.buy(size=size, sl=sl_price, tp=tp_price)
                actual_entry = entry_price
                self.entry_bar = self.bar_count
                print(f"🌙 Moon Dev: Long Entry 🚀 Price: {actual_entry:.2f}, Size: {size:.4f}, SL: {sl_price:.2f}, TP: {tp_price:.2f} ✨")
        
        # Short Entry
        if not self.position and in_squeeze:
            if (current_price < self.bb_lower[-1] and
                self.adx[-1] > self.adx_threshold and self.adx[-1] > self.adx[-2] and
                self.minus_di[-1] > self.plus_di[-1] and
                current_volume > self.vol_multiplier * self.vol_avg[-1]):
                
                print(f"🌙 Moon Dev: Short ENTRY SIGNAL at bar {self.bar_count}! ADX: {self.adx[-1]:.2f}, +DI: {self.plus_di[-1]:.2f}, -DI: {self.minus_di[-1]:.2f}, Vol ratio: {current_volume / self.vol_avg[-1]:.2f} ✨")
                
                entry_price = current_price
                stop_distance = self.atr[-1]
                sl_price = entry_price + stop_distance
                tp_price = entry_price - (stop_distance * self.rr_ratio)
                
                relative_risk = stop_distance / entry_price
                size = self.risk_pct / relative_risk
                size = min(1.0, size)
                self.sell(size=size, sl=sl_price, tp=tp_price)
                actual_entry = entry_price
                self.entry_bar = self.bar_count
                print(f"🌙 Moon Dev: Short Entry 📉 Price: {actual_entry:.2f}, Size: {size:.4f}, SL: {sl_price:.2f}, TP: {tp_price:.2f} ✨")
        
        # Exit Management
        if self.position:
            current_price = self.data.Close[-1]
            is_long = self.position.size > 0
            
            # Max hold time
            if self.entry_bar > 0:
                bars_held = self.bar_count - self.entry_bar + 1
                if bars_held > self.max_hold_bars:
                    self.position.close()
                    print(f"🌙 Moon Dev: Time Exit ⏰ Bars held: {bars_held} ✨")
                    self.entry_bar = -1
                    return
            
            # Early exit conditions
            if is_long:
                if (current_price < self.bb_middle[-1] or  # Re-enter bands
                    self.adx[-1] < 20 or
                    self.plus_di[-1] < self.minus_di[-1]):
                    self.position.close()
                    reason = "Re-enter bands" if current_price < self.bb_middle[-1] else "ADX/DI invalid"
                    print(f"🌙 Moon Dev: Long Exit {reason} 📊 Price: {current_price:.2f} ✨")
                    self.entry_bar = -1
            else:
                if (current_price > self.bb_middle[-1] or  # Re-enter bands
                    self.adx[-1] < 20 or
                    self.minus_di[-1] < self.plus_di[-1]):
                    self.position.close()
                    reason = "Re-enter bands" if current_price > self.bb_middle[-1] else "ADX/DI invalid"
                    print(f"🌙 Moon Dev: Short Exit {reason} 📊 Price: {current_price:.2f} ✨")
                    self.entry_bar = -1

# Run backtest
bt = Backtest(data, SqueezeValidation, cash=100000, commission=0.002, exclusive_orders=True)
stats = bt.run()
print(stats)