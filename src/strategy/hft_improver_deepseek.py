"""
🌙 Moon Dev's HFT Strategy Improver - DeepSeek Only
Stündliche Verbesserung für High-Frequency Trading

Nutzt NUR DeepSeek (deepseek-chat oder deepseek-reasoner)
Kein OpenRouter!
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from termcolor import cprint
from datetime import datetime
import sys

# Add project root
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.models.deepseek_model import DeepSeekModel


class HFTImproverDeepSeek:
    """Stündliche HFT Strategy Verbesserung mit DeepSeek"""
    
    def __init__(self, api_key: str, model_name: str = "deepseek-reasoner"):
        cprint("\n🧠 Initializing HFT Improver (DeepSeek)", "cyan", attrs=['bold'])
        
        # DeepSeek Model (kein OpenRouter!)
        self.llm = DeepSeekModel(
            api_key=api_key,
            model_name=model_name  # "deepseek-chat" or "deepseek-reasoner"
        )
        
        self.hourly_log = Path("src/data/trades/hft_hourly_analysis.json")
        self.hourly_log.parent.mkdir(parents=True, exist_ok=True)
        
        cprint(f"✅ HFT Improver ready (Model: {model_name})", "green")
    
    def analyze_hourly_trades(self, hourly_trades: List[Dict], stats: Dict) -> Optional[Dict]:
        """
        Analysiert Trades der letzten Stunde mit DeepSeek
        
        Args:
            hourly_trades: Liste aller Trades der letzten Stunde
            stats: Performance Stats (win_rate, pnl, etc.)
        
        Returns:
            Analysis mit Verbesserungsvorschlägen
        """
        
        if not hourly_trades:
            return None
        
        # Nur bei schlechter Performance
        if not stats.get('needs_improvement', False):
            cprint("✅ Hourly performance good - No analysis needed", "green")
            return None
        
        cprint(f"\n{'='*70}", "yellow")
        cprint(f"⚠️  POOR HOURLY PERFORMANCE - Starting DeepSeek Analysis", "yellow", attrs=['bold'])
        cprint(f"{'='*70}\n", "yellow")
        
        # Build analysis prompt
        trade_summaries = []
        for i, trade in enumerate(hourly_trades, 1):
            features = trade.get('features', {})
            outcome = "WIN" if trade.get('is_winner', False) else "LOSS"
            
            summary = (
                f"Trade {i} ({outcome}):\n"
                f"  Side: {trade['side'].upper()}\n"
                f"  Entry: ${trade['entry_price']:.2f}\n"
                f"  Features:\n"
                f"    - Momentum Z-Score: {features.get('momentum_zscore', 0):.2f}\n"
                f"    - RSI: {features.get('rsi', 50):.1f}\n"
                f"    - Volume Spike: {features.get('volume_spike', 1.0):.2f}x\n"
                f"    - Volatility: {features.get('volatility', 0):.4f}\n"
                f"    - 5-candle Return: {features.get('returns_5', 0):.2%}\n"
                f"  Reason: {trade.get('reason', 'N/A')}\n"
            )
            trade_summaries.append(summary)
        
        prompt = f"""You are an expert High-Frequency Trading strategist analyzing a crypto HFT strategy.

HOURLY PERFORMANCE:
- Total Trades: {stats['total_trades']}
- Winners: {stats['winners']} | Losers: {stats['losers']}
- Win Rate: {stats['win_rate']:.1%}
- Total P&L: ${stats['total_pnl']:.2f}

STRATEGY DETAILS:
- Uses 1h timeframe for trend direction (only LONG when 1h bullish, only SHORT when 1h bearish)
- Executes on 1m/5m timeframe with tight stops (0.5%) and quick targets (1%)
- Goal: Win rate > 50% for HFT profitability

TRADES THIS HOUR:
{''.join(trade_summaries)}

TASK:
1. Identify why the win rate is < 50% this hour
2. Find common patterns in losing trades
3. Suggest 2-3 SPECIFIC improvements to increase win rate

Focus on:
- Signal quality filters (momentum thresholds, RSI ranges)
- Volume confirmation requirements
- Volatility conditions
- Timing improvements

FORMAT YOUR RESPONSE AS:

ANALYSIS:
- [Key insight 1]
- [Key insight 2]

LOSING PATTERNS:
- [Pattern found in losers]

IMPROVEMENTS:
1. [Specific improvement with exact threshold]
2. [Specific improvement with exact threshold]
3. [Specific improvement with exact threshold]

Be SPECIFIC with numbers (e.g., "Require momentum_zscore > 1.2" not "stronger momentum")
"""
        
        cprint("🤖 Asking DeepSeek for hourly analysis...", "cyan")
        
        response = self.llm.generate_response(
            system_prompt="You are an expert HFT trading strategist specializing in crypto momentum strategies.",
            user_content=prompt,
            temperature=0.2,  # Low temp for focused analysis
            max_tokens=1536
        )
        
        analysis = response.content if hasattr(response, 'content') else str(response)
        
        cprint("\n📊 DeepSeek Analysis Complete", "green")
        
        # Print analysis
        cprint(f"\n{'='*70}", "cyan")
        cprint(f"🧠 DEEPSEEK HOURLY ANALYSIS", "cyan", attrs=['bold'])
        cprint(f"{'='*70}", "cyan")
        print(analysis)
        cprint(f"{'='*70}\n", "cyan")
        
        # Extract improvements
        improvements = self._extract_improvements(analysis)
        
        if improvements:
            cprint(f"✨ Extracted {len(improvements)} improvements:", "green")
            for i, imp in enumerate(improvements, 1):
                cprint(f"  {i}. {imp}", "white")
        
        # Save analysis
        analysis_record = {
            'timestamp': datetime.now().isoformat(),
            'hour': stats['hour'],
            'stats': stats,
            'analysis': analysis,
            'improvements': improvements,
            'trades_analyzed': len(hourly_trades)
        }
        
        self._save_analysis(analysis_record)
        
        return analysis_record
    
    def _extract_improvements(self, analysis_text: str) -> List[str]:
        """Extract improvement suggestions from DeepSeek analysis"""
        
        improvements = []
        lines = analysis_text.split('\n')
        in_improvements = False
        
        for line in lines:
            if 'IMPROVEMENTS' in line.upper() or 'RECOMMENDED' in line.upper():
                in_improvements = True
                continue
            
            if in_improvements:
                # Stop at next major section
                if any(keyword in line.upper() for keyword in ['EXPECTED', 'CONCLUSION', 'SUMMARY']):
                    break
                
                # Extract numbered improvements
                if line.strip() and (line.strip()[0].isdigit() or line.strip().startswith('-')):
                    improvement = line.strip().lstrip('0123456789.-) ')
                    if improvement:
                        improvements.append(improvement)
        
        return improvements
    
    def _save_analysis(self, record: Dict):
        """Save hourly analysis to log"""
        
        # Load existing
        if self.hourly_log.exists():
            with open(self.hourly_log, 'r') as f:
                records = json.load(f)
        else:
            records = []
        
        records.append(record)
        
        # Save
        with open(self.hourly_log, 'w') as f:
            json.dump(records, f, indent=2)
        
        cprint(f"💾 Analysis saved to: {self.hourly_log}", "cyan")
    
    def get_latest_improvements(self) -> Optional[List[str]]:
        """Get most recent improvements for auto-apply"""
        
        if not self.hourly_log.exists():
            return None
        
        with open(self.hourly_log, 'r') as f:
            records = json.load(f)
        
        if not records:
            return None
        
        return records[-1].get('improvements', [])


def main():
    """Test HFT Improver with DeepSeek"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    api_key = os.getenv('DEEPSEEK_KEY')
    if not api_key:
        cprint("❌ DEEPSEEK_KEY not found in .env", "red")
        return
    
    # Initialize
    improver = HFTImproverDeepSeek(
        api_key=api_key,
        model_name="deepseek-reasoner"  # or "deepseek-chat"
    )
    
    # Simulate poor hourly performance
    cprint("\n🧪 Simulating poor hourly trades...", "yellow")
    
    import numpy as np
    
    hourly_trades = []
    for i in range(20):  # 20 trades in 1 hour (HFT)
        is_winner = i < 8  # 40% win rate (poor)
        
        hourly_trades.append({
            'timestamp': datetime.now().isoformat(),
            'side': 'long' if i % 2 == 0 else 'short',
            'entry_price': 52000 + np.random.randn() * 50,
            'is_winner': is_winner,
            'features': {
                'momentum_zscore': 0.6 if not is_winner else 1.8,
                'rsi': 48 if not is_winner else 58,
                'volume_spike': 1.1 if not is_winner else 1.8,
                'volatility': 0.003,
                'returns_5': -0.001 if not is_winner else 0.003
            },
            'reason': 'HFT momentum signal'
        })
    
    stats = {
        'hour': datetime.now().strftime("%Y-%m-%d %H:00"),
        'total_trades': 20,
        'winners': 8,
        'losers': 12,
        'win_rate': 0.40,
        'total_pnl': -50.0,
        'needs_improvement': True
    }
    
    # Run analysis
    result = improver.analyze_hourly_trades(hourly_trades, stats)
    
    if result:
        cprint("\n✅ Hourly analysis complete", "green")
        improvements = result.get('improvements', [])
        if improvements:
            cprint(f"\n🚀 Ready to apply {len(improvements)} improvements", "cyan")


if __name__ == "__main__":
    main()
