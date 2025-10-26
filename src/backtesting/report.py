"""BacktestReport - Generates comprehensive backtest analysis reports.

Produces:
- HTML reports with charts
- JSON export for programmatic use
- CSV trade logs
- Text summary
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class BacktestReport:
    """Comprehensive backtest report generator.
    
    Generates analysis in multiple formats:
    - HTML report with visualizations
    - JSON data export
    - CSV trade log
    - Text summary
    """

    def __init__(self, results: Any, metrics: Dict[str, float]):
        """Initialize report generator.
        
        Args:
            results: BacktestResults instance
            metrics: Performance metrics dict
        """
        self.results = results
        self.metrics = metrics
        self.timestamp = datetime.utcnow()

    def summary(self) -> str:
        """Generate text summary of backtest results.
        
        Returns:
            Formatted text summary
        """
        summary_data = self.results.get_summary()

        lines = [
            "=" * 70,
            "BACKTEST REPORT",
            "=" * 70,
            "",
            f"Backtest ID:        {summary_data['backtest_id']}",
            f"Period:             {summary_data['period']}",
            f"Initial Balance:    ${summary_data['initial_balance']:,.2f}",
            f"Final Balance:      ${summary_data['final_balance']:,.2f}",
            f"Total Return:       {summary_data['total_return_pct']:,.2f}%",
            "",
            "RISK-ADJUSTED METRICS",
            "-" * 70,
            f"Sharpe Ratio:       {self.metrics.get('sharpe_ratio', 0):.3f}",
            f"Sortino Ratio:      {self.metrics.get('sortino_ratio', 0):.3f}",
            f"Max Drawdown:       {summary_data['max_drawdown_pct']:.2f}%",
            "",
            "TRADING METRICS",
            "-" * 70,
            f"Total Trades:       {summary_data['trade_count']}",
            f"Win Rate:           {summary_data['win_rate_pct']:.1f}%",
            f"Profit Factor:      {self.metrics.get('profit_factor', 0):.2f}",
            f"Consecutive Wins:   {self.metrics.get('consecutive_wins', 0)}",
            f"Consecutive Losses: {self.metrics.get('consecutive_losses', 0)}",
            f"Avg Win %:          {self.metrics.get('avg_win_pct', 0):.2f}%",
            f"Avg Loss %:         {self.metrics.get('avg_loss_pct', 0):.2f}%",
            "",
            "BACKTEST INFO",
            "-" * 70,
            f"Events Processed:   {summary_data['events_processed']:,}",
            f"Backtest Speed:     {summary_data['backtest_speed']}",
            f"Generated:          {self.timestamp.isoformat()}",
            "=" * 70,
        ]

        return "\n".join(lines)

    def to_json(self) -> str:
        """Generate JSON export of backtest results.
        
        Returns:
            JSON string
        """
        report_data = {
            "report_type": "backtest",
            "timestamp": self.timestamp.isoformat(),
            "backtest_id": self.results.backtest_id,
            "period": {
                "start": self.results.start_date.isoformat(),
                "end": self.results.end_date.isoformat(),
            },
            "portfolio": {
                "initial_balance": self.results.initial_balance,
                "final_balance": self.results.final_balance,
            },
            "metrics": self.metrics,
            "summary": self.results.get_summary(),
            "trades": self._sanitize_trades(),
            "monthly_returns": self.results.calculator.calculate_monthly_returns(),
        }

        return json.dumps(report_data, indent=2)

    def to_csv(self) -> str:
        """Generate CSV export of trades.
        
        Returns:
            CSV string
        """
        if not self.results.trades:
            return "No trades to export"

        lines = [
            "token,direction,size,entry_price,exit_price,pnl,timestamp,source",
        ]

        for trade in self.results.trades:
            lines.append(
                f"{trade.get('token', '')},"
                f"{trade.get('direction', '')},"
                f"{trade.get('size', 0):.4f},"
                f"{trade.get('entry_price', 0):.2f},"
                f"{trade.get('exit_price', 0):.2f},"
                f"{trade.get('pnl', 0):.2f},"
                f"\"{trade.get('timestamp', '')}\","
                f"{trade.get('source', '')}"
            )

        return "\n".join(lines)

    def to_html(self) -> str:
        """Generate HTML report with visualizations.
        
        Returns:
            HTML string
        """
        summary = self.results.get_summary()

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Backtest Report - {self.results.backtest_id}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }}
        h1 {{ color: #333; border-bottom: 3px solid #007bff; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; }}
        .metric-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0; }}
        .metric-card {{ background: #f9f9f9; padding: 15px; border-radius: 5px; border-left: 4px solid #007bff; }}
        .metric-label {{ font-size: 12px; color: #999; text-transform: uppercase; }}
        .metric-value {{ font-size: 24px; font-weight: bold; color: #333; margin: 10px 0; }}
        .metric-unit {{ font-size: 14px; color: #666; }}
        .positive {{ color: #28a745; }}
        .negative {{ color: #dc3545; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #007bff; color: white; }}
        tr:hover {{ background-color: #f5f5f5; }}
        .info-section {{ background: #e7f3ff; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .chart-placeholder {{ background: #f0f0f0; padding: 40px; text-align: center; color: #999; border-radius: 5px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Backtest Report</h1>
        
        <div class="info-section">
            <strong>Backtest ID:</strong> {self.results.backtest_id}<br>
            <strong>Period:</strong> {summary['period']}<br>
            <strong>Generated:</strong> {self.timestamp.isoformat()}<br>
            <strong>Events Processed:</strong> {summary['events_processed']:,}<br>
            <strong>Replay Speed:</strong> {summary['backtest_speed']}
        </div>

        <h2>Portfolio Performance</h2>
        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-label">Initial Balance</div>
                <div class="metric-value">${summary['initial_balance']:,.2f}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Final Balance</div>
                <div class="metric-value">${summary['final_balance']:,.2f}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Total Return</div>
                <div class="metric-value {('positive' if summary['total_return_pct'] > 0 else 'negative')}">
                    {summary['total_return_pct']:+.2f}%
                </div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Max Drawdown</div>
                <div class="metric-value negative">{summary['max_drawdown_pct']:.2f}%</div>
            </div>
        </div>

        <h2>Risk-Adjusted Metrics</h2>
        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-label">Sharpe Ratio</div>
                <div class="metric-value">{self.metrics.get('sharpe_ratio', 0):.3f}</div>
                <div class="metric-unit">Annual risk-adjusted return</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Sortino Ratio</div>
                <div class="metric-value">{self.metrics.get('sortino_ratio', 0):.3f}</div>
                <div class="metric-unit">Return per unit of downside risk</div>
            </div>
        </div>

        <h2>Trading Statistics</h2>
        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-label">Total Trades</div>
                <div class="metric-value">{summary['trade_count']}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Win Rate</div>
                <div class="metric-value">{summary['win_rate_pct']:.1f}%</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Profit Factor</div>
                <div class="metric-value">{self.metrics.get('profit_factor', 0):.2f}x</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Consecutive Wins</div>
                <div class="metric-value">{self.metrics.get('consecutive_wins', 0)}</div>
            </div>
        </div>

        <h2>Equity Curve</h2>
        <div class="chart-placeholder">
            📈 Equity Curve Visualization<br>
            (Implement with Chart.js or similar library)
        </div>

        <h2>Monthly Returns</h2>
        {self._generate_monthly_returns_table()}

        <h2>Top 10 Trades</h2>
        {self._generate_top_trades_table()}

        <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #999; font-size: 12px;">
            <p>This report was generated automatically by Moon Dev EDA Backtesting Engine.</p>
            <p>For more information, see BACKTESTING.md in the implementation folder.</p>
        </div>
    </div>
</body>
</html>
"""
        return html

    def _sanitize_trades(self) -> List[Dict]:
        """Sanitize trades for JSON export.
        
        Returns:
            List of trade dicts with string timestamps
        """
        sanitized = []

        for trade in self.results.trades:
            trade_copy = trade.copy()

            # Convert datetime to string
            if isinstance(trade_copy.get('timestamp'), datetime):
                trade_copy['timestamp'] = trade_copy['timestamp'].isoformat()

            sanitized.append(trade_copy)

        return sanitized

    def _generate_monthly_returns_table(self) -> str:
        """Generate HTML table of monthly returns.
        
        Returns:
            HTML table string
        """
        monthly = self.results.calculator.calculate_monthly_returns()

        rows = []
        for month, ret in sorted(monthly.items()):
            color = "positive" if ret > 0 else "negative"
            rows.append(
                f'<tr><td>{month}</td><td class="{color}">{ret:+.2f}%</td></tr>'
            )

        table = f"""
        <table>
            <tr><th>Month</th><th>Return %</th></tr>
            {"".join(rows)}
        </table>
        """

        return table

    def _generate_top_trades_table(self) -> str:
        """Generate HTML table of top 10 trades by PnL.
        
        Returns:
            HTML table string
        """
        sorted_trades = sorted(
            self.results.trades,
            key=lambda t: abs(t.get('pnl', 0)),
            reverse=True
        )[:10]

        rows = []
        for i, trade in enumerate(sorted_trades, 1):
            pnl = trade.get('pnl', 0)
            color = "positive" if pnl > 0 else "negative"
            rows.append(
                f'<tr><td>{i}</td><td>{trade.get("token", "")}</td>'
                f'<td class="{color}">${pnl:+,.2f}</td>'
                f'<td>{trade.get("source", "")}</td></tr>'
            )

        table = f"""
        <table>
            <tr><th>#</th><th>Token</th><th>PnL</th><th>Source</th></tr>
            {"".join(rows)}
        </table>
        """

        return table
