"""Kafka Event Consumer - subscribes to and processes events.

Maps to T-2.2 (Kafka Consumer Framework) in TASKS.md.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Callable, Dict, Optional, List
from datetime import datetime

from kafka import KafkaConsumer
from kafka.errors import KafkaError
from prometheus_client import Counter, Histogram, Gauge

from .models import Event, EventType

logger = logging.getLogger(__name__)

# Prometheus metrics (T-2.2.5: Monitoring)
messages_consumed = Counter(
    "kafka_messages_consumed_total",
    "Total messages consumed from Kafka",
    ["topic", "event_type"]
)
messages_failed = Counter(
    "kafka_messages_failed_total",
    "Total messages that failed processing",
    ["topic", "event_type"]
)
consumer_lag = Gauge(
    "kafka_consumer_lag",
    "Current consumer lag in messages",
    ["consumer_group", "topic"]
)
process_latency_ms = Histogram(
    "kafka_process_latency_ms",
    "Time to process message after consumption",
    ["topic"],
    buckets=[1, 5, 10, 50, 100, 500, 1000]
)


class EventConsumer(ABC):
    """Base class for Kafka event consumers.
    
    WHEN developer creates Kafka consumer
    THEN the system SHALL:
      1. Abstract Kafka consumer API (T-2.2.1)
      2. Provide automatic offset management (T-2.2.2)
      3. Handle consumer group rebalancing
      4. Handle errors gracefully (T-2.2.3)
      5. Support async processing (T-2.2.4)
      6. Emit metrics and logs (T-2.2.5)
    
    Performance Target: Message processing < 100ms latency (T-2.2)
    
    Usage:
        class MyEventConsumer(EventConsumer):
            @EventConsumer.event_handler(EventType.PRICE_TICK)
            async def handle_price_tick(self, event: Event) -> None:
                # Process price tick
                pass
    """

    # Class-level registry of event handlers
    _handlers: Dict[EventType, Callable] = {}

    def __init__(
        self,
        bootstrap_servers: list[str] = None,
        group_id: str = "default_group",
        topics: list[str] = None,
        auto_offset_reset: str = "latest",
    ):
        """Initialize Kafka consumer.
        
        Args:
            bootstrap_servers: Kafka broker addresses
            group_id: Consumer group ID for coordinating consumers
            topics: Topics to subscribe to
            auto_offset_reset: Where to start reading if no offset exists
        """
        self.bootstrap_servers = bootstrap_servers or ['localhost:9092']
        self.group_id = group_id
        self.topics = topics or []
        self.auto_offset_reset = auto_offset_reset
        self._running = False
        self._tasks: List[asyncio.Task] = []

        # T-2.2.1: Create Kafka consumer
        self.consumer = KafkaConsumer(
            *self.topics,
            bootstrap_servers=self.bootstrap_servers,
            group_id=group_id,
            auto_offset_reset=auto_offset_reset,
            enable_auto_commit=False,  # Manual commit for control
            value_deserializer=self._deserialize,
            max_poll_records=100,
            session_timeout_ms=30000,
        )

    @staticmethod
    def event_handler(event_type: EventType):
        """Decorator to register an event handler.
        
        T-2.2.1: Decorator pattern for event routing
        
        Example:
            @EventConsumer.event_handler(EventType.PRICE_TICK)
            async def handle_price(self, event: Event):
                pass
        """
        def decorator(func: Callable) -> Callable:
            EventConsumer._handlers[event_type] = func
            return func
        return decorator

    async def start(self) -> None:
        """Start consuming and processing events.
        
        WHEN consumer.start() is called
        THEN consumer SHALL continuously read from Kafka
        AND route to appropriate event handlers
        AND manage offsets after successful processing
        """
        self._running = True
        logger.info(f"Starting consumer {self.group_id}")

        try:
            while self._running:
                # T-2.2.2: Consume messages with auto-commit disabled
                messages = self.consumer.poll(timeout_ms=1000)

                for topic_partition, records in messages.items():
                    for record in records:
                        try:
                            # Deserialize event
                            event_data = record.value
                            event_type = EventType(event_data.get('event_type'))
                            event = Event(**event_data)

                            # T-2.2.1: Route to appropriate handler
                            start_time = datetime.utcnow()
                            await self._route_event(event)
                            latency = (datetime.utcnow() - start_time).total_seconds() * 1000

                            # Record metrics (T-2.2.5)
                            messages_consumed.labels(
                                topic=topic_partition.topic,
                                event_type=event_type.value
                            ).inc()
                            process_latency_ms.labels(
                                topic=topic_partition.topic
                            ).observe(latency)

                            # T-2.2.2: Commit offset after successful processing
                            self.consumer.commit()

                        except Exception as e:
                            # T-2.2.3: Error handling
                            messages_failed.labels(
                                topic=topic_partition.topic,
                                event_type="unknown"
                            ).inc()
                            logger.error(f"Error processing event: {e}")

                            # Optionally send to dead-letter queue
                            await self._handle_failed_event(record, e)

        except KafkaError as e:
            logger.error(f"Kafka consumer error: {e}")
            raise
        finally:
            self.stop()

    async def _route_event(self, event: Event) -> None:
        """Route event to appropriate handler.
        
        WHEN event is received
        THEN it SHALL be routed to handler for its event_type
        AND handler SHALL be awaited
        """
        handler = self._handlers.get(event.event_type)

        if handler:
            # T-2.2.4: Support async processing
            if asyncio.iscoroutinefunction(handler):
                await handler(self, event)
            else:
                # Run sync handler in thread pool to not block consumer
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, handler, self, event)
        else:
            logger.warning(f"No handler for event type: {event.event_type}")

    async def _handle_failed_event(self, record: Any, error: Exception) -> None:
        """Handle failed event processing.
        
        T-2.2.3: On repeated failures, send to dead-letter queue
        Can be overridden by subclasses for custom handling.
        
        Args:
            record: The Kafka message record
            error: The exception that occurred
        """
        logger.error(
            f"Failed event - Topic: {record.topic}, "
            f"Partition: {record.partition}, "
            f"Offset: {record.offset}, "
            f"Error: {error}"
        )
        # TODO: Send to DLQ topic for later analysis

    def stop(self) -> None:
        """Stop the consumer."""
        self._running = False
        logger.info(f"Stopping consumer {self.group_id}")

        try:
            self.consumer.close(timeout_ms=10000)
        except Exception as e:
            logger.error(f"Error closing consumer: {e}")

    def subscribe(self, topics: list[str]) -> None:
        """Subscribe to additional topics.
        
        WHEN subscribe is called
        THEN consumer SHALL add topics to subscription
        AND rebalancing MAY trigger
        """
        self.consumer.subscribe(topics)
        logger.info(f"Subscribed to topics: {topics}")

    def unsubscribe(self) -> None:
        """Unsubscribe from all topics."""
        self.consumer.unsubscribe()
        logger.info("Unsubscribed from all topics")

    @staticmethod
    def _deserialize(data: bytes) -> Dict:
        """Deserialize event from JSON bytes.
        
        T-2.2: Event deserialization
        """
        import json
        return json.loads(data.decode('utf-8'))

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        self.stop()
