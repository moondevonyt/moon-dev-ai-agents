"""
Integration Tests - Agents and Consensus

Tests agent signal generation and multi-agent consensus.
"""

import pytest
import asyncio
from datetime import datetime

from src.consensus.consensus_models import (
    RiskSignal,
    TradingSignal,
    SentimentSignal,
    SignalDirection,
)
from src.consensus.signal_aggregator import SignalAggregator
from src.consensus.consensus_engine import ConsensusEngine
from src.core.event_producer import EventProducer
from src.core.cache_layer import CacheLayer


@pytest.mark.asyncio
class TestSignalAggregation:
    """Test signal aggregation logic."""
    
    def test_signal_aggregator_initialization(self):
        """Test signal aggregator initialization."""
        # Act
        aggregator = SignalAggregator()
        
        # Assert
        assert aggregator is not None
        assert aggregator.AGENT_WEIGHTS["risk_agent"] == 0.35
        assert aggregator.AGENT_WEIGHTS["trading_agent"] == 0.40
        assert aggregator.AGENT_WEIGHTS["sentiment_agent"] == 0.25
    
    def test_add_signal_to_aggregator(self):
        """Test adding signal to aggregator."""
        # Arrange
        aggregator = SignalAggregator()
        token = "BTC-USD"
        
        risk_signal = RiskSignal(
            direction=SignalDirection.LONG,
            confidence=0.8,
            reasoning="Risk acceptable",
            leverage_ratio=2.5,
            liquidation_distance=0.75,
            risk_level="ok",
        )
        
        # Act
        aggregator.add_signal(risk_signal, token)
        
        # Assert
        assert token in aggregator.signal_history
        assert len(aggregator.signal_history[token]) == 1
    
    def test_consensus_long_direction(self):
        """Test consensus with all agents agreeing on LONG."""
        # Arrange
        aggregator = SignalAggregator()
        token = "BTC-USD"
        processing_start = datetime.utcnow()
        
        # Risk agent: LONG
        risk_signal = RiskSignal(
            direction=SignalDirection.LONG,
            confidence=0.8,
            reasoning="Risk acceptable",
            leverage_ratio=2.5,
            liquidation_distance=0.75,
            risk_level="ok",
        )
        
        # Trading agent: LONG
        trading_signal = TradingSignal(
            direction=SignalDirection.LONG,
            confidence=0.85,
            reasoning="Technical indicators bullish",
            indicators={"SMA20": 43100, "RSI": 65, "MACD": "positive"},
            llm_based=False,
            recommended_size=2.0,
            recommended_entry=43200.0,
        )
        
        # Sentiment agent: LONG
        sentiment_signal = SentimentSignal(
            direction=SignalDirection.LONG,
            confidence=0.7,
            reasoning="Positive sentiment detected",
            sentiment_score=0.65,
            sources=["twitter", "reddit"],
            volume=1250,
            velocity=0.15,
        )
        
        # Act
        aggregator.add_signal(risk_signal, token)
        aggregator.add_signal(trading_signal, token)
        aggregator.add_signal(sentiment_signal, token)
        
        consensus = aggregator.aggregate_consensus(token, processing_start)
        
        # Assert
        assert consensus is not None
        assert consensus.consensus_direction == SignalDirection.LONG
        assert consensus.consensus_confidence > 0.7
        assert consensus.recommended_action == "EXECUTE"
        assert consensus.risk_approval is True
    
    def test_consensus_short_direction(self):
        """Test consensus with LONG vs SHORT conflict."""
        # Arrange
        aggregator = SignalAggregator()
        token = "ETH-USD"
        processing_start = datetime.utcnow()
        
        # Risk agent: SHORT (bearish)
        risk_signal = RiskSignal(
            direction=SignalDirection.SHORT,
            confidence=0.7,
            reasoning="High leverage warning",
            leverage_ratio=8.5,
            liquidation_distance=0.45,
            risk_level="warning",
        )
        
        # Trading agent: LONG (technical)
        trading_signal = TradingSignal(
            direction=SignalDirection.LONG,
            confidence=0.75,
            reasoning="Bullish crossover",
            indicators={"SMA20": 2250, "RSI": 55},
            llm_based=False,
            recommended_size=1.5,
            recommended_entry=2240.0,
        )
        
        # Act
        aggregator.add_signal(risk_signal, token)
        aggregator.add_signal(trading_signal, token)
        
        consensus = aggregator.aggregate_consensus(token, processing_start)
        
        # Assert
        assert consensus is not None
        # Likely HOLD or LONG with reduced confidence
        assert consensus.consensus_confidence <= 0.75
    
    def test_consensus_with_missing_sentiment(self):
        """Test consensus when sentiment agent signal is missing."""
        # Arrange
        aggregator = SignalAggregator()
        token = "SOL-USD"
        processing_start = datetime.utcnow()
        
        # Risk agent only
        risk_signal = RiskSignal(
            direction=SignalDirection.LONG,
            confidence=0.8,
            reasoning="Risk acceptable",
            leverage_ratio=3.0,
            liquidation_distance=0.8,
            risk_level="ok",
        )
        
        # Trading agent only
        trading_signal = TradingSignal(
            direction=SignalDirection.LONG,
            confidence=0.9,
            reasoning="Strong buy signal",
            indicators={"RSI": 75, "MACD": "strong_positive"},
            llm_based=False,
            recommended_size=3.0,
            recommended_entry=105.0,
        )
        
        # Act
        aggregator.add_signal(risk_signal, token)
        aggregator.add_signal(trading_signal, token)
        
        consensus = aggregator.aggregate_consensus(token, processing_start)
        
        # Assert
        assert consensus is not None
        assert consensus.consensus_direction == SignalDirection.LONG
        assert consensus.consensus_confidence > 0.7


@pytest.mark.asyncio
class TestConsensusEngine:
    """Test consensus engine orchestration."""
    
    async def test_consensus_engine_initialization(self, kafka_producer, cache):
        """Test consensus engine initialization."""
        # Act
        engine = ConsensusEngine(kafka_producer, cache)
        
        # Assert
        assert engine is not None
        assert engine.aggregator is not None
        assert len(engine.signal_buffers) == 0
    
    async def test_signal_processing_flow(self, kafka_producer, cache):
        """Test complete signal processing flow."""
        # Arrange
        engine = ConsensusEngine(kafka_producer, cache)
        token = "BTC-USD"
        processing_start = datetime.utcnow()
        
        risk_signal = RiskSignal(
            direction=SignalDirection.LONG,
            confidence=0.8,
            reasoning="Risk acceptable",
            leverage_ratio=2.5,
            liquidation_distance=0.75,
            risk_level="ok",
        )
        
        trading_signal = TradingSignal(
            direction=SignalDirection.LONG,
            confidence=0.85,
            reasoning="Bullish",
            indicators={"RSI": 65},
            llm_based=False,
            recommended_size=2.0,
            recommended_entry=43200.0,
        )
        
        # Act
        consensus1 = await engine.on_signal(risk_signal, token)
        consensus2 = await engine.on_signal(trading_signal, token)
        
        # Assert
        assert consensus1 is None  # Need both signals
        assert consensus2 is not None  # Now we have consensus
        assert consensus2.consensus.consensus_direction == SignalDirection.LONG
    
    async def test_consensus_callback_registration(self, kafka_producer, cache):
        """Test callback registration on consensus."""
        # Arrange
        engine = ConsensusEngine(kafka_producer, cache)
        token = "ETH-USD"
        callback_called = False
        
        async def test_callback(consensus_signal):
            nonlocal callback_called
            callback_called = True
        
        # Act
        engine.register_callback(token, test_callback)
        
        # Assert
        assert token in engine.consensus_callbacks
        assert test_callback in engine.consensus_callbacks[token]


@pytest.mark.asyncio
class TestSignalValidation:
    """Test signal validation."""
    
    def test_signal_confidence_range(self):
        """Test signal confidence is 0-1."""
        # Arrange & Act
        signal = TradingSignal(
            direction=SignalDirection.LONG,
            confidence=0.75,
            reasoning="Test signal",
            indicators={},
            llm_based=False,
            recommended_size=1.0,
            recommended_entry=100.0,
        )
        
        # Assert
        assert 0 <= signal.confidence <= 1
    
    def test_risk_signal_liquidation_distance(self):
        """Test liquidation distance is 0-1."""
        # Arrange & Act
        signal = RiskSignal(
            direction=SignalDirection.LONG,
            confidence=0.8,
            reasoning="Test",
            leverage_ratio=5.0,
            liquidation_distance=0.65,
            risk_level="ok",
        )
        
        # Assert
        assert 0 <= signal.liquidation_distance <= 1
    
    def test_sentiment_score_range(self):
        """Test sentiment score is -1 to 1."""
        # Arrange & Act
        signal = SentimentSignal(
            direction=SignalDirection.LONG,
            confidence=0.7,
            reasoning="Test sentiment",
            sentiment_score=0.45,
            sources=["twitter"],
            volume=100,
            velocity=0.1,
        )
        
        # Assert
        assert -1 <= signal.sentiment_score <= 1


@pytest.mark.asyncio
class TestWeightedConsensus:
    """Test weighted consensus calculation."""
    
    def test_agent_weight_sum(self):
        """Test agent weights sum to 100%."""
        # Arrange
        aggregator = SignalAggregator()
        
        # Act
        weight_sum = sum(aggregator.AGENT_WEIGHTS.values())
        
        # Assert
        assert abs(weight_sum - 1.0) < 0.001  # Allow floating point error
    
    def test_weighted_score_calculation(self):
        """Test weighted score calculation."""
        # Arrange
        aggregator = SignalAggregator()
        
        risk_signal = RiskSignal(
            direction=SignalDirection.LONG,
            confidence=0.8,
            reasoning="Test",
            leverage_ratio=2.0,
            liquidation_distance=0.8,
            risk_level="ok",
        )
        
        trading_signal = TradingSignal(
            direction=SignalDirection.LONG,
            confidence=0.9,
            reasoning="Test",
            indicators={},
            llm_based=False,
            recommended_size=1.0,
            recommended_entry=100.0,
        )
        
        # Act
        scores = aggregator._calculate_weighted_scores(
            risk_signal, trading_signal, None
        )
        
        # Assert
        assert SignalDirection.LONG in scores
        assert scores[SignalDirection.LONG] > 0
