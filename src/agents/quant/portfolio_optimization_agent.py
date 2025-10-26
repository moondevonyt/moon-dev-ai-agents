"""
🌙 Moon Dev's Portfolio Optimization Agent
Optimizes portfolio allocation using MPT, Kelly, and Risk Parity

Implements portfolio optimization:
- Modern Portfolio Theory (MPT) optimization
- Kelly Criterion position sizing
- Risk parity allocation
- Correlation-based diversification
"""

import asyncio
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from termcolor import cprint
from scipy.optimize import minimize

from src.agents.quant.base_quant_agent import BaseQuantAgent
from src.core.models import Event, EventType
from src.config import (
    PORTFOLIO_MAX_POSITION_PCT,
    PORTFOLIO_KELLY_FRACTION,
    PORTFOLIO_REBALANCE_FREQUENCY_HOURS,
    PORTFOLIO_MIN_EXPECTED_RETURN,
    PORTFOLIO_RISK_PARITY_ENABLED,
    CORRELATION_DIVERSIFICATION_THRESHOLD
)


@dataclass
class PortfolioAllocation:
    """Portfolio allocation data."""
    token: str
    target_weight: float
    current_weight: float
    expected_return: float
    volatility: float
    allocation_method: str


class PortfolioOptimizationAgent(BaseQuantAgent):
    """Optimizes portfolio allocation."""
    
    def __init__(self):
        super().__init__(
            agent_type="portfolio_optimization",
            subscribed_topics=["signal.aggregated", "strategy.capacity", "signal.correlation"]
        )
        
        # Current portfolio state
        self.current_portfolio: Dict[str, float] = {}  # token -> weight
        
        # Signal data for optimization
        self.signals: Dict[str, Dict] = {}  # token -> signal_data
        
        # Correlation matrix
        self.correlation_matrix: Dict[str, float] = {}  # pair_key -> correlation
        
        # Capacity constraints
        self.capacity_constraints: Dict[str, float] = {}  # token -> max_allocation
        
        cprint("✅ Portfolio Optimization Agent initialized", "green")
    
    async def initialize(self):
        """Initialize agent and start rebalancing task."""
        await super().initialize()
        
        # Start periodic rebalancing
        asyncio.create_task(self._rebalancing_loop())
    
    async def handle_signal_aggregated(self, event: Event):
        """Store signal for portfolio optimization."""
        token = event.token
        if not token:
            return
        
        self.signals[token] = {
            'direction': event.data.get('direction'),
            'confidence': event.data.get('confidence', 0.5),
            'consensus_score': event.data.get('consensus_score', 0),
            'timestamp': event.timestamp
        }
    
    async def handle_capacity_warning(self, event: Event):
        """Update capacity constraints."""
        strategy_id = event.data.get('strategy_id')
        estimated_capacity = event.data.get('estimated_capacity', 0)
        
        if strategy_id:
            self.capacity_constraints[strategy_id] = estimated_capacity
    
    async def handle_correlation_event(self, event: Event):
        """Update correlation matrix."""
        token1 = event.data.get('token_1')
        token2 = event.data.get('token_2')
        correlation = event.data.get('current_correlation', 0)
        
        if token1 and token2:
            pair_key = f"{min(token1, token2)}_{max(token1, token2)}"
            self.correlation_matrix[pair_key] = correlation
    
    async def _rebalancing_loop(self):
        """Periodic portfolio rebalancing."""
        while self.is_running:
            await asyncio.sleep(3600 * PORTFOLIO_REBALANCE_FREQUENCY_HOURS)
            
            cprint("🔄 Running portfolio optimization...", "cyan")
            
            await self._optimize_portfolio()
    
    async def _optimize_portfolio(self):
        """Optimize portfolio allocation."""
        if not self.signals:
            return
        
        # Get tokens with signals
        tokens = list(self.signals.keys())
        
        if len(tokens) == 0:
            return
        
        # Calculate expected returns and volatilities
        expected_returns = []
        volatilities = []
        
        for token in tokens:
            signal = self.signals[token]
            # Use consensus score as proxy for expected return
            expected_return = signal['consensus_score'] / 100
            expected_returns.append(expected_return)
            
            # Estimate volatility (simplified - should use historical data)
            volatility = 0.3  # Default 30% annualized
            volatilities.append(volatility)
        
        expected_returns = np.array(expected_returns)
        volatilities = np.array(volatilities)
        
        # Build covariance matrix
        cov_matrix = self._build_covariance_matrix(tokens, volatilities)
        
        # Optimize using different methods
        if PORTFOLIO_RISK_PARITY_ENABLED:
            weights = self._optimize_risk_parity(cov_matrix)
        else:
            weights = self._optimize_mpt(expected_returns, cov_matrix)
        
        # Apply Kelly Criterion sizing
        weights = self._apply_kelly_criterion(weights, expected_returns, tokens)
        
        # Apply diversification constraints
        weights = self._apply_diversification_constraints(weights, tokens)
        
        # Apply capacity constraints
        weights = self._apply_capacity_constraints(weights, tokens)
        
        # Normalize weights
        weights = weights / np.sum(weights)
        
        # Generate rebalancing trades
        await self._generate_rebalancing_trades(tokens, weights)
    
    def _build_covariance_matrix(self, tokens: List[str], volatilities: np.ndarray) -> np.ndarray:
        """Build covariance matrix from correlations and volatilities."""
        n = len(tokens)
        cov_matrix = np.zeros((n, n))
        
        for i in range(n):
            for j in range(n):
                if i == j:
                    cov_matrix[i, j] = volatilities[i] ** 2
                else:
                    pair_key = f"{min(tokens[i], tokens[j])}_{max(tokens[i], tokens[j])}"
                    corr = self.correlation_matrix.get(pair_key, 0.5)  # Default 0.5
                    cov_matrix[i, j] = corr * volatilities[i] * volatilities[j]
        
        return cov_matrix
    
    def _optimize_mpt(self, expected_returns: np.ndarray, cov_matrix: np.ndarray) -> np.ndarray:
        """Optimize using Modern Portfolio Theory."""
        n = len(expected_returns)
        
        # Objective: minimize variance
        def objective(weights):
            return weights.T @ cov_matrix @ weights
        
        # Constraints
        constraints = [
            {'type': 'eq', 'fun': lambda w: np.sum(w) - 1},  # Weights sum to 1
            {'type': 'ineq', 'fun': lambda w: w.T @ expected_returns - PORTFOLIO_MIN_EXPECTED_RETURN}  # Min return
        ]
        
        # Bounds
        bounds = [(0, PORTFOLIO_MAX_POSITION_PCT / 100) for _ in range(n)]
        
        # Initial guess
        x0 = np.ones(n) / n
        
        # Optimize
        result = minimize(objective, x0, method='SLSQP', bounds=bounds, constraints=constraints)
        
        return result.x if result.success else x0
    
    def _optimize_risk_parity(self, cov_matrix: np.ndarray) -> np.ndarray:
        """Optimize using risk parity."""
        n = cov_matrix.shape[0]
        
        # Objective: minimize variance of risk contributions
        def objective(weights):
            portfolio_vol = np.sqrt(weights.T @ cov_matrix @ weights)
            marginal_risk = (cov_matrix @ weights) / portfolio_vol
            risk_contrib = weights * marginal_risk
            return np.var(risk_contrib)
        
        # Constraints
        constraints = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1}]
        
        # Bounds
        bounds = [(0, PORTFOLIO_MAX_POSITION_PCT / 100) for _ in range(n)]
        
        # Initial guess
        x0 = np.ones(n) / n
        
        # Optimize
        result = minimize(objective, x0, method='SLSQP', bounds=bounds, constraints=constraints)
        
        return result.x if result.success else x0
    
    def _apply_kelly_criterion(self, weights: np.ndarray, expected_returns: np.ndarray, tokens: List[str]) -> np.ndarray:
        """Apply Kelly Criterion position sizing."""
        kelly_weights = np.zeros_like(weights)
        
        for i, token in enumerate(tokens):
            signal = self.signals.get(token, {})
            win_rate = signal.get('win_rate', 0.5)
            avg_win = signal.get('avg_win', 0.02)
            avg_loss = signal.get('avg_loss', 0.01)
            
            if avg_loss == 0:
                kelly_fraction = 0
            else:
                # Kelly formula: f = (p * b - q) / b
                b = avg_win / avg_loss
                p = win_rate
                q = 1 - p
                kelly_fraction = (p * b - q) / b
            
            # Apply fractional Kelly
            kelly_weights[i] = max(0, kelly_fraction * PORTFOLIO_KELLY_FRACTION)
        
        # Blend with original weights
        blended_weights = 0.5 * weights + 0.5 * kelly_weights
        
        return blended_weights
    
    def _apply_diversification_constraints(self, weights: np.ndarray, tokens: List[str]) -> np.ndarray:
        """Filter out highly correlated positions."""
        adjusted_weights = weights.copy()
        
        for i, token1 in enumerate(tokens):
            for j, token2 in enumerate(tokens):
                if i >= j:
                    continue
                
                pair_key = f"{min(token1, token2)}_{max(token1, token2)}"
                corr = self.correlation_matrix.get(pair_key, 0)
                
                # If correlation too high, reduce weight of smaller position
                if abs(corr) > CORRELATION_DIVERSIFICATION_THRESHOLD:
                    if weights[i] < weights[j]:
                        adjusted_weights[i] *= 0.5
                    else:
                        adjusted_weights[j] *= 0.5
        
        return adjusted_weights
    
    def _apply_capacity_constraints(self, weights: np.ndarray, tokens: List[str]) -> np.ndarray:
        """Apply capacity constraints."""
        adjusted_weights = weights.copy()
        
        for i, token in enumerate(tokens):
            if token in self.capacity_constraints:
                max_allocation = self.capacity_constraints[token]
                # Reduce weight if exceeds capacity
                if weights[i] > max_allocation:
                    adjusted_weights[i] = max_allocation
        
        return adjusted_weights
    
    async def _generate_rebalancing_trades(self, tokens: List[str], target_weights: np.ndarray):
        """Generate rebalancing trades."""
        allocations = []
        
        for i, token in enumerate(tokens):
            current_weight = self.current_portfolio.get(token, 0)
            target_weight = target_weights[i]
            
            allocation = PortfolioAllocation(
                token=token,
                target_weight=float(target_weight),
                current_weight=float(current_weight),
                expected_return=0.0,
                volatility=0.0,
                allocation_method="mpt" if not PORTFOLIO_RISK_PARITY_ENABLED else "risk_parity"
            )
            
            allocations.append(allocation)
        
        # Emit rebalancing event
        await self.emit_event(
            event_type=EventType.PORTFOLIO_REBALANCE,
            token=None,
            data={
                "allocations": [
                    {
                        "token": a.token,
                        "target_weight": a.target_weight,
                        "current_weight": a.current_weight,
                        "rebalance_amount": a.target_weight - a.current_weight
                    }
                    for a in allocations
                ],
                "optimization_method": "risk_parity" if PORTFOLIO_RISK_PARITY_ENABLED else "mpt",
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        cprint(f"📊 Portfolio rebalanced: {len(allocations)} positions", "green")
    
    async def run_event_loop(self):
        """Override to register event handlers."""
        self._event_handlers[EventType.SIGNAL_AGGREGATED] = self.handle_signal_aggregated
        self._event_handlers[EventType.STRATEGY_CAPACITY_WARNING] = self.handle_capacity_warning
        self._event_handlers[EventType.SIGNAL_CORRELATION] = self.handle_correlation_event
        await super().run_event_loop()


if __name__ == "__main__":
    agent = PortfolioOptimizationAgent()
    agent.run()
