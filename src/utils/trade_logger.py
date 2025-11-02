"""
🌙 Moon Dev's Trade Logger
Tracks all trades for strategy improvement analysis

Features:
- Logs every trade with full context (entry, exit, P&L, features)
- Aggregates daily performance
- Triggers improvement analysis on bad days
"""

import json
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from termcolor import cprint
import pandas as pd

class TradeLogger:
    """Logs all trades and triggers improvement analysis"""
    
    def __init__(self, log_dir: str = "src/data/trades"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.trades_file = self.log_dir / "trades.txt"
        self.daily_summary_file = self.log_dir / "daily_summary.csv"
        
        # Initialize files if they don't exist
        self._init_files()
        
        # Current session trades
        self.today_trades = []
        self.current_date = datetime.now().strftime("%Y-%m-%d")
    
    def _init_files(self):
        """Initialize log files with headers"""
        if not self.trades_file.exists():
            self.trades_file.write_text("# Moon Dev's Trade Log\n# Format: JSON per line\n")
        
        if not self.daily_summary_file.exists():
            with open(self.daily_summary_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'date', 'total_trades', 'winning_trades', 'losing_trades',
                    'win_rate', 'avg_pnl', 'total_pnl', 'sharpe', 'needs_improvement'
                ])
    
    def log_trade(self, 
                  symbol: str,
                  side: str,  # 'long' or 'short'
                  entry_price: float,
                  exit_price: float,
                  quantity: float,
                  pnl: float,
                  pnl_pct: float,
                  entry_time: datetime,
                  exit_time: datetime,
                  features: Dict,
                  reason: str = "") -> None:
        """Log a completed trade with all details"""
        
        trade = {
            'timestamp': datetime.now().isoformat(),
            'date': self.current_date,
            'symbol': symbol,
            'side': side,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'quantity': quantity,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'entry_time': entry_time.isoformat(),
            'exit_time': exit_time.isoformat(),
            'duration_minutes': (exit_time - entry_time).total_seconds() / 60,
            'is_winner': pnl > 0,
            'features': features,  # momentum, funding_rate, volatility, etc.
            'reason': reason  # Why we entered this trade
        }
        
        # Add to today's trades
        self.today_trades.append(trade)
        
        # Append to trades.txt
        with open(self.trades_file, 'a') as f:
            f.write(json.dumps(trade) + '\n')
        
        # Log to console
        color = 'green' if pnl > 0 else 'red'
        cprint(f"✅ Trade logged: {symbol} {side} | P&L: ${pnl:.2f} ({pnl_pct:.2f}%)", color)
    
    def analyze_daily_performance(self) -> Dict:
        """Analyze today's trading performance"""
        
        if not self.today_trades:
            return {
                'total_trades': 0,
                'needs_improvement': False
            }
        
        total = len(self.today_trades)
        winners = sum(1 for t in self.today_trades if t['is_winner'])
        losers = total - winners
        win_rate = winners / total if total > 0 else 0
        
        avg_pnl = sum(t['pnl'] for t in self.today_trades) / total
        total_pnl = sum(t['pnl'] for t in self.today_trades)
        
        # Calculate Sharpe (simplified)
        pnls = [t['pnl'] for t in self.today_trades]
        std_pnl = pd.Series(pnls).std() if len(pnls) > 1 else 1
        sharpe = (avg_pnl / std_pnl) if std_pnl > 0 else 0
        
        # Determine if we need improvement
        needs_improvement = (
            win_rate < 0.30 or  # Less than 30% win rate
            total_pnl < 0 or     # Negative P&L
            (total >= 10 and winners < 3)  # At least 10 trades but <3 winners
        )
        
        summary = {
            'date': self.current_date,
            'total_trades': total,
            'winning_trades': winners,
            'losing_trades': losers,
            'win_rate': win_rate,
            'avg_pnl': avg_pnl,
            'total_pnl': total_pnl,
            'sharpe': sharpe,
            'needs_improvement': needs_improvement
        }
        
        # Log summary
        with open(self.daily_summary_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                summary['date'],
                summary['total_trades'],
                summary['winning_trades'],
                summary['losing_trades'],
                f"{summary['win_rate']:.2%}",
                f"{summary['avg_pnl']:.2f}",
                f"{summary['total_pnl']:.2f}",
                f"{summary['sharpe']:.2f}",
                summary['needs_improvement']
            ])
        
        # Print summary
        cprint(f"\n{'='*60}", "cyan")
        cprint(f"📊 Daily Trading Summary - {self.current_date}", "cyan", attrs=['bold'])
        cprint(f"{'='*60}", "cyan")
        cprint(f"Total Trades: {total}", "white")
        cprint(f"Winners: {winners} | Losers: {losers}", "white")
        cprint(f"Win Rate: {win_rate:.1%}", "green" if win_rate >= 0.5 else "yellow")
        cprint(f"Total P&L: ${total_pnl:.2f}", "green" if total_pnl > 0 else "red")
        cprint(f"Avg P&L: ${avg_pnl:.2f}", "white")
        cprint(f"Sharpe: {sharpe:.2f}", "white")
        
        if needs_improvement:
            cprint(f"\n⚠️  BAD DAY DETECTED - Triggering Strategy Improvement Analysis", "red", attrs=['bold'])
        else:
            cprint(f"\n✅ Good day - Strategy performing well", "green")
        
        cprint(f"{'='*60}\n", "cyan")
        
        return summary
    
    def get_losing_trades(self) -> List[Dict]:
        """Get all losing trades from today for analysis"""
        return [t for t in self.today_trades if not t['is_winner']]
    
    def get_trade_patterns(self) -> Dict:
        """Analyze patterns in losing trades"""
        
        losers = self.get_losing_trades()
        if not losers:
            return {}
        
        patterns = {
            'high_funding_longs': [],
            'low_momentum_entries': [],
            'high_volatility_trades': [],
            'overextended_entries': []
        }
        
        for trade in losers:
            features = trade.get('features', {})
            
            # Check for high funding on longs
            if trade['side'] == 'long' and features.get('funding_rate', 0) > 0.5:
                patterns['high_funding_longs'].append(trade)
            
            # Check for low momentum
            if features.get('momentum_zscore', 0) < 0.5:
                patterns['low_momentum_entries'].append(trade)
            
            # Check for high volatility
            if features.get('volatility', 0) > 0.05:  # >5% daily vol
                patterns['high_volatility_trades'].append(trade)
            
            # Check for overextended
            if features.get('rsi', 50) > 75 or features.get('rsi', 50) < 25:
                patterns['overextended_entries'].append(trade)
        
        return patterns
    
    def export_for_analysis(self, output_file: Optional[str] = None) -> str:
        """Export today's trades for LLM analysis"""
        
        if output_file is None:
            output_file = self.log_dir / f"analysis_input_{self.current_date}.json"
        
        analysis_data = {
            'date': self.current_date,
            'summary': self.analyze_daily_performance(),
            'all_trades': self.today_trades,
            'losing_trades': self.get_losing_trades(),
            'patterns': self.get_trade_patterns()
        }
        
        with open(output_file, 'w') as f:
            json.dump(analysis_data, f, indent=2)
        
        cprint(f"📁 Analysis data exported to: {output_file}", "cyan")
        return str(output_file)
    
    def reset_daily(self):
        """Reset for new trading day"""
        self.today_trades = []
        self.current_date = datetime.now().strftime("%Y-%m-%d")


# Singleton instance
_logger_instance = None

def get_trade_logger() -> TradeLogger:
    """Get singleton trade logger instance"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = TradeLogger()
    return _logger_instance
