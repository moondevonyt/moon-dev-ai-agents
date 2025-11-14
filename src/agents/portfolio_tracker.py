"""
🌙 Moon Dev's Portfolio Tracker
Tracks all trades, PnL, win rate, and agent performance
Built with love by Moon Dev 🚀
"""

import pandas as pd
from datetime import datetime
from pathlib import Path
import json
from termcolor import cprint
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

class PortfolioTracker:
    """Comprehensive portfolio and trade tracking"""

    def __init__(self, data_dir="src/data/portfolio_tracker"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.trades_file = self.data_dir / "trades_history.csv"
        self.positions_file = self.data_dir / "open_positions.csv"
        self.performance_file = self.data_dir / "agent_performance.json"

        # Initialize files
        self._init_files()

    def _init_files(self):
        """Initialize CSV files with headers if they don't exist"""
        if not self.trades_file.exists():
            df = pd.DataFrame(columns=[
                'trade_id', 'timestamp_open', 'timestamp_close', 'agent_name',
                'token_address', 'token_symbol', 'entry_price', 'exit_price',
                'quantity', 'pnl_usd', 'pnl_percent', 'fees_usd', 'duration_minutes',
                'win', 'strategy', 'notes'
            ])
            df.to_csv(self.trades_file, index=False)

        if not self.positions_file.exists():
            df = pd.DataFrame(columns=[
                'position_id', 'timestamp_open', 'agent_name', 'token_address',
                'token_symbol', 'entry_price', 'quantity', 'usd_value',
                'strategy', 'notes'
            ])
            df.to_csv(self.positions_file, index=False)

        if not self.performance_file.exists():
            with open(self.performance_file, 'w') as f:
                json.dump({}, f)

    def log_position_open(self, agent_name, token_address, token_symbol,
                          entry_price, quantity, usd_value, strategy="", notes=""):
        """
        Log a new position opening

        Args:
            agent_name: Which agent opened this position
            token_address: Token contract address
            token_symbol: Token symbol
            entry_price: Entry price
            quantity: Quantity purchased
            usd_value: Total USD value
            strategy: Strategy name (optional)
            notes: Additional notes (optional)

        Returns:
            position_id
        """
        positions_df = pd.read_csv(self.positions_file)

        position_id = f"{agent_name}_{token_symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        new_position = {
            'position_id': position_id,
            'timestamp_open': datetime.now().isoformat(),
            'agent_name': agent_name,
            'token_address': token_address,
            'token_symbol': token_symbol,
            'entry_price': entry_price,
            'quantity': quantity,
            'usd_value': usd_value,
            'strategy': strategy,
            'notes': notes
        }

        positions_df = pd.concat([positions_df, pd.DataFrame([new_position])], ignore_index=True)
        positions_df.to_csv(self.positions_file, index=False)

        cprint(f"📈 Position opened: {token_symbol} by {agent_name}", "green")
        return position_id

    def log_position_close(self, position_id, exit_price, fees_usd=0, notes=""):
        """
        Log a position closing

        Args:
            position_id: ID of position to close
            exit_price: Exit price
            fees_usd: Trading fees in USD
            notes: Additional notes

        Returns:
            trade dict with PnL info
        """
        # Get position
        positions_df = pd.read_csv(self.positions_file)
        position = positions_df[positions_df['position_id'] == position_id]

        if len(position) == 0:
            cprint(f"❌ Position {position_id} not found", "red")
            return None

        position = position.iloc[0]

        # Calculate PnL
        entry_price = position['entry_price']
        quantity = position['quantity']
        entry_value = position['usd_value']

        exit_value = exit_price * quantity
        pnl_usd = exit_value - entry_value - fees_usd
        pnl_percent = (pnl_usd / entry_value) * 100 if entry_value > 0 else 0

        # Calculate duration
        timestamp_open = pd.to_datetime(position['timestamp_open'])
        timestamp_close = datetime.now()
        duration_minutes = (timestamp_close - timestamp_open).total_seconds() / 60

        # Create trade record
        trade = {
            'trade_id': position_id,
            'timestamp_open': position['timestamp_open'],
            'timestamp_close': timestamp_close.isoformat(),
            'agent_name': position['agent_name'],
            'token_address': position['token_address'],
            'token_symbol': position['token_symbol'],
            'entry_price': entry_price,
            'exit_price': exit_price,
            'quantity': quantity,
            'pnl_usd': pnl_usd,
            'pnl_percent': pnl_percent,
            'fees_usd': fees_usd,
            'duration_minutes': duration_minutes,
            'win': pnl_usd > 0,
            'strategy': position['strategy'],
            'notes': notes
        }

        # Append to trades history
        trades_df = pd.read_csv(self.trades_file)
        trades_df = pd.concat([trades_df, pd.DataFrame([trade])], ignore_index=True)
        trades_df.to_csv(self.trades_file, index=False)

        # Remove from open positions
        positions_df = positions_df[positions_df['position_id'] != position_id]
        positions_df.to_csv(self.positions_file, index=False)

        # Update agent performance
        self._update_agent_performance(position['agent_name'], trade)

        result = "WIN" if pnl_usd > 0 else "LOSS"
        cprint(f"📉 Position closed: {position['token_symbol']} by {position['agent_name']} | {result} | PnL: ${pnl_usd:.2f} ({pnl_percent:.2f}%)", "green" if pnl_usd > 0 else "red")

        return trade

    def _update_agent_performance(self, agent_name, trade):
        """Update agent performance stats"""
        with open(self.performance_file, 'r') as f:
            performance = json.load(f)

        if agent_name not in performance:
            performance[agent_name] = {
                'total_trades': 0,
                'wins': 0,
                'losses': 0,
                'total_pnl_usd': 0,
                'total_pnl_percent': 0,
                'avg_win_usd': 0,
                'avg_loss_usd': 0,
                'largest_win_usd': 0,
                'largest_loss_usd': 0,
                'win_rate': 0
            }

        stats = performance[agent_name]
        stats['total_trades'] += 1

        if trade['win']:
            stats['wins'] += 1
            stats['avg_win_usd'] = ((stats['avg_win_usd'] * (stats['wins'] - 1)) + trade['pnl_usd']) / stats['wins']
            if trade['pnl_usd'] > stats['largest_win_usd']:
                stats['largest_win_usd'] = trade['pnl_usd']
        else:
            stats['losses'] += 1
            stats['avg_loss_usd'] = ((stats['avg_loss_usd'] * (stats['losses'] - 1)) + trade['pnl_usd']) / stats['losses']
            if trade['pnl_usd'] < stats['largest_loss_usd']:
                stats['largest_loss_usd'] = trade['pnl_usd']

        stats['total_pnl_usd'] += trade['pnl_usd']
        stats['total_pnl_percent'] += trade['pnl_percent']
        stats['win_rate'] = (stats['wins'] / stats['total_trades']) * 100 if stats['total_trades'] > 0 else 0

        with open(self.performance_file, 'w') as f:
            json.dump(performance, f, indent=2, default=str)

    def get_open_positions(self):
        """Get all open positions"""
        return pd.read_csv(self.positions_file)

    def get_trade_history(self, limit=None, agent_name=None):
        """
        Get trade history

        Args:
            limit: Max number of trades to return
            agent_name: Filter by agent name

        Returns:
            DataFrame of trades
        """
        df = pd.read_csv(self.trades_file)

        if agent_name:
            df = df[df['agent_name'] == agent_name]

        if limit:
            df = df.tail(limit)

        return df

    def get_agent_performance(self):
        """Get performance stats for all agents"""
        with open(self.performance_file, 'r') as f:
            return json.load(f)

    def get_portfolio_summary(self):
        """Get comprehensive portfolio summary"""
        trades_df = pd.read_csv(self.trades_file)
        positions_df = pd.read_csv(self.positions_file)
        performance = self.get_agent_performance()

        summary = {
            'total_trades': len(trades_df),
            'open_positions': len(positions_df),
            'total_pnl': trades_df['pnl_usd'].sum() if len(trades_df) > 0 else 0,
            'total_wins': len(trades_df[trades_df['win'] == True]) if len(trades_df) > 0 else 0,
            'total_losses': len(trades_df[trades_df['win'] == False]) if len(trades_df) > 0 else 0,
            'overall_win_rate': (len(trades_df[trades_df['win'] == True]) / len(trades_df) * 100) if len(trades_df) > 0 else 0,
            'avg_pnl_per_trade': trades_df['pnl_usd'].mean() if len(trades_df) > 0 else 0,
            'best_trade': trades_df['pnl_usd'].max() if len(trades_df) > 0 else 0,
            'worst_trade': trades_df['pnl_usd'].min() if len(trades_df) > 0 else 0,
            'agent_performance': performance
        }

        return summary

    def print_portfolio_summary(self):
        """Print colorized portfolio summary"""
        summary = self.get_portfolio_summary()

        cprint("\n" + "="*80, "cyan")
        cprint("🌙 MOON DEV PORTFOLIO SUMMARY", "white", "on_blue")
        cprint("="*80, "cyan")

        cprint(f"\n📊 Overall Performance:", "cyan", attrs=["bold"])
        cprint(f"  Total Trades: {summary['total_trades']}", "white")
        cprint(f"  Open Positions: {summary['open_positions']}", "white")
        pnl_color = "green" if summary['total_pnl'] > 0 else "red"
        cprint(f"  Total PnL: ${summary['total_pnl']:.2f}", pnl_color, attrs=["bold"])
        cprint(f"  Win Rate: {summary['overall_win_rate']:.1f}% ({summary['total_wins']}W / {summary['total_losses']}L)", "white")
        cprint(f"  Avg PnL/Trade: ${summary['avg_pnl_per_trade']:.2f}", "white")
        cprint(f"  Best Trade: ${summary['best_trade']:.2f}", "green")
        cprint(f"  Worst Trade: ${summary['worst_trade']:.2f}", "red")

        cprint(f"\n🏆 Agent Performance Leaderboard:", "cyan", attrs=["bold"])
        if not summary['agent_performance']:
            cprint("  No agent data yet", "yellow")
        else:
            # Sort by total PnL
            sorted_agents = sorted(
                summary['agent_performance'].items(),
                key=lambda x: x[1]['total_pnl_usd'],
                reverse=True
            )

            for i, (agent_name, stats) in enumerate(sorted_agents, 1):
                medal = ["🥇", "🥈", "🥉"][i-1] if i <= 3 else f"{i}."
                pnl_color = "green" if stats['total_pnl_usd'] > 0 else "red"

                cprint(f"  {medal} {agent_name}:", "white", attrs=["bold"])
                cprint(f"     PnL: ${stats['total_pnl_usd']:.2f} | Win Rate: {stats['win_rate']:.1f}% | Trades: {stats['total_trades']}", pnl_color)

        cprint("\n" + "="*80, "cyan")


# Singleton instance
_tracker_instance = None

def get_tracker():
    """Get singleton tracker instance"""
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = PortfolioTracker()
    return _tracker_instance


if __name__ == "__main__":
    tracker = get_tracker()
    tracker.print_portfolio_summary()
