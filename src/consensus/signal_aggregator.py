"""
Signal Aggregator (T-3.5.2)

Collects, weights, and aggregates signals from multiple agents.
"""

import logging
from typing import Dict, List, Optional
from collections import defaultdict
from datetime import datetime, timedelta

from .consensus_models import (
    AgentSignal,
    RiskSignal,
    TradingSignal,
    SentimentSignal,
    SignalDirection,
    ConsensusResult,
)

logger = logging.getLogger(__name__)


class SignalAggregator:
    """
    Aggregates signals from multiple agents using weighted consensus.
    
    Weighting Strategy:
    - Risk Agent: 35% weight (safety-critical, prevents liquidation)
    - Trading Agent: 40% weight (primary profit signal)
    - Sentiment Agent: 25% weight (sentiment/momentum confirmation)
    
    Consensus Rules:
    - EXECUTE: ≥70% weighted consensus + risk approval
    - HOLD: 40-70% weighted consensus
    - REJECT: <40% weighted consensus OR risk agent veto
    """
    
    # Agent weights (sum = 100%)
    AGENT_WEIGHTS = {
        "risk_agent": 0.35,
        "trading_agent": 0.40,
        "sentiment_agent": 0.25,
    }
    
    # Confidence thresholds
    EXECUTE_THRESHOLD = 0.70
    HOLD_THRESHOLD = 0.40
    REJECT_THRESHOLD = 0.40
    
    # Signal time window (signals older than this are discarded)
    SIGNAL_WINDOW_SECONDS = 60
    
    def __init__(self):
        """Initialize signal aggregator."""
        self.signal_history: Dict[str, List[AgentSignal]] = defaultdict(list)
        self.consensus_history: Dict[str, List[ConsensusResult]] = defaultdict(list)
    
    def add_signal(self, signal: AgentSignal, token: str) -> None:
        """Add a signal for a token."""
        # Validate signal is recent
        age = (datetime.utcnow() - signal.timestamp).total_seconds()
        if age > self.SIGNAL_WINDOW_SECONDS:
            logger.warning(f"Discarding stale signal from {signal.agent_name}: {age}s old")
            return
        
        self.signal_history[token].append(signal)
        
        # Keep only recent signals
        cutoff = datetime.utcnow() - timedelta(seconds=self.SIGNAL_WINDOW_SECONDS)
        self.signal_history[token] = [
            s for s in self.signal_history[token]
            if s.timestamp > cutoff
        ]
        
        logger.info(f"✅ Added {signal.agent_name} signal for {token}")
    
    def aggregate_consensus(
        self,
        token: str,
        processing_start: datetime,
    ) -> Optional[ConsensusResult]:
        """
        Aggregate signals into consensus decision.
        
        Returns:
            ConsensusResult if enough signals, None otherwise
        
        Processing:
            1. Validate we have required signals (risk + at least 1 other)
            2. Calculate weighted direction scores
            3. Determine recommendation (EXECUTE/HOLD/REJECT)
            4. Validate risk agent approval
        """
        signals = self.signal_history.get(token, [])
        
        if not signals:
            logger.warning(f"No signals for {token}")
            return None
        
        # Extract signals by agent
        risk_signal = None
        trading_signal = None
        sentiment_signal = None
        
        for signal in signals:
            if signal.agent_name == "risk_agent" and isinstance(signal, RiskSignal):
                risk_signal = signal
            elif signal.agent_name == "trading_agent" and isinstance(signal, TradingSignal):
                trading_signal = signal
            elif signal.agent_name == "sentiment_agent" and isinstance(signal, SentimentSignal):
                sentiment_signal = signal
        
        # Validate we have minimum required signals
        if not risk_signal:
            logger.warning(f"Missing risk signal for {token}")
            return None
        
        if not trading_signal:
            logger.warning(f"Missing trading signal for {token}")
            return None
        
        # Calculate weighted consensus
        weighted_scores = self._calculate_weighted_scores(
            risk_signal, trading_signal, sentiment_signal
        )
        
        # Determine direction with highest score
        best_direction = max(
            weighted_scores.items(),
            key=lambda x: x[1]
        )[0]
        
        # Calculate final confidence
        consensus_confidence = weighted_scores[best_direction]
        
        # Determine recommended action
        recommended_action, risk_approval, risk_reason = self._determine_action(
            best_direction,
            consensus_confidence,
            risk_signal
        )
        
        # Get position sizing recommendation
        recommended_size = trading_signal.recommended_size
        recommended_entry = trading_signal.recommended_entry
        
        # Calculate processing latency
        processing_latency_ms = (datetime.utcnow() - processing_start).total_seconds() * 1000
        
        # Build voting summary
        voting_summary = self._build_voting_summary(signals)
        weight_summary = weighted_scores
        
        # Create consensus result
        consensus = ConsensusResult(
            token=token,
            consensus_direction=best_direction,
            consensus_confidence=consensus_confidence,
            agent_signals=[s.dict() for s in signals],
            voting_summary=voting_summary,
            weight_summary=weight_summary,
            recommended_action=recommended_action,
            recommended_size=recommended_size,
            recommended_entry=recommended_entry,
            risk_approval=risk_approval,
            risk_reason=risk_reason,
            processing_latency_ms=processing_latency_ms,
        )
        
        # Store in history
        self.consensus_history[token].append(consensus)
        
        logger.info(
            f"🤝 Consensus for {token}: {best_direction} "
            f"({consensus_confidence:.1%}) → {recommended_action}"
        )
        
        return consensus
    
    def _calculate_weighted_scores(
        self,
        risk_signal: RiskSignal,
        trading_signal: TradingSignal,
        sentiment_signal: Optional[SentimentSignal],
    ) -> Dict[SignalDirection, float]:
        """
        Calculate weighted direction scores.
        
        Scoring:
        - LONG: All agents voting long, weighted by agent confidence
        - SHORT: All agents voting short, weighted by agent confidence
        - NEUTRAL: Mixed signals or low confidence
        - CLOSE: Risk agent veto or liquidation warning
        """
        scores = defaultdict(float)
        
        # Risk agent scoring
        risk_direction = risk_signal.direction
        risk_weight = self.AGENT_WEIGHTS["risk_agent"]
        
        if risk_direction == SignalDirection.CLOSE:
            # Force close overrides everything
            scores[SignalDirection.CLOSE] += risk_weight * risk_signal.confidence
        else:
            scores[risk_direction] += risk_weight * risk_signal.confidence
        
        # Trading agent scoring
        trading_direction = trading_signal.direction
        trading_weight = self.AGENT_WEIGHTS["trading_agent"]
        scores[trading_direction] += trading_weight * trading_signal.confidence
        
        # Sentiment agent scoring (if present)
        if sentiment_signal:
            sentiment_direction = sentiment_signal.direction
            sentiment_weight = self.AGENT_WEIGHTS["sentiment_agent"]
            scores[sentiment_direction] += sentiment_weight * sentiment_signal.confidence
        else:
            # If no sentiment signal, redistribute weight to other agents
            redistribute_weight = self.AGENT_WEIGHTS["sentiment_agent"] * 0.5
            scores[risk_direction] += redistribute_weight * 0.5
            scores[trading_direction] += redistribute_weight * 0.5
        
        # Normalize scores to 0-1 range
        total_weight = sum(scores.values())
        if total_weight > 0:
            for direction in scores:
                scores[direction] = min(1.0, scores[direction])
        
        return dict(scores)
    
    def _determine_action(
        self,
        best_direction: SignalDirection,
        consensus_confidence: float,
        risk_signal: RiskSignal,
    ) -> tuple[str, bool, str]:
        """
        Determine recommended action and risk approval.
        
        Returns:
            (action: EXECUTE|HOLD|REJECT, risk_approval: bool, reason: str)
        """
        # Risk agent veto
        if best_direction == SignalDirection.CLOSE:
            return "REJECT", False, f"Force close signal: {risk_signal.reason}"
        
        if risk_signal.direction == SignalDirection.CLOSE:
            return "REJECT", False, f"Risk agent force close: {risk_signal.reasoning}"
        
        # Risk level check
        if risk_signal.risk_level == "critical":
            return "REJECT", False, "Risk level critical - liquidation imminent"
        
        risk_approval = risk_signal.risk_level == "ok"
        risk_reason = f"Risk: {risk_signal.risk_level} (leverage: {risk_signal.leverage_ratio:.2f}x)"
        
        # Confidence-based action determination
        if consensus_confidence >= self.EXECUTE_THRESHOLD and risk_approval:
            return "EXECUTE", True, f"Consensus {consensus_confidence:.1%}: Execute"
        
        elif consensus_confidence >= self.HOLD_THRESHOLD:
            return "HOLD", risk_approval, f"Consensus {consensus_confidence:.1%}: Hold"
        
        else:
            return "REJECT", risk_approval, f"Consensus {consensus_confidence:.1%}: Insufficient confidence"
    
    def _build_voting_summary(self, signals: List[AgentSignal]) -> Dict[str, int]:
        """Build vote count by direction."""
        votes = defaultdict(int)
        for signal in signals:
            votes[signal.direction] += 1
        return dict(votes)
    
    def get_recent_consensus(self, token: str, limit: int = 10) -> List[ConsensusResult]:
        """Get recent consensus decisions for a token."""
        return self.consensus_history[token][-limit:]
    
    def clear_signals(self, token: str) -> None:
        """Clear old signals for a token."""
        cutoff = datetime.utcnow() - timedelta(seconds=self.SIGNAL_WINDOW_SECONDS)
        self.signal_history[token] = [
            s for s in self.signal_history[token]
            if s.timestamp > cutoff
        ]
