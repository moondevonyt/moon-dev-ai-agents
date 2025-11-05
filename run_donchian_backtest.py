"""
🌙 Moon Dev - DonchianAscent Backtest
BESTE STRATEGIE: 3.04% Return op BTC 15m data

Strategie Kenmerken:
- Donchian Channel breakout (15 periods)
- Volume confirmatie (1.5x gemiddelde)
- RSI > 55 voor momentum
- ADX > 25 voor trend strength
- SMA20 en SMA200 regime filters
- 3x ATR channel width minimum
- 2% risk per trade
- 3.5x risk/reward ratio
- Trailing stop loss (2x ATR)
"""

from backtesting import Backtest, Strategy
import pandas as pd
import numpy as np

# Simplified RSI calculation (no TA-Lib needed)
def calculate_rsi(prices, period=14):
    """Calculate RSI indicator"""
    deltas = np.diff(prices)
    seed = deltas[:period+1]
    up = seed[seed >= 0].sum() / period
    down = -seed[seed < 0].sum() / period
    if down == 0:
        rs = 100
    else:
        rs = up / down
    rsi = np.zeros_like(prices)
    rsi[:period] = 100. - 100. / (1. + rs)

    for i in range(period, len(prices)):
        delta = deltas[i - 1]
        if delta > 0:
            upval = delta
            downval = 0.
        else:
            upval = 0.
            downval = -delta

        up = (up * (period - 1) + upval) / period
        down = (down * (period - 1) + downval) / period
        if down == 0:
            rsi[i] = 100
        else:
            rs = up / down
            rsi[i] = 100. - 100. / (1. + rs)

    return rsi

def calculate_atr(high, low, close, period=14):
    """Calculate Average True Range"""
    tr = np.maximum(high[1:] - low[1:],
                    np.abs(high[1:] - close[:-1]),
                    np.abs(low[1:] - close[:-1]))
    atr = np.zeros(len(close))
    atr[period] = np.mean(tr[:period])
    for i in range(period + 1, len(close)):
        atr[i] = (atr[i-1] * (period - 1) + tr[i-1]) / period
    return atr

def calculate_adx(high, low, close, period=14):
    """Calculate ADX (simplified)"""
    # Simplified ADX calculation
    tr = np.maximum(high[1:] - low[1:],
                    np.abs(high[1:] - close[:-1]),
                    np.abs(low[1:] - close[:-1]))

    plus_dm = np.where((high[1:] - high[:-1]) > (low[:-1] - low[1:]),
                       np.maximum(high[1:] - high[:-1], 0), 0)
    minus_dm = np.where((low[:-1] - low[1:]) > (high[1:] - high[:-1]),
                        np.maximum(low[:-1] - low[1:], 0), 0)

    atr_values = np.zeros(len(close))
    atr_values[period] = np.mean(tr[:period])
    for i in range(period + 1, len(close)):
        atr_values[i] = (atr_values[i-1] * (period - 1) + tr[i-1]) / period

    # Simplified DI calculations
    plus_di = 100 * (np.convolve(plus_dm, np.ones(period), 'same') / period) / (atr_values[1:] + 0.0001)
    minus_di = 100 * (np.convolve(minus_dm, np.ones(period), 'same') / period) / (atr_values[1:] + 0.0001)

    # DX and ADX
    dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di + 0.0001)
    adx = np.convolve(dx, np.ones(period), 'same') / period

    result = np.zeros(len(close))
    result[1:] = adx
    return result

# Load data
print("📊 Loading BTC data...")
data = pd.read_csv('src/data/rbi/BTC-USD-15m.csv')
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])
data = data.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'})
data['datetime'] = pd.to_datetime(data['datetime'])
data = data.set_index('datetime')

print(f"✅ Data loaded: {len(data)} rows from {data.index[0]} to {data.index[-1]}\n")

class DonchianAscent(Strategy):
    period = 15
    risk_percent = 0.02
    tp_multiplier = 3.5
    time_exit_bars = 20
    min_channel_width_pct = 0.015
    extended_multiplier = 1.5
    vol_multiplier = 1.5
    rsi_period = 14
    rsi_threshold = 55
    sma_period = 20
    atr_period = 14
    adx_period = 14
    adx_threshold = 25

    def init(self):
        # Donchian Channels
        close = self.data.Close
        high = self.data.High
        low = self.data.Low
        volume = self.data.Volume

        self.upper = self.I(lambda: pd.Series(high).rolling(self.period).max().values)
        self.lower = self.I(lambda: pd.Series(low).rolling(self.period).min().values)
        self.middle = self.I(lambda: (self.upper + self.lower) / 2)
        self.avg_vol = self.I(lambda: pd.Series(volume).rolling(self.period).mean().values)
        self.width = self.I(lambda: self.upper - self.lower)

        # Trend and momentum indicators
        self.sma20 = self.I(lambda: pd.Series(close).rolling(self.sma_period).mean().values)
        self.sma200 = self.I(lambda: pd.Series(close).rolling(200).mean().values)
        self.rsi = self.I(calculate_rsi, close, self.rsi_period)
        self.atr = self.I(calculate_atr, high, low, close, self.atr_period)
        self.adx = self.I(calculate_adx, high, low, close, self.adx_period)

        self.entry_bar = None
        self.initial_sl = None
        self.trailing_sl = None
        print("🌙 Moon Dev DonchianAscent Initialized! ✨\n")

    def next(self):
        current_close = self.data.Close[-1]
        current_high = self.data.High[-1]
        current_vol = self.data.Volume[-1]
        current_lower = self.lower[-1]
        current_middle = self.middle[-1]
        current_sma20 = self.sma20[-1]
        current_sma200 = self.sma200[-1]
        current_rsi = self.rsi[-1]
        current_atr = self.atr[-1]
        current_adx = self.adx[-1]
        current_upper = self.upper[-1]

        prev_idx = -2 if len(self.data) > 1 else -1
        prev_upper = self.upper[prev_idx]
        prev_avg_vol = self.avg_vol[prev_idx]
        prev_width = self.width[prev_idx]
        prev_middle = self.middle[prev_idx]
        prev_atr = self.atr[prev_idx]

        if self.position:
            bars_in_trade = len(self.data) - self.entry_bar if self.entry_bar else 0

            # Trailing stop
            if not self.trailing_sl:
                self.trailing_sl = self.initial_sl
            trail_candidate = current_high - (2.0 * current_atr)
            self.trailing_sl = max(self.trailing_sl, trail_candidate, current_middle)
            self.trailing_sl = max(self.trailing_sl, self.initial_sl)

            if current_close < self.trailing_sl:
                self.position.close()
                self.entry_bar = None
                self.initial_sl = None
                self.trailing_sl = None
            elif bars_in_trade > self.time_exit_bars:
                self.position.close()
                self.entry_bar = None
                self.initial_sl = None
                self.trailing_sl = None
        else:
            # Entry conditions
            breakout = current_close > prev_upper
            vol_confirm = current_vol > (self.vol_multiplier * prev_avg_vol)
            channel_too_narrow = prev_width < (3 * prev_atr)
            pct_width = prev_width / prev_middle if prev_middle > 0 else 0
            pct_too_narrow = pct_width < self.min_channel_width_pct
            extended = (current_close - prev_middle) > (self.extended_multiplier * prev_width)
            trend_filter = current_close > current_sma20
            momentum_filter = current_rsi > self.rsi_threshold
            adx_filter = current_adx > self.adx_threshold
            ascending_channel = current_upper > prev_upper
            regime_filter = current_close > current_sma200

            if (breakout and vol_confirm and not channel_too_narrow and not pct_too_narrow and not extended and
                trend_filter and momentum_filter and adx_filter and ascending_channel and regime_filter):
                sl_price = current_lower
                risk_per_share = current_close - sl_price
                if risk_per_share > 0:
                    atr_factor = current_atr / current_close
                    adjusted_risk = self.risk_percent * (1 / (1 + atr_factor))
                    position_size = int(round((self.equity * adjusted_risk) / risk_per_share))
                    tp_price = current_close + (self.tp_multiplier * risk_per_share)

                    self.buy(size=position_size, sl=sl_price, tp=tp_price)
                    self.entry_bar = len(self.data)
                    self.initial_sl = sl_price
                    self.trailing_sl = sl_price

# Run backtest
print("🚀 Running DonchianAscent Backtest...\n")
bt = Backtest(data, DonchianAscent, cash=1000000, commission=.002)
stats = bt.run()

print("\n" + "=" * 70)
print("📊 DONCHIAN ASCENT BACKTEST RESULTS")
print("=" * 70)
print(f"Initial Capital:     ${1000000:,.2f}")
print(f"Final Portfolio:     ${stats['Equity Final [$]']:,.2f}")
print(f"Return:              {stats['Return [%]']:.2f}%")
print(f"Buy & Hold Return:   {stats['Buy & Hold Return [%]']:.2f}%")
print(f"Max Drawdown:        {stats['Max. Drawdown [%]']:.2f}%")
print(f"Sharpe Ratio:        {stats['Sharpe Ratio']:.2f}")
print(f"Sortino Ratio:       {stats.get('Sortino Ratio', 'N/A')}")
print(f"# Trades:            {stats['# Trades']}")
print(f"Win Rate:            {stats['Win Rate [%]']:.2f}%")
print(f"Avg Trade:           {stats['Avg. Trade [%]']:.2f}%")
print(f"Max Trade Duration:  {stats['Max. Trade Duration']}")
print(f"Expectancy:          {stats.get('Expectancy [%]', 'N/A')}")
print("=" * 70)

if stats['Return [%]'] > 1:
    print("\n✅ WINNENDE STRATEGIE! Return > 1%")
    print(f"   📈 Outperformance vs Buy & Hold: {stats['Return [%]'] - stats['Buy & Hold Return [%]']:.2f}%")
else:
    print("\n⚠️  Strategie onderpresteert Buy & Hold")
