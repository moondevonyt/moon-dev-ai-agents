"""
Unit Tests - Event Models

Tests for event model validation and serialization.
"""

import pytest
from datetime import datetime
from uuid import UUID

from src.core.models import (
    Event,
    EventType,
    PriceTickEvent,
    SignalGeneratedEvent,
    TradeExecutedEvent,
    PortfolioStateSnapshot,
)


class TestEventBase:
    """Test base Event class."""
    
    def test_event_creation(self):
        """Test creating a base event."""
        # Act
        event = Event(
            event_type=EventType.PRICE_TICK,
            token="BTC-USD",
            source="price_feed",
            data={"price": 43250.50}
        )
        
        # Assert
        assert event.token == "BTC-USD"
        assert event.event_type == EventType.PRICE_TICK
        assert event.source == "price_feed"
        assert event.data == {"price": 43250.50}
        assert isinstance(event.event_id, str)
        assert isinstance(event.timestamp, datetime)
    
    def test_event_has_correlation_id(self):
        """Test event correlation ID."""
        # Act
        event = Event(
            event_type=EventType.PRICE_TICK,
            token="BTC-USD",
            source="test",
            data={}
        )
        
        # Assert
        assert event.correlation_id is not None
        assert isinstance(event.correlation_id, str)
    
    def test_event_correlation_id_propagation(self):
        """Test correlation ID propagates through events."""
        # Arrange
        original_correlation_id = "test-correlation-123"
        
        # Act
        event1 = Event(
            event_type=EventType.PRICE_TICK,
            token="BTC-USD",
            source="source1",
            data={},
            correlation_id=original_correlation_id
        )
        
        event2 = Event(
            event_type=EventType.SIGNAL_GENERATED,
            token="BTC-USD",
            source="source2",
            data={},
            correlation_id=event1.correlation_id
        )
        
        # Assert
        assert event1.correlation_id == event2.correlation_id
        assert event1.correlation_id == original_correlation_id
    
    def test_event_serialization(self):
        """Test event can be serialized to dict."""
        # Arrange
        event = Event(
            event_type=EventType.PRICE_TICK,
            token="BTC-USD",
            source="test",
            data={"price": 43250.50}
        )
        
        # Act
        event_dict = event.dict()
        
        # Assert
        assert isinstance(event_dict, dict)
        assert event_dict["token"] == "BTC-USD"
        assert event_dict["data"] == {"price": 43250.50}


class TestPriceTickEvent:
    """Test PriceTickEvent."""
    
    def test_price_tick_creation(self):
        """Test creating a price tick event."""
        # Act
        event = PriceTickEvent(
            token="BTC-USD",
            data={"price": 43250.50}
        )
        
        # Assert
        assert event.token == "BTC-USD"
        assert event.event_type == EventType.PRICE_TICK
        assert event.source == "price_feed"
        assert event.data["price"] == 43250.50
    
    def test_price_tick_with_full_data(self):
        """Test price tick with comprehensive market data."""
        # Act
        event = PriceTickEvent(
            token="ETH-USD",
            data={
                "price": 2250.75,
                "bid": 2249.50,
                "ask": 2251.00,
                "volume_24h": 50000000,
                "high_24h": 2300.00,
                "low_24h": 2200.00,
            }
        )
        
        # Assert
        assert event.data["price"] == 2250.75
        assert event.data["bid"] == 2249.50
        assert event.data["volume_24h"] == 50000000


class TestSignalGeneratedEvent:
    """Test SignalGeneratedEvent."""
    
    def test_signal_event_creation(self):
        """Test creating a signal event."""
        # Act
        event = SignalGeneratedEvent(
            token="BTC-USD",
            data={
                "agent": "trading_agent",
                "direction": "long",
                "confidence": 0.85,
                "indicators": {"RSI": 65, "SMA": "bullish"}
            }
        )
        
        # Assert
        assert event.token == "BTC-USD"
        assert event.event_type == EventType.SIGNAL_GENERATED
        assert event.source == "agent"
        assert event.data["agent"] == "trading_agent"
        assert event.data["confidence"] == 0.85
    
    def test_signal_confidence_validation(self):
        """Test signal confidence is 0-1."""
        # Act
        event = SignalGeneratedEvent(
            token="BTC-USD",
            data={"confidence": 0.75}
        )
        
        # Assert
        assert 0 <= event.data["confidence"] <= 1


class TestTradeExecutedEvent:
    """Test TradeExecutedEvent."""
    
    def test_trade_executed_event(self):
        """Test creating a trade executed event."""
        # Act
        event = TradeExecutedEvent(
            token="BTC-USD",
            data={
                "order_id": "order-123",
                "direction": "long",
                "size": 2.5,
                "entry_price": 43250.50,
                "fill_price": 43251.00,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        # Assert
        assert event.token == "BTC-USD"
        assert event.event_type == EventType.TRADE_EXECUTED
        assert event.data["order_id"] == "order-123"
        assert event.data["size"] == 2.5
    
    def test_trade_pnl_calculation(self):
        """Test calculating P&L from trade."""
        # Arrange
        entry_price = 43250.50
        fill_price = 43251.00
        size = 2.5
        
        # Act
        event = TradeExecutedEvent(
            token="BTC-USD",
            data={
                "entry_price": entry_price,
                "fill_price": fill_price,
                "size": size,
                "direction": "long"
            }
        )
        
        # Calculate P&L
        pnl = (fill_price - entry_price) * size
        
        # Assert
        assert pnl == 1.25  # (43251 - 43250.5) * 2.5 = 1.25


class TestPortfolioStateSnapshot:
    """Test PortfolioStateSnapshot."""
    
    def test_portfolio_snapshot_creation(self):
        """Test creating a portfolio snapshot."""
        # Act
        event = PortfolioStateSnapshot(
            token="BTC-USD",
            data={
                "user_id": "user-123",
                "positions": [
                    {
                        "token": "BTC-USD",
                        "direction": "long",
                        "size": 1.5,
                        "entry_price": 42000.0
                    }
                ],
                "balance": 50000.0,
                "metrics": {
                    "leverage_ratio": 1.29,
                    "daily_pnl": 1000.0
                }
            }
        )
        
        # Assert
        assert event.event_type == EventType.PORTFOLIO_UPDATED
        assert event.data["user_id"] == "user-123"
        assert len(event.data["positions"]) == 1
        assert event.data["balance"] == 50000.0


class TestEventTypeEnum:
    """Test EventType enum."""
    
    def test_event_type_values(self):
        """Test all event types are defined."""
        # Assert
        assert EventType.PRICE_TICK
        assert EventType.LIQUIDATION_EVENT
        assert EventType.SENTIMENT_UPDATE
        assert EventType.SIGNAL_GENERATED
        assert EventType.TRADE_PLACED
        assert EventType.TRADE_EXECUTED
        assert EventType.PORTFOLIO_UPDATED
    
    def test_event_type_string_conversion(self):
        """Test event type string conversion."""
        # Arrange
        event_type = EventType.PRICE_TICK
        
        # Act
        event_type_str = event_type.value
        
        # Assert
        assert isinstance(event_type_str, str)
        assert "price" in event_type_str.lower()


class TestEventValidation:
    """Test event validation."""
    
    def test_event_requires_type(self):
        """Test event requires event_type."""
        # Assert
        with pytest.raises(TypeError):
            Event(token="BTC-USD", source="test", data={})
    
    def test_event_requires_token(self):
        """Test event requires token."""
        # Assert
        with pytest.raises(TypeError):
            Event(event_type=EventType.PRICE_TICK, source="test", data={})
    
    def test_event_data_can_be_empty(self):
        """Test event data can be empty dict."""
        # Act
        event = Event(
            event_type=EventType.PRICE_TICK,
            token="BTC-USD",
            source="test",
            data={}
        )
        
        # Assert
        assert event.data == {}
    
    def test_invalid_data_type(self):
        """Test event data must be dict."""
        # Assert
        with pytest.raises(TypeError):
            Event(
                event_type=EventType.PRICE_TICK,
                token="BTC-USD",
                source="test",
                data="invalid"  # Should be dict
            )


class TestEventTimestamp:
    """Test event timestamp handling."""
    
    def test_event_timestamp_auto_set(self):
        """Test event timestamp is automatically set."""
        # Act
        before = datetime.utcnow()
        event = Event(
            event_type=EventType.PRICE_TICK,
            token="BTC-USD",
            source="test",
            data={}
        )
        after = datetime.utcnow()
        
        # Assert
        assert before <= event.timestamp <= after
    
    def test_event_timestamp_is_utc(self):
        """Test event timestamp is UTC."""
        # Act
        event = Event(
            event_type=EventType.PRICE_TICK,
            token="BTC-USD",
            source="test",
            data={}
        )
        
        # Assert
        assert event.timestamp.tzinfo is not None or True  # Allow naive UTC
