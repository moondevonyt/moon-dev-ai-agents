"""
🌙 Moon Dev's Signal Aggregation Agent
Aggregates weak signals into strong consensus predictions

Implements Jim Simons-style signal aggregation:
- Weighted signal aggregation
- Bayesian weight updating
- Consensus decision logic
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from termcolor import cprint

from src.agents.quant.base_quant_agent import BaseQuantAgent
from src.core.models import Event, EventType
from src.config import (
    SIGNAL_AGGREGATION_WINDOW_SECONDS,
    SIGNAL_AGGREGATION_MIN_SOURCES,
    SIGNAL_AGGREGATION_CONSENSUS_THRESHOLD,
    SIGNAL_AGGREGATION_WEIGHT_ALPHA,
    SIGNAL_AGGREGATION_MIN_OBSERVATIONS
)


@dataclass
class SignalWeight:
    """Signal weight data structure."""
    signal_source: str
    weight: float = 0.5  # Start with neutral weight
    accuracy: float = 0.5  # Start with neutral accuracy
    observations: int = 0
    last_updated: datetime = None


@dataclass
class Signal:
    """Individual signal data structure."""
    signal_source: str
    token: str
    direction: str  # LONG, SHORT, NEUTRAL
    confidence: float
    timestamp: datetime
    data: dict


class SignalAggregationAgent(BaseQuantAgent):
    """Aggregates multiple signals into consensus decisions."""
    
    def __init__(self):
        super().__init__(
            agent_type="signal_aggregation",
            subscribed_topics=[
                "signal.generated",
                "signal.anomaly",
                "signal.correlation",
                "trade.executed"
            ]
        )
        
        # Signal buffer (token -> list of signals)
        self.signal_buffer: Dict[str, List[Signal]] = {}
        
        # Signal weights (signal_source -> SignalWeight)
        self.signal_weights: Dict[str, SignalWeight] = {}
        
        # Pending trades for performance tracking (trade_id -> signal_sources)
        self.pending_trades: Dict[str, List[str]] = {}
        
        cprint("✅ Signal Aggregation Agent initialized", "green")

    async def initialize(self):
        """Initialize agent and load weights from Redis."""
        await super().initialize()
        
        # Load signal weights from Redis
        await self._load_weights_from_cache()
        
        # Start signal aggregation task
        asyncio.create_task(self._aggregation_loop())
    
    async def _load_weights_from_cache(self):
        """Load signal weights from Redis cache."""
        try:
            weights_data = await self.cache.get("signal_weights")
            if weights_data:
                weights_dict = json.loads(weights_data)
                for source, weight_data in weights_dict.items():
                    self.signal_weights[source] = SignalWeight(**weight_data)
                cprint(f"✅ Loaded {len(self.signal_weights)} signal weights from cache", "green")
        except Exception as e:
            cprint(f"⚠️ Could not load weights from cache: {str(e)}", "yellow")
    
    async def _save_weights_to_cache(self):
        """Save signal weights to Redis cache."""
        try:
            weights_dict = {
                source: asdict(weight)
                for source, weight in self.signal_weights.items()
            }
            await self.cache.set("signal_weights", json.dumps(weights_dict, default=str))
        except Exception as e:
            cprint(f"⚠️ Could not save weights to cache: {str(e)}", "yellow")

    async def handle_signal(self, event: Event):
        """Handle incoming signal events."""
        token = event.token
        if not token:
            return
        
        # Extract signal data
        signal = Signal(
            signal_source=event.source,
            token=token,
            direction=event.data.get('direction', 'NEUTRAL'),
            confidence=event.data.get('confidence', 0.5),
            timestamp=event.timestamp,
            data=event.data
        )
        
        # Add to buffer
        if token not in self.signal_buffer:
            self.signal_buffer[token] = []
        
        self.signal_buffer[token].append(signal)
        
        # Initialize weight if new source
        if signal.signal_source not in self.signal_weights:
            self.signal_weights[signal.signal_source] = SignalWeight(
                signal_source=signal.signal_source,
                last_updated=datetime.utcnow()
            )
    
    async def handle_trade_executed(self, event: Event):
        """Handle trade execution to update signal weights."""
        trade_id = event.data.get('order_id')
        token = event.token
        actual_return = event.data.get('return', 0.0)
        
        if not trade_id or trade_id not in self.pending_trades:
            return
        
        # Get signal sources that contributed to this trade
        signal_sources = self.pending_trades[trade_id]
        
        # Update weights for each contributing signal
        for source in signal_sources:
            if source in self.signal_weights:
                await self._update_signal_weight(source, actual_return)
        
        # Remove from pending
        del self.pending_trades[trade_id]

    async def _update_signal_weight(self, signal_source: str, actual_return: float):
        """Update signal weight using Bayesian updating."""
        weight_obj = self.signal_weights[signal_source]
        
        # Calculate accuracy (1.0 - normalized error)
        accuracy = 1.0 - min(abs(actual_return) / 100, 1.0)
        
        # Apply Bayesian prior for signals with few observations
        if weight_obj.observations < SIGNAL_AGGREGATION_MIN_OBSERVATIONS:
            prior_weight = 0.5
            posterior_weight = (
                prior_weight * (SIGNAL_AGGREGATION_MIN_OBSERVATIONS - weight_obj.observations) +
                accuracy * weight_obj.observations
            ) / SIGNAL_AGGREGATION_MIN_OBSERVATIONS
            weight_obj.weight = posterior_weight
        else:
            # Use exponential moving average for established signals
            alpha = SIGNAL_AGGREGATION_WEIGHT_ALPHA
            weight_obj.weight = (1 - alpha) * weight_obj.weight + alpha * accuracy
        
        weight_obj.accuracy = accuracy
        weight_obj.observations += 1
        weight_obj.last_updated = datetime.utcnow()
        
        # Save to cache
        await self._save_weights_to_cache()
        
        cprint(f"📊 Updated weight for {signal_source}: {weight_obj.weight:.3f} (obs={weight_obj.observations})", "cyan")

    async def _aggregation_loop(self):
        """Periodic aggregation of signals."""
        while self.is_running:
            await asyncio.sleep(SIGNAL_AGGREGATION_WINDOW_SECONDS)
            
            # Process each token's signals
            for token in list(self.signal_buffer.keys()):
                await self._aggregate_signals_for_token(token)
    
    async def _aggregate_signals_for_token(self, token: str):
        """Aggregate signals for a specific token."""
        signals = self.signal_buffer.get(token, [])
        
        if len(signals) == 0:
            return
        
        # Remove old signals (outside time window)
        cutoff_time = datetime.utcnow() - timedelta(seconds=SIGNAL_AGGREGATION_WINDOW_SECONDS)
        signals = [s for s in signals if s.timestamp > cutoff_time]
        self.signal_buffer[token] = signals
        
        # Check minimum sources requirement
        unique_sources = set(s.signal_source for s in signals)
        if len(unique_sources) < SIGNAL_AGGREGATION_MIN_SOURCES:
            return
        
        # Calculate weighted consensus
        consensus_score, contributing_signals = self._calculate_weighted_consensus(signals)
        
        # Check consensus threshold
        if abs(consensus_score) >= SIGNAL_AGGREGATION_CONSENSUS_THRESHOLD:
            # Emit consensus approved event
            direction = "LONG" if consensus_score > 0 else "SHORT"
            
            await self.emit_event(
                event_type=EventType.TRADE_CONSENSUS_APPROVED,
                token=token,
                data={
                    "direction": direction,
                    "consensus_score": float(consensus_score),
                    "confidence": abs(consensus_score) / 100,
                    "contributing_signals": contributing_signals,
                    "num_sources": len(unique_sources),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            cprint(f"✅ Consensus approved for {token}: {direction} (score={consensus_score:.1f})", "green")
            
            # Clear buffer for this token
            self.signal_buffer[token] = []
        else:
            # Emit consensus failed event
            await self.emit_event(
                event_type=EventType.SIGNAL_CONSENSUS_FAILED,
                token=token,
                data={
                    "consensus_score": float(consensus_score),
                    "threshold": SIGNAL_AGGREGATION_CONSENSUS_THRESHOLD,
                    "num_sources": len(unique_sources),
                    "reason": "Consensus score below threshold"
                }
            )

    def _calculate_weighted_consensus(self, signals: List[Signal]) -> tuple:
        """Calculate weighted consensus score from signals."""
        total_weighted_score = 0.0
        total_weight = 0.0
        contributing_signals = []
        
        for signal in signals:
            # Get weight for this signal source
            weight_obj = self.signal_weights.get(signal.signal_source)
            if not weight_obj:
                continue
            
            weight = weight_obj.weight
            
            # Convert direction to score (-100 to +100)
            if signal.direction == "LONG":
                score = signal.confidence * 100
            elif signal.direction == "SHORT":
                score = -signal.confidence * 100
            else:
                score = 0
            
            # Apply weight
            weighted_score = score * weight
            total_weighted_score += weighted_score
            total_weight += weight
            
            # Track contributing signal
            contributing_signals.append({
                "source": signal.signal_source,
                "direction": signal.direction,
                "confidence": signal.confidence,
                "weight": weight,
                "weighted_score": weighted_score
            })
        
        # Calculate consensus (weighted average)
        if total_weight > 0:
            consensus_score = total_weighted_score / total_weight
        else:
            consensus_score = 0.0
        
        return consensus_score, contributing_signals
    
    async def run_event_loop(self):
        """Override to register event handlers."""
        # Register event handlers
        self._event_handlers[EventType.SIGNAL_GENERATED] = self.handle_signal
        self._event_handlers[EventType.SIGNAL_ANOMALY] = self.handle_signal
        self._event_handlers[EventType.SIGNAL_CORRELATION] = self.handle_signal
        self._event_handlers[EventType.TRADE_EXECUTED] = self.handle_trade_executed
        
        # Run parent event loop
        await super().run_event_loop()


# Entry point for running agent standalone
if __name__ == "__main__":
    agent = SignalAggregationAgent()
    agent.run()
