# -*- coding: utf-8 -*-
# 🌙 AI GENERATED STRATEGY 1: MomentumVolatilityFusion
# Strategy Architect + Technical Analyst + Risk Manager + Backtest Engineer
# Moon Dev AI Hive-Mind Collaborative Development

from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import pandas as pd
import talib
import numpy as np

# Load and preprocess data with adaptive header detection
data = pd.read_csv('/home/user/moon-dev-ai-agents/src/data/rbi/BTC-USD-15m.csv')

# Clean column names and handle various CSV formats
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])

# Format columns for backtesting.py
data.rename(columns={
    'open': 'Open',
    'high': 'High', 
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
}, inplace=True)

# Set datetime index
data['datetime'] = pd.to_datetime(data['datetime'])
data = data.set_index('datetime')

class MomentumVolatilityFusion(Strategy):
    # Optimizable parameters designed for 100+ trades and Sharpe >= 2.0
    rsi_period = 14
    rsi_oversold = 30
    rsi_overbought = 70
    atr_period = 14
    atr_multiplier = 1.5
    volatility_period = 20
    volatility_threshold = 0.02
    momentum_period = 12
    risk_pct = 0.015
    
    def init(self):
        # Technical indicators from successful strategies
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=self.rsi_period)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=self.atr_period)
        self.ema_fast = self.I(talib.EMA, self.data.Close, timeperiod=8)
        self.ema_slow = self.I(talib.EMA, self.data.Close, timeperiod=21)
        self.momentum = self.I(talib.MOM, self.data.Close, timeperiod=self.momentum_period)
        
        # Volatility filter
        self.volatility = self.I(lambda x: talib.STDDEV(x, timeperiod=self.volatility_period) / talib.SMA(x, timeperiod=self.volatility_period), self.data.Close)
        
        # Volume indicators
        self.volume_sma = self.I(talib.SMA, self.data.Volume, timeperiod=20)
        
    def next(self):
        if len(self.data) < max(self.volatility_period, self.momentum_period, 21):
            return
            
        current_price = self.data.Close[-1]
        current_volatility = self.volatility[-1]
        volume_ratio = self.data.Volume[-1] / self.volume_sma[-1] if self.volume_sma[-1] > 0 else 1
        
        if not self.position:
            # Long entry conditions: Momentum + Volatility Filter + Volume Confirmation
            if (self.rsi[-1] < self.rsi_overbought and 
                self.rsi[-1] > self.rsi_oversold and
                self.ema_fast[-1] > self.ema_slow[-1] and
                self.momentum[-1] > 0 and
                current_volatility > self.volatility_threshold and
                volume_ratio > 1.2):
                
                # Dynamic position sizing based on volatility
                volatility_adj = min(2.0, max(0.5, 1.0 / current_volatility))
                adjusted_risk = self.risk_pct * volatility_adj
                
                stop_loss = current_price - (self.atr[-1] * self.atr_multiplier)
                risk_per_share = current_price - stop_loss
                
                if risk_per_share > 0:
                    risk_amount = adjusted_risk * self.equity
                    position_size = min(int(self.equity * 0.95 / current_price), 
                                      int(risk_amount / risk_per_share))
                    
                    if position_size > 0:
                        self.buy(size=position_size, sl=stop_loss)
            
            # Short entry conditions: Bearish momentum with volatility
            elif (self.rsi[-1] > self.rsi_oversold and 
                  self.rsi[-1] < self.rsi_overbought and
                  self.ema_fast[-1] < self.ema_slow[-1] and
                  self.momentum[-1] < 0 and
                  current_volatility > self.volatility_threshold and
                  volume_ratio > 1.2):
                
                volatility_adj = min(2.0, max(0.5, 1.0 / current_volatility))
                adjusted_risk = self.risk_pct * volatility_adj
                
                stop_loss = current_price + (self.atr[-1] * self.atr_multiplier)
                risk_per_share = stop_loss - current_price
                
                if risk_per_share > 0:
                    risk_amount = adjusted_risk * self.equity
                    position_size = min(int(self.equity * 0.95 / current_price),
                                      int(risk_amount / risk_per_share))
                    
                    if position_size > 0:
                        self.sell(size=position_size, sl=stop_loss)
        
        else:
            # Dynamic exit conditions
            if self.position.is_long:
                if (self.rsi[-1] > 75 or 
                    self.ema_fast[-1] < self.ema_slow[-1] or
                    self.momentum[-1] < -50):
                    self.position.close()
            
            elif self.position.is_short:
                if (self.rsi[-1] < 25 or 
                    self.ema_fast[-1] > self.ema_slow[-1] or
                    self.momentum[-1] > 50):
                    self.position.close()

# Run backtest with default parameters
bt = Backtest(data, MomentumVolatilityFusion, cash=1_000_000, exclusive_orders=True)
stats = bt.run()

print("\n" + "="*80)
print("🌙 MOON DEV AI HIVE-MIND STRATEGY RESULTS")
print("Strategy: MomentumVolatilityFusion (Momentum + Volatility Filter)")
print("="*80)
print(f"Return [%]: {stats['Return [%]']:.2f}")
print(f"Sharpe Ratio: {stats['Sharpe Ratio']:.2f}")
print(f"Total Trades: {stats['# Trades']}")
print(f"Win Rate [%]: {stats['Win Rate [%]']:.2f}")
print(f"Max Drawdown [%]: {stats['Max. Drawdown [%]']:.2f}")
print("="*80)

# Optimize parameters for better performance
optimization_results = bt.optimize(
    rsi_period=range(10, 21, 2),
    rsi_oversold=range(25, 36, 5),
    rsi_overbought=range(65, 76, 5),
    atr_multiplier=[1.0, 1.5, 2.0, 2.5],
    volatility_threshold=[0.015, 0.02, 0.025, 0.03],
    momentum_period=range(8, 17, 2),
    risk_pct=[0.01, 0.015, 0.02, 0.025],
    maximize='Sharpe Ratio',
    constraint=lambda p: p['# Trades'] >= 100
)

print("\n" + "="*80)
print("🚀 OPTIMIZED RESULTS (Target: 100+ Trades, Sharpe >= 2.0)")
print("="*80)
print(f"Return [%]: {optimization_results['Return [%]']:.2f}")
print(f"Sharpe Ratio: {optimization_results['Sharpe Ratio']:.2f}")
print(f"Total Trades: {optimization_results['# Trades']}")
print(f"Win Rate [%]: {optimization_results['Win Rate [%]']:.2f}")
print(f"Max Drawdown [%]: {optimization_results['Max. Drawdown [%]']:.2f}")
print(f"Best Parameters: {optimization_results._strategy}")
print("="*80)
print("🌙 Moon Dev AI Hive-Mind - Strategy Complete")
print("="*80)