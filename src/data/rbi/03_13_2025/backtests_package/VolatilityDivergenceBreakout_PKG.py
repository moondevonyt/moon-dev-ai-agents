# 🌙 MOON DEV BACKTESTING SCRIPT FOR VOLATILITY DIVERGENCE BREAKOUT STRATEGY

# Required imports
import pandas as pd
import numpy as np
import talib
import pandas_ta as ta
from backtesting import Backtest, Strategy
import os

# Data preparation
data_path = "/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv"
data = pd.read_csv(data_path)

# Clean and prepare data
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
}, inplace=True)
data['datetime'] = pd.to_datetime(data['datetime'])
data.set_index('datetime', inplace=True)

class VolatilityDivergenceBreakout(Strategy):
    risk_per_trade = 0.02  # 2% risk per trade
    tp_percent = 0.05      # 5% take profit
    sl_percent = 0.08      # 8% stop loss
    
    def init(self):
        # 🌙 Indicators setup
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14, name='RSI_14')
        self.ma50 = self.I(talib.SMA, self.data.Close, timeperiod=50, name='MA_50')
        self.hv = self.I(lambda close: ta.hv(close=close, length=20), self.data.Close, name='HV_20')
        self.av = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=14, name='AV_14')
        
        print("🌙✨ Strategy Indicators Initialized:")
        print(f"RSI(14), MA(50), HV(20), ATR(14)")

    def next(self):
        if not self.position:
            # 🌟 Current market conditions
            price = self.data.Close[-1]
            ma50 = self.ma50[-1]
            rsi = self.rsi[-1]
            
            # 🚀 Bullish divergence check
            lower_low = self.data.Low[-1] < self.data.Low[-2]
            hv_increase = self.hv[-1] > self.hv[-2]
            av_increase = (self.av[-1][4] - self.av[-2][4]) / self.av[-2][4] > 0
            bullish_div = lower_low and (hv_increase or av_increase)
            
            # 🐻 Bearish divergence check
            higher_high = self.data.High[-1] > self.data.High[-2]
            hv_decrease = self.hv[-1] < self.hv[-2]
            av_decrease = (self.av[-1][4] - self.av[-2][4]) / self.av[-2][4] < 0
            bearish_div = higher_high and (hv_decrease or av_decrease)
            
            # Long entry conditions
            if bullish_div and price > ma50 and rsi <= 30:
                self.enter_long()
            
            # Short entry conditions
            elif bearish_div and price < ma50 and rsi >= 70:
                self.enter_short()

    def enter_long(self):
        entry_price = self.data.Close[-1]
        stop_loss = entry_price * (1 - self.sl_percent)
        take_profit = entry_price * (1 + self.tp_percent)
        
        # 🌙 Position sizing calculation
        risk_amount = self.equity * self.risk_per_trade
        risk_per_share = entry_price - stop_loss
        position_size = int(round(risk_amount / risk_per_share))
        
        # 🚀 Execute buy order
        self.buy(size=position_size, sl=stop_loss, tp=take_profit)
        
        print(f"\n🌙✨🚀 BULLISH ENTRY at {entry_price:.2f}")
        print(f"RSI: {self.rsi[-1]:.2f}, MA50: {self.ma50[-1]:.2f}")
        print(f"Position Size: {position_size} units")
        print(f"Stop Loss: {stop_loss:.2f}, Take Profit: {take_profit:.2f}")

    def enter_short(self):
        entry_price = self.data.Close[-1]
        stop_loss = entry_price * (1 + self.sl_percent)
        take_profit = entry_price * (1 - self.tp_percent)
        
        # 🌙 Position sizing calculation
        risk_amount = self.equity * self.risk_per_trade
        risk_per_share = entry_price - stop_loss
        position_size = int(round(risk_amount / risk_per_share))
        
        # 🚀 Execute sell order
        self.sell(size=position_size, sl=stop_loss, tp=take_profit)
        
        print(f"\n🌙✨🚀 BEARISH ENTRY at {entry_price:.2f}")
        print(f"RSI: {self.rsi[-1]:.2f}, MA50: {self.ma50[-1]:.2f}")
        print(f"Position Size: {position_size} units")
        print(f"Stop Loss: {stop_loss:.2f}, Take Profit: {take_profit:.2f}")

# Run the strategy
backtest = Backtest(
    self,
    data,
    cash=10000,
    initial_capital=10000,
    equity_dividend=False,
    risk_free_rate=0.02,
    commission=None,
    slippage=0.001,
    min_trade_size=1e-6,
    max_drawdown=0.7,
)

backtest.run()