"""
Test Swarm functionality directly with OpenRouter API
Bypasses model_factory to avoid dependency issues
"""

import os
from openai import OpenAI
import time
from concurrent.futures import ThreadPoolExecutor
from termcolor import cprint
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# OpenRouter configuration - load from environment
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')

if not OPENROUTER_API_KEY:
    cprint("❌ ERROR: OPENROUTER_API_KEY not found in environment!", "red")
    cprint("Please set OPENROUTER_API_KEY in your .env file", "yellow")
    cprint("Get your key at: https://openrouter.ai/keys", "cyan")
    exit(1)

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
    default_headers={
        "HTTP-Referer": "https://github.com/moon-dev-ai-agents",
        "X-Title": "Moon Dev AI Trading Swarm",
    }
)

# Models to query - Using official upstream model IDs from moondevonyt/moon-dev-ai-agents
SWARM_MODELS = [
    ("google/gemini-2.5-flash", "Gemini 2.5 Flash"),
    ("qwen/qwen3-max", "Qwen 3 Max"),
    ("moonshot/kimi-k2", "Kimi K2"),
    ("anthropic/claude-sonnet-4.5", "Claude 4.5 Sonnet"),
    ("openai/gpt-5-mini", "GPT-5 Mini"),
    ("deepseek/deepseek-r1-0528", "DeepSeek R1"),
]

# Complex query
COMPLEX_QUERY = """
COMPLEX TRADING STRATEGY ANALYSIS REQUEST:

We have discovered through systematic backtesting that a 5x leverage strategy achieves 66.38% annual return:

Strategy Parameters:
- Timeframe: 1H BTC-USD
- Fast EMA: 20, Slow EMA: 100
- Entry: EMA crossover + RSI > 70 + Volume > 2x average
- Exit: Death cross
- Position Size: 5x leverage
- Stop Loss: 1% (5% effective with leverage)
- Take Profit: 6% (30% effective with leverage)

Backtest Results (BTC 1H, 2023 bull market):
- Return: 66.38%
- Max Drawdown: -6.47%
- Sharpe Ratio: 2.51
- Win Rate: 45.16%
- Trades: 31
- Buy & Hold Return: 122.12%

CRITICAL QUESTIONS:

1. Is -6.47% max drawdown with 5x leverage realistic or overfitting?
2. Will this fail in sideways/bear markets? (tested only on bull market)
3. Liquidation risks during flash crashes?
4. RSI>70 filter: too conservative or appropriately selective?
5. Real-world differences from backtest (slippage, delays, etc.)?

Provide HONEST, CRITICAL analysis. Identify weaknesses and suggest improvements.
Keep response under 300 words.
"""

def query_model(model_id, model_name):
    """Query a single model"""
    start_time = time.time()

    try:
        response = client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "system", "content": "You are an expert quantitative trader providing honest, critical analysis."},
                {"role": "user", "content": COMPLEX_QUERY}
            ],
            temperature=0.7,
            max_tokens=500,
        )

        elapsed = time.time() - start_time
        content = response.choices[0].message.content

        return {
            'model': model_name,
            'model_id': model_id,
            'response': content,
            'success': True,
            'time': round(elapsed, 2),
            'error': None
        }

    except Exception as e:
        elapsed = time.time() - start_time
        error_msg = str(e)

        # Extract detailed error from OpenRouter if available
        if hasattr(e, 'response'):
            try:
                error_details = e.response.json()
                if 'error' in error_details:
                    error_msg = f"{error_details['error'].get('message', error_msg)} (code: {error_details['error'].get('code', 'unknown')})"
            except:
                pass

        return {
            'model': model_name,
            'model_id': model_id,
            'response': None,
            'success': False,
            'time': round(elapsed, 2),
            'error': error_msg
        }

def main():
    print("=" * 90)
    print("🌙 SWARM AGENT - DIRECT OPENROUTER TEST")
    print("=" * 90)

    print(f"\n📝 Query: Complex trading strategy analysis")
    print(f"🤖 Testing {len(SWARM_MODELS)} models in parallel\n")

    # Query all models in parallel
    print("🚀 Querying models...\n")

    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {
            executor.submit(query_model, model_id, name): (model_id, name)
            for model_id, name in SWARM_MODELS
        }

        results = []
        for future in futures:
            result = future.result()
            results.append(result)

            if result['success']:
                cprint(f"✅ {result['model']}: {result['time']}s", "green")
            else:
                cprint(f"❌ {result['model']}: {result['error'][:50]}", "red")

    # Display results
    print(f"\n{'='*90}")
    print("📊 INDIVIDUAL RESPONSES")
    print(f"{'='*90}\n")

    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]

    print(f"Success Rate: {len(successful)}/{len(results)} ({len(successful)/len(results)*100:.0f}%)\n")

    for i, result in enumerate(successful, 1):
        print(f"\n{'='*90}")
        print(f"AI #{i}: {result['model']} (⏱️  {result['time']}s)")
        print(f"{'='*90}\n")
        print(result['response'][:800])
        if len(result['response']) > 800:
            print(f"\n... (truncated - full: {len(result['response'])} chars)")

    if failed:
        print(f"\n\n{'='*90}")
        print("❌ FAILED MODELS")
        print(f"{'='*90}\n")
        for result in failed:
            print(f"• {result['model']}: {result['error']}")

    # Simple consensus (if we have responses)
    if successful:
        print(f"\n\n{'='*90}")
        print("🎯 KEY THEMES ACROSS RESPONSES")
        print(f"{'='*90}\n")

        # Count common warnings
        all_text = " ".join([r['response'].lower() for r in successful])

        warnings = {
            'Overfitting': 'overfit' in all_text,
            'Bull market bias': 'bull' in all_text or 'bear' in all_text,
            'Liquidation risk': 'liquidat' in all_text,
            'Slippage concerns': 'slippage' in all_text,
            'High leverage risk': 'leverage' in all_text and 'risk' in all_text,
        }

        print("Common concerns mentioned:")
        for warning, found in warnings.items():
            status = "✅" if found else "  "
            print(f"{status} {warning}")

        print(f"\n💡 {len([w for w in warnings.values() if w])}/{len(warnings)} key risk factors mentioned across responses")

    print(f"\n{'='*90}\n")

if __name__ == "__main__":
    main()
