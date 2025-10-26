# Moon Dev EDA Implementation - Getting Started Guide

This guide walks you through setting up and running the Moon Dev Real-Time Event-Driven Architecture system locally and in production.

**Document Maps to**: TASKS.md Phases 1-5

---

## Quick Start (Local Development)

### Prerequisites

- Python 3.10+
- Docker & Docker Compose
- git
- 8+ GB RAM available
- Anthropic API key (for Trading Agent)

### 1. Clone and Setup

```bash
# Clone repository
git clone <repo-url>
cd MOON_DEV_EDA_IMPLEMENTATION

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Create .env file
cp .env.example .env
# Edit .env and add your Anthropic API key
```

### 2. Start Local Infrastructure (Docker Compose)

```bash
# Start Kafka, TimescaleDB, Redis
docker-compose up -d

# Verify services are running
docker-compose ps

# Check Kafka connectivity
docker-compose exec kafka kafka-topics.sh --list --bootstrap-server localhost:9092
```

### 3. Initialize Database

```bash
# Run migrations
alembic upgrade head

# Verify tables created
psql -h localhost -U postgres -d moon_dev -c "\dt"
```

### 4. Run Tests

```bash
# Unit tests
pytest tests/unit -v --cov=src

# Integration tests  
pytest tests/integration -v

# Check coverage
coverage report
```

### 5. Start Agents (Local)

```bash
# Terminal 1: Risk Agent
python -m src.agents.risk_agent

# Terminal 2: Trading Agent
ANTHROPIC_API_KEY=<your-key> python -m src.agents.trading_agent

# Terminal 3: Sentiment Agent
python -m src.agents.sentiment_agent

# Terminal 4: Event Producer (simulator)
python scripts/price_simulator.py
```

### 6. Monitor System

```bash
# Check Prometheus
http://localhost:9090

# Check Grafana
http://localhost:3000

# Check logs
docker-compose logs -f kafka
docker-compose logs -f postgres
```

---

## Phase 1: Infrastructure Setup (Weeks 1-2)

Maps to T-1.1, T-1.2, T-1.3, T-1.4

### T-1.1: Kubernetes Cluster Provisioning

**For Local Development**: Use Docker Desktop Kubernetes or Minikube

```bash
# Using Minikube (macOS/Linux)
brew install minikube
minikube start --cpus=4 --memory=8192 --disk-size=100g

# Using Docker Desktop (Windows/macOS)
# Enable Kubernetes in Docker Desktop settings

# Verify cluster
kubectl get nodes
```

**For AWS**: Use EKS

```bash
# Install eksctl
brew install weaveworks/tap/eksctl

# Create cluster
eksctl create cluster \
  --name moon-dev-eda \
  --region us-east-1 \
  --nodes 3 \
  --node-type t3.large \
  --with-oidc

# Configure kubectl
aws eks update-kubeconfig --name moon-dev-eda --region us-east-1
```

### T-1.2: Kafka Cluster Deployment

**Using Helm (Kubernetes)**

```bash
# Add Kafka Helm repo
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

# Install Kafka
helm install kafka bitnami/kafka \
  -f k8s/values.yaml \
  --namespace moon-dev-eda \
  --create-namespace

# Verify Kafka
kubectl get pods -n moon-dev-eda
kubectl logs -f kafka-0 -n moon-dev-eda

# Create topics
kubectl exec kafka-0 -n moon-dev-eda -- \
  kafka-topics.sh --create \
  --bootstrap-server localhost:9092 \
  --topic price.ticks \
  --partitions 10 \
  --replication-factor 3
```

**For Local Testing**: Use Docker Compose

```bash
docker-compose up -d kafka zookeeper

# Create topics
docker-compose exec kafka kafka-topics.sh \
  --create \
  --bootstrap-server kafka:9092 \
  --topic price.ticks \
  --partitions 10 \
  --replication-factor 3

# List topics
docker-compose exec kafka kafka-topics.sh \
  --list \
  --bootstrap-server kafka:9092
```

### T-1.3: TimescaleDB Setup

**Using Helm (Kubernetes)**

```bash
# Install TimescaleDB
helm repo add timescale https://charts.timescale.com
helm repo update

helm install timescaledb timescale/timescaledb-single \
  -n moon-dev-eda \
  --set global.credentials.username=postgres \
  --set global.credentials.password=<generate-secure-password>

# Verify
kubectl get pods -n moon-dev-eda
kubectl port-forward svc/timescaledb 5432:5432 -n moon-dev-eda
```

**For Local Testing**: Use Docker Compose

```bash
docker-compose up -d postgres timescaledb

# Connect and create schema
psql -h localhost -U postgres -d moon_dev -f infrastructure/schema.sql

# Verify hypertable
psql -h localhost -U postgres -d moon_dev \
  -c "SELECT * FROM timescaledb_information.hypertables;"
```

### T-1.4: Redis Cluster Setup

**Using Helm (Kubernetes)**

```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

helm install redis bitnami/redis \
  -n moon-dev-eda \
  --set architecture=replication \
  --set replica.replicaCount=2 \
  --set auth.password=<generate-secure-password>

# Verify
kubectl port-forward svc/redis-master 6379:6379 -n moon-dev-eda
redis-cli -h localhost ping
```

**For Local Testing**: Use Docker Compose

```bash
docker-compose up -d redis

# Verify
redis-cli -h localhost ping
redis-cli -h localhost CONFIG GET maxmemory
```

---

## Phase 2: Core Event System (Weeks 3-4)

Maps to T-2.1, T-2.2, T-2.3, T-2.4

### Test Event System Locally

```bash
# Start Python REPL
python

# In Python:
from src.core import EventProducer, EventStore, CacheLayer
from src.core.models import Event, EventType, PriceTickEvent

# Test Producer
producer = EventProducer(['localhost:9092'])

event = PriceTickEvent(
    token='BTC-USD',
    source='exchange.test',
    data={'price': 43250.50, 'volume': 10.5}
)

event_id = producer.publish(event)
print(f"Published: {event_id}")

# Test EventStore
import asyncio
async def test_store():
    store = EventStore()
    await store.connect()
    
    # Insert
    await store.insert_event(event)
    
    # Query
    events = await store.query_by_date_range(
        datetime.now() - timedelta(hours=1),
        datetime.now(),
        token='BTC-USD'
    )
    print(f"Found {len(events)} events")
    
    await store.disconnect()

asyncio.run(test_store())

# Test Cache
async def test_cache():
    cache = CacheLayer()
    await cache.connect()
    
    # Set
    await cache.set('portfolio:user1', {'balance': 10000})
    
    # Get
    portfolio = await cache.get('portfolio:user1')
    print(portfolio)
    
    await cache.disconnect()

asyncio.run(test_cache())
```

---

## Phase 3: Agent Development (Weeks 5-8)

Maps to T-3.1, T-3.2, T-3.3, T-3.4

### Run Traditional Agents Locally

```bash
# In separate terminals:

# Terminal 1: Risk Agent
python -m src.main --agent risk_agent \
  --kafka-servers localhost:9092 \
  --redis-host localhost

# Terminal 2: Trading Agent
export ANTHROPIC_API_KEY=your-key-here
python -m src.main --agent trading_agent \
  --kafka-servers localhost:9092 \
  --use-llm true

# Terminal 3: Sentiment Agent
python -m src.main --agent sentiment_agent \
  --kafka-servers localhost:9092
```

### Run Quantitative Agents Locally

```bash
# Enable quant agents in src/main.py
# Edit ACTIVE_AGENTS dict to enable desired agents

# Run all enabled quant agents (background thread)
python src/main.py

# Or run individual quant agents for testing:

# Terminal 1: Anomaly Detection
python -m src.agents.quant.anomaly_detection_agent

# Terminal 2: Signal Aggregation
python -m src.agents.quant.signal_aggregation_agent

# Terminal 3: Transaction Cost Analysis
python -m src.agents.quant.transaction_cost_agent

# Terminal 4: Portfolio Optimization
python -m src.agents.quant.portfolio_optimization_agent
```

**Quant Agent Configuration**:
- All settings in `src/config.py` under "QUANTITATIVE TRADING AGENT CONFIGURATION"
- 60+ configurable parameters for fine-tuning
- See [QUANT_AGENTS_INTEGRATION_GUIDE.md](QUANT_AGENTS_INTEGRATION_GUIDE.md) for details

### Generate Test Data

```bash
# Simulate price ticks
python scripts/price_simulator.py \
  --token BTC-USD \
  --interval 1 \
  --kafka-servers localhost:9092

# Generate sentiment updates
python scripts/sentiment_simulator.py \
  --token BTC-USD \
  --kafka-servers localhost:9092
```

### Monitor Agent Metrics

```bash
# View Prometheus metrics
curl http://localhost:9090/api/v1/query?query=kafka_messages_consumed_total

# View in Grafana
http://localhost:3000
# Login: admin / admin
# Navigate to Dashboards > Agent Metrics
```

---

## Phase 4: Testing & Optimization (Weeks 9-12)

Maps to T-4.1, T-4.2, T-4.3

### Unit Tests

```bash
# Run all unit tests
pytest tests/unit -v --cov=src --cov-report=html

# Run specific test
pytest tests/unit/test_event_producer.py -v

# With coverage threshold
pytest tests/unit \
  --cov=src \
  --cov-fail-under=80 \
  -v
```

### Integration Tests

```bash
# Run integration tests (requires services running)
pytest tests/integration -v

# With specific marker
pytest -m integration -v
```

### Load Testing

```bash
# Using Locust
pip install locust

locust -f tests/load/locustfile.py \
  --host=http://localhost:8080 \
  --users 100 \
  --spawn-rate 10

# Access web UI at http://localhost:8089
```

### Chaos Engineering

```bash
# Kill Kafka broker (using chaos toolkit)
pip install chaostoolkit-kubernetes

chaos run experiments/kafka_broker_failure.yaml

# Verify system recovers
# Check logs: docker-compose logs kafka
```

---

## Phase 5: Deployment & Monitoring (Weeks 13-16)

Maps to T-5.1, T-5.2, T-5.3, T-5.4, T-5.5

### Build Docker Images

```bash
# Build
docker build -t moon-dev-eda:latest .

# Push to registry
docker tag moon-dev-eda:latest docker.io/moondev/eda:latest
docker push docker.io/moondev/eda:latest
```

### Deploy to Kubernetes

```bash
# Using Helm
helm install moon-dev-eda ./helm/chart \
  -f k8s/values.yaml \
  --namespace moon-dev-eda \
  --create-namespace

# Verify deployment
kubectl get all -n moon-dev-eda

# Check logs
kubectl logs -f deployment/trading-agent -n moon-dev-eda

# Port forward to access services
kubectl port-forward svc/kafka 9092:9092 -n moon-dev-eda
kubectl port-forward svc/prometheus 9090:9090 -n moon-dev-eda
```

### Setup Monitoring & Alerting

```bash
# Prometheus is auto-deployed by Helm
# Access at: http://localhost:9090

# Grafana dashboards
kubectl port-forward svc/grafana 3000:3000 -n moon-dev-eda
# Navigate to http://localhost:3000

# Create alert rules
kubectl apply -f k8s/alerting-rules.yaml -n moon-dev-eda
```

### Setup Logging (ELK Stack)

```bash
# Already deployed via Helm
# Access Kibana
kubectl port-forward svc/kibana 5601:5601 -n moon-dev-eda
# Navigate to http://localhost:5601

# Create index pattern
# - Go to Management > Index Patterns
# - Create pattern: logs-*
# - Time field: @timestamp
```

---

## Configuration Reference

### Environment Variables

```bash
# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_CONSUMER_GROUP=moon-dev-eda

# TimescaleDB
DB_HOST=localhost
DB_PORT=5432
DB_NAME=moon_dev
DB_USER=postgres
DB_PASSWORD=change-me

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=change-me

# LLM
ANTHROPIC_API_KEY=<your-key>
ANTHROPIC_MODEL=claude-3-sonnet-20240229

# Agents
MAX_LEVERAGE=10.0
LIQUIDATION_WARNING_THRESHOLD=0.85
FORCE_CLOSE_THRESHOLD=0.95
```

### Kubernetes Resources

```yaml
# Check resource usage
kubectl top nodes -n moon-dev-eda
kubectl top pods -n moon-dev-eda

# View resource limits
kubectl get resourcequota -n moon-dev-eda
kubectl describe quota -n moon-dev-eda
```

---

## Troubleshooting

### Kafka Connection Issues

```bash
# Check Kafka connectivity
kafka-console-producer.sh \
  --bootstrap-server localhost:9092 \
  --topic test

# Check topic partitions
kafka-topics.sh \
  --describe \
  --bootstrap-server localhost:9092 \
  --topic price.ticks

# Check consumer lag
kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 \
  --group moon-dev-eda \
  --describe
```

### Database Connection Issues

```bash
# Test PostgreSQL connection
psql -h localhost -U postgres -d moon_dev -c "SELECT 1"

# Check hypertables
psql -h localhost -U postgres -d moon_dev \
  -c "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"

# Check TimescaleDB version
psql -h localhost -U postgres -d moon_dev -c "SELECT version();"
```

### Agent Failures

```bash
# Check agent logs
kubectl logs -f deployment/trading-agent -n moon-dev-eda

# Check consumer lag
kafka-consumer-groups.sh \
  --bootstrap-server kafka:9092 \
  --group trading_agent_group \
  --describe

# Restart agent
kubectl rollout restart deployment/trading-agent -n moon-dev-eda
```

---

## Performance Tuning

### Kafka Tuning

```yaml
# In values.yaml
kafka:
  broker:
    jvmHeapSize: 4G
  resources:
    limits:
      memory: 8Gi
      cpu: 4000m
```

### TimescaleDB Tuning

```sql
-- Increase work_mem for faster sorts
ALTER SYSTEM SET work_mem = '256MB';

-- Increase shared_buffers
ALTER SYSTEM SET shared_buffers = '4GB';

-- Reload config
SELECT pg_reload_conf();
```

### Redis Tuning

```bash
# Increase max memory
redis-cli CONFIG SET maxmemory 64gb
redis-cli CONFIG SET maxmemory-policy allkeys-lru

# Persist changes
redis-cli CONFIG REWRITE
```

---

## Quantitative Agents Setup

### Quick Start with Quant Agents

```bash
# 1. Apply database schema
psql -U postgres -d moon_dev -f infrastructure/schema_quant.sql

# 2. Install additional dependencies
pip install numpy scipy pandas

# 3. Enable agents in src/main.py
# Edit ACTIVE_AGENTS dict:
ACTIVE_AGENTS = {
    'quant_anomaly': True,
    'quant_signal_agg': True,
    'quant_transaction': True,
    'quant_backtest': True,
    'quant_capacity': True,
    'quant_decay': True,
    'quant_regime': True,
    'quant_correlation': True,
    'quant_portfolio': True,
    'quant_altdata': True,
}

# 4. Run the system
python src/main.py
```

### Quant Agent Documentation

- **Quick Start**: [QUANT_AGENTS_QUICKSTART.md](QUANT_AGENTS_QUICKSTART.md)
- **Integration Guide**: [QUANT_AGENTS_INTEGRATION_GUIDE.md](QUANT_AGENTS_INTEGRATION_GUIDE.md)
- **Implementation Status**: [QUANT_AGENTS_IMPLEMENTATION_STATUS.md](QUANT_AGENTS_IMPLEMENTATION_STATUS.md)
- **Agent Details**: [src/agents/quant/README.md](src/agents/quant/README.md)

### Key Features

- **Event-Driven**: All agents communicate via Kafka
- **Statistical Rigor**: p-values, Sharpe ratios, significance testing
- **Automatic Decay Detection**: Signals automatically retired when degraded
- **Transaction Cost Modeling**: Square-root market impact model
- **Portfolio Optimization**: MPT with Kelly Criterion sizing
- **Walk-Forward Backtesting**: 12 rolling windows with statistical validation

---

## Next Steps

1. **Deploy to Staging**: Follow Phase 5 deployment steps
2. **Run Load Tests**: Use locust with realistic traffic patterns
3. **Monitor Metrics**: Set up Grafana dashboards and alerts
4. **Document Runbooks**: Create operational procedures for common scenarios
5. **Train Team**: Ensure all team members understand system architecture
6. **Enable Quant Agents**: Start with a few agents and gradually enable more

---

## Support & Documentation

### General Documentation
- **Architecture**: See `DESIGN.md` in parent folder
- **Requirements**: See `REQUIREMENTS.md` in parent folder  
- **Tasks & Timeline**: See `TASKS.md` in parent folder
- **Real-time Architecture**: See `MOON_DEV_REALTIME_ARCHITECTURE.md`

### Quantitative Agents Documentation
- **Quick Start**: [QUANT_AGENTS_QUICKSTART.md](QUANT_AGENTS_QUICKSTART.md)
- **Integration Guide**: [QUANT_AGENTS_INTEGRATION_GUIDE.md](QUANT_AGENTS_INTEGRATION_GUIDE.md)
- **Implementation Status**: [QUANT_AGENTS_IMPLEMENTATION_STATUS.md](QUANT_AGENTS_IMPLEMENTATION_STATUS.md)
- **Agent Details**: [src/agents/quant/README.md](src/agents/quant/README.md)

---

**Last Updated**: 2025-10-26  
**Version**: 1.0  
**Status**: Implementation Planning Phase
