"""
Consensus Models (T-3.5.1)

Pydantic models for multi-agent signal consensus.
"""

from datetime import datetime
from typing import Dict, Optional, List
from enum import Enum
from pydantic import BaseModel, Field


class SignalDirection(str, Enum):
    """Trading direction."""
    LONG = "long"
    SHORT = "short"
    NEUTRAL = "neutral"
    CLOSE = "close"


class AgentSignal(BaseModel):
    """Signal from a single agent."""
    
    agent_name: str = Field(..., description="Agent that generated signal")
    direction: SignalDirection = Field(..., description="Trade direction")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0-1")
    reasoning: str = Field(..., description="Why this signal was generated")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict = Field(default_factory=dict, description="Additional signal data")
    
    class Config:
        use_enum_values = True


class RiskSignal(AgentSignal):
    """Risk agent signal."""
    
    leverage_ratio: float = Field(..., description="Current leverage ratio")
    liquidation_distance: float = Field(..., ge=0.0, le=1.0, description="Distance to liquidation")
    risk_level: str = Field(..., description="risk, warning, critical")
    
    def __init__(self, **data):
        if "agent_name" not in data:
            data["agent_name"] = "risk_agent"
        super().__init__(**data)


class TradingSignal(AgentSignal):
    """Trading agent signal."""
    
    indicators: Dict[str, float] = Field(..., description="Technical indicators (SMA, RSI, etc)")
    llm_based: bool = Field(..., description="Whether signal used LLM inference")
    recommended_size: float = Field(..., description="Recommended position size")
    recommended_entry: float = Field(..., description="Recommended entry price")
    
    def __init__(self, **data):
        if "agent_name" not in data:
            data["agent_name"] = "trading_agent"
        super().__init__(**data)


class SentimentSignal(AgentSignal):
    """Sentiment agent signal."""
    
    sentiment_score: float = Field(..., ge=-1.0, le=1.0, description="Sentiment -1 to 1")
    sources: List[str] = Field(..., description="Sources (twitter, reddit, discord)")
    volume: int = Field(..., description="Number of mentions")
    velocity: float = Field(..., description="Sentiment change rate")
    
    def __init__(self, **data):
        if "agent_name" not in data:
            data["agent_name"] = "sentiment_agent"
        super().__init__(**data)


class ConsensusResult(BaseModel):
    """Result of multi-agent consensus."""
    
    token: str = Field(..., description="Trading pair")
    consensus_direction: SignalDirection = Field(..., description="Final agreed direction")
    consensus_confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence")
    
    # Consensus breakdown
    agent_signals: List[Dict] = Field(..., description="All agent signals considered")
    voting_summary: Dict[str, int] = Field(..., description="Vote counts by direction")
    weight_summary: Dict[str, float] = Field(..., description="Weighted sum by direction")
    
    # Recommendation
    recommended_action: str = Field(..., description="EXECUTE, HOLD, or REJECT")
    recommended_size: float = Field(..., description="Recommended position size")
    recommended_entry: float = Field(..., description="Recommended entry price")
    
    # Risk assessment
    risk_approval: bool = Field(..., description="Risk agent approval")
    risk_reason: str = Field(..., description="Risk agent reasoning")
    
    # Metadata
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    processing_latency_ms: float = Field(..., description="Time to reach consensus")
    
    class Config:
        use_enum_values = True


class ConsensusSignal(BaseModel):
    """Wrapper for consensus with original signals."""
    
    consensus: ConsensusResult = Field(...)
    risk_signal: Optional[RiskSignal] = None
    trading_signal: Optional[TradingSignal] = None
    sentiment_signal: Optional[SentimentSignal] = None
    
    class Config:
        use_enum_values = True
