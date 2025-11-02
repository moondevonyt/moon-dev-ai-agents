"""
🌙 Moon Dev's Strategy Auto-Updater
Automatically applies validated improvements to trading strategy

Features:
- Applies validated improvements
- Creates git commits for versioning
- Backs up before changes
- Rollback capability
"""

import json
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from termcolor import cprint
from datetime import datetime


class StrategyUpdater:
    """Automatically updates strategy with validated improvements"""
    
    def __init__(self, strategy_file: str = "src/strategy/momentum_strategy.py"):
        cprint("\n🔧 Initializing Strategy Updater", "cyan", attrs=['bold'])
        
        self.strategy_file = Path(strategy_file)
        self.validated_log = Path("src/data/trades/validated_improvements.json")
        self.deployment_log = Path("src/data/trades/deployments.json")
        self.backup_dir = Path("src/data/trades/strategy_backups")
        
        # Create directories
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        cprint("✅ Strategy Updater ready", "green")
    
    def load_validated_improvements(self) -> Optional[Dict]:
        """Load validated improvements ready for deployment"""
        
        if not self.validated_log.exists():
            return None
        
        with open(self.validated_log, 'r') as f:
            records = json.load(f)
        
        # Get most recent validated improvements
        for record in reversed(records):
            if record.get('ready_for_deployment'):
                return record
        
        return None
    
    def backup_strategy(self) -> str:
        """Backup current strategy before making changes"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"momentum_strategy_backup_{timestamp}.py"
        
        if self.strategy_file.exists():
            shutil.copy2(self.strategy_file, backup_file)
            cprint(f"💾 Strategy backed up to: {backup_file}", "cyan")
            return str(backup_file)
        else:
            cprint(f"⚠️  Strategy file not found: {self.strategy_file}", "yellow")
            return ""
    
    def generate_improvement_code(self, improvements: List[Dict]) -> str:
        """Generate Python code for improvements"""
        
        code_additions = []
        
        for imp in improvements:
            if not imp.get('validated'):
                continue
            
            desc = imp['improvement']['description'].lower()
            
            # Generate filter code based on improvement description
            if 'funding' in desc and 'long' in desc:
                # Extract threshold if mentioned
                threshold = 0.5  # Default
                if '0.5%' in desc or '0.5' in desc:
                    threshold = 0.5
                elif '1%' in desc or '1.0' in desc:
                    threshold = 1.0
                
                code = f"""
    # 🌙 Auto-improvement: Avoid longs with high funding
    if side == 'long' and features.get('funding_rate', 0) > {threshold}:
        logger.info(f"Skipping {{symbol}} long - funding rate {{features['funding_rate']:.2f}}% > {threshold}%")
        return None  # Skip this trade
"""
                code_additions.append(code)
            
            if 'momentum' in desc and ('threshold' in desc or 'minimum' in desc):
                threshold = 1.0  # Default z-score
                if '1.5' in desc:
                    threshold = 1.5
                elif '0.5' in desc:
                    threshold = 0.5
                
                code = f"""
    # 🌙 Auto-improvement: Require stronger momentum
    if features.get('momentum_zscore', 0) < {threshold}:
        logger.info(f"Skipping {{symbol}} - momentum {{features['momentum_zscore']:.2f}} < {threshold}")
        return None  # Skip this trade
"""
                code_additions.append(code)
            
            if 'rsi' in desc and ('overbought' in desc or 'oversold' in desc):
                upper = 75
                lower = 25
                
                code = f"""
    # 🌙 Auto-improvement: Avoid overextended entries
    rsi = features.get('rsi', 50)
    if side == 'long' and rsi > {upper}:
        logger.info(f"Skipping {{symbol}} long - RSI {{rsi}} > {upper} (overbought)")
        return None
    if side == 'short' and rsi < {lower}:
        logger.info(f"Skipping {{symbol}} short - RSI {{rsi}} < {lower} (oversold)")
        return None
"""
                code_additions.append(code)
            
            if 'volatility' in desc:
                threshold = 0.05  # 5% daily volatility
                
                code = f"""
    # 🌙 Auto-improvement: Avoid high volatility periods
    if features.get('volatility', 0) > {threshold}:
        logger.info(f"Skipping {{symbol}} - volatility {{features['volatility']:.2%}} > {threshold:.2%}")
        return None  # Skip this trade
"""
                code_additions.append(code)
        
        return '\n'.join(code_additions)
    
    def apply_improvements(self, dry_run: bool = False) -> bool:
        """Apply validated improvements to strategy"""
        
        cprint("\n" + "="*70, "magenta")
        cprint("🚀 STRATEGY AUTO-UPDATE", "magenta", attrs=['bold'])
        cprint("="*70 + "\n", "magenta")
        
        # Load validated improvements
        validated_record = self.load_validated_improvements()
        
        if not validated_record:
            cprint("No validated improvements ready for deployment", "yellow")
            return False
        
        improvements = validated_record.get('validated_improvements', [])
        validated_imps = [imp for imp in improvements if imp.get('validated')]
        
        if not validated_imps:
            cprint("No validated improvements found", "yellow")
            return False
        
        cprint(f"📋 Found {len(validated_imps)} validated improvements:", "cyan")
        for i, imp in enumerate(validated_imps, 1):
            cprint(f"  {i}. {imp['improvement']['description']}", "white")
            cprint(f"     Confidence: {imp['confidence']:.1%}", "green")
        
        # Generate improvement code
        cprint("\n🔧 Generating improvement code...", "cyan")
        improvement_code = self.generate_improvement_code(validated_imps)
        
        if not improvement_code.strip():
            cprint("⚠️  No code generated from improvements", "yellow")
            return False
        
        cprint("\n📝 Generated Code:", "cyan")
        print(improvement_code)
        
        if dry_run:
            cprint("\n🧪 DRY RUN - No changes applied", "yellow")
            return True
        
        # Backup current strategy
        backup_file = self.backup_strategy()
        
        # Read current strategy
        if not self.strategy_file.exists():
            cprint(f"❌ Strategy file not found: {self.strategy_file}", "red")
            return False
        
        with open(self.strategy_file, 'r') as f:
            strategy_content = f.read()
        
        # Find insertion point (before return statement in trade logic)
        # This is a simplified approach - in production you'd parse AST
        insertion_marker = "# AUTO-IMPROVEMENT FILTERS"
        
        if insertion_marker in strategy_content:
            # Replace existing auto-improvements
            parts = strategy_content.split(insertion_marker)
            if len(parts) >= 2:
                # Find end of previous auto-improvements (next function or class)
                end_marker_idx = parts[1].find('\ndef ')
                if end_marker_idx == -1:
                    end_marker_idx = parts[1].find('\nclass ')
                
                if end_marker_idx != -1:
                    new_content = (
                        parts[0] + 
                        insertion_marker + 
                        improvement_code + 
                        '\n' +
                        parts[1][end_marker_idx:]
                    )
                else:
                    new_content = parts[0] + insertion_marker + improvement_code
            else:
                new_content = strategy_content + '\n' + insertion_marker + improvement_code
        else:
            # Add marker and improvements at end of file
            new_content = strategy_content + '\n\n' + insertion_marker + improvement_code
        
        # Write updated strategy
        with open(self.strategy_file, 'w') as f:
            f.write(new_content)
        
        cprint(f"\n✅ Strategy updated: {self.strategy_file}", "green")
        
        # Git commit
        self._git_commit(validated_imps)
        
        # Log deployment
        self._log_deployment(validated_record, backup_file)
        
        cprint("\n🎉 Strategy improvements deployed!", "green", attrs=['bold'])
        
        return True
    
    def _git_commit(self, improvements: List[Dict]):
        """Create git commit for versioning"""
        
        try:
            # Create commit message
            commit_msg = f"[AUTO] Strategy improvements - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
            for imp in improvements:
                commit_msg += f"- {imp['improvement']['description']}\n"
            
            # Git add
            subprocess.run(['git', 'add', str(self.strategy_file)], check=True)
            
            # Git commit
            subprocess.run(['git', 'commit', '-m', commit_msg], check=True)
            
            cprint("✅ Git commit created", "green")
            
        except subprocess.CalledProcessError as e:
            cprint(f"⚠️  Git commit failed: {e}", "yellow")
        except FileNotFoundError:
            cprint("⚠️  Git not available - skipping version control", "yellow")
    
    def _log_deployment(self, validated_record: Dict, backup_file: str):
        """Log deployment for audit trail"""
        
        deployment = {
            'timestamp': datetime.now().isoformat(),
            'improvements_applied': validated_record.get('validated_improvements'),
            'backup_file': backup_file,
            'original_analysis': validated_record.get('original_analysis'),
            'status': 'deployed'
        }
        
        # Load existing
        if self.deployment_log.exists():
            with open(self.deployment_log, 'r') as f:
                deployments = json.load(f)
        else:
            deployments = []
        
        deployments.append(deployment)
        
        # Save
        with open(self.deployment_log, 'w') as f:
            json.dump(deployments, f, indent=2)
        
        cprint(f"📝 Deployment logged to: {self.deployment_log}", "cyan")
    
    def rollback_last_deployment(self) -> bool:
        """Rollback to previous version if something goes wrong"""
        
        if not self.deployment_log.exists():
            cprint("No deployments to rollback", "yellow")
            return False
        
        with open(self.deployment_log, 'r') as f:
            deployments = json.load(f)
        
        if not deployments:
            cprint("No deployments found", "yellow")
            return False
        
        last_deployment = deployments[-1]
        backup_file = last_deployment.get('backup_file')
        
        if not backup_file or not Path(backup_file).exists():
            cprint(f"Backup file not found: {backup_file}", "red")
            return False
        
        # Restore backup
        shutil.copy2(backup_file, self.strategy_file)
        
        cprint(f"✅ Strategy rolled back to: {backup_file}", "green")
        
        # Mark as rolled back
        last_deployment['status'] = 'rolled_back'
        last_deployment['rollback_time'] = datetime.now().isoformat()
        
        with open(self.deployment_log, 'w') as f:
            json.dump(deployments, f, indent=2)
        
        return True


def main():
    """Test Strategy Updater"""
    
    updater = StrategyUpdater()
    
    cprint("\n🧪 Testing Strategy Updater (DRY RUN)", "yellow")
    
    # Dry run
    success = updater.apply_improvements(dry_run=True)
    
    if success:
        cprint("\n✅ Dry run successful", "green")
        cprint("\nTo apply for real, run: updater.apply_improvements(dry_run=False)", "cyan")
    else:
        cprint("\n⚠️  No improvements to apply", "yellow")


if __name__ == "__main__":
    main()
