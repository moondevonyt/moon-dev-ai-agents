"""BacktestEngine - Orchestrates historical event replay and backtesting.

Maps to DESIGN.md User Story 3: Event Replay for Backtesting

WHEN a user initiates a backtest run with historical date range
THEN the system SHALL:
  1. Query EventStore for all events in that date range
  2. Deserialize and normalize all historical events
  3. FOR each event in chronological order:
     - Publish to isolated Kafka instance
     - All subscribed agents process event as if live
     - Record all emitted events and trade executions
     - Calculate performance metrics (returns, Sharpe, drawdown)
  4. Generate comprehensive backtest report
  5. Save report to event store for auditing
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import uuid4

from ..core import EventStore, CacheLayer
from ..core.models import Event, EventType
from .calculator import PerformanceCalculator
from .report import BacktestReport

logger = logging.getLogger(__name__)


class BacktestEngine:
    """Historical event replay engine for strategy backtesting.
    
    WHEN a backtest is executed
    THEN the system SHALL:
      1. Retrieve historical events from EventStore
      2. Replay events through agents in chronological order
      3. Record all trades and performance metrics
      4. Generate comprehensive backtest report
      5. Execute >100x real-time speed
    
    Performance Targets:
      - Event replay speed: >100x real-time (1 hour of data in <36 seconds)
      - Memory efficiency: Handle 6+ months of data
      - Accuracy: Identical results to live trading
    """

    def __init__(
        self,
        event_store: EventStore,
        cache_layer: Optional[CacheLayer] = None,
    ):
        """Initialize backtesting engine.
        
        Args:
            event_store: EventStore instance for querying historical events
            cache_layer: Optional CacheLayer for state management
        """
        self.event_store = event_store
        self.cache_layer = cache_layer or CacheLayer()
        self.backtest_id = str(uuid4())
        
        # Backtest state
        self.trades: List[Dict[str, Any]] = []
        self.events_processed = 0
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None

    async def run_backtest(
        self,
        start_date: datetime,
        end_date: datetime,
        initial_balance: float = 50000.0,
        tokens: Optional[List[str]] = None,
        agents: Optional[List[str]] = None,
    ) -> "BacktestResults":
        """Execute a backtest run.
        
        WHEN backtest.run() is called
        THEN the system SHALL:
          1. Query EventStore for events in date range
          2. Initialize portfolio with initial_balance
          3. Replay each event through agents
          4. Record all trades
          5. Calculate performance metrics
          6. Return BacktestResults
        
        Args:
            start_date: Backtest start date
            end_date: Backtest end date
            initial_balance: Starting portfolio balance
            tokens: Optional token filter (default: all)
            agents: Optional agent filter (default: all)
        
        Returns:
            BacktestResults with performance metrics and trades
        """
        import time
        backtest_start = time.time()

        logger.info(
            f"Starting backtest {self.backtest_id} "
            f"from {start_date} to {end_date}"
        )

        try:
            # Initialize backtest state
            self.start_time = start_date
            self.end_time = end_date
            self.trades = []
            self.events_processed = 0

            # Initialize portfolio
            portfolio = {
                "balance": initial_balance,
                "positions": {},
                "trades": [],
                "timestamp": start_date,
            }

            # Query historical events from EventStore
            logger.info(f"Querying events from {start_date} to {end_date}")
            events = await self.event_store.query_by_date_range(
                start_date,
                end_date,
                limit=1000000,
            )

            logger.info(f"Retrieved {len(events)} historical events")

            # Replay events through agent simulation
            for event_data in events:
                try:
                    # Parse event
                    event_dict = dict(event_data) if hasattr(event_data, '__iter__') else event_data
                    
                    # Filter by token if specified
                    if tokens and event_dict.get('token') not in tokens:
                        continue

                    # Process event through agent simulation
                    await self._process_event(
                        event_dict,
                        portfolio,
                        agents,
                    )

                    self.events_processed += 1

                except Exception as e:
                    logger.error(f"Error processing event: {e}")
                    continue

            # Calculate performance metrics
            calculator = PerformanceCalculator(
                trades=self.trades,
                initial_balance=initial_balance,
                start_date=start_date,
                end_date=end_date,
            )

            backtest_time = time.time() - backtest_start
            replay_speed = (end_date - start_date).total_seconds() / backtest_time

            logger.info(
                f"Backtest complete: "
                f"{self.events_processed} events in {backtest_time:.1f}s "
                f"({replay_speed:.0f}x real-time)"
            )

            return BacktestResults(
                backtest_id=self.backtest_id,
                start_date=start_date,
                end_date=end_date,
                initial_balance=initial_balance,
                trades=self.trades,
                portfolio_state=portfolio,
                events_processed=self.events_processed,
                backtest_time=backtest_time,
                calculator=calculator,
            )

        except Exception as e:
            logger.error(f"Backtest failed: {e}", exc_info=True)
            raise

    async def _process_event(
        self,
        event_dict: Dict[str, Any],
        portfolio: Dict[str, Any],
        agent_filters: Optional[List[str]] = None,
    ) -> None:
        """Process a single event during replay.
        
        Simulates agent processing and trade execution.
        
        Args:
            event_dict: Event data
            portfolio: Current portfolio state
            agent_filters: Optional agent name filters
        """
        event_type = event_dict.get('event_type')
        token = event_dict.get('token')

        # Simulate agent processing based on event type
        if event_type == EventType.PRICE_TICK.value:
            await self._handle_price_tick(event_dict, portfolio)

        elif event_type == EventType.SIGNAL_GENERATED.value:
            if not agent_filters or event_dict.get('source') in agent_filters:
                await self._handle_signal(event_dict, portfolio)

        elif event_type == EventType.TRADE_EXECUTED.value:
            await self._handle_trade_executed(event_dict, portfolio)

        elif event_type == EventType.POSITION_CLOSED.value:
            await self._handle_position_closed(event_dict, portfolio)

    async def _handle_price_tick(
        self,
        event_dict: Dict[str, Any],
        portfolio: Dict[str, Any],
    ) -> None:
        """Handle price tick event.
        
        Updates mark prices for open positions.
        
        Args:
            event_dict: Price tick event
            portfolio: Portfolio state
        """
        price = event_dict.get('data', {}).get('price')
        token = event_dict.get('token')

        if price and token and token in portfolio.get('positions', {}):
            # Update unrealized PnL for position
            position = portfolio['positions'][token]
            position['current_price'] = price
            position['unrealized_pnl'] = (price - position['entry_price']) * position['size']

    async def _handle_signal(
        self,
        event_dict: Dict[str, Any],
        portfolio: Dict[str, Any],
    ) -> None:
        """Handle trading signal event.
        
        Simulates trade execution on signals.
        
        Args:
            event_dict: Signal generated event
            portfolio: Portfolio state
        """
        signal_data = event_dict.get('data', {})
        direction = signal_data.get('direction')
        confidence = signal_data.get('confidence', 0.5)
        token = event_dict.get('token')

        if not direction or not token or confidence < 0.6:
            return

        # Simulate trade execution
        await self._execute_simulated_trade(
            token=token,
            direction=direction,
            confidence=confidence,
            portfolio=portfolio,
            signal_source=event_dict.get('source', 'unknown'),
        )

    async def _handle_trade_executed(
        self,
        event_dict: Dict[str, Any],
        portfolio: Dict[str, Any],
    ) -> None:
        """Handle trade executed event.
        
        Records trade and updates portfolio.
        
        Args:
            event_dict: Trade executed event
            portfolio: Portfolio state
        """
        trade_data = event_dict.get('data', {})
        token = event_dict.get('token')
        fill_price = trade_data.get('fill_price')
        size = trade_data.get('filled_amount', 0)

        if not token or not fill_price:
            return

        # Record trade
        trade = {
            "token": token,
            "entry_price": fill_price,
            "size": size,
            "timestamp": event_dict.get('timestamp'),
            "source": "simulated",
        }

        self.trades.append(trade)

        # Update portfolio
        if token not in portfolio['positions']:
            portfolio['positions'][token] = {
                "size": 0,
                "entry_price": fill_price,
                "current_price": fill_price,
                "unrealized_pnl": 0,
            }

        position = portfolio['positions'][token]
        position['size'] += size
        position['entry_price'] = fill_price

    async def _handle_position_closed(
        self,
        event_dict: Dict[str, Any],
        portfolio: Dict[str, Any],
    ) -> None:
        """Handle position closed event.
        
        Realizes PnL and removes position.
        
        Args:
            event_dict: Position closed event
            portfolio: Portfolio state
        """
        token = event_dict.get('token')
        pnl = event_dict.get('data', {}).get('pnl_usd', 0)

        if token in portfolio['positions']:
            position = portfolio['positions'][token]

            # Realize PnL
            portfolio['balance'] += pnl

            # Record closed trade
            closed_trade = {
                "token": token,
                "exit_price": event_dict.get('data', {}).get('exit_price'),
                "size": position['size'],
                "pnl": pnl,
                "timestamp": event_dict.get('timestamp'),
                "duration": event_dict.get('data', {}).get('duration_seconds'),
            }

            self.trades.append(closed_trade)

            # Remove position
            del portfolio['positions'][token]

    async def _execute_simulated_trade(
        self,
        token: str,
        direction: str,
        confidence: float,
        portfolio: Dict[str, Any],
        signal_source: str,
    ) -> None:
        """Execute a simulated trade.
        
        Args:
            token: Trading pair
            direction: LONG or SHORT
            confidence: Signal confidence (0-1)
            portfolio: Portfolio state
            signal_source: Agent that generated signal
        """
        # Simulate trade sizing (1-5% of portfolio based on confidence)
        trade_size = (portfolio['balance'] * confidence) / 100

        if trade_size < 10:  # Minimum trade size
            return

        # Record trade
        trade = {
            "token": token,
            "direction": direction,
            "size": trade_size,
            "confidence": confidence,
            "source": signal_source,
            "timestamp": datetime.utcnow(),
        }

        self.trades.append(trade)

        # Update portfolio state
        if token not in portfolio['positions']:
            portfolio['positions'][token] = {
                "size": 0,
                "entry_price": 0,
                "direction": direction,
                "confidence": confidence,
            }


class BacktestResults:
    """Results from a backtest run.
    
    Contains trades, metrics, and report generation.
    """

    def __init__(
        self,
        backtest_id: str,
        start_date: datetime,
        end_date: datetime,
        initial_balance: float,
        trades: List[Dict[str, Any]],
        portfolio_state: Dict[str, Any],
        events_processed: int,
        backtest_time: float,
        calculator: PerformanceCalculator,
    ):
        """Initialize backtest results.
        
        Args:
            backtest_id: Unique backtest ID
            start_date: Backtest start date
            end_date: Backtest end date
            initial_balance: Initial portfolio balance
            trades: List of recorded trades
            portfolio_state: Final portfolio state
            events_processed: Number of events processed
            backtest_time: Time taken to run backtest (seconds)
            calculator: PerformanceCalculator instance
        """
        self.backtest_id = backtest_id
        self.start_date = start_date
        self.end_date = end_date
        self.initial_balance = initial_balance
        self.trades = trades
        self.portfolio_state = portfolio_state
        self.events_processed = events_processed
        self.backtest_time = backtest_time
        self.calculator = calculator

    def get_metrics(self) -> Dict[str, float]:
        """Get all performance metrics.
        
        Returns:
            Dict of metric_name -> value
        """
        return self.calculator.calculate_all_metrics()

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of backtest results.
        
        Returns:
            Dict with key metrics and statistics
        """
        metrics = self.get_metrics()

        return {
            "backtest_id": self.backtest_id,
            "period": f"{self.start_date.date()} to {self.end_date.date()}",
            "initial_balance": self.initial_balance,
            "final_balance": self.calculator.final_balance,
            "total_return_pct": metrics.get('total_return_pct', 0),
            "sharpe_ratio": metrics.get('sharpe_ratio', 0),
            "max_drawdown_pct": metrics.get('max_drawdown_pct', 0),
            "win_rate_pct": metrics.get('win_rate_pct', 0),
            "trade_count": len(self.trades),
            "events_processed": self.events_processed,
            "backtest_speed": f"{(self.end_date - self.start_date).total_seconds() / self.backtest_time:.0f}x",
        }

    def generate_report(self) -> BacktestReport:
        """Generate comprehensive backtest report.
        
        Returns:
            BacktestReport instance
        """
        return BacktestReport(
            results=self,
            metrics=self.get_metrics(),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert results to dictionary.
        
        Returns:
            Dict representation of results
        """
        return {
            "backtest_id": self.backtest_id,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "initial_balance": self.initial_balance,
            "trades": self.trades,
            "portfolio_state": self.portfolio_state,
            "metrics": self.get_metrics(),
            "summary": self.get_summary(),
        }
