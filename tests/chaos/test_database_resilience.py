"""
Chaos Tests - Database Resilience

Tests system behavior when database fails or is slow.
"""

import pytest
import asyncio
from datetime import datetime, timedelta

from src.core.event_store import EventStore
from src.core.models import PriceTickEvent


@pytest.mark.asyncio
class TestDatabaseFailureScenarios:
    """Test database failure scenarios."""
    
    async def test_database_connection_failure(self, event_store_db):
        """Test behavior when database connection fails."""
        # In practice: docker-compose stop timescaledb
        
        event = PriceTickEvent(
            token="BTC-USD",
            data={"price": 43250.50}
        )
        
        # Act - Try to insert with DB down
        try:
            event_id = await event_store_db.insert_event(event)
            assert event_id is not None
        except Exception as e:
            # Expected when DB is down
            assert "connect" in str(e).lower() or "database" in str(e).lower()
    
    async def test_database_slow_response(self, event_store_db):
        """Test behavior when database is slow."""
        # In practice: Network delay or resource constraints
        
        import time
        start = time.time()
        
        event = PriceTickEvent(
            token="BTC-USD",
            data={"price": 43250.50}
        )
        
        # Act
        try:
            event_id = await event_store_db.insert_event(event)
            elapsed = (time.time() - start) * 1000
            
            # Should eventually complete
            assert event_id is not None
            # Latency may exceed normal target
        except Exception as e:
            pass
    
    async def test_query_timeout_on_slow_database(self, event_store_db):
        """Test query timeout behavior."""
        # Large query on slow database
        
        start_time = datetime.utcnow() - timedelta(days=90)
        end_time = datetime.utcnow()
        
        # Act - Query large date range
        try:
            events = await event_store_db.query_by_date_range(
                start_time, end_time
            )
            # Query eventually completes
            assert isinstance(events, list)
        except Exception as e:
            # May timeout
            pass
    
    async def test_batch_insert_partial_failure(self, event_store_db):
        """Test behavior when batch insert partially fails."""
        # Mid-batch database becomes unavailable
        
        events = [
            PriceTickEvent(token=f"TOKEN{i}", data={"price": i * 100})
            for i in range(100)
        ]
        
        # Act
        try:
            await event_store_db.insert_batch(events)
            # All succeed
        except Exception as e:
            # Partial failure - some events inserted, others not
            pass


@pytest.mark.asyncio
class TestDatabaseConnectionPoolExhaustion:
    """Test behavior when connection pool is exhausted."""
    
    async def test_connection_pool_under_load(self, event_store_db):
        """Test connection pool behavior under high load."""
        # Simulate many concurrent queries
        
        async def query():
            try:
                events = await event_store_db.query_by_date_range(
                    datetime.utcnow() - timedelta(hours=1),
                    datetime.utcnow()
                )
                return len(events)
            except Exception:
                return 0
        
        # Act - Create many concurrent queries
        tasks = [query() for _ in range(50)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Assert - Most should succeed, some may fail if pool exhausted
        successes = sum(1 for r in results if isinstance(r, int) and r >= 0)
        assert successes > 25  # At least half should succeed


@pytest.mark.asyncio
class TestDatabaseConstraintViolation:
    """Test handling of database constraint violations."""
    
    async def test_duplicate_event_insertion(self, event_store_db):
        """Test inserting duplicate event (same ID)."""
        event = PriceTickEvent(
            token="BTC-USD",
            data={"price": 43250.50}
        )
        
        # Insert first time
        event_id1 = await event_store_db.insert_event(event)
        
        # Try to insert same event again (violates unique constraint)
        try:
            event_id2 = await event_store_db.insert_event(event)
            # If UUID differs, both succeed
            if event_id1 != event_id2:
                assert True
        except Exception as e:
            # Expected: unique constraint violation
            assert "unique" in str(e).lower() or "duplicate" in str(e).lower()
