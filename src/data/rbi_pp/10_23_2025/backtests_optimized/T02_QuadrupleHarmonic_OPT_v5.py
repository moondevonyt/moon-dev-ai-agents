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
        self.macd, self.macdsignal, _ = self.I(talib.MACD, self.data.Close, fastperiod=12, slowperiod=26, signalperiod=9)  # 🌙 New: Added MACD for momentum confirmation to filter better entries
        self.entry_bar = None  # To track for potential exits
        self.highest_since_entry = 0  # 🌙 New: Track high for trailing stop activation

    def next(self):
        current_close = self.data.Close[-1]
        current_open = self.data.Open[-1]
        current_low = self.data.Low[-1]
        current_high = self.data.High[-1]
        
        # Debug print for trend context 🌙
        if len(self.data) % 100 == 0:
            print(f"🌙 Moon Dev Debug: Current Close {current_close:.2f}, EMA {self.ema[-1]:.2f}, ADX {self.adx[-1]:.2f} ✨")
        
        # Enhanced exit logic for position management 🌙
        if self.position:
            # Early exit if breaks below EMA (uptrend protection)
            if current_close < self.ema[-1]:
                self.position.close()
                print(f"🌙 Moon Dev Exit: Early close below EMA at {current_close:.2f} 🚀")
            # Time-based exit extended to 20 bars for more room in crypto trends 🌙 (improves holding winners longer)
            if self.entry_bar and len(self.data) - self.entry_bar > 20:
                self.position.close()
                print(f"🌙 Moon Dev Exit: Time-based close after 20 bars at {current_close:.2f} ✨")
            # New: Trailing stop after 1:1 RR reached 🌙 (activates trail to capture more upside while protecting gains)
            entry_price = self.position.plns  # Planned entry price
            stop_distance = entry_price - self.position.sl
            if current_high > entry_price + stop_distance:  # If price reached 1:1
                trail_sl = current_high - 1.5 * self.atr[-1]  # Trail 1.5 ATR below high
                if trail_sl > self.position.sl:
                    self.position.sl = trail_sl
                    print(f"🌙 Moon Dev Update: Trailing SL to {trail_sl:.2f} after 1:1 hit 🚀")
            # Update highest since entry for trail reference
            if current_high > self.highest_since_entry:
                self.highest_since_entry = current_high
            return
        
        # Entry logic only if no position
        if self.position or len(self.data) < 200:  # 🌙 Increased from 21 to 200 for EMA200 maturity
            return
        
        # Enhanced bullish candle strength filter 🌙 (tightened to >60% body for higher quality reversals)
        body = current_close - current_open
        candle_range = current_high - current_low
        strong_bullish = body > 0.6 * candle_range and body > 0  # 🌙 Tightened from 0.5 to 0.6 for better entry setups
        
        # Check for previous 4 consecutive down bars and current bullish confirmation (uptrend pullback) 🌙
        # Added pullback depth filter: min low not below 5% of EMA to avoid deep corrections 🌙 (improves risk-reward in trends)
        if (len(self.data) >= 5 and
            self.data.Close[-5] < self.data.Open[-5] and
            self.data.Close[-4] < self.data.Open[-4] and
            self.data.Close[-3] < self.data.Open[-3] and
            self.data.Close[-2] < self.data.Open[-2] and
            self.data.Close[-4] < self.data.Close[-5] and
            self.data.Close[-3] < self.data.Close[-4] and
            self.data.Close[-2] < self.data.Close[-3] and
            strong_bullish and  # Bullish confirmation candle with enhanced strength filter
            current_close > self.ema[-1] and  # Uptrend filter for pullback buys
            self.adx[-1] > 25 and  # 🌙 Raised ADX from 20 to 25 for stronger trend filter (reduces choppy entries)
            self.rsi[-1] < 35 and  # 🌙 Tightened RSI from <40 to <35 for deeper oversold pullbacks (better timing)
            self.data.Volume[-1] > 2.0 * self.vol_sma[-1] and  # 🌙 Increased volume filter from 1.5x to 2x for higher conviction signals
            self.macd[-1] > self.macdsignal[-1] and  # 🌙 New: MACD bullish crossover for momentum confirmation
            min(self.data.Low[-5:-1]) > 0.95 * self.ema[-1]):  # 🌙 New: Pullback depth filter to stay in shallow retracements
            
            print(f"🌙 Moon Dev Signal: Enhanced 4 down bars pullback in strong uptrend at {current_close:.2f} 🚀")
            
            # Pattern details - improved min_low calculation 🌙
            pattern_lows = self.data.Low[-5:-1]  # Lows of the 4 down bars
            min_low = min(pattern_lows)
            
            # SL: Adjusted to 1.5 ATR below pattern low for more breathing room in volatile crypto 🌙 (reduces premature stops)
            atr_val = self.atr[-1]
            sl_price = min_low - 1.5 * atr_val
            
            # Entry at current close (approximate)
            entry_price = current_close
            
            # Enhanced TP: Increased to 1:3 Risk-Reward ratio for higher return potential 🌙 (balances more winners in trends)
            stop_distance = entry_price - sl_price
            if stop_distance <= 0:
                print(f"🌙 Moon Dev Skip: Zero or negative stop distance 😔")
                return
            tp_price = entry_price + 3 * stop_distance
            
            # Risk management: Reduced to 0.75% risk for tighter control, still fraction of equity 🌙 (improves drawdown management)
            risk_pct = 0.0075
            size_frac = risk_pct * (entry_price / stop_distance)
            size = min(size_frac, 0.3)  # 🌙 Lowered cap from 0.5 to 0.3 for better risk in volatile markets
            
            if size > 0:
                # Debug print before order 🌙
                print(f"🌙 Moon Dev Debug: Order params - Size {size:.4f}, SL {sl_price:.5f}, TP {tp_price:.5f}, Entry/Close {entry_price:.5f} ✨")
                # Market entry at next open for better fills
                self.buy(size=size, sl=sl_price, tp=tp_price)
                self.entry_bar = len(self.data)
                self.highest_since_entry = entry_price  # Initialize trail high
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