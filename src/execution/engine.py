"""ExecutionEngine - Orchestrates order submission and monitoring.

Maps to T-3.4 (Execution Engine) in TASKS.md.

WHEN trade signals are approved
THEN Execution Engine SHALL:
  1. Validate all risk constraints
  2. Calculate position sizing
  3. Submit orders to exchange
  4. Monitor fills
  5. Update state on execution
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from prometheus_client import Counter, Histogram

from ..core import EventProducer, CacheLayer
from ..core.models import Event, EventType
from .risk_validator import RiskValidator
from .exchange_adapter import ExchangeAdapter, ExchangeType

logger = logging.getLogger(__name__)

# Prometheus metrics
orders_submitted = Counter(
    "orders_submitted_total",
    "Total orders submitted",
    ["exchange", "direction"]
)
order_latency_ms = Histogram(
    "order_latency_ms",
    "Order submission latency",
    ["exchange"],
    buckets=[10, 50, 100, 200, 500]
)
fills_recorded = Counter(
    "fills_recorded_total",
    "Total fills recorded",
    ["exchange"]
)
trade_errors = Counter(
    "trade_errors_total",
    "Total trade errors",
    ["error_type"]
)


class ExecutionEngine:
    """Trade execution orchestrator.
    
    WHEN trade signals are received
    THEN Execution Engine SHALL:
      1. Validate risk constraints (T-3.4.2)
      2. Calculate position size (T-3.4.3)
      3. Submit orders (T-3.4.4, T-3.4.5)
      4. Monitor fills (T-3.4.6)
      5. Update portfolio state
      6. Emit trade.executed event
    
    Performance Target: <100ms from signal to order submission (T-3.4)
    
    Latency Breakdown:
      - Risk validation: <5ms
      - Position sizing: <1ms
      - Order submission: <50ms
      - Fill monitoring: <100ms
      - Total: <100ms
    """

    def __init__(
        self,
        producer: EventProducer,
        cache_layer: CacheLayer,
        hyperliquid_key: Optional[str] = None,
        solana_rpc: Optional[str] = None,
    ):
        """Initialize execution engine.
        
        Args:
            producer: EventProducer for emitting events
            cache_layer: CacheLayer for state updates
            hyperliquid_key: HyperLiquid API key
            solana_rpc: Solana RPC endpoint
        """
        self.producer = producer
        self.cache = cache_layer

        # Risk validator
        self.validator = RiskValidator()

        # Exchange adapters
        self.exchanges = {
            ExchangeType.HYPERLIQUID: ExchangeAdapter(
                ExchangeType.HYPERLIQUID,
                api_key=hyperliquid_key,
            ),
            ExchangeType.SOLANA: ExchangeAdapter(
                ExchangeType.SOLANA,
                rpc_endpoint=solana_rpc,
            ),
        }

        # Trade tracking
        self.active_trades: Dict[str, Dict[str, Any]] = {}

        logger.info("ExecutionEngine initialized")

    async def execute_signal(
        self,
        signal_event: Event,
        portfolio: Dict[str, Any],
    ) -> bool:
        """Execute a trading signal.
        
        T-3.4: Complete Trade Execution
        
        WHEN signal.generated event received
        THEN Execution Engine SHALL:
          1. Validate constraints (<5ms)
          2. Calculate position size (<1ms)
          3. Submit order (<50ms)
          4. Emit trade.placed event
          5. Monitor fill (<100ms)
          6. Emit trade.executed event
          7. Update cache
        
        Args:
            signal_event: signal.generated event
            portfolio: Current portfolio state
        
        Returns:
            True if order submitted successfully
        """
        import time
        start_time = time.time()

        try:
            signal_data = signal_event.data
            token = signal_event.token
            direction = signal_data.get('direction')
            confidence = signal_data.get('confidence', 0.5)

            if not direction or not token:
                logger.warning(f"Invalid signal: {signal_data}")
                return False

            logger.info(
                f"Executing signal for {token}: {direction} "
                f"(confidence: {confidence:.2f})"
            )

            # Step 1: Validate risk constraints (T-3.4.2)
            is_valid, reason = self.validator.validate_trade(
                token=token,
                direction=direction,
                size=1.0,  # Will be recalculated
                entry_price=100.0,  # Placeholder
                portfolio=portfolio,
            )

            if not is_valid:
                logger.warning(f"Trade validation failed: {reason}")
                trade_errors.labels(error_type="validation_failed").inc()

                await self._emit_trade_rejected(
                    token=token,
                    reason=reason,
                )
                return False

            # Step 2: Calculate position size (T-3.4.3)
            position_size = self.validator.calculate_position_size(
                portfolio=portfolio,
                signal_confidence=confidence,
                method="fixed_pct",
            )

            logger.info(f"Calculated position size: {position_size}")

            # Determine exchange (simplified: use HyperLiquid for futures)
            exchange = self.exchanges[ExchangeType.HYPERLIQUID]

            # Step 3: Submit order (T-3.4.4, T-3.4.5)
            order_result = await self._submit_order(
                exchange=exchange,
                token=token,
                direction=direction,
                size=position_size,
                confidence=confidence,
            )

            if not order_result:
                return False

            # Step 4: Monitor fill and update state
            await self._monitor_fill_and_update_state(
                order_result=order_result,
                token=token,
                direction=direction,
                size=position_size,
                portfolio=portfolio,
            )

            # Record latency
            latency = (time.time() - start_time) * 1000
            order_latency_ms.labels(exchange=exchange.exchange_type.value).observe(latency)

            logger.info(f"Trade executed successfully in {latency:.1f}ms")
            return True

        except Exception as e:
            logger.error(f"Trade execution failed: {e}", exc_info=True)
            trade_errors.labels(error_type="execution_error").inc()
            return False

    async def _submit_order(
        self,
        exchange: ExchangeAdapter,
        token: str,
        direction: str,
        size: float,
        confidence: float,
    ) -> Optional[Dict[str, Any]]:
        """Submit order to exchange.
        
        T-3.4.4: Order Submission
        
        Args:
            exchange: ExchangeAdapter instance
            token: Trading pair
            direction: LONG or SHORT
            size: Position size
            confidence: Signal confidence
        
        Returns:
            Order result dict or None if failed
        """
        try:
            order = await exchange.submit_order(
                token=token,
                direction=direction,
                size=size,
                order_type="MARKET",
            )

            logger.info(f"Order submitted: {order}")

            orders_submitted.labels(
                exchange=exchange.exchange_type.value,
                direction=direction,
            ).inc()

            # Emit trade.placed event
            await self._emit_trade_placed(
                token=token,
                order_id=order.get('order_id'),
                direction=direction,
                size=size,
            )

            return order

        except Exception as e:
            logger.error(f"Order submission failed: {e}")
            trade_errors.labels(error_type="order_submission_failed").inc()
            return None

    async def _monitor_fill_and_update_state(
        self,
        order_result: Dict[str, Any],
        token: str,
        direction: str,
        size: float,
        portfolio: Dict[str, Any],
    ) -> None:
        """Monitor fill and update portfolio state.
        
        T-3.4.6: Fill Monitoring and State Updates
        
        WHEN order is filled
        THEN update cache and emit events
        
        Args:
            order_result: Order submission result
            token: Trading pair
            direction: LONG or SHORT
            size: Position size
            portfolio: Portfolio state
        """
        # In production, would wait for actual fill
        # For now, simulate immediate fill
        await asyncio.sleep(0.05)  # Simulate 50ms

        order_id = order_result.get('order_id')
        exchange_type = order_result.get('exchange', 'hyperliquid')

        # Simulate fill
        fill_price = 43250.0  # Mock price
        filled_amount = size

        # Update portfolio state
        if token not in portfolio.get('positions', {}):
            portfolio['positions'][token] = {
                "size": 0,
                "entry_price": fill_price,
                "direction": direction,
            }

        position = portfolio['positions'][token]
        position['size'] = filled_amount
        position['current_price'] = fill_price

        # Calculate fee (0.1% for maker, 0.05% for taker)
        fee = filled_amount * fill_price * 0.001

        # Update balance
        portfolio['balance'] -= fee

        # Update cache
        await self.cache.update_portfolio(
            user_id="default",
            positions=list(portfolio['positions'].values()),
            balance=portfolio['balance'],
            metrics={
                "leverage_ratio": 1.0,
                "liquidation_distance": 0.5,
            },
        )

        # Emit trade.executed event
        await self._emit_trade_executed(
            order_id=order_id,
            token=token,
            fill_price=fill_price,
            filled_amount=filled_amount,
            fee=fee,
        )

        fills_recorded.labels(exchange=exchange_type).inc()

        logger.info(
            f"Trade executed: {token} {direction} {filled_amount} "
            f"@ ${fill_price:,.2f}"
        )

    async def _emit_trade_placed(
        self,
        token: str,
        order_id: str,
        direction: str,
        size: float,
    ) -> None:
        """Emit trade.placed event.
        
        Args:
            token: Trading pair
            order_id: Order ID
            direction: LONG or SHORT
            size: Position size
        """
        event = Event(
            event_type=EventType.TRADE_PLACED,
            token=token,
            source="execution_engine",
            data={
                "order_id": order_id,
                "direction": direction,
                "size": size,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        await asyncio.to_thread(self.producer.publish, event)

    async def _emit_trade_executed(
        self,
        order_id: str,
        token: str,
        fill_price: float,
        filled_amount: float,
        fee: float,
    ) -> None:
        """Emit trade.executed event.
        
        T-3.4: Trade Execution Event
        
        Args:
            order_id: Order ID
            token: Trading pair
            fill_price: Fill price
            filled_amount: Filled amount
            fee: Trading fee
        """
        event = Event(
            event_type=EventType.TRADE_EXECUTED,
            token=token,
            source="execution_engine",
            data={
                "order_id": order_id,
                "fill_price": fill_price,
                "filled_amount": filled_amount,
                "fee": fee,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        await asyncio.to_thread(self.producer.publish, event)

    async def _emit_trade_rejected(
        self,
        token: str,
        reason: str,
    ) -> None:
        """Emit trade rejection event.
        
        Args:
            token: Trading pair
            reason: Rejection reason
        """
        event = Event(
            event_type=EventType.RISK_ALERT,
            token=token,
            source="execution_engine",
            data={
                "alert_type": "trade_rejected",
                "reason": reason,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        await asyncio.to_thread(self.producer.publish, event)
