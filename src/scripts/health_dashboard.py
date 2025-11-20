"""
🌙 Moon Dev's Agent Health Dashboard
Web UI for monitoring agent and API health in real-time
Built with love by Moon Dev 🚀

Usage:
    python src/scripts/health_dashboard.py

Then open: http://localhost:8002
"""

from flask import Flask, render_template_string, jsonify
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.agents.agent_health_monitor import get_monitor

app = Flask(__name__)
monitor = get_monitor()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>🌙 Moon Dev Agent Health Monitor</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1400px;
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
            color: #667eea;
            font-size: 2.5em;
            margin-bottom: 10px;
        }

        .header .tagline {
            color: #666;
            font-size: 1.1em;
        }

        .alerts {
            background: #fff3cd;
            border: 2px solid #ffc107;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 30px;
            display: none;
        }

        .alerts.show {
            display: block;
        }

        .alert-item {
            padding: 10px;
            margin: 5px 0;
            background: white;
            border-radius: 5px;
            border-left: 4px solid #ff6b6b;
        }

        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .status-card {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }

        .status-card h2 {
            color: #333;
            margin-bottom: 20px;
            font-size: 1.5em;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .agent-item, .api-item {
            padding: 15px;
            margin: 10px 0;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #28a745;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .agent-item.stale {
            border-left-color: #ffc107;
            background: #fffbf0;
        }

        .agent-item.error {
            border-left-color: #dc3545;
            background: #fff5f5;
        }

        .api-item.slow {
            border-left-color: #ffc107;
            background: #fffbf0;
        }

        .api-item.down {
            border-left-color: #dc3545;
            background: #fff5f5;
        }

        .item-name {
            font-weight: 600;
            font-size: 1.1em;
            color: #333;
        }

        .item-details {
            font-size: 0.9em;
            color: #666;
            margin-top: 5px;
        }

        .status-badge {
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
            text-transform: uppercase;
        }

        .badge-healthy {
            background: #d4edda;
            color: #155724;
        }

        .badge-stale {
            background: #fff3cd;
            color: #856404;
        }

        .badge-error, .badge-down {
            background: #f8d7da;
            color: #721c24;
        }

        .badge-slow {
            background: #fff3cd;
            color: #856404;
        }

        .refresh-info {
            text-align: center;
            color: rgba(255,255,255,0.9);
            margin-top: 20px;
            font-size: 0.9em;
        }

        .empty-state {
            text-align: center;
            padding: 40px;
            color: #666;
            font-style: italic;
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
            <h1>🌙 Moon Dev Agent Health Monitor</h1>
            <p class="tagline">Real-time monitoring of trading agents and APIs</p>
        </div>

        <div id="alerts" class="alerts">
            <h3 style="color: #856404; margin-bottom: 15px;">🚨 Active Alerts</h3>
            <div id="alert-list"></div>
        </div>

        <div class="status-grid">
            <div class="status-card">
                <h2>🤖 Trading Agents</h2>
                <div id="agents-list" class="loading">Loading agents...</div>
            </div>

            <div class="status-card">
                <h2>🌐 API Status</h2>
                <div id="apis-list" class="loading">Loading APIs...</div>
            </div>
        </div>

        <div class="refresh-info">
            Auto-refreshing every 10 seconds | Last update: <span id="last-update">-</span>
        </div>
    </div>

    <script>
        function updateHealth() {
            fetch('/api/health')
                .then(response => response.json())
                .then(data => {
                    updateAlerts(data.alerts);
                    updateAgents(data.agents);
                    updateAPIs(data.apis);
                    document.getElementById('last-update').textContent = new Date(data.timestamp).toLocaleTimeString();
                })
                .catch(error => {
                    console.error('Error fetching health data:', error);
                });
        }

        function updateAlerts(alerts) {
            const alertsDiv = document.getElementById('alerts');
            const alertList = document.getElementById('alert-list');

            if (alerts && alerts.length > 0) {
                alertsDiv.classList.add('show');
                alertList.innerHTML = alerts.map(alert =>
                    `<div class="alert-item">${alert}</div>`
                ).join('');
            } else {
                alertsDiv.classList.remove('show');
            }
        }

        function updateAgents(agents) {
            const agentsList = document.getElementById('agents-list');

            if (!agents || Object.keys(agents).length === 0) {
                agentsList.innerHTML = '<div class="empty-state">No agents have reported yet<br><small>Agents will appear here once they start running</small></div>';
                agentsList.classList.remove('loading');
                return;
            }

            agentsList.classList.remove('loading');
            agentsList.innerHTML = Object.entries(agents)
                .sort((a, b) => a[0].localeCompare(b[0]))
                .map(([name, data]) => {
                    const healthClass = data.health === 'healthy' ? '' : data.health;
                    const badgeClass = `badge-${data.health}`;
                    return `
                        <div class="agent-item ${healthClass}">
                            <div>
                                <div class="item-name">${name}</div>
                                <div class="item-details">
                                    Last run: ${data.minutes_ago}m ago | Status: ${data.status}
                                </div>
                            </div>
                            <span class="status-badge ${badgeClass}">${data.health}</span>
                        </div>
                    `;
                }).join('');
        }

        function updateAPIs(apis) {
            const apisList = document.getElementById('apis-list');

            if (!apis || Object.keys(apis).length === 0) {
                apisList.innerHTML = '<div class="empty-state">No API checks yet<br><small>APIs will appear here once health checks run</small></div>';
                apisList.classList.remove('loading');
                return;
            }

            apisList.classList.remove('loading');
            apisList.innerHTML = Object.entries(apis)
                .sort((a, b) => a[0].localeCompare(b[0]))
                .map(([name, data]) => {
                    const healthClass = data.health === 'healthy' ? '' : data.health;
                    const badgeClass = `badge-${data.health}`;
                    const responseTime = data.response_time ? `${data.response_time.toFixed(2)}s` : 'N/A';
                    const errorInfo = data.error ? `<br>Error: ${data.error}` : '';
                    return `
                        <div class="api-item ${healthClass}">
                            <div>
                                <div class="item-name">${name}</div>
                                <div class="item-details">
                                    Response: ${responseTime} | Checked: ${data.minutes_ago}m ago${errorInfo}
                                </div>
                            </div>
                            <span class="status-badge ${badgeClass}">${data.health}</span>
                        </div>
                    `;
                }).join('');
        }

        // Initial load
        updateHealth();

        // Auto-refresh every 10 seconds
        setInterval(updateHealth, 10000);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/health')
def health_api():
    """API endpoint for health data"""
    report = monitor.get_health_report()
    return jsonify(report)

if __name__ == '__main__':
    print("🌙 Moon Dev Agent Health Dashboard")
    print("=" * 60)
    print("🚀 Starting web server on http://localhost:8002")
    print("📊 Dashboard will auto-refresh every 10 seconds")
    print("Press Ctrl+C to stop")
    print("=" * 60 + "\n")

    app.run(host='0.0.0.0', port=8002, debug=False)
