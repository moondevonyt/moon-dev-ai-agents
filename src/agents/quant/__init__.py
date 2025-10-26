"""
🌙 Moon Dev's Quantitative Trading Agents
Jim Simons-style statistical trading system

This module contains quantitative agents that implement Renaissance Technologies'
core principles: data-first analysis, weak signal aggregation, statistical
significance testing, and pattern detection without causal reasoning.
"""

from .base_quant_agent import BaseQuantAgent
from .anomaly_detection_agent import AnomalyDetectionAgent
from .signal_aggregation_agent import SignalAggregationAgent
from .transaction_cost_agent import TransactionCostAgent
from .backtesting_validation_agent import BacktestingValidationAgent
from .capacity_monitoring_agent import CapacityMonitoringAgent
from .signal_decay_agent import SignalDecayAgent
from .regime_detection_agent import RegimeDetectionAgent
from .correlation_matrix_agent import CorrelationMatrixAgent
from .portfolio_optimization_agent import PortfolioOptimizationAgent
from .alternative_data_agent import AlternativeDataAgent

__all__ = [
    'BaseQuantAgent',
    'AnomalyDetectionAgent',
    'SignalAggregationAgent',
    'TransactionCostAgent',
    'BacktestingValidationAgent',
    'CapacityMonitoringAgent',
    'SignalDecayAgent',
    'RegimeDetectionAgent',
    'CorrelationMatrixAgent',
    'PortfolioOptimizationAgent',
    'AlternativeDataAgent',
]
