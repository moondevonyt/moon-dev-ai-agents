"""Trade execution module for submitting orders to exchanges.

Maps to T-3.4 (Execution Engine) in TASKS.md.

Handles:
- Risk constraint validation
- Position sizing calculations
- Order submission to exchanges (HyperLiquid, Solana)
- Fill monitoring and tracking
- Trade state updates
"""

from .engine import ExecutionEngine
from .risk_validator import RiskValidator
from .exchange_adapter import ExchangeAdapter

__all__ = [
    "ExecutionEngine",
    "RiskValidator",
    "ExchangeAdapter",
]
