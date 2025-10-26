"""
Trade Consensus Engine (T-3.5)

Multi-agent signal aggregation and consensus decision-making.
Collects signals from Risk, Trading, and Sentiment agents.
"""

from .consensus_engine import ConsensusEngine
from .signal_aggregator import SignalAggregator
from .consensus_models import ConsensusSignal, AgentSignal, ConsensusResult

__all__ = [
    "ConsensusEngine",
    "SignalAggregator",
    "ConsensusSignal",
    "AgentSignal",
    "ConsensusResult",
]
