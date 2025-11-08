"""
🌙 Moon Dev's RBI AI v2.0 (Simplified - Direct DeepSeek)
"""

import subprocess
import json
import os
import time
import re
from datetime import datetime
from pathlib import Path
from termcolor import cprint
import threading
import itertools
import sys
from dotenv import load_dotenv
from openai import OpenAI
from anthropic import Anthropic

# Load environment variables
load_dotenv()

# Configuration
CONDA_ENV = "tflow"
MAX_DEBUG_ITERATIONS = 3
EXECUTION_TIMEOUT = 300
AI_TEMPERATURE = 0.7
AI_MAX_TOKENS = 4000

# DeepSeek client
deepseek_client = OpenAI(
    api_key=os.getenv("DEEPSEEK_KEY"),
    base_url="https://api.deepseek.com"
)

# Claude client
claude_client = Anthropic(
    api_key=os.getenv("ANTHROPIC_KEY")
)

# Get today's date
TODAY_DATE = datetime.now().strftime("%m_%d_%Y")

# Directory setup
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data/rbi_v2"
TODAY_DIR = DATA_DIR / TODAY_DATE
RESEARCH_DIR = TODAY_DIR / "research"
BACKTEST_DIR = TODAY_DIR / "backtests"
PACKAGE_DIR = TODAY_DIR / "backtests_package"
FINAL_BACKTEST_DIR = TODAY_DIR / "backtests_final"
EXECUTION_DIR = TODAY_DIR / "execution_results"
IDEAS_FILE = DATA_DIR / "ideas.txt"

# Create directories
for dir in [DATA_DIR, TODAY_DIR, RESEARCH_DIR, BACKTEST_DIR, PACKAGE_DIR, 
            FINAL_BACKTEST_DIR, EXECUTION_DIR]:
    dir.mkdir(parents=True, exist_ok=True)

# Prompts (same as before)
RESEARCH_PROMPT = """
You are Moon Dev's Research AI 🌙

IMPORTANT NAMING RULES:
1. Create a UNIQUE TWO-WORD NAME for this specific strategy
2. The name must be DIFFERENT from any generic names like "TrendFollower" or "MomentumStrategy"
3. First word should describe the main approach (e.g., Adaptive, Neural, Quantum, Fractal, Dynamic)
4. Second word should describe the specific technique (e.g., Reversal, Breakout, Oscillator, Divergence)
5. Make the name SPECIFIC to this strategy's unique aspects

Output format must start with:
STRATEGY_NAME: [Your unique two-word name]

Then analyze the trading strategy content and create detailed instructions.
Focus on:
1. Key strategy components
2. Entry/exit rules
3. Risk management
4. Required indicators

Your complete output must follow this format:
STRATEGY_NAME: [Your unique two-word name]

STRATEGY_DETAILS:
[Your detailed analysis]

Remember: The name must be UNIQUE and SPECIFIC to this strategy's approach!
"""

BACKTEST_PROMPT = """
You are Moon Dev's Backtest AI 🌙 ONLY SEND BACK CODE, NO OTHER TEXT.
Create a backtesting.py implementation for the strategy.
USE BACKTESTING.PY
Include:
1. All necessary imports
2. Strategy class with indicators
3. Entry/exit logic
4. Risk management
5. your size should be 1,000,000
6. If you need indicators use TA lib or pandas TA.

Use this data path: /moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv

FOR THE PYTHON BACKTESTING LIBRARY USE BACKTESTING.PY AND SEND BACK ONLY THE CODE, NO OTHER TEXT.
ONLY SEND BACK CODE, NO OTHER TEXT.
"""

def chat_with_deepseek(system_prompt, user_content, model_name="deepseek-chat"):
    """Direct DeepSeek API call"""
    response = deepseek_client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        temperature=AI_TEMPERATURE,
        max_tokens=AI_MAX_TOKENS
    )
    return response.choices[0].message.content

def chat_with_claude(system_prompt, user_content, model_name="claude-3-opus-20240229"):
    """Direct Claude API call"""
    response = claude_client.messages.create(
        model=model_name,
        max_tokens=AI_MAX_TOKENS,
        temperature=AI_TEMPERATURE,
        system=system_prompt,
        messages=[
            {"role": "user", "content": user_content}
        ]
    )
    return response.content[0].text

def animate_progress(agent_name, stop_event):
    """Fun animation while AI is thinking"""
    spinners = ['🌑', '🌒', '🌓', '🌔', '🌕', '🌖', '🌗', '🌘']
    messages = ["brewing coffee ☕️", "studying charts 📊", "making magic ✨"]
    
    spinner = itertools.cycle(spinners)
    message = itertools.cycle(messages)
    
    while not stop_event.is_set():
        sys.stdout.write(f'\r{next(spinner)} {agent_name} is {next(message)}...')
        sys.stdout.flush()
        time.sleep(0.5)
    sys.stdout.write('\r' + ' ' * 50 + '\r')
    sys.stdout.flush()

def run_with_animation(func, agent_name, *args, **kwargs):
    """Run a function with animation"""
    stop_animation = threading.Event()
    animation_thread = threading.Thread(target=animate_progress, args=(agent_name, stop_animation))
    
    animation_thread.start()
    result = func(*args, **kwargs)
    stop_animation.set()
    animation_thread.join()
    return result

def clean_model_output(output, content_type="text"):
    """Clean model output"""
    cleaned_output = output
    
    # Remove thinking tags
    if "<think>" in output and "</think>" in output:
        clean_content = output.split("</think>")[-1].strip()
        if clean_content:
            cleaned_output = clean_content
    
    # Extract code from markdown
    if content_type == "code" and "```" in cleaned_output:
        import re
        code_blocks = re.findall(r'```python\n(.*?)\n```', cleaned_output, re.DOTALL)
        if not code_blocks:
            code_blocks = re.findall(r'```(?:python)?\n(.*?)\n```', cleaned_output, re.DOTALL)
        if code_blocks:
            cleaned_output = "\n\n".join(code_blocks)
    
    return cleaned_output

def research_strategy(content):
    """Research AI: Analyzes and creates trading strategy"""
    cprint("\n🔍 Starting Research AI...", "cyan")
    
    output = run_with_animation(
        chat_with_deepseek,
        "Research AI",
        RESEARCH_PROMPT, 
        content,
        "deepseek-chat"
    )
    
    output = clean_model_output(output, "text")
    
    # Extract strategy name
    strategy_name = "UnknownStrategy"
    if "STRATEGY_NAME:" in output:
        name_section = output.split("STRATEGY_NAME:")[1].strip()
        if "\n\n" in name_section:
            strategy_name = name_section.split("\n\n")[0].strip()
        else:
            strategy_name = name_section.split("\n")[0].strip()
        strategy_name = re.sub(r'[^\w\s-]', '', strategy_name)
        strategy_name = re.sub(r'[\s]+', '', strategy_name)
    
    # Save research output
    filepath = RESEARCH_DIR / f"{strategy_name}_strategy.txt"
    with open(filepath, 'w') as f:
        f.write(output)
    cprint(f"📝 Research saved to {filepath}", "green")
    return output, strategy_name

def create_backtest(strategy, strategy_name="UnknownStrategy"):
    """Backtest AI: Creates backtest implementation using Claude Opus"""
    cprint("\n📊 Starting Backtest AI (Claude Opus)...", "cyan")
    
    output = run_with_animation(
        chat_with_claude,
        "Backtest AI",
        BACKTEST_PROMPT,
        f"Create a backtest for this strategy:\n\n{strategy}",
        "claude-3-opus-20240229"  # Use Claude Opus for complex coding
    )
    
    output = clean_model_output(output, "code")
    
    filepath = BACKTEST_DIR / f"{strategy_name}_BT.py"
    with open(filepath, 'w') as f:
        f.write(output)
    cprint(f"🔥 Backtest saved to {filepath}", "green")
    return output

def execute_backtest(file_path: str, strategy_name: str) -> dict:
    """Execute backtest in conda environment"""
    cprint(f"\n🚀 Executing backtest: {strategy_name}", "cyan")
    
    cmd = ["conda", "run", "-n", CONDA_ENV, "python", str(file_path)]
    
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=EXECUTION_TIMEOUT
    )
    
    output = {
        "success": result.returncode == 0,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "execution_time": 0,
        "timestamp": datetime.now().isoformat()
    }
    
    # Save execution results
    result_file = EXECUTION_DIR / f"{strategy_name}_{datetime.now().strftime('%H%M%S')}.json"
    with open(result_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    if output['success']:
        cprint("✅ Backtest executed successfully!", "green")
        if output['stdout']:
            print("\n📊 RESULTS:")
            print(output['stdout'][:1000] + "..." if len(output['stdout']) > 1000 else output['stdout'])
    else:
        cprint("❌ Backtest failed!", "red")
        if output['stderr']:
            print("\n🐛 ERRORS:")
            print(output['stderr'])
    
    return output

def main():
    """Main function"""
    cprint(f"\n🌟 Moon Dev's RBI AI v2.0 (Simplified) Starting Up!", "green")
    cprint(f"📅 Today's Date: {TODAY_DATE}", "magenta")
    cprint(f"🔄 EXECUTION LOOP ENABLED!", "yellow")
    
    # Test with first idea from file
    if not IDEAS_FILE.exists():
        cprint("❌ ideas.txt not found!", "red")
        return
    
    with open(IDEAS_FILE, 'r') as f:
        ideas = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    if not ideas:
        cprint("❌ No ideas found!", "red")
        return
    
    # Process first idea as test
    idea = ideas[0]
    cprint(f"\n🎯 Testing with first idea:", "cyan")
    cprint(f"📝 {idea[:100]}...", "yellow")
    
    # Phase 1: Research
    strategy, strategy_name = research_strategy(idea)
    cprint(f"🏷️ Strategy Name: {strategy_name}", "yellow")
    
    # Phase 2: Backtest
    backtest_code = create_backtest(strategy, strategy_name)
    
    # Phase 3: Execute
    backtest_file = BACKTEST_DIR / f"{strategy_name}_BT.py"
    execution_result = execute_backtest(backtest_file, strategy_name)
    
    if execution_result['success']:
        cprint("\n🎉 SUCCESS! Full pipeline working!", "green")
    else:
        cprint("\n⚠️ Execution failed - need to add debug loop", "yellow")
    
    cprint("\n✨ Simplified test complete!", "green")

if __name__ == "__main__":
    main()