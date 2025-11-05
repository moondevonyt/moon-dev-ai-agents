"""
🌙 Moon Dev - Trend Following Backtest
Simpele maar effectieve trend-following strategie

Strategie:
- Buy: Prijs boven 50 SMA + RSI > 50 + ADX > 20
- Sell: Prijs onder 20 SMA of RSI < 30
- Stop Loss: 2% onder entry
- Take Profit: 6% boven entry (3:1 R/R)
- Position size: 10% van capital per trade
"""

from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import pandas as pd
import numpy as np

def calculate_rsi(prices, period=14):
    """Calculate RSI"""
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

def calculate_sma(prices, period):
    """Calculate Simple Moving Average"""
    return pd.Series(prices).rolling(period).mean().values

def calculate_atr(high, low, close, period=14):
    """Calculate ATR"""
    tr = np.maximum(high[1:] - low[1:],
                    np.maximum(np.abs(high[1:] - close[:-1]),
                              np.abs(low[1:] - close[:-1])))
    atr = np.zeros(len(close))
    atr[period] = np.mean(tr[:period])
    for i in range(period + 1, len(close)):
        atr[i] = (atr[i-1] * (period - 1) + tr[i-1]) / period
    return atr

def calculate_adx(high, low, close, period=14):
    """Simplified ADX"""
    # True Range
    tr = np.maximum(high[1:] - low[1:],
                    np.maximum(np.abs(high[1:] - close[:-1]),
                              np.abs(low[1:] - close[:-1])))

    # Directional Movement
    up_move = high[1:] - high[:-1]
    down_move = low[:-1] - low[1:]

    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)

    # Smooth TR and DM
    tr_smooth = np.zeros(len(close))
    plus_di = np.zeros(len(close))
    minus_di = np.zeros(len(close))

    for i in range(period, len(close)):
        if i == period:
            tr_smooth[i] = np.sum(tr[i-period:i])
            plus_sum = np.sum(plus_dm[i-period:i])
            minus_sum = np.sum(minus_dm[i-period:i])
        else:
            tr_smooth[i] = tr_smooth[i-1] - (tr_smooth[i-1]/period) + tr[i-1]
            plus_sum = plus_di[i-1] - (plus_di[i-1]/period) + plus_dm[i-1]
            minus_sum = minus_di[i-1] - (minus_di[i-1]/period) + minus_dm[i-1]

        plus_di[i] = 100 * plus_sum / (tr_smooth[i] + 0.0001)
        minus_di[i] = 100 * minus_sum / (tr_smooth[i] + 0.0001)

    # Calculate DX and ADX
    dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di + 0.0001)
    adx = np.zeros(len(close))

    for i in range(period*2, len(close)):
        if i == period*2:
            adx[i] = np.mean(dx[i-period:i])
        else:
            adx[i] = (adx[i-1] * (period-1) + dx[i]) / period

    return adx

# Load data
print("📊 Loading BTC data...")
data = pd.read_csv('src/data/rbi/BTC-USD-15m.csv')
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data = data.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'})
data['datetime'] = pd.to_datetime(data['datetime'])
data = data.set_index('datetime')

print(f"✅ Loaded: {len(data)} rows from {data.index[0]} to {data.index[-1]}")

# Resample to 1H for cleaner signals
print("🔄 Resampling to 1H timeframe...")
data = data.resample('1h').agg({
    'Open': 'first',
    'High': 'max',
    'Low': 'min',
    'Close': 'last',
    'Volume': 'sum'
}).dropna()

print(f"✅ After resampling: {len(data)} rows\n")

class TrendFollowing(Strategy):
    # Parameters
    fast_sma = 20
    slow_sma = 50
    rsi_period = 14
    rsi_entry = 50
    rsi_exit = 30
    adx_period = 14
    adx_threshold = 20
    stop_loss_pct = 0.02  # 2%
    take_profit_pct = 0.06  # 6%
    position_size = 0.10  # 10% of capital

    def init(self):
        close = self.data.Close
        high = self.data.High
        low = self.data.Low

        # Indicators
        self.sma_fast = self.I(calculate_sma, close, self.fast_sma)
        self.sma_slow = self.I(calculate_sma, close, self.slow_sma)
        self.rsi = self.I(calculate_rsi, close, self.rsi_period)
        self.atr = self.I(calculate_atr, high, low, close, 14)
        self.adx = self.I(calculate_adx, high, low, close, self.adx_period)

        print("🌙 Trend Following Strategy Initialized! ✨")
        print(f"   Fast SMA: {self.fast_sma}, Slow SMA: {self.slow_sma}")
        print(f"   RSI: {self.rsi_period}, ADX: {self.adx_period}")
        print(f"   Stop Loss: {self.stop_loss_pct*100}%, Take Profit: {self.take_profit_pct*100}%\n")

    def next(self):
        price = self.data.Close[-1]

        # Skip if not enough data
        if np.isnan(self.sma_slow[-1]) or np.isnan(self.rsi[-1]) or np.isnan(self.adx[-1]):
            return

        if not self.position:
            # Entry conditions
            trend_up = price > self.sma_slow[-1]
            fast_above_slow = self.sma_fast[-1] > self.sma_slow[-1]
            momentum_ok = self.rsi[-1] > self.rsi_entry
            trending = self.adx[-1] > self.adx_threshold

            if trend_up and fast_above_slow and momentum_ok and trending:
                # Calculate position size
                size = max(1, int((self.equity * self.position_size) / price))

                # Set stop loss and take profit
                sl_price = price * (1 - self.stop_loss_pct)
                tp_price = price * (1 + self.take_profit_pct)

                if size >= 1:  # Only buy if we can afford at least 1 unit
                    self.buy(size=size, sl=sl_price, tp=tp_price)

        else:
            # Exit conditions
            trend_broken = price < self.sma_fast[-1]
            momentum_weak = self.rsi[-1] < self.rsi_exit

            if trend_broken or momentum_weak:
                self.position.close()

# Run backtest
print("🚀 Running Trend Following Backtest...\n")
bt = Backtest(data, TrendFollowing, cash=100000, commission=.002)
stats = bt.run()

print("\n" + "=" * 70)
print("📊 TREND FOLLOWING BACKTEST RESULTS (1H)")
print("=" * 70)
print(f"Initial Capital:     ${100000:,.2f}")
print(f"Final Portfolio:     ${stats['Equity Final [$]']:,.2f}")
print(f"Return:              {stats['Return [%]']:.2f}%")
print(f"Buy & Hold Return:   {stats['Buy & Hold Return [%]']:.2f}%")
print(f"Max Drawdown:        {stats['Max. Drawdown [%]']:.2f}%")
print(f"Sharpe Ratio:        {stats['Sharpe Ratio']:.2f}")
print(f"# Trades:            {stats['# Trades']}")
print(f"Win Rate:            {stats['Win Rate [%]']:.2f}%")
print(f"Avg Trade:           {stats['Avg. Trade [%]']:.2f}%")
print(f"Best Trade:          {stats['Best Trade [%]']:.2f}%")
print(f"Worst Trade:         {stats['Worst Trade [%]']:.2f}%")
print(f"Max Trade Duration:  {stats['Max. Trade Duration']}")
print("=" * 70)

profit = stats['Equity Final [$]'] - 100000
if stats['Return [%]'] > 0:
    print(f"\n✅ WINNENDE STRATEGIE! Profit: ${profit:,.2f}")
else:
    print(f"\n❌ Verlies: ${profit:,.2f}")

print(f"\n💡 Alpha vs Buy & Hold: {stats['Return [%]'] - stats['Buy & Hold Return [%]']:.2f}%")
print(f"💡 Risk/Reward Ratio: {abs(stats['Best Trade [%]'] / stats['Worst Trade [%]']):.2f}:1")

# Optimization suggestions
if stats['Win Rate [%]'] < 40:
    print("\n⚠️  Low win rate - consider tightening entry filters")
if stats['Max. Drawdown [%]'] < -20:
    print("⚠️  High drawdown - consider reducing position size")
if stats['# Trades'] < 10:
    print("⚠️  Few trades - strategy may be over-optimized")
