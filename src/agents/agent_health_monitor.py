"""
🌙 Moon Dev's Agent Health Monitor
Tracks which agents are running, when they last executed, and if APIs are responding
Built with love by Moon Dev 🚀
"""

import os
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from termcolor import cprint
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

class AgentHealthMonitor:
    """Monitors health of all trading agents"""

    def __init__(self, data_dir="src/data/health_monitor"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.heartbeat_file = self.data_dir / "agent_heartbeats.json"
        self.api_status_file = self.data_dir / "api_status.json"

        # Initialize files if they don't exist
        if not self.heartbeat_file.exists():
            self._save_json({}, self.heartbeat_file)
        if not self.api_status_file.exists():
            self._save_json({}, self.api_status_file)

    def _save_json(self, data, filepath):
        """Save JSON data to file"""
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    def _load_json(self, filepath):
        """Load JSON data from file"""
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except:
            return {}

    def heartbeat(self, agent_name, status="running", metadata=None):
        """
        Record agent heartbeat

        Args:
            agent_name: Name of the agent (e.g., 'trading_agent')
            status: Status ('running', 'success', 'error')
            metadata: Optional dict with additional info
        """
        heartbeats = self._load_json(self.heartbeat_file)

        heartbeats[agent_name] = {
            "last_run": datetime.now().isoformat(),
            "status": status,
            "metadata": metadata or {}
        }

        self._save_json(heartbeats, self.heartbeat_file)

    def log_api_status(self, api_name, status, response_time=None, error=None):
        """
        Log API health status

        Args:
            api_name: Name of API (e.g., 'birdeye', 'moondev', 'coingecko')
            status: 'up', 'down', 'slow'
            response_time: Response time in seconds
            error: Error message if any
        """
        api_statuses = self._load_json(self.api_status_file)

        api_statuses[api_name] = {
            "last_checked": datetime.now().isoformat(),
            "status": status,
            "response_time": response_time,
            "error": str(error) if error else None
        }

        self._save_json(api_statuses, self.api_status_file)

    def get_health_report(self):
        """
        Generate comprehensive health report

        Returns:
            dict with agent and API health status
        """
        heartbeats = self._load_json(self.heartbeat_file)
        api_statuses = self._load_json(self.api_status_file)

        now = datetime.now()
        report = {
            "timestamp": now.isoformat(),
            "agents": {},
            "apis": {},
            "alerts": []
        }

        # Check agent health
        for agent_name, data in heartbeats.items():
            last_run = datetime.fromisoformat(data["last_run"])
            time_since_run = (now - last_run).total_seconds() / 60  # minutes

            health_status = "healthy"
            if time_since_run > 60:  # No run in 1 hour
                health_status = "stale"
                report["alerts"].append(f"⚠️ {agent_name} hasn't run in {int(time_since_run)} minutes")
            elif data["status"] == "error":
                health_status = "error"
                report["alerts"].append(f"❌ {agent_name} last run resulted in error")

            report["agents"][agent_name] = {
                "last_run": data["last_run"],
                "minutes_ago": round(time_since_run, 1),
                "status": data["status"],
                "health": health_status,
                "metadata": data.get("metadata", {})
            }

        # Check API health
        for api_name, data in api_statuses.items():
            last_checked = datetime.fromisoformat(data["last_checked"])
            time_since_check = (now - last_checked).total_seconds() / 60  # minutes

            health_status = "healthy"
            if data["status"] == "down":
                health_status = "down"
                report["alerts"].append(f"🔴 {api_name} API is DOWN")
            elif data["status"] == "slow":
                health_status = "slow"
                report["alerts"].append(f"🟡 {api_name} API is responding slowly")

            report["apis"][api_name] = {
                "last_checked": data["last_checked"],
                "minutes_ago": round(time_since_check, 1),
                "status": data["status"],
                "response_time": data.get("response_time"),
                "error": data.get("error"),
                "health": health_status
            }

        return report

    def print_health_report(self):
        """Print colorized health report to console"""
        report = self.get_health_report()

        cprint("\n" + "="*80, "cyan")
        cprint("🌙 MOON DEV AGENT HEALTH MONITOR", "white", "on_blue")
        cprint("="*80 + "\n", "cyan")

        # Print alerts first
        if report["alerts"]:
            cprint("🚨 ALERTS:", "red", attrs=["bold"])
            for alert in report["alerts"]:
                cprint(f"  {alert}", "red")
            print()
        else:
            cprint("✅ All systems healthy!", "green", attrs=["bold"])
            print()

        # Print agent status
        cprint("🤖 AGENTS:", "cyan", attrs=["bold"])
        if not report["agents"]:
            cprint("  No agents have reported yet", "yellow")
        else:
            for agent_name, data in sorted(report["agents"].items()):
                status_color = {
                    "healthy": "green",
                    "stale": "yellow",
                    "error": "red"
                }.get(data["health"], "white")

                status_icon = {
                    "healthy": "✅",
                    "stale": "⚠️",
                    "error": "❌"
                }.get(data["health"], "❓")

                cprint(f"  {status_icon} {agent_name:25s} ", status_color, end="")
                cprint(f"Last run: {data['minutes_ago']}m ago ({data['status']})", "white")

        print()

        # Print API status
        cprint("🌐 APIs:", "cyan", attrs=["bold"])
        if not report["apis"]:
            cprint("  No API checks yet", "yellow")
        else:
            for api_name, data in sorted(report["apis"].items()):
                status_color = {
                    "healthy": "green",
                    "slow": "yellow",
                    "down": "red"
                }.get(data["health"], "white")

                status_icon = {
                    "healthy": "🟢",
                    "slow": "🟡",
                    "down": "🔴"
                }.get(data["health"], "❓")

                cprint(f"  {status_icon} {api_name:25s} ", status_color, end="")
                if data.get("response_time"):
                    cprint(f"{data['response_time']:.2f}s", "white", end="")
                if data.get("error"):
                    cprint(f" - Error: {data['error']}", "red")
                else:
                    cprint("", "white")

        cprint("\n" + "="*80, "cyan")
        cprint(f"Report generated at: {report['timestamp']}", "white")
        cprint("="*80 + "\n", "cyan")

    def continuous_monitor(self, interval=30):
        """
        Continuously print health report

        Args:
            interval: Seconds between reports
        """
        try:
            while True:
                os.system('clear' if os.name == 'posix' else 'cls')
                self.print_health_report()
                time.sleep(interval)
        except KeyboardInterrupt:
            cprint("\n👋 Health monitor stopped", "yellow")


# Singleton instance
_monitor_instance = None

def get_monitor():
    """Get singleton monitor instance"""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = AgentHealthMonitor()
    return _monitor_instance


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Moon Dev Agent Health Monitor")
    parser.add_argument("--continuous", "-c", action="store_true", help="Run continuous monitoring")
    parser.add_argument("--interval", "-i", type=int, default=30, help="Refresh interval (seconds)")
    args = parser.parse_args()

    monitor = get_monitor()

    if args.continuous:
        cprint("🌙 Starting continuous health monitoring...", "cyan")
        cprint(f"📊 Refreshing every {args.interval} seconds", "cyan")
        cprint("Press Ctrl+C to stop\n", "yellow")
        monitor.continuous_monitor(interval=args.interval)
    else:
        monitor.print_health_report()
