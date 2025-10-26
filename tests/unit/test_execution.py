"""
Unit Tests - Execution Engine

Tests for trade execution, risk validation, and exchange adapters.
"""

import pytest
from typing import Tuple, Optional

from src.execution.risk_validator import RiskValidator


class TestRiskValidator:
    """Test RiskValidator constraints."""
    
    def test_validator_initialization(self):
        """Test risk validator initializes."""
        # Act
        validator = RiskValidator(
            max_leverage=10.0,
            max_positions=10,
            max_daily_loss_pct=2.0,
        )
        
        # Assert
        assert validator.max_leverage == 10.0
        assert validator.max_positions == 10
        assert validator.max_daily_loss_pct == 2.0
    
    def test_validate_trade_sufficient_balance(self):
        """Test validation with sufficient balance."""
        # Arrange
        validator = RiskValidator()
        portfolio = {
            "balance": 50000.0,
            "positions": [],
            "metrics": {"daily_pnl": 0.0}
        }
        
        # Act
        is_valid, reason = validator.validate_trade(
            token="BTC-USD",
            direction="long",
            size=2.0,
            entry_price=43250.0,
            portfolio=portfolio
        )
        
        # Assert
        assert is_valid is True
        assert reason is None
    
    def test_validate_trade_insufficient_balance(self):
        """Test validation with insufficient balance."""
        # Arrange
        validator = RiskValidator()
        portfolio = {
            "balance": 100.0,  # Low balance
            "positions": [],
            "metrics": {"daily_pnl": 0.0}
        }
        
        # Act
        is_valid, reason = validator.validate_trade(
            token="BTC-USD",
            direction="long",
            size=10.0,
            entry_price=43250.0,
            portfolio=portfolio
        )
        
        # Assert
        assert is_valid is False
        assert "balance" in reason.lower()
    
    def test_validate_trade_leverage_check(self):
        """Test leverage ratio validation."""
        # Arrange
        validator = RiskValidator(max_leverage=5.0)
        portfolio = {
            "balance": 50000.0,
            "positions": [],
            "metrics": {"leverage_ratio": 4.5}
        }
        
        # Act - Trade that would exceed max leverage
        is_valid, reason = validator.validate_trade(
            token="BTC-USD",
            direction="long",
            size=50.0,  # Very large position
            entry_price=43250.0,
            portfolio=portfolio
        )
        
        # Assert
        assert is_valid is False
        assert "leverage" in reason.lower()
    
    def test_validate_trade_position_limit(self):
        """Test maximum positions validation."""
        # Arrange
        validator = RiskValidator(max_positions=3)
        
        # Create portfolio with max positions already open
        portfolio = {
            "balance": 50000.0,
            "positions": [
                {"token": "BTC-USD", "size": 1.0},
                {"token": "ETH-USD", "size": 2.0},
                {"token": "SOL-USD", "size": 1.5},
            ],
            "metrics": {"daily_pnl": 0.0}
        }
        
        # Act - Try to open new position when at max
        is_valid, reason = validator.validate_trade(
            token="ADA-USD",  # New token
            direction="long",
            size=1.0,
            entry_price=0.5,
            portfolio=portfolio
        )
        
        # Assert
        assert is_valid is False
        assert "position" in reason.lower()
    
    def test_validate_trade_daily_loss_limit(self):
        """Test daily loss limit validation."""
        # Arrange
        validator = RiskValidator(max_daily_loss_pct=2.0)
        portfolio = {
            "balance": 50000.0,
            "positions": [],
            "metrics": {
                "daily_pnl": -1500.0,  # Already down 3%
                "leverage_ratio": 1.0
            }
        }
        
        # Act - Trade that would increase loss
        is_valid, reason = validator.validate_trade(
            token="BTC-USD",
            direction="short",
            size=2.0,
            entry_price=43250.0,
            portfolio=portfolio
        )
        
        # Assert
        assert is_valid is False
        assert "loss" in reason.lower() or "daily" in reason.lower()
    
    def test_calculate_kelly_position_size(self):
        """Test Kelly Criterion position sizing."""
        # Arrange
        validator = RiskValidator()
        
        # Act
        size = validator.calculate_position_size(
            portfolio_balance=50000.0,
            win_rate=0.60,
            confidence=0.85,
            sizing_method="kelly"
        )
        
        # Assert
        assert size > 0
        assert size <= 50000.0  # Can't be larger than balance
    
    def test_calculate_fixed_position_size(self):
        """Test fixed percentage position sizing."""
        # Arrange
        validator = RiskValidator()
        
        # Act
        size = validator.calculate_position_size(
            portfolio_balance=50000.0,
            win_rate=0.60,
            confidence=0.85,
            sizing_method="fixed"
        )
        
        # Assert
        assert size > 0
        assert size <= 50000.0
    
    def test_position_size_with_high_confidence(self):
        """Test position size increases with confidence."""
        # Arrange
        validator = RiskValidator()
        balance = 50000.0
        
        # Act - Low confidence
        low_conf_size = validator.calculate_position_size(
            portfolio_balance=balance,
            win_rate=0.50,
            confidence=0.50,
            sizing_method="fixed"
        )
        
        # Act - High confidence
        high_conf_size = validator.calculate_position_size(
            portfolio_balance=balance,
            win_rate=0.50,
            confidence=0.95,
            sizing_method="fixed"
        )
        
        # Assert
        assert high_conf_size > low_conf_size
    
    def test_validate_trade_open_position_update(self):
        """Test validation when updating existing position."""
        # Arrange
        validator = RiskValidator()
        portfolio = {
            "balance": 50000.0,
            "positions": [
                {"token": "BTC-USD", "size": 2.0, "entry_price": 42000.0}
            ],
            "metrics": {"daily_pnl": 500.0, "leverage_ratio": 1.5}
        }
        
        # Act - Add to existing position
        is_valid, reason = validator.validate_trade(
            token="BTC-USD",
            direction="long",
            size=1.5,  # Adding to existing 2.0
            entry_price=43250.0,
            portfolio=portfolio
        )
        
        # Assert
        assert is_valid is True
    
    def test_validate_trade_return_format(self):
        """Test validation returns correct format."""
        # Arrange
        validator = RiskValidator()
        portfolio = {
            "balance": 50000.0,
            "positions": [],
            "metrics": {"daily_pnl": 0.0}
        }
        
        # Act
        result = validator.validate_trade(
            token="BTC-USD",
            direction="long",
            size=2.0,
            entry_price=43250.0,
            portfolio=portfolio
        )
        
        # Assert
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], bool)
        assert isinstance(result[1], (str, type(None)))


class TestPositionSizing:
    """Test position sizing methods."""
    
    def test_kelly_criterion_sizing(self):
        """Test Kelly Criterion calculation."""
        # Arrange
        validator = RiskValidator()
        
        # Act - With 60% win rate
        size_60 = validator.calculate_position_size(
            portfolio_balance=100000.0,
            win_rate=0.60,
            confidence=0.8,
            sizing_method="kelly"
        )
        
        # Act - With 50% win rate
        size_50 = validator.calculate_position_size(
            portfolio_balance=100000.0,
            win_rate=0.50,
            confidence=0.8,
            sizing_method="kelly"
        )
        
        # Assert
        assert size_60 > size_50  # Higher win rate = larger position
    
    def test_fixed_percentage_sizing(self):
        """Test fixed percentage position sizing."""
        # Arrange
        validator = RiskValidator()
        
        # Act
        size = validator.calculate_position_size(
            portfolio_balance=100000.0,
            win_rate=0.55,
            confidence=0.75,
            sizing_method="fixed"
        )
        
        # Assert
        assert size > 0
        assert size < 100000.0  # Should be a fraction of balance
    
    def test_sizing_respects_max_leverage(self):
        """Test position sizing respects max leverage."""
        # Arrange
        validator = RiskValidator(max_leverage=5.0)
        
        # Act
        size = validator.calculate_position_size(
            portfolio_balance=50000.0,
            win_rate=0.60,
            confidence=1.0,
            sizing_method="kelly"
        )
        
        # Assert
        # Even with perfect confidence, should not exceed leverage limit
        assert size <= 50000.0 * 5.0  # max_leverage * balance


class TestRiskConstraints:
    """Test various risk constraints."""
    
    def test_all_constraints_pass(self):
        """Test trade passes all constraints."""
        # Arrange
        validator = RiskValidator(
            max_leverage=10.0,
            max_positions=10,
            max_daily_loss_pct=2.0,
        )
        
        portfolio = {
            "balance": 50000.0,
            "positions": [{"token": "ETH-USD", "size": 1.0}],
            "metrics": {
                "daily_pnl": -500.0,  # -1%
                "leverage_ratio": 1.5
            }
        }
        
        # Act
        is_valid, reason = validator.validate_trade(
            token="BTC-USD",
            direction="long",
            size=2.0,
            entry_price=43250.0,
            portfolio=portfolio
        )
        
        # Assert
        assert is_valid is True
        assert reason is None
    
    def test_constraint_priority(self):
        """Test which constraint fails first."""
        # Arrange
        validator = RiskValidator(
            max_leverage=1.0,  # Very low
            max_positions=0,    # No more positions allowed
            max_daily_loss_pct=1.0,  # -1% threshold
        )
        
        portfolio = {
            "balance": 10000.0,
            "positions": [{"token": "ETH-USD", "size": 5.0}],
            "metrics": {
                "daily_pnl": -500.0,
                "leverage_ratio": 5.0
            }
        }
        
        # Act
        is_valid, reason = validator.validate_trade(
            token="BTC-USD",
            direction="long",
            size=1.0,
            entry_price=43250.0,
            portfolio=portfolio
        )
        
        # Assert
        assert is_valid is False
        # Should fail on at least one constraint
        assert reason is not None
