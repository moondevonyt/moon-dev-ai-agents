"""Cache Layer - Redis-backed portfolio state cache.

Maps to T-2.4 (Cache Layer Redis Integration) in TASKS.md.

WHEN trades execute
THEN the system SHALL:
  1. Update Redis cache with position data
  2. Maintain consistency with events
  3. Support fast reads (sub-millisecond)
  4. Handle cache failures gracefully
"""

import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

import redis.asyncio as aioredis
from prometheus_client import Counter, Histogram, Gauge

logger = logging.getLogger(__name__)

# Prometheus metrics (T-2.4.5: Metrics)
cache_hits = Counter(
    "cache_hits_total",
    "Total cache hits",
    ["key_pattern"]
)
cache_misses = Counter(
    "cache_misses_total",
    "Total cache misses",
    ["key_pattern"]
)
cache_latency_ms = Histogram(
    "cache_latency_ms",
    "Time to read/write from Redis",
    ["operation"],
    buckets=[0.5, 1, 5, 10, 50]
)
cache_size = Gauge(
    "cache_size_bytes",
    "Approximate size of cache in bytes"
)


class CacheLayer:
    """Redis-backed cache for real-time state.
    
    WHEN portfolio state needs to be read/updated
    THEN CacheLayer SHALL:
      1. Provide fast reads (< 5ms latency) (T-2.4.1)
      2. Keep cache consistent with events (T-2.4.2)
      3. Handle failures gracefully (T-2.4.4)
      4. Track cache metrics (T-2.4.5)
    
    Performance Target: Get/Set < 5ms latency (T-2.4)
    
    Key Structure:
        portfolio:{user_id}:positions → JSON list
        portfolio:{user_id}:balance → float
        portfolio:{user_id}:metrics → JSON dict
        state:{user_id}:{resource} → JSON
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        fallback_enabled: bool = True,
    ):
        """Initialize cache layer.
        
        Args:
            host: Redis host
            port: Redis port
            db: Database number
            password: Redis password
            fallback_enabled: If True, can fallback to DB when Redis unavailable
        """
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.fallback_enabled = fallback_enabled
        self.client: Optional[aioredis.Redis] = None
        self._available = False

    async def connect(self) -> None:
        """Connect to Redis."""
        try:
            self.client = await aioredis.from_url(
                f"redis://{self.host}:{self.port}/{self.db}",
                password=self.password,
                encoding="utf-8",
                decode_responses=True,
            )
            # Test connection
            await self.client.ping()
            self._available = True
            logger.info(f"Connected to Redis at {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self._available = False
            if not self.fallback_enabled:
                raise

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self.client:
            await self.client.close()
            logger.info("Disconnected from Redis")

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache.
        
        T-2.4.1: Get operation
        WHEN get() is called
        THEN system SHALL return cached value if available
        AND record cache hit/miss metrics
        
        Performance Target: < 5ms
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None
        """
        if not self._available or not self.client:
            return None

        import time
        start = time.time()

        try:
            value = await self.client.get(key)

            if value:
                cache_hits.labels(key_pattern=self._get_key_pattern(key)).inc()
                # Parse JSON if it looks like JSON
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    return value
            else:
                cache_misses.labels(key_pattern=self._get_key_pattern(key)).inc()
                return None

        except Exception as e:
            logger.error(f"Cache get error for {key}: {e}")
            cache_misses.labels(key_pattern=self._get_key_pattern(key)).inc()
            return None

        finally:
            latency = (time.time() - start) * 1000
            cache_latency_ms.labels(operation="get").observe(latency)

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """Set value in cache.
        
        T-2.4.1: Set operation
        WHEN set() is called
        THEN system SHALL store value in cache
        AND set TTL if provided
        
        Performance Target: < 5ms
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time to live in seconds (optional)
        
        Returns:
            bool: True if successful
        """
        if not self._available or not self.client:
            return False

        import time
        start = time.time()

        try:
            # Serialize to JSON
            if isinstance(value, str):
                serialized = value
            else:
                serialized = json.dumps(value)

            if ttl:
                await self.client.setex(key, ttl, serialized)
            else:
                await self.client.set(key, serialized)

            return True

        except Exception as e:
            logger.error(f"Cache set error for {key}: {e}")
            return False

        finally:
            latency = (time.time() - start) * 1000
            cache_latency_ms.labels(operation="set").observe(latency)

    async def delete(self, key: str) -> bool:
        """Delete value from cache.
        
        Args:
            key: Cache key
        
        Returns:
            bool: True if key existed
        """
        if not self._available or not self.client:
            return False

        try:
            deleted = await self.client.delete(key)
            return deleted > 0
        except Exception as e:
            logger.error(f"Cache delete error for {key}: {e}")
            return False

    async def get_all(self, pattern: str) -> Dict[str, Any]:
        """Get all keys matching pattern.
        
        T-2.4.1: Pattern matching
        
        Args:
            pattern: Key pattern (e.g., "portfolio:user_id:*")
        
        Returns:
            Dict of matching keys and values
        """
        if not self._available or not self.client:
            return {}

        try:
            keys = await self.client.keys(pattern)
            result = {}

            for key in keys:
                value = await self.get(key)
                if value:
                    result[key] = value

            return result

        except Exception as e:
            logger.error(f"Cache get_all error for {pattern}: {e}")
            return {}

    async def mget(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values.
        
        T-2.4.1: Multi-get operation
        
        Args:
            keys: List of cache keys
        
        Returns:
            Dict of found keys and values
        """
        if not self._available or not self.client:
            return {}

        try:
            values = await self.client.mget(keys)
            result = {}

            for key, value in zip(keys, values):
                if value:
                    try:
                        result[key] = json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        result[key] = value

            return result

        except Exception as e:
            logger.error(f"Cache mget error: {e}")
            return {}

    async def get_portfolio(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get cached portfolio state for user.
        
        T-2.4.2: Portfolio state caching
        
        WHEN portfolio state is needed
        THEN cache returns:
          - positions: list of open positions
          - balance: available balance
          - metrics: leverage, liquidation distance, etc.
        
        Args:
            user_id: User identifier
        
        Returns:
            Portfolio state dict or None
        """
        return await self.get(f"portfolio:{user_id}")

    async def update_portfolio(
        self,
        user_id: str,
        positions: List[Dict],
        balance: float,
        metrics: Dict[str, float],
        ttl: int = 3600,
    ) -> bool:
        """Update cached portfolio atomically.
        
        T-2.4.2: Atomic portfolio updates
        
        WHEN a trade executes
        THEN all portfolio state updates SHALL be atomic
        AND all fields updated within single operation
        
        Args:
            user_id: User identifier
            positions: List of open positions
            balance: Available balance
            metrics: Portfolio metrics (leverage, liquidation_distance, etc.)
            ttl: Time to live for cache
        
        Returns:
            bool: True if successful
        """
        portfolio_data = {
            "user_id": user_id,
            "positions": positions,
            "balance": balance,
            "metrics": metrics,
            "updated_at": datetime.utcnow().isoformat(),
        }

        return await self.set(
            f"portfolio:{user_id}",
            portfolio_data,
            ttl=ttl,
        )

    async def invalidate_user_cache(self, user_id: str) -> int:
        """Invalidate all cache entries for a user.
        
        WHEN portfolio state becomes stale
        THEN cache SHALL be invalidated to force refresh
        
        Args:
            user_id: User identifier
        
        Returns:
            int: Number of keys deleted
        """
        if not self._available or not self.client:
            return 0

        try:
            pattern = f"portfolio:{user_id}:*"
            keys = await self.client.keys(pattern)
            if keys:
                return await self.client.delete(*keys)
            return 0

        except Exception as e:
            logger.error(f"Cache invalidate error for {user_id}: {e}")
            return 0

    def is_available(self) -> bool:
        """Check if cache is available.
        
        T-2.4.4: Fallback support
        
        Returns:
            bool: True if Redis is available
        """
        return self._available

    @staticmethod
    def _get_key_pattern(key: str) -> str:
        """Extract pattern from key for metrics.
        
        Example: "portfolio:user123:positions" → "portfolio:*:positions"
        """
        parts = key.split(":")
        if len(parts) > 1:
            parts[1] = "*"
        return ":".join(parts)

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
