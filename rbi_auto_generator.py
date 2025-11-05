"""
🌙 Moon Dev - RBI Automated Strategy Generator
Continuously generates, tests, and deploys winning trading strategies

This system:
1. Uses AI to generate creative trading strategy ideas
2. Tests each strategy via backtesting
3. Tracks and ranks all results
4. Auto-saves winning strategies (>60% return, <-25% drawdown)
"""

import pandas as pd
import numpy as np
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import time
import os
from datetime import datetime
import json
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    print("❌ ERROR: OPENROUTER_API_KEY not found in .env file!")
    print("Please add your OpenRouter API key to .env")
    exit(1)

TARGET_RETURN = 60.0  # Target return %
MAX_DRAWDOWN = -25.0  # Maximum acceptable drawdown
STRATEGIES_PER_BATCH = 20  # How many strategies to generate
DATA_PATH = 'src/data/rbi/BTC-USD-15m.csv'
RESULTS_DIR = 'src/data/rbi_auto/'
WINNERS_DIR = 'src/data/rbi_auto/winners/'

# Create directories
os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(WINNERS_DIR, exist_ok=True)

# AI Models to use for generation - using official upstream model IDs
AI_MODELS = [
    "anthropic/claude-sonnet-4.5",  # Claude 4.5 Sonnet - Great for creative strategies
    "openai/gpt-5-mini",  # GPT-5 Mini - Strong analytical thinking
    "google/gemini-2.5-flash",  # Gemini 2.5 Flash - Fast and creative
]

def calculate_sma(prices, period):
    return pd.Series(prices).rolling(period).mean().values

def calculate_ema(prices, period):
    return pd.Series(prices).ewm(span=period, adjust=False).mean().values

def calculate_rsi(prices, period=14):
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

def generate_strategy_idea(model_name, iteration):
    """Use AI to generate a creative trading strategy idea"""
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
    )

    prompt = f"""Generate a creative and profitable trading strategy for cryptocurrency (BTC).

REQUIREMENTS:
- Must target >60% annual return
- Maximum drawdown <25%
- Use technical indicators available in pandas_ta or simple calculations
- Focus on trend following, momentum, or volatility strategies
- Can use leverage (2x-5x) if properly risk-managed

Previous winning strategy for reference:
- 5x Leverage EMA 20/100 + RSI >68 + Volume 2x confirmation
- Return: 64.78%, Max DD: -8.71%, Sharpe: 2.13

Your strategy should be DIFFERENT and creative. Consider:
- Different indicator combinations
- Alternative entry/exit timing
- Unique filter combinations
- Different risk management approaches

Output ONLY a JSON object with this structure:
{{
    "name": "UniqueTwoWordName",
    "description": "Brief description",
    "fast_ma": 20,
    "slow_ma": 100,
    "use_ema": true,
    "leverage": 5.0,
    "stop_loss_pct": 0.01,
    "take_profit_pct": 0.06,
    "rsi_min": 68,
    "rsi_max": null,
    "use_volume": true,
    "volume_mult": 2.0,
    "additional_filters": "any special logic"
}}

Generate strategy #{iteration}. Be creative and unique!"""

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=1.0,  # High temperature for creativity
            max_tokens=1000,
        )

        content = response.choices[0].message.content.strip()

        # Extract JSON from response
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        strategy = json.loads(content)
        return strategy

    except Exception as e:
        print(f"   ❌ Error generating strategy: {e}")
        return None

def test_strategy(strategy_config, data):
    """Backtest a strategy configuration"""

    class GeneratedStrategy(Strategy):
        def init(self):
            close = self.data.Close

            # Moving averages
            if strategy_config.get('use_ema', False):
                self.ma_fast = self.I(calculate_ema, close, strategy_config['fast_ma'])
                self.ma_slow = self.I(calculate_ema, close, strategy_config['slow_ma'])
            else:
                self.ma_fast = self.I(calculate_sma, close, strategy_config['fast_ma'])
                self.ma_slow = self.I(calculate_sma, close, strategy_config['slow_ma'])

            # RSI
            if strategy_config.get('rsi_min') or strategy_config.get('rsi_max'):
                self.rsi = self.I(calculate_rsi, close, 14)

            # Volume
            if strategy_config.get('use_volume', False):
                vol = self.data.Volume
                self.vol_avg = self.I(lambda: pd.Series(vol).rolling(20).mean().values)

        def next(self):
            if np.isnan(self.ma_slow[-1]):
                return

            price = self.data.Close[-1]

            if not self.position:
                # Entry conditions
                entry_ok = False

                # MA crossover or above
                if crossover(self.ma_fast, self.ma_slow) or self.ma_fast[-1] > self.ma_slow[-1]:
                    entry_ok = True

                # RSI filters
                if strategy_config.get('rsi_min') and hasattr(self, 'rsi'):
                    if self.rsi[-1] < strategy_config['rsi_min']:
                        entry_ok = False

                if strategy_config.get('rsi_max') and hasattr(self, 'rsi'):
                    if self.rsi[-1] > strategy_config['rsi_max']:
                        entry_ok = False

                # Volume filter
                if strategy_config.get('use_volume') and hasattr(self, 'vol_avg'):
                    vol_mult = strategy_config.get('volume_mult', 1.5)
                    if self.data.Volume[-1] < (self.vol_avg[-1] * vol_mult):
                        entry_ok = False

                if entry_ok:
                    leverage = strategy_config.get('leverage', 1.0)
                    sl_pct = strategy_config.get('stop_loss_pct', 0.02)
                    tp_pct = strategy_config.get('take_profit_pct', 0.10)

                    sl = price * (1 - sl_pct)
                    tp = price * (1 + tp_pct)
                    self.buy(size=leverage, sl=sl, tp=tp)

            else:
                # Exit on death cross
                if crossover(self.ma_slow, self.ma_fast):
                    self.position.close()

    try:
        bt = Backtest(data, GeneratedStrategy, cash=100000, commission=.002)
        stats = bt.run()

        return {
            'success': True,
            'return': stats['Return [%]'],
            'buy_hold': stats['Buy & Hold Return [%]'],
            'trades': stats['# Trades'],
            'win_rate': stats['Win Rate [%]'],
            'max_dd': stats['Max. Drawdown [%]'],
            'sharpe': stats['Sharpe Ratio'],
            'final_equity': stats['Equity Final [$]'],
            'avg_trade': stats['Avg. Trade [%]'],
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def save_winner(strategy_config, results, iteration):
    """Save a winning strategy to file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{WINNERS_DIR}winner_{iteration}_{timestamp}_{results['return']:.1f}pct.json"

    winner_data = {
        'timestamp': timestamp,
        'iteration': iteration,
        'strategy': strategy_config,
        'results': results,
    }

    with open(filename, 'w') as f:
        json.dump(winner_data, f, indent=2)

    print(f"   💾 Saved winner to: {filename}")

def main():
    print("=" * 90)
    print("🌙 MOON DEV - RBI AUTOMATED STRATEGY GENERATOR")
    print("=" * 90)
    print(f"\n🎯 Target: >{TARGET_RETURN}% return with max DD {MAX_DRAWDOWN}%")
    print(f"🤖 AI Models: {len(AI_MODELS)} models")
    print(f"📊 Batch size: {STRATEGIES_PER_BATCH} strategies")

    # Load data
    print(f"\n📈 Loading BTC data from {DATA_PATH}...")
    data = pd.read_csv(DATA_PATH)
    data.columns = data.columns.str.strip().str.lower()
    data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
    data = data.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'})
    data['datetime'] = pd.to_datetime(data['datetime'])
    data = data.set_index('datetime')

    # Resample to 1H
    data = data.resample('1h').agg({
        'Open': 'first',
        'High': 'max',
        'Low': 'min',
        'Close': 'last',
        'Volume': 'sum'
    }).dropna()

    print(f"✅ Data loaded: {len(data)} bars (1H)")

    # Results tracking
    all_results = []
    winners_found = 0

    print(f"\n{'='*90}")
    print("🚀 STARTING AUTOMATED STRATEGY GENERATION")
    print(f"{'='*90}\n")

    for i in range(STRATEGIES_PER_BATCH):
        model = AI_MODELS[i % len(AI_MODELS)]

        print(f"\n{'='*90}")
        print(f"🔬 Strategy {i+1}/{STRATEGIES_PER_BATCH} - Using {model.split('/')[-1]}")
        print(f"{'='*90}")

        # Generate strategy
        print(f"   🤖 Generating strategy idea...")
        strategy = generate_strategy_idea(model, i+1)

        if not strategy:
            print(f"   ⚠️  Failed to generate strategy, skipping...")
            continue

        print(f"   📝 Strategy: {strategy.get('name', 'Unknown')}")
        print(f"   📄 Description: {strategy.get('description', 'N/A')}")
        print(f"   ⚙️  Config: MA {strategy.get('fast_ma')}/{strategy.get('slow_ma')}, "
              f"Leverage {strategy.get('leverage')}x, "
              f"RSI >{strategy.get('rsi_min', 'None')}")

        # Test strategy
        print(f"   🧪 Running backtest...")
        results = test_strategy(strategy, data)

        if not results['success']:
            print(f"   ❌ Backtest failed: {results.get('error', 'Unknown error')}")
            continue

        # Display results
        print(f"\n   📊 RESULTS:")
        print(f"      Return:        {results['return']:.2f}%")
        print(f"      Max DD:        {results['max_dd']:.2f}%")
        print(f"      Sharpe:        {results['sharpe']:.2f}")
        print(f"      Win Rate:      {results['win_rate']:.2f}%")
        print(f"      # Trades:      {results['trades']}")
        print(f"      Avg Trade:     {results['avg_trade']:.2f}%")

        # Check if winner
        is_winner = (results['return'] >= TARGET_RETURN and
                    results['max_dd'] >= MAX_DRAWDOWN)

        if is_winner:
            print(f"\n   🎉🎉🎉 WINNER FOUND! {results['return']:.2f}% >= {TARGET_RETURN}%")
            save_winner(strategy, results, i+1)
            winners_found += 1

        # Track result
        all_results.append({
            'iteration': i+1,
            'model': model,
            'name': strategy.get('name', 'Unknown'),
            'strategy': strategy,
            'results': results,
            'is_winner': is_winner,
        })

        time.sleep(1)  # Rate limiting

    # Final summary
    print(f"\n\n{'='*90}")
    print("🏁 AUTOMATED GENERATION COMPLETE")
    print(f"{'='*90}\n")

    # Sort by return
    all_results.sort(key=lambda x: x['results']['return'] if x['results']['success'] else -999, reverse=True)

    print(f"{'Rank':<6} {'Strategy':<30} {'Model':<20} {'Return':<12} {'MaxDD':<10} {'Status':<8}")
    print("-" * 90)

    for rank, r in enumerate(all_results[:10], 1):  # Top 10
        if not r['results']['success']:
            continue

        medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else "  "
        status = "🎯" if r['is_winner'] else ""
        model_short = r['model'].split('/')[-1][:18]

        print(f"{medal} #{rank:<4} {r['name']:<28} {model_short:<18} "
              f"{r['results']['return']:>9.2f}%  {r['results']['max_dd']:>8.2f}%  {status}")

    # Save all results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"{RESULTS_DIR}batch_{timestamp}.json"
    with open(results_file, 'w') as f:
        json.dump(all_results, f, indent=2)

    print(f"\n✅ All results saved to: {results_file}")
    print(f"🏆 Winners found: {winners_found}")

    if winners_found > 0:
        print(f"💾 Winner files saved to: {WINNERS_DIR}")
        print(f"\n🚀 Ready for deployment!")
    else:
        best = all_results[0] if all_results else None
        if best and best['results']['success']:
            print(f"\n📊 Best strategy: {best['name']}")
            print(f"   Return: {best['results']['return']:.2f}%")
            print(f"   Max DD: {best['results']['max_dd']:.2f}%")
            print(f"   Gap to target: {TARGET_RETURN - best['results']['return']:.2f}%")

    print(f"\n{'='*90}\n")

if __name__ == "__main__":
    main()
