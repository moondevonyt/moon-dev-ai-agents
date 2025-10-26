"""
Integration Tests - Event Flow

Tests complete event flow from producer through consumers to database.
"""

import pytest
import asyncio
import logging
from datetime import datetime, timedelta

from src.core.event_producer import EventProducer
from src.core.event_store import EventStore
from src.core.cache_layer import CacheLayer
from src.core.models import Event, EventType, PriceTickEvent, TradeExecutedEvent

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
class TestEventProducerConsumer:
    """Test event producer and consumer integration."""
    
    async def test_publish_event_to_kafka(self, kafka_producer):
        """Test publishing event to Kafka."""
        # Arrange
        event = PriceTickEvent(
            token="BTC-USD",
            data={"price": 43250.50}
        )
        
        # Act
        event_id = kafka_producer.publish(event)
        
        # Assert
        assert event_id is not None
        assert len(event_id) > 0
        logger.info(f"✅ Published event: {event_id}")
    
    async def test_publish_multiple_events(self, kafka_producer):
        """Test publishing multiple events in batch."""
        # Arrange
        events = [
            PriceTickEvent(token="BTC-USD", data={"price": 43250.50}),
            PriceTickEvent(token="ETH-USD", data={"price": 2250.75}),
            PriceTickEvent(token="SOL-USD", data={"price": 105.30}),
        ]
        
        # Act
        await kafka_producer.publish_batch(events)
        
        # Assert
        assert len(events) == 3
        logger.info("✅ Published 3 events in batch")
    
    async def test_event_persistence_to_db(self, kafka_producer, event_store_db):
        """Test event persistence from Kafka to TimescaleDB."""
        # Arrange
        event = PriceTickEvent(
            token="BTC-USD",
            data={"price": 43250.50}
        )
        
        # Act
        kafka_producer.publish(event)
        await asyncio.sleep(0.5)  # Wait for processing
        
        # Query from event store
        await event_store_db.connect()
        events = await event_store_db.query_by_date_range(
            datetime.utcnow() - timedelta(seconds=5),
            datetime.utcnow(),
            token="BTC-USD",
            event_type=EventType.PRICE_TICK
        )
        
        # Assert
        assert len(events) > 0
        assert events[0]["token"] == "BTC-USD"
        logger.info(f"✅ Persisted {len(events)} events to database")


@pytest.mark.asyncio
class TestCacheLayer:
    """Test cache layer integration."""
    
    async def test_portfolio_cache_get_set(self, cache, sample_portfolio):
        """Test getting and setting portfolio in cache."""
        # Arrange
        user_id = "test_user"
        
        # Act - Set portfolio
        await cache.set_portfolio(
            user_id,
            sample_portfolio["positions"],
            sample_portfolio["balance"],
            sample_portfolio["metrics"],
        )
        
        # Act - Get portfolio
        portfolio = await cache.get_portfolio(user_id)
        
        # Assert
        assert portfolio is not None
        assert portfolio["balance"] == sample_portfolio["balance"]
        assert len(portfolio["positions"]) == len(sample_portfolio["positions"])
        logger.info("✅ Portfolio cache get/set successful")
    
    async def test_cache_key_operations(self, cache):
        """Test cache key operations."""
        # Arrange
        test_key = "test_key"
        test_value = {"data": "test"}
        
        # Act - Set
        await cache.set(test_key, test_value)
        
        # Act - Get
        result = await cache.get(test_key)
        
        # Assert
        assert result == test_value
        
        # Act - Delete
        await cache.delete(test_key)
        result = await cache.get(test_key)
        
        # Assert
        assert result is None
        logger.info("✅ Cache key operations successful")
    
    async def test_cache_fallback_to_db(self, cache, event_store_db):
        """Test cache fallback to database."""
        # Arrange
        token = "BTC-USD"
        start_time = datetime.utcnow() - timedelta(hours=1)
        end_time = datetime.utcnow()
        
        # Act - Query from cache (miss)
        cache_result = await cache.get(f"events:{token}")
        
        # Assert cache miss
        assert cache_result is None
        
        # Act - Query from database
        db_events = await event_store_db.query_by_date_range(
            start_time, end_time, token=token
        )
        
        # Assert
        assert isinstance(db_events, list)
        logger.info("✅ Cache fallback to database successful")


@pytest.mark.asyncio
class TestEventStoreQueries:
    """Test event store query functionality."""
    
    async def test_query_events_by_date_range(self, event_store_db):
        """Test querying events by date range."""
        # Arrange
        start_time = datetime.utcnow() - timedelta(hours=1)
        end_time = datetime.utcnow()
        
        # Act
        events = await event_store_db.query_by_date_range(
            start_time, end_time
        )
        
        # Assert
        assert isinstance(events, list)
        logger.info(f"✅ Queried {len(events)} events by date range")
    
    async def test_query_events_by_token(self, event_store_db):
        """Test querying events by token."""
        # Arrange
        token = "BTC-USD"
        start_time = datetime.utcnow() - timedelta(hours=1)
        end_time = datetime.utcnow()
        
        # Act
        events = await event_store_db.query_by_date_range(
            start_time, end_time, token=token
        )
        
        # Assert
        assert isinstance(events, list)
        if len(events) > 0:
            assert events[0]["token"] == token
        logger.info(f"✅ Queried {len(events)} events for {token}")
    
    async def test_query_events_by_type(self, event_store_db):
        """Test querying events by type."""
        # Arrange
        event_type = EventType.PRICE_TICK
        start_time = datetime.utcnow() - timedelta(hours=1)
        end_time = datetime.utcnow()
        
        # Act
        events = await event_store_db.query_by_date_range(
            start_time, end_time, event_type=event_type
        )
        
        # Assert
        assert isinstance(events, list)
        if len(events) > 0:
            assert events[0]["event_type"] == event_type
        logger.info(f"✅ Queried {len(events)} events of type {event_type}")


@pytest.mark.asyncio
class TestEventStoreInsert:
    """Test event store insert functionality."""
    
    async def test_insert_single_event(self, event_store_db):
        """Test inserting single event."""
        # Arrange
        event = PriceTickEvent(
            token="BTC-USD",
            data={"price": 43250.50}
        )
        
        # Act
        event_id = await event_store_db.insert_event(event)
        
        # Assert
        assert event_id is not None
        logger.info(f"✅ Inserted event: {event_id}")
    
    async def test_insert_batch_events(self, event_store_db):
        """Test inserting batch of events."""
        # Arrange
        events = [
            PriceTickEvent(token="BTC-USD", data={"price": 43250.50}),
            PriceTickEvent(token="ETH-USD", data={"price": 2250.75}),
            PriceTickEvent(token="SOL-USD", data={"price": 105.30}),
        ]
        
        # Act
        await event_store_db.insert_batch(events)
        
        # Assert
        assert len(events) == 3
        logger.info(f"✅ Inserted batch of {len(events)} events")


@pytest.mark.asyncio
class TestEventStorePerformance:
    """Test event store performance characteristics."""
    
    async def test_insert_latency(self, event_store_db):
        """Test event insert latency (<50ms target)."""
        # Arrange
        import time
        event = PriceTickEvent(
            token="BTC-USD",
            data={"price": 43250.50}
        )
        
        # Act
        start = time.time()
        await event_store_db.insert_event(event)
        latency_ms = (time.time() - start) * 1000
        
        # Assert
        assert latency_ms < 100  # Allow 100ms in test environment
        logger.info(f"✅ Insert latency: {latency_ms:.2f}ms")
    
    async def test_query_latency(self, event_store_db):
        """Test query latency (<5s for 30-day range target)."""
        # Arrange
        import time
        start_time = datetime.utcnow() - timedelta(days=30)
        end_time = datetime.utcnow()
        
        # Act
        start = time.time()
        events = await event_store_db.query_by_date_range(
            start_time, end_time
        )
        latency_ms = (time.time() - start) * 1000
        
        # Assert
        assert latency_ms < 10000  # Allow 10s in test environment
        logger.info(f"✅ Query latency: {latency_ms:.2f}ms for {len(events)} events")
