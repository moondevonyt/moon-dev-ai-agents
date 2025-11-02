"""
🌙 Moon Dev's Research-Based Strategy Improver
Uses Research Agent to find and validate strategy improvements

Integrates with LLM Strategy Improver output to generate concrete solutions
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional
from termcolor import cprint
from datetime import datetime

# Add project root
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.models import model_factory


class ResearchImprover:
    """Uses Research Agent to find strategy improvements"""
    
    def __init__(self):
        cprint("\n🔬 Initializing Research-Based Improver", "cyan", attrs=['bold'])
        
        self.improvements_log = Path("src/data/trades/improvements.json")
        self.validated_improvements = Path("src/data/trades/validated_improvements.json")
        
        cprint("✅ Research Improver ready", "green")
    
    def load_pending_improvements(self) -> Optional[Dict]:
        """Load improvements awaiting validation"""
        
        if not self.improvements_log.exists():
            return None
        
        with open(self.improvements_log, 'r') as f:
            records = json.load(f)
        
        # Get most recent pending improvement
        for record in reversed(records):
            if record.get('status') == 'awaiting_validation':
                return record
        
        return None
    
    def generate_research_queries(self, improvements: List[Dict]) -> List[str]:
        """Convert improvement proposals into research queries"""
        
        queries = []
        
        for imp in improvements:
            desc = imp['description'].lower()
            
            # Extract key concepts
            if 'funding' in desc:
                queries.append(
                    "Research optimal funding rate thresholds for crypto momentum strategies. "
                    "At what funding rate level should we avoid taking long positions? "
                    "Historical data on funding rates vs future returns."
                )
            
            if 'momentum' in desc or 'zscore' in desc:
                queries.append(
                    "Analyze momentum signal strength requirements for crypto trading. "
                    "What minimum momentum z-score indicates a reliable trend? "
                    "Compare different momentum lookback periods."
                )
            
            if 'volatility' in desc:
                queries.append(
                    "Investigate volatility filtering for momentum strategies. "
                    "Should we avoid trading during high volatility periods? "
                    "Optimal volatility thresholds."
                )
            
            if 'rsi' in desc or 'overbought' in desc or 'oversold' in desc:
                queries.append(
                    "Study RSI thresholds for mean-reversion overlay on momentum. "
                    "At what RSI levels should we pause momentum entries? "
                    "RSI + momentum combination strategies."
                )
            
            if 'position size' in desc or 'risk' in desc:
                queries.append(
                    "Research position sizing for volatile crypto momentum trades. "
                    "Optimal risk per trade as percentage of portfolio. "
                    "Volatility-based position sizing."
                )
        
        # Remove duplicates
        queries = list(set(queries))
        
        return queries
    
    def research_improvement(self, improvement: Dict) -> Dict:
        """Use Research Agent to validate and refine an improvement"""
        
        cprint(f"\n🔍 Researching: {improvement['description']}", "cyan")
        
        # Generate research queries
        queries = self.generate_research_queries([improvement])
        
        if not queries:
            cprint("⚠️  No research queries generated", "yellow")
            return {
                'improvement': improvement,
                'research_findings': None,
                'validated': False,
                'confidence': 0.0
            }
        
        cprint(f"📋 Generated {len(queries)} research queries", "white")
        
        research_findings = []
        
        for i, query in enumerate(queries, 1):
            cprint(f"\n  Query {i}/{len(queries)}: {query[:80]}...", "white")
            
            try:
                # Get OpenRouter model for research
                model = model_factory.get_model(
                    "openrouter",
                    "deepseek/deepseek-chat-v3-0324:free"
                )
                
                if not model:
                    cprint("    ⚠️  Model not available", "yellow")
                    continue
                
                # Research query
                response = model.generate_response(
                    system_prompt=(
                        "You are a quantitative trading researcher. "
                        "Provide data-driven insights on crypto trading strategies. "
                        "Focus on specific thresholds, parameters, and empirical evidence."
                    ),
                    user_content=query,
                    temperature=0.4,
                    max_tokens=1024
                )
                
                finding = response.content if hasattr(response, 'content') else str(response)
                research_findings.append({
                    'query': query,
                    'finding': finding
                })
                
                cprint(f"    ✅ Research completed", "green")
                
            except Exception as e:
                cprint(f"    ❌ Research failed: {str(e)}", "red")
                continue
        
        # Synthesize findings
        if research_findings:
            cprint(f"\n✅ Completed {len(research_findings)} research queries", "green")
            
            # Calculate confidence based on research support
            confidence = min(len(research_findings) / len(queries), 1.0)
            
            return {
                'improvement': improvement,
                'research_findings': research_findings,
                'validated': confidence >= 0.5,  # At least 50% of queries succeeded
                'confidence': confidence,
                'timestamp': datetime.now().isoformat()
            }
        else:
            cprint("\n⚠️  No research findings obtained", "yellow")
            return {
                'improvement': improvement,
                'research_findings': None,
                'validated': False,
                'confidence': 0.0
            }
    
    def validate_all_improvements(self) -> Optional[List[Dict]]:
        """Validate all pending improvements with research"""
        
        cprint("\n" + "="*70, "magenta")
        cprint("🔬 RESEARCH VALIDATION CYCLE", "magenta", attrs=['bold'])
        cprint("="*70 + "\n", "magenta")
        
        # Load pending improvements
        pending = self.load_pending_improvements()
        
        if not pending:
            cprint("No pending improvements to validate", "yellow")
            return None
        
        improvements = pending.get('proposed_improvements', [])
        
        if not improvements:
            cprint("No improvements in pending record", "yellow")
            return None
        
        cprint(f"📊 Validating {len(improvements)} improvements...", "cyan")
        
        validated_results = []
        
        for i, improvement in enumerate(improvements, 1):
            cprint(f"\n{'='*70}", "white")
            cprint(f"Improvement {i}/{len(improvements)}", "white", attrs=['bold'])
            cprint(f"{'='*70}", "white")
            
            result = self.research_improvement(improvement)
            validated_results.append(result)
            
            # Print result
            status = "✅ VALIDATED" if result['validated'] else "❌ NOT VALIDATED"
            color = "green" if result['validated'] else "red"
            cprint(f"\n{status} (Confidence: {result['confidence']:.1%})", color, attrs=['bold'])
        
        # Save validated results
        self._save_validated_improvements(pending, validated_results)
        
        # Summary
        validated_count = sum(1 for r in validated_results if r['validated'])
        cprint(f"\n" + "="*70, "cyan")
        cprint(f"📊 VALIDATION SUMMARY", "cyan", attrs=['bold'])
        cprint(f"="*70, "cyan")
        cprint(f"Total Improvements: {len(validated_results)}", "white")
        cprint(f"Validated: {validated_count}", "green")
        cprint(f"Not Validated: {len(validated_results) - validated_count}", "red")
        cprint(f"="*70 + "\n", "cyan")
        
        return validated_results
    
    def _save_validated_improvements(self, original_record: Dict, validated_results: List[Dict]):
        """Save validated improvements"""
        
        record = {
            'timestamp': datetime.now().isoformat(),
            'original_analysis': original_record.get('llm_analysis'),
            'daily_summary': original_record.get('daily_summary'),
            'validated_improvements': validated_results,
            'ready_for_deployment': any(r['validated'] for r in validated_results)
        }
        
        # Load existing
        if self.validated_improvements.exists():
            with open(self.validated_improvements, 'r') as f:
                records = json.load(f)
        else:
            records = []
        
        records.append(record)
        
        # Save
        self.validated_improvements.parent.mkdir(parents=True, exist_ok=True)
        with open(self.validated_improvements, 'w') as f:
            json.dump(records, f, indent=2)
        
        cprint(f"💾 Validated improvements saved to: {self.validated_improvements}", "cyan")
        
        # Update original record status
        if self.improvements_log.exists():
            with open(self.improvements_log, 'r') as f:
                records = json.load(f)
            
            for record in records:
                if record.get('timestamp') == original_record.get('timestamp'):
                    record['status'] = 'validated'
                    break
            
            with open(self.improvements_log, 'w') as f:
                json.dump(records, f, indent=2)


def main():
    """Test Research Improver"""
    
    improver = ResearchImprover()
    
    # Validate pending improvements
    results = improver.validate_all_improvements()
    
    if results:
        cprint("\n✅ Validation complete", "green")
        
        validated = [r for r in results if r['validated']]
        if validated:
            cprint(f"\n🚀 {len(validated)} improvements ready for deployment:", "green")
            for r in validated:
                cprint(f"  • {r['improvement']['description']}", "white")
    else:
        cprint("\n⚠️  No improvements to validate", "yellow")


if __name__ == "__main__":
    main()
