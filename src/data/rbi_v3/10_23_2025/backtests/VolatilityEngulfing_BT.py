import pandas as pd
import talib
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import numpy as np

# Data loading and cleaning
path = '/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv'
data = pd.read_csv(path, parse_dates=['datetime'], index_col='datetime')
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data.columns = [col.capitalize() for col in data.columns]
data = data[['Open', 'High', 'Low', 'Close', 'Volume']]

class VolatilityEngulfing(Strategy):
    bb_period = 20
    bb_std = 2.0
    vol_period = 20
    vol_multiplier = 1.5
    sma_period = 50
    atr_period = 14
    risk_per_trade = 0.01
    rr_ratio = 2.0
    atr_multiplier_sl = 1.0

    def init(self):
        # Bollinger Bands
        self.bb_upper, self.bb_middle, self.bb_lower = self.I(talib.BBANDS, self.data.Close, timeperiod=self.bb_period, nbdevup=self.bb_std, nbdevdn=self.bb_std, matype=0)
        
        # Volume SMA
        self.vol_sma = self.I(talib.SMA, self.data.Volume, timeperiod=self.vol_period)
        
        # 50 SMA
        self.sma50 = self.I(talib.SMA, self.data.Close, timeperiod=self.sma_period)
        
        # ATR
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=self.atr_period)
        
        # Debug print
        print("🌙 Moon Dev: VolatilityEngulfing Strategy Initialized! 🚀 Bollinger Bands, Volume SMA, SMA50, and ATR ready. ✨")

    def next(self):
        # Skip if not enough data
        if len(self.data) < max(self.bb_period, self.vol_period, self.sma_period, self.atr_period) + 1:
            return
        
        # Current and previous values
        curr_o = self.data.Open[-1]
        curr_h = self.data.High[-1]
        curr_l = self.data.Low[-1]
        curr_c = self.data.Close[-1]
        curr_v = self.data.Volume[-1]
        
        prev_o = self.data.Open[-2]
        prev_c = self.data.Close[-2]
        
        # Bullish Engulfing
        bearish_prev = prev_c < prev_o
        bullish_curr = curr_c > curr_o
        engulfs = (curr_o < prev_c) and (curr_c > prev_o)
        is_bullish_engulfing = bearish_prev and bullish_curr and engulfs
        
        # Bearish Engulfing for exit
        prev_bullish = prev_c > prev_o
        bearish_curr_exit = curr_c < curr_o  # Hypothetical for current, but use prev for signal
        # For exit, check on current bar as potential signal
        bearish_engulfs = prev_bullish and (curr_c < curr_o) and (curr_o > prev_c) and (curr_c < prev_o)
        is_bearish_engulfing = bearish_engulfs
        
        # Entry conditions
        breakout = curr_c > self.bb_upper[-1]
        vol_confirm = curr_v > self.vol_multiplier * self.vol_sma[-1]
        trend_filter = curr_c > self.sma50[-1]
        pattern_confirm = is_bullish_engulfing
        
        # Debug print for signals
        if breakout and vol_confirm and pattern_confirm and trend_filter:
            print(f"🌙 Moon Dev: Volatility Breakout Detected! Close: {curr_c:.2f} > BB Upper: {self.bb_upper[-1]:.2f} | Vol: {curr_v:.2f} > {self.vol_multiplier}*{self.vol_sma[-1]:.2f} | Engulfing: True | Above SMA50: {self.sma50[-1]:.2f} 🚀")
        
        # Entry logic
        if not self.position and breakout and vol_confirm and pattern_confirm and trend_filter:
            # Approximate entry price (will execute at next open, approx with current close)
            entry_price = curr_c
            # SL below current low minus ATR buffer
            sl_price = curr_l - (self.atr_multiplier_sl * self.atr[-1])
            risk_dist = entry_price - sl_price
            if risk_dist > 0:
                risk_amount = self.equity * self.risk_per_trade
                units = risk_amount / risk_dist
                size = int(round(units))
                tp_price = entry_price + (self.rr_ratio * risk_dist)
                
                self.buy(size=size, sl=sl_price, tp=tp_price)
                print(f"🚀 Moon Dev: Long Entry! Size: {size}, Entry≈{entry_price:.2f}, SL: {sl_price:.2f}, TP: {tp_price:.2f} | Risk: {risk_amount:.2f} (1%) ✨")
        
        # Additional exit logic if in position
        if self.position:
            # Exit if close below middle BB
            if curr_c < self.bb_middle[-1]:
                self.position.close()
                print(f"🌙 Moon Dev: Trailing Exit - Close below Middle BB: {curr_c:.2f} < {self.bb_middle[-1]:.2f} 💫")
            
            # Exit on bearish engulfing
            if is_bearish_engulfing:
                self.position.close()
                print(f"🌙 Moon Dev: Bearish Engulfing Exit! 🚨 Pattern confirmed, closing position.")
        
        # Debug position info
        if self.position:
            print(f"🌙 Moon Dev Position Update: PL: {self.position.pl:.2f}, Size: {self.position.size}, Entry: {self.position.entry_price:.2f} 📊")

# Run backtest
bt = Backtest(data, VolatilityEngulfing, cash=1000000, commission=0.002, exclusive_orders=True)
stats = bt.run()
print(stats)