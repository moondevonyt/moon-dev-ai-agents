"""
🌙 Moon Dev - LLM Trading Competition (Simplified via OpenRouter)
Alle modellen via OpenRouter - geen complexe dependencies!

Target: >60% return met acceptabele drawdown
"""

import json
import time
import pandas as pd
import numpy as np
from backtesting import Backtest, Strategy
import os
from openai import OpenAI

# OpenRouter configuration
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '')

if not OPENROUTER_API_KEY:
    print("❌ ERROR: OPENROUTER_API_KEY not found in environment!")
    print("Add it to .env file: OPENROUTER_API_KEY=your_key_here")
    exit(1)

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# LLM Models to test
COMPETING_LLMS = [
    ("google/gemini-2.5-flash", "Gemini 2.5 Flash"),
    ("moonshot/kimi-k2", "Kimi K2"),
    ("anthropic/claude-haiku-4.5", "Claude Haiku 4.5"),
    ("deepseek/deepseek-r1-0528", "DeepSeek R1"),
    ("openai/gpt-5-mini", "GPT-5 Mini"),
    ("qwen/qwen3-max", "Qwen 3 Max"),
]

# Target
TARGET_RETURN = 60.0
MAX_DRAWDOWN = -25.0
MAX_ATTEMPTS_PER_LLM = 5

# Strategy prompts
PROMPTS = [
    "Create an aggressive momentum strategy using multiple EMAs and RSI for 1H BTC. Target high returns with strong trend following.",

    "Design a mean reversion strategy with Bollinger Bands and volume analysis for 1H BTC. Focus on catching rebounds.",

    "Build a breakout strategy using Donchian Channels, ATR and volume for 1H BTC. Capture strong movements.",

    "Create a multi-indicator strategy combining MACD, RSI, and moving averages for 1H BTC. Aim for high win rate.",

    "Design a volatility-based strategy using ATR and price action for 1H BTC. Profit from volatility expansion.",
]

results = []
best_return = 0
best_strategy = None

def load_data():
    data = pd.read_csv('src/data/rbi/BTC-USD-15m.csv')
    data.columns = data.columns.str.strip().str.lower()
    data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
    data = data.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'})
    data['datetime'] = pd.to_datetime(data['datetime'])
    data = data.set_index('datetime')
    return data.resample('1h').agg({
        'Open': 'first',
        'High': 'max',
        'Low': 'min',
        'Close': 'last',
        'Volume': 'sum'
    }).dropna()

def ask_llm(model_name, prompt, iteration):
    system_msg = """You are an expert quantitative trader. Create a profitable BTC trading strategy for 1H timeframe.

Return ONLY valid JSON in this exact format (no markdown):
{
    "name": "StrategyName",
    "description": "What it does",
    "sma_fast": 20,
    "sma_slow": 50,
    "rsi_period": 14,
    "rsi_entry": 50,
    "rsi_exit": 30,
    "use_volume": true,
    "volume_mult": 1.5,
    "stop_loss": 0.02,
    "take_profit": 0.08,
    "position_size": 0.15
}

Focus on AGGRESSIVE strategies for HIGH RETURNS. This is iteration #{iteration}, so try something different."""

    try:
        print(f"   🤖 Querying {model_name}...")
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": f"{prompt}\n\nMake it aggressive to achieve >60% returns!"}
            ],
            temperature=0.9,
            max_tokens=800
        )

        content = response.choices[0].message.content.strip()

        # Clean JSON
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        config = json.loads(content)
        print(f"   ✅ Got: {config.get('name', 'Unknown')}")
        return config
    except Exception as e:
        print(f"   ❌ Error: {str(e)[:100]}")
        return None

def test_strategy(config, data):
    class DynStrat(Strategy):
        def init(self):
            c = self.data.Close
            self.sma_f = self.I(lambda: pd.Series(c).rolling(config.get('sma_fast', 20)).mean().values)
            self.sma_s = self.I(lambda: pd.Series(c).rolling(config.get('sma_slow', 50)).mean().values)

            def rsi(prices, period):
                deltas = np.diff(prices)
                seed = deltas[:period+1]
                up = seed[seed >= 0].sum() / period
                down = -seed[seed < 0].sum() / period
                if down == 0:
                    return np.full_like(prices, 100)
                rs = up / down
                rsi = np.zeros_like(prices)
                rsi[:period] = 100. - 100. / (1. + rs)
                for i in range(period, len(prices)):
                    delta = deltas[i - 1]
                    up = (up * (period - 1) + max(delta, 0)) / period
                    down = (down * (period - 1) + max(-delta, 0)) / period
                    if down == 0:
                        rsi[i] = 100
                    else:
                        rsi[i] = 100. - 100. / (1. + up/down)
                return rsi

            self.rsi = self.I(rsi, c, config.get('rsi_period', 14))

            if config.get('use_volume'):
                v = self.data.Volume
                self.vol_avg = self.I(lambda: pd.Series(v).rolling(20).mean().values)

        def next(self):
            if np.isnan(self.sma_s[-1]) or np.isnan(self.rsi[-1]):
                return

            p = self.data.Close[-1]

            if not self.position:
                ok = True
                ok = ok and p > self.sma_s[-1]
                ok = ok and self.rsi[-1] > config.get('rsi_entry', 50)
                if config.get('use_volume') and hasattr(self, 'vol_avg'):
                    ok = ok and self.data.Volume[-1] > (self.vol_avg[-1] * config.get('volume_mult', 1.5))

                if ok:
                    size = max(1, int((self.equity * config.get('position_size', 0.1)) / p))
                    sl = p * (1 - config.get('stop_loss', 0.02))
                    tp = p * (1 + config.get('take_profit', 0.06))
                    if size >= 1:
                        self.buy(size=size, sl=sl, tp=tp)
            else:
                if p < self.sma_f[-1] or self.rsi[-1] < config.get('rsi_exit', 30):
                    self.position.close()

    try:
        bt = Backtest(data, DynStrat, cash=100000, commission=.002)
        stats = bt.run()
        return {
            'return': stats['Return [%]'],
            'trades': stats['# Trades'],
            'win_rate': stats['Win Rate [%]'],
            'max_dd': stats['Max. Drawdown [%]'],
            'sharpe': stats['Sharpe Ratio'],
            'equity': stats['Equity Final [$]']
        }
    except Exception as e:
        print(f"   ❌ Backtest failed: {str(e)[:80]}")
        return None

# Main competition
print("\n" + "="*90)
print("🏆 LLM TRADING COMPETITION - RACE TO 60% RETURN!")
print("="*90)
print(f"\n🎯 Target: >{TARGET_RETURN}% return")
print(f"🤖 {len(COMPETING_LLMS)} AI models x {MAX_ATTEMPTS_PER_LLM} attempts each = {len(COMPETING_LLMS) * MAX_ATTEMPTS_PER_LLM} total tests\n")

data = load_data()
print(f"✅ Data loaded: {len(data)} bars (1H BTC)\n")

for llm_idx, (model_name, display_name) in enumerate(COMPETING_LLMS, 1):
    print(f"\n{'='*90}")
    print(f"🤖 LLM #{llm_idx}/{len(COMPETING_LLMS)}: {display_name}")
    print(f"{'='*90}")

    llm_best = 0

    for i in range(1, MAX_ATTEMPTS_PER_LLM + 1):
        print(f"\n📝 Attempt {i}/{MAX_ATTEMPTS_PER_LLM}")

        prompt = PROMPTS[(i-1) % len(PROMPTS)]
        config = ask_llm(model_name, prompt, i)

        if not config:
            continue

        print(f"   🧪 Testing strategy...")
        res = test_strategy(config, data)

        if not res:
            continue

        profit = res['equity'] - 100000
        print(f"   📊 Return: {res['return']:.2f}% | Profit: ${profit:,.0f} | Trades: {res['trades']} | Win: {res['win_rate']:.1f}% | DD: {res['max_dd']:.1f}%")

        llm_best = max(llm_best, res['return'])
        best_return = max(best_return, res['return'])

        if res['return'] > (best_strategy['results']['return'] if best_strategy else 0):
            best_strategy = {'config': config, 'results': res, 'llm': display_name}

        results.append({'llm': display_name, 'iteration': i, **res})

        if res['return'] >= TARGET_RETURN and res['max_dd'] >= MAX_DRAWDOWN:
            print(f"\n   🎉 TARGET MET! {res['return']:.2f}% >= {TARGET_RETURN}%")
            break

        time.sleep(0.5)

    print(f"\n📊 {display_name} Best: {llm_best:.2f}%")

    if best_strategy and best_strategy['results']['return'] >= TARGET_RETURN:
        break

# Summary
print(f"\n\n{'='*90}")
print("🏁 COMPETITION COMPLETE!")
print(f"{'='*90}")

if best_strategy:
    r = best_strategy['results']
    print(f"\n🏆 WINNER:")
    print(f"   LLM:      {best_strategy['llm']}")
    print(f"   Strategy: {best_strategy['config'].get('name', 'Unknown')}")
    print(f"   Return:   {r['return']:.2f}%")
    print(f"   Profit:   ${r['equity']-100000:,.2f}")
    print(f"   Trades:   {r['trades']}")
    print(f"   Win Rate: {r['win_rate']:.2f}%")
    print(f"   Max DD:   {r['max_dd']:.2f}%")
    print(f"   Sharpe:   {r['sharpe']:.2f}")

    if r['return'] >= TARGET_RETURN:
        print(f"\n   ✅ TARGET ACHIEVED!")
    else:
        print(f"\n   ⚠️  Best found: {r['return']:.2f}% (target: {TARGET_RETURN}%)")

    # Save
    df = pd.DataFrame(results)
    df.to_csv('llm_competition_results.csv', index=False)
    print(f"\n✅ Saved to: llm_competition_results.csv")

    # Leaderboard
    print(f"\n📊 LLM LEADERBOARD:")
    lb = df.groupby('llm')['return'].agg(['mean', 'max', 'count']).sort_values('max', ascending=False)
    print(f"\n{'LLM':<25} {'Avg':<10} {'Best':<10} {'Tries':<8}")
    print("-"*60)
    for llm, row in lb.iterrows():
        print(f"{llm:<25} {row['mean']:>7.2f}%  {row['max']:>7.2f}%  {int(row['count']):>6}")

print(f"\n{'='*90}\n")
