# 🌙 Quantitative Trading Agents - Quick Start Guide

## What's Been Built

A Jim Simons-style quantitative trading system with:
- **Anomaly Detection:** Finds statistical anomalies in market data
- **Signal Aggregation:** Combines weak signals into strong predictions
- **Transaction Cost Analysis:** Validates trades are profitable after costs
- **Statistical Utilities:** Comprehensive statistical functions
- **Database Schema:** TimescaleDB tables for all quant data

## Quick Start

### 1. Install Dependencies

```bash
cd MOON_DEV_EDA_IMPLEMENTATION
pip install numpy scipy pandas termcolor
```

### 2. Set Up Database

```bash
# Apply the quantitative schema
psql -U your_user -d your_database -f infrastructure/schema_quant.sql
```

### 3. Configure Settings

Edit `src/config.py` and adjust these key parameters:

```python
# Anomaly Detection
ANOMALY_DETECTION_SIGMA_THRESHOLD = 2.0  # Standard deviations for anomaly
ANOMALY_DETECTION_P_VALUE_THRESHOLD = 0.05  # Statistical significance

# Signal Aggregation
SIGNAL_AGGREGATION_CONSENSUS_THRESHOLD = 70  # Consensus threshold %
SIGNAL_AGGREGATION_MIN_SOURCES = 3  # Minimum signal sources

# Transaction Costs
MAX_TRANSACTION_COST_PCT = 0.3  # Maximum cost percentage
```

### 4. Run Individual Agents

```bash
# Anomaly Detection Agent
python -m src.agents.quant.anomaly_detection_agent

# Signal Aggregation Agent
python -m src.agents.quant.signal_aggregation_agent

# Transaction Cost Agent
python -m src.agents.quant.transaction_cost_agent
```

## How It Works

### Event Flow

```
1. Price Tick Event → Anomaly Detection Agent
   ↓
2. Detects statistical anomalies (z-score > 2σ, p < 0.05)
   ↓
3. Emits SIGNAL_ANOMALY event → Signal Aggregation Agent
   ↓
4. Aggregates signals with Bayesian weights
   ↓
5. Emits SIGNAL_AGGREGATED event → Transaction Cost Agent
   ↓
6. Validates transaction costs < 0.3%
   ↓
7. Emits TRADE_COST_ANALYSIS event → Execution Engine
```

### Key Features

**Anomaly Detection:**
- Mean reversion detection using z-scores
- Correlation anomaly detection (>0.3 change)
- Autocorrelation pattern detection
- Statistical significance testing (p-value < 0.05)

**Signal Aggregation:**
- Weighted signal combination
- Bayesian weight updating based on performance
- Minimum 3 signal sources required
- 70% consensus threshold

**Transaction Cost Analysis:**
- Square-root market impact model
- Automatic cost model calibration
- Trade rejection when cost > 0.3%
- Separate models per token

## Testing

### Test Anomaly Detection

```python
from src.agents.quant.anomaly_detection_agent import AnomalyDetectionAgent
from src.core.models import Event, EventType
from datetime import datetime

# Create agent
agent = AnomalyDetectionAgent()

# Simulate price tick
event = Event(
    event_type=EventType.PRICE_TICK,
    token="BTC-USD",
    source="test",
    data={"price": 43250.50}
)

# Process event
await agent.handle_price_tick(event)
```

### Test Signal Aggregation

```python
from src.agents.quant.signal_aggregation_agent import SignalAggregationAgent

# Create agent
agent = SignalAggregationAgent()

# Simulate signals
signal_event = Event(
    event_type=EventType.SIGNAL_GENERATED,
    token="BTC-USD",
    source="agent.trading",
    data={
        "direction": "LONG",
        "confidence": 0.85
    }
)

await agent.handle_signal(signal_event)
```

## Configuration Reference

### Anomaly Detection Settings

| Parameter | Default | Description |
|-----------|---------|-------------|
| `ANOMALY_DETECTION_WINDOW_DAYS` | 30 | Rolling window for statistics |
| `ANOMALY_DETECTION_SIGMA_THRESHOLD` | 2.0 | Standard deviations for anomaly |
| `ANOMALY_DETECTION_P_VALUE_THRESHOLD` | 0.05 | Statistical significance |
| `ANOMALY_CORRELATION_CHANGE_THRESHOLD` | 0.3 | Correlation change threshold |

### Signal Aggregation Settings

| Parameter | Default | Description |
|-----------|---------|-------------|
| `SIGNAL_AGGREGATION_WINDOW_SECONDS` | 5 | Time window to collect signals |
| `SIGNAL_AGGREGATION_MIN_SOURCES` | 3 | Minimum signal sources |
| `SIGNAL_AGGREGATION_CONSENSUS_THRESHOLD` | 70 | Consensus threshold % |
| `SIGNAL_AGGREGATION_WEIGHT_ALPHA` | 0.1 | EMA alpha for weight updates |

### Transaction Cost Settings

| Parameter | Default | Description |
|-----------|---------|-------------|
| `MAX_TRANSACTION_COST_PCT` | 0.3 | Maximum cost percentage |
| `MARKET_IMPACT_COEFFICIENT` | 0.01 | Initial market impact coefficient |
| `SLIPPAGE_CALIBRATION_DAYS` | 7 | Days for cost model calibration |

## Database Tables

### signal_weights
Tracks historical weights for each signal source.

```sql
SELECT * FROM signal_weights 
WHERE signal_source = 'agent.trading' 
ORDER BY time DESC LIMIT 10;
```

### strategy_capacity
Tracks capacity metrics and slippage.

```sql
SELECT * FROM strategy_capacity 
WHERE strategy_id = 'mean_reversion_v1' 
ORDER BY time DESC LIMIT 10;
```

### signal_performance
Tracks performance metrics for signals.

```sql
SELECT signal_source, AVG(sharpe_ratio) as avg_sharpe
FROM signal_performance 
WHERE time > NOW() - INTERVAL '30 days'
GROUP BY signal_source;
```

## Troubleshooting

### Agent Won't Start

**Problem:** `ModuleNotFoundError: No module named 'src'`

**Solution:** Run from project root:
```bash
cd MOON_DEV_EDA_IMPLEMENTATION
python -m src.agents.quant.anomaly_detection_agent
```

### No Events Being Processed

**Problem:** Agent starts but doesn't process events

**Solution:** Check Kafka is running:
```bash
docker-compose ps
# Should show kafka and zookeeper running
```

### Database Connection Error

**Problem:** `psycopg2.OperationalError: could not connect`

**Solution:** Check TimescaleDB is running:
```bash
docker-compose ps timescaledb
# Apply schema if needed
psql -U moondev -d moondev_db -f infrastructure/schema_quant.sql
```

### Redis Connection Error

**Problem:** `redis.exceptions.ConnectionError`

**Solution:** Check Redis is running:
```bash
docker-compose ps redis
# Restart if needed
docker-compose restart redis
```

## Next Steps

### Implement Remaining Agents

1. **Backtesting Validation Agent** - Validate strategies with historical data
2. **Capacity Monitoring Agent** - Track strategy capacity limits
3. **Signal Decay Agent** - Detect and retire degraded signals
4. **Regime Detection Agent** - Identify market regimes
5. **Correlation Matrix Agent** - Discover hidden correlations
6. **Portfolio Optimization Agent** - Optimize capital allocation
7. **Alternative Data Agent** - Ingest alternative data sources

### Integration

1. Connect to existing trading agents
2. Add Prometheus metrics
3. Create Grafana dashboards
4. Write integration tests
5. Deploy to production

## Resources

- **Full Status:** `QUANT_AGENTS_IMPLEMENTATION_STATUS.md`
- **Requirements:** `.kiro/specs/simons-quant-agents/requirements.md`
- **Tasks:** `.kiro/specs/simons-quant-agents/tasks.md`
- **Code:** `src/agents/quant/`

## Support

For issues or questions:
1. Check the implementation status document
2. Review the requirements and tasks
3. Examine the code comments
4. Test with the examples above

---

**Built with 🌙 by Moon Dev**  
**Powered by Jim Simons-style quantitative methods**
