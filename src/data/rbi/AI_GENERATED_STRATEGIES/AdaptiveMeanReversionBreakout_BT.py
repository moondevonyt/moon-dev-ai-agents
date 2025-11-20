# -*- coding: utf-8 -*-
# 🌙 AI GENERATED STRATEGY 2: AdaptiveMeanReversionBreakout  
# Performance Optimizer + Data Analyst + Quality Assurance + Portfolio Manager
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

class AdaptiveMeanReversionBreakout(Strategy):
    # Optimizable parameters for high-frequency mean reversion with trend confirmation
    bb_period = 20
    bb_std = 2.0
    rsi_period = 14
    rsi_extreme_low = 25
    rsi_extreme_high = 75
    trend_period = 50
    atr_period = 14
    atr_exit_multiplier = 1.0
    volume_threshold = 1.3
    risk_pct = 0.02
    profit_target_multiplier = 2.0
    
    def init(self):
        # Bollinger Bands for mean reversion
        self.bb_upper, self.bb_middle, self.bb_lower = self.I(
            talib.BBANDS, self.data.Close, timeperiod=self.bb_period, nbdevup=self.bb_std, nbdevdn=self.bb_std
        )
        
        # RSI for oversold/overbought conditions
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=self.rsi_period)
        
        # Trend confirmation
        self.trend_sma = self.I(talib.SMA, self.data.Close, timeperiod=self.trend_period)
        self.ema_fast = self.I(talib.EMA, self.data.Close, timeperiod=12)
        self.ema_slow = self.I(talib.EMA, self.data.Close, timeperiod=26)
        
        # Volatility and volume
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=self.atr_period)
        self.volume_sma = self.I(talib.SMA, self.data.Volume, timeperiod=20)
        
        # MACD for momentum confirmation
        self.macd, self.macd_signal, self.macd_hist = self.I(
            talib.MACD, self.data.Close, fastperiod=12, slowperiod=26, signalperiod=9
        )
        
        # Stochastic for additional mean reversion signals
        self.stoch_k, self.stoch_d = self.I(
            talib.STOCH, self.data.High, self.data.Low, self.data.Close, 
            fastk_period=14, slowk_period=3, slowd_period=3
        )
    
    def next(self):
        if len(self.data) < max(self.bb_period, self.trend_period, 26):
            return
            
        current_price = self.data.Close[-1]
        volume_ratio = self.data.Volume[-1] / self.volume_sma[-1] if self.volume_sma[-1] > 0 else 1
        
        # Trend direction
        trend_up = current_price > self.trend_sma[-1]
        ema_trend_up = self.ema_fast[-1] > self.ema_slow[-1]
        
        if not self.position:
            # Long entry: Oversold bounce with trend confirmation
            if (current_price <= self.bb_lower[-1] and
                self.rsi[-1] <= self.rsi_extreme_low and
                self.stoch_k[-1] <= 20 and
                trend_up and  # Only trade in direction of main trend
                ema_trend_up and  # EMA trend confirmation
                self.macd[-1] > self.macd_signal[-1] and  # MACD bullish
                volume_ratio > self.volume_threshold):
                
                # Calculate position size with risk management
                stop_loss = current_price - (self.atr[-1] * self.atr_exit_multiplier)
                profit_target = current_price + (self.atr[-1] * self.profit_target_multiplier)
                risk_per_share = current_price - stop_loss
                
                if risk_per_share > 0:
                    risk_amount = self.risk_pct * self.equity
                    position_size = min(int(self.equity * 0.95 / current_price),
                                      int(risk_amount / risk_per_share))
                    
                    if position_size > 0:
                        self.buy(size=position_size, sl=stop_loss, tp=profit_target)
            
            # Short entry: Overbought rejection with trend confirmation
            elif (current_price >= self.bb_upper[-1] and
                  self.rsi[-1] >= self.rsi_extreme_high and
                  self.stoch_k[-1] >= 80 and
                  not trend_up and  # Only short in bearish trend
                  not ema_trend_up and  # EMA trend confirmation
                  self.macd[-1] < self.macd_signal[-1] and  # MACD bearish
                  volume_ratio > self.volume_threshold):
                
                stop_loss = current_price + (self.atr[-1] * self.atr_exit_multiplier)
                profit_target = current_price - (self.atr[-1] * self.profit_target_multiplier)
                risk_per_share = stop_loss - current_price
                
                if risk_per_share > 0:
                    risk_amount = self.risk_pct * self.equity
                    position_size = min(int(self.equity * 0.95 / current_price),
                                      int(risk_amount / risk_per_share))
                    
                    if position_size > 0:
                        self.sell(size=position_size, sl=stop_loss, tp=profit_target)
        
        else:
            # Dynamic exit conditions for mean reversion
            if self.position.is_long:
                # Exit long if price reaches middle band or trend changes
                if (current_price >= self.bb_middle[-1] or
                    self.rsi[-1] >= 70 or
                    not ema_trend_up or
                    self.macd[-1] < self.macd_signal[-1]):
                    self.position.close()
            
            elif self.position.is_short:
                # Exit short if price reaches middle band or trend changes
                if (current_price <= self.bb_middle[-1] or
                    self.rsi[-1] <= 30 or
                    ema_trend_up or
                    self.macd[-1] > self.macd_signal[-1]):
                    self.position.close()

# Run backtest with default parameters
bt = Backtest(data, AdaptiveMeanReversionBreakout, cash=1_000_000, exclusive_orders=True)
stats = bt.run()

print("\n" + "="*80)
print("🌙 MOON DEV AI HIVE-MIND STRATEGY RESULTS")
print("Strategy: AdaptiveMeanReversionBreakout (Mean Reversion + Trend Confirmation)")
print("="*80)
print(f"Return [%]: {stats['Return [%]']:.2f}")
print(f"Sharpe Ratio: {stats['Sharpe Ratio']:.2f}")
print(f"Total Trades: {stats['# Trades']}")
print(f"Win Rate [%]: {stats['Win Rate [%]']:.2f}")
print(f"Max Drawdown [%]: {stats['Max. Drawdown [%]']:.2f}")
print("="*80)

# Optimize parameters for better performance
optimization_results = bt.optimize(
    bb_period=range(15, 26, 2),
    bb_std=[1.5, 2.0, 2.5],
    rsi_extreme_low=range(20, 31, 5),
    rsi_extreme_high=range(70, 81, 5),
    trend_period=range(40, 61, 5),
    atr_exit_multiplier=[0.5, 1.0, 1.5, 2.0],
    volume_threshold=[1.1, 1.3, 1.5],
    risk_pct=[0.015, 0.02, 0.025, 0.03],
    profit_target_multiplier=[1.5, 2.0, 2.5, 3.0],
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