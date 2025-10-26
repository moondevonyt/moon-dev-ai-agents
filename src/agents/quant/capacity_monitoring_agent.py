"""
🌙 Moon Dev's Capacity Monitoring Agent
Monitors strategy capacity and prevents performance degradation

Implements capacity tracking:
- Slippage tracking vs position size
- Market impact modeling (square-root model)
- Capacity estimation
- Automatic position reduction when capacity exceeded
"""

import asyncio
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from termcolor import cprint
from scipy.optimize import curve_fit

from src.agents.quant.base_quant_agent import BaseQuantAgent
from src.core.models import Event, EventType
from src.config import (
    CAPACITY_SLIPPAGE_THRESHOLD_PCT,
    CAPACITY_WARNING_UTILIZATION_PCT,
    CAPACITY_EXCEEDED_UTILIZATION_PCT,
    CAPACITY_POSITION_REDUCTION_PCT,
    CAPACITY_CALIBRATION_DAYS,
    CAPACITY_UPDATE_FREQUENCY_DAYS
)


@dataclass
class CapacityMetrics:
    """Capacity metrics for a strategy."""
    strategy_id: str
    slippage_history: List[Dict] = field(default_factory=list)
    estimated_capacity: float = 0.0
    current_allocation: float = 0.0
    market_impact_coefficient: float = 0.01
    last_calibration: Optional[datetime] = None
    last_warning: Optional[datetime] = None


class CapacityMonitoringAgent(BaseQuantAgent):
    """Monitors strategy capacity limits."""
    
    def __init__(self):
        super().__init__(
            agent_type="capacity_monitoring",
            subscribed_topics=["trade.executed", "trade.placed", "position.updated"]
        )
        
        # Capacity metrics per strategy
        self.capacity_metrics: Dict[str, CapacityMetrics] = {}
        
        # Pending trades (trade_id -> expected_price)
        self.pending_trades: Dict[str, Dict] = {}
        
        cprint("✅ Capacity Monitoring Agent initialized", "green")

    
    async def initialize(self):
        """Initialize agent and start calibration task."""
        await super().initialize()
        
        # Start periodic calibration task
        asyncio.create_task(self._calibration_loop())
    
    async def handle_trade_placed(self, event: Event):
        """Track expected price from trade placement."""
        trade_id = event.data.get('order_id')
        expected_price = event.data.get('expected_price')
        strategy_id = event.data.get('strategy_id', 'default')
        position_size = event.data.get('size', 0)
        
        if trade_id and expected_price:
            self.pending_trades[trade_id] = {
                'expected_price': expected_price,
                'strategy_id': strategy_id,
                'position_size': position_size,
                'timestamp': event.timestamp
            }
    
    async def handle_trade_executed(self, event: Event):
        """Track slippage and capacity."""
        trade_id = event.data.get('order_id')
        actual_price = event.data.get('entry_price')
        strategy_id = event.data.get('strategy_id', 'default')
        position_size = event.data.get('size', 0)
        
        if not trade_id or not actual_price:
            return
        
        # Get expected price from pending trades
        pending = self.pending_trades.get(trade_id)
        if not pending:
            # No expected price, can't calculate slippage
            return
        
        expected_price = pending['expected_price']
        
        # Calculate slippage
        slippage_pct = abs(actual_price - expected_price) / expected_price * 100
        
        # Initialize metrics if needed
        if strategy_id not in self.capacity_metrics:
            self.capacity_metrics[strategy_id] = CapacityMetrics(strategy_id=strategy_id)
        
        metrics = self.capacity_metrics[strategy_id]
        
        # Store slippage data
        metrics.slippage_history.append({
            'timestamp': event.timestamp,
            'position_size': position_size,
            'slippage_pct': slippage_pct,
            'expected_price': expected_price,
            'actual_price': actual_price
        })
        
        # Trim old history
        cutoff = datetime.utcnow() - timedelta(days=CAPACITY_CALIBRATION_DAYS)
        metrics.slippage_history = [
            h for h in metrics.slippage_history
            if h['timestamp'] > cutoff
        ]
        
        # Remove from pending
        del self.pending_trades[trade_id]
        
        cprint(f"📊 Slippage for {strategy_id}: {slippage_pct:.3f}% (size=${position_size:.0f})", "cyan")
        
        # Check if we need to recalibrate
        if len(metrics.slippage_history) >= 10:
            await self._check_capacity_utilization(strategy_id)

    
    async def handle_position_updated(self, event: Event):
        """Track current allocation per strategy."""
        strategy_id = event.data.get('strategy_id', 'default')
        allocation = event.data.get('allocation', 0)
        
        if strategy_id in self.capacity_metrics:
            self.capacity_metrics[strategy_id].current_allocation = allocation
            await self._check_capacity_utilization(strategy_id)
    
    async def _estimate_capacity(self, strategy_id: str) -> Optional[float]:
        """
        Estimate strategy capacity using square-root market impact model.
        
        Args:
            strategy_id: Strategy identifier
            
        Returns:
            Estimated capacity in USD, or None if insufficient data
        """
        metrics = self.capacity_metrics.get(strategy_id)
        if not metrics or len(metrics.slippage_history) < 10:
            return None
        
        # Extract position sizes and slippages
        position_sizes = np.array([h['position_size'] for h in metrics.slippage_history])
        slippages = np.array([h['slippage_pct'] for h in metrics.slippage_history])
        
        try:
            # Fit square-root model: slippage = k * sqrt(position_size)
            def model_func(x, k):
                return k * np.sqrt(x)
            
            popt, _ = curve_fit(model_func, position_sizes, slippages, p0=[metrics.market_impact_coefficient])
            k = popt[0]
            
            # Update coefficient
            metrics.market_impact_coefficient = k
            
            # Calculate capacity: solve for position_size where slippage = threshold
            # slippage_threshold = k * sqrt(capacity)
            # capacity = (slippage_threshold / k)^2
            capacity = (CAPACITY_SLIPPAGE_THRESHOLD_PCT / k) ** 2
            
            metrics.estimated_capacity = capacity
            metrics.last_calibration = datetime.utcnow()
            
            cprint(f"📈 Estimated capacity for {strategy_id}: ${capacity:,.0f} (k={k:.6f})", "cyan")
            
            return capacity
            
        except Exception as e:
            cprint(f"⚠️ Could not estimate capacity for {strategy_id}: {str(e)}", "yellow")
            return None

    
    async def _check_capacity_utilization(self, strategy_id: str):
        """Check capacity utilization and emit warnings if needed."""
        metrics = self.capacity_metrics.get(strategy_id)
        if not metrics:
            return
        
        # Estimate capacity if not done recently
        if metrics.estimated_capacity == 0 or not metrics.last_calibration:
            await self._estimate_capacity(strategy_id)
        
        if metrics.estimated_capacity == 0:
            return
        
        # Calculate utilization
        utilization_pct = (metrics.current_allocation / metrics.estimated_capacity) * 100
        
        # Check warning threshold
        if utilization_pct >= CAPACITY_WARNING_UTILIZATION_PCT:
            # Don't spam warnings (max once per hour)
            if metrics.last_warning and (datetime.utcnow() - metrics.last_warning).seconds < 3600:
                return
            
            metrics.last_warning = datetime.utcnow()
            
            if utilization_pct >= CAPACITY_EXCEEDED_UTILIZATION_PCT:
                # Capacity exceeded - emit critical warning
                await self.emit_event(
                    event_type=EventType.STRATEGY_CAPACITY_EXCEEDED,
                    token=None,
                    data={
                        "strategy_id": strategy_id,
                        "utilization_pct": float(utilization_pct),
                        "current_allocation": float(metrics.current_allocation),
                        "estimated_capacity": float(metrics.estimated_capacity),
                        "recommended_allocation": float(metrics.estimated_capacity * 0.5),
                        "action": f"Reduce position sizing by {CAPACITY_POSITION_REDUCTION_PCT}%"
                    }
                )
                cprint(f"🚨 CAPACITY EXCEEDED for {strategy_id}: {utilization_pct:.1f}%", "red")
            else:
                # Warning threshold - emit warning
                await self.emit_event(
                    event_type=EventType.STRATEGY_CAPACITY_WARNING,
                    token=None,
                    data={
                        "strategy_id": strategy_id,
                        "utilization_pct": float(utilization_pct),
                        "current_allocation": float(metrics.current_allocation),
                        "estimated_capacity": float(metrics.estimated_capacity),
                        "warning_threshold": CAPACITY_WARNING_UTILIZATION_PCT
                    }
                )
                cprint(f"⚠️ Capacity warning for {strategy_id}: {utilization_pct:.1f}%", "yellow")
    
    async def _calibration_loop(self):
        """Periodic calibration of capacity estimates."""
        while self.is_running:
            await asyncio.sleep(86400 * CAPACITY_UPDATE_FREQUENCY_DAYS)  # Run weekly
            
            cprint("🔄 Running capacity calibration...", "cyan")
            
            for strategy_id in list(self.capacity_metrics.keys()):
                await self._estimate_capacity(strategy_id)
    
    async def run_event_loop(self):
        """Override to register event handlers."""
        self._event_handlers[EventType.TRADE_PLACED] = self.handle_trade_placed
        self._event_handlers[EventType.TRADE_EXECUTED] = self.handle_trade_executed
        self._event_handlers[EventType.POSITION_UPDATED] = self.handle_position_updated
        await super().run_event_loop()


if __name__ == "__main__":
    agent = CapacityMonitoringAgent()
    agent.run()
