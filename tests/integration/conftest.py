"""
Pytest Configuration for Integration Tests

Provides fixtures for testing with Kafka, TimescaleDB, and Redis.
"""

import pytest
import asyncio
from datetime import datetime
from typing import AsyncGenerator

from src.core.event_producer import EventProducer
from src.core.event_consumer import EventConsumer
from src.core.event_store import EventStore
from src.core.cache_layer import CacheLayer
from src.core.models import Event, EventType, PriceTickEvent


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def kafka_producer() -> AsyncGenerator[EventProducer, None]:
    """Provide Kafka producer."""
    producer = EventProducer(["kafka-1:29091", "kafka-2:29092", "kafka-3:29093"])
    yield producer
    producer.close()


@pytest.fixture
async def event_store_db() -> AsyncGenerator[EventStore, None]:
    """Provide connected EventStore."""
    store = EventStore(
        host="timescaledb",
        port=5432,
        database="moon_dev",
        user="postgres",
        password="postgres",
    )
    await store.connect()
    yield store
    await store.close()


@pytest.fixture
async def cache() -> AsyncGenerator[CacheLayer, None]:
    """Provide connected CacheLayer."""
    layer = CacheLayer(host="redis-master", port=6379)
    await layer.connect()
    yield layer
    await layer.close()


@pytest.fixture
def sample_price_tick() -> PriceTickEvent:
    """Create sample price tick event."""
    return PriceTickEvent(
        token="BTC-USD",
        data={
            "price": 43250.50,
            "bid": 43249.75,
            "ask": 43251.25,
            "volume_24h": 125000000,
            "timestamp": datetime.utcnow().isoformat(),
        }
    )


@pytest.fixture
def sample_portfolio() -> dict:
    """Create sample portfolio state."""
    return {
        "user_id": "test_user",
        "positions": [
            {
                "token": "BTC-USD",
                "direction": "long",
                "size": 1.5,
                "entry_price": 42000.0,
                "current_price": 43250.50,
                "unrealized_pnl": 1875.75,
                "unrealized_pnl_pct": 2.97,
            }
        ],
        "balance": 50000.0,
        "metrics": {
            "leverage_ratio": 1.29,
            "liquidation_distance": 0.78,
            "daily_pnl": 1000.0,
            "daily_pnl_pct": 2.0,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }
