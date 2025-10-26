"""PerformanceCalculator - Computes trading performance metrics.

Calculates:
- Total return percentage
- Sharpe ratio (risk-adjusted returns)
- Maximum drawdown
- Win rate and profit factor
- Monthly and daily returns
- Sortino ratio
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
import math

import numpy as np

logger = logging.getLogger(__name__)


class PerformanceCalculator:
    """Calculate trading performance metrics from backtest results.
    
    Metrics calculated:
    - Total Return %
    - Sharpe Ratio (excess return / volatility)
    - Sortino Ratio (excess return / downside volatility)
    - Maximum Drawdown %
    - Win Rate %
    - Profit Factor (gross profit / gross loss)
    - Monthly/Daily Returns
    - Consecutive Wins/Losses
    """

    # Assumptions
    RISK_FREE_RATE = 0.02  # 2% annual
    TRADING_DAYS_PER_YEAR = 252

    def __init__(
        self,
        trades: List[Dict[str, Any]],
        initial_balance: float,
        start_date: datetime,
        end_date: datetime,
    ):
        """Initialize performance calculator.
        
        Args:
            trades: List of trade records
            initial_balance: Starting portfolio balance
            start_date: Backtest start date
            end_date: Backtest end date
        """
        self.trades = trades
        self.initial_balance = initial_balance
        self.start_date = start_date
        self.end_date = end_date

        # Derived metrics
        self.total_days = (end_date - start_date).days
        self.annual_factor = 365 / max(self.total_days, 1)

        # Calculate equity curve
        self.equity_curve = self._calculate_equity_curve()
        self.final_balance = self.equity_curve[-1] if self.equity_curve else initial_balance

    def _calculate_equity_curve(self) -> List[float]:
        """Calculate equity curve from trades.
        
        Returns:
            List of portfolio values over time
        """
        equity = [self.initial_balance]

        for trade in self.trades:
            pnl = trade.get('pnl', 0)
            if pnl != 0:
                equity.append(equity[-1] + pnl)

        return equity if equity else [self.initial_balance]

    def calculate_all_metrics(self) -> Dict[str, float]:
        """Calculate all performance metrics.
        
        Returns:
            Dict of metric_name -> value
        """
        return {
            'total_return_pct': self.calculate_total_return(),
            'sharpe_ratio': self.calculate_sharpe_ratio(),
            'sortino_ratio': self.calculate_sortino_ratio(),
            'max_drawdown_pct': self.calculate_max_drawdown(),
            'win_rate_pct': self.calculate_win_rate(),
            'profit_factor': self.calculate_profit_factor(),
            'consecutive_wins': self.calculate_consecutive_wins(),
            'consecutive_losses': self.calculate_consecutive_losses(),
            'avg_win_pct': self.calculate_avg_win(),
            'avg_loss_pct': self.calculate_avg_loss(),
        }

    def calculate_total_return(self) -> float:
        """Calculate total return percentage.
        
        WHEN backtest completes
        THEN system SHALL calculate:
          total_return % = (final_balance - initial_balance) / initial_balance * 100
        
        Returns:
            Total return percentage
        """
        if self.initial_balance <= 0:
            return 0.0

        return ((self.final_balance - self.initial_balance) / self.initial_balance) * 100

    def calculate_sharpe_ratio(self, risk_free_rate: float = None) -> float:
        """Calculate Sharpe ratio.
        
        Sharpe = (mean_return - risk_free_rate) / std_dev * sqrt(252)
        
        Where:
        - mean_return = average daily return
        - std_dev = standard deviation of returns
        - 252 = trading days per year
        
        Args:
            risk_free_rate: Annual risk-free rate (default 2%)
        
        Returns:
            Sharpe ratio
        """
        if risk_free_rate is None:
            risk_free_rate = self.RISK_FREE_RATE

        if len(self.equity_curve) < 2:
            return 0.0

        # Calculate daily returns
        daily_returns = []
        for i in range(1, len(self.equity_curve)):
            ret = (self.equity_curve[i] - self.equity_curve[i-1]) / self.equity_curve[i-1]
            daily_returns.append(ret)

        if not daily_returns:
            return 0.0

        # Calculate Sharpe ratio
        mean_return = np.mean(daily_returns)
        std_return = np.std(daily_returns)

        if std_return == 0:
            return 0.0

        daily_rf_rate = risk_free_rate / self.TRADING_DAYS_PER_YEAR
        sharpe = (mean_return - daily_rf_rate) / std_return * math.sqrt(self.TRADING_DAYS_PER_YEAR)

        return float(sharpe)

    def calculate_sortino_ratio(self) -> float:
        """Calculate Sortino ratio (penalizes downside volatility).
        
        Sortino = (mean_return - risk_free_rate) / downside_std_dev * sqrt(252)
        
        Where downside_std_dev = std_dev of negative returns only
        
        Returns:
            Sortino ratio
        """
        if len(self.equity_curve) < 2:
            return 0.0

        # Calculate daily returns
        daily_returns = []
        for i in range(1, len(self.equity_curve)):
            ret = (self.equity_curve[i] - self.equity_curve[i-1]) / self.equity_curve[i-1]
            daily_returns.append(ret)

        if not daily_returns:
            return 0.0

        # Calculate downside returns
        downside_returns = [r for r in daily_returns if r < 0]

        if not downside_returns:
            # No losing periods = infinite Sortino (return positive value)
            return 100.0

        mean_return = np.mean(daily_returns)
        downside_std = np.std(downside_returns)

        if downside_std == 0:
            return 0.0

        daily_rf_rate = self.RISK_FREE_RATE / self.TRADING_DAYS_PER_YEAR
        sortino = (mean_return - daily_rf_rate) / downside_std * math.sqrt(self.TRADING_DAYS_PER_YEAR)

        return float(sortino)

    def calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown percentage.
        
        Max Drawdown = (trough - peak) / peak * 100
        
        Returns:
            Maximum drawdown percentage (negative value)
        """
        if len(self.equity_curve) < 2:
            return 0.0

        peak = self.equity_curve[0]
        max_dd = 0.0

        for value in self.equity_curve:
            if value > peak:
                peak = value

            dd = (value - peak) / peak
            if dd < max_dd:
                max_dd = dd

        return max_dd * 100

    def calculate_win_rate(self) -> float:
        """Calculate win rate percentage.
        
        Win Rate % = winning_trades / total_trades * 100
        
        Returns:
            Win rate percentage
        """
        if not self.trades:
            return 0.0

        winning_trades = sum(1 for t in self.trades if t.get('pnl', 0) > 0)
        return (winning_trades / len(self.trades)) * 100

    def calculate_profit_factor(self) -> float:
        """Calculate profit factor.
        
        Profit Factor = gross_profit / abs(gross_loss)
        
        Returns:
            Profit factor (>1 is profitable)
        """
        if not self.trades:
            return 0.0

        gross_profit = sum(max(0, t.get('pnl', 0)) for t in self.trades)
        gross_loss = sum(abs(min(0, t.get('pnl', 0))) for t in self.trades)

        if gross_loss == 0:
            return 0.0

        return gross_profit / gross_loss

    def calculate_consecutive_wins(self) -> int:
        """Calculate longest winning streak.
        
        Returns:
            Number of consecutive winning trades
        """
        if not self.trades:
            return 0

        max_wins = 0
        current_wins = 0

        for trade in self.trades:
            if trade.get('pnl', 0) > 0:
                current_wins += 1
                max_wins = max(max_wins, current_wins)
            else:
                current_wins = 0

        return max_wins

    def calculate_consecutive_losses(self) -> int:
        """Calculate longest losing streak.
        
        Returns:
            Number of consecutive losing trades
        """
        if not self.trades:
            return 0

        max_losses = 0
        current_losses = 0

        for trade in self.trades:
            if trade.get('pnl', 0) < 0:
                current_losses += 1
                max_losses = max(max_losses, current_losses)
            else:
                current_losses = 0

        return max_losses

    def calculate_avg_win(self) -> float:
        """Calculate average winning trade percentage.
        
        Returns:
            Average profit percentage per winning trade
        """
        winning_trades = [t for t in self.trades if t.get('pnl', 0) > 0]

        if not winning_trades:
            return 0.0

        avg_pnl = np.mean([t.get('pnl', 0) for t in winning_trades])
        return (avg_pnl / self.initial_balance) * 100

    def calculate_avg_loss(self) -> float:
        """Calculate average losing trade percentage.
        
        Returns:
            Average loss percentage per losing trade (negative value)
        """
        losing_trades = [t for t in self.trades if t.get('pnl', 0) < 0]

        if not losing_trades:
            return 0.0

        avg_pnl = np.mean([t.get('pnl', 0) for t in losing_trades])
        return (avg_pnl / self.initial_balance) * 100

    def calculate_monthly_returns(self) -> Dict[str, float]:
        """Calculate returns by month.
        
        Returns:
            Dict of month -> return %
        """
        monthly = {}

        current_month = self.start_date.replace(day=1)
        start_balance = self.initial_balance

        while current_month <= self.end_date:
            # Find trades in this month
            month_end = (current_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            month_end = min(month_end, self.end_date)

            month_pnl = sum(
                t.get('pnl', 0) for t in self.trades
                if current_month <= datetime.fromisoformat(str(t.get('timestamp', ''))) <= month_end
            )

            month_return = (month_pnl / start_balance) * 100
            month_key = current_month.strftime('%Y-%m')
            monthly[month_key] = month_return

            start_balance += month_pnl
            current_month = month_end + timedelta(days=1)

        return monthly

    def calculate_daily_returns(self) -> Dict[str, float]:
        """Calculate returns by day.
        
        Returns:
            Dict of date -> return %
        """
        daily = {}
        start_balance = self.initial_balance

        current_day = self.start_date

        while current_day <= self.end_date:
            day_end = current_day + timedelta(days=1)

            day_pnl = sum(
                t.get('pnl', 0) for t in self.trades
                if current_day <= datetime.fromisoformat(str(t.get('timestamp', ''))) < day_end
            )

            if day_pnl != 0:
                day_return = (day_pnl / start_balance) * 100
                day_key = current_day.strftime('%Y-%m-%d')
                daily[day_key] = day_return
                start_balance += day_pnl

            current_day = day_end

        return daily
