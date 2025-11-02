"""
🌙 Moon Dev's LLM Strategy Improver
Uses DeepSeek to analyze losing trades and suggest improvements

Triggered only on bad trading days (win rate < 30% or negative P&L)
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from termcolor import cprint
from datetime import datetime
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.models.deepseek_model import DeepSeekModel
from src.utils.trade_logger import TradeLogger, get_trade_logger


class LLMStrategyImprover:
    """Analyzes bad trading days and suggests strategy improvements"""
    
    def __init__(self, api_key: str):
        cprint("\n🧠 Initializing LLM Strategy Improver", "cyan", attrs=['bold'])
        
        # Use DeepSeek Reasoner for deep analysis
        self.llm = DeepSeekModel(
            api_key=api_key,
            model_name="deepseek-reasoner"  # Best for analytical tasks
        )
        
        self.trade_logger = get_trade_logger()
        self.improvements_log = Path("src/data/trades/improvements.json")
        
        cprint("✅ LLM Strategy Improver ready (DeepSeek Reasoner)", "green")
    
    def should_trigger_analysis(self, daily_summary: Dict) -> bool:
        """Check if we should trigger improvement analysis"""
        
        return daily_summary.get('needs_improvement', False)
    
    def analyze_losing_trades(self, trades: List[Dict]) -> str:
        """Analyze losing trades and identify patterns"""
        
        if not trades:
            return "No losing trades to analyze."
        
        cprint(f"\n🔍 Analyzing {len(trades)} losing trades...", "yellow")
        
        # Build analysis prompt
        trade_summaries = []
        for i, trade in enumerate(trades, 1):
            features = trade.get('features', {})
            summary = (
                f"Trade {i}:\n"
                f"  Symbol: {trade['symbol']}\n"
                f"  Side: {trade['side']}\n"
                f"  P&L: ${trade['pnl']:.2f} ({trade['pnl_pct']:.2f}%)\n"
                f"  Duration: {trade['duration_minutes']:.1f} min\n"
                f"  Features:\n"
                f"    - Momentum Z-Score: {features.get('momentum_zscore', 'N/A')}\n"
                f"    - Funding Rate: {features.get('funding_rate', 'N/A')}%\n"
                f"    - Volatility: {features.get('volatility', 'N/A')}\n"
                f"    - RSI: {features.get('rsi', 'N/A')}\n"
                f"    - Volume: {features.get('volume_zscore', 'N/A')}\n"
                f"  Reason: {trade.get('reason', 'N/A')}\n"
            )
            trade_summaries.append(summary)
        
        prompt = f"""You are an expert quantitative trading strategist analyzing a crypto momentum + mean-reversion strategy.

TODAY'S LOSING TRADES:
{''.join(trade_summaries)}

TASK:
1. Identify common patterns in these losing trades
2. Determine the root cause of losses (e.g., chasing overextended moves, high funding costs, low momentum, etc.)
3. Suggest 2-3 SPECIFIC, ACTIONABLE improvements to the strategy

FORMAT YOUR RESPONSE AS:

PATTERNS IDENTIFIED:
- [Pattern 1]
- [Pattern 2]
- [Pattern 3]

ROOT CAUSES:
- [Root cause analysis]

RECOMMENDED IMPROVEMENTS:
1. [Specific improvement with exact threshold/parameter]
2. [Specific improvement with exact threshold/parameter]
3. [Specific improvement with exact threshold/parameter]

EXPECTED IMPACT:
- [How this should improve performance]

Be SPECIFIC with numbers (e.g., "Skip longs if funding_rate > 0.5%" not "avoid high funding")
"""
        
        cprint("🤖 Asking DeepSeek Reasoner for analysis...", "cyan")
        
        response = self.llm.generate_response(
            system_prompt="You are a quantitative trading expert specializing in crypto momentum strategies.",
            user_content=prompt,
            temperature=0.3,  # Lower temp for more focused analysis
            max_tokens=2048
        )
        
        analysis = response.content if hasattr(response, 'content') else str(response)
        
        cprint("\n📊 LLM Analysis Complete", "green")
        return analysis
    
    def extract_improvements(self, llm_analysis: str) -> List[Dict]:
        """Extract actionable improvements from LLM analysis"""
        
        improvements = []
        
        # Simple parsing of improvements section
        lines = llm_analysis.split('\n')
        in_improvements = False
        
        for line in lines:
            if 'RECOMMENDED IMPROVEMENTS' in line.upper():
                in_improvements = True
                continue
            
            if in_improvements:
                if line.strip().startswith(('1.', '2.', '3.', '-')):
                    improvement_text = line.strip().lstrip('123.- ')
                    
                    improvements.append({
                        'description': improvement_text,
                        'timestamp': datetime.now().isoformat(),
                        'status': 'proposed',
                        'validated': False
                    })
                
                # Stop at next major section
                if any(keyword in line.upper() for keyword in ['EXPECTED IMPACT', 'CONCLUSION']):
                    break
        
        return improvements
    
    def run_improvement_cycle(self) -> Optional[Dict]:
        """Main improvement cycle - triggered on bad days"""
        
        cprint("\n" + "="*70, "magenta")
        cprint("🔄 STRATEGY IMPROVEMENT CYCLE TRIGGERED", "magenta", attrs=['bold'])
        cprint("="*70 + "\n", "magenta")
        
        # Get daily performance
        daily_summary = self.trade_logger.analyze_daily_performance()
        
        # Check if improvement is needed
        if not self.should_trigger_analysis(daily_summary):
            cprint("✅ Performance acceptable - No improvement needed", "green")
            return None
        
        cprint("⚠️  Bad trading day detected - Starting deep analysis", "yellow")
        
        # Step 1: Export trade data
        analysis_file = self.trade_logger.export_for_analysis()
        
        # Step 2: Get losing trades
        losing_trades = self.trade_logger.get_losing_trades()
        
        if not losing_trades:
            cprint("No losing trades to analyze", "yellow")
            return None
        
        # Step 3: LLM Analysis
        llm_analysis = self.analyze_losing_trades(losing_trades)
        
        # Print analysis
        cprint("\n" + "="*70, "cyan")
        cprint("🧠 DEEPSEEK ANALYSIS", "cyan", attrs=['bold'])
        cprint("="*70, "cyan")
        print(llm_analysis)
        cprint("="*70 + "\n", "cyan")
        
        # Step 4: Extract improvements
        improvements = self.extract_improvements(llm_analysis)
        
        if not improvements:
            cprint("⚠️  No specific improvements extracted", "yellow")
            return None
        
        cprint(f"\n✨ Extracted {len(improvements)} improvement proposals:", "green")
        for i, imp in enumerate(improvements, 1):
            cprint(f"  {i}. {imp['description']}", "white")
        
        # Step 5: Save improvements for validation
        improvement_record = {
            'timestamp': datetime.now().isoformat(),
            'daily_summary': daily_summary,
            'llm_analysis': llm_analysis,
            'proposed_improvements': improvements,
            'losing_trades_count': len(losing_trades),
            'status': 'awaiting_validation'
        }
        
        self._save_improvement_record(improvement_record)
        
        cprint("\n💾 Improvements saved - Ready for validation step", "cyan")
        
        return improvement_record
    
    def _save_improvement_record(self, record: Dict):
        """Save improvement record to log"""
        
        # Load existing records
        if self.improvements_log.exists():
            with open(self.improvements_log, 'r') as f:
                records = json.load(f)
        else:
            records = []
        
        records.append(record)
        
        # Save
        self.improvements_log.parent.mkdir(parents=True, exist_ok=True)
        with open(self.improvements_log, 'w') as f:
            json.dump(records, f, indent=2)
        
        cprint(f"📝 Improvement record saved to: {self.improvements_log}", "cyan")


def main():
    """Test the LLM Strategy Improver"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    api_key = os.getenv('DEEPSEEK_KEY')
    if not api_key:
        cprint("❌ DEEPSEEK_KEY not found in .env", "red")
        return
    
    # Initialize
    improver = LLMStrategyImprover(api_key)
    
    # Simulate some losing trades for testing
    logger = get_trade_logger()
    
    cprint("\n🧪 Simulating bad trading day for testing...", "yellow")
    
    from datetime import datetime, timedelta
    now = datetime.now()
    
    # Simulate 10 trades, 8 losers
    for i in range(10):
        is_winner = i < 2  # Only first 2 are winners
        
        logger.log_trade(
            symbol=f"BTC/USDT",
            side='long' if i % 2 == 0 else 'short',
            entry_price=50000 + i*100,
            exit_price=50000 + i*100 + (50 if is_winner else -100),
            quantity=0.1,
            pnl=5 if is_winner else -10,
            pnl_pct=0.1 if is_winner else -0.2,
            entry_time=now - timedelta(hours=2),
            exit_time=now - timedelta(hours=1),
            features={
                'momentum_zscore': 0.3 if not is_winner else 1.5,
                'funding_rate': 1.2 if not is_winner else 0.2,
                'volatility': 0.06 if not is_winner else 0.03,
                'rsi': 80 if not is_winner else 60,
                'volume_zscore': 0.5
            },
            reason="High momentum signal" if is_winner else "Low momentum + high funding"
        )
    
    # Run improvement cycle
    result = improver.run_improvement_cycle()
    
    if result:
        cprint("\n✅ Improvement cycle completed", "green")
        cprint(f"Next step: Validate improvements with Research Agent", "cyan")
    

if __name__ == "__main__":
    main()
