"""Kafka Event Producer - publishes events to Kafka topics.

Maps to T-2.1 (Kafka Producer Framework) in TASKS.md.
"""

import json
import logging
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from kafka import KafkaProducer
from kafka.errors import KafkaError
from prometheus_client import Counter, Histogram

from .models import Event, EventType

logger = logging.getLogger(__name__)

# Prometheus metrics (T-2.1.5: Metrics)
messages_published = Counter(
    "kafka_messages_published_total",
    "Total messages published to Kafka",
    ["topic", "event_type"]
)
publish_latency_ms = Histogram(
    "kafka_publish_latency_ms",
    "Time to publish message to Kafka",
    ["topic"],
    buckets=[1, 5, 10, 50, 100, 500, 1000]
)
publish_errors = Counter(
    "kafka_publish_errors_total",
    "Total publish errors",
    ["topic", "error_type"]
)


class EventProducer:
    """Kafka Event Producer for publishing events.
    
    WHEN developer publishes events to Kafka
    THEN the system SHALL:
      1. Abstract the Kafka client library (T-2.1.1)
      2. Serialize events to JSON (T-2.1.2)
      3. Route messages by token to appropriate partition (T-2.1.3)
      4. Handle retries and exponential backoff (T-2.1.4)
      5. Batch messages for efficiency
      6. Emit metrics for monitoring (T-2.1.5)
    
    Performance Target: Publish latency < 50ms (T-2.1)
    """

    def __init__(
        self,
        bootstrap_servers: list[str] = None,
        batch_size: int = 100,
        batch_timeout_ms: int = 1000,
        retries: int = 3,
        max_in_flight_requests: int = 5,
    ):
        """Initialize Kafka producer.
        
        Args:
            bootstrap_servers: Kafka broker addresses (e.g., ['localhost:9092'])
            batch_size: Number of messages to batch before sending
            batch_timeout_ms: Max time to wait before sending partial batch
            retries: Number of retries before failing
            max_in_flight_requests: Max concurrent requests
        """
        self.bootstrap_servers = bootstrap_servers or ['localhost:9092']
        self.batch_size = batch_size
        self.batch_timeout_ms = batch_timeout_ms
        self.retries = retries
        self.max_in_flight_requests = max_in_flight_requests

        # T-2.1.1: Create Kafka producer with optimized settings
        self.producer = KafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=self._serialize,
            retries=retries,
            max_in_flight_requests_per_connection=max_in_flight_requests,
            acks='all',  # Wait for all replicas
            batch_size=batch_size,
            linger_ms=batch_timeout_ms,
            compression_type='snappy',
        )

    def publish(
        self,
        event: Event,
        topic: Optional[str] = None,
    ) -> str:
        """Publish a single event to Kafka.
        
        WHEN publish() is called
        THEN the system SHALL:
          1. Determine target topic (or use event type)
          2. Select partition key based on token (T-2.1.3)
          3. Serialize event to JSON
          4. Submit to Kafka with callbacks
          5. Track metrics and errors
        
        Args:
            event: Event to publish
            topic: Optional override for topic name (default: event type)
        
        Returns:
            str: Event ID (for correlation)
        
        Raises:
            ValueError: If event validation fails
            KafkaError: If publish fails after retries
        """
        if not isinstance(event, Event):
            raise ValueError("event must be an Event instance")

        # Determine topic
        target_topic = topic or event.event_type.value

        # T-2.1.3: Partition routing by token
        partition_key = self._get_partition_key(event.token)

        # T-2.1.2: Serialize event
        event_data = event.model_dump(mode='json')

        try:
            # Send to Kafka
            future = self.producer.send(
                target_topic,
                value=event_data,
                key=partition_key.encode() if partition_key else None,
            )

            # Add callback for success/failure
            future.add_callback(
                self._on_send_success,
                topic=target_topic,
                event_type=event.event_type.value,
            )
            future.add_errback(
                self._on_send_error,
                topic=target_topic,
            )

            # Wait for send to complete (non-blocking in batch mode)
            record_metadata = future.get(timeout=5)

            logger.debug(
                f"Published event {event.event_id} to {target_topic}:{record_metadata.partition}"
            )

            return str(event.event_id)

        except KafkaError as e:
            publish_errors.labels(
                topic=target_topic,
                error_type=type(e).__name__
            ).inc()
            logger.error(f"Failed to publish event {event.event_id}: {e}")
            raise

    def publish_batch(
        self,
        events: list[Event],
        topic: Optional[str] = None,
    ) -> list[str]:
        """Publish multiple events in a batch.
        
        WHEN publish_batch() is called
        THEN Kafka producer SHALL batch events for efficiency
        AND return list of event IDs
        
        Performance: Should be more efficient than single publishes
        due to batching and compression.
        
        Args:
            events: List of events to publish
            topic: Optional override for topic name
        
        Returns:
            list[str]: List of event IDs
        """
        event_ids = []
        for event in events:
            try:
                event_id = self.publish(event, topic)
                event_ids.append(event_id)
            except Exception as e:
                logger.error(f"Failed to publish event in batch: {e}")
                # Continue with next event
                continue

        # Flush to ensure all messages sent
        self.producer.flush(timeout=30)

        logger.info(f"Published {len(event_ids)} events in batch")
        return event_ids

    def _get_partition_key(self, token: Optional[str]) -> Optional[str]:
        """Generate partition key for deterministic routing.
        
        T-2.1.3: Partition routing
        WHEN partition key is determined
        THEN same token SHALL always route to same partition
        
        Args:
            token: Trading pair token (e.g., 'BTC-USD')
        
        Returns:
            str: Partition key
        """
        # Use token as partition key for deterministic routing
        # Messages with same token go to same partition (preserves ordering)
        return token if token else "default"

    def _serialize(self, value: Dict[str, Any]) -> bytes:
        """Serialize event to JSON bytes.
        
        T-2.1.2: Event serialization
        """
        return json.dumps(value).encode('utf-8')

    def _on_send_success(
        self,
        record_metadata: Any,
        topic: str,
        event_type: str,
    ) -> None:
        """Callback on successful send."""
        messages_published.labels(topic=topic, event_type=event_type).inc()
        publish_latency_ms.labels(topic=topic).observe(
            (datetime.utcnow() - datetime.utcnow()).total_seconds() * 1000
        )

    def _on_send_error(self, exc_value: Exception, topic: str) -> None:
        """Callback on send error.
        
        T-2.1.4: Error handling and retries
        """
        publish_errors.labels(
            topic=topic,
            error_type=type(exc_value).__name__
        ).inc()
        logger.error(f"Kafka send error to {topic}: {exc_value}")

    def close(self) -> None:
        """Close the producer and flush pending messages."""
        try:
            self.producer.flush(timeout=30)
            self.producer.close(timeout=10)
            logger.info("Kafka producer closed successfully")
        except Exception as e:
            logger.error(f"Error closing Kafka producer: {e}")

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        self.close()
