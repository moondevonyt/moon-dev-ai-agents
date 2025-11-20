# -*- coding: utf-8 -*-
# 🌙 AI GENERATED STRATEGY 3: VolumeBreakoutConvergence
# Strategy Architect + Technical Analyst + Risk Manager + Data Analyst
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

class VolumeBreakoutConvergence(Strategy):
    # Optimizable parameters for volume-confirmed breakouts
    resistance_period = 20
    support_period = 20
    volume_period = 20
    volume_multiplier = 1.5
    rsi_period = 14
    rsi_neutral_low = 40
    rsi_neutral_high = 60
    atr_period = 14
    atr_stop_multiplier = 1.2
    atr_target_multiplier = 2.5
    breakout_threshold = 0.005  # 0.5% price movement threshold
    risk_pct = 0.018
    convergence_lookback = 5
    
    def init(self):
        # Support and resistance levels
        self.resistance = self.I(talib.MAX, self.data.High, timeperiod=self.resistance_period)
        self.support = self.I(talib.MIN, self.data.Low, timeperiod=self.support_period)
        
        # Volume analysis
        self.volume_sma = self.I(talib.SMA, self.data.Volume, timeperiod=self.volume_period)
        self.volume_ema = self.I(talib.EMA, self.data.Volume, timeperiod=self.volume_period)
        
        # Price action indicators
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=self.rsi_period)
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, timeperiod=self.atr_period)
        
        # Multiple timeframe EMAs for convergence
        self.ema_8 = self.I(talib.EMA, self.data.Close, timeperiod=8)
        self.ema_13 = self.I(talib.EMA, self.data.Close, timeperiod=13)
        self.ema_21 = self.I(talib.EMA, self.data.Close, timeperiod=21)
        self.ema_34 = self.I(talib.EMA, self.data.Close, timeperiod=34)
        
        # Momentum indicators
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        self.cci = self.I(talib.CCI, self.data.High, self.data.Low, self.data.Close, timeperiod=20)
        self.williams_r = self.I(talib.WILLR, self.data.High, self.data.Low, self.data.Close, timeperiod=14)
        
        # MACD for trend confirmation
        self.macd, self.macd_signal, self.macd_hist = self.I(
            talib.MACD, self.data.Close, fastperiod=12, slowperiod=26, signalperiod=9
        )
    
    def ema_convergence(self):
        """Check if EMAs are converging (indicating potential breakout)"""
        if len(self.data) < self.convergence_lookback + 34:
            return False
            
        # Calculate EMA spread (range between highest and lowest EMA)
        current_emas = [self.ema_8[-1], self.ema_13[-1], self.ema_21[-1], self.ema_34[-1]]
        past_emas = [self.ema_8[-self.convergence_lookback], self.ema_13[-self.convergence_lookback], 
                    self.ema_21[-self.convergence_lookback], self.ema_34[-self.convergence_lookback]]
        
        current_spread = max(current_emas) - min(current_emas)
        past_spread = max(past_emas) - min(past_emas)
        
        return current_spread < past_spread  # EMAs are converging
    
    def volume_surge(self):
        """Check for volume surge confirmation"""
        return (self.data.Volume[-1] > self.volume_sma[-1] * self.volume_multiplier and
                self.data.Volume[-1] > self.volume_ema[-1] * self.volume_multiplier)
    
    def next(self):
        if len(self.data) < max(self.resistance_period, self.support_period, 34):
            return
            
        current_price = self.data.Close[-1]
        prev_price = self.data.Close[-2]
        
        # Calculate breakout levels
        resistance_level = self.resistance[-2]  # Previous resistance
        support_level = self.support[-2]  # Previous support
        
        # Breakout detection
        resistance_breakout = (prev_price <= resistance_level and 
                             current_price > resistance_level * (1 + self.breakout_threshold))
        support_breakout = (prev_price >= support_level and 
                          current_price < support_level * (1 - self.breakout_threshold))
        
        if not self.position:
            # Long entry: Resistance breakout with volume and convergence
            if (resistance_breakout and
                self.volume_surge() and
                self.ema_convergence() and
                self.rsi[-1] >= self.rsi_neutral_low and
                self.rsi[-1] <= self.rsi_neutral_high and
                self.adx[-1] > 25 and  # Strong trend
                self.macd[-1] > self.macd_signal[-1] and  # MACD bullish
                self.cci[-1] < 100 and  # Not extremely overbought
                self.williams_r[-1] > -80):  # Not oversold
                
                # Calculate position size
                stop_loss = current_price - (self.atr[-1] * self.atr_stop_multiplier)
                profit_target = current_price + (self.atr[-1] * self.atr_target_multiplier)
                risk_per_share = current_price - stop_loss
                
                if risk_per_share > 0:
                    risk_amount = self.risk_pct * self.equity
                    position_size = min(int(self.equity * 0.95 / current_price),
                                      int(risk_amount / risk_per_share))
                    
                    if position_size > 0:
                        self.buy(size=position_size, sl=stop_loss, tp=profit_target)
            
            # Short entry: Support breakdown with volume and convergence
            elif (support_breakout and
                  self.volume_surge() and
                  self.ema_convergence() and
                  self.rsi[-1] >= self.rsi_neutral_low and
                  self.rsi[-1] <= self.rsi_neutral_high and
                  self.adx[-1] > 25 and  # Strong trend
                  self.macd[-1] < self.macd_signal[-1] and  # MACD bearish
                  self.cci[-1] > -100 and  # Not extremely oversold
                  self.williams_r[-1] < -20):  # Not overbought
                
                stop_loss = current_price + (self.atr[-1] * self.atr_stop_multiplier)
                profit_target = current_price - (self.atr[-1] * self.atr_target_multiplier)
                risk_per_share = stop_loss - current_price
                
                if risk_per_share > 0:
                    risk_amount = self.risk_pct * self.equity
                    position_size = min(int(self.equity * 0.95 / current_price),
                                      int(risk_amount / risk_per_share))
                    
                    if position_size > 0:
                        self.sell(size=position_size, sl=stop_loss, tp=profit_target)
        
        else:
            # Early exit conditions for better trade management
            if self.position.is_long:
                # Exit long if momentum weakens
                if (self.rsi[-1] > 75 or
                    self.adx[-1] < 20 or  # Weak trend
                    self.macd[-1] < self.macd_signal[-1] or
                    self.cci[-1] > 150):  # Extremely overbought
                    self.position.close()
            
            elif self.position.is_short:
                # Exit short if momentum weakens
                if (self.rsi[-1] < 25 or
                    self.adx[-1] < 20 or  # Weak trend
                    self.macd[-1] > self.macd_signal[-1] or
                    self.cci[-1] < -150):  # Extremely oversold
                    self.position.close()

# Run backtest with default parameters
bt = Backtest(data, VolumeBreakoutConvergence, cash=1_000_000, exclusive_orders=True)
stats = bt.run()

print("\n" + "="*80)
print("🌙 MOON DEV AI HIVE-MIND STRATEGY RESULTS")
print("Strategy: VolumeBreakoutConvergence (Breakout + Volume Confirmation)")
print("="*80)
print(f"Return [%]: {stats['Return [%]']:.2f}")
print(f"Sharpe Ratio: {stats['Sharpe Ratio']:.2f}")
print(f"Total Trades: {stats['# Trades']}")
print(f"Win Rate [%]: {stats['Win Rate [%]']:.2f}")
print(f"Max Drawdown [%]: {stats['Max. Drawdown [%]']:.2f}")
print("="*80)

# Optimize parameters for better performance
optimization_results = bt.optimize(
    resistance_period=range(15, 26, 2),
    support_period=range(15, 26, 2),
    volume_multiplier=[1.3, 1.5, 1.8, 2.0],
    rsi_neutral_low=range(35, 46, 5),
    rsi_neutral_high=range(55, 66, 5),
    atr_stop_multiplier=[1.0, 1.2, 1.5, 1.8],
    atr_target_multiplier=[2.0, 2.5, 3.0, 3.5],
    breakout_threshold=[0.003, 0.005, 0.007, 0.01],
    risk_pct=[0.015, 0.018, 0.02, 0.025],
    convergence_lookback=range(3, 8),
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