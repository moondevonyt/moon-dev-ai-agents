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
            # Time-based exit after 20 bars (extended from 15 for more room in volatile crypto, allowing trends to develop) 🌙
            if self.entry_bar and len(self.data) - self.entry_bar > 20:
                self.position.close()
                print(f"🌙 Moon Dev Exit: Time-based close after 20 bars at {current_close:.2f} ✨")
            return
        
        # Entry logic only if no position
        if self.position or len(self.data) < 200:  # 🌙 Increased from 21 to 200 for EMA200 maturity
            return
        
        # Calculate bullish candle strength 🌙
        body = current_close - current_open
        candle_range = current_high - current_low
        strong_bullish = body > 0.6 * candle_range and body > 0  # 🌙 Tightened entry further: require stronger bullish candle body > 60% of range for higher quality reversals
        
        # Check for previous 4 consecutive down bars and current bullish confirmation (now in uptrend pullback) 🌙
        if (len(self.data) >= 6 and  # 🌙 Extended to 6 for pullback depth check
            self.data.Close[-5] < self.data.Open[-5] and
            self.data.Close[-4] < self.data.Open[-4] and
            self.data.Close[-3] < self.data.Open[-3] and
            self.data.Close[-2] < self.data.Open[-2] and
            self.data.Close[-4] < self.data.Close[-5] and
            self.data.Close[-3] < self.data.Close[-4] and
            self.data.Close[-2] < self.data.Close[-3] and
            strong_bullish and  # Bullish confirmation candle with strength filter
            current_close > self.ema[-1] and  # 🌙 Changed to uptrend filter (from below to above EMA) for pullback buys in trending up markets
            self.ema[-1] > self.ema[-5] and  # 🌙 Added EMA rising filter for stronger uptrend confirmation, avoiding flat/choppy regimes
            self.adx[-1] > 25 and  # 🌙 Increased ADX threshold from 20 to 25 for stronger trend signals, reducing false entries in weak trends
            self.rsi[-1] < 35 and  # 🌙 Tightened RSI oversold filter from 40 to 35 for deeper pullbacks and better timing
            self.data.Volume[-1] > 2.0 * self.vol_sma[-1] and  # 🌙 Increased volume filter from 1.5x to 2x for higher conviction on reversal volume spikes
            
            # 🌙 Added pullback depth filter: total drop from close before down bars to min low > 1.5 ATR for meaningful pullbacks
            pattern_lows = self.data.Low[-5:-1]  # Lows of the 4 down bars
            min_low = min(pattern_lows)
            pullback_depth = self.data.Close[-6] - min_low
            atr_val = self.atr[-1]
            pullback_filter = pullback_depth > 1.5 * atr_val):
            
            print(f"🌙 Moon Dev Signal: 4 down bars pullback in uptrend, strong bullish confirmation at {current_close:.2f} 🚀")
            
            # Pattern details - improved min_low calculation 🌙
            pattern_lows = self.data.Low[-5:-1]  # Lows of the 4 down bars
            min_low = min(pattern_lows)
            
            # SL: below pattern low by 1.2 ATR (increased from 1.0 for more breathing room, reducing whipsaw stops in volatile BTC) 🌙
            atr_val = self.atr[-1]
            sl_price = min_low - 1.2 * atr_val
            
            # Entry at current close (approximate)
            entry_price = current_close
            
            # Improved TP: Increased to 1:3 Risk-Reward ratio (from 1:2) for higher average returns on winners, targeting 50%+ overall 🌙
            stop_distance = entry_price - sl_price
            if stop_distance <= 0:
                print(f"🌙 Moon Dev Skip: Zero or negative stop distance 😔")
                return
            tp_price = entry_price + 3 * stop_distance
            
            # Risk management: 1% risk, but compute as fraction of equity 🌙 (fixed position sizing to prevent overleverage)
            risk_pct = 0.01
            size_frac = risk_pct * (entry_price / stop_distance)
            size = min(size_frac, 0.3)  # 🌙 Reduced cap from 0.5 to 0.3 for tighter risk management, preserving capital for more opportunities
            
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