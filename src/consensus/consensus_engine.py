"""
Consensus Engine (T-3.5)

Orchestrates multi-agent consensus and decision-making.
Receives signals from Risk, Trading, and Sentiment agents.
Produces trade consensus approval/rejection for ExecutionEngine.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional, Callable

from src.core.event_producer import EventProducer
from src.core.models import Event, EventType
from src.core.cache_layer import CacheLayer

from .consensus_models import (
    AgentSignal,
    RiskSignal,
    TradingSignal,
    SentimentSignal,
    ConsensusSignal,
)
from .signal_aggregator import SignalAggregator

logger = logging.getLogger(__name__)


class ConsensusEngine:
    """
    Multi-agent consensus engine for trade decisions.
    
    Workflow:
    1. Receive signal from Risk Agent (required)
    2. Receive signal from Trading Agent (required)
    3. Receive signal from Sentiment Agent (optional)
    4. Aggregate signals into weighted consensus
    5. Validate risk constraints
    6. Emit consensus approval/rejection event
    
    Performance Target: <100ms from last signal to consensus decision
    """
    
    # Timeout waiting for all signals (ms)
    SIGNAL_COLLECTION_TIMEOUT_MS = 500
    
    def __init__(
        self,
        producer: EventProducer,
        cache_layer: CacheLayer,
    ):
        """
        Initialize consensus engine.
        
        Args:
            producer: EventProducer for emitting consensus events
            cache_layer: CacheLayer for state management
        """
        self.producer = producer
        self.cache_layer = cache_layer
        self.aggregator = SignalAggregator()
        
        # Token-specific signal buffers
        self.signal_buffers: Dict[str, Dict[str, AgentSignal]] = {}
        
        # Consensus callbacks
        self.consensus_callbacks: Dict[str, list[Callable]] = {}
        
        # Metrics
        self.metrics = {
            "consensus_decisions": 0,
            "consensus_approved": 0,
            "consensus_rejected": 0,
            "avg_consensus_latency_ms": 0.0,
        }
    
    async def on_signal(
        self,
        signal: AgentSignal,
        token: str,
    ) -> Optional[ConsensusSignal]:
        """
        Process incoming agent signal.
        
        Args:
            signal: AgentSignal from an agent
            token: Trading pair
        
        Returns:
            ConsensusSignal if consensus reached, None otherwise
        """
        processing_start = datetime.utcnow()
        
        logger.info(f"📥 Received {signal.agent_name} signal for {token}")
        
        # Initialize buffer for token if needed
        if token not in self.signal_buffers:
            self.signal_buffers[token] = {}
        
        # Add signal to buffer (overwrites previous signal from same agent)
        self.signal_buffers[token][signal.agent_name] = signal
        self.aggregator.add_signal(signal, token)
        
        # Try to reach consensus
        consensus_result = self.aggregator.aggregate_consensus(
            token,
            processing_start
        )
        
        if not consensus_result:
            logger.info(f"⏳ Waiting for more signals ({len(self.signal_buffers[token])}/3)")
            return None
        
        # Build consensus signal with all components
        consensus_signal = ConsensusSignal(
            consensus=consensus_result,
            risk_signal=self.signal_buffers[token].get("risk_agent"),
            trading_signal=self.signal_buffers[token].get("trading_agent"),
            sentiment_signal=self.signal_buffers[token].get("sentiment_agent"),
        )
        
        # Update metrics
        self.metrics["consensus_decisions"] += 1
        if consensus_result.recommended_action == "EXECUTE":
            self.metrics["consensus_approved"] += 1
        else:
            self.metrics["consensus_rejected"] += 1
        
        # Emit consensus event
        await self._emit_consensus_event(consensus_signal, token, consensus_result)
        
        # Clear buffers for this token
        self.signal_buffers[token] = {}
        
        return consensus_signal
    
    async def _emit_consensus_event(
        self,
        consensus_signal: ConsensusSignal,
        token: str,
        consensus_result,
    ) -> None:
        """Emit consensus approval or rejection event."""
        
        if consensus_result.recommended_action == "EXECUTE":
            # Emit approval event
            event = Event(
                event_type=EventType.TRADE_CONSENSUS_APPROVED,
                token=token,
                source="consensus_engine",
                data={
                    "consensus": consensus_result.dict(),
                    "direction": consensus_result.consensus_direction,
                    "confidence": consensus_result.consensus_confidence,
                    "recommended_size": consensus_result.recommended_size,
                    "recommended_entry": consensus_result.recommended_entry,
                }
            )
            
            await self.producer.publish(event, topic="trading.consensus")
            logger.info(f"✅ Emitted TRADE_CONSENSUS_APPROVED for {token}")
        
        else:
            # Emit rejection event
            event = Event(
                event_type=EventType.TRADE_CONSENSUS_REJECTED,
                token=token,
                source="consensus_engine",
                data={
                    "consensus": consensus_result.dict(),
                    "reason": consensus_result.recommended_action,
                    "confidence": consensus_result.consensus_confidence,
                }
            )
            
            await self.producer.publish(event, topic="trading.consensus")
            logger.info(f"❌ Emitted TRADE_CONSENSUS_REJECTED for {token}: {consensus_result.recommended_action}")
        
        # Call registered callbacks
        if token in self.consensus_callbacks:
            for callback in self.consensus_callbacks[token]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(consensus_signal)
                    else:
                        callback(consensus_signal)
                except Exception as e:
                    logger.error(f"Error in consensus callback: {e}")
    
    def register_callback(
        self,
        token: str,
        callback: Callable,
    ) -> None:
        """
        Register callback to be invoked when consensus is reached.
        
        Args:
            token: Trading pair
            callback: Async function(consensus_signal) or sync function
        """
        if token not in self.consensus_callbacks:
            self.consensus_callbacks[token] = []
        self.consensus_callbacks[token].append(callback)
        logger.info(f"Registered consensus callback for {token}")
    
    def get_metrics(self) -> Dict:
        """Get consensus engine metrics."""
        return {
            **self.metrics,
            "signal_buffers_active": len(self.signal_buffers),
        }
    
    def get_consensus_history(self, token: str, limit: int = 10):
        """Get recent consensus decisions for a token."""
        return self.aggregator.get_recent_consensus(token, limit)
    
    async def close(self) -> None:
        """Cleanup resources."""
        logger.info("🛑 Closing consensus engine")
        self.signal_buffers.clear()
        self.consensus_callbacks.clear()
