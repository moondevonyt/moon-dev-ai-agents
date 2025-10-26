# Integration Tests - Moon Dev EDA

Comprehensive integration tests for event flows, API endpoints, and agent consensus.

## Test Categories

### 1. Event Flow Tests (`test_event_flow.py`)

Tests complete event processing pipeline:

- **Event Producer/Consumer**: Publishing and consuming events through Kafka
- **Event Persistence**: Events flowing from Kafka to TimescaleDB
- **Cache Layer**: Redis cache get/set operations and fallback behavior
- **Event Store Queries**: Querying events by date range, token, type
- **Event Store Performance**: Insert and query latency benchmarks

**Key Performance Targets**:
- Event insert: <50ms
- Event query (30-day range): <5s
- Cache operations: <5ms

### 2. API Tests (`test_api.py`)

Tests REST API and WebSocket endpoints:

- **Health Checks**: Liveness (`/health`) and readiness (`/ready`) probes
- **Portfolio Management**: Get portfolio, positions, metrics
- **Event Query**: Query events with filters (token, type, time range)
- **Backtesting**: Run backtest and retrieve results
- **Metrics Export**: Prometheus metrics endpoint
- **Documentation**: Root endpoint with API info

**Coverage**:
- All public REST endpoints
- Request parameter validation
- Response format validation
- HTTP status codes

### 3. Agent & Consensus Tests (`test_agents_consensus.py`)

Tests multi-agent signal generation and consensus:

- **Signal Aggregation**: Collecting signals from Risk, Trading, Sentiment agents
- **Weighted Consensus**: Risk (35%), Trading (40%), Sentiment (25%) weighting
- **Consensus Decision**: EXECUTE, HOLD, or REJECT recommendation
- **Consensus Engine**: Signal processing and callback orchestration
- **Signal Validation**: Confidence ranges, liquidation distance, sentiment scores

**Key Features**:
- Consensus with all agents agreeing
- Consensus with conflicting signals
- Consensus with missing sentiment signal
- Risk agent veto on liquidation warnings

## Running Tests

### Prerequisites

1. Docker Compose infrastructure running:
```bash
docker-compose up -d
docker-compose logs -f
```

2. Dependencies installed:
```bash
pip install -e ".[dev]"
```

### Run All Integration Tests

```bash
pytest tests/integration -v
```

### Run Specific Test Class

```bash
pytest tests/integration/test_event_flow.py::TestEventProducerConsumer -v
pytest tests/integration/test_api.py::TestPortfolioEndpoints -v
pytest tests/integration/test_agents_consensus.py::TestSignalAggregation -v
```

### Run Single Test

```bash
pytest tests/integration/test_event_flow.py::TestEventProducerConsumer::test_publish_event_to_kafka -v
```

### Run with Coverage

```bash
pytest tests/integration -v --cov=src --cov-report=html --cov-fail-under=70
```

### Run with Verbose Output

```bash
pytest tests/integration -v -s
```

### Run with Timeout

```bash
pytest tests/integration -v --timeout=300
```

## Test Fixtures

### Database Fixtures

- `kafka_producer`: Connected EventProducer
- `event_store_db`: Connected EventStore
- `cache`: Connected CacheLayer
- `http_client`: AsyncClient for API testing

### Data Fixtures

- `sample_price_tick`: Sample PriceTickEvent
- `sample_portfolio`: Sample portfolio state

## Environment Variables

Tests use Docker Compose service names:

```env
KAFKA_BOOTSTRAP_SERVERS=kafka-1:29091,kafka-2:29092,kafka-3:29093
DB_HOST=timescaledb
REDIS_HOST=redis-master
```

## Test Data

### Sample Event

```python
PriceTickEvent(
    token="BTC-USD",
    data={
        "price": 43250.50,
        "bid": 43249.75,
        "ask": 43251.25,
        "volume_24h": 125000000,
    }
)
```

### Sample Portfolio

```python
{
    "user_id": "test_user",
    "positions": [...],
    "balance": 50000.0,
    "metrics": {
        "leverage_ratio": 1.29,
        "liquidation_distance": 0.78,
    }
}
```

## Performance Benchmarks

### Event Flow

| Operation | Target | Status |
|-----------|--------|--------|
| Event publish | <5ms | 🔄 Testing |
| Event insert | <50ms | 🔄 Testing |
| Event query (30-day) | <5s | 🔄 Testing |
| Cache get/set | <5ms | 🔄 Testing |

### API Endpoints

| Endpoint | Target Latency | Status |
|----------|-----------------|--------|
| Health check | <50ms | 🔄 Testing |
| Portfolio fetch | <100ms | 🔄 Testing |
| Event query | <500ms | 🔄 Testing |

### Consensus

| Operation | Target | Status |
|-----------|--------|--------|
| Signal aggregation | <100ms | 🔄 Testing |
| Consensus decision | <100ms | 🔄 Testing |

## Troubleshooting

### Connection Errors

If tests fail with connection errors:

1. Check Docker Compose is running:
```bash
docker-compose ps
```

2. Verify service health:
```bash
docker-compose logs kafka-1 timescaledb redis-master
```

3. Check network connectivity:
```bash
docker network ls
docker network inspect moon-dev
```

### Database Errors

If tests fail with database errors:

1. Check TimescaleDB is initialized:
```bash
docker-compose exec timescaledb psql -U postgres -d moon_dev -c "SELECT * FROM events LIMIT 1;"
```

2. Verify schema was created:
```bash
docker-compose exec timescaledb psql -U postgres -d moon_dev -c "\dt"
```

### Kafka Errors

If tests fail with Kafka errors:

1. Check broker connectivity:
```bash
docker-compose exec kafka-1 kafka-broker-api-versions --bootstrap-server localhost:9091
```

2. List topics:
```bash
docker-compose exec kafka-1 kafka-topics --bootstrap-server localhost:9091 --list
```

### Redis Errors

If tests fail with Redis errors:

1. Check Redis connectivity:
```bash
docker-compose exec redis-master redis-cli ping
```

2. Check replication:
```bash
docker-compose exec redis-master redis-cli INFO replication
```

## CI/CD Integration

### GitHub Actions

```yaml
- name: Run Integration Tests
  run: |
    docker-compose up -d
    pytest tests/integration -v --cov=src
    docker-compose down
```

### Local Pre-commit

Add to `.pre-commit-config.yaml`:

```yaml
- repo: local
  hooks:
    - id: integration-tests
      name: Integration Tests
      entry: pytest tests/integration -v
      language: system
      pass_filenames: false
```

## Adding New Tests

### Test Template

```python
@pytest.mark.asyncio
class TestNewFeature:
    """Test description."""
    
    async def test_scenario(self, kafka_producer):
        """Test scenario description."""
        # Arrange
        data = setup_test_data()
        
        # Act
        result = await kafka_producer.publish(data)
        
        # Assert
        assert result is not None
```

### Naming Convention

- Test files: `test_<feature>.py`
- Test classes: `Test<FeatureName>`
- Test methods: `test_<scenario_description>`

## Dependencies

- `pytest`: Testing framework
- `pytest-asyncio`: Async test support
- `httpx`: HTTP client for API testing
- `asyncpg`: PostgreSQL async driver
- `redis`: Redis client

## Performance Testing

### Load Test Simulation

```bash
# Simulate 1000 events/sec
pytest tests/integration/test_event_flow.py::TestEventStorePerformance -v --workers=10
```

### Profile Tests

```bash
# Run with profiling
pytest tests/integration -v --profile
```

## Continuous Integration

Tests run on:
- Every commit (pre-commit)
- Every PR (GitHub Actions)
- Nightly (full test suite with profiling)
- Pre-deployment (staging environment)

## Contributing

1. Write tests for new features
2. Maintain 70%+ code coverage
3. All tests must pass locally before PR
4. Integration tests must pass in CI/CD

## Related Documentation

- [Testing Strategy](../../docs/TESTING.md)
- [Architecture Overview](../../docs/ARCHITECTURE.md)
- [API Documentation](../../docs/API.md)
