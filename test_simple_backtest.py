"""
🌙 Moon Dev - Simple Backtest Demonstration
Test van de backtesting.py library met een eenvoudige RSI strategie
"""

from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import pandas as pd
import numpy as np

def calculate_rsi(close_prices, period=14):
    """Calculate RSI indicator"""
    deltas = np.diff(close_prices)
    seed = deltas[:period+1]
    up = seed[seed >= 0].sum() / period
    down = -seed[seed < 0].sum() / period
    rs = up / down
    rsi = np.zeros_like(close_prices)
    rsi[:period] = 100. - 100. / (1. + rs)

    for i in range(period, len(close_prices)):
        delta = deltas[i - 1]
        if delta > 0:
            upval = delta
            downval = 0.
        else:
            upval = 0.
            downval = -delta

        up = (up * (period - 1) + upval) / period
        down = (down * (period - 1) + downval) / period
        rs = up / down
        rsi[i] = 100. - 100. / (1. + rs)

    return rsi

class SimpleRSIStrategy(Strategy):
    """
    Eenvoudige RSI strategie:
    - Koop wanneer RSI < 30 (oversold)
    - Verkoop wanneer RSI > 70 (overbought)
    """

    # Parameters
    rsi_period = 14
    rsi_lower = 30
    rsi_upper = 70

    def init(self):
        """Initialiseer indicatoren"""
        self.rsi = self.I(calculate_rsi, self.data.Close, self.rsi_period)

    def next(self):
        """Trading logica per bar"""

        # Koop signaal: RSI onder 30 (oversold)
        if crossover(self.rsi_lower, self.rsi):
            if not self.position:
                self.buy()

        # Verkoop signaal: RSI boven 70 (overbought)
        elif crossover(self.rsi, self.rsi_upper):
            if self.position:
                self.position.close()


# Laad de data
print("📊 Loading BTC data...")
df = pd.read_csv('src/data/rbi/BTC-USD-15m.csv', index_col=0, parse_dates=True)

# Strip whitespace from column names and capitalize
df.columns = [col.strip().capitalize() for col in df.columns]

# Keep only required columns (drop unnamed columns)
required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
df = df[[col for col in required_cols if col in df.columns]]

# Resample to 1H timeframe
print("🔄 Resampling from 15m to 1H timeframe...")
df_1h = df.resample('1h').agg({
    'Open': 'first',
    'High': 'max',
    'Low': 'min',
    'Close': 'last',
    'Volume': 'sum'
}).dropna()

df = df_1h

print(f"✅ Data loaded: {len(df)} rows from {df.index[0]} to {df.index[-1]}")
print(f"📈 Columns: {list(df.columns)}")
print(f"📈 Sample data:\n{df.head()}\n")

# Run backtest
print("🚀 Running backtest...")
INITIAL_CASH = 100000  # $100k for BTC trading
bt = Backtest(df, SimpleRSIStrategy, cash=INITIAL_CASH, commission=.002)
stats = bt.run()

# Toon resultaten
print("=" * 60)
print("📊 BACKTEST RESULTS")
print("=" * 60)
print(f"Initial Capital:     ${INITIAL_CASH:,.2f}")
print(f"Final Portfolio:     ${stats['Equity Final [$]']:,.2f}")
print(f"Return:              {stats['Return [%]']:.2f}%")
print(f"Buy & Hold Return:   {stats['Buy & Hold Return [%]']:.2f}%")
print(f"Max Drawdown:        {stats['Max. Drawdown [%]']:.2f}%")
print(f"Sharpe Ratio:        {stats['Sharpe Ratio']:.2f}")
print(f"# Trades:            {stats['# Trades']}")
print(f"Win Rate:            {stats['Win Rate [%]']:.2f}%")
print(f"Avg Trade:           {stats['Avg. Trade [%]']:.2f}%")
print("=" * 60)

# Beoordeling
if stats['Return [%]'] > 0:
    print("✅ STRATEGIE IS WINSTGEVEND!")
else:
    print("❌ Strategie verliesgevend - optimalisatie nodig")

print("\n💡 Tip: Run bt.plot() om een grafische visualisatie te zien (vereist browser)")
