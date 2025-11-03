"""
🔍 Moon Dev's Agent Update Checker
Built with love by Moon Dev 🚀

Checks which agents need to be updated to use OpenRouter pattern.
"""

import os
import re
from pathlib import Path

# Simple colored output
def cprint(text, color=None):
    """Simple colored print"""
    colors = {
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'cyan': '\033[96m',
        'end': '\033[0m'
    }
    color_code = colors.get(color, '')
    end_code = colors['end'] if color else ''
    print(f"{color_code}{text}{end_code}")


def check_agent(file_path):
    """Check if agent uses old pattern or new pattern"""
    with open(file_path) as f:
        content = f.read()

    agent_name = file_path.name

    # Check for old patterns
    has_anthropic_import = 'import anthropic' in content or 'from anthropic' in content
    has_openai_import = 'import openai' in content and 'OpenAI(' in content
    has_old_client = 'anthropic.Anthropic(' in content or 'openai.OpenAI(' in content

    # Check for new patterns
    has_model_helper = 'from src.agents.model_helper' in content
    has_model_factory = 'from src.models.model_factory' in content or 'model_factory.get_model' in content
    has_get_model = 'get_agent_model(' in content or 'get_model_for_task(' in content

    # Determine status
    if has_model_helper or has_get_model:
        return 'updated', agent_name, '✅ Uses new OpenRouter pattern'
    elif has_model_factory and not has_old_client:
        return 'compatible', agent_name, '⚡ Uses ModelFactory (compatible, can optimize)'
    elif has_anthropic_import or has_openai_import or has_old_client:
        return 'needs_update', agent_name, '❌ Uses old direct API pattern'
    else:
        return 'no_llm', agent_name, 'ℹ️ No LLM usage detected'


def main():
    """Check all agents"""
    cprint("\n🔍 Moon Dev's Agent Update Status Check\n", "cyan")
    cprint("="*70, "cyan")

    agents_dir = Path(__file__).parent.parent / 'src' / 'agents'

    # Find all agent files
    agent_files = sorted(agents_dir.glob('*_agent.py'))

    if not agent_files:
        cprint("❌ No agent files found!", "red")
        return

    # Categorize agents
    updated = []
    compatible = []
    needs_update = []
    no_llm = []

    for agent_file in agent_files:
        status, name, message = check_agent(agent_file)

        if status == 'updated':
            updated.append((name, message))
        elif status == 'compatible':
            compatible.append((name, message))
        elif status == 'needs_update':
            needs_update.append((name, message))
        else:
            no_llm.append((name, message))

    # Print results
    cprint(f"\n✅ UPDATED TO OPENROUTER ({len(updated)} agents):", "green")
    for name, msg in updated:
        cprint(f"  {msg} - {name}", "green")

    cprint(f"\n⚡ COMPATIBLE WITH OPENROUTER ({len(compatible)} agents):", "yellow")
    cprint("   (Already use ModelFactory, can be optimized with helper functions)", "yellow")
    for name, msg in compatible:
        cprint(f"  {msg} - {name}", "yellow")

    cprint(f"\n❌ NEEDS UPDATE ({len(needs_update)} agents):", "red")
    cprint("   (Use old direct API clients - should be updated)", "red")
    for name, msg in needs_update:
        cprint(f"  {msg} - {name}", "red")

    if no_llm:
        cprint(f"\nℹ️ NO LLM USAGE ({len(no_llm)} agents):", "cyan")
        for name, msg in no_llm:
            cprint(f"  {msg} - {name}", "cyan")

    # Summary
    cprint("\n" + "="*70, "cyan")
    cprint("\n📊 SUMMARY:", "cyan")
    cprint(f"  Total agents: {len(agent_files)}", "cyan")
    cprint(f"  ✅ Fully updated: {len(updated)}", "green")
    cprint(f"  ⚡ Compatible (can optimize): {len(compatible)}", "yellow")
    cprint(f"  ❌ Needs update: {len(needs_update)}", "red")
    cprint(f"  ℹ️ No LLM: {len(no_llm)}\n", "cyan")

    # Recommendations
    if needs_update:
        cprint("💡 RECOMMENDATIONS:", "cyan")
        cprint("  1. Start with high-priority agents: risk_agent, trading_agent, sentiment_agent", "cyan")
        cprint("  2. See AGENT_UPDATE_GUIDE.md for step-by-step instructions", "cyan")
        cprint("  3. Use src/agents/risk_agent.py as reference for updated pattern", "cyan")
        cprint("  4. Test each agent after updating: python src/agents/<agent_name>.py\n", "cyan")

    if compatible:
        cprint("💡 OPTIMIZATION TIP:", "cyan")
        cprint("  Compatible agents can be optimized with task-specific helpers:", "cyan")
        cprint("  - get_trading_model() for trading decisions", "cyan")
        cprint("  - get_risk_model() for risk management", "cyan")
        cprint("  - get_research_model() for strategy development", "cyan")
        cprint("  - get_chat_model() for cheap/fast tasks\n", "cyan")

    cprint("📚 Resources:", "cyan")
    cprint("  - AGENT_UPDATE_GUIDE.md - Complete update instructions", "cyan")
    cprint("  - src/agents/model_helper.py - Helper functions", "cyan")
    cprint("  - src/agents/risk_agent.py - Reference updated agent\n", "cyan")


if __name__ == "__main__":
    main()
