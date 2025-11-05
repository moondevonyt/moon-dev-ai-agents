"""
🌙 Moon Dev - AI-Generated Strategy Testing
Geïnspireerd door RBI Agent - test meerdere populaire strategieën

Strategieën:
1. Bollinger Band Mean Reversion
2. MACD + RSI Combo
3. Volume Breakout
4. Triple EMA Crossover
"""

from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import pandas as pd
import numpy as np

def calculate_sma(prices, period):
    return pd.Series(prices).rolling(period).mean().values

def calculate_ema(prices, period):
    return pd.Series(prices).ewm(span=period, adjust=False).mean().values

def calculate_bb(prices, period=20, std=2):
    """Bollinger Bands"""
    sma = pd.Series(prices).rolling(period).mean()
    std_dev = pd.Series(prices).rolling(period).std()
    upper = sma + (std_dev * std)
    lower = sma - (std_dev * std)
    return upper.values, sma.values, lower.values

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

def calculate_macd(prices, fast=12, slow=26, signal=9):
    """MACD calculation"""
    ema_fast = pd.Series(prices).ewm(span=fast, adjust=False).mean()
    ema_slow = pd.Series(prices).ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    return macd_line.values, signal_line.values

# Load data
print("📊 Loading BTC data...")
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

print(f"✅ Data: {len(data)} rows\n")

# Strategy 1: Bollinger Band Mean Reversion
class BollingerMeanReversion(Strategy):
    bb_period = 20
    bb_std = 2

    def init(self):
        self.bb_upper, self.bb_middle, self.bb_lower = self.I(
            calculate_bb, self.data.Close, self.bb_period, self.bb_std
        )

    def next(self):
        if np.isnan(self.bb_lower[-1]):
            return

        price = self.data.Close[-1]

        if not self.position:
            # Buy when price touches lower band (oversold)
            if price <= self.bb_lower[-1]:
                self.buy()
        else:
            # Sell when price reaches middle or upper band
            if price >= self.bb_middle[-1]:
                self.position.close()

# Strategy 2: MACD + RSI Combo
class MACDRSICombo(Strategy):
    rsi_period = 14
    rsi_oversold = 30
    rsi_overbought = 70

    def init(self):
        self.macd, self.signal = self.I(calculate_macd, self.data.Close)
        self.rsi = self.I(calculate_rsi, self.data.Close, self.rsi_period)

    def next(self):
        if np.isnan(self.macd[-1]) or np.isnan(self.rsi[-1]):
            return

        if not self.position:
            # Buy: MACD cross above signal + RSI oversold
            if crossover(self.macd, self.signal) and self.rsi[-1] < 50:
                self.buy()
        else:
            # Sell: MACD cross below signal OR RSI overbought
            if crossover(self.signal, self.macd) or self.rsi[-1] > self.rsi_overbought:
                self.position.close()

# Strategy 3: Volume Breakout
class VolumeBreakout(Strategy):
    sma_period = 20
    vol_multiplier = 2.0

    def init(self):
        self.sma = self.I(calculate_sma, self.data.Close, self.sma_period)
        self.vol_sma = self.I(calculate_sma, self.data.Volume, self.sma_period)

    def next(self):
        if np.isnan(self.sma[-1]) or np.isnan(self.vol_sma[-1]):
            return

        price = self.data.Close[-1]
        volume = self.data.Volume[-1]

        if not self.position:
            # Buy: Price above SMA + Volume spike
            if price > self.sma[-1] and volume > (self.vol_sma[-1] * self.vol_multiplier):
                self.buy()
        else:
            # Sell: Price below SMA
            if price < self.sma[-1]:
                self.position.close()

# Strategy 4: Triple EMA
class TripleEMA(Strategy):
    ema_fast = 12
    ema_medium = 26
    ema_slow = 50

    def init(self):
        close = self.data.Close
        self.ema12 = self.I(calculate_ema, close, self.ema_fast)
        self.ema26 = self.I(calculate_ema, close, self.ema_medium)
        self.ema50 = self.I(calculate_ema, close, self.ema_slow)

    def next(self):
        if np.isnan(self.ema50[-1]):
            return

        if not self.position:
            # Buy: Fast > Medium > Slow (bullish alignment)
            if self.ema12[-1] > self.ema26[-1] > self.ema50[-1]:
                self.buy()
        else:
            # Sell: Fast < Medium (trend reversal)
            if self.ema12[-1] < self.ema26[-1]:
                self.position.close()

# Test all strategies
strategies = [
    (BollingerMeanReversion, "Bollinger Mean Reversion"),
    (MACDRSICombo, "MACD + RSI Combo"),
    (VolumeBreakout, "Volume Breakout"),
    (TripleEMA, "Triple EMA Crossover")
]

results = []

print("=" * 80)
print("🤖 AI-STYLE STRATEGY TESTING (RBI-Inspired)")
print("=" * 80)

for strategy_class, name in strategies:
    print(f"\n📊 Testing: {name}")
    print("-" * 80)

    try:
        bt = Backtest(data, strategy_class, cash=100000, commission=.002)
        stats = bt.run()

        result = {
            'name': name,
            'return': stats['Return [%]'],
            'buy_hold': stats['Buy & Hold Return [%]'],
            'trades': stats['# Trades'],
            'win_rate': stats['Win Rate [%]'],
            'max_dd': stats['Max. Drawdown [%]'],
            'sharpe': stats['Sharpe Ratio'],
            'final_equity': stats['Equity Final [$]']
        }
        results.append(result)

        profit = result['final_equity'] - 100000
        alpha = result['return'] - result['buy_hold']

        print(f"✅ Return:        {result['return']:.2f}%")
        print(f"   Profit:        ${profit:,.2f}")
        print(f"   # Trades:      {result['trades']}")
        print(f"   Win Rate:      {result['win_rate']:.2f}%")
        print(f"   Max DD:        {result['max_dd']:.2f}%")
        print(f"   Sharpe:        {result['sharpe']:.2f}")
        print(f"   Alpha vs B&H:  {alpha:.2f}%")

    except Exception as e:
        print(f"❌ Error: {str(e)}")

# Sort by return
results.sort(key=lambda x: x['return'], reverse=True)

# Display comparison
print("\n\n" + "=" * 80)
print("📊 AI STRATEGY COMPARISON")
print("=" * 80)
print(f"{'Strategy':<30} {'Return':<10} {'Trades':<8} {'Win%':<8} {'MaxDD':<10} {'Sharpe':<8}")
print("-" * 80)

for r in results:
    status = "🏆" if r == results[0] else "✅" if r['return'] > 0 else "❌"
    print(f"{status} {r['name']:<28} {r['return']:>7.2f}%  {r['trades']:>6}  {r['win_rate']:>6.1f}%  {r['max_dd']:>8.2f}%  {r['sharpe']:>6.2f}")

# Best strategy
if results:
    best = results[0]
    print("\n" + "=" * 80)
    print("🏆 BEST AI STRATEGY")
    print("=" * 80)
    print(f"Strategy:         {best['name']}")
    print(f"Return:           {best['return']:.2f}%")
    print(f"Final Capital:    ${best['final_equity']:,.2f}")
    print(f"Profit:           ${best['final_equity'] - 100000:,.2f}")
    print(f"# Trades:         {best['trades']}")
    print(f"Win Rate:         {best['win_rate']:.2f}%")
    print(f"Max Drawdown:     {best['max_dd']:.2f}%")
    print(f"Sharpe Ratio:     {best['sharpe']:.2f}")

# Save results
df_results = pd.DataFrame(results)
df_results.to_csv('ai_strategies_results.csv', index=False)
print(f"\n✅ Results saved to: ai_strategies_results.csv")
