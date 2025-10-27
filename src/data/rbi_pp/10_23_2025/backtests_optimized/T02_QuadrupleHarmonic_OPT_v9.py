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
        self.entry_price = None  # 🌙 Track entry price for potential trailing stops

    def next(self):
        current_close = self.data.Close[-1]
        current_open = self.data.Open[-1]
        current_low = self.data.Low[-1]
        current_high = self.data.High[-1]
        
        # Debug print for trend context 🌙
        if len(self.data) % 100 == 0:
            print(f"🌙 Moon Dev Debug: Current Close {current_close:.2f}, EMA {self.ema[-1]:.2f}, ADX {self.adx[-1]:.2f} ✨")
        
        # 🌙 Improved exit logic: Removed early close below EMA to let winners run in uptrend; rely on SL/TP for protection
        # Time-based exit extended to 20 bars for more room in volatile markets 🌙
        if self.position:
            if self.entry_bar and len(self.data) - self.entry_bar > 20:
                self.position.close()
                print(f"🌙 Moon Dev Exit: Time-based close after 20 bars at {current_close:.2f} ✨")
            # 🌙 Simple breakeven trailing: If unrealized profit > 1x initial risk, move SL to entry (reduces risk on winners)
            if (self.entry_price and current_close > self.entry_price and
                not hasattr(self.position, '_sl_moved') or not self.position._sl_moved):
                initial_risk = self.entry_price - self.position.sl  # Approximate initial SL
                if current_close >= self.entry_price + initial_risk:
                    self.position.sl = self.entry_price
                    self.position._sl_moved = True  # Flag to move only once
                    print(f"🌙 Moon Dev Trailing: SL moved to breakeven at {self.entry_price:.2f} 🚀")
            return
        
        # Entry logic only if no position
        if self.position or len(self.data) < 200:  # 🌙 Increased from 21 to 200 for EMA200 maturity
            return
        
        # Calculate bullish candle strength 🌙 - Tightened to >60% body for stronger reversal signals
        body = current_close - current_open
        candle_range = current_high - current_low
        strong_bullish = body > 0.6 * candle_range and body > 0  # 🌙 Tightened entry: require stronger bullish candle body > 60% of range
        
        # 🌙 Added pre-pullback trend filter: Ensure the bar before the 4 downs was in uptrend (above EMA) for true pullback setups
        pre_pullback_above_ema = self.data.Close[-5] > self.ema[-1]
        
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
            pre_pullback_above_ema and  # 🌙 New: Confirms pullback from established uptrend
            self.adx[-1] > 25 and  # 🌙 Increased ADX threshold from 20 to 25 for stronger trend quality
            self.rsi[-1] < 35 and  # 🌙 Tightened RSI oversold filter to <35 for deeper, higher-quality pullbacks
            self.data.Volume[-1] > 2.0 * self.vol_sma[-1]):  # 🌙 Increased volume filter to 2x SMA for higher conviction entries
            
            print(f"🌙 Moon Dev Signal: 4 down bars pullback in uptrend, strong bullish confirmation at {current_close:.2f} 🚀")
            
            # Pattern details - improved min_low calculation 🌙
            pattern_lows = self.data.Low[-5:-1]  # Lows of the 4 down bars
            min_low = min(pattern_lows)
            
            # SL: below pattern low by 1 ATR (kept conservative for risk management)
            atr_val = self.atr[-1]
            sl_price = min_low - 1.0 * atr_val
            
            # Entry at current close (approximate)
            entry_price = current_close
            
            # 🌙 Improved TP: Increased to 1:3 Risk-Reward ratio for higher average returns on winners
            stop_distance = entry_price - sl_price
            if stop_distance <= 0:
                print(f"🌙 Moon Dev Skip: Zero or negative stop distance 😔")
                return
            tp_price = entry_price + 3 * stop_distance
            
            # Risk management: Increased to 2% risk for amplified returns while maintaining control 🌙
            risk_pct = 0.02
            size_frac = risk_pct / (stop_distance / entry_price)  # 🌙 Corrected position sizing formula: risk / (stop_distance %)
            size = min(size_frac, 0.5)  # Cap at 50% exposure for risk management in volatile BTC
            
            if size > 0:
                # Debug print before order 🌙
                print(f"🌙 Moon Dev Debug: Order params - Size {size:.4f}, SL {sl_price:.5f}, TP {tp_price:.5f}, Entry/Close {entry_price:.5f} ✨")
                # Removed limit=entry_price for market entry at next open (improves fill rate in gappy crypto) 🌙
                self.buy(size=size, sl=sl_price, tp=tp_price)
                self.entry_bar = len(self.data)
                self.entry_price = entry_price  # 🌙 Set for trailing logic
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