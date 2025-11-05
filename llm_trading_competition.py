"""
🌙 Moon Dev - LLM Trading Strategy Competition
Laat verschillende AI modellen strategieën genereren en testen tot we >60% return vinden!

LLM's in competitie:
1. Gemini 2.5 Flash (Google) - Fast & multimodal
2. Kimi K2 (Moonshot) - Advanced Chinese/English
3. Claude Haiku 4.5 (Anthropic) - Fast reasoning
4. DeepSeek R1 (DeepSeek) - Advanced reasoning
5. GPT-5 Mini (OpenAI) - Efficient
6. Qwen 3 Max (Alibaba) - Powerful reasoning

Target: >60% return met max 25% drawdown
"""

import sys
from pathlib import Path
import os
import json
import time
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# Import model factory
from src.models.model_factory import model_factory
from backtesting import Backtest, Strategy
import pandas as pd
import numpy as np
from termcolor import cprint

# LLM Configuration
COMPETING_LLMS = [
    ("openrouter", "google/gemini-2.5-flash", "Gemini 2.5 Flash"),
    ("openrouter", "moonshot/kimi-k2", "Kimi K2"),
    ("openrouter", "anthropic/claude-haiku-4.5", "Claude Haiku 4.5"),
    ("openrouter", "deepseek/deepseek-r1-0528", "DeepSeek R1"),
    ("openrouter", "openai/gpt-5-mini", "GPT-5 Mini"),
    ("openrouter", "qwen/qwen3-max", "Qwen 3 Max"),
]

# Target metrics
TARGET_RETURN = 60.0  # >60%
MAX_DRAWDOWN = -25.0  # Max 25% DD acceptable
MAX_ITERATIONS_PER_LLM = 5  # Try 5 strategies per LLM

# Strategy ideas to test
STRATEGY_PROMPTS = [
    "Create a momentum breakout strategy using RSI, MACD and volume confirmation for 1H BTC trading. Focus on strong trending moves with tight stop losses.",

    "Design a mean reversion strategy using Bollinger Bands and RSI for oversold/overbought conditions on 1H BTC. Include dynamic position sizing.",

    "Build a trend following strategy with multiple EMAs (12/26/50) and ADX for trend strength confirmation on 1H BTC. Focus on riding strong trends.",

    "Create a volatility breakout strategy using ATR and Donchian Channels for 1H BTC. Enter on volatility expansion with momentum confirmation.",

    "Design a swing trading strategy combining Fibonacci retracements with RSI divergence on 1H BTC. Target high probability reversal setups.",
]

# Results tracking
all_results = []
best_strategy = None
best_return = 0

def load_btc_data():
    """Load and prepare BTC data"""
    data = pd.read_csv('src/data/rbi/BTC-USD-15m.csv')
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

    return data

def ask_llm_for_strategy(model_type, model_name, prompt_text, iteration):
    """Ask LLM to generate a trading strategy"""

    system_prompt = """You are an expert quantitative trading strategist.
Generate a profitable BTC trading strategy for 1H timeframe based on the user's request.

Provide your response in this exact JSON format (no markdown, just pure JSON):
{
    "name": "StrategyName",
    "description": "Brief description",
    "indicators": {
        "sma_fast": 20,
        "sma_slow": 50,
        "rsi_period": 14,
        "use_volume": true,
        "volume_multiplier": 1.5
    },
    "entry_conditions": "Price above SMA50 AND RSI > 50 AND volume > 1.5x average",
    "exit_conditions": "Price below SMA20 OR RSI < 30",
    "risk_management": {
        "stop_loss_pct": 0.02,
        "take_profit_pct": 0.06,
        "position_size": 0.10
    }
}

Focus on:
- Simple, implementable logic
- Clear entry/exit rules
- Proper risk management
- Realistic parameters for 1H BTC"""

    user_prompt = f"""{prompt_text}

This is attempt #{iteration}. Previous attempts may have failed, so try a different approach.
Consider:
- Different indicator combinations
- Varying timeframes or parameters
- Alternative entry/exit logic
- Better risk/reward ratios

Return ONLY valid JSON, no extra text."""

    try:
        cprint(f"   🤖 Asking {model_name} for strategy idea...", "cyan")
        model = model_factory.get_model(model_type, model_name)

        if not model:
            cprint(f"   ❌ Could not get model {model_name}", "red")
            return None

        response = model.generate_response(
            system_prompt=system_prompt,
            user_content=user_prompt,
            temperature=0.8,  # Higher for creativity
            max_tokens=1500
        )

        if not response or not response.content:
            cprint(f"   ❌ No response from {model_name}", "red")
            return None

        # Try to extract JSON from response
        content = response.content.strip()

        # Remove markdown code blocks if present
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        strategy_config = json.loads(content)
        cprint(f"   ✅ Received strategy: {strategy_config.get('name', 'Unknown')}", "green")
        return strategy_config

    except json.JSONDecodeError as e:
        cprint(f"   ❌ JSON parsing error: {str(e)}", "red")
        cprint(f"   Response was: {content[:200]}...", "yellow")
        return None
    except Exception as e:
        cprint(f"   ❌ Error: {str(e)}", "red")
        return None

def test_strategy_config(strategy_config, data):
    """Test a strategy configuration"""

    # Create dynamic strategy class
    class DynamicStrategy(Strategy):
        def init(self):
            close = self.data.Close
            high = self.data.High
            low = self.data.Low
            volume = self.data.Volume

            # Calculate indicators based on config
            indicators = strategy_config.get('indicators', {})

            if 'sma_fast' in indicators:
                self.sma_fast = self.I(lambda: pd.Series(close).rolling(indicators['sma_fast']).mean().values)
            if 'sma_slow' in indicators:
                self.sma_slow = self.I(lambda: pd.Series(close).rolling(indicators['sma_slow']).mean().values)
            if 'rsi_period' in indicators:
                # Simple RSI
                def calc_rsi(prices, period):
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
                        upval = max(delta, 0)
                        downval = max(-delta, 0)
                        up = (up * (period - 1) + upval) / period
                        down = (down * (period - 1) + downval) / period
                        if down == 0:
                            rsi[i] = 100
                        else:
                            rs = up / down
                            rsi[i] = 100. - 100. / (1. + rs)
                    return rsi
                self.rsi = self.I(calc_rsi, close, indicators['rsi_period'])

            if indicators.get('use_volume'):
                vol_period = indicators.get('volume_period', 20)
                self.vol_avg = self.I(lambda: pd.Series(volume).rolling(vol_period).mean().values)

        def next(self):
            # Skip if not enough data
            if hasattr(self, 'sma_slow') and np.isnan(self.sma_slow[-1]):
                return

            indicators = strategy_config.get('indicators', {})
            risk_mgmt = strategy_config.get('risk_management', {})

            price = self.data.Close[-1]

            if not self.position:
                # Simple entry logic based on config
                can_enter = True

                # Check trend
                if hasattr(self, 'sma_fast') and hasattr(self, 'sma_slow'):
                    if price <= self.sma_slow[-1]:
                        can_enter = False

                # Check momentum
                if hasattr(self, 'rsi'):
                    if self.rsi[-1] < 50:
                        can_enter = False

                # Check volume
                if indicators.get('use_volume') and hasattr(self, 'vol_avg'):
                    vol_mult = indicators.get('volume_multiplier', 1.5)
                    if self.data.Volume[-1] < (self.vol_avg[-1] * vol_mult):
                        can_enter = False

                if can_enter:
                    # Position sizing
                    pos_size = risk_mgmt.get('position_size', 0.10)
                    size = max(1, int((self.equity * pos_size) / price))

                    # Stop loss and take profit
                    sl_pct = risk_mgmt.get('stop_loss_pct', 0.02)
                    tp_pct = risk_mgmt.get('take_profit_pct', 0.06)

                    sl_price = price * (1 - sl_pct)
                    tp_price = price * (1 + tp_pct)

                    if size >= 1:
                        self.buy(size=size, sl=sl_price, tp=tp_price)
            else:
                # Exit logic
                can_exit = False

                # Check if trend broken
                if hasattr(self, 'sma_fast'):
                    if price < self.sma_fast[-1]:
                        can_exit = True

                # Check RSI
                if hasattr(self, 'rsi'):
                    if self.rsi[-1] < 30:
                        can_exit = True

                if can_exit:
                    self.position.close()

    try:
        bt = Backtest(data, DynamicStrategy, cash=100000, commission=.002)
        stats = bt.run()

        return {
            'return': stats['Return [%]'],
            'buy_hold': stats['Buy & Hold Return [%]'],
            'trades': stats['# Trades'],
            'win_rate': stats['Win Rate [%]'],
            'max_dd': stats['Max. Drawdown [%]'],
            'sharpe': stats['Sharpe Ratio'],
            'final_equity': stats['Equity Final [$]']
        }
    except Exception as e:
        cprint(f"   ❌ Backtest error: {str(e)}", "red")
        return None

# Main competition loop
def run_competition():
    global best_strategy, best_return, all_results

    cprint("\n" + "=" * 100, "cyan")
    cprint("🏆 LLM TRADING STRATEGY COMPETITION - RACE TO 60% RETURN!", "cyan")
    cprint("=" * 100, "cyan")

    cprint(f"\n🎯 Target: >{TARGET_RETURN}% return with max {abs(MAX_DRAWDOWN)}% drawdown", "yellow")
    cprint(f"🤖 {len(COMPETING_LLMS)} AI models competing", "yellow")
    cprint(f"💡 {MAX_ITERATIONS_PER_LLM} attempts per model\n", "yellow")

    # Load data
    cprint("📊 Loading BTC 1H data...", "cyan")
    data = load_btc_data()
    cprint(f"✅ Data loaded: {len(data)} bars\n", "green")

    # Test each LLM
    for llm_idx, (model_type, model_name, display_name) in enumerate(COMPETING_LLMS, 1):
        cprint(f"\n{'='*100}", "cyan")
        cprint(f"🤖 LLM #{llm_idx}/{len(COMPETING_LLMS)}: {display_name}", "cyan")
        cprint(f"{'='*100}", "cyan")

        llm_best_return = 0
        llm_best_strategy = None

        for iteration in range(1, MAX_ITERATIONS_PER_LLM + 1):
            cprint(f"\n📝 Iteration {iteration}/{MAX_ITERATIONS_PER_LLM}", "yellow")

            # Select a prompt
            prompt = STRATEGY_PROMPTS[(iteration - 1) % len(STRATEGY_PROMPTS)]

            # Get strategy from LLM
            strategy_config = ask_llm_for_strategy(model_type, model_name, prompt, iteration)

            if not strategy_config:
                cprint(f"   ⏭️  Skipping to next iteration", "yellow")
                continue

            # Test the strategy
            cprint(f"   🧪 Testing strategy...", "cyan")
            results = test_strategy_config(strategy_config, data)

            if not results:
                cprint(f"   ⏭️  Strategy failed, trying next", "yellow")
                continue

            # Display results
            profit = results['final_equity'] - 100000
            alpha = results['return'] - results['buy_hold']

            cprint(f"   📊 Results:", "white")
            cprint(f"      Return:     {results['return']:.2f}%", "white")
            cprint(f"      Profit:     ${profit:,.2f}", "white")
            cprint(f"      Trades:     {results['trades']}", "white")
            cprint(f"      Win Rate:   {results['win_rate']:.2f}%", "white")
            cprint(f"      Max DD:     {results['max_dd']:.2f}%", "white")
            cprint(f"      Sharpe:     {results['sharpe']:.2f}", "white")

            # Check if this is LLM's best
            if results['return'] > llm_best_return:
                llm_best_return = results['return']
                llm_best_strategy = {
                    'config': strategy_config,
                    'results': results,
                    'llm': display_name,
                    'iteration': iteration
                }

            # Check if target met
            if results['return'] >= TARGET_RETURN and results['max_dd'] >= MAX_DRAWDOWN:
                cprint(f"\n   🎉 TARGET MET! {results['return']:.2f}% return!", "green")
                best_strategy = {
                    'config': strategy_config,
                    'results': results,
                    'llm': display_name,
                    'iteration': iteration
                }
                best_return = results['return']

                # Save and exit
                save_results()
                return True

            # Track globally best
            if results['return'] > best_return:
                best_return = results['return']
                best_strategy = {
                    'config': strategy_config,
                    'results': results,
                    'llm': display_name,
                    'iteration': iteration
                }

            # Store result
            all_results.append({
                'llm': display_name,
                'iteration': iteration,
                'strategy_name': strategy_config.get('name', 'Unknown'),
                **results
            })

            time.sleep(1)  # Rate limiting

        # LLM summary
        cprint(f"\n{'='*100}", "yellow")
        cprint(f"📊 {display_name} Summary:", "yellow")
        cprint(f"   Best Return: {llm_best_return:.2f}%", "yellow")
        if llm_best_strategy:
            cprint(f"   Best Strategy: {llm_best_strategy['config'].get('name', 'Unknown')}", "yellow")
        cprint(f"{'='*100}", "yellow")

    # Competition complete
    save_results()
    return False

def save_results():
    """Save competition results"""
    cprint(f"\n\n{'='*100}", "cyan")
    cprint("🏁 COMPETITION COMPLETE!", "cyan")
    cprint(f"{'='*100}", "cyan")

    if best_strategy:
        cprint(f"\n🏆 OVERALL WINNER:", "green")
        cprint(f"   LLM:         {best_strategy['llm']}", "green")
        cprint(f"   Strategy:    {best_strategy['config'].get('name', 'Unknown')}", "green")
        cprint(f"   Return:      {best_strategy['results']['return']:.2f}%", "green")
        cprint(f"   Profit:      ${best_strategy['results']['final_equity'] - 100000:,.2f}", "green")
        cprint(f"   Trades:      {best_strategy['results']['trades']}", "green")
        cprint(f"   Win Rate:    {best_strategy['results']['win_rate']:.2f}%", "green")
        cprint(f"   Max DD:      {best_strategy['results']['max_dd']:.2f}%", "green")
        cprint(f"   Sharpe:      {best_strategy['results']['sharpe']:.2f}", "green")

        if best_strategy['results']['return'] >= TARGET_RETURN:
            cprint(f"\n   ✅ TARGET ACHIEVED: {best_strategy['results']['return']:.2f}% >= {TARGET_RETURN}%", "green")
        else:
            cprint(f"\n   ⚠️  Target not met: {best_strategy['results']['return']:.2f}% < {TARGET_RETURN}%", "yellow")
            cprint(f"   Best we found in this run. Try running again or adjust parameters.", "yellow")

    # Save to CSV
    if all_results:
        df = pd.DataFrame(all_results)
        df.to_csv('llm_competition_results.csv', index=False)
        cprint(f"\n✅ Results saved to: llm_competition_results.csv", "green")

        # LLM leaderboard
        cprint(f"\n📊 LLM LEADERBOARD:", "cyan")
        llm_avg = df.groupby('llm')['return'].agg(['mean', 'max', 'count']).sort_values('max', ascending=False)
        cprint(f"\n{'LLM':<25} {'Avg Return':<12} {'Best Return':<12} {'Attempts':<10}", "cyan")
        cprint("-"*60, "cyan")
        for llm, row in llm_avg.iterrows():
            cprint(f"{llm:<25} {row['mean']:>10.2f}%  {row['max']:>10.2f}%  {int(row['count']):>8}", "white")

    cprint(f"\n{'='*100}\n", "cyan")

if __name__ == "__main__":
    target_met = run_competition()

    if target_met:
        cprint("🎉 SUCCESS! Target of 60% return achieved!", "green")
    else:
        cprint("⚠️  Target not met in this run. Best strategy found has been saved.", "yellow")
        cprint("💡 Try running again or adjust TARGET_RETURN", "yellow")
