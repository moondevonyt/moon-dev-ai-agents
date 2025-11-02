"""
🌙 Moon Dev's Self-Improving Trading Loop
Complete end-to-end adaptive learning system

Flow:
1. Trade Logger tracks all trades
2. On bad day (< 30% win rate), trigger improvement
3. LLM (DeepSeek) analyzes losing patterns
4. Research Agent validates improvements
5. Auto-apply validated changes to strategy
"""

import os
import sys
from pathlib import Path
from termcolor import cprint
from datetime import datetime
from dotenv import load_dotenv

# Add project root
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.trade_logger import get_trade_logger
from src.strategy.llm_strategy_improver import LLMStrategyImprover
from src.strategy.research_improver import ResearchImprover
from src.strategy.strategy_updater import StrategyUpdater


class SelfImprovingLoop:
    """Complete self-improving trading system"""
    
    def __init__(self):
        load_dotenv()
        
        cprint("\n" + "="*70, "magenta")
        cprint("🌙 MOON DEV'S SELF-IMPROVING TRADING SYSTEM", "magenta", attrs=['bold'])
        cprint("="*70 + "\n", "magenta")
        
        # Components
        self.trade_logger = get_trade_logger()
        
        deepseek_key = os.getenv('DEEPSEEK_KEY')
        if not deepseek_key:
            cprint("⚠️  DEEPSEEK_KEY not found - using OpenRouter instead", "yellow")
            deepseek_key = os.getenv('OPENROUTER_API_KEY_1', '')
        
        self.llm_improver = LLMStrategyImprover(deepseek_key) if deepseek_key else None
        self.research_improver = ResearchImprover()
        self.strategy_updater = StrategyUpdater()
        
        cprint("✅ All components initialized", "green")
    
    def check_daily_performance(self) -> bool:
        """Check if today was a bad day requiring improvement"""
        
        summary = self.trade_logger.analyze_daily_performance()
        return summary.get('needs_improvement', False)
    
    def run_full_improvement_cycle(self, dry_run: bool = True):
        """Run complete improvement cycle"""
        
        cprint("\n" + "="*70, "cyan")
        cprint("🔄 STARTING FULL IMPROVEMENT CYCLE", "cyan", attrs=['bold'])
        cprint("="*70 + "\n", "cyan")
        
        # Step 1: Check if improvement needed
        cprint("📊 Step 1: Analyzing Daily Performance", "white", attrs=['bold'])
        if not self.check_daily_performance():
            cprint("✅ Performance acceptable - No improvement needed\n", "green")
            return
        
        cprint("⚠️  Bad day detected - Proceeding with improvement\n", "yellow")
        
        # Step 2: LLM Analysis
        cprint("🧠 Step 2: LLM Strategy Analysis (DeepSeek)", "white", attrs=['bold'])
        if not self.llm_improver:
            cprint("❌ LLM Improver not available\n", "red")
            return
        
        improvement_record = self.llm_improver.run_improvement_cycle()
        
        if not improvement_record:
            cprint("⚠️  No improvements generated\n", "yellow")
            return
        
        # Step 3: Research Validation
        cprint("\n🔬 Step 3: Research-Based Validation", "white", attrs=['bold'])
        validated_results = self.research_improver.validate_all_improvements()
        
        if not validated_results:
            cprint("⚠️  No improvements validated\n", "yellow")
            return
        
        validated_count = sum(1 for r in validated_results if r.get('validated'))
        
        if validated_count == 0:
            cprint("❌ None of the improvements passed validation\n", "red")
            return
        
        # Step 4: Apply Improvements
        cprint("\n🚀 Step 4: Applying Strategy Improvements", "white", attrs=['bold'])
        
        if dry_run:
            cprint("🧪 DRY RUN MODE - No actual changes will be made\n", "yellow")
        
        success = self.strategy_updater.apply_improvements(dry_run=dry_run)
        
        if success:
            cprint("\n" + "="*70, "green")
            cprint("✅ IMPROVEMENT CYCLE COMPLETED SUCCESSFULLY", "green", attrs=['bold'])
            cprint("="*70, "green")
            
            if dry_run:
                cprint("\n💡 To apply for real, run with dry_run=False", "cyan")
            else:
                cprint("\n🎉 Strategy has been updated and committed!", "green")
                cprint("📝 Check git log for changes", "cyan")
        else:
            cprint("\n❌ Improvement cycle failed", "red")
    
    def simulate_bad_trading_day(self):
        """Simulate a bad trading day for testing"""
        
        cprint("\n🧪 SIMULATION: Creating bad trading day...", "yellow")
        
        from datetime import timedelta
        now = datetime.now()
        
        # Simulate 10 trades, 7 losers (30% win rate)
        test_trades = [
            # Winners
            {
                'symbol': 'BTC/USDT',
                'side': 'long',
                'entry_price': 50000,
                'exit_price': 50500,
                'pnl': 50,
                'pnl_pct': 1.0,
                'features': {
                    'momentum_zscore': 2.0,
                    'funding_rate': 0.1,
                    'volatility': 0.02,
                    'rsi': 65,
                    'volume_zscore': 1.5
                },
                'reason': 'Strong momentum + low funding'
            },
            {
                'symbol': 'ETH/USDT',
                'side': 'long',
                'entry_price': 3000,
                'exit_price': 3050,
                'pnl': 50,
                'pnl_pct': 1.67,
                'features': {
                    'momentum_zscore': 1.8,
                    'funding_rate': 0.2,
                    'volatility': 0.03,
                    'rsi': 60,
                    'volume_zscore': 1.2
                },
                'reason': 'Good momentum trend'
            },
            {
                'symbol': 'SOL/USDT',
                'side': 'short',
                'entry_price': 100,
                'exit_price': 98,
                'pnl': 20,
                'pnl_pct': 2.0,
                'features': {
                    'momentum_zscore': -1.5,
                    'funding_rate': 1.5,
                    'volatility': 0.04,
                    'rsi': 30,
                    'volume_zscore': -0.5
                },
                'reason': 'Weak momentum + high funding'
            },
            
            # Losers (common pattern: high funding on longs)
            {
                'symbol': 'DOGE/USDT',
                'side': 'long',
                'entry_price': 0.10,
                'exit_price': 0.095,
                'pnl': -50,
                'pnl_pct': -5.0,
                'features': {
                    'momentum_zscore': 0.5,  # Weak momentum
                    'funding_rate': 1.8,     # Very high funding
                    'volatility': 0.08,
                    'rsi': 78,               # Overbought
                    'volume_zscore': 0.3
                },
                'reason': 'Momentum signal but overextended'
            },
            {
                'symbol': 'SHIB/USDT',
                'side': 'long',
                'entry_price': 0.00001,
                'exit_price': 0.0000095,
                'pnl': -50,
                'pnl_pct': -5.0,
                'features': {
                    'momentum_zscore': 0.3,
                    'funding_rate': 2.0,
                    'volatility': 0.10,
                    'rsi': 82,
                    'volume_zscore': 0.2
                },
                'reason': 'High funding chase'
            },
            {
                'symbol': 'PEPE/USDT',
                'side': 'long',
                'entry_price': 0.000001,
                'exit_price': 0.00000092,
                'pnl': -80,
                'pnl_pct': -8.0,
                'features': {
                    'momentum_zscore': 0.4,
                    'funding_rate': 1.6,
                    'volatility': 0.12,
                    'rsi': 85,
                    'volume_zscore': 0.1
                },
                'reason': 'Chasing pump'
            },
            {
                'symbol': 'WIF/USDT',
                'side': 'long',
                'entry_price': 2.0,
                'exit_price': 1.85,
                'pnl': -75,
                'pnl_pct': -7.5,
                'features': {
                    'momentum_zscore': 0.6,
                    'funding_rate': 1.4,
                    'volatility': 0.09,
                    'rsi': 76,
                    'volume_zscore': 0.4
                },
                'reason': 'Weak momentum + high cost'
            },
            {
                'symbol': 'BONK/USDT',
                'side': 'long',
                'entry_price': 0.00002,
                'exit_price': 0.000018,
                'pnl': -100,
                'pnl_pct': -10.0,
                'features': {
                    'momentum_zscore': 0.2,
                    'funding_rate': 2.2,
                    'volatility': 0.15,
                    'rsi': 88,
                    'volume_zscore': 0.0
                },
                'reason': 'Extreme overextension'
            },
            {
                'symbol': 'FLOKI/USDT',
                'side': 'long',
                'entry_price': 0.0001,
                'exit_price': 0.000092,
                'pnl': -80,
                'pnl_pct': -8.0,
                'features': {
                    'momentum_zscore': 0.5,
                    'funding_rate': 1.9,
                    'volatility': 0.11,
                    'rsi': 80,
                    'volume_zscore': 0.2
                },
                'reason': 'High funding trap'
            },
            {
                'symbol': 'BOME/USDT',
                'side': 'long',
                'entry_price': 0.01,
                'exit_price': 0.009,
                'pnl': -100,
                'pnl_pct': -10.0,
                'features': {
                    'momentum_zscore': 0.3,
                    'funding_rate': 2.5,
                    'volatility': 0.14,
                    'rsi': 83,
                    'volume_zscore': 0.1
                },
                'reason': 'Chasing with high funding'
            }
        ]
        
        # Log all trades
        for trade in test_trades:
            is_winner = trade['pnl'] > 0
            
            self.trade_logger.log_trade(
                symbol=trade['symbol'],
                side=trade['side'],
                entry_price=trade['entry_price'],
                exit_price=trade['exit_price'],
                quantity=100,
                pnl=trade['pnl'],
                pnl_pct=trade['pnl_pct'],
                entry_time=now - timedelta(hours=4),
                exit_time=now - timedelta(hours=2),
                features=trade['features'],
                reason=trade['reason']
            )
        
        cprint(f"✅ Simulated {len(test_trades)} trades (3 winners, 7 losers = 30% win rate)\n", "green")


def main():
    """Run the self-improving loop"""
    
    # Initialize system
    loop = SelfImprovingLoop()
    
    # Simulate bad day for testing
    cprint("\n" + "="*70, "yellow")
    cprint("🧪 DEMO MODE - Simulating Bad Trading Day", "yellow", attrs=['bold'])
    cprint("="*70 + "\n", "yellow")
    
    loop.simulate_bad_trading_day()
    
    # Run improvement cycle
    loop.run_full_improvement_cycle(dry_run=True)
    
    cprint("\n" + "="*70, "cyan")
    cprint("📚 NEXT STEPS", "cyan", attrs=['bold'])
    cprint("="*70, "cyan")
    cprint("\n1. Review the analysis and proposed improvements above", "white")
    cprint("2. If satisfied, run with dry_run=False to apply changes", "white")
    cprint("3. The strategy will automatically update with validated improvements", "white")
    cprint("4. All changes are version-controlled via git commits", "white")
    cprint("5. Use strategy_updater.rollback_last_deployment() if needed\n", "white")


if __name__ == "__main__":
    main()
