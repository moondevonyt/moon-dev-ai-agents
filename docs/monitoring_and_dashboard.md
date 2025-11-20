# 🌙 Moon Dev Monitoring & Dashboard Guide

Complete guide to the Agent Health Monitor and Portfolio Dashboard systems.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Agent Health Monitor](#agent-health-monitor)
3. [Portfolio Dashboard](#portfolio-dashboard)
4. [Integration Guide](#integration-guide)
5. [Quick Start](#quick-start)

---

## Overview

Two powerful monitoring systems for Moon Dev's trading agents:

1. **Agent Health Monitor** - Tracks which agents are running, when they last executed, and if APIs are responding
2. **Portfolio Dashboard** - Real-time PnL tracking, win rate analysis, and agent performance leaderboard

---

## Agent Health Monitor

### What It Does

- 🤖 Tracks agent heartbeats (last run time, status)
- 🌐 Monitors API health (response time, up/down status)
- 🚨 Generates alerts for stale agents or down APIs
- 📊 Web dashboard with auto-refresh
- 💾 Stores data in JSON files

### Files

- **Monitor**: `src/agents/agent_health_monitor.py`
- **Web Dashboard**: `src/scripts/health_dashboard.py`
- **Example Integration**: `src/agents/example_monitored_agent.py`
- **Data Directory**: `src/data/health_monitor/`

### Quick Start

```bash
# Option 1: CLI - One-time health report
python src/agents/agent_health_monitor.py

# Option 2: CLI - Continuous monitoring (refreshes every 30s)
python src/agents/agent_health_monitor.py --continuous

# Option 3: Web Dashboard (opens on http://localhost:8002)
python src/scripts/health_dashboard.py
```

### Web Dashboard

Open `http://localhost:8002` in your browser to see:

- ✅ All agents with last run time and status
- 🟢 All APIs with response time and health
- 🚨 Active alerts (stale agents, down APIs)
- Auto-refreshes every 10 seconds

---

## Portfolio Dashboard

### What It Does

- 📈 Tracks all trades (entry/exit, PnL, win/loss)
- 💰 Real-time PnL across all positions
- 🏆 Agent performance leaderboard
- 📊 Win rate analysis by agent
- 🎯 Open positions monitoring
- 💾 Stores data in CSV files

### Files

- **Tracker**: `src/agents/portfolio_tracker.py`
- **Web Dashboard**: `src/scripts/portfolio_dashboard.py`
- **Data Directory**: `src/data/portfolio_tracker/`
  - `trades_history.csv` - All closed trades
  - `open_positions.csv` - Current open positions
  - `agent_performance.json` - Agent stats

### Quick Start

```bash
# Option 1: CLI - Print portfolio summary
python src/agents/portfolio_tracker.py

# Option 2: Web Dashboard (opens on http://localhost:8003)
python src/scripts/portfolio_dashboard.py
```

### Web Dashboard

Open `http://localhost:8003` in your browser to see:

- 📊 Total PnL, win rate, avg PnL/trade
- 🏆 Agent performance leaderboard (sorted by PnL)
- 📈 All open positions
- 📉 Recent trades with PnL details
- Auto-refreshes every 10 seconds

---

## Integration Guide

### Add Health Monitoring to Your Agent

**Step 1:** Import the monitor

```python
from agent_health_monitor import get_monitor

class YourAgent:
    def __init__(self):
        self.monitor = get_monitor()
        self.agent_name = "your_agent_name"
```

**Step 2:** Log heartbeat at start

```python
def run(self):
    try:
        # Log starting
        self.monitor.heartbeat(
            agent_name=self.agent_name,
            status="running",
            metadata={"action": "starting"}
        )

        # Your agent logic...

        # Log success
        self.monitor.heartbeat(
            agent_name=self.agent_name,
            status="success"
        )
    except Exception as e:
        # Log error
        self.monitor.heartbeat(
            agent_name=self.agent_name,
            status="error",
            metadata={"error": str(e)}
        )
```

**Step 3:** Monitor API health

```python
import time

def call_api(self):
    start = time.time()
    try:
        response = requests.get("https://api.example.com")
        response_time = time.time() - start

        status = "slow" if response_time > 3 else "up"

        self.monitor.log_api_status(
            api_name="example_api",
            status=status,
            response_time=response_time
        )
    except Exception as e:
        self.monitor.log_api_status(
            api_name="example_api",
            status="down",
            error=str(e)
        )
```

### Add Portfolio Tracking to Your Agent

**Step 1:** Import the tracker

```python
from portfolio_tracker import get_tracker

class YourAgent:
    def __init__(self):
        self.tracker = get_tracker()
```

**Step 2:** Log position open

```python
def buy_token(self, token_address, token_symbol, price, quantity, usd_value):
    # Execute buy order...

    # Log to portfolio tracker
    position_id = self.tracker.log_position_open(
        agent_name="trading_agent",
        token_address=token_address,
        token_symbol=token_symbol,
        entry_price=price,
        quantity=quantity,
        usd_value=usd_value,
        strategy="momentum_breakout",
        notes="AI confidence: 85%"
    )

    # Save position_id for later
    return position_id
```

**Step 3:** Log position close

```python
def sell_token(self, position_id, exit_price, fees=0):
    # Execute sell order...

    # Log to portfolio tracker
    trade = self.tracker.log_position_close(
        position_id=position_id,
        exit_price=exit_price,
        fees_usd=fees,
        notes="Stop loss triggered"
    )

    # trade dict contains PnL info
    print(f"PnL: ${trade['pnl_usd']:.2f}")
```

---

## Complete Integration Example

```python
"""
Example Trading Agent with Full Monitoring
"""

from agent_health_monitor import get_monitor
from portfolio_tracker import get_tracker
import time

class MonitoredTradingAgent:
    def __init__(self):
        self.health_monitor = get_monitor()
        self.portfolio_tracker = get_tracker()
        self.agent_name = "example_trading_agent"

    def run(self):
        """Main agent loop"""
        try:
            # Log agent starting
            self.health_monitor.heartbeat(
                agent_name=self.agent_name,
                status="running"
            )

            # Check API health
            self._check_birdeye_api()

            # Analyze market
            signal = self.analyze_market()

            if signal == "BUY":
                self.execute_buy()
            elif signal == "SELL":
                self.execute_sell()

            # Log success
            self.health_monitor.heartbeat(
                agent_name=self.agent_name,
                status="success",
                metadata={"signal": signal}
            )

        except Exception as e:
            # Log error
            self.health_monitor.heartbeat(
                agent_name=self.agent_name,
                status="error",
                metadata={"error": str(e)}
            )
            raise

    def _check_birdeye_api(self):
        """Monitor BirdEye API health"""
        import requests

        start = time.time()
        try:
            response = requests.get(
                "https://public-api.birdeye.so/public/tokenlist",
                timeout=5
            )
            response_time = time.time() - start

            status = "slow" if response_time > 3 else "up"
            self.health_monitor.log_api_status(
                api_name="birdeye",
                status=status,
                response_time=response_time
            )
        except Exception as e:
            self.health_monitor.log_api_status(
                api_name="birdeye",
                status="down",
                error=str(e)
            )

    def execute_buy(self):
        """Buy token and track in portfolio"""
        # Your buy logic...
        token_address = "..."
        token_symbol = "TOKEN"
        entry_price = 0.001
        quantity = 1000
        usd_value = 1.0

        # Log position opening
        position_id = self.portfolio_tracker.log_position_open(
            agent_name=self.agent_name,
            token_address=token_address,
            token_symbol=token_symbol,
            entry_price=entry_price,
            quantity=quantity,
            usd_value=usd_value,
            strategy="momentum"
        )

        # Save position_id for later
        self.current_position = position_id

    def execute_sell(self):
        """Sell token and calculate PnL"""
        # Your sell logic...
        exit_price = 0.0012
        fees = 0.01

        # Log position closing (calculates PnL automatically)
        trade = self.portfolio_tracker.log_position_close(
            position_id=self.current_position,
            exit_price=exit_price,
            fees_usd=fees
        )

        print(f"Trade closed: PnL = ${trade['pnl_usd']:.2f}")
```

---

## Quick Start - All Dashboards

Run all monitoring dashboards in separate terminals:

```bash
# Terminal 1: Agent Health Monitor
python src/scripts/health_dashboard.py
# Open: http://localhost:8002

# Terminal 2: Portfolio Dashboard
python src/scripts/portfolio_dashboard.py
# Open: http://localhost:8003

# Terminal 3: Backtest Dashboard (if you have it)
python src/scripts/backtestdashboard.py
# Open: http://localhost:8001
```

---

## Data Storage

### Agent Health Monitor

```
src/data/health_monitor/
├── agent_heartbeats.json     # Agent last run times
└── api_status.json            # API health status
```

### Portfolio Tracker

```
src/data/portfolio_tracker/
├── trades_history.csv         # All closed trades
├── open_positions.csv         # Current positions
└── agent_performance.json     # Agent stats
```

---

## Alerts & Notifications

### Agent Health Alerts

- ⚠️ Agent hasn't run in > 60 minutes
- ❌ Agent last run resulted in error
- 🔴 API is down
- 🟡 API response time > 3 seconds

### Portfolio Alerts

Currently displayed in dashboard:
- Total PnL (positive/negative)
- Win rate (above/below 50%)
- Individual agent performance

---

## Tips

1. **Start dashboards on system boot** - Add to cron/systemd
2. **Monitor on mobile** - Dashboards are responsive
3. **Export data** - CSVs can be opened in Excel/Sheets
4. **Add custom alerts** - Modify code for Telegram/Discord
5. **Backup data** - CSV/JSON files are in `src/data/`

---

## Future Enhancements

Potential additions:
- [ ] Telegram bot for alerts
- [ ] Discord webhook integration
- [ ] Email notifications for critical alerts
- [ ] Export reports (PDF/CSV)
- [ ] Historical performance charts
- [ ] Multi-timeframe analysis
- [ ] Sharpe ratio calculations
- [ ] Comparison with buy-and-hold

---

Built with love by Moon Dev 🌙🚀
