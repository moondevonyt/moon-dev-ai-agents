"""
🌙 Moon Dev - Agent Health Check System
Tests all major agents for proper configuration and dependencies

Categorizes agents into:
- Core Trading Agents
- Market Analysis Agents
- Content Creation Agents
- Strategy Development Agents
- Supporting Agents
"""

import os
import sys
import importlib
import traceback
from datetime import datetime

# Test categories
AGENT_CATEGORIES = {
    "Core Trading": [
        "trading_agent",
        "risk_agent",
        "strategy_agent",
        "copybot_agent",
    ],

    "Market Analysis": [
        "sentiment_agent",
        "whale_agent",
        "funding_agent",
        "liquidation_agent",
        "chartanalysis_agent",
        "coingecko_agent",
    ],

    "Content Creation": [
        "chat_agent",
        "clips_agent",
        "tweet_agent",
        "phone_agent",
        "tiktok_agent",
        "shortvid_agent",
    ],

    "Strategy Development": [
        "rbi_agent",
        "research_agent",
        "backtest_runner",
        "swarm_agent",
    ],

    "Specialized": [
        "sniper_agent",
        "solana_agent",
        "tx_agent",
        "million_agent",
        "polymarket_agent",
        "housecoin_agent",
        "websearch_agent",
    ],

    "Arbitrage": [
        "fundingarb_agent",
        "listingarb_agent",
    ],
}

def test_agent_import(agent_name):
    """Test if agent can be imported without errors"""
    try:
        # Suppress import warnings and errors
        import warnings
        warnings.filterwarnings('ignore')

        module = importlib.import_module(f"src.agents.{agent_name}")
        return {
            'success': True,
            'module': module,
            'error': None
        }
    except ModuleNotFoundError as e:
        return {
            'success': False,
            'module': None,
            'error': f"Missing dependency: {str(e)[:100]}",
            'error_type': 'dependency'
        }
    except ImportError as e:
        return {
            'success': False,
            'module': None,
            'error': f"Import error: {str(e)[:100]}",
            'error_type': 'import'
        }
    except Exception as e:
        return {
            'success': False,
            'module': None,
            'error': str(e)[:100],
            'error_type': 'other'
        }

def check_agent_config(agent_name, module):
    """Check agent configuration requirements"""
    issues = []

    # Check for common config patterns
    config_vars = [
        'AI_MODEL', 'AI_PROVIDER', 'OPENROUTER_API_KEY',
        'ANTHROPIC_KEY', 'OPENAI_KEY', 'DEEPSEEK_KEY'
    ]

    found_configs = []
    for var in config_vars:
        if hasattr(module, var):
            found_configs.append(var)

    # Check for main execution function
    has_main = hasattr(module, 'main') or hasattr(module, 'run')

    return {
        'configs_found': found_configs,
        'has_main': has_main,
        'issues': issues
    }

def test_agent_standalone(agent_name):
    """Test if agent can run standalone (dry run)"""
    agent_path = f"src/agents/{agent_name}.py"

    if not os.path.exists(agent_path):
        return {'runnable': False, 'reason': 'File not found'}

    # Read file to check for if __name__ == '__main__'
    with open(agent_path, 'r') as f:
        content = f.read()

    has_main_guard = 'if __name__ == "__main__"' in content or 'if __name__ == \'__main__\'' in content

    return {
        'runnable': has_main_guard,
        'reason': 'Has main guard' if has_main_guard else 'No main guard found'
    }

def main():
    print("=" * 90)
    print("🌙 MOON DEV - AGENT HEALTH CHECK SYSTEM")
    print("=" * 90)
    print(f"\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Testing {sum(len(agents) for agents in AGENT_CATEGORIES.values())} agents across {len(AGENT_CATEGORIES)} categories\n")

    all_results = {}
    total_tested = 0
    total_passed = 0
    total_failed = 0

    for category, agents in AGENT_CATEGORIES.items():
        print(f"\n{'='*90}")
        print(f"📂 {category} Agents ({len(agents)})")
        print(f"{'='*90}\n")

        category_results = []

        for agent_name in agents:
            total_tested += 1

            print(f"🔍 Testing: {agent_name}")

            # Test import
            import_result = test_agent_import(agent_name)

            if import_result['success']:
                # Test configuration
                config_result = check_agent_config(agent_name, import_result['module'])

                # Test standalone
                standalone_result = test_agent_standalone(agent_name)

                result = {
                    'name': agent_name,
                    'import_success': True,
                    'configs': config_result['configs_found'],
                    'has_main': config_result['has_main'],
                    'runnable': standalone_result['runnable'],
                    'status': 'PASS'
                }

                print(f"   ✅ Import: SUCCESS")
                print(f"   📋 Configs: {len(config_result['configs_found'])} found")
                print(f"   🎯 Main function: {'Yes' if config_result['has_main'] else 'No'}")
                print(f"   🚀 Standalone: {'Yes' if standalone_result['runnable'] else 'No'}")

                total_passed += 1

            else:
                result = {
                    'name': agent_name,
                    'import_success': False,
                    'error': import_result['error'],
                    'error_type': import_result.get('error_type', 'unknown'),
                    'status': 'FAIL'
                }

                error_icon = "📦" if import_result.get('error_type') == 'dependency' else "❌"
                print(f"   {error_icon} Import: FAILED")
                print(f"   Error: {import_result['error']}")

                total_failed += 1

            category_results.append(result)
            print()

        all_results[category] = category_results

    # Summary
    print(f"\n{'='*90}")
    print("📊 HEALTH CHECK SUMMARY")
    print(f"{'='*90}\n")

    print(f"Total agents tested: {total_tested}")
    print(f"✅ Passed: {total_passed} ({(total_passed/total_tested)*100:.1f}%)")
    print(f"❌ Failed: {total_failed} ({(total_failed/total_tested)*100:.1f}%)")

    # Category breakdown
    print(f"\n{'='*90}")
    print("CATEGORY BREAKDOWN")
    print(f"{'='*90}\n")

    for category, results in all_results.items():
        passed = sum(1 for r in results if r['status'] == 'PASS')
        failed = sum(1 for r in results if r['status'] == 'FAIL')

        status_icon = "✅" if failed == 0 else "⚠️" if failed < len(results)/2 else "❌"

        print(f"{status_icon} {category}: {passed}/{len(results)} passed")

    # Failed agents detail
    if total_failed > 0:
        print(f"\n{'='*90}")
        print("FAILED AGENTS DETAIL")
        print(f"{'='*90}\n")

        for category, results in all_results.items():
            failed_agents = [r for r in results if r['status'] == 'FAIL']

            if failed_agents:
                print(f"\n{category}:")
                for agent in failed_agents:
                    print(f"  ❌ {agent['name']}")
                    print(f"     Error: {agent['error'][:150]}")

    # Configuration summary
    print(f"\n{'='*90}")
    print("CONFIGURATION SUMMARY")
    print(f"{'='*90}\n")

    all_configs = set()
    for category, results in all_results.items():
        for result in results:
            if result['status'] == 'PASS' and 'configs' in result:
                all_configs.update(result['configs'])

    print(f"Configuration variables found across agents:")
    for config in sorted(all_configs):
        count = sum(1 for cat_results in all_results.values()
                   for r in cat_results
                   if r['status'] == 'PASS' and 'configs' in r and config in r['configs'])
        print(f"  - {config}: {count} agents")

    # Standalone runnable
    print(f"\n{'='*90}")
    print("STANDALONE EXECUTION")
    print(f"{'='*90}\n")

    runnable_count = sum(1 for cat_results in all_results.values()
                        for r in cat_results
                        if r['status'] == 'PASS' and r.get('runnable'))

    print(f"Agents with standalone execution: {runnable_count}/{total_passed}")

    print(f"\n{'='*90}\n")

    return all_results

if __name__ == "__main__":
    results = main()
