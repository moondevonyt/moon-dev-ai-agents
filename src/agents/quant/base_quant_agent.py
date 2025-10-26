"""
🌙 Moon Dev's Base Quantitative Agent
Base class for all quantitative trading agents

Extends the existing BaseAgent with quantitative-specific functionality
including event handling, statistical utilities, and Redis caching.
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from termcolor import cprint

from src.agents.base_agent import BaseAgent
from src.core.event_consumer import EventConsumer
from src.core.event_producer import EventProducer
from src.core.cache_layer import CacheLayer
from src.core.models import Event, EventType


class BaseQuantAgent(BaseAgent):
    """Base class for quantitative agents with event-driven capabilities."""
    
    def __init__(self, agent_type: str, subscribed_topics: list[str] = None):
        """
        Initialize base quantitative agent.
        
        Args:
            agent_type: Type of agent (e.g., 'anomaly_detection', 'signal_aggregation')
            subscribed_topics: List of Kafka topics to subscribe to
        """
        super().__init__(agent_type, use_exchange_manager=False)
        
        # Event infrastructure
        self.event_consumer = None
        self.event_producer = None
        self.cache = None
        self.subscribed_topics = subscribed_topics or []
        
        # Event handlers registry
        self._event_handlers: Dict[EventType, Callable] = {}
        
        # Agent state
        self.is_running = False
        self.loop = None
        
        cprint(f"✅ {agent_type.capitalize()} quantitative agent initialized", "green")
    
    async def initialize(self):
        """Initialize event infrastructure (Kafka, Redis, etc.)."""
        try:
            # Initialize event consumer
            if self.subscribed_topics:
                self.event_consumer = EventConsumer(
                    topics=self.subscribed_topics,
                    group_id=f"{self.type}_group"
                )
                await self.event_consumer.start()
                cprint(f"✅ Event consumer started for topics: {self.subscribed_topics}", "green")
            
            # Initialize event producer
            self.event_producer = EventProducer()
            await self.event_producer.start()
            cprint(f"✅ Event producer started", "green")
            
            # Initialize cache layer
            self.cache = CacheLayer()
            await self.cache.connect()
            cprint(f"✅ Redis cache connected", "green")
            
        except Exception as e:
            cprint(f"❌ Failed to initialize {self.type} agent: {str(e)}", "red")
            raise
    
    async def shutdown(self):
        """Gracefully shutdown agent and close connections."""
        self.is_running = False
        
        try:
            if self.event_consumer:
                await self.event_consumer.stop()
            if self.event_producer:
                await self.event_producer.stop()
            if self.cache:
                await self.cache.disconnect()
            
            cprint(f"✅ {self.type} agent shutdown complete", "green")
        except Exception as e:
            cprint(f"⚠️ Error during shutdown: {str(e)}", "yellow")
    
    def event_handler(self, event_type: EventType):
        """
        Decorator to register event handlers.
        
        Usage:
            @event_handler(EventType.PRICE_TICK)
            async def handle_price_tick(self, event: Event):
                # Handle price tick event
                pass
        """
        def decorator(func: Callable):
            self._event_handlers[event_type] = func
            return func
        return decorator
    
    async def process_event(self, event: Event):
        """
        Process incoming event by routing to appropriate handler.
        
        Args:
            event: Event to process
        """
        handler = self._event_handlers.get(event.event_type)
        if handler:
            try:
                await handler(self, event)
            except Exception as e:
                cprint(f"❌ Error processing {event.event_type}: {str(e)}", "red")
        else:
            cprint(f"⚠️ No handler registered for {event.event_type}", "yellow")
    
    async def emit_event(self, event_type: EventType, token: Optional[str], 
                        data: Dict[str, Any], correlation_id: Optional[str] = None):
        """
        Emit an event to Kafka.
        
        Args:
            event_type: Type of event to emit
            token: Token symbol for partition routing
            data: Event payload
            correlation_id: Optional correlation ID for tracing
        """
        event = Event(
            event_type=event_type,
            token=token,
            source=f"agent.{self.type}",
            data=data,
            correlation_id=correlation_id
        )
        
        await self.event_producer.publish(event)
    
    async def run_event_loop(self):
        """Main event processing loop."""
        self.is_running = True
        
        try:
            while self.is_running:
                if self.event_consumer:
                    # Consume events from Kafka
                    events = await self.event_consumer.consume(timeout=1.0)
                    
                    for event in events:
                        await self.process_event(event)
                else:
                    # No consumer, just sleep
                    await asyncio.sleep(1.0)
                    
        except Exception as e:
            cprint(f"❌ Error in event loop: {str(e)}", "red")
            raise
    
    def run(self):
        """
        Run the agent (synchronous entry point).
        Override this in child classes for custom behavior.
        """
        self.loop = asyncio.get_event_loop()
        
        try:
            # Initialize
            self.loop.run_until_complete(self.initialize())
            
            # Run event loop
            self.loop.run_until_complete(self.run_event_loop())
            
        except KeyboardInterrupt:
            cprint(f"\n⚠️ {self.type} agent interrupted by user", "yellow")
        finally:
            # Shutdown
            self.loop.run_until_complete(self.shutdown())
