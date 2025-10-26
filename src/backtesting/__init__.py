"""Backtesting module for replaying and analyzing historical trading strategies.

This module enables complete historical event replay for strategy validation.

Maps to:
  - DESIGN.md User Story 3: Event Replay for Backtesting
  - REQUIREMENTS.md FR-2.3: Backtesting Support
  - TASKS.md T-4.1: Testing Framework

Components:
  - BacktestEngine: Orchestrates historical event replay
  - PerformanceCalculator: Computes trading metrics (Sharpe, Drawdown, Win Rate)
  - BacktestReport: Generates comprehensive analysis reports
"""

from .engine import BacktestEngine
from .calculator import PerformanceCalculator
from .report import BacktestReport

__all__ = [
    "BacktestEngine",
    "PerformanceCalculator",
    "BacktestReport",
]
