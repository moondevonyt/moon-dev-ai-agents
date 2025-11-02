"""
🔒 Moon Dev's Security Check Script
Built with love by Moon Dev 🚀

Checks for common security issues before production deployment.
"""

import os
import subprocess
import sys
from pathlib import Path

# Simple colored output without termcolor dependency
def cprint(text, color=None, attrs=None):
    """Simple colored print without termcolor dependency"""
    colors = {
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'cyan': '\033[96m',
        'end': '\033[0m'
    }
    color_code = colors.get(color, '')
    end_code = colors['end'] if color else ''
    bold = '\033[1m' if attrs and 'bold' in attrs else ''
    print(f"{bold}{color_code}{text}{end_code}")

class SecurityChecker:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.issues_found = []
        self.warnings = []

    def check_env_file(self):
        """Check if .env exists and is properly configured"""
        cprint("\n🔍 Checking .env file...", "cyan")

        env_file = self.project_root / '.env'
        env_example = self.project_root / '.env_example'

        if not env_file.exists():
            self.issues_found.append("❌ .env file not found! Copy .env_example to .env")
            return

        cprint("✅ .env file exists", "green")

        # Check if .env has minimum required keys
        required_keys = ['OPENROUTER_API_KEY']
        with open(env_file) as f:
            content = f.read()

        for key in required_keys:
            if key not in content:
                self.warnings.append(f"⚠️ {key} not found in .env")
            elif f"{key}=your_" in content or f"{key}=" in content.split(key)[1].split('\n')[0].strip() == "":
                self.warnings.append(f"⚠️ {key} appears to be a placeholder, not set")
            else:
                cprint(f"  ✅ {key} is set", "green")

    def check_gitignore(self):
        """Verify .env is in .gitignore"""
        cprint("\n🔍 Checking .gitignore...", "cyan")

        gitignore_file = self.project_root / '.gitignore'

        if not gitignore_file.exists():
            self.issues_found.append("❌ .gitignore not found!")
            return

        with open(gitignore_file) as f:
            content = f.read()

        if '.env' in content and '!.env_example' in content:
            cprint("✅ .env is properly ignored", "green")
        else:
            self.issues_found.append("❌ .env not properly configured in .gitignore")

    def check_git_history(self):
        """Check if .env was ever committed to git"""
        cprint("\n🔍 Checking git history for exposed secrets...", "cyan")

        try:
            # Check if .env is tracked by git
            result = subprocess.run(
                ['git', 'ls-files', '.env'],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )

            if result.stdout.strip():
                self.issues_found.append("❌ CRITICAL: .env is tracked by git! Run: git rm --cached .env")
                return

            cprint("✅ .env is not tracked by git", "green")

            # Check git history for .env
            result = subprocess.run(
                ['git', 'log', '--all', '--full-history', '--', '.env'],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )

            if result.stdout.strip():
                self.issues_found.append("❌ CRITICAL: .env found in git history! Keys may be exposed!")
                cprint("   Run: git filter-branch --force --index-filter 'git rm --cached --ignore-unmatch .env' --prune-empty --tag-name-filter cat -- --all", "yellow")
            else:
                cprint("✅ .env not found in git history", "green")

        except Exception as e:
            self.warnings.append(f"⚠️ Could not check git: {str(e)}")

    def check_hardcoded_keys(self):
        """Scan for hardcoded API keys in Python files"""
        cprint("\n🔍 Scanning for hardcoded API keys...", "cyan")

        src_dir = self.project_root / 'src'
        patterns = [
            'sk-',  # OpenAI/OpenRouter keys
            'api_key.*=.*["\'][^"\']{20,}',  # Generic API keys
            'API_KEY.*=.*["\'][^"\']{20,}',
            'secret.*=.*["\'][^"\']{20,}',
            'password.*=.*["\'][^"\']{10,}',
        ]

        issues = []
        for py_file in src_dir.rglob('*.py'):
            with open(py_file) as f:
                content = f.read()

            # Skip if it's using os.getenv
            if 'os.getenv' in content or 'os.environ' in content:
                continue

            for pattern in patterns:
                if pattern in content.lower():
                    # Make sure it's not a comment or example
                    if 'your_' not in content and 'example' not in content.lower():
                        issues.append(f"⚠️ Possible hardcoded key in {py_file}")

        if issues:
            self.warnings.extend(issues)
            cprint("⚠️ Found possible hardcoded keys (review manually)", "yellow")
        else:
            cprint("✅ No obvious hardcoded keys found", "green")

    def check_openrouter_config(self):
        """Check if OpenRouter is properly configured"""
        cprint("\n🔍 Checking OpenRouter configuration...", "cyan")

        config_file = self.project_root / 'src' / 'config.py'

        with open(config_file) as f:
            content = f.read()

        if 'AI_PROVIDER' in content:
            if 'AI_PROVIDER = "openrouter"' in content:
                cprint("✅ OpenRouter is set as default provider", "green")
            else:
                self.warnings.append("⚠️ OpenRouter not set as default provider in config.py")
        else:
            self.warnings.append("⚠️ AI_PROVIDER not found in config.py")

    def check_model_factory(self):
        """Check if OpenRouter model exists"""
        cprint("\n🔍 Checking Model Factory...", "cyan")

        model_file = self.project_root / 'src' / 'models' / 'openrouter_model.py'

        if model_file.exists():
            cprint("✅ OpenRouter model implementation exists", "green")
        else:
            self.issues_found.append("❌ OpenRouter model implementation not found!")

        # Check if it's imported in model_factory
        factory_file = self.project_root / 'src' / 'models' / 'model_factory.py'
        with open(factory_file) as f:
            content = f.read()

        if 'OpenRouterModel' in content:
            cprint("✅ OpenRouter model is imported in ModelFactory", "green")
        else:
            self.issues_found.append("❌ OpenRouter model not imported in ModelFactory")

    def check_file_permissions(self):
        """Check file permissions on sensitive files"""
        cprint("\n🔍 Checking file permissions...", "cyan")

        env_file = self.project_root / '.env'

        if env_file.exists():
            # On Unix systems, check if .env is readable by others
            if os.name != 'nt':  # Not Windows
                mode = oct(os.stat(env_file).st_mode)[-3:]
                if mode != '600':
                    self.warnings.append(f"⚠️ .env has permissions {mode}, should be 600 (run: chmod 600 .env)")
                else:
                    cprint("✅ .env has secure permissions (600)", "green")

    def print_summary(self):
        """Print summary of security check"""
        cprint("\n" + "="*60, "cyan")
        cprint("🔒 SECURITY CHECK SUMMARY", "cyan", attrs=['bold'])
        cprint("="*60, "cyan")

        if not self.issues_found and not self.warnings:
            cprint("\n🎉 ALL CHECKS PASSED! System is production-ready!", "green", attrs=['bold'])
            return True

        if self.issues_found:
            cprint(f"\n❌ CRITICAL ISSUES FOUND ({len(self.issues_found)}):", "red", attrs=['bold'])
            for issue in self.issues_found:
                cprint(f"  {issue}", "red")

        if self.warnings:
            cprint(f"\n⚠️ WARNINGS ({len(self.warnings)}):", "yellow", attrs=['bold'])
            for warning in self.warnings:
                cprint(f"  {warning}", "yellow")

        if self.issues_found:
            cprint("\n❌ FIX CRITICAL ISSUES BEFORE PRODUCTION!", "red", attrs=['bold'])
            return False
        else:
            cprint("\n⚠️ Review warnings, but system can go to production", "yellow", attrs=['bold'])
            return True

def main():
    """Run security checks"""
    cprint("\n🌙 Moon Dev's Security Check", "cyan", attrs=['bold'])
    cprint("Checking for common security issues...\n", "cyan")

    checker = SecurityChecker()

    # Run all checks
    checker.check_env_file()
    checker.check_gitignore()
    checker.check_git_history()
    checker.check_hardcoded_keys()
    checker.check_openrouter_config()
    checker.check_model_factory()
    checker.check_file_permissions()

    # Print summary
    success = checker.print_summary()

    cprint("\n💡 TIP: See PRODUCTION_SETUP.md for full deployment guide", "cyan")

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
