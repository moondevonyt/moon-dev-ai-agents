# 🚀 Deployment Checklist

## Jim Simons-Style Quantitative Trading System

Use this checklist to deploy the quant agents to production.

---

## ✅ Pre-Deployment Checklist

### 1. Infrastructure Requirements

- [ ] **Kafka** is running and accessible
  - Default: `localhost:9092`
  - Test: `kafka-topics.sh --list --bootstrap-server localhost:9092`

- [ ] **Redis** is running and accessible
  - Default: `localhost:6379`
  - Test: `redis-cli ping` (should return "PONG")

- [ ] **TimescaleDB/PostgreSQL** is running and accessible
  - Default: `localhost:5432`
  - Test: `psql -U your_user -d your_database -c "SELECT version();"`

### 2. Database Setup

- [ ] **Apply schema** to TimescaleDB
  ```bash
  cd MOON_DEV_EDA_IMPLEMENTATION
  psql -U your_user -d your_database -f infrastructure/schema_quant.sql
  ```

- [ ] **Verify tables** were created
  ```sql
  SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename LIKE '%quant%';
  ```
  Should show: `signal_weights`, `strategy_capacity`, `signal_performance`, etc.

### 3. Python Dependencies

- [ ] **Install required packages**
  ```bash
  pip install numpy scipy pandas termcolor
  ```

- [ ] **Verify installations**
  ```bash
  python -c "import numpy, scipy, pandas, termcolor; print('All dependencies installed')"
  ```

### 4. Configuration

- [ ] **Review config.py** settings
  - Check `src/config.py` lines 140-220
  - Adjust thresholds if needed (defaults are production-ready)

- [ ] **Set environment variables** (if needed)
  - Kafka host/port
  - Redis host/port
  - Database connection string

---

## 🔧 Deployment Steps

### Step 1: Enable Agents

Edit `src/main.py` and enable desired agents:

```python
ACTIVE_AGENTS = {
    # Start with core agents
    'quant_anomaly': True,         # Anomaly detection
    'quant_signal_agg': True,      # Signal aggregation
    'quant_transaction': True,     # Transaction cost analysis
    
    # Add validation agents
    'quant_backtest': True,        # Backtesting validation
    'quant_capacity': True,        # Capacity monitoring
    'quant_decay': True,           # Signal decay monitoring
    
    # Add advanced agents
    'quant_regime': True,          # Regime detection
    'quant_correlation': True,     # Correlation analysis
    'quant_portfolio': True,       # Portfolio optimization
    'quant_altdata': True,         # Alternative data
}
```

**Recommendation:** Start with 3-5 agents, then gradually enable more.

### Step 2: Test Individual Agents

Test each agent standalone before running the full system:

```bash
# Test anomaly detection
python -m src.agents.quant.anomaly_detection_agent

# Test signal aggregation
python -m src.agents.quant.signal_aggregation_agent

# Test transaction cost
python -m src.agents.quant.transaction_cost_agent
```

Press `Ctrl+C` to stop each test.

### Step 3: Run the Full System

```bash
cd MOON_DEV_EDA_IMPLEMENTATION
python src/main.py
```

### Step 4: Monitor Startup

Watch for these startup messages:

```
🌙 Moon Dev AI Agent Trading System Starting...
📊 Active Agents:
  • Quant_anomaly: ✅ ON
  • Quant_signal_agg: ✅ ON
  ...

🔬 Starting X quantitative agents...
✅ Quantitative agents running in background thread
```

### Step 5: Verify Agent Operation

Check logs for successful event processing:

```
🔬 [AnomalyDetectionAgent] Subscribed to topics: ['price.tick']
✅ [SignalAggregationAgent] Initialized with 0 signals
🔬 [TransactionCostAgent] Cost model initialized
```

---

## 🔍 Post-Deployment Verification

### 1. Check Agent Health

- [ ] All agents started without errors
- [ ] Agents are processing events (check logs)
- [ ] No connection errors to Kafka/Redis/DB

### 2. Verify Event Flow

- [ ] Price ticks are being received
- [ ] Anomalies are being detected
- [ ] Signals are being aggregated
- [ ] Events are being stored in database

### 3. Database Verification

```sql
-- Check if events are being stored
SELECT COUNT(*) FROM signal_weights;
SELECT COUNT(*) FROM signal_performance;
SELECT COUNT(*) FROM strategy_capacity;

-- Check recent activity
SELECT * FROM signal_weights ORDER BY timestamp DESC LIMIT 10;
```

### 4. Redis Verification

```bash
# Check if data is being cached
redis-cli KEYS "quant:*"

# Check specific agent data
redis-cli HGETALL "quant:signal_weights"
redis-cli HGETALL "quant:signal_performance"
```

---

## 🐛 Troubleshooting

### Issue: Agents Not Starting

**Symptoms:** No quant agent startup messages

**Solutions:**
1. Check that at least one quant agent is enabled in `ACTIVE_AGENTS`
2. Verify Python path includes project root
3. Check for import errors in logs

### Issue: Kafka Connection Errors

**Symptoms:** `KafkaError: Failed to connect to broker`

**Solutions:**
1. Verify Kafka is running: `kafka-topics.sh --list --bootstrap-server localhost:9092`
2. Check Kafka host/port in config
3. Ensure Kafka is accessible from your network

### Issue: Redis Connection Errors

**Symptoms:** `redis.exceptions.ConnectionError`

**Solutions:**
1. Verify Redis is running: `redis-cli ping`
2. Check Redis host/port in config
3. Ensure Redis is accessible from your network

### Issue: Database Errors

**Symptoms:** `psycopg2.errors.UndefinedTable`

**Solutions:**
1. Apply schema: `psql -f infrastructure/schema_quant.sql`
2. Verify tables exist: `\dt` in psql
3. Check database connection string

### Issue: Import Errors

**Symptoms:** `ModuleNotFoundError: No module named 'scipy'`

**Solutions:**
1. Install dependencies: `pip install numpy scipy pandas termcolor`
2. Verify installation: `python -c "import scipy"`
3. Check Python environment (venv, conda, etc.)

### Issue: No Events Being Processed

**Symptoms:** Agents start but no activity in logs

**Solutions:**
1. Verify Kafka topics exist and have data
2. Check that price ticks are being published
3. Verify agent subscriptions match topic names
4. Check Kafka consumer group status

---

## 📊 Monitoring

### Logs to Watch

Monitor these log patterns:

**Good Signs:**
- `✅ [AgentName] Successfully processed event`
- `🔬 [AgentName] Detected anomaly`
- `✅ [AgentName] Signal aggregated`

**Warning Signs:**
- `⚠️ [AgentName] Warning: ...`
- `⚠️ [AgentName] Retrying...`

**Error Signs:**
- `❌ [AgentName] Error: ...`
- `❌ [AgentName] Failed to connect`

### Performance Metrics

Monitor these metrics:

- **Event Processing Rate:** Should be 100+ events/second per agent
- **Latency:** Should be < 10ms per event
- **Memory Usage:** Should be ~100MB per agent
- **Error Rate:** Should be < 1%

### Health Checks

Run periodic health checks:

```python
# In Python console
from src.agents.quant.anomaly_detection_agent import AnomalyDetectionAgent
agent = AnomalyDetectionAgent()
print(agent.health_check())  # Should return agent status
```

---

## 🔄 Graceful Shutdown

To stop the system:

1. Press `Ctrl+C` in the terminal
2. Wait for graceful shutdown messages:
   ```
   👋 Gracefully shutting down...
   🔬 [AgentName] Shutting down...
   ✅ [AgentName] Shutdown complete
   ```
3. Verify all agents stopped cleanly

---

## 📈 Scaling Considerations

### Horizontal Scaling

To scale agents horizontally:

1. Run multiple instances of main.py
2. Each instance will process events independently
3. Kafka consumer groups handle load balancing
4. Redis and TimescaleDB are shared

### Vertical Scaling

To scale agents vertically:

1. Increase Python process resources (CPU, memory)
2. Tune Kafka consumer settings (batch size, fetch size)
3. Optimize Redis connection pooling
4. Tune TimescaleDB query performance

---

## ✅ Production Readiness Checklist

- [ ] All infrastructure is running (Kafka, Redis, TimescaleDB)
- [ ] Database schema is applied
- [ ] Dependencies are installed
- [ ] Configuration is reviewed and tuned
- [ ] Individual agents tested successfully
- [ ] Full system tested successfully
- [ ] Event flow verified
- [ ] Database writes verified
- [ ] Redis caching verified
- [ ] Logs are being monitored
- [ ] Error handling tested
- [ ] Graceful shutdown tested
- [ ] Performance metrics are acceptable
- [ ] Backup and recovery plan in place

---

## 🎉 You're Ready!

Once all checklist items are complete, your Jim Simons-style quantitative trading system is ready for production use!

**Next Steps:**
1. Monitor system performance for 24-48 hours
2. Tune configuration parameters based on results
3. Gradually enable more agents
4. Add optional enhancements (Prometheus, Grafana, etc.)

---

**Built with ❤️ by Moon Dev and Kiro AI**  
**Date:** October 26, 2025  
**Status:** ✅ PRODUCTION READY
