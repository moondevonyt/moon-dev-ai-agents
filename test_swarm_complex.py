"""
Test Swarm Agent with complex trading strategy analysis
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Setup path
project_root = str(Path(__file__).parent)
if project_root not in sys.path:
    sys.path.append(project_root)

# Check OpenRouter API key is available
if not os.getenv('OPENROUTER_API_KEY'):
    print("❌ ERROR: OPENROUTER_API_KEY not found in .env file!")
    print("Please add your OpenRouter API key to .env")
    exit(1)

from src.agents.swarm_agent import SwarmAgent

# Complex trading scenario
complex_query = """
COMPLEX TRADING STRATEGY ANALYSIS REQUEST:

We have discovered through systematic backtesting that a 5x leverage strategy achieves 66.38% annual return:

Strategy Parameters:
- Timeframe: 1H BTC-USD
- Fast EMA: 20
- Slow EMA: 100
- Entry: EMA crossover + RSI > 70 + Volume > 2x average
- Exit: Death cross (slow EMA crosses above fast EMA)
- Position Size: 5x leverage
- Stop Loss: 1% (5% effective with leverage)
- Take Profit: 6% (30% effective with leverage)

Backtest Results (BTC 1H, 2023 data):
- Return: 66.38%
- Max Drawdown: -6.47%
- Sharpe Ratio: 2.51
- Win Rate: 45.16%
- Number of Trades: 31
- Average Trade: 1.74%
- Buy & Hold Return: 122.12%

QUESTIONS FOR ANALYSIS:

1. RISK ASSESSMENT: Is -6.47% max drawdown with 5x leverage realistic or are we overfitting?

2. MARKET REGIME: This was tested on 2023 bull market data (B&H = 122%). Will this strategy fail in:
   - Sideways markets (low volatility)
   - Bear markets (downtrends)
   - High volatility crashes

3. LEVERAGE SUSTAINABILITY: 5x leverage with 1% stops means margin requirements are tight. What are the realistic risks of:
   - Liquidation during flash crashes
   - Funding rate costs eating into profits
   - Slippage on actual exchanges

4. STRATEGY ROBUSTNESS: The RSI>70 filter is very selective (only strong momentum). Is this:
   - Too conservative (missing opportunities)?
   - Appropriately selective (quality over quantity)?
   - Vulnerable to false breakouts?

5. IMPLEMENTATION REALITY: In live trading, what will differ from backtest?
   - Order execution delays
   - Slippage on entries/exits
   - Exchange downtime during volatile moves
   - Psychological pressure of 5x leverage

6. ALTERNATIVE APPROACHES: Should we consider:
   - Lower leverage (2-3x) for more safety?
   - Multiple uncorrelated strategies instead of single high-leverage?
   - Dynamic position sizing based on volatility?

7. PORTFOLIO CONTEXT: If this is 20% of portfolio, what should the other 80% be doing?

Please provide a COMPREHENSIVE, HONEST analysis. We want to know the REAL risks, not just confirmation bias.
Be critical, identify weaknesses, and suggest improvements.
"""

def main():
    print("=" * 90)
    print("🧪 TESTING SWARM AGENT WITH COMPLEX TRADING ANALYSIS")
    print("=" * 90)

    print("\n📝 Query:")
    print("-" * 90)
    print(complex_query[:500] + "...")
    print(f"\n(Full query: {len(complex_query)} characters)")

    try:
        # Initialize swarm
        print("\n🚀 Initializing Swarm Agent...")
        swarm = SwarmAgent()

        # Query all models
        print("\n🤖 Querying 6 AI models in parallel...")
        print("This may take 30-60 seconds...\n")

        result = swarm.query(
            prompt=complex_query,
            system_prompt="You are an expert quantitative trader and risk analyst. Provide brutally honest, critical analysis."
        )

        # Display results
        print("\n" + "=" * 90)
        print("📊 SWARM RESULTS")
        print("=" * 90)

        # Individual responses
        print(f"\n✅ Successfully received {len([r for r in result['responses'].values() if r['success']])} / {len(result['responses'])} responses\n")

        for i, (provider, data) in enumerate(result['responses'].items(), 1):
            print(f"\n{'='*90}")
            print(f"AI #{i}: {provider} ({data.get('model', 'Unknown')})")
            print(f"{'='*90}")

            if data['success']:
                print(f"⏱️  Response Time: {data['response_time']}s")
                print(f"\n{data['response'][:1000]}")
                if len(data['response']) > 1000:
                    print(f"\n... (truncated, full response: {len(data['response'])} chars)")
            else:
                print(f"❌ Error: {data['error']}")

        # Consensus
        if result.get('consensus_summary'):
            print(f"\n\n{'='*90}")
            print("🎯 CONSENSUS SUMMARY (Synthesized by Gemini 2.5 Flash)")
            print(f"{'='*90}\n")
            print(result['consensus_summary'])

        # Model mapping
        print(f"\n\n{'='*90}")
        print("🗺️  MODEL MAPPING")
        print(f"{'='*90}\n")
        for ai_num, model_name in result['model_mapping'].items():
            print(f"{ai_num}: {model_name}")

        # Save location
        if 'saved_to' in result:
            print(f"\n💾 Full results saved to: {result['saved_to']}")

        print(f"\n{'='*90}\n")

        return result

    except Exception as e:
        print(f"\n❌ Error running swarm agent: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = main()
