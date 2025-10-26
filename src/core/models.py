"""Event data models and schemas for the EDA system.

Defines all event types and their structure using Pydantic for validation.
See DESIGN.md Event Taxonomy for complete event specifications.
"""

from enum import Enum
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional, Any, Dict

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """All event types in the system (EARS Event Taxonomy).
    
    WHEN an event occurs
    THEN the system SHALL use one of these event types to categorize it
    AND emit the event to appropriate Kafka topics
    """

    # Market Events (FR-1.1: Real-Time Event Ingestion)
    PRICE_TICK = "price.tick"
    LIQUIDATION_EVENT = "liquidation.event"
    SENTIMENT_UPDATE = "sentiment.update"
    WHALE_ACTIVITY = "whale.activity"

    # Processing Events (FR-2: Event Processing and Signal Generation)
    SIGNAL_GENERATED = "signal.generated"
    RISK_ALERT = "risk.alert"
    TRADE_CONSENSUS_APPROVED = "trade.consensus_approved"

    # Action Events (FR-3: Trade Execution)
    TRADE_PLACED = "trade.placed"
    TRADE_EXECUTED = "trade.executed"
    POSITION_CLOSED = "position.closed"
    ORDER_FILLED = "order.filled"

    # State Events (FR-4: State Management)
    STATE_SNAPSHOT = "state.snapshot"
    STATE_CHANGED = "state.changed"
    PORTFOLIO_UPDATED = "portfolio.updated"


class Event(BaseModel):
    """Base event schema for all events in the system.
    
    WHEN an event is published
    THEN it SHALL include all fields from this schema
    AND be serializable to JSON for Kafka transmission
    """

    event_id: UUID = Field(default_factory=uuid4, description="Unique event identifier")
    event_type: EventType = Field(description="Type of event")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC timestamp when event occurred"
    )
    token: Optional[str] = Field(
        default=None,
        description="Trading pair token (e.g., 'BTC-USD'). Used for Kafka partition routing"
    )
    source: str = Field(
        description="System component that generated this event (e.g., 'exchange', 'agent', 'risk')"
    )
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Event payload - structure varies by event_type"
    )
    correlation_id: Optional[str] = Field(
        default=None,
        description="Trace ID for correlating related events"
    )
    version: int = Field(
        default=1,
        description="Event schema version for evolution compatibility"
    )

    class Config:
        use_enum_values = True
        json_schema_extra = {
            "example": {
                "event_id": "550e8400-e29b-41d4-a716-446655440000",
                "event_type": "price.tick",
                "timestamp": "2025-10-26T10:30:45.123456Z",
                "token": "BTC-USD",
                "source": "exchange.hyperliquid",
                "data": {
                    "price": 43250.50,
                    "volume": 10.5,
                    "bid": 43250.00,
                    "ask": 43251.00,
                },
                "correlation_id": "trace-001",
                "version": 1,
            }
        }


class PriceTickEvent(Event):
    """Market price tick event (FR-1.1: Price Tick Ingestion)."""

    event_type: EventType = EventType.PRICE_TICK

    class Config:
        json_schema_extra = {
            "example": {
                "event_id": "550e8400-e29b-41d4-a716-446655440001",
                "event_type": "price.tick",
                "timestamp": "2025-10-26T10:30:45.123456Z",
                "token": "BTC-USD",
                "source": "exchange.hyperliquid",
                "data": {
                    "price": 43250.50,
                    "volume": 10.5,
                    "bid": 43250.00,
                    "ask": 43251.00,
                    "timestamp_ms": 1698316245123,
                },
            }
        }


class SignalGeneratedEvent(Event):
    """Agent generated trading signal event (FR-2.2: Signal Generation)."""

    event_type: EventType = EventType.SIGNAL_GENERATED

    class Config:
        json_schema_extra = {
            "example": {
                "event_id": "550e8400-e29b-41d4-a716-446655440002",
                "event_type": "signal.generated",
                "timestamp": "2025-10-26T10:30:46.000000Z",
                "token": "BTC-USD",
                "source": "agent.trading",
                "data": {
                    "direction": "LONG",
                    "confidence": 0.85,
                    "indicators": {
                        "sma_50": 43200.00,
                        "sma_200": 43000.00,
                        "rsi": 65.5,
                    },
                    "agent_type": "trading",
                    "reasoning": "RSI oversold, SMA bullish cross",
                },
            }
        }


class TradeExecutedEvent(Event):
    """Trade execution confirmation event (FR-3.3: Fill Monitoring)."""

    event_type: EventType = EventType.TRADE_EXECUTED

    class Config:
        json_schema_extra = {
            "example": {
                "event_id": "550e8400-e29b-41d4-a716-446655440003",
                "event_type": "trade.executed",
                "timestamp": "2025-10-26T10:30:47.500000Z",
                "token": "BTC-USD",
                "source": "execution.engine",
                "data": {
                    "order_id": "order-12345",
                    "direction": "LONG",
                    "size": 1.5,
                    "entry_price": 43250.50,
                    "fee": 12.97,
                    "exchange": "hyperliquid",
                    "leverage": 5,
                },
            }
        }


class PortfolioStateSnapshot(Event):
    """Portfolio state snapshot for consistency checking (FR-4.3: State Snapshots)."""

    event_type: EventType = EventType.STATE_SNAPSHOT

    class Config:
        json_schema_extra = {
            "example": {
                "event_id": "550e8400-e29b-41d4-a716-446655440004",
                "event_type": "state.snapshot",
                "timestamp": "2025-10-26T10:30:50.000000Z",
                "source": "cache.layer",
                "data": {
                    "user_id": "user-001",
                    "positions": [
                        {
                            "token": "BTC-USD",
                            "size": 1.5,
                            "entry_price": 43250.50,
                            "unrealized_pnl": 150.25,
                        }
                    ],
                    "balance": 10000.00,
                    "portfolio_value": 10150.25,
                    "leverage_ratio": 5.0,
                    "max_leverage": 10.0,
                },
            }
        }
