"""
🌙 Moon Dev - RBI Auto-Deployment System
Automatically deploys winning strategies to trading_agent.py

This system:
1. Monitors the winners directory for new strategies
2. Converts winner JSON to trading_agent format
3. Creates strategy files in src/strategies/
4. Updates configuration to use new strategies
"""

import json
import os
from datetime import datetime
from pathlib import Path

WINNERS_DIR = 'src/data/rbi_auto/winners/'
STRATEGIES_DIR = 'src/strategies/auto_generated/'
DEPLOY_LOG = 'src/data/rbi_auto/deployment_log.txt'

os.makedirs(STRATEGIES_DIR, exist_ok=True)

def load_winners():
    """Load all winner strategy files"""
    winners = []

    if not os.path.exists(WINNERS_DIR):
        return winners

    for filename in os.listdir(WINNERS_DIR):
        if filename.endswith('.json'):
            filepath = os.path.join(WINNERS_DIR, filename)
            with open(filepath, 'r') as f:
                winner = json.load(f)
                winner['filename'] = filename
                winners.append(winner)

    # Sort by return (best first)
    winners.sort(key=lambda x: x['results']['return'], reverse=True)

    return winners

def generate_strategy_code(winner):
    """Generate Python strategy code from winner JSON"""

    strategy = winner['strategy']
    name = strategy['name'].replace(' ', '').replace('-', '').replace('/', '_').replace('.', '_')

    code = f'''"""
🌙 Moon Dev - Auto-Generated Strategy: {strategy['name']}
Generated: {winner['timestamp']}
Performance: {winner['results']['return']:.2f}% return, {winner['results']['max_dd']:.2f}% max DD

Description: {strategy.get('description', 'N/A')}
"""

from backtesting import Strategy
from backtesting.lib import crossover
import pandas as pd
import numpy as np

class {name}Strategy(Strategy):
    """
    {strategy.get('description', 'Auto-generated strategy')}

    Parameters:
    - Fast MA: {strategy['fast_ma']}
    - Slow MA: {strategy['slow_ma']}
    - Use EMA: {strategy['use_ema']}
    - Leverage: {strategy.get('leverage', 1.0)}x
    - Stop Loss: {strategy.get('stop_loss_pct', 0.02) * 100:.1f}%
    - Take Profit: {strategy.get('take_profit_pct', 0.10) * 100:.1f}%
    - RSI Min: {strategy.get('rsi_min', 'None')}
    - Volume Filter: {strategy.get('use_volume', False)}

    Backtest Results:
    - Return: {winner['results']['return']:.2f}%
    - Win Rate: {winner['results']['win_rate']:.2f}%
    - Sharpe Ratio: {winner['results']['sharpe']:.2f}
    - Trades: {winner['results']['trades']}
    """

    # Strategy parameters
    fast_ma = {strategy['fast_ma']}
    slow_ma = {strategy['slow_ma']}
    use_ema = {strategy['use_ema']}
    leverage = {strategy.get('leverage', 1.0)}
    stop_loss_pct = {strategy.get('stop_loss_pct', 0.02)}
    take_profit_pct = {strategy.get('take_profit_pct', 0.10)}
    rsi_min = {strategy.get('rsi_min', 'None')}
    use_volume = {strategy.get('use_volume', False)}
    volume_mult = {strategy.get('volume_mult', 1.5)}

    def init(self):
        close = self.data.Close

        # Calculate moving averages
        if self.use_ema:
            self.ma_fast = self.I(self._ema, close, self.fast_ma)
            self.ma_slow = self.I(self._ema, close, self.slow_ma)
        else:
            self.ma_fast = self.I(self._sma, close, self.fast_ma)
            self.ma_slow = self.I(self._sma, close, self.slow_ma)

        # RSI
        if self.rsi_min is not None:
            self.rsi = self.I(self._rsi, close, 14)

        # Volume average
        if self.use_volume:
            vol = self.data.Volume
            self.vol_avg = self.I(lambda: pd.Series(vol).rolling(20).mean().values)

    def _sma(self, prices, period):
        return pd.Series(prices).rolling(period).mean().values

    def _ema(self, prices, period):
        return pd.Series(prices).ewm(span=period, adjust=False).mean().values

    def _rsi(self, prices, period=14):
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

    def next(self):
        if np.isnan(self.ma_slow[-1]):
            return

        price = self.data.Close[-1]

        if not self.position:
            # Entry logic
            entry_ok = False

            # MA condition
            if crossover(self.ma_fast, self.ma_slow) or self.ma_fast[-1] > self.ma_slow[-1]:
                entry_ok = True

            # RSI filter
            if self.rsi_min is not None and hasattr(self, 'rsi'):
                if self.rsi[-1] < self.rsi_min:
                    entry_ok = False

            # Volume filter
            if self.use_volume and hasattr(self, 'vol_avg'):
                if self.data.Volume[-1] < (self.vol_avg[-1] * self.volume_mult):
                    entry_ok = False

            if entry_ok:
                sl = price * (1 - self.stop_loss_pct)
                tp = price * (1 + self.take_profit_pct)
                self.buy(size=self.leverage, sl=sl, tp=tp)

        else:
            # Exit on death cross
            if crossover(self.ma_slow, self.ma_fast):
                self.position.close()
'''

    return code

def deploy_strategy(winner, rank):
    """Deploy a winner strategy to strategies directory"""

    name = winner['strategy']['name'].replace(' ', '').replace('-', '').replace('/', '_').replace('.', '_')
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Generate code
    code = generate_strategy_code(winner)

    # Save to strategies directory
    filename = f"{STRATEGIES_DIR}{name}_rank{rank}_{timestamp}.py"
    with open(filename, 'w') as f:
        f.write(code)

    # Log deployment
    log_entry = f"""
{'='*80}
Deployment: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Strategy: {winner['strategy']['name']}
Rank: #{rank}
Return: {winner['results']['return']:.2f}%
Max DD: {winner['results']['max_dd']:.2f}%
Sharpe: {winner['results']['sharpe']:.2f}
File: {filename}
{'='*80}
"""

    with open(DEPLOY_LOG, 'a') as f:
        f.write(log_entry + '\n')

    return filename

def main():
    print("=" * 90)
    print("🌙 MOON DEV - RBI AUTO-DEPLOYMENT SYSTEM")
    print("=" * 90)

    # Load winners
    print(f"\n📂 Loading winners from {WINNERS_DIR}...")
    winners = load_winners()

    if not winners:
        print("⚠️  No winners found in directory")
        print(f"   Run rbi_auto_generator.py first to generate strategies")
        return

    print(f"✅ Found {len(winners)} winning strategies")

    # Display winners
    print(f"\n{'='*90}")
    print("🏆 WINNING STRATEGIES")
    print(f"{'='*90}\n")

    print(f"{'Rank':<6} {'Name':<30} {'Return':<12} {'Max DD':<10} {'Sharpe':<8}")
    print("-" * 90)

    for rank, winner in enumerate(winners, 1):
        print(f"#{rank:<5} {winner['strategy']['name']:<28} "
              f"{winner['results']['return']:>9.2f}%  "
              f"{winner['results']['max_dd']:>8.2f}%  "
              f"{winner['results']['sharpe']:>6.2f}")

    # Deploy strategies
    print(f"\n{'='*90}")
    print("🚀 DEPLOYING STRATEGIES")
    print(f"{'='*90}\n")

    deployed_files = []

    for rank, winner in enumerate(winners, 1):
        print(f"📦 Deploying #{rank}: {winner['strategy']['name']}...")

        try:
            filename = deploy_strategy(winner, rank)
            deployed_files.append(filename)
            print(f"   ✅ Deployed to: {filename}")

        except Exception as e:
            print(f"   ❌ Error: {e}")

    # Summary
    print(f"\n{'='*90}")
    print("✅ DEPLOYMENT COMPLETE")
    print(f"{'='*90}\n")

    print(f"📊 Deployed: {len(deployed_files)}/{len(winners)} strategies")
    print(f"📁 Location: {STRATEGIES_DIR}")
    print(f"📝 Log: {DEPLOY_LOG}")

    # Usage instructions
    print(f"\n{'='*90}")
    print("📚 USAGE INSTRUCTIONS")
    print(f"{'='*90}\n")

    if deployed_files:
        best_file = deployed_files[0]
        strategy_name = winners[0]['strategy']['name'].replace(' ', '').replace('-', '')

        print("To use the best strategy in your trading:")
        print("")
        print(f"1. Import the strategy:")
        print(f"   from src.strategies.auto_generated.{Path(best_file).stem} import {strategy_name}Strategy")
        print("")
        print(f"2. Use in backtesting:")
        print(f"   bt = Backtest(data, {strategy_name}Strategy, cash=100000, commission=.002)")
        print(f"   stats = bt.run()")
        print("")
        print(f"3. Or integrate with trading_agent.py for live trading")
        print("")

    print(f"{'='*90}\n")

if __name__ == "__main__":
    main()
