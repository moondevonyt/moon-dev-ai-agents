#!/usr/bin/env python3
"""
🌙 Moon Dev's Codebase Aggregator Script 🌙

This script safely aggregates all Python (.py) files from the project into a single text file.

⚠️ SECURITY FEATURES:
- EXCLUDES all .env files
- EXCLUDES all files in .gitignore
- EXCLUDES sensitive directories (venv, __pycache__, node_modules, etc.)
- EXCLUDES API keys, private keys, and credentials
- ONLY includes .py files
- NO environment variables or secrets will be included

Output: Creates a single text file with all Python code for AI analysis

Built with security in mind by Moon Dev 🚀
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from termcolor import colored, cprint
import fnmatch

# ============================================
# 🎯 CONFIGURATION - EDIT THIS SECTION 🎯
# ============================================

# Leave empty ("") to scan entire project, OR specify a folder path to scan only that folder
# Examples:
#   SPECIFIC_FOLDER = "src/agents"  # Scan only agents folder
#   SPECIFIC_FOLDER = "src/strategies"  # Scan only strategies folder
#   SPECIFIC_FOLDER = ""  # Scan entire project (default)

SPECIFIC_FOLDER = "src/agents"  # 👈 Currently set to scan only agents folder

# ============================================
# END CONFIGURATION
# ============================================

# Project root (go up from scripts to main directory)
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Determine scan path based on configuration
if SPECIFIC_FOLDER:
    SCAN_PATH = PROJECT_ROOT / SPECIFIC_FOLDER
    if not SCAN_PATH.exists():
        print(f"❌ Error: Specified folder does not exist: {SCAN_PATH}")
        sys.exit(1)
    OUTPUT_SUFFIX = f"{SPECIFIC_FOLDER.replace('/', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
else:
    SCAN_PATH = PROJECT_ROOT
    OUTPUT_SUFFIX = f"full_project_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# Output configuration
OUTPUT_DIR = PROJECT_ROOT / "src" / "data" / "codebase_export"
OUTPUT_FILE = OUTPUT_DIR / f"aggregated_codebase_{OUTPUT_SUFFIX}.txt"

# ============ SECURITY: EXCLUDED PATTERNS ============
# These patterns will NEVER be included, regardless of .gitignore
ALWAYS_EXCLUDE = [
    # Environment and secrets
    '.env',
    '.env.*',
    '*.env',
    'env/',
    'venv/',
    '.venv/',
    '*.key',
    '*.pem',
    '*.cert',
    'secrets.py',
    'credentials.py',
    'private_*',
    '*_private.py',

    # API keys and sensitive data
    'api_keys.py',
    'config_private.py',
    'keys/',
    'passwords*',
    'tokens*',

    # System and cache
    '__pycache__/',
    '*.pyc',
    '*.pyo',
    '.git/',
    '.DS_Store',
    'Thumbs.db',

    # Virtual environments
    'env/',
    'venv/',
    '.venv/',
    'ENV/',
    'env.bak/',
    'venv.bak/',

    # IDE and editor files
    '.vscode/',
    '.idea/',
    '*.swp',
    '*.swo',
    '*~',

    # Data and logs that might contain sensitive info
    '*.log',
    '*.csv',
    '*.json',
    '*.db',
    '*.sqlite',

    # Notebooks might contain output with sensitive data
    '*.ipynb',

    # Compiled files
    'dist/',
    'build/',
    '*.egg-info/',

    # Test coverage
    '.coverage',
    'htmlcov/',
    '.pytest_cache/',
    '.tox/',

    # Node modules (if any)
    'node_modules/',

    # The output directory itself
    'codebase_export/',
    'aggregated_codebase_*.txt'
]

class CodebaseAggregator:
    def __init__(self):
        """Initialize the aggregator"""
        self.files_processed = 0
        self.files_skipped = 0
        self.total_lines = 0
        self.gitignore_patterns = []

        # Create output directory
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        # Load .gitignore patterns
        self.load_gitignore()

        cprint("\n" + "="*60, "cyan")
        cprint("🌙 Moon Dev's Codebase Aggregator 🌙", "cyan", attrs=['bold'])
        cprint("="*60, "cyan")

        # Show what we're scanning
        if SPECIFIC_FOLDER:
            cprint(f"\n📁 Scanning specific folder: {SPECIFIC_FOLDER}", "yellow", attrs=['bold'])
            cprint(f"   Full path: {SCAN_PATH}", "yellow")
        else:
            cprint(f"\n📁 Scanning entire project", "green", attrs=['bold'])
            cprint(f"   Project root: {PROJECT_ROOT}", "green")

        cprint("\n⚠️  SECURITY NOTICE:", "yellow", attrs=['bold'])
        cprint("✅ WILL include: Only .py Python files", "green")
        cprint("❌ WILL NOT include:", "red")
        cprint("   - .env files or environment variables", "red")
        cprint("   - API keys or credentials", "red")
        cprint("   - Files in .gitignore", "red")
        cprint("   - Virtual environments", "red")
        cprint("   - Cache or compiled files", "red")
        cprint("   - Any sensitive data files\n", "red")

    def load_gitignore(self):
        """Load patterns from .gitignore"""
        gitignore_path = PROJECT_ROOT / '.gitignore'
        if gitignore_path.exists():
            with open(gitignore_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        self.gitignore_patterns.append(line)
            cprint(f"📋 Loaded {len(self.gitignore_patterns)} patterns from .gitignore", "green")

    def should_exclude(self, file_path: Path) -> tuple[bool, str]:
        """
        Check if a file should be excluded
        Returns: (should_exclude, reason)
        """
        # Convert to relative path for pattern matching
        try:
            rel_path = file_path.relative_to(PROJECT_ROOT)
            rel_path_str = str(rel_path)
        except ValueError:
            # File is outside project root
            return True, "Outside project root"

        # Check against ALWAYS_EXCLUDE patterns
        for pattern in ALWAYS_EXCLUDE:
            if fnmatch.fnmatch(rel_path_str, pattern):
                return True, f"Matched security exclusion: {pattern}"
            if fnmatch.fnmatch(file_path.name, pattern):
                return True, f"Matched security exclusion: {pattern}"
            # Check if any part of the path matches
            for part in rel_path.parts:
                if fnmatch.fnmatch(part, pattern):
                    return True, f"Path contains excluded pattern: {pattern}"

        # Check against .gitignore patterns
        for pattern in self.gitignore_patterns:
            if fnmatch.fnmatch(rel_path_str, pattern):
                return True, f"In .gitignore: {pattern}"
            if fnmatch.fnmatch(file_path.name, pattern):
                return True, f"In .gitignore: {pattern}"

        # Extra safety: Check for common sensitive patterns in filename
        sensitive_keywords = ['key', 'secret', 'credential', 'password', 'token', 'private', 'env']
        filename_lower = file_path.name.lower()
        for keyword in sensitive_keywords:
            if keyword in filename_lower:
                return True, f"Filename contains sensitive keyword: {keyword}"

        # Only include .py files
        if not file_path.suffix == '.py':
            return True, "Not a Python file"

        return False, ""

    def aggregate_code(self):
        """Main method to aggregate all Python files"""
        cprint("\n🔍 Scanning for Python files...\n", "cyan")

        all_code_sections = []

        # Walk through all directories (starting from SCAN_PATH)
        for root, dirs, files in os.walk(SCAN_PATH):
            # Skip hidden directories and common exclusions
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in
                      ['venv', 'env', '__pycache__', 'node_modules', 'dist', 'build']]

            for file in files:
                file_path = Path(root) / file

                # Check if file should be excluded
                should_exclude, reason = self.should_exclude(file_path)

                if should_exclude:
                    if file_path.suffix == '.py':
                        # Only log skipped Python files
                        cprint(f"⏭️  Skipping: {file_path.relative_to(PROJECT_ROOT)}", "yellow")
                        cprint(f"   Reason: {reason}", "yellow")
                        self.files_skipped += 1
                    continue

                # Process the Python file
                try:
                    rel_path = file_path.relative_to(PROJECT_ROOT)
                    cprint(f"✅ Including: {rel_path}", "green")

                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        lines = content.count('\n') + 1
                        self.total_lines += lines

                    # Add to aggregated content with clear separation
                    section = f"""
{'='*80}
FILE: {rel_path}
LINES: {lines}
{'='*80}

{content}

"""
                    all_code_sections.append(section)
                    self.files_processed += 1

                except Exception as e:
                    cprint(f"❌ Error reading {file_path}: {e}", "red")

        # Write aggregated content to file
        if all_code_sections:
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                # Write header
                scan_info = f"Specific Folder: {SPECIFIC_FOLDER}" if SPECIFIC_FOLDER else "Full Project"
                f.write(f"""
🌙 MOON DEV'S AGGREGATED CODEBASE 🌙
=====================================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Scan Type: {scan_info}
Scan Path: {SCAN_PATH}
Total Files: {self.files_processed}
Total Lines: {self.total_lines:,}
Project Root: {PROJECT_ROOT}

⚠️ SECURITY NOTICE:
This file contains ONLY Python source code (.py files).
All sensitive files, environment variables, and credentials have been excluded.

Files are separated by clear markers for easy navigation.
=====================================

""")

                # Write all code sections
                f.writelines(all_code_sections)

                # Write footer
                f.write(f"""
=====================================
END OF AGGREGATED CODEBASE
Files Included: {self.files_processed}
Files Skipped: {self.files_skipped}
Total Lines: {self.total_lines:,}
Generated by Moon Dev's Codebase Aggregator 🌙
=====================================
""")

            # Print summary
            cprint("\n" + "="*60, "green")
            cprint("✨ AGGREGATION COMPLETE! ✨", "green", attrs=['bold'])
            cprint("="*60, "green")

            # Show what was scanned
            if SPECIFIC_FOLDER:
                cprint(f"\n📁 Scanned folder: {SPECIFIC_FOLDER}", "cyan", attrs=['bold'])
            else:
                cprint(f"\n📁 Scanned: Entire project", "cyan", attrs=['bold'])

            cprint(f"\n📊 Summary:", "cyan", attrs=['bold'])
            cprint(f"   Files included: {self.files_processed}", "green")
            cprint(f"   Files skipped: {self.files_skipped}", "yellow")
            cprint(f"   Total lines of code: {self.total_lines:,}", "blue")
            cprint(f"\n📁 Output saved to:", "cyan", attrs=['bold'])
            cprint(f"   {OUTPUT_FILE.relative_to(PROJECT_ROOT)}", "green")
            cprint(f"\n📏 File size: {os.path.getsize(OUTPUT_FILE) / 1024 / 1024:.2f} MB", "blue")

            cprint("\n🔒 Security Check:", "yellow", attrs=['bold'])
            cprint("   ✅ No .env files included", "green")
            cprint("   ✅ No API keys or credentials included", "green")
            cprint("   ✅ No files from .gitignore included", "green")
            cprint("   ✅ Safe to share with other AIs", "green")

            cprint("\n🚀 You can now share this file with other AIs for code analysis!", "cyan", attrs=['bold'])

        else:
            cprint("\n❌ No Python files found to aggregate!", "red")

def main():
    """Main entry point"""
    try:
        aggregator = CodebaseAggregator()
        aggregator.aggregate_code()

    except Exception as e:
        cprint(f"\n❌ Fatal error: {e}", "red", attrs=['bold'])
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())