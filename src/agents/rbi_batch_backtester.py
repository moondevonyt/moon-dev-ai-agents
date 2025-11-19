"""
🌙 Moon Dev's RBI Batch Backtester (GPT-5 Edition)

- Scans a research folder of strategy writeups
- Generates backtesting.py code for each strategy using your RBI prompts (no changes to RBI agent)
- Saves code to a `GPT-5` subfolder under the research folder
- Executes each backtest in conda env `tflow`, printing full stats to terminal
- On errors, automatically runs package-fix and debug passes until success (or attempts exhausted)
- Saves run outputs (stdout/stderr/metadata) as JSON and plain text next to the code

Keep files under 800 lines. No moving files, only creating new ones. 🚀
"""

from __future__ import annotations

import os
from pathlib import Path
from datetime import datetime
import json

# Import prompts and helpers from RBI agent (do not modify RBI agent)
from src.agents import rbi_agent
from src.agents.backtest_runner import run_backtest_in_conda, save_results


# ==== CONFIG ====
# Target research folder (can be overridden via CLI argument)
from pathlib import Path as PathLib
PROJECT_ROOT = PathLib(__file__).parent.parent.parent
DEFAULT_RESEARCH_DIR = PROJECT_ROOT / "src" / "data" / "rbi" / "03_14_2025" / "research"

# Output subfolder name under the research directory
OUTPUT_SUBDIR_NAME = "GPT-5"

# Conda environment to use for execution
CONDA_ENV_NAME = "tflow"

# Max attempts: initial -> package-fix -> debug (loop)
MAX_DEBUG_ATTEMPTS = 3


def ensure_output_dir(research_dir: Path) -> Path:
    output_dir = research_dir / OUTPUT_SUBDIR_NAME
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"📂🌙 MOON DEV: Output directory ready at: {output_dir} ✨")
    return output_dir


def read_strategy(file_path: Path) -> str:
    with open(file_path, "r") as f:
        content = f.read()
    print(f"📝🌙 MOON DEV: Loaded strategy text from {file_path.name} ({len(content)} chars) 📚")
    return content


def derive_strategy_name(file_path: Path, content: str) -> str:
    # Prefer STRATEGY_NAME: inside the file; else fallback to filename stem before _strategy
    name = None
    marker = "STRATEGY_NAME:"
    if marker in content:
        try:
            after = content.split(marker, 1)[1].strip()
            line = after.splitlines()[0].strip()
            name = line
        except Exception:
            name = None
    if not name:
        stem = file_path.stem  # e.g., BandSqueezeTrend_strategy
        if stem.endswith("_strategy"):
            stem = stem[: -len("_strategy")]
        name = stem
    # Sanitize for filesystem
    import re as _re
    name = _re.sub(r"[^\w\s-]", "", name)
    name = _re.sub(r"[\s]+", "", name)
    print(f"🏷️🌙 MOON DEV: Strategy name resolved: {name}")
    return name


def generate_backtest_code(strategy_text: str) -> str:
    print("🤖🌙 MOON DEV: Generating backtest code via BACKTEST prompt... 🚀")
    content = f"Create a backtest for this strategy:\n\n{strategy_text}"

    # Try primary config, then fallbacks if unavailable
    candidate_configs = [
        rbi_agent.BACKTEST_CONFIG,
        {"type": "openai", "name": "o1-mini"},
        {"type": "openai", "name": "gpt-4o"},
        {"type": "claude", "name": "claude-3-haiku"},
        {"type": "deepseek", "name": "deepseek-chat"},
        {"type": "ollama", "name": "llama3.2"},
        {"type": "ollama", "name": "deepseek-r1"},
    ]

    raw = None
    last_error = None
    for cfg in candidate_configs:
        print(f"🛰️🌙 MOON DEV: Attempting model {cfg['type']} :: {cfg['name']} for codegen ✨")
        try:
            raw = rbi_agent.chat_with_model(
                rbi_agent.BACKTEST_PROMPT,
                content,
                cfg,
            )
            if raw:
                break
        except Exception as e:
            last_error = str(e)
            print(f"⚠️🌙 MOON DEV: Model attempt failed: {last_error}")

    if not raw:
        msg = "Backtest generation returned empty response from all model candidates"
        if last_error:
            msg += f" | last error: {last_error}"
        raise RuntimeError(msg)

    code = rbi_agent.clean_model_output(raw, "code")
    print("✅🌙 MOON DEV: Initial backtest code generated (cleaned from markdown) ✨")
    return code


def package_fix_code(code: str) -> str:
    print("📦🌙 MOON DEV: Running package-check to remove forbidden backtesting.lib usage... 🧹")
    content = f"Check and fix indicator packages in this code:\n\n{code}"

    candidate_configs = [
        rbi_agent.PACKAGE_CONFIG,
        {"type": "openai", "name": "o1-mini"},
        {"type": "openai", "name": "gpt-4o"},
        {"type": "claude", "name": "claude-3-haiku"},
        {"type": "deepseek", "name": "deepseek-chat"},
        {"type": "ollama", "name": "llama3.2"},
        {"type": "ollama", "name": "deepseek-r1"},
    ]

    raw = None
    for cfg in candidate_configs:
        print(f"🛰️🌙 MOON DEV: Package-fix model attempt {cfg['type']} :: {cfg['name']}")
        try:
            raw = rbi_agent.chat_with_model(
                rbi_agent.PACKAGE_PROMPT,
                content,
                cfg,
            )
            if raw:
                break
        except Exception:
            pass

    if not raw:
        return code
    fixed = rbi_agent.clean_model_output(raw, "code")
    print("✅🌙 MOON DEV: Package-check completed ✨")
    return fixed or code


def debug_fix_code(code: str, strategy_text: str | None = None) -> str:
    print("🔧🌙 MOON DEV: Running debug pass to fix technical issues... 🐛")
    context = f"Here's the backtest code to debug:\n\n{code}"
    if strategy_text:
        context += f"\n\nOriginal strategy for reference:\n{strategy_text}"
    
    candidate_configs = [
        rbi_agent.DEBUG_CONFIG,
        {"type": "openai", "name": "o1-mini"},
        {"type": "openai", "name": "gpt-4o"},
        {"type": "claude", "name": "claude-3-haiku"},
        {"type": "deepseek", "name": "deepseek-chat"},
        {"type": "ollama", "name": "deepseek-r1"},
        {"type": "ollama", "name": "llama3.2"},
    ]

    raw = None
    for cfg in candidate_configs:
        print(f"🛰️🌙 MOON DEV: Debug model attempt {cfg['type']} :: {cfg['name']}")
        try:
            raw = rbi_agent.chat_with_model(
                rbi_agent.DEBUG_PROMPT,
                context,
                cfg,
            )
            if raw:
                break
        except Exception:
            pass

    if not raw:
        return code
    fixed = rbi_agent.clean_model_output(raw, "code")
    print("✅🌙 MOON DEV: Debug pass produced updated code ✨")
    return fixed or code


def write_code(output_dir: Path, strategy_name: str, code: str) -> Path:
    out_file = output_dir / f"{strategy_name}_BT.py"
    with open(out_file, "w") as f:
        f.write(code)
    print(f"💾🌙 MOON DEV: Saved backtest code to {out_file}")
    return out_file


def save_text_outputs(output_dir: Path, strategy_name: str, stdout: str, stderr: str) -> None:
    stdout_file = output_dir / f"{strategy_name}_stdout.txt"
    stderr_file = output_dir / f"{strategy_name}_stderr.txt"
    with open(stdout_file, "w") as f:
        f.write(stdout or "")
    with open(stderr_file, "w") as f:
        f.write(stderr or "")
    print(f"💾🌙 MOON DEV: Saved stdout/stderr to {stdout_file.name} / {stderr_file.name}")


def run_one_strategy(research_dir: Path, file_path: Path, conda_env: str) -> None:
    print("\n" + "=" * 80)
    print(f"🌙 MOON DEV RUN: Processing {file_path.name} 📜")
    print("=" * 80)

    output_dir = ensure_output_dir(research_dir)
    strategy_text = read_strategy(file_path)
    strategy_name = derive_strategy_name(file_path, strategy_text)

    # 1) Generate backtest
    code = generate_backtest_code(strategy_text)

    # 2) Package fix before first run (to ensure no backtesting.lib)
    code = package_fix_code(code)

    # 3) Write and execute
    code_path = write_code(output_dir, strategy_name, code)

    attempt = 0
    result = run_backtest_in_conda(str(code_path), conda_env)

    while (not result.get("success")) and attempt < MAX_DEBUG_ATTEMPTS:
        attempt += 1
        print(f"❌🌙 MOON DEV: Run failed. Attempting auto-fix #{attempt} 🔁")
        # Try debug fix
        code = debug_fix_code(code, strategy_text)
        # Package fix again (ensure compliance after debug)
        code = package_fix_code(code)
        code_path = write_code(output_dir, strategy_name, code)
        result = run_backtest_in_conda(str(code_path), conda_env)

    # 4) Finalize outputs
    print("\n📊🌙 MOON DEV: EXECUTION RESULTS (raw)")
    print(json.dumps({k: v for k, v in result.items() if k != "stdout" and k != "stderr"}, indent=2))

    # Always print stdout (the stats) to terminal per requirement
    stdout = result.get("stdout", "")
    stderr = result.get("stderr", "")
    if stdout:
        print("\n📈🌙 MOON DEV: STANDARD OUTPUT (stats)")
        print("-" * 60)
        print(stdout)
        print("-" * 60)
    if stderr:
        print("\n⚠️🌙 MOON DEV: ERRORS/WARNINGS")
        print("-" * 60)
        print(stderr)
        print("-" * 60)

    # Save JSON results next to code
    results_file = save_results(result, str(code_path))
    save_text_outputs(output_dir, strategy_name, stdout, stderr)

    if result.get("success"):
        print("✅🌙 MOON DEV: Backtest completed successfully! To the moon! 🚀")
    else:
        print("💥🌙 MOON DEV: Backtest still failing after auto-fixes. Needs manual review.")


def main():
    import sys

    # Resolve research directory
    research_dir = DEFAULT_RESEARCH_DIR
    only_file: Path | None = None

    # Simple CLI parsing: optional [research_dir] and/or --file /path/to/file.txt
    args = list(sys.argv[1:])
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--file" and i + 1 < len(args):
            only_file = Path(args[i + 1]).expanduser().resolve()
            i += 2
        else:
            candidate = Path(arg).expanduser().resolve()
            if candidate.exists() and candidate.is_dir():
                research_dir = candidate
            i += 1
    print(f"\n🌙 MOON DEV: Batch Backtester starting for research dir: {research_dir}")

    # Collect strategy files
    txt_files = sorted([p for p in research_dir.glob("*.txt") if p.is_file()])
    if only_file is not None:
        if not only_file.exists():
            print(f"❌🌙 MOON DEV: --file not found: {only_file}")
            return
        if only_file.is_file():
            txt_files = [only_file]
        else:
            print(f"❌🌙 MOON DEV: --file must be a file: {only_file}")
            return
    print(f"🔎🌙 MOON DEV: Found {len(txt_files)} strategies to process ✍️")

    for idx, file_path in enumerate(txt_files, start=1):
        print(f"\n➡️🌙 MOON DEV: [{idx}/{len(txt_files)}] {file_path.name}")
        run_one_strategy(research_dir, file_path, CONDA_ENV_NAME)

    print("\n🎉🌙 MOON DEV: Batch run complete. Check the GPT-5 folder for code and outputs. ✨🚀")


if __name__ == "__main__":
    main()


