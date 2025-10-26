"""
FastAPI application for Moon Dev EDA System

Provides REST endpoints for:
- Health checks and readiness probes
- Portfolio state and metrics
- Backtesting execution and results
- WebSocket real-time updates
- Metrics export (Prometheus)
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, Path, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import generate_latest, Counter, Histogram, Gauge
import uvicorn

from src.core.cache_layer import CacheLayer
from src.core.event_store import EventStore
from src.core.models import EventType
from src.backtesting.engine import BacktestEngine
from src.backtesting.calculator import PerformanceCalculator

# ============================================================================
# Logging Configuration
# ============================================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# Prometheus Metrics
# ============================================================================

# HTTP endpoint metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"]
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "endpoint"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)
)

# WebSocket metrics
websocket_connections = Gauge(
    "websocket_connections",
    "Active WebSocket connections",
    ["type"]
)

websocket_messages_sent = Counter(
    "websocket_messages_sent_total",
    "WebSocket messages sent",
    ["type"]
)

# Backtest metrics
backtest_executions = Counter(
    "backtest_executions_total",
    "Total backtest runs",
    ["status"]  # success, failure, timeout
)

backtest_duration_seconds = Histogram(
    "backtest_duration_seconds",
    "Backtest execution time",
    buckets=(0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 300.0)
)

# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="Moon Dev EDA API",
    description="Real-time Event-Driven Architecture Trading System",
    version="1.0.0-alpha"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Global Resources
# ============================================================================

cache_layer: Optional[CacheLayer] = None
event_store: Optional[EventStore] = None
backtest_engine: Optional[BacktestEngine] = None

# Active WebSocket connections
active_portfolio_connections: Dict[str, List[WebSocket]] = {}
active_backtest_connections: Dict[str, List[WebSocket]] = {}

# ============================================================================
# Startup/Shutdown Events
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize database and cache connections on startup."""
    global cache_layer, event_store, backtest_engine
    
    logger.info("🚀 Starting Moon Dev EDA API Server")
    
    try:
        # Initialize cache layer
        cache_layer = CacheLayer()
        await cache_layer.connect()
        logger.info("✅ Cache layer initialized")
        
        # Initialize event store
        event_store = EventStore()
        await event_store.connect()
        logger.info("✅ Event store initialized")
        
        # Initialize backtest engine
        backtest_engine = BacktestEngine(cache_layer, event_store)
        logger.info("✅ Backtest engine initialized")
        
    except Exception as e:
        logger.error(f"❌ Startup error: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Close database and cache connections on shutdown."""
    global cache_layer, event_store
    
    logger.info("🛑 Shutting down Moon Dev EDA API Server")
    
    try:
        if cache_layer:
            await cache_layer.close()
        if event_store:
            await event_store.close()
    except Exception as e:
        logger.error(f"❌ Shutdown error: {e}")


# ============================================================================
# Health Check Endpoints
# ============================================================================

@app.get("/health", tags=["Health"])
async def health_check() -> Dict[str, str]:
    """
    Basic health check endpoint (liveness probe).
    
    Returns immediately with status. Used by Kubernetes liveness probes.
    """
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.get("/ready", tags=["Health"])
async def readiness_check() -> Dict[str, Any]:
    """
    Readiness probe checking all dependencies.
    
    Verifies:
    - Cache layer (Redis) connectivity
    - Event store (TimescaleDB) connectivity
    - Backtest engine initialization
    
    Returns 503 if any dependency is unavailable.
    """
    global cache_layer, event_store, backtest_engine
    
    status = {
        "ready": True,
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "cache": "down",
            "event_store": "down",
            "backtest_engine": "down"
        }
    }
    
    try:
        # Check cache connectivity
        if cache_layer:
            ping_result = await cache_layer.cache.ping()
            if ping_result:
                status["services"]["cache"] = "up"
    except Exception as e:
        logger.warning(f"Cache check failed: {e}")
    
    try:
        # Check event store connectivity
        if event_store and event_store.pool:
            async with event_store.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            status["services"]["event_store"] = "up"
    except Exception as e:
        logger.warning(f"Event store check failed: {e}")
    
    try:
        # Check backtest engine
        if backtest_engine:
            status["services"]["backtest_engine"] = "up"
    except Exception as e:
        logger.warning(f"Backtest engine check failed: {e}")
    
    # Mark as not ready if any critical service is down
    if status["services"]["cache"] == "down" or status["services"]["event_store"] == "down":
        status["ready"] = False
    
    http_code = 200 if status["ready"] else 503
    return JSONResponse(status, status_code=http_code)


# ============================================================================
# Portfolio Management Endpoints
# ============================================================================

@app.get("/portfolio/{user_id}", tags=["Portfolio"])
async def get_portfolio(
    user_id: str = Path(..., description="User ID")
) -> Dict[str, Any]:
    """
    Get current portfolio state for a user.
    
    Returns:
    - Positions (active trades with unrealized P&L)
    - Balance (cash available)
    - Metrics (leverage ratio, liquidation distance, daily P&L)
    - Timestamp (last update)
    """
    global cache_layer
    
    if not cache_layer:
        raise HTTPException(status_code=503, detail="Cache layer unavailable")
    
    try:
        portfolio = await cache_layer.get_portfolio(user_id)
        
        if portfolio:
            return {
                "user_id": user_id,
                "positions": portfolio.get("positions", []),
                "balance": portfolio.get("balance", 0.0),
                "metrics": portfolio.get("metrics", {}),
                "timestamp": portfolio.get("timestamp", datetime.utcnow().isoformat()),
                "status": "success"
            }
        else:
            return {
                "user_id": user_id,
                "positions": [],
                "balance": 0.0,
                "metrics": {},
                "timestamp": datetime.utcnow().isoformat(),
                "status": "not_found"
            }
    
    except Exception as e:
        logger.error(f"Error fetching portfolio: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/portfolio/{user_id}/positions", tags=["Portfolio"])
async def get_positions(
    user_id: str = Path(..., description="User ID")
) -> Dict[str, Any]:
    """
    Get open positions for a user.
    
    Returns array of positions with:
    - token (trading pair)
    - direction (long/short)
    - size (quantity)
    - entry_price
    - current_price
    - unrealized_pnl
    - unrealized_pnl_pct
    """
    global cache_layer
    
    if not cache_layer:
        raise HTTPException(status_code=503, detail="Cache layer unavailable")
    
    try:
        portfolio = await cache_layer.get_portfolio(user_id)
        
        if portfolio and portfolio.get("positions"):
            return {
                "user_id": user_id,
                "count": len(portfolio["positions"]),
                "positions": portfolio["positions"],
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            return {
                "user_id": user_id,
                "count": 0,
                "positions": [],
                "timestamp": datetime.utcnow().isoformat()
            }
    
    except Exception as e:
        logger.error(f"Error fetching positions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/portfolio/{user_id}/metrics", tags=["Portfolio"])
async def get_portfolio_metrics(
    user_id: str = Path(..., description="User ID")
) -> Dict[str, Any]:
    """
    Get portfolio metrics for a user.
    
    Returns:
    - leverage_ratio: Current leverage (total_exposure / balance)
    - liquidation_distance: Margin remaining before liquidation (0-1)
    - daily_pnl: Daily profit/loss
    - daily_pnl_pct: Daily P&L as percentage
    - hourly_pnl: Hourly profit/loss
    - roi: Return on investment (%)
    """
    global cache_layer
    
    if not cache_layer:
        raise HTTPException(status_code=503, detail="Cache layer unavailable")
    
    try:
        portfolio = await cache_layer.get_portfolio(user_id)
        
        if portfolio:
            return {
                "user_id": user_id,
                "metrics": portfolio.get("metrics", {}),
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            return {
                "user_id": user_id,
                "metrics": {},
                "timestamp": datetime.utcnow().isoformat()
            }
    
    except Exception as e:
        logger.error(f"Error fetching metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Event History Endpoints
# ============================================================================

@app.get("/events", tags=["Events"])
async def query_events(
    token: Optional[str] = Query(None, description="Token filter (e.g., BTC-USD)"),
    event_type: Optional[str] = Query(None, description="Event type filter"),
    start_time: Optional[str] = Query(None, description="Start time (ISO 8601)"),
    end_time: Optional[str] = Query(None, description="End time (ISO 8601)"),
    limit: int = Query(100, ge=1, le=1000, description="Result limit")
) -> Dict[str, Any]:
    """
    Query events from event store with optional filters.
    
    Query parameters:
    - token: Filter by trading pair
    - event_type: Filter by event type
    - start_time: ISO 8601 start timestamp
    - end_time: ISO 8601 end timestamp
    - limit: Maximum results (default 100, max 1000)
    """
    global event_store
    
    if not event_store:
        raise HTTPException(status_code=503, detail="Event store unavailable")
    
    try:
        # Parse timestamps if provided
        start_dt = None
        end_dt = None
        
        if start_time:
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        if end_time:
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        
        # Query event store
        events = await event_store.query_by_date_range(
            start_dt or datetime.utcnow(),
            end_dt or datetime.utcnow(),
            token=token,
            event_type=event_type
        )
        
        # Limit results
        events = events[:limit]
        
        return {
            "count": len(events),
            "events": events,
            "filters": {
                "token": token,
                "event_type": event_type,
                "start_time": start_time,
                "end_time": end_time
            }
        }
    
    except Exception as e:
        logger.error(f"Error querying events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Backtesting Endpoints
# ============================================================================

@app.post("/backtest/run", tags=["Backtesting"])
async def run_backtest(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    initial_balance: float = Query(50000.0, gt=0, description="Initial balance"),
    tokens: Optional[str] = Query(None, description="Comma-separated tokens"),
    agents: Optional[str] = Query(None, description="Comma-separated agent names")
) -> Dict[str, Any]:
    """
    Run a backtest with specified parameters.
    
    Parameters:
    - start_date: Start date (YYYY-MM-DD)
    - end_date: End date (YYYY-MM-DD)
    - initial_balance: Starting capital (default 50000.0)
    - tokens: Comma-separated token list (e.g., BTC-USD,ETH-USD)
    - agents: Comma-separated agent names (e.g., risk_agent,trading_agent)
    
    Returns backtest results with performance metrics.
    """
    global backtest_engine
    
    if not backtest_engine:
        raise HTTPException(status_code=503, detail="Backtest engine unavailable")
    
    try:
        # Parse dates
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        # Parse token list
        token_list = None
        if tokens:
            token_list = [t.strip().upper() for t in tokens.split(",")]
        
        # Parse agent list
        agent_list = None
        if agents:
            agent_list = [a.strip().lower() for a in agents.split(",")]
        
        # Run backtest
        results = await backtest_engine.run_backtest(
            start_date=start,
            end_date=end,
            initial_balance=initial_balance,
            tokens=token_list,
            agents=agent_list
        )
        
        backtest_executions.labels(status="success").inc()
        
        return {
            "status": "completed",
            "results": results.to_dict(),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error running backtest: {e}")
        backtest_executions.labels(status="failure").inc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/backtest/{backtest_id}", tags=["Backtesting"])
async def get_backtest_results(
    backtest_id: str = Path(..., description="Backtest ID")
) -> Dict[str, Any]:
    """
    Get results for a completed backtest.
    
    Returns backtest results with all performance metrics.
    """
    global event_store
    
    if not event_store:
        raise HTTPException(status_code=503, detail="Event store unavailable")
    
    try:
        # Query event store for backtest results
        # This would be implemented with actual storage
        return {
            "backtest_id": backtest_id,
            "status": "not_found",
            "message": "Backtest results not found"
        }
    
    except Exception as e:
        logger.error(f"Error fetching backtest: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# WebSocket Endpoints
# ============================================================================

@app.websocket("/ws/portfolio/{user_id}")
async def websocket_portfolio(
    websocket: WebSocket,
    user_id: str = Path(..., description="User ID")
):
    """
    WebSocket endpoint for real-time portfolio updates.
    
    Streams:
    - Position updates (opens, closes, size changes)
    - Balance changes
    - Risk alerts (leverage, liquidation warnings)
    - P&L updates
    
    Connection format:
    {
        "type": "position_update|balance_update|risk_alert|pnl_update",
        "user_id": "user_123",
        "data": {...}
    }
    """
    global cache_layer, websocket_connections
    
    await websocket.accept()
    
    # Track connection
    if user_id not in active_portfolio_connections:
        active_portfolio_connections[user_id] = []
    active_portfolio_connections[user_id].append(websocket)
    websocket_connections.labels(type="portfolio").inc()
    
    logger.info(f"📡 Portfolio WebSocket connected: {user_id}")
    
    try:
        # Send initial portfolio state
        if cache_layer:
            portfolio = await cache_layer.get_portfolio(user_id)
            if portfolio:
                await websocket.send_json({
                    "type": "initial_state",
                    "data": portfolio,
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        # Keep connection open and listen for messages
        while True:
            # In production, this would subscribe to real-time events
            # For now, just keep the connection alive
            await asyncio.sleep(5)
            
            # Send periodic updates
            if cache_layer:
                portfolio = await cache_layer.get_portfolio(user_id)
                if portfolio:
                    await websocket.send_json({
                        "type": "portfolio_update",
                        "data": portfolio,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    websocket_messages_sent.labels(type="portfolio").inc()
    
    except WebSocketDisconnect:
        # Remove connection
        if user_id in active_portfolio_connections:
            active_portfolio_connections[user_id].remove(websocket)
            if not active_portfolio_connections[user_id]:
                del active_portfolio_connections[user_id]
        websocket_connections.labels(type="portfolio").dec()
        logger.info(f"📡 Portfolio WebSocket disconnected: {user_id}")
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        websocket_connections.labels(type="portfolio").dec()


@app.websocket("/ws/backtest/{backtest_id}")
async def websocket_backtest(
    websocket: WebSocket,
    backtest_id: str = Path(..., description="Backtest ID")
):
    """
    WebSocket endpoint for real-time backtest progress.
    
    Streams backtest execution progress:
    - Progress percentage
    - Current date being processed
    - Trades executed
    - Performance metrics updates
    
    Connection format:
    {
        "type": "progress|trade_executed|metrics_update",
        "backtest_id": "backtest_123",
        "data": {...}
    }
    """
    await websocket.accept()
    
    # Track connection
    if backtest_id not in active_backtest_connections:
        active_backtest_connections[backtest_id] = []
    active_backtest_connections[backtest_id].append(websocket)
    websocket_connections.labels(type="backtest").inc()
    
    logger.info(f"📡 Backtest WebSocket connected: {backtest_id}")
    
    try:
        # Listen for backtest events (in production)
        while True:
            await asyncio.sleep(10)
    
    except WebSocketDisconnect:
        # Remove connection
        if backtest_id in active_backtest_connections:
            active_backtest_connections[backtest_id].remove(websocket)
            if not active_backtest_connections[backtest_id]:
                del active_backtest_connections[backtest_id]
        websocket_connections.labels(type="backtest").dec()
        logger.info(f"📡 Backtest WebSocket disconnected: {backtest_id}")
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        websocket_connections.labels(type="backtest").dec()


# ============================================================================
# Metrics Export Endpoint
# ============================================================================

@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """
    Export Prometheus metrics in text format.
    
    Includes:
    - HTTP request metrics
    - WebSocket connection metrics
    - Backtest execution metrics
    - Business metrics (trades, signals, alerts)
    """
    return generate_latest()


# ============================================================================
# API Documentation
# ============================================================================

@app.get("/", tags=["Documentation"])
async def root():
    """Root endpoint with API documentation."""
    return {
        "name": "Moon Dev EDA API",
        "version": "1.0.0-alpha",
        "documentation": "/docs",
        "openapi": "/openapi.json",
        "endpoints": {
            "health": "/health",
            "readiness": "/ready",
            "portfolio": "/portfolio/{user_id}",
            "events": "/events",
            "backtesting": "/backtest/run",
            "metrics": "/metrics"
        }
    }


# ============================================================================
# Server Startup (for local development)
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
