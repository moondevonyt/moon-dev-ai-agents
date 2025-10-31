"""
🌙 Moon Dev - Quick Agent Check
Fast syntax and configuration check without executing agent code
"""

import os
import ast
from datetime import datetime

# Agent categories
AGENT_CATEGORIES = {
    "Core Trading": [
        "trading_agent", "risk_agent", "strategy_agent", "copybot_agent",
    ],
    "Market Analysis": [
        "sentiment_agent", "whale_agent", "funding_agent", "liquidation_agent",
        "chartanalysis_agent", "coingecko_agent",
    ],
    "Content Creation": [
        "chat_agent", "clips_agent", "tweet_agent", "phone_agent",
        "tiktok_agent", "shortvid_agent",
    ],
    "Strategy Development": [
        "rbi_agent", "research_agent", "backtest_runner", "swarm_agent",
    ],
    "Specialized": [
        "sniper_agent", "solana_agent", "tx_agent", "million_agent",
        "polymarket_agent", "housecoin_agent", "websearch_agent",
    ],
    "Arbitrage": [
        "fundingarb_agent", "listingarb_agent",
    ],
}

def check_file_syntax(filepath):
    """Check if file has valid Python syntax"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            code = f.read()
        ast.parse(code)
        return {'valid': True, 'error': None}
    except SyntaxError as e:
        return {'valid': False, 'error': f"Syntax error line {e.lineno}: {e.msg}"}
    except Exception as e:
        return {'valid': False, 'error': str(e)}

def analyze_agent_file(agent_name):
    """Analyze agent file for key features"""
    filepath = f"src/agents/{agent_name}.py"

    if not os.path.exists(filepath):
        return {
            'exists': False,
            'error': 'File not found'
        }

    # Check syntax
    syntax_check = check_file_syntax(filepath)

    if not syntax_check['valid']:
        return {
            'exists': True,
            'syntax_valid': False,
            'error': syntax_check['error']
        }

    # Read file content
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check features
    features = {
        'has_main_guard': 'if __name__ == "__main__"' in content or "if __name__ == '__main__'" in content,
        'has_docstring': '"""' in content[:500] or "'''" in content[:500],
        'uses_model_factory': 'ModelFactory' in content or 'model_factory' in content,
        'uses_openrouter': 'openrouter' in content.lower() or 'OPENROUTER' in content,
        'has_api_key_check': 'API_KEY' in content or 'api_key' in content,
        'lines_of_code': len(content.splitlines()),
        'imports_nice_funcs': 'nice_funcs' in content,
        'uses_termcolor': 'termcolor' in content or 'cprint' in content,
    }

    return {
        'exists': True,
        'syntax_valid': True,
        **features
    }

def main():
    print("=" * 90)
    print("🌙 MOON DEV - QUICK AGENT CHECK")
    print("=" * 90)
    print(f"\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    total_agents = sum(len(agents) for agents in AGENT_CATEGORIES.values())
    print(f"Checking {total_agents} agents across {len(AGENT_CATEGORIES)} categories\n")

    all_results = {}
    total_valid = 0
    total_invalid = 0
    total_missing = 0

    for category, agents in AGENT_CATEGORIES.items():
        print(f"\n{'='*90}")
        print(f"📂 {category} ({len(agents)} agents)")
        print(f"{'='*90}\n")

        category_results = []

        for agent_name in agents:
            result = analyze_agent_file(agent_name)
            result['name'] = agent_name

            if not result['exists']:
                print(f"❌ {agent_name:<25} - File not found")
                total_missing += 1
                result['status'] = 'MISSING'

            elif not result['syntax_valid']:
                print(f"⚠️  {agent_name:<25} - Syntax error")
                print(f"   Error: {result['error']}")
                total_invalid += 1
                result['status'] = 'INVALID'

            else:
                # Valid file
                features = []
                if result['has_main_guard']:
                    features.append("Standalone")
                if result['uses_openrouter']:
                    features.append("OpenRouter")
                if result['uses_model_factory']:
                    features.append("ModelFactory")

                feature_str = ", ".join(features) if features else "Basic"
                lines = result['lines_of_code']

                print(f"✅ {agent_name:<25} - {lines:>4} lines | {feature_str}")
                total_valid += 1
                result['status'] = 'VALID'

            category_results.append(result)

        all_results[category] = category_results

    # Summary
    print(f"\n{'='*90}")
    print("📊 SUMMARY")
    print(f"{'='*90}\n")

    print(f"Total agents: {total_agents}")
    print(f"✅ Valid: {total_valid} ({(total_valid/total_agents)*100:.1f}%)")
    print(f"⚠️  Invalid syntax: {total_invalid}")
    print(f"❌ Missing: {total_missing}")

    # Category breakdown
    print(f"\n{'='*90}")
    print("CATEGORY HEALTH")
    print(f"{'='*90}\n")

    for category, results in all_results.items():
        valid = sum(1 for r in results if r['status'] == 'VALID')
        total = len(results)

        if valid == total:
            status = "✅ Perfect"
        elif valid >= total * 0.75:
            status = "🟢 Good"
        elif valid >= total * 0.5:
            status = "🟡 Fair"
        else:
            status = "🔴 Poor"

        print(f"{status:12} {category:25} {valid}/{total}")

    # Feature analysis
    print(f"\n{'='*90}")
    print("FEATURE ADOPTION")
    print(f"{'='*90}\n")

    valid_agents = [r for cat_results in all_results.values()
                   for r in cat_results if r['status'] == 'VALID']

    if valid_agents:
        features_count = {
            'Standalone execution (main guard)': sum(1 for r in valid_agents if r['has_main_guard']),
            'OpenRouter integration': sum(1 for r in valid_agents if r['uses_openrouter']),
            'ModelFactory pattern': sum(1 for r in valid_agents if r['uses_model_factory']),
            'Docstring present': sum(1 for r in valid_agents if r['has_docstring']),
            'API key checking': sum(1 for r in valid_agents if r['has_api_key_check']),
            'Nice funcs import': sum(1 for r in valid_agents if r['imports_nice_funcs']),
            'Colored output (termcolor)': sum(1 for r in valid_agents if r['uses_termcolor']),
        }

        for feature, count in features_count.items():
            pct = (count / len(valid_agents)) * 100
            bar = "█" * int(pct / 5)
            print(f"{feature:<35} {count:>2}/{len(valid_agents):<2} {bar} {pct:>5.1f}%")

    # Code size analysis
    print(f"\n{'='*90}")
    print("CODE SIZE DISTRIBUTION")
    print(f"{'='*90}\n")

    if valid_agents:
        sizes = [r['lines_of_code'] for r in valid_agents]
        avg_size = sum(sizes) / len(sizes)
        max_size = max(sizes)
        min_size = min(sizes)

        print(f"Average: {avg_size:.0f} lines")
        print(f"Range: {min_size} - {max_size} lines")

        # Find largest agents
        largest = sorted(valid_agents, key=lambda x: x['lines_of_code'], reverse=True)[:5]
        print(f"\nLargest agents:")
        for i, agent in enumerate(largest, 1):
            print(f"  {i}. {agent['name']}: {agent['lines_of_code']} lines")

    print(f"\n{'='*90}\n")

if __name__ == "__main__":
    main()
