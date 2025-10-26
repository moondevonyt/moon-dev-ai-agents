# Moon Dev AI Agents - EDA with Kafka: System Design Document

**Project**: Moon Dev Real-Time Event-Driven Architecture
**Version**: 1.0
**Date**: 2025-10-26
**Status**: Design Phase

---

## ⚡ BACKTESTING SYSTEM - NOW IMPLEMENTED!

**New Feature**: Complete backtesting engine has been added to the implementation!

**What's Included**:
- ✅ BacktestEngine: Historical event replay with isolated environment
- ✅ PerformanceCalculator: Sharpe ratio, drawdown, win rate, PnL analysis
- ✅ BacktestReport: Comprehensive HTML/JSON reports
- ✅ Full integration with EventStore for historical data

**Location**: `src/backtesting/` in MOON_DEV_EDA_IMPLEMENTATION folder
**Documentation**: See BACKTESTING.md in implementation folder
**Maps To**: User Story 3 (Event Replay for Backtesting)

**Quick Example**:
```python
engine = BacktestEngine(event_store)
results = await engine.run_backtest(
    start_date=datetime(2025, 1, 1),
    end_date=datetime(2025, 3, 31),
    agents=['trading_agent', 'sentiment_agent'],
    initial_balance=50000
)
report = results.generate_report()
print(report.summary())  # Sharpe: 2.45, Max Drawdown: -12.3%, Win Rate: 62%
```

---

## TABLE OF CONTENTS

1. [User Stories](#user-stories)
2. [System Design Overview](#system-design-overview)
3. [Architectural Components](#architectural-components)
4. [Data Flow Design](#data-flow-design)
5. [Event Taxonomy](#event-taxonomy)
6. [Agent Design](#agent-design)
7. [Integration Points](#integration-points)
8. [Design Decisions](#design-decisions)
9. [Non-Functional Requirements](#non-functional-requirements)

---

## USER STORIES

### Story 1: Real-Time Price Alert Detection

**As a** risk manager,
**I want to** receive price change alerts in real-time,
**So that** I can prevent liquidation cascades and protect portfolio equity.

**EARS Specification:**

```
WHEN a price.tick event is received from market data sources
AND the price change exceeds the configured threshold (e.g., ±5%)
AND the current portfolio is at risk
THEN the system SHALL emit a risk.alert event within 50ms
AND the alert SHALL be routed to the Risk Agent subscriber group
AND the Risk Agent SHALL evaluate liquidation distance within 100ms total
AND IF liquidation risk is critical (< 10% buffer)
  THEN the system SHALL automatically emit a trade.close event
  AND the trade SHALL be submitted to the exchange within 200ms
ELSE the system SHALL notify the user via Discord webhook immediately.
```

**Acceptance Criteria:**
- ✓ Price alerts generated within 50ms of event
- ✓ Risk evaluation completes within 100ms total latency
- ✓ Liquidation prevention executed within 200ms
- ✓ Discord notification sent within 1 second
- ✓ System handles 1000+ price ticks per second without degradation

---

### Story 2: Multi-Signal Consensus Trading

**As a** trader,
**I want to** execute trades based on consensus signals from multiple agents,
**So that** I can reduce false signals and improve trade accuracy.

**EARS Specification:**

```
WHEN multiple agents (Trading, Sentiment, Funding, Chart) emit signal.generated events
AND all signals reference the same token within a 5-second window
THEN the system SHALL aggregate these signals into a consensus signal event
AND the consensus SHALL calculate a weighted score based on agent confidence
AND IF consensus score exceeds the threshold (e.g., >70%)
  THEN the system SHALL emit a trade.consensus_approved event
  AND the Execution Engine SHALL validate risk constraints
  AND IF risk constraints are satisfied
    THEN the system SHALL place the order within 100ms of consensus
  ELSE the system SHALL emit a risk.constraint_violation event
ELSE the system SHALL discard the signals and emit a signal.consensus_failed event.
```

**Acceptance Criteria:**
- ✓ Consensus signals generated within 200ms of final input signal
- ✓ Weighted scoring algorithm correctly weights agent confidence
- ✓ Orders placed within 100ms of consensus approval
- ✓ Risk constraints evaluated before any trade execution
- ✓ Audit trail maintained for all consensus decisions

---

### Story 3: Event Replay for Backtesting

**As a** strategy researcher,
**I want to** replay historical events to backtest new trading algorithms,
**So that** I can validate strategy performance before live deployment.

**EARS Specification:**

```
WHEN a user initiates a backtest run with historical date range
AND selects specific agents/strategies to test
THEN the system SHALL query the event store for all events in that date range
AND the system SHALL deserialize and normalize all historical events
AND FOR each event in chronological order
  WHEN the event is published to the backtest broker (isolated Kafka instance)
  THEN all subscribed agents SHALL process the event as if it were live
  AND the system SHALL record all emitted events and trade execution results
  AND the system SHALL calculate performance metrics (returns, Sharpe, drawdown)
AFTER the final event is processed
THEN the system SHALL generate a comprehensive backtest report
AND the report SHALL be saved to the event store for auditing.
```

**Acceptance Criteria:**
- ✓ Event replay executes at >100x real-time speed
- ✓ Agents process backtest events identically to live events
- ✓ Performance metrics calculated accurately
- ✓ All trade executions recorded and auditable
- ✓ Backtest isolation prevents interference with live trading

---

### Story 4: Real-Time Portfolio Monitoring

**As a** portfolio manager,
**I want to** monitor portfolio metrics in real-time,
**So that** I can make informed decisions about position sizing and rebalancing.

**EARS Specification:**

```
WHEN any trade.executed event is published to the message broker
AND the trade is related to the user's portfolio
THEN the system SHALL update the cache layer (Redis) with new position data
AND the system SHALL recalculate portfolio metrics:
  - Total portfolio value
  - Leverage ratio
  - Risk score
  - Liquidation distance per position
  - Unrealized P&L
AND WHEN a user connects to the dashboard WebSocket endpoint
THEN the system SHALL stream updated portfolio metrics
AND WHEN portfolio metrics change
THEN the system SHALL push the delta to all connected dashboard clients
AND the update SHALL be delivered within 50ms of the cache update.
```

**Acceptance Criteria:**
- ✓ Portfolio metrics updated within 100ms of trade execution
- ✓ Dashboard clients receive updates within 50ms
- ✓ No data loss or stale reads
- ✓ Handles 100+ concurrent dashboard connections
- ✓ Graceful degradation if Redis unavailable

---

### Story 5: Sentiment-Driven Market Analysis

**As a** sentiment analyst,
**I want to** correlate social sentiment with price action in real-time,
**So that** I can detect emerging market trends before they become obvious.

**EARS Specification:**

```
WHEN the Sentiment Agent receives sentiment.update events from social media feeds
AND WHEN the Trading Agent simultaneously receives price.tick events from markets
THEN the system SHALL correlate sentiment changes with price movements
AND the system SHALL calculate correlation coefficient within the last 1-hour window
AND IF correlation > 0.7 (strong positive correlation)
  THEN the system SHALL emit a correlation.detected event
  AND this event SHALL be routed to the Trading Agent
WHEN the Trading Agent receives a correlation.detected event
AND a new price movement occurs in the correlated direction
THEN the Trading Agent SHALL increase confidence in the signal
AND IF increased confidence exceeds 80%
  THEN the system SHALL execute the trade with higher position size.
```

**Acceptance Criteria:**
- ✓ Sentiment updates processed within 200ms
- ✓ Correlation calculations complete within 100ms
- ✓ Trending detection accurate within 1-hour window
- ✓ Strong correlations trigger enhanced signals
- ✓ System handles 50+ sentiment updates per second

---

## SYSTEM DESIGN OVERVIEW

### High-Level Architecture (EARS-Specified)

```
WHEN the system starts up
THEN it SHALL initialize all components in the following order:
1. Message Broker (Kafka)
2. Event Store (TimescaleDB)
3. Cache Layer (Redis)
4. Agent Handlers
5. API Server (FastAPI)

AND the system SHALL perform health checks
AND IF all components are healthy
  THEN the system SHALL transition to READY state
  AND SHALL start accepting market data
ELSE the system SHALL log failures
AND SHALL not accept trading signals
AND SHALL emit a system.startup_failure event.
```

### Design Principles

```
PRINCIPLE 1: Event Sourcing
The system SHALL maintain an immutable log of all events in TimescaleDB
AND the cache layer SHALL be a projection of this event log
AND IF the cache is lost
  THEN the system SHALL be able to rebuild it from the event log
  WITHOUT loss of correctness or completeness.

PRINCIPLE 2: Asynchronous Processing
All agents SHALL process events asynchronously
AND the system SHALL NOT block on agent processing
AND IF an agent is slow
  THEN other agents SHALL continue processing new events
  AND the slow agent's lag SHALL be tracked in metrics.

PRINCIPLE 3: Event-Driven Orchestration
Agents SHALL communicate exclusively through events
AND there SHALL be NO direct method calls between agents
AND the message broker SHALL be the single source of truth for event ordering
AND within a partition.

PRINCIPLE 4: Resilience
WHEN any component fails
THEN the system SHALL continue operating with degraded functionality
AND events SHALL be queued until the component recovers
AND no data SHALL be lost during recovery.
```

---

## ARCHITECTURAL COMPONENTS

### Component 1: Message Broker (Kafka)

**Purpose:** Central hub for all event routing and distribution

```
KAFKA CLUSTER SHALL:
  ✓ Consist of 3 broker nodes in production
  ✓ Maintain topics for each event type:
    - price.ticks (1000 msgs/sec)
    - signal.generated (100 msgs/sec)
    - trade.executed (50 msgs/sec)
    - liquidation.events (20 msgs/sec)
    - sentiment.updates (50 msgs/sec)
    - risk.alerts (30 msgs/sec)
    - state.changes (200 msgs/sec)

  ✓ Partition each topic by token/symbol for parallelism
  ✓ Maintain 3-way replication for high availability
  ✓ Retain price.ticks for 24 hours
  ✓ Retain other events for 7 days
  ✓ Persist all events to TimescaleDB event store

WHEN a message is published to Kafka
THEN it SHALL be available to all subscribers within 5ms
ELSE the broker SHALL retry publication up to 3 times
AND IF all retries fail
  THEN the system SHALL log the failure
  AND SHALL alert monitoring system.
```

---

### Component 2: Event Store (TimescaleDB)

**Purpose:** Immutable, queryable event log for auditing and replay

```
EVENT STORE SHALL:
  ✓ Persist all events to hypertable with time-series optimization
  ✓ Store events in JSON format for flexibility
  ✓ Include metadata: event_id, timestamp, source, agent
  ✓ Support compression to reduce storage footprint by 80%
  ✓ Retain events for 1 year (compliance requirement)
  ✓ Create indices on (timestamp, token, event_type) for fast queries

WHEN an event is inserted into the store
THEN the insertion SHALL complete within 10ms (p99)
ELSE the system SHALL log a warning
AND SHALL still allow the event to process live
(event store write SHALL be asynchronous).

WHEN a user queries historical events
THEN the query SHALL complete within 5 seconds
ELSE the system SHALL automatically paginate results.
```

---

### Component 3: Cache Layer (Redis)

**Purpose:** Real-time state projection for low-latency reads

```
CACHE LAYER SHALL:
  ✓ Store current portfolio state (positions, balance, metrics)
  ✓ Store agent state (last signal generated, confidence)
  ✓ Store calculated metrics (leverage, risk score, PnL)
  ✓ Never expire keys (explicit updates only)
  ✓ Run in 3-node cluster with replication
  ✓ Persist snapshots to disk every 60 seconds

WHEN the cache is updated
THEN the update SHALL complete within 5ms
AND the updated value SHALL be immediately available to readers.

WHEN the cache cluster fails
THEN the system SHALL:
  1. Stop accepting new trades (until recovery)
  2. Serve stale state from event store (read-only)
  3. Queue updates in local buffer
  4. Replay updates once cluster recovers.
```

---

### Component 4: Agent Layer

**Purpose:** Asynchronous event handlers implementing trading logic

```
EACH AGENT SHALL:
  ✓ Subscribe to specific event topics
  ✓ Process events asynchronously (non-blocking)
  ✓ Emit new events based on logic
  ✓ Track its own performance metrics
  ✓ Handle errors gracefully (continue processing)
  ✓ Support distributed tracing (correlation IDs)

WHEN an agent receives an event
THEN it SHALL process it within the configured timeout (default 5s)
ELSE the system SHALL log a timeout warning
AND the event SHALL be available for reprocessing
AND the agent's lag metric SHALL be incremented.

WHEN an agent encounters an error
THEN it SHALL:
  1. Log the error with full context
  2. Emit an agent.error event
  3. Continue processing the next event
  4. NOT crash or disconnect from broker.
```

---

### Component 5: Execution Engine

**Purpose:** Validates and executes trades against exchange APIs

```
EXECUTION ENGINE SHALL:
  ✓ Subscribe to signal.generated and trade.consensus_approved events
  ✓ Validate every trade against risk constraints
  ✓ Check position limits, leverage ratios, drawdown
  ✓ Calculate order sizing based on portfolio value
  ✓ Submit orders to exchange via REST/WebSocket
  ✓ Track order status until fill or rejection
  ✓ Emit trade.executed event upon fill
  ✓ Update cache with new position immediately

WHEN a trade signal is received
THEN the execution engine SHALL:
  1. Fetch risk constraints from cache (<1ms)
  2. Validate constraints (< 5ms)
  3. Calculate position size (<1ms)
  4. Submit order to exchange (<50ms)
  5. Total latency: <100ms
ELSE IF validation fails
  THEN emit trade.rejected with reason
  AND update metrics with rejection count.
```

---

## DATA FLOW DESIGN

### End-to-End Trade Flow (EARS)

```
WHEN a market event (price spike) occurs at time t=0
THEN the following sequence of events SHALL occur:

t=0ms:     Market Data Adapter receives WebSocket message
           WHEN message is valid JSON
           THEN normalize to internal EventMsg format
           AND publish to Kafka topic

t=5ms:     Multiple agents subscribe to topic
           THEN all agents SHALL receive the event simultaneously
           AND each agent SHALL process independently

t=10ms:    Risk Agent evaluates event
           WHEN portfolio leverge > threshold
           THEN emit risk.alert event
           ELSE emit risk.ok event

t=20ms:    Trading Agent processes event (async LLM queued)
           WHEN event matches trading conditions
           THEN queue LLM inference request (non-blocking)
           AND continue processing other events

t=100ms:   Consensus mechanism aggregates signals
           WHEN multiple agents have emitted signals within window
           THEN calculate weighted consensus score
           AND IF score > threshold
             THEN emit trade.consensus_approved
           ELSE emit signal.consensus_failed

t=120ms:   Execution Engine validates approved signal
           WHEN risk constraints are satisfied
           THEN calculate position size
           AND submit order to exchange

t=150ms:   Exchange API returns order confirmation
           WHEN order is accepted
           THEN Execution Engine emits trade.placed event

t=200ms:   Order fill notification from exchange WebSocket
           WHEN fill is confirmed
           THEN Execution Engine emits trade.executed event
           AND State Manager updates cache
           AND Event Store persists event

TOTAL LATENCY: 200ms from market event to trade execution
(Target: <200ms for typical scenario)
```

---

## EVENT TAXONOMY

### Event Categories and EARS Specifications

```
CATEGORY 1: MARKET EVENTS (External)
─────────────────────────────────────

Event: price.tick
WHEN: HyperLiquid WebSocket publishes price update
THEN: System SHALL normalize and publish to Kafka within 5ms
Structure:
  {
    "event_type": "price.tick",
    "token": "BTC",
    "price": 43250.50,
    "volume_1m": 1500000,
    "timestamp": 1729950000000
  }

Event: liquidation.event
WHEN: Exchange detects liquidation
THEN: System SHALL publish to liquidation.events topic
AND Alert subscribers of liquidation cascade
Structure:
  {
    "event_type": "liquidation.event",
    "token": "BTC",
    "liquidation_count": 150,
    "cascade_indicator": true,
    "timestamp": 1729950000000
  }

Event: sentiment.update
WHEN: Sentiment analysis completes on social data
THEN: System SHALL publish to sentiment.updates topic
Structure:
  {
    "event_type": "sentiment.update",
    "token": "SOL",
    "bullish_pct": 72,
    "velocity": 15,
    "confidence": 0.78
  }


CATEGORY 2: PROCESSING EVENTS (Internal)
────────────────────────────────────────

Event: signal.generated
WHEN: Trading Agent completes analysis
THEN: System SHALL emit signal.generated event
AND route to Execution Engine and State Manager
Structure:
  {
    "event_type": "signal.generated",
    "token": "BTC",
    "action": "BUY",
    "score": 78,
    "confidence": 0.85,
    "agent": "trading_agent"
  }

Event: risk.alert
WHEN: Risk Agent detects risk violation
THEN: System SHALL emit risk.alert immediately
AND route to Execution Engine (for position closure)
AND route to User Notifications (for alerts)
Structure:
  {
    "event_type": "risk.alert",
    "severity": "CRITICAL",
    "violation_type": "liquidation_risk",
    "action_required": "close_positions"
  }

Event: trade.consensus_approved
WHEN: Consensus score exceeds threshold from multiple agents
THEN: System SHALL emit consensus approval
AND trigger Execution Engine evaluation
Structure:
  {
    "event_type": "trade.consensus_approved",
    "token": "BTC",
    "consensus_score": 82,
    "contributing_agents": ["trading_agent", "chart_agent"],
    "recommended_action": "BUY"
  }


CATEGORY 3: ACTION EVENTS (System Directives)
──────────────────────────────────────────────

Event: trade.placed
WHEN: Execution Engine submits order to exchange
THEN: System SHALL emit trade.placed
AND track order in order book cache
Structure:
  {
    "event_type": "trade.placed",
    "order_id": "ord_123456",
    "token": "BTC",
    "size": 0.1156,
    "order_type": "MARKET"
  }

Event: trade.executed
WHEN: Exchange confirms fill
THEN: System SHALL emit trade.executed
AND update positions in cache
AND persist to event store
Structure:
  {
    "event_type": "trade.executed",
    "order_id": "ord_123456",
    "token": "BTC",
    "fill_price": 43265.25,
    "filled_amount": 0.1156,
    "timestamp": 1729950100000
  }

Event: position.closed
WHEN: All units of position sold/exited
THEN: System SHALL emit position.closed
AND calculate final PnL
Structure:
  {
    "event_type": "position.closed",
    "token": "BTC",
    "exit_price": 44395,
    "pnl_usd": 1155.45,
    "duration_seconds": 3600
  }


CATEGORY 4: STATE EVENTS (Event Sourcing)
──────────────────────────────────────────

Event: state.snapshot
WHEN: Periodic snapshot interval (every 5 minutes)
OR WHEN: Significant state change occurs
THEN: System SHALL emit state.snapshot
AND persist complete portfolio state
Structure:
  {
    "event_type": "state.snapshot",
    "timestamp": 1729950000000,
    "portfolio_value": 50123.45,
    "positions": {...},
    "leverage_ratio": 1.0,
    "daily_pnl": 123.45
  }

Event: state.changed
WHEN: Any state update occurs (cache update)
THEN: System SHALL emit state.changed
AND notify dashboard subscribers
Structure:
  {
    "event_type": "state.changed",
    "timestamp": 1729950100000,
    "delta": {
      "new_portfolio_value": 50500.00,
      "changed_fields": ["portfolio_value", "positions"]
    }
  }
```

---

## AGENT DESIGN

### Risk Agent Design (EARS)

```
RISK AGENT ARCHITECTURE:

Subscribes to:
  - price.ticks (for leverage recalculation)
  - liquidation.events (for cascade detection)
  - trade.executed (for position updates)
  - state.snapshots (for consistency)

WHEN price.tick event received
THEN Risk Agent SHALL:
  1. Fetch current positions from cache (<1ms)
  2. Calculate new portfolio value based on price
  3. Recalculate leverage ratio (< 2ms total)
  4. Check against MAX_LEVERAGE threshold
  5. IF leverage > MAX_LEVERAGE
     THEN emit risk.alert event immediately
     AND set HALT_TRADING flag
  6. Check liquidation distances
  7. IF any position < 10% from liquidation
     THEN emit risk.critical event
     AND trigger FORCE_CLOSE procedure

WHEN liquidation.event received (cascade detected)
THEN Risk Agent SHALL:
  1. Evaluate portfolio exposure to liquidated tokens
  2. Calculate cascade impact on portfolio
  3. IF impact > threshold
     THEN emit risk.cascade_detected event
     AND recommend position reducing
  4. Monitor for further liquidations

FORCE_CLOSE PROCEDURE (triggered by risk.critical):
  WHEN critical liquidation risk detected
  THEN Execution Engine SHALL:
    1. Validate risk signal (< 5ms)
    2. Place market close orders (no slippage negotiation)
    3. Submit to exchange via priority channel
    4. Emit trade.force_close event
    5. Total latency: <100ms

Output Events:
  - risk.ok (no issues)
  - risk.alert (warning)
  - risk.critical (emergency)
  - risk.cascade_detected
```

### Trading Agent Design (EARS)

```
TRADING AGENT ARCHITECTURE:

Subscribes to:
  - price.ticks (for technical analysis)
  - signal.consensus_approved (when consensus reached)
  - risk.alert (to halt if risk violated)

WHEN price.tick event received
THEN Trading Agent SHALL:
  1. Fetch OHLCV data from cache (<1ms)
  2. Calculate technical indicators (<5ms):
     - SMA(20), SMA(50)
     - RSI(14)
     - MACD
     - Bollinger Bands
  3. Queue LLM inference request (async, non-blocking)
     - Do NOT wait for response
     - Continue processing other events
  4. When LLM response received (100-500ms later):
     - Parse signal from response
     - Emit signal.generated event

WHEN risk.alert received with HALT_TRADING flag
THEN Trading Agent SHALL:
  1. Stop processing new signals
  2. Continue monitoring (no action)
  3. Wait for risk.ok signal to resume

LLM INFERENCE (Async):
  - Uses ModelFactory to select provider
  - Claude (default): 100-300ms
  - Groq (fast): 50-100ms
  - DeepSeek (reasoning): 200-500ms

  WHEN LLM response received
  THEN Parse JSON signal
  AND validate format
  AND emit signal.generated with full context

Output Events:
  - signal.generated (with score, action, confidence)
  - signal.error (if parsing fails)
  - agent.lagging (if processing >1s behind)
```

---

## INTEGRATION POINTS

### Exchange Integration (EARS)

```
WHEN Execution Engine has approved trade
THEN it SHALL integrate with exchange via:

HyperLiquid Integration:
  ✓ REST API for order placement
  ✓ WebSocket for real-time fill notifications
  ✓ Authentication via ETH signature

WHEN order is placed via REST
THEN system SHALL:
  1. Construct order message with signature
  2. POST to /api/v1/action/placeOrder
  3. Wait for acknowledgment (< 50ms typically)
  4. Emit trade.placed event
  5. Subscribe to WebSocket fill updates for this order_id

WHEN fill is confirmed via WebSocket
THEN system SHALL:
  1. Extract fill details (price, amount)
  2. Emit trade.executed event
  3. Update cache with position
  4. Persist to event store

Solana Integration:
  ✓ RPC for balance queries
  ✓ Jupiter API for swaps
  ✓ SPL token interactions

WHEN user is on Solana chain
THEN system SHALL:
  1. Use ExchangeManager to abstract chain differences
  2. Build transaction with Anchor
  3. Sign with SOLANA_PRIVATE_KEY
  4. Send to RPC endpoint
  5. Monitor for confirmation (3-5 seconds typical)
```

### Alert Integration (EARS)

```
WHEN risk.alert or signal.generated event emitted
THEN system SHALL integrate with user notification channels:

Discord Integration:
  WHEN event severity is CRITICAL
  THEN send Discord message immediately
  AND format: @user Alert: {message}
  AND include action buttons (if applicable)

  WHEN event severity is WARNING
  THEN send Discord message within 5 seconds
  AND include relevant metrics

Telegram Integration (if enabled):
  WHEN Telegram bot token configured
  THEN send Telegram message
  AND include emoji for quick visual scanning

Email Integration (for daily summaries):
  WHEN event.type is state.snapshot
  AND daily summary interval reached
  THEN compile daily report
  AND send email with performance metrics

SMS Integration (for critical alerts):
  WHEN risk.critical event emitted
  AND SMS enabled for this alert type
  THEN send SMS immediately
  AND include order ID for reference
```

---

## DESIGN DECISIONS

### Decision 1: Why Event Sourcing?

```
DECISION: Implement Event Sourcing pattern (store immutable event log)

RATIONALE:
  ✓ Auditability: Every trade decision has a recorded event chain
  ✓ Replay: Can backtest by replaying historical events
  ✓ Debugging: Can trace exact sequence of events leading to issue
  ✓ Compliance: Complete audit trail for regulatory requirements
  ✓ Recovery: Can rebuild state from event log if cache fails

ALTERNATIVE: Traditional database updates
  ✗ No audit trail of how we arrived at current state
  ✗ Difficult to backtest (no historical event sequence)
  ✗ Hard to debug state inconsistencies
  ✗ Harder to recover from corruption

SELECTED: Event Sourcing
COST: Additional storage (~2-5x), operational complexity
BENEFIT: Auditability, replay, debugging, compliance (Worth it for regulated trading)
```

### Decision 2: Why Async Agents?

```
DECISION: Implement asynchronous (non-blocking) agent processing

RATIONALE:
  ✓ Scalability: One slow agent doesn't block others
  ✓ Responsiveness: Can process 1000+ events/second
  ✓ Parallelism: Multiple agents run concurrently
  ✓ Resource efficiency: No idle waiting on I/O

ALTERNATIVE: Synchronous sequential processing
  ✗ One slow agent (e.g., LLM call) blocks entire system
  ✗ Throughput limited to slowest agent
  ✗ Poor latency (15-30 seconds typical vs <100ms)

SELECTED: Async event-driven processing
COST: Complexity of async programming, harder debugging
BENEFIT: 150x latency improvement, 1000x throughput improvement (Worth it for real-time trading)
```

### Decision 3: Why Kafka over RabbitMQ?

```
DECISION: Use Apache Kafka as message broker

RATIONALE:
  ✓ Durable: Messages persisted to disk (don't lose events)
  ✓ Scalable: Horizontal scaling via partitions
  ✓ Replay: Can reprocess events from any offset
  ✓ Streaming: Native support for stream processing
  ✓ Performance: High throughput (1M+ msgs/sec)

ALTERNATIVE: RabbitMQ
  ✓ More traditional, easier setup
  ✗ Messages cleared after consumption (no replay by default)
  ✗ No native stream processing

ALTERNATIVE: Redis Streams
  ✓ Simpler to operate
  ✗ Limited scalability
  ✗ Single-node bottleneck

SELECTED: Apache Kafka
COST: Operational complexity, requires proper cluster management
BENEFIT: Durability, replay, scalability (Essential for financial trading)
```

### Decision 4: Cache Invalidation Strategy

```
DECISION: Never expire cache keys, explicit updates only

RATIONALE:
  ✓ No stale reads: Always fresh state
  ✓ No surprise evictions: Cache doesn't shrink unexpectedly
  ✓ Simpler logic: Cache = true current state

ALTERNATIVE: TTL-based expiration
  ✗ Risk of stale reads for critical data
  ✗ Unpredictable evictions

ALTERNATIVE: LRU eviction
  ✗ Least recently used might still be in-use data

SELECTED: Explicit updates only
COST: Must manage cache invalidation proactively
BENEFIT: Guaranteed freshness for risk-critical data
```

---

## NON-FUNCTIONAL REQUIREMENTS

### Performance (EARS)

```
REQUIREMENT: Sub-100ms latency from market event to trade execution

The system SHALL:
  ✓ Process price ticks within 5-10ms of WebSocket receipt
  ✓ Publish events to Kafka within 1-2ms
  ✓ Deliver events to subscribers within 5ms
  ✓ Execute risk checks within 5ms
  ✓ Execute trades within 100ms of signal
  ✓ Handle 1000+ ticks per second without degradation
  ✓ Handle 100+ concurrent dashboard connections

MEASUREMENT: P99 latency (worst 1% of requests)
  - Price tick → Kafka publish: <15ms (p99)
  - Signal generation → Trade placement: <200ms (p99)
  - Cache update → Dashboard delivery: <50ms (p99)

If latency SLA is violated:
  THEN system SHALL emit a metric.sla_violation event
  AND monitoring SHALL alert operators
  AND root cause analysis SHALL be triggered
```

### Availability (EARS)

```
REQUIREMENT: 99.9% availability (maximum 44 minutes downtime/month)

The system SHALL:
  ✓ Continue operating with any single component failure
  ✓ Automatically failover within 30 seconds
  ✓ Never lose trading events or positions
  ✓ Maintain data consistency across failures

Component redundancy:
  - Kafka: 3-node cluster (tolerates 1 node failure)
  - TimescaleDB: 2-node replica set (tolerates 1 node failure)
  - Redis: 3-node cluster (tolerates 1 node failure)
  - Agents: Multiple instances per agent type (auto-restart)
  - API: Load-balanced across 3 instances

If a component fails:
  THEN remaining instances SHALL continue serving traffic
  AND alerts SHALL notify operators to replace failed instance
  AND system SHALL remain operational (degraded if needed)
```

### Security (EARS)

```
REQUIREMENT: Protect against unauthorized trading and data breaches

The system SHALL:
  ✓ Authenticate all API requests (JWT tokens)
  ✓ Encrypt all data in transit (TLS 1.3)
  ✓ Encrypt all data at rest (AES-256)
  ✓ Separate trading permissions from read-only access
  ✓ Audit all trade executions with user/timestamp/reason
  ✓ Rate-limit API endpoints (100 req/min per user)
  ✓ Mask sensitive data in logs (API keys, private keys)

WHEN a user attempts to execute a trade
THEN system SHALL:
  1. Verify user authentication token
  2. Check user permissions (trading_enabled flag)
  3. Verify signature (for HyperLiquid: ETH signature)
  4. Log action with user_id, timestamp, reason
  5. Check rate limits
  6. Only THEN proceed with trade

WHEN logs are written
THEN system SHALL:
  ✓ Redact private keys
  ✓ Redact API keys
  ✓ Store audit log in encrypted database
  ✓ Maintain 1-year retention for compliance
```

### Maintainability (EARS)

```
REQUIREMENT: System must be maintainable by 2-3 engineers

The system SHALL:
  ✓ Have comprehensive logs with correlation IDs
  ✓ Have distributed tracing enabled (Jaeger)
  ✓ Have runbooks for common failures
  ✓ Have monitoring dashboards for key metrics
  ✓ Have alerts for anomalies
  ✓ Have deployment automation (CI/CD)
  ✓ Have database migration tools
  ✓ Have rollback procedures for bad deployments

WHEN a critical issue occurs
THEN engineer SHALL:
  1. See alert in monitoring system (within 5 seconds)
  2. Access runbook with troubleshooting steps
  3. View distributed trace showing root cause
  4. Execute remediation (restart component, scale, etc.)
  5. Verify fix via metrics dashboard

Development process:
  ✓ Code review required for all changes
  ✓ Automated testing (unit, integration, E2E)
  ✓ Staging environment mirrors production
  ✓ Blue-green deployments for zero downtime
```

---

**Document Status**: Design Complete
**Next Phase**: Requirements Specification (requirements.md)
**Review Date**: 2025-10-27
