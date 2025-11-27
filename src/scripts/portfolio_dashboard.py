"""
🌙 Moon Dev's Portfolio Dashboard
Real-time PnL tracking, win rate analysis, and agent performance leaderboard
Built with love by Moon Dev 🚀

Usage:
    python src/scripts/portfolio_dashboard.py

Then open: http://localhost:8003
"""

from flask import Flask, render_template_string, jsonify
from pathlib import Path
import sys
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.agents.portfolio_tracker import get_tracker

app = Flask(__name__)
tracker = get_tracker()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>🌙 Moon Dev Portfolio Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1600px;
            margin: 0 auto;
        }

        .header {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            text-align: center;
        }

        .header h1 {
            color: #1e3c72;
            font-size: 2.5em;
            margin-bottom: 10px;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .stat-card {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            text-align: center;
        }

        .stat-label {
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            margin-bottom: 10px;
            font-weight: 600;
        }

        .stat-value {
            color: #1e3c72;
            font-size: 2em;
            font-weight: bold;
        }

        .stat-value.positive {
            color: #28a745;
        }

        .stat-value.negative {
            color: #dc3545;
        }

        .dashboard-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 30px;
        }

        @media (max-width: 1200px) {
            .dashboard-grid {
                grid-template-columns: 1fr;
            }
        }

        .dashboard-card {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }

        .dashboard-card h2 {
            color: #333;
            margin-bottom: 20px;
            font-size: 1.5em;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .leaderboard-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px;
            margin: 10px 0;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #28a745;
        }

        .leaderboard-item.negative {
            border-left-color: #dc3545;
        }

        .leaderboard-rank {
            font-size: 1.5em;
            font-weight: bold;
            color: #666;
            min-width: 40px;
        }

        .leaderboard-name {
            flex: 1;
            font-weight: 600;
            color: #333;
        }

        .leaderboard-stats {
            text-align: right;
            font-size: 0.9em;
        }

        .leaderboard-pnl {
            font-size: 1.2em;
            font-weight: bold;
        }

        .leaderboard-pnl.positive {
            color: #28a745;
        }

        .leaderboard-pnl.negative {
            color: #dc3545;
        }

        .position-item {
            padding: 15px;
            margin: 10px 0;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #007bff;
        }

        .position-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }

        .position-symbol {
            font-weight: 600;
            font-size: 1.1em;
            color: #333;
        }

        .position-agent {
            color: #666;
            font-size: 0.9em;
        }

        .position-details {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            font-size: 0.9em;
            color: #666;
        }

        .trade-item {
            padding: 15px;
            margin: 10px 0;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #28a745;
        }

        .trade-item.loss {
            border-left-color: #dc3545;
        }

        .trade-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }

        .trade-symbol {
            font-weight: 600;
            font-size: 1.1em;
            color: #333;
        }

        .trade-pnl {
            font-weight: bold;
            font-size: 1.1em;
        }

        .trade-pnl.positive {
            color: #28a745;
        }

        .trade-pnl.negative {
            color: #dc3545;
        }

        .trade-details {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 10px;
            font-size: 0.85em;
            color: #666;
        }

        .empty-state {
            text-align: center;
            padding: 40px;
            color: #666;
            font-style: italic;
        }

        .refresh-info {
            text-align: center;
            color: rgba(255,255,255,0.9);
            margin-top: 20px;
            font-size: 0.9em;
        }

        .full-width {
            grid-column: 1 / -1;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .loading {
            animation: pulse 2s infinite;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌙 Moon Dev Portfolio Dashboard</h1>
            <p class="tagline">Real-time PnL tracking and agent performance</p>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Total PnL</div>
                <div id="total-pnl" class="stat-value loading">$0.00</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Total Trades</div>
                <div id="total-trades" class="stat-value loading">0</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Win Rate</div>
                <div id="win-rate" class="stat-value loading">0%</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Open Positions</div>
                <div id="open-positions" class="stat-value loading">0</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Avg PnL/Trade</div>
                <div id="avg-pnl" class="stat-value loading">$0.00</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Best Trade</div>
                <div id="best-trade" class="stat-value positive loading">$0.00</div>
            </div>
        </div>

        <div class="dashboard-grid">
            <div class="dashboard-card">
                <h2>🏆 Agent Performance Leaderboard</h2>
                <div id="leaderboard" class="loading">Loading...</div>
            </div>

            <div class="dashboard-card">
                <h2>📈 Open Positions</h2>
                <div id="positions" class="loading">Loading...</div>
            </div>
        </div>

        <div class="dashboard-card full-width">
            <h2>📊 Recent Trades</h2>
            <div id="trades" class="loading">Loading...</div>
        </div>

        <div class="refresh-info">
            Auto-refreshing every 10 seconds | Last update: <span id="last-update">-</span>
        </div>
    </div>

    <script>
        function updateDashboard() {
            fetch('/api/portfolio')
                .then(response => response.json())
                .then(data => {
                    updateStats(data.summary);
                    updateLeaderboard(data.summary.agent_performance);
                    updatePositions(data.positions);
                    updateTrades(data.recent_trades);
                    document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
                })
                .catch(error => console.error('Error:', error));
        }

        function updateStats(summary) {
            document.getElementById('total-pnl').textContent = '$' + summary.total_pnl.toFixed(2);
            document.getElementById('total-pnl').className = 'stat-value ' + (summary.total_pnl >= 0 ? 'positive' : 'negative');

            document.getElementById('total-trades').textContent = summary.total_trades;
            document.getElementById('total-trades').className = 'stat-value';

            document.getElementById('win-rate').textContent = summary.overall_win_rate.toFixed(1) + '%';
            document.getElementById('win-rate').className = 'stat-value ' + (summary.overall_win_rate >= 50 ? 'positive' : 'negative');

            document.getElementById('open-positions').textContent = summary.open_positions;
            document.getElementById('open-positions').className = 'stat-value';

            document.getElementById('avg-pnl').textContent = '$' + summary.avg_pnl_per_trade.toFixed(2);
            document.getElementById('avg-pnl').className = 'stat-value ' + (summary.avg_pnl_per_trade >= 0 ? 'positive' : 'negative');

            document.getElementById('best-trade').textContent = '$' + summary.best_trade.toFixed(2);
            document.getElementById('best-trade').className = 'stat-value positive';
        }

        function updateLeaderboard(agents) {
            const leaderboard = document.getElementById('leaderboard');
            leaderboard.classList.remove('loading');

            if (!agents || Object.keys(agents).length === 0) {
                leaderboard.innerHTML = '<div class="empty-state">No agent data yet</div>';
                return;
            }

            const sorted = Object.entries(agents).sort((a, b) => b[1].total_pnl_usd - a[1].total_pnl_usd);
            const medals = ['🥇', '🥈', '🥉'];

            leaderboard.innerHTML = sorted.map(([name, stats], i) => {
                const rank = i < 3 ? medals[i] : `${i + 1}.`;
                const negClass = stats.total_pnl_usd < 0 ? 'negative' : '';
                const pnlClass = stats.total_pnl_usd >= 0 ? 'positive' : 'negative';

                return `
                    <div class="leaderboard-item ${negClass}">
                        <div class="leaderboard-rank">${rank}</div>
                        <div class="leaderboard-name">${name}</div>
                        <div class="leaderboard-stats">
                            <div class="leaderboard-pnl ${pnlClass}">$${stats.total_pnl_usd.toFixed(2)}</div>
                            <div>${stats.win_rate.toFixed(1)}% WR | ${stats.total_trades} trades</div>
                        </div>
                    </div>
                `;
            }).join('');
        }

        function updatePositions(positions) {
            const positionsDiv = document.getElementById('positions');
            positionsDiv.classList.remove('loading');

            if (!positions || positions.length === 0) {
                positionsDiv.innerHTML = '<div class="empty-state">No open positions</div>';
                return;
            }

            positionsDiv.innerHTML = positions.map(pos => `
                <div class="position-item">
                    <div class="position-header">
                        <div>
                            <div class="position-symbol">${pos.token_symbol}</div>
                            <div class="position-agent">by ${pos.agent_name}</div>
                        </div>
                    </div>
                    <div class="position-details">
                        <div>Entry: $${parseFloat(pos.entry_price).toFixed(6)}</div>
                        <div>Qty: ${parseFloat(pos.quantity).toFixed(2)}</div>
                        <div>Value: $${parseFloat(pos.usd_value).toFixed(2)}</div>
                    </div>
                </div>
            `).join('');
        }

        function updateTrades(trades) {
            const tradesDiv = document.getElementById('trades');
            tradesDiv.classList.remove('loading');

            if (!trades || trades.length === 0) {
                tradesDiv.innerHTML = '<div class="empty-state">No trades yet</div>';
                return;
            }

            tradesDiv.innerHTML = trades.map(trade => {
                const lossClass = !trade.win ? 'loss' : '';
                const pnlClass = trade.pnl_usd >= 0 ? 'positive' : 'negative';

                return `
                    <div class="trade-item ${lossClass}">
                        <div class="trade-header">
                            <div>
                                <div class="trade-symbol">${trade.token_symbol}</div>
                                <div style="font-size: 0.9em; color: #666;">by ${trade.agent_name}</div>
                            </div>
                            <div class="trade-pnl ${pnlClass}">
                                $${trade.pnl_usd.toFixed(2)} (${trade.pnl_percent.toFixed(2)}%)
                            </div>
                        </div>
                        <div class="trade-details">
                            <div>Entry: $${parseFloat(trade.entry_price).toFixed(6)}</div>
                            <div>Exit: $${parseFloat(trade.exit_price).toFixed(6)}</div>
                            <div>Duration: ${Math.round(trade.duration_minutes)}m</div>
                            <div>${trade.win ? '✅ WIN' : '❌ LOSS'}</div>
                        </div>
                    </div>
                `;
            }).join('');
        }

        // Initial load
        updateDashboard();

        // Auto-refresh every 10 seconds
        setInterval(updateDashboard, 10000);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/portfolio')
def portfolio_api():
    """API endpoint for portfolio data"""
    summary = tracker.get_portfolio_summary()
    positions = tracker.get_open_positions().to_dict('records')
    recent_trades = tracker.get_trade_history(limit=20).to_dict('records')

    return jsonify({
        'summary': summary,
        'positions': positions,
        'recent_trades': recent_trades
    })

if __name__ == '__main__':
    print("🌙 Moon Dev Portfolio Dashboard")
    print("=" * 60)
    print("🚀 Starting web server on http://localhost:8003")
    print("📊 Dashboard will auto-refresh every 10 seconds")
    print("Press Ctrl+C to stop")
    print("=" * 60 + "\n")

    app.run(host='0.0.0.0', port=8003, debug=False)
