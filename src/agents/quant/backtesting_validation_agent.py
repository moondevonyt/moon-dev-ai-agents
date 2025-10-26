"""
🌙 Moon Dev's Backtesting Validation Agent
Validates trading strategies using statistical backtesting

Implements rigorous validation:
- Walk-forward analysis with 12 rolling windows
- Statistical significance testing (p-value < 0.05)
- Performance metrics validation (Sharpe, drawdown, win rate)
- Strategy approval/rejection based on criteria
"""

import asyncio
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from termcolor import cprint

from src.agents.quant.base_quant_agent import BaseQuantAgent
from src.agents.quant.statistical_utils import (
    ttest_significance,
    calculate_sharpe_ratio,
    calculate_max_drawdown,
    calculate_win_rate,
    calculate_profit_factor,
    bonferroni_correction
)
from src.backtesting.engine import BacktestEngine
from src.core.models import Event, EventType
from src.config import (
    BACKTEST_MIN_YEARS,
    BACKTEST_P_VALUE_THRESHOLD,
    BACKTEST_MIN_SHARPE_RATIO,
    BACKTEST_MAX_DRAWDOWN_PCT,
    BACKTEST_MIN_WIN_RATE_PCT,
    BACKTEST_WALK_FORWARD_WINDOWS
)


@dataclass
class ValidationCriteria:
    """Strategy validation criteria."""
    min_sharpe_ratio: float = BACKTEST_MIN_SHARPE_RATIO
    max_drawdown_pct: float = BACKTEST_MAX_DRAWDOWN_PCT
    min_win_rate_pct: float = BACKTEST_MIN_WIN_RATE_PCT
    max_p_value: float = BACKTEST_P_VALUE_THRESHOLD
    min_years: int = BACKTEST_MIN_YEARS



class BacktestingValidationAgent(BaseQuantAgent):
    """Validates strategies with rigorous backtesting."""
    
    def __init__(self):
        super().__init__(
            agent_type="backtesting_validation",
            subscribed_topics=["strategy.submitted"]
        )
        
        # Backtest engine (will be initialized with event_store)
        self.backtest_engine = None
        
        # Validation criteria
        self.criteria = ValidationCriteria()
        
        # Validation history (strategy_id -> results)
        self.validation_history: Dict[str, List[Dict]] = {}
        
        cprint("✅ Backtesting Validation Agent initialized", "green")
    
    async def initialize(self):
        """Initialize agent and backtest engine."""
        await super().initialize()
        
        # Initialize backtest engine
        from src.core.event_store import EventStore
        event_store = EventStore()
        await event_store.connect()
        
        self.backtest_engine = BacktestEngine(
            event_store=event_store,
            cache_layer=self.cache
        )
        
        cprint("✅ Backtest engine initialized", "green")

    
    async def handle_strategy_submitted(self, event: Event):
        """Handle strategy submission for validation."""
        strategy_id = event.data.get('strategy_id')
        strategy_config = event.data.get('config', {})
        
        if not strategy_id:
            cprint("⚠️ Strategy submission missing strategy_id", "yellow")
            return
        
        cprint(f"📊 Validating strategy: {strategy_id}", "cyan")
        
        try:
            # Run walk-forward analysis
            validation_results = await self.run_walk_forward_validation(
                strategy_id=strategy_id,
                strategy_config=strategy_config
            )
            
            # Check validation criteria
            is_valid, rejection_reasons = self._check_validation_criteria(validation_results)
            
            if is_valid:
                # Strategy passed validation
                await self.emit_event(
                    event_type=EventType.STRATEGY_VALIDATED,
                    token=None,
                    data={
                        "strategy_id": strategy_id,
                        "validation_results": validation_results,
                        "criteria_met": True,
                        "timestamp": datetime.utcnow().isoformat()
                    },
                    correlation_id=event.correlation_id
                )
                cprint(f"✅ Strategy {strategy_id} VALIDATED", "green")
            else:
                # Strategy failed validation
                await self.emit_event(
                    event_type=EventType.STRATEGY_REJECTED,
                    token=None,
                    data={
                        "strategy_id": strategy_id,
                        "validation_results": validation_results,
                        "rejection_reasons": rejection_reasons,
                        "criteria_met": False,
                        "timestamp": datetime.utcnow().isoformat()
                    },
                    correlation_id=event.correlation_id
                )
                cprint(f"❌ Strategy {strategy_id} REJECTED: {', '.join(rejection_reasons)}", "red")
            
            # Store validation history
            if strategy_id not in self.validation_history:
                self.validation_history[strategy_id] = []
            self.validation_history[strategy_id].append({
                "timestamp": datetime.utcnow(),
                "is_valid": is_valid,
                "results": validation_results,
                "rejection_reasons": rejection_reasons if not is_valid else []
            })
            
        except Exception as e:
            cprint(f"❌ Error validating strategy {strategy_id}: {str(e)}", "red")
            await self.emit_event(
                event_type=EventType.STRATEGY_REJECTED,
                token=None,
                data={
                    "strategy_id": strategy_id,
                    "error": str(e),
                    "rejection_reasons": [f"Validation error: {str(e)}"]
                }
            )

    
    async def run_walk_forward_validation(
        self,
        strategy_id: str,
        strategy_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run walk-forward analysis with rolling windows.
        
        Args:
            strategy_id: Strategy identifier
            strategy_config: Strategy configuration
            
        Returns:
            Dict with validation results
        """
        cprint(f"🔄 Running walk-forward analysis for {strategy_id}...", "cyan")
        
        # Calculate date ranges for walk-forward windows
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=365 * self.criteria.min_years)
        
        # Split into rolling windows
        window_results = []
        total_days = (end_date - start_date).days
        window_size_days = total_days // BACKTEST_WALK_FORWARD_WINDOWS
        
        for i in range(BACKTEST_WALK_FORWARD_WINDOWS):
            window_start = start_date + timedelta(days=i * window_size_days)
            window_end = window_start + timedelta(days=window_size_days)
            
            if window_end > end_date:
                window_end = end_date
            
            cprint(f"  Window {i+1}/{BACKTEST_WALK_FORWARD_WINDOWS}: {window_start.date()} to {window_end.date()}", "cyan")
            
            try:
                # Run backtest for this window
                backtest_results = await self.backtest_engine.run_backtest(
                    start_date=window_start,
                    end_date=window_end,
                    initial_balance=50000.0,
                    tokens=strategy_config.get('tokens'),
                    agents=strategy_config.get('agents')
                )
                
                # Calculate metrics for this window
                metrics = backtest_results.get_metrics()
                
                window_results.append({
                    "window": i + 1,
                    "start_date": window_start.isoformat(),
                    "end_date": window_end.isoformat(),
                    "metrics": metrics,
                    "trade_count": len(backtest_results.trades)
                })
                
            except Exception as e:
                cprint(f"  ⚠️ Window {i+1} failed: {str(e)}", "yellow")
                window_results.append({
                    "window": i + 1,
                    "error": str(e)
                })
        
        # Aggregate results across all windows
        aggregated_results = self._aggregate_window_results(window_results)
        
        # Perform statistical significance testing
        statistical_results = self._perform_statistical_tests(window_results)
        
        return {
            "strategy_id": strategy_id,
            "validation_date": datetime.utcnow().isoformat(),
            "window_count": BACKTEST_WALK_FORWARD_WINDOWS,
            "window_results": window_results,
            "aggregated_metrics": aggregated_results,
            "statistical_tests": statistical_results
        }

    
    def _aggregate_window_results(self, window_results: List[Dict]) -> Dict[str, float]:
        """Aggregate metrics across all windows."""
        # Extract metrics from successful windows
        all_sharpe = []
        all_drawdown = []
        all_win_rate = []
        all_returns = []
        
        for window in window_results:
            if 'error' not in window and 'metrics' in window:
                metrics = window['metrics']
                all_sharpe.append(metrics.get('sharpe_ratio', 0))
                all_drawdown.append(metrics.get('max_drawdown_pct', 0))
                all_win_rate.append(metrics.get('win_rate_pct', 0))
                all_returns.append(metrics.get('total_return_pct', 0))
        
        if not all_sharpe:
            return {
                "avg_sharpe_ratio": 0,
                "avg_max_drawdown_pct": 0,
                "avg_win_rate_pct": 0,
                "avg_return_pct": 0,
                "successful_windows": 0
            }
        
        return {
            "avg_sharpe_ratio": float(np.mean(all_sharpe)),
            "std_sharpe_ratio": float(np.std(all_sharpe)),
            "avg_max_drawdown_pct": float(np.mean(all_drawdown)),
            "avg_win_rate_pct": float(np.mean(all_win_rate)),
            "avg_return_pct": float(np.mean(all_returns)),
            "successful_windows": len(all_sharpe),
            "failed_windows": len(window_results) - len(all_sharpe)
        }
    
    def _perform_statistical_tests(self, window_results: List[Dict]) -> Dict[str, Any]:
        """Perform statistical significance tests on results."""
        # Extract returns from all windows
        all_returns = []
        
        for window in window_results:
            if 'error' not in window and 'metrics' in window:
                returns = window['metrics'].get('total_return_pct', 0)
                all_returns.append(returns)
        
        if len(all_returns) < 2:
            return {
                "t_statistic": 0,
                "p_value": 1.0,
                "is_significant": False,
                "note": "Insufficient data for statistical testing"
            }
        
        # Perform t-test (null hypothesis: mean return = 0)
        t_stat, p_value = ttest_significance(all_returns, null_hypothesis=0.0)
        
        # Apply Bonferroni correction for multiple testing
        corrected_alpha = BACKTEST_P_VALUE_THRESHOLD / len(all_returns)
        is_significant = p_value < corrected_alpha
        
        return {
            "t_statistic": float(t_stat),
            "p_value": float(p_value),
            "corrected_alpha": float(corrected_alpha),
            "is_significant": is_significant,
            "sample_size": len(all_returns),
            "mean_return": float(np.mean(all_returns)),
            "std_return": float(np.std(all_returns))
        }
    
    def _check_validation_criteria(
        self,
        validation_results: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Check if validation results meet criteria.
        
        Args:
            validation_results: Results from walk-forward validation
            
        Returns:
            Tuple of (is_valid, rejection_reasons)
        """
        rejection_reasons = []
        
        # Get aggregated metrics
        metrics = validation_results.get('aggregated_metrics', {})
        statistical = validation_results.get('statistical_tests', {})
        
        # Check statistical significance
        if not statistical.get('is_significant', False):
            rejection_reasons.append(
                f"Not statistically significant (p-value: {statistical.get('p_value', 1.0):.4f})"
            )
        
        # Check Sharpe ratio
        avg_sharpe = metrics.get('avg_sharpe_ratio', 0)
        if avg_sharpe < self.criteria.min_sharpe_ratio:
            rejection_reasons.append(
                f"Sharpe ratio too low ({avg_sharpe:.2f} < {self.criteria.min_sharpe_ratio})"
            )
        
        # Check max drawdown
        avg_drawdown = metrics.get('avg_max_drawdown_pct', 100)
        if avg_drawdown > self.criteria.max_drawdown_pct:
            rejection_reasons.append(
                f"Max drawdown too high ({avg_drawdown:.2f}% > {self.criteria.max_drawdown_pct}%)"
            )
        
        # Check win rate
        avg_win_rate = metrics.get('avg_win_rate_pct', 0)
        if avg_win_rate < self.criteria.min_win_rate_pct:
            rejection_reasons.append(
                f"Win rate too low ({avg_win_rate:.2f}% < {self.criteria.min_win_rate_pct}%)"
            )
        
        # Check if enough windows succeeded
        successful_windows = metrics.get('successful_windows', 0)
        if successful_windows < BACKTEST_WALK_FORWARD_WINDOWS * 0.75:  # At least 75% must succeed
            rejection_reasons.append(
                f"Too many failed windows ({successful_windows}/{BACKTEST_WALK_FORWARD_WINDOWS})"
            )
        
        is_valid = len(rejection_reasons) == 0
        return is_valid, rejection_reasons
    
    async def run_event_loop(self):
        """Register event handlers and run loop."""
        self._event_handlers[EventType.STRATEGY_SUBMITTED] = self.handle_strategy_submitted
        await super().run_event_loop()


if __name__ == "__main__":
    agent = BacktestingValidationAgent()
    agent.run()

    
    def _check_validation_criteria(
        self,
        validation_results: Dict[str, Any]
    ) -> tuple[bool, List[str]]:
        """
        Check if strategy meets validation criteria.
        
        Args:
            validation_results: Results from walk-forward validation
            
        Returns:
            Tuple of (is_valid, rejection_reasons)
        """
        rejection_reasons = []
        
        aggregated = validation_results.get('aggregated_metrics', {})
        statistical = validation_results.get('statistical_tests', {})
        
        # Check statistical significance
        if not statistical.get('is_significant', False):
            p_value = statistical.get('p_value', 1.0)
            rejection_reasons.append(
                f"Not statistically significant (p-value={p_value:.4f} >= {BACKTEST_P_VALUE_THRESHOLD})"
            )
        
        # Check Sharpe ratio
        avg_sharpe = aggregated.get('avg_sharpe_ratio', 0)
        if avg_sharpe < self.criteria.min_sharpe_ratio:
            rejection_reasons.append(
                f"Sharpe ratio too low ({avg_sharpe:.2f} < {self.criteria.min_sharpe_ratio})"
            )
        
        # Check max drawdown
        avg_drawdown = aggregated.get('avg_max_drawdown_pct', 100)
        if avg_drawdown > self.criteria.max_drawdown_pct:
            rejection_reasons.append(
                f"Max drawdown too high ({avg_drawdown:.1f}% > {self.criteria.max_drawdown_pct}%)"
            )
        
        # Check win rate
        avg_win_rate = aggregated.get('avg_win_rate_pct', 0)
        if avg_win_rate < self.criteria.min_win_rate_pct:
            rejection_reasons.append(
                f"Win rate too low ({avg_win_rate:.1f}% < {self.criteria.min_win_rate_pct}%)"
            )
        
        # Check successful windows
        successful_windows = aggregated.get('successful_windows', 0)
        if successful_windows < BACKTEST_WALK_FORWARD_WINDOWS * 0.8:  # At least 80% success
            rejection_reasons.append(
                f"Too many failed windows ({successful_windows}/{BACKTEST_WALK_FORWARD_WINDOWS})"
            )
        
        is_valid = len(rejection_reasons) == 0
        
        return is_valid, rejection_reasons
    
    async def run_event_loop(self):
        """Override to register event handlers."""
        self._event_handlers[EventType.STRATEGY_SUBMITTED] = self.handle_strategy_submitted
        await super().run_event_loop()


if __name__ == "__main__":
    agent = BacktestingValidationAgent()
    agent.run()
