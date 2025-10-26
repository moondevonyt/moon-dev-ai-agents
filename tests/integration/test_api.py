"""
Integration Tests - API Endpoints

Tests REST API and WebSocket endpoints.
"""

import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient

from src.api.main import app


@pytest.fixture
async def http_client():
    """Provide HTTP client for API testing."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
class TestHealthEndpoints:
    """Test health check endpoints."""
    
    async def test_health_check(self, http_client):
        """Test liveness probe."""
        # Act
        response = await http_client.get("/health")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    async def test_readiness_check(self, http_client):
        """Test readiness probe."""
        # Act
        response = await http_client.get("/ready")
        
        # Assert
        assert response.status_code in [200, 503]  # 200 if ready, 503 if not
        data = response.json()
        assert "ready" in data
        assert "services" in data


@pytest.mark.asyncio
class TestPortfolioEndpoints:
    """Test portfolio management endpoints."""
    
    async def test_get_portfolio(self, http_client, sample_portfolio):
        """Test GET /portfolio/{user_id}."""
        # Arrange
        user_id = "test_user"
        
        # Act
        response = await http_client.get(f"/portfolio/{user_id}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == user_id
        assert "positions" in data
        assert "balance" in data
        assert "metrics" in data
    
    async def test_get_positions(self, http_client):
        """Test GET /portfolio/{user_id}/positions."""
        # Arrange
        user_id = "test_user"
        
        # Act
        response = await http_client.get(f"/portfolio/{user_id}/positions")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == user_id
        assert "positions" in data
        assert isinstance(data["positions"], list)
    
    async def test_get_metrics(self, http_client):
        """Test GET /portfolio/{user_id}/metrics."""
        # Arrange
        user_id = "test_user"
        
        # Act
        response = await http_client.get(f"/portfolio/{user_id}/metrics")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == user_id
        assert "metrics" in data


@pytest.mark.asyncio
class TestEventEndpoints:
    """Test event query endpoints."""
    
    async def test_query_events(self, http_client):
        """Test GET /events."""
        # Act
        response = await http_client.get("/events")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert "events" in data
        assert isinstance(data["events"], list)
    
    async def test_query_events_with_filters(self, http_client):
        """Test GET /events with query parameters."""
        # Arrange
        token = "BTC-USD"
        start_time = (datetime.utcnow() - timedelta(hours=1)).isoformat()
        end_time = datetime.utcnow().isoformat()
        
        # Act
        response = await http_client.get(
            "/events",
            params={
                "token": token,
                "start_time": start_time,
                "end_time": end_time,
                "limit": 50,
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert "events" in data
        if len(data["events"]) > 0:
            # Verify token filter worked
            for event in data["events"]:
                assert event.get("token") == token or token is None


@pytest.mark.asyncio
class TestBacktestEndpoints:
    """Test backtest endpoints."""
    
    async def test_run_backtest(self, http_client):
        """Test POST /backtest/run."""
        # Arrange
        start_date = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
        end_date = datetime.utcnow().strftime("%Y-%m-%d")
        
        # Act
        response = await http_client.post(
            "/backtest/run",
            params={
                "start_date": start_date,
                "end_date": end_date,
                "initial_balance": 50000.0,
                "tokens": "BTC-USD,ETH-USD",
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "results" in data or "error" in data
    
    async def test_get_backtest_results(self, http_client):
        """Test GET /backtest/{backtest_id}."""
        # Arrange
        backtest_id = "test_backtest_001"
        
        # Act
        response = await http_client.get(f"/backtest/{backtest_id}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "backtest_id" in data
        assert "status" in data


@pytest.mark.asyncio
class TestMetricsEndpoint:
    """Test metrics export endpoint."""
    
    async def test_metrics_export(self, http_client):
        """Test GET /metrics."""
        # Act
        response = await http_client.get("/metrics")
        
        # Assert
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/plain")
        # Prometheus format check
        assert b"#HELP" in response.content or b"#TYPE" in response.content


@pytest.mark.asyncio
class TestRootEndpoint:
    """Test documentation endpoint."""
    
    async def test_root_endpoint(self, http_client):
        """Test GET /."""
        # Act
        response = await http_client.get("/")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "endpoints" in data
