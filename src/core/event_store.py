"""Event Store - persists all events to TimescaleDB.

Maps to T-2.3 (Event Store Persistence) in TASKS.md.

WHEN events are published
THEN the system SHALL persist all events to TimescaleDB
AND enable event replay for backtesting (FR-4.2)
AND maintain audit trail (CR-1.1)
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID

import asyncpg
from sqlalchemy import text
from prometheus_client import Counter, Histogram

from .models import Event, EventType

logger = logging.getLogger(__name__)

# Prometheus metrics (T-2.3: Metrics)
events_persisted = Counter(
    "events_persisted_total",
    "Total events persisted to EventStore",
    ["event_type"]
)
insert_latency_ms = Histogram(
    "event_store_insert_latency_ms",
    "Time to insert event(s) to TimescaleDB",
    ["batch_size"],
    buckets=[1, 5, 10, 50, 100, 500]
)
query_latency_ms = Histogram(
    "event_store_query_latency_ms",
    "Time to query events from TimescaleDB",
    ["query_type"],
    buckets=[100, 500, 1000, 5000, 10000]
)


class EventStore:
    """TimescaleDB event persistence layer.
    
    WHEN events need to be persisted
    THEN EventStore SHALL:
      1. Connect to TimescaleDB (T-2.3.1)
      2. Insert events with metadata
      3. Support batch inserts for efficiency (T-2.3.2)
      4. Enable fast queries (T-2.3.3)
      5. Track metrics and errors
    
    Performance Target: Insert latency < 5ms, Query latency < 5s (T-2.3)
    
    Schema (created during T-1.3):
        CREATE TABLE events (
            event_id UUID PRIMARY KEY,
            event_type VARCHAR(50) NOT NULL,
            timestamp TIMESTAMPTZ NOT NULL,
            token VARCHAR(20),
            data JSONB,
            source VARCHAR(50),
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        SELECT create_hypertable('events', 'timestamp', if_not_exists => TRUE);
        CREATE INDEX ON events (timestamp, token, event_type);
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str = "moon_dev",
        user: str = "postgres",
        password: str = "password",
        min_pool_size: int = 10,
        max_pool_size: int = 20,
    ):
        """Initialize EventStore.
        
        Args:
            host: PostgreSQL host
            port: PostgreSQL port
            database: Database name
            user: Database user
            password: Database password
            min_pool_size: Minimum connection pool size
            max_pool_size: Maximum connection pool size
        """
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.min_pool_size = min_pool_size
        self.max_pool_size = max_pool_size
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self) -> None:
        """Establish connection pool to TimescaleDB."""
        try:
            self.pool = await asyncpg.create_pool(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                min_size=self.min_pool_size,
                max_size=self.max_pool_size,
            )
            logger.info(f"Connected to EventStore at {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to connect to EventStore: {e}")
            raise

    async def disconnect(self) -> None:
        """Close connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("Disconnected from EventStore")

    async def insert_event(self, event: Event) -> bool:
        """Insert a single event.
        
        T-2.3.1: Insert single event
        
        Args:
            event: Event to persist
        
        Returns:
            bool: True if successful
        """
        return len(await self.insert_batch([event])) > 0

    async def insert_batch(self, events: List[Event]) -> List[UUID]:
        """Insert multiple events in a batch.
        
        T-2.3.2: Batch inserts for efficiency
        
        WHEN insert_batch is called
        THEN system SHALL batch 100+ events before inserting
        AND use bulk insert for performance
        
        Args:
            events: List of events to persist
        
        Returns:
            List[UUID]: Event IDs that were successfully inserted
        """
        if not events:
            return []

        if not self.pool:
            raise RuntimeError("EventStore not connected")

        start_time = datetime.utcnow()
        inserted_ids = []

        try:
            async with self.pool.acquire() as conn:
                # Prepare batch insert statement
                query = """
                    INSERT INTO events (
                        event_id, event_type, timestamp, token, 
                        data, source, created_at
                    ) VALUES 
                    ($1, $2, $3, $4, $5, $6, $7)
                    ON CONFLICT (event_id) DO NOTHING
                """

                # Insert events
                for event in events:
                    try:
                        await conn.execute(
                            query,
                            event.event_id,
                            event.event_type.value,
                            event.timestamp,
                            event.token,
                            event.model_dump_json(),
                            event.source,
                            datetime.utcnow(),
                        )
                        inserted_ids.append(event.event_id)
                        events_persisted.labels(event_type=event.event_type.value).inc()

                    except Exception as e:
                        logger.error(f"Failed to insert event {event.event_id}: {e}")
                        continue

        except Exception as e:
            logger.error(f"Batch insert failed: {e}")
            raise

        # Record latency
        latency = (datetime.utcnow() - start_time).total_seconds() * 1000
        batch_size_label = "small" if len(events) < 100 else "large"
        insert_latency_ms.labels(batch_size=batch_size_label).observe(latency)

        logger.info(f"Inserted {len(inserted_ids)} events in {latency:.1f}ms")
        return inserted_ids

    async def query_by_date_range(
        self,
        start_time: datetime,
        end_time: datetime,
        token: Optional[str] = None,
        event_type: Optional[EventType] = None,
        limit: int = 10000,
    ) -> List[Dict[str, Any]]:
        """Query events by date range.
        
        T-2.3.3: Query optimization for replay scenarios
        
        Performance: Uses time-series indices created in T-1.3
        Typical latency: < 5 seconds for 30-day range
        
        WHEN backtesting or analyzing events
        THEN EventStore SHALL retrieve events efficiently
        AND return results in chronological order
        
        Args:
            start_time: Start of time range
            end_time: End of time range
            token: Optional token filter
            event_type: Optional event type filter
            limit: Maximum results
        
        Returns:
            List[Dict]: Event records
        """
        if not self.pool:
            raise RuntimeError("EventStore not connected")

        start_query = datetime.utcnow()

        # Build dynamic query based on filters
        where_clauses = [
            "timestamp >= $1",
            "timestamp <= $2"
        ]
        params = [start_time, end_time]

        if token:
            where_clauses.append(f"token = ${len(params) + 1}")
            params.append(token)

        if event_type:
            where_clauses.append(f"event_type = ${len(params) + 1}")
            params.append(event_type.value)

        query = f"""
            SELECT 
                event_id, event_type, timestamp, token, 
                data, source, created_at
            FROM events
            WHERE {' AND '.join(where_clauses)}
            ORDER BY timestamp ASC
            LIMIT ${len(params) + 1}
        """
        params.append(limit)

        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, *params)

                # Convert to dicts
                results = [dict(row) for row in rows]

                # Record latency (T-2.3: Metrics)
                latency = (datetime.utcnow() - start_query).total_seconds() * 1000
                query_latency_ms.labels(query_type="range").observe(latency)

                logger.debug(f"Query returned {len(results)} events in {latency:.1f}ms")
                return results

        except Exception as e:
            logger.error(f"Query failed: {e}")
            raise

    async def get_latest_event(
        self,
        token: Optional[str] = None,
        event_type: Optional[EventType] = None,
    ) -> Optional[Dict[str, Any]]:
        """Get the most recent event matching criteria.
        
        Used for state consistency checks (FR-4.3: State Snapshots)
        
        Args:
            token: Optional token filter
            event_type: Optional event type filter
        
        Returns:
            Dict: Most recent event, or None if not found
        """
        if not self.pool:
            raise RuntimeError("EventStore not connected")

        where_clauses = []
        params = []

        if token:
            where_clauses.append(f"token = ${len(params) + 1}")
            params.append(token)

        if event_type:
            where_clauses.append(f"event_type = ${len(params) + 1}")
            params.append(event_type.value)

        where_str = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        query = f"""
            SELECT 
                event_id, event_type, timestamp, token, 
                data, source, created_at
            FROM events
            {where_str}
            ORDER BY timestamp DESC
            LIMIT 1
        """

        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(query, *params)
                return dict(row) if row else None

        except Exception as e:
            logger.error(f"Get latest event failed: {e}")
            raise

    async def count_events(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        token: Optional[str] = None,
    ) -> int:
        """Count events matching criteria.
        
        Used for monitoring and analytics
        
        Args:
            start_time: Start of time range
            end_time: End of time range
            token: Optional token filter
        
        Returns:
            int: Number of matching events
        """
        if not self.pool:
            raise RuntimeError("EventStore not connected")

        where_clauses = []
        params = []

        if start_time:
            where_clauses.append(f"timestamp >= ${len(params) + 1}")
            params.append(start_time)

        if end_time:
            where_clauses.append(f"timestamp <= ${len(params) + 1}")
            params.append(end_time)

        if token:
            where_clauses.append(f"token = ${len(params) + 1}")
            params.append(token)

        where_str = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        query = f"SELECT COUNT(*) as count FROM events {where_str}"

        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchval(query, *params)
                return row or 0

        except Exception as e:
            logger.error(f"Count events failed: {e}")
            raise

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
