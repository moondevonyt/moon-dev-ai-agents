import pandas as pd
import talib
from backtesting import Backtest, Strategy

class QuadrupleHarmonic(Strategy):
    def init(self):
        self.ema = self.I(talib.EMA, self.data.Close, timeperiod=200)
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14)  # 🌙 Added RSI for oversold filter in pullbacks
        self.vol_sma = self.I(talib.SMA, self.data.Volume, timeperiod=20)  # 🌙 Added volume SMA for confirmation filter
        self.entry_bar = None  # To track for potential exits

    def next(self):
        current_close = self.data.Close[-1]
        current_open = self.data.Open[-1]
        current_low = self.data.Low[-1]
        current_high = self.data.High[-1]
        
        # Debug print for trend context 🌙
        if len(self.data) % 100 == 0:
            print(f"🌙 Moon Dev Debug: Current Close {current_close:.2f}, EMA {self.ema[-1]:.2f}, ADX {self.adx[-1]:.2f} ✨")
        
        # Early exit if position and breaks below EMA (post-entry filter) - kept for uptrend protection
        if self.position:
            if current_close < self.ema[-1]:
                self.position.close()
                print(f"🌙 Moon Dev Exit: Early close below EMA at {current_close:.2f} 🚀")
            # Time-based exit after 15 bars (extended from 10 for more room in volatile crypto) 🌙
            if self.entry_bar and len(self.data) - self.entry_bar > 15:
                self.position.close()
                print(f"🌙 Moon Dev Exit: Time-based close after 15 bars at {current_close:.2f} ✨")
            return
        
        # Entry logic only if no position
        if self.position or len(self.data) < 200:  # 🌙 Increased from 21 to 200 for EMA200 maturity
            return
        
        # Calculate bullish candle strength 🌙
        body = current_close - current_open
        candle_range = current_high - current_low
        strong_bullish = body > 0.5 * candle_range and body > 0  # 🌙 Tightened entry: require strong bullish candle body > 50% of range
        
        # Check for previous 4 consecutive down bars and current bullish confirmation (now in uptrend pullback) 🌙
        if (len(self.data) >= 5 and
            self.data.Close[-5] < self.data.Open[-5] and
            self.data.Close[-4] < self.data.Open[-4] and
            self.data.Close[-3] < self.data.Open[-3] and
            self.data.Close[-2] < self.data.Open[-2] and
            self.data.Close[-4] < self.data.Close[-5] and
            self.data.Close[-3] < self.data.Close[-4] and
            self.data.Close[-2] < self.data.Close[-3] and
            strong_bullish and  # Bullish confirmation candle with strength filter
            current_close > self.ema[-1] and  # 🌙 Changed to uptrend filter (from below to above EMA) for pullback buys in trending up markets
            self.adx[-1] > 20 and  # 🌙 Lowered ADX threshold from 25 to 20 for more quality trend signals without too many
            self.rsi[-1] < 40 and  # 🌙 Added RSI oversold filter for better pullback timing
            self.data.Volume[-1] > 1.5 * self.vol_sma[-1]):  # 🌙 Added volume filter: confirmation on higher than average volume for conviction
            
            print(f"🌙 Moon Dev Signal: 4 down bars pullback in uptrend, strong bullish confirmation at {current_close:.2f} 🚀")
            
            # Pattern details - improved min_low calculation 🌙
            pattern_lows = self.data.Low[-5:-1]  # Lows of the 4 down bars
            min_low = min(pattern_lows)
            
            # SL: below pattern low by 1 ATR (kept conservative)
            atr_val = self.atr[-1]
            sl_price = min_low - 1.0 * atr_val
            
            # Entry at current close (approximate)
            entry_price = current_close
            
            # Improved TP: Fixed 1:2 Risk-Reward ratio for better average returns 🌙 (replaced harmonic approx with standard RR)
            stop_distance = entry_price - sl_price
            if stop_distance <= 0:
                print(f"🌙 Moon Dev Skip: Zero or negative stop distance 😔")
                return
            tp_price = entry_price + 2 * stop_distance
            
            # Risk management: 1% risk, but compute as fraction of equity 🌙 (fixed position sizing to prevent overleverage)
            risk_pct = 0.01
            size_frac = risk_pct * (entry_price / stop_distance)
            size = min(size_frac, 0.5)  # Cap at 50% exposure for risk management in volatile BTC
            
            if size > 0:
                # Debug print before order 🌙
                print(f"🌙 Moon Dev Debug: Order params - Size {size:.4f}, SL {sl_price:.5f}, TP {tp_price:.5f}, Entry/Close {entry_price:.5f} ✨")
                # Removed limit=entry_price for market entry at next open (improves fill rate in gappy crypto) 🌙
                self.buy(size=size, sl=sl_price, tp=tp_price)
                self.entry_bar = len(self.data)
                print(f"🌙 Moon Dev Entry: Long {size:.4f} fraction at ~{entry_price:.2f}, SL {sl_price:.2f}, TP {tp_price:.2f} (Min Low {min_low:.2f}) 🚀✨")

# Data loading and cleaning
data_path = '/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv'
data = pd.read_csv(data_path)
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data = data.set_index(pd.to_datetime(data['datetime']))
data = data.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'})

# Ensure required columns exist
required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
for col in required_cols:
    if col not in data.columns:
        print(f"Warning: Column {col} missing!")

# Run backtest
bt = Backtest(data, QuadrupleHarmonic, cash=1000000, commission=0.002, exclusive_orders=True)
stats = bt.run()
print(stats)
print(stats._strategy)