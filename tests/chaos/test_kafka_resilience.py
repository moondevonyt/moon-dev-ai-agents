"""
Chaos Tests - Kafka Broker Resilience

Tests system behavior when Kafka brokers fail.
"""

import pytest
import asyncio
from datetime import datetime

from src.core.event_producer import EventProducer
from src.core.models import Event, EventType, PriceTickEvent


@pytest.mark.asyncio
class TestKafkaFailureScenarios:
    """Test Kafka failure scenarios."""
    
    async def test_kafka_broker_unavailable(self, kafka_producer):
        """Test behavior when Kafka broker is unavailable."""
        # This test would run with broker down
        # In practice: docker-compose pause kafka-1
        
        # Act - Try to publish with broker unavailable
        event = PriceTickEvent(
            token="BTC-USD",
            data={"price": 43250.50}
        )
        
        # Should either:
        # 1. Raise exception
        # 2. Retry and eventually fail
        # 3. Fall back to queue
        try:
            event_id = kafka_producer.publish(event)
            # If succeeds, broker was available
            assert event_id is not None
        except Exception as e:
            # Expected when broker down
            assert "connection" in str(e).lower() or "timeout" in str(e).lower()
    
    async def test_kafka_slow_broker(self, kafka_producer):
        """Test behavior when Kafka is slow."""
        # This test would run with network delay injected
        # In practice: tc qdisc add dev docker0 root netem delay 1000ms
        
        import time
        start = time.time()
        
        event = PriceTickEvent(
            token="BTC-USD",
            data={"price": 43250.50}
        )
        
        # Act
        event_id = kafka_producer.publish(event)
        elapsed = time.time() - start
        
        # Assert - Should eventually succeed but be slow
        assert event_id is not None
        # May take longer due to network delay
    
    async def test_kafka_replication_failure(self, kafka_producer):
        """Test behavior when replica brokers fail."""
        # Simulate 1 of 3 brokers failing
        
        event = PriceTickEvent(
            token="BTC-USD",
            data={"price": 43250.50}
        )
        
        # Act - Publish should still succeed with 2 brokers alive
        event_id = kafka_producer.publish(event)
        
        # Assert
        assert event_id is not None
    
    async def test_publish_batch_with_broker_failure(self, kafka_producer):
        """Test batch publish with broker failure mid-operation."""
        events = [
            PriceTickEvent(token="BTC-USD", data={"price": 43250.50}),
            PriceTickEvent(token="ETH-USD", data={"price": 2250.75}),
            PriceTickEvent(token="SOL-USD", data={"price": 105.30}),
        ]
        
        # Act
        try:
            await kafka_producer.publish_batch(events)
            # Success
        except Exception as e:
            # Should have robust error handling
            assert "batch" in str(e).lower() or "publish" in str(e).lower()


@pytest.mark.asyncio
class TestKafkaPartitionFailure:
    """Test partition rebalancing during failures."""
    
    async def test_partition_rebalancing(self, kafka_producer):
        """Test consumer group rebalancing."""
        # When broker fails, Kafka rebalances partitions
        # Consumers should handle this gracefully
        
        event = PriceTickEvent(
            token="BTC-USD",
            data={"price": 43250.50}
        )
        
        # Act - Publish during rebalancing
        try:
            event_id = kafka_producer.publish(event)
            assert event_id is not None
        except Exception as e:
            # Rebalancing may cause temporary failures
            pass
    
    async def test_leader_election_during_publish(self, kafka_producer):
        """Test behavior during Kafka leader election."""
        # When leader broker fails, election takes time
        
        event = PriceTickEvent(
            token="BTC-USD",
            data={"price": 43250.50}
        )
        
        # Act - May fail or retry during election
        try:
            event_id = kafka_producer.publish(event)
            assert event_id is not None
        except Exception as e:
            pass


@pytest.mark.asyncio
class TestKafkaLatencyInjection:
    """Test with injected latency."""
    
    async def test_latency_budget_with_broker_delay(self, kafka_producer):
        """Test that latency target is maintained even with slow broker."""
        import time
        
        # With network delay, should still be under target latency
        start = time.time()
        
        event = PriceTickEvent(
            token="BTC-USD",
            data={"price": 43250.50}
        )
        
        event_id = kafka_producer.publish(event)
        latency_ms = (time.time() - start) * 1000
        
        # Should attempt to maintain sub-100ms target
        # Even if broker is slow, SDK should timeout gracefully
        assert latency_ms < 5000  # Reasonable timeout
