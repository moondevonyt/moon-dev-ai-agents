"""
Unit Tests - Consensus Logic

Tests for signal aggregation and consensus decision-making.
"""

import pytest
from datetime import datetime, timedelta

from src.consensus.consensus_models import (
    SignalDirection,
    RiskSignal,
    TradingSignal,
    SentimentSignal,
    ConsensusResult,
)
from src.consensus.signal_aggregator import SignalAggregator


class TestRiskSignal:
    """Test RiskSignal creation and validation."""
    
    def test_risk_signal_creation(self):
        """Test creating a risk signal."""
        # Act
        signal = RiskSignal(
            direction=SignalDirection.LONG,
            confidence=0.8,
            reasoning="Risk acceptable",
            leverage_ratio=2.5,
            liquidation_distance=0.75,
            risk_level="ok",
        )
        
        # Assert
        assert signal.agent_name == "risk_agent"
        assert signal.direction == SignalDirection.LONG
        assert signal.confidence == 0.8
        assert signal.leverage_ratio == 2.5
        assert signal.liquidation_distance == 0.75
        assert signal.risk_level == "ok"
    
    def test_risk_signal_liquidation_distance_range(self):
        """Test liquidation distance is 0-1."""
        # Act
        signal = RiskSignal(
            direction=SignalDirection.LONG,
            confidence=0.8,
            reasoning="Test",
            leverage_ratio=5.0,
            liquidation_distance=0.5,  # Valid: 0-1
            risk_level="ok",
        )
        
        # Assert
        assert 0 <= signal.liquidation_distance <= 1
    
    def test_risk_signal_invalid_liquidation_distance(self):
        """Test liquidation distance validation."""
        # Assert - should raise validation error
        with pytest.raises(ValueError):
            RiskSignal(
                direction=SignalDirection.LONG,
                confidence=0.8,
                reasoning="Test",
                leverage_ratio=5.0,
                liquidation_distance=1.5,  # Invalid: >1
                risk_level="ok",
            )


class TestTradingSignal:
    """Test TradingSignal creation and validation."""
    
    def test_trading_signal_creation(self):
        """Test creating a trading signal."""
        # Act
        signal = TradingSignal(
            direction=SignalDirection.LONG,
            confidence=0.85,
            reasoning="Technical indicators bullish",
            indicators={"SMA20": 43100, "RSI": 65, "MACD": "positive"},
            llm_based=False,
            recommended_size=2.0,
            recommended_entry=43200.0,
        )
        
        # Assert
        assert signal.agent_name == "trading_agent"
        assert signal.direction == SignalDirection.LONG
        assert signal.confidence == 0.85
        assert signal.llm_based is False
        assert signal.recommended_size == 2.0
        assert signal.recommended_entry == 43200.0
    
    def test_trading_signal_with_indicators(self):
        """Test trading signal with multiple indicators."""
        # Act
        indicators = {
            "SMA20": 43100,
            "SMA50": 42800,
            "SMA200": 42500,
            "RSI": 65,
            "MACD": "positive",
            "BB_Upper": 43500,
            "BB_Lower": 42800,
        }
        
        signal = TradingSignal(
            direction=SignalDirection.LONG,
            confidence=0.9,
            reasoning="All indicators aligned",
            indicators=indicators,
            llm_based=False,
            recommended_size=3.0,
            recommended_entry=43250.0,
        )
        
        # Assert
        assert len(signal.indicators) == 7
        assert signal.indicators["RSI"] == 65


class TestSentimentSignal:
    """Test SentimentSignal creation and validation."""
    
    def test_sentiment_signal_creation(self):
        """Test creating a sentiment signal."""
        # Act
        signal = SentimentSignal(
            direction=SignalDirection.LONG,
            confidence=0.7,
            reasoning="Positive sentiment detected",
            sentiment_score=0.65,
            sources=["twitter", "reddit"],
            volume=1250,
            velocity=0.15,
        )
        
        # Assert
        assert signal.agent_name == "sentiment_agent"
        assert signal.sentiment_score == 0.65
        assert len(signal.sources) == 2
        assert signal.volume == 1250
        assert signal.velocity == 0.15
    
    def test_sentiment_score_range(self):
        """Test sentiment score is -1 to 1."""
        # Act - Positive sentiment
        positive_signal = SentimentSignal(
            direction=SignalDirection.LONG,
            confidence=0.8,
            reasoning="Bullish",
            sentiment_score=0.8,
            sources=["twitter"],
            volume=100,
            velocity=0.1,
        )
        
        # Act - Negative sentiment
        negative_signal = SentimentSignal(
            direction=SignalDirection.SHORT,
            confidence=0.7,
            reasoning="Bearish",
            sentiment_score=-0.5,
            sources=["twitter"],
            volume=100,
            velocity=-0.1,
        )
        
        # Assert
        assert -1 <= positive_signal.sentiment_score <= 1
        assert -1 <= negative_signal.sentiment_score <= 1
    
    def test_invalid_sentiment_score(self):
        """Test sentiment score validation."""
        # Assert
        with pytest.raises(ValueError):
            SentimentSignal(
                direction=SignalDirection.LONG,
                confidence=0.7,
                reasoning="Test",
                sentiment_score=1.5,  # Invalid: >1
                sources=["twitter"],
                volume=100,
                velocity=0.1,
            )


class TestSignalAggregator:
    """Test SignalAggregator logic."""
    
    def test_aggregator_initialization(self):
        """Test aggregator initializes correctly."""
        # Act
        aggregator = SignalAggregator()
        
        # Assert
        assert aggregator.AGENT_WEIGHTS["risk_agent"] == 0.35
        assert aggregator.AGENT_WEIGHTS["trading_agent"] == 0.40
        assert aggregator.AGENT_WEIGHTS["sentiment_agent"] == 0.25
        assert sum(aggregator.AGENT_WEIGHTS.values()) == 1.0
    
    def test_add_signal(self):
        """Test adding a signal to aggregator."""
        # Arrange
        aggregator = SignalAggregator()
        token = "BTC-USD"
        
        signal = RiskSignal(
            direction=SignalDirection.LONG,
            confidence=0.8,
            reasoning="Test",
            leverage_ratio=2.5,
            liquidation_distance=0.75,
            risk_level="ok",
        )
        
        # Act
        aggregator.add_signal(signal, token)
        
        # Assert
        assert token in aggregator.signal_history
        assert len(aggregator.signal_history[token]) == 1
        assert aggregator.signal_history[token][0] == signal
    
    def test_stale_signal_rejection(self):
        """Test stale signals are rejected."""
        # Arrange
        aggregator = SignalAggregator()
        token = "BTC-USD"
        
        # Create old signal (>60 seconds)
        old_signal = RiskSignal(
            direction=SignalDirection.LONG,
            confidence=0.8,
            reasoning="Old signal",
            leverage_ratio=2.5,
            liquidation_distance=0.75,
            risk_level="ok",
            timestamp=datetime.utcnow() - timedelta(seconds=65)
        )
        
        # Act
        aggregator.add_signal(old_signal, token)
        
        # Assert - Signal should be discarded
        assert token not in aggregator.signal_history or len(aggregator.signal_history[token]) == 0
    
    def test_consensus_all_long(self):
        """Test consensus when all agents agree on LONG."""
        # Arrange
        aggregator = SignalAggregator()
        token = "BTC-USD"
        processing_start = datetime.utcnow()
        
        risk_signal = RiskSignal(
            direction=SignalDirection.LONG,
            confidence=0.8,
            reasoning="Risk ok",
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
        
        sentiment_signal = SentimentSignal(
            direction=SignalDirection.LONG,
            confidence=0.7,
            reasoning="Positive",
            sentiment_score=0.65,
            sources=["twitter"],
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
        assert consensus.consensus_confidence >= 0.70
        assert consensus.recommended_action == "EXECUTE"
        assert consensus.risk_approval is True
    
    def test_consensus_conflicting_signals(self):
        """Test consensus with conflicting signals."""
        # Arrange
        aggregator = SignalAggregator()
        token = "ETH-USD"
        processing_start = datetime.utcnow()
        
        # Risk: SHORT (warning)
        risk_signal = RiskSignal(
            direction=SignalDirection.SHORT,
            confidence=0.7,
            reasoning="High leverage",
            leverage_ratio=8.5,
            liquidation_distance=0.45,
            risk_level="warning",
        )
        
        # Trading: LONG (bullish)
        trading_signal = TradingSignal(
            direction=SignalDirection.LONG,
            confidence=0.75,
            reasoning="Bullish",
            indicators={"RSI": 55},
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
        # With conflict, confidence should be moderate
        assert consensus.consensus_confidence < 0.75
    
    def test_consensus_missing_sentiment(self):
        """Test consensus when sentiment agent doesn't signal."""
        # Arrange
        aggregator = SignalAggregator()
        token = "SOL-USD"
        processing_start = datetime.utcnow()
        
        risk_signal = RiskSignal(
            direction=SignalDirection.LONG,
            confidence=0.8,
            reasoning="Ok",
            leverage_ratio=3.0,
            liquidation_distance=0.8,
            risk_level="ok",
        )
        
        trading_signal = TradingSignal(
            direction=SignalDirection.LONG,
            confidence=0.9,
            reasoning="Strong buy",
            indicators={"RSI": 75},
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
        assert consensus.consensus_confidence >= 0.70
    
    def test_consensus_risk_veto(self):
        """Test risk agent can veto with CLOSE signal."""
        # Arrange
        aggregator = SignalAggregator()
        token = "ADA-USD"
        processing_start = datetime.utcnow()
        
        # Risk agent forces CLOSE
        risk_signal = RiskSignal(
            direction=SignalDirection.CLOSE,
            confidence=0.9,
            reasoning="Liquidation imminent",
            leverage_ratio=9.9,
            liquidation_distance=0.05,
            risk_level="critical",
        )
        
        trading_signal = TradingSignal(
            direction=SignalDirection.LONG,
            confidence=0.8,
            reasoning="Buy signal",
            indicators={},
            llm_based=False,
            recommended_size=2.0,
            recommended_entry=0.5,
        )
        
        # Act
        aggregator.add_signal(risk_signal, token)
        aggregator.add_signal(trading_signal, token)
        
        consensus = aggregator.aggregate_consensus(token, processing_start)
        
        # Assert
        assert consensus is not None
        assert consensus.recommended_action == "REJECT"
        assert consensus.risk_approval is False


class TestConsensusResult:
    """Test ConsensusResult data model."""
    
    def test_consensus_result_creation(self):
        """Test creating a consensus result."""
        # Act
        result = ConsensusResult(
            token="BTC-USD",
            consensus_direction=SignalDirection.LONG,
            consensus_confidence=0.78,
            agent_signals=[],
            voting_summary={str(SignalDirection.LONG): 3},
            weight_summary={str(SignalDirection.LONG): 0.78},
            recommended_action="EXECUTE",
            recommended_size=2.5,
            recommended_entry=43250.0,
            risk_approval=True,
            risk_reason="Leverage 2.5x, acceptable",
            processing_latency_ms=45.2,
        )
        
        # Assert
        assert result.token == "BTC-USD"
        assert result.consensus_direction == SignalDirection.LONG
        assert result.consensus_confidence == 0.78
        assert result.recommended_action == "EXECUTE"
        assert result.processing_latency_ms == 45.2
    
    def test_consensus_result_confidence_range(self):
        """Test consensus confidence is 0-1."""
        # Act
        result = ConsensusResult(
            token="BTC-USD",
            consensus_direction=SignalDirection.LONG,
            consensus_confidence=0.85,
            agent_signals=[],
            voting_summary={},
            weight_summary={},
            recommended_action="EXECUTE",
            recommended_size=1.0,
            recommended_entry=100.0,
            risk_approval=True,
            risk_reason="Test",
            processing_latency_ms=50.0,
        )
        
        # Assert
        assert 0 <= result.consensus_confidence <= 1


class TestWeightedScoreCalculation:
    """Test weighted score calculations."""
    
    def test_weighted_score_calculation(self):
        """Test calculating weighted scores."""
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
        assert scores[SignalDirection.LONG] <= 1.0
    
    def test_score_sum_with_missing_sentiment(self):
        """Test score calculation with missing sentiment agent."""
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
        # Should still have LONG direction (weighted from risk and trading agents)
        assert scores[SignalDirection.LONG] > 0
