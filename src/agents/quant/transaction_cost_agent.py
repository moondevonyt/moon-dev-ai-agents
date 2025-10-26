"""
🌙 Moon Dev's Transaction Cost Analysis Agent
Analyzes and validates transaction costs before execution

Implements realistic cost modeling:
- Slippage estimation (square-root market impact model)
- Fee calculation (exchange + network fees)
- Cost-based trade rejection
- Cost model calibration
"""

import asyncio
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Optional
from dataclasses import dataclass
from termcolor import cprint
from scipy.optimize import curve_fit

from src.agents.quant.base_quant_agent import BaseQuantAgent
from src.core.models import Event, EventType
from src.config import (
    MAX_TRANSACTION_COST_PCT,
    MARKET_IMPACT_COEFFICIENT,
    SLIPPAGE_CALIBRATION_DAYS
)


@dataclass
class CostModel:
    """Transaction cost model parameters."""
    token: str
    market_impact_coefficient: float = MARKET_IMPACT_COEFFICIENT
    avg_volume: float = 0.0
    last_calibration: datetime = None


class TransactionCostAgent(BaseQuantAgent):
    """Analyzes transaction costs and rejects expensive trades."""
    
    def __init__(self):
        super().__init__(
            agent_type="transaction_cost",
            subscribed_topics=["signal.aggregated", "trade.executed"]
        )
        
        # Cost models per token
        self.cost_models: Dict[str, CostModel] = {}
        
        # Execution history for calibration
        self.execution_history: Dict[str, list] = {}
        
        cprint("✅ Transaction Cost Agent initialized", "green")

    async def handle_signal_aggregated(self, event: Event):
        """Handle aggregated signal and analyze costs."""
        token = event.token
        if not token:
            return
        
        # Get or create cost model
        if token not in self.cost_models:
            self.cost_models[token] = CostModel(token=token)
        
        model = self.cost_models[token]
        
        # Extract trade parameters
        direction = event.data.get('direction')
        order_size = event.data.get('order_size', 1000)  # Default $1000
        
        # Estimate costs
        slippage_pct = self._estimate_slippage(model, order_size)
        fees = self._calculate_fees(order_size)
        total_cost_pct = slippage_pct + (fees / order_size * 100)
        
        # Check if cost exceeds threshold
        if total_cost_pct > MAX_TRANSACTION_COST_PCT:
            # Reject trade
            await self.emit_event(
                event_type=EventType.TRADE_COST_REJECTED,
                token=token,
                data={
                    "direction": direction,
                    "order_size": order_size,
                    "estimated_slippage_pct": float(slippage_pct),
                    "estimated_fees": float(fees),
                    "total_cost_pct": float(total_cost_pct),
                    "threshold_pct": MAX_TRANSACTION_COST_PCT,
                    "reason": f"Cost {total_cost_pct:.3f}% exceeds threshold {MAX_TRANSACTION_COST_PCT}%"
                }
            )
            cprint(f"❌ Trade rejected for {token}: cost {total_cost_pct:.3f}% > {MAX_TRANSACTION_COST_PCT}%", "red")
        else:
            # Approve trade with cost analysis
            await self.emit_event(
                event_type=EventType.TRADE_COST_ANALYSIS,
                token=token,
                data={
                    "direction": direction,
                    "order_size": order_size,
                    "estimated_slippage_pct": float(slippage_pct),
                    "estimated_fees": float(fees),
                    "total_cost_pct": float(total_cost_pct),
                    "approved": True
                },
                correlation_id=event.correlation_id
            )
            cprint(f"✅ Trade approved for {token}: cost {total_cost_pct:.3f}%", "green")
    
    def _estimate_slippage(self, model: CostModel, order_size: float) -> float:
        """Estimate slippage using square-root market impact model."""
        if model.avg_volume == 0:
            # Default assumption if no volume data
            model.avg_volume = 100000
        
        # Square-root model: impact = k * sqrt(order_size / avg_volume)
        impact = model.market_impact_coefficient * np.sqrt(order_size / model.avg_volume)
        
        # Add bid-ask spread (assume 0.1% for now)
        spread = 0.1
        
        total_slippage = spread / 2 + impact
        return total_slippage
    
    def _calculate_fees(self, order_size: float) -> float:
        """Calculate exchange and network fees."""
        # Exchange fee (assume 0.1% maker/taker)
        exchange_fee = order_size * 0.001
        
        # Network fee (Solana ~$0.02, HyperLiquid varies)
        network_fee = 0.02
        
        return exchange_fee + network_fee
    
    async def handle_trade_executed(self, event: Event):
        """Handle trade execution to calibrate cost model."""
        token = event.token
        if not token:
            return
        
        # Extract execution data
        expected_price = event.data.get('expected_price')
        actual_price = event.data.get('entry_price')
        order_size = event.data.get('size', 0)
        
        if not expected_price or not actual_price:
            return
        
        # Calculate actual slippage
        actual_slippage_pct = abs(actual_price - expected_price) / expected_price * 100
        
        # Store execution history
        if token not in self.execution_history:
            self.execution_history[token] = []
        
        self.execution_history[token].append({
            'timestamp': event.timestamp,
            'order_size': order_size,
            'actual_slippage_pct': actual_slippage_pct
        })
        
        # Trim old history
        cutoff = datetime.utcnow() - timedelta(days=SLIPPAGE_CALIBRATION_DAYS)
        self.execution_history[token] = [
            h for h in self.execution_history[token]
            if h['timestamp'] > cutoff
        ]
        
        # Recalibrate if enough data
        if len(self.execution_history[token]) >= 10:
            await self._calibrate_cost_model(token)
    
    async def _calibrate_cost_model(self, token: str):
        """Calibrate cost model using actual execution data."""
        history = self.execution_history.get(token, [])
        if len(history) < 10:
            return
        
        # Extract data
        order_sizes = np.array([h['order_size'] for h in history])
        slippages = np.array([h['actual_slippage_pct'] for h in history])
        
        # Fit square-root model
        try:
            def model_func(x, k):
                return k * np.sqrt(x)
            
            popt, _ = curve_fit(model_func, order_sizes, slippages, p0=[MARKET_IMPACT_COEFFICIENT])
            
            # Update model
            if token in self.cost_models:
                self.cost_models[token].market_impact_coefficient = popt[0]
                self.cost_models[token].last_calibration = datetime.utcnow()
                
                cprint(f"📊 Calibrated cost model for {token}: k={popt[0]:.6f}", "cyan")
        except Exception as e:
            cprint(f"⚠️ Could not calibrate cost model for {token}: {str(e)}", "yellow")
    
    async def run_event_loop(self):
        """Override to register event handlers."""
        self._event_handlers[EventType.SIGNAL_AGGREGATED] = self.handle_signal_aggregated
        self._event_handlers[EventType.TRADE_EXECUTED] = self.handle_trade_executed
        
        await super().run_event_loop()


if __name__ == "__main__":
    agent = TransactionCostAgent()
    agent.run()
