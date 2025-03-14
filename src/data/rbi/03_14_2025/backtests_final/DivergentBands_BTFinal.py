```python
# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import talib
from backtesting import Strategy, Backtest

class DivergentBands(Strategy):
    atr_multiplier = 2
    risk_percentage = 0.01
    max_bars_in_trade = 10

    def init(self):
        # 🌙✨ Calculate Bollinger Bands components using TA-Lib
        def bb_upper(close):
            upper, _, _ = talib.BBANDS(close, timeperiod=20, nbdevup=2, nbdevdn=2)
            return upper
        self.upper_band = self.I(bb_upper, self.data.Close)

        def bb_lower(close):
            _, _, lower = talib.BBANDS(close, timeperiod=20, nbdevup=2, nbdevdn=2)
            return lower
        self.lower_band = self.I(bb_lower, self.data.Close)

        # 🌙 Calculate ATR for volatility-based exits
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, 14)

        # 🌙 Volume confirmation using SMA
        self.volume_sma = self.I(talib.SMA, self.data.Volume, 5)

    def next(self):
        # 🌙✨ Avoid repainting and ensure indicator stability
        if len(self.data.Close) < 20 or len(self.volume_sma) < 5:
            return

        # 🌙✨ Entry Logic Core
        if not self.position:
            # 1. Check Bollinger Band divergence (expanding bands)
            spread_increasing = (self.upper_band[-1] - self.lower_band[-1] > 
                                self.upper_band[-2] - self.lower_band[-2] > 
                                self.upper_band[-3] - self.lower_band[-3])

            # 2. Price near lower band (within 1%)
            price_near_lower = self.data.Close[-1] <= self.lower_band[-1] * 1.01

            # 3. Volume confirmation (current < SMA)
            volume_confirmation = self.data.Volume[-1] < self.volume_sma[-1]

            if spread_increasing and price_near_lower and volume_confirmation:
                # 🌙✨ Risk Management Calculations
                entry_price = self.data.Close[-1]
                sl_price = self.lower_band[-1] - (self.atr[-1] * self.atr_multiplier)
                tp_price = self.upper_band[-1]  # Middle band would be (upper+lower)/2

                risk_amount = self.equity * self.risk_percentage
                risk_per_share = entry_price - sl_price
                if risk_per_share <= 0:
                    print("🌙⚠️ Aborting trade: Negative risk detected!")
                    return

                position_size = int(round(risk_amount / risk_per_share))
                if position_size == 0:
                    print("🌙⚠️ Position size zero: Not enough equity!")
                    return

                # 🌙🚀 Execute trade with Moon Dev flair
                self.buy(size=position_size, sl=sl_price, tp=tp_price)
                print(f"🌙✨ ENTRY: {entry_price:.2f} | SL: {sl_price:.2f} | TP: {tp_price:.2f} | SIZE: {position_size} 🚀")

        # 🌙⏰ Time-based exit check
        elif self.position and (len(self.data) - self.position.entry_bar) >= self.max_bars_in_trade:
            self.position.close()
            print(f"🌙⏰ TIME EXIT: Held {self.max_bars_in_trade} bars")

# 🌙✨ Data Preparation Ritual
data_path = "/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv"
data = pd.read_csv(data_path)

# 🌙 Cleanse the data columns
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col])

# 🌙 Align with cosmic energy (proper column naming)
data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
}, inplace=True)

data['datetime'] = pd.to_datetime(data['datetime'])
data.set_index('datetime', inplace=True)

# 🌙✨ Backtest Initialization
bt = Backtest(data, DivergentBands,