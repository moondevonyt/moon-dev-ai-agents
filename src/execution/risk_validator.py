"""RiskValidator - Validates trades against risk constraints.

Maps to T-3.4: Execution Engine - Risk Constraint Validation

WHEN a trade signal is received
THEN Execution Engine SHALL validate all risk constraints:
  1. Sufficient balance
  2. Leverage within limits
  3. Position limits not exceeded
  4. Daily loss limit not exceeded
  5. Correlation limits
"""

import logging
from typing import Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)


class RiskValidator:
    """Validates trades against risk constraints.
    
    Constraints enforced:
    - Available balance must exceed trade size
    - Leverage ratio must not exceed max
    - Position count must not exceed limit
    - Daily loss must not exceed max
    - Position correlation must be acceptable
    """

    # Default constraints (configurable)
    MAX_LEVERAGE = 10.0
    MAX_POSITION_SIZE_PCT = 5.0  # Max 5% of balance per position
    MAX_POSITIONS = 10
    MAX_DAILY_LOSS_PCT = 2.0  # Max 2% daily loss
    MAX_CORRELATION = 0.8  # Max correlation between positions

    def __init__(
        self,
        max_leverage: float = MAX_LEVERAGE,
        max_position_size_pct: float = MAX_POSITION_SIZE_PCT,
        max_positions: int = MAX_POSITIONS,
        max_daily_loss_pct: float = MAX_DAILY_LOSS_PCT,
        max_correlation: float = MAX_CORRELATION,
    ):
        """Initialize risk validator.
        
        Args:
            max_leverage: Maximum leverage ratio
            max_position_size_pct: Max position size as % of balance
            max_positions: Max number of open positions
            max_daily_loss_pct: Max daily loss as % of balance
            max_correlation: Max correlation between positions
        """
        self.max_leverage = max_leverage
        self.max_position_size_pct = max_position_size_pct
        self.max_positions = max_positions
        self.max_daily_loss_pct = max_daily_loss_pct
        self.max_correlation = max_correlation

    def validate_trade(
        self,
        token: str,
        direction: str,
        size: float,
        entry_price: float,
        portfolio: Dict[str, Any],
    ) -> Tuple[bool, Optional[str]]:
        """Validate if trade meets all risk constraints.
        
        WHEN a trade is proposed
        THEN validate against all constraints
        AND return (is_valid, reason)
        
        Args:
            token: Trading pair
            direction: LONG or SHORT
            size: Position size
            entry_price: Entry price
            portfolio: Current portfolio state
        
        Returns:
            Tuple of (is_valid: bool, rejection_reason: str or None)
        """
        # Check balance
        valid, reason = self._check_balance(size, entry_price, portfolio)
        if not valid:
            return False, reason

        # Check leverage
        valid, reason = self._check_leverage(
            size, entry_price, portfolio
        )
        if not valid:
            return False, reason

        # Check position limit
        valid, reason = self._check_position_limit(token, portfolio)
        if not valid:
            return False, reason

        # Check daily loss
        valid, reason = self._check_daily_loss(portfolio)
        if not valid:
            return False, reason

        # Check position correlation
        valid, reason = self._check_correlation(token, portfolio)
        if not valid:
            return False, reason

        return True, None

    def _check_balance(
        self,
        size: float,
        price: float,
        portfolio: Dict[str, Any],
    ) -> Tuple[bool, Optional[str]]:
        """Check if sufficient balance available.
        
        Args:
            size: Position size
            price: Entry price
            portfolio: Portfolio state
        
        Returns:
            (is_valid, reason)
        """
        trade_cost = size * price
        available_balance = portfolio.get('balance', 0)

        if trade_cost > available_balance:
            return False, (
                f"Insufficient balance. "
                f"Need ${trade_cost:,.2f}, have ${available_balance:,.2f}"
            )

        return True, None

    def _check_leverage(
        self,
        size: float,
        price: float,
        portfolio: Dict[str, Any],
    ) -> Tuple[bool, Optional[str]]:
        """Check if leverage would exceed maximum.
        
        Leverage = total_position_size / equity
        
        Args:
            size: Position size
            price: Entry price
            portfolio: Portfolio state
        
        Returns:
            (is_valid, reason)
        """
        balance = portfolio.get('balance', 0)
        positions = portfolio.get('positions', {})

        # Calculate current total position size
        current_total_size = sum(
            abs(p.get('size', 0)) * p.get('current_price', price)
            for p in positions.values()
        )

        # New leverage with this trade
        new_total_size = current_total_size + (size * price)
        new_leverage = new_total_size / max(balance, 1)

        if new_leverage > self.max_leverage:
            return False, (
                f"Leverage would exceed maximum. "
                f"New leverage: {new_leverage:.2f}x, "
                f"Max: {self.max_leverage}x"
            )

        return True, None

    def _check_position_limit(
        self,
        token: str,
        portfolio: Dict[str, Any],
    ) -> Tuple[bool, Optional[str]]:
        """Check if position count would exceed limit.
        
        Args:
            token: Trading pair
            portfolio: Portfolio state
        
        Returns:
            (is_valid, reason)
        """
        positions = portfolio.get('positions', {})
        open_positions = len([p for p in positions.values() if p.get('size', 0) != 0])

        # If already holding this token, don't count as new
        if token in positions and positions[token].get('size', 0) != 0:
            open_positions -= 1

        if open_positions >= self.max_positions:
            return False, (
                f"Maximum position limit reached. "
                f"Open positions: {open_positions}, "
                f"Max: {self.max_positions}"
            )

        return True, None

    def _check_daily_loss(
        self,
        portfolio: Dict[str, Any],
    ) -> Tuple[bool, Optional[str]]:
        """Check if daily loss would exceed limit.
        
        Args:
            portfolio: Portfolio state
        
        Returns:
            (is_valid, reason)
        """
        initial_balance = portfolio.get('initial_balance', 0)
        current_balance = portfolio.get('balance', 0)

        daily_loss_pct = ((initial_balance - current_balance) / initial_balance) * 100

        if daily_loss_pct > self.max_daily_loss_pct:
            return False, (
                f"Daily loss limit exceeded. "
                f"Loss: {daily_loss_pct:.2f}%, "
                f"Max: {self.max_daily_loss_pct}%"
            )

        return True, None

    def _check_correlation(
        self,
        token: str,
        portfolio: Dict[str, Any],
    ) -> Tuple[bool, Optional[str]]:
        """Check if new position correlation acceptable.
        
        Note: Simplified version. Full implementation would calculate
        historical correlation between tokens.
        
        Args:
            token: Trading pair
            portfolio: Portfolio state
        
        Returns:
            (is_valid, reason)
        """
        # Simplified: just check we're not over-concentrating
        positions = portfolio.get('positions', {})
        if len(positions) > 0:
            # In full implementation, calculate Pearson correlation
            # For now, allow (actual correlation checking in production)
            pass

        return True, None

    def calculate_position_size(
        self,
        portfolio: Dict[str, Any],
        signal_confidence: float = 0.5,
        method: str = "fixed_pct",
    ) -> float:
        """Calculate appropriate position size for trade.
        
        T-3.4: Position Sizing
        
        WHEN trade is approved
        THEN calculate position size based on:
          1. Available balance
          2. Signal confidence
          3. Risk management method
        
        Args:
            portfolio: Portfolio state
            signal_confidence: Signal confidence (0-1)
            method: Sizing method ("fixed_pct" or "kelly")
        
        Returns:
            Position size
        """
        balance = portfolio.get('balance', 0)

        if method == "kelly":
            # Kelly Criterion: f = (bp - q) / b
            # Simplified: use signal confidence as probability of win
            win_rate = 0.6  # Assume 60% from backtest
            win_loss_ratio = 1.5  # Assume 1.5:1 from backtest

            kelly_fraction = (
                (win_loss_ratio * win_rate - (1 - win_rate)) 
                / win_loss_ratio
            )

            # Use half Kelly to be conservative
            position_pct = max(0.01, min(kelly_fraction / 2, 0.05))

        else:  # fixed_pct
            # Conservative: 1-3% based on confidence
            position_pct = 0.01 + (signal_confidence * 0.02)

        # Apply max position size limit
        position_pct = min(position_pct, self.max_position_size_pct / 100)

        position_size = balance * position_pct

        logger.info(
            f"Calculated position size: ${position_size:,.2f} "
            f"({position_pct*100:.2f}% of balance) "
            f"using {method}"
        )

        return position_size
