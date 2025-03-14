```python
# 🌙 MOON DEV BACKTESTING SCRIPT FOR VOLATILITY REVERSAL STRATEGY 🌙
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import pandas as pd
import talib

# =====================
# DATA PREPARATION
# =====================
def load_data(file_path):
    # Load and clean data with Moon Dev precision 🌙
    data = pd.read_csv(file_path)
    
    # Clean column names
    data.columns = data.columns.str.strip().str.lower()
    data = data.drop(columns=[col for col in data.columns if 'unnamed' in col])
    
    # Proper column mapping
    data.rename(columns={
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume'
    }, inplace=True)
    
    # Convert and set index
    data['datetime'] = pd.to_datetime(data['datetime'])
    data.set_index('datetime', inplace=True)
    return data

# =====================
# CORE STRATEGY CLASS
# =====================
class VolatilityReversal(Strategy):
    # Strategy parameters ✨
    atr_period = 14
    swing_period = 20
    risk_pct = 0.01  # 1% risk per trade
    atr_multiplier = 1.5  # Volatility threshold
    
    def init(self):
        # Calculate indicators with TA-Lib 🌌
        self.swing_high = self.I(talib.MAX, self.data.High, timeperiod=self.swing_period)
        self.swing_low = self.I(talib.MIN, self.data.Low, timeperiod=self.swing_period)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, self.atr_period)
        self.atr_avg = self.I(talib.SMA, self.atr, 20)  # 20-period ATR average
        self.engulfing = self.I(talib.CDLENGULFING, self.data.Open, self.data.High, self.data.Low, self.data.Close)

    def next(self):
        current_close = self.data.Close[-1]
        current_atr = self.atr[-1]
        avg_atr = self.atr_avg[-1] if len(self.atr_avg) > 0 else current_atr
        
        # 🌙 MOON DEV RISK MANAGEMENT SYSTEM 🌙
        if not self.position:
            # =====================
            # LONG ENTRY CONDITIONS
            # =====================
            if (current_close <= self.swing_low[-1] + current_atr and  # Near support
                self.engulfing[-1] == 100 and  # Bullish engulfing
                current_atr > self.atr_multiplier * avg_atr):  # Volatility filter
                
                # Calculate position size with Moon Dev precision 🌙
                sl = self.swing_low[-1] - 0.5 * current_atr
                risk_per_share = current_close - sl
                if risk_per_share > 0:
                    risk_amount = self.risk_pct * self.equity
                    position_size = int(round(risk_amount / risk_per_share))
                    
                    if position_size > 0:
                        self.buy(size=position_size, sl=sl, tp=current_close + 2*current_atr)
                        print(f"🌙🚀 BULLISH REVERSAL! Size: {position_size} | Entry: {current_close:.2f} | SL: {sl:.2f} | TP: {current_close + 2*current_atr:.2f}")

            # ======================
            # SHORT ENTRY CONDITIONS
            # ======================
            elif (current_close >= self.swing_high[-1] - current_atr and  # Near resistance
                  self.engulfing[-1] == -100 and  # Bearish engulfing
                  current_atr > self.atr_multiplier * avg_atr):
                
                sl = self.swing_high[-1] + 0.5 * current_atr
                risk_per_share = sl - current_close
                if risk_per_share > 0:
                    risk_amount = self.risk_pct * self.equity
                    position_size = int(round(risk_amount / risk_per_share))
                    
                    if position_size > 0:
                        self.sell(size=position_size, sl=sl, tp=current_close - 2*current_atr)
                        print(f"🌙⚡ BEARISH REVERSAL!