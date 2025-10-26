"""
Load Tests - Locust File

Performance testing for Moon Dev EDA API.

Run with:
  locust -f tests/load/locustfile.py --users 1000 --spawn-rate 50
"""

import random
from datetime import datetime, timedelta
from locust import HttpUser, task, between, events
import logging

logger = logging.getLogger(__name__)


class MoonDevUser(HttpUser):
    """
    Simulated user for Moon Dev EDA API.
    
    Tasks:
    - Check health (every request)
    - Query portfolio (30% of requests)
    - Query events (40% of requests)
    - Run backtest (10% of requests)
    - Get metrics (20% of requests)
    """
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests
    
    def on_start(self):
        """Initialize user with test data."""
        self.user_id = f"load_test_user_{random.randint(1, 1000)}"
        self.tokens = ["BTC-USD", "ETH-USD", "SOL-USD", "ADA-USD"]
        self.event_types = ["price_tick", "signal_generated", "trade_executed"]
    
    @task(5)
    def health_check(self):
        """Health check endpoint (5x weight)."""
        self.client.get(
            "/health",
            name="/health",
            timeout=5
        )
    
    @task(3)
    def get_portfolio(self):
        """Get user portfolio (3x weight)."""
        self.client.get(
            f"/portfolio/{self.user_id}",
            name="/portfolio/[user_id]",
            timeout=5
        )
    
    @task(2)
    def get_positions(self):
        """Get user positions (2x weight)."""
        self.client.get(
            f"/portfolio/{self.user_id}/positions",
            name="/portfolio/[user_id]/positions",
            timeout=5
        )
    
    @task(2)
    def get_metrics(self):
        """Get portfolio metrics (2x weight)."""
        self.client.get(
            f"/portfolio/{self.user_id}/metrics",
            name="/portfolio/[user_id]/metrics",
            timeout=5
        )
    
    @task(4)
    def query_events(self):
        """Query events with random filters (4x weight)."""
        params = {
            "token": random.choice(self.tokens),
            "limit": random.choice([10, 50, 100]),
        }
        
        if random.random() > 0.5:
            # Add time filter
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=random.randint(1, 24))
            params["start_time"] = start_time.isoformat()
            params["end_time"] = end_time.isoformat()
        
        self.client.get(
            "/events",
            params=params,
            name="/events",
            timeout=10
        )
    
    @task(1)
    def run_backtest(self):
        """Run backtest simulation (1x weight)."""
        end_date = datetime.utcnow().date()
        start_date = (datetime.utcnow() - timedelta(days=random.randint(7, 30))).date()
        
        self.client.post(
            "/backtest/run",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "initial_balance": random.choice([10000, 50000, 100000]),
                "tokens": ",".join(random.sample(self.tokens, k=random.randint(1, 3))),
            },
            name="/backtest/run",
            timeout=30
        )
    
    @task(2)
    def get_metrics_export(self):
        """Get Prometheus metrics (2x weight)."""
        self.client.get(
            "/metrics",
            name="/metrics",
            timeout=10
        )
    
    @task(1)
    def readiness_check(self):
        """Readiness probe (1x weight)."""
        self.client.get(
            "/ready",
            name="/ready",
            timeout=5
        )


class HighVolumeUser(HttpUser):
    """
    High-volume trading user making rapid requests.
    Simulates active trading scenario.
    """
    
    wait_time = between(0.1, 0.5)  # Very short waits between requests
    
    def on_start(self):
        """Initialize high-volume user."""
        self.user_id = f"hv_user_{random.randint(1, 100)}"
        self.tokens = ["BTC-USD", "ETH-USD"]
    
    @task(10)
    def rapid_portfolio_check(self):
        """Rapid portfolio checks."""
        self.client.get(
            f"/portfolio/{self.user_id}",
            name="/portfolio/[user_id]_rapid",
            timeout=2
        )
    
    @task(5)
    def rapid_metrics_check(self):
        """Rapid metrics checks for risk monitoring."""
        self.client.get(
            f"/portfolio/{self.user_id}/metrics",
            name="/portfolio/[user_id]/metrics_rapid",
            timeout=2
        )


class DataAnalystUser(HttpUser):
    """
    Data analyst user making heavy analytical queries.
    Simulates backtesting and report generation.
    """
    
    wait_time = between(5, 15)  # Long waits between heavy queries
    
    def on_start(self):
        """Initialize data analyst user."""
        self.query_count = 0
    
    @task(1)
    def run_long_backtest(self):
        """Run extended backtest."""
        end_date = datetime.utcnow().date()
        start_date = (datetime.utcnow() - timedelta(days=90)).date()  # 90-day backtest
        
        self.client.post(
            "/backtest/run",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "initial_balance": 250000.0,
                "tokens": "BTC-USD,ETH-USD,SOL-USD",
            },
            name="/backtest/run_long",
            timeout=60
        )
        self.query_count += 1
    
    @task(2)
    def query_large_event_range(self):
        """Query large event date range."""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=30)
        
        self.client.get(
            "/events",
            params={
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "limit": 1000,
            },
            name="/events_large",
            timeout=30
        )
        self.query_count += 1


# ============================================================================
# Event Handlers for Metrics
# ============================================================================

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Log test start."""
    logger.info("🚀 Load test starting")
    logger.info(f"Target: http://{environment.host}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Log test stop and summary."""
    logger.info("🛑 Load test stopped")
    logger.info("\n" + "="*60)
    logger.info("LOAD TEST SUMMARY")
    logger.info("="*60)
    
    stats = environment.stats
    logger.info(f"Total requests: {stats.total.num_requests}")
    logger.info(f"Total failures: {stats.total.num_failures}")
    logger.info(f"Failure rate: {stats.total.fail_ratio*100:.2f}%")
    logger.info(f"Avg response time: {stats.total.avg_response_time:.2f}ms")
    logger.info(f"Min response time: {stats.total.min_response_time:.2f}ms")
    logger.info(f"Max response time: {stats.total.max_response_time:.2f}ms")
    logger.info(f"Median response time: {stats.total.median_response_time:.2f}ms")
    logger.info(f"95th percentile: {stats.total.get_response_time_percentile(0.95):.2f}ms")
    logger.info(f"99th percentile: {stats.total.get_response_time_percentile(0.99):.2f}ms")


@events.request.add_listener
def on_request_success(request_type, name, response_time, response_length, **kwargs):
    """Log successful requests."""
    if response_time > 5000:  # Log slow requests (>5s)
        logger.warning(f"⚠️  Slow request: {name} took {response_time}ms")


@events.request_failure.add_listener
def on_request_failure(request_type, name, response_time, exception, **kwargs):
    """Log failed requests."""
    logger.error(f"❌ Failed request: {name} - {exception}")


# ============================================================================
# Custom Shape Class for Gradual Load Increase
# ============================================================================

class StepLoadShape:
    """
    Gradually increases load over time.
    Useful for finding breaking points.
    """
    
    def tick(self):
        """Return (users, spawn_rate) tuple."""
        run_time = self.get_run_time()
        
        if run_time < 60:
            # Phase 1: 0-60 seconds - ramp to 100 users
            return (int((run_time / 60) * 100), 2)
        
        elif run_time < 120:
            # Phase 2: 60-120 seconds - ramp to 500 users
            return (100 + int(((run_time - 60) / 60) * 400), 5)
        
        elif run_time < 180:
            # Phase 3: 120-180 seconds - ramp to 1000 users
            return (500 + int(((run_time - 120) / 60) * 500), 10)
        
        elif run_time < 300:
            # Phase 4: 180-300 seconds - maintain 1000 users
            return (1000, 0)
        
        else:
            # Phase 5: 300+ seconds - ramp down
            return (max(0, int(1000 - ((run_time - 300) / 60) * 1000)), 10)
