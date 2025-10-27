import pandas as pd
import talib
from backtesting import Backtest, Strategy
from backtesting.lib import crossover

# Load and prepare data
data_path = '/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data/rbi/BTC-USD-15m.csv'
data = pd.read_csv(data_path)

# Clean column names
data.columns = data.columns.str.strip().str.lower()
data = data.drop(columns=[col for col in data.columns if 'unnamed' in col.lower()])

# Handle datetime index
data['Datetime'] = pd.to_datetime(data['datetime'])
data = data.set_index('Datetime')
data = data.drop('datetime', axis=1)

# Rename to proper case for backtesting.py
data = data.rename(columns={
    'open': 'Open',
    'high': 'High',
    'low': 'Low',
    'close': 'Close',
    'volume': 'Volume'
})

# Ensure required columns
data = data[['Open', 'High', 'Low', 'Close', 'Volume']]

class SequentialHarmony(Strategy):
    def init(self):
        self.ema200 = self.I(talib.EMA, self.data.Close, timeperiod=200)
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14)
        # Note: Full harmonic pattern detection (Gartley, Bat, etc.) requires advanced pivot/Fib logic;
        # approximated here via RSI oversold + reversal candle confluence for backtest purposes 🌙

    def next(self):
        # Skip if not enough data
        if len(self.data) < 205:  # Buffer for EMA200
            return

        # Only long positions, skip if already in position
        if self.position:
            return

        # Check previous 4 bars for consecutive down bars
        if len(self.data) < 5:
            return

        prev_closes = self.data.Close[-5:-1]
        prev_opens = self.data.Open[-5:-1]
        prev_lows = self.data.Low[-5:-1]

        is_down_sequence = (
            (prev_closes[0] < prev_opens[0]) and
            (prev_closes[1] < prev_opens[1]) and
            (prev_closes[2] < prev_opens[2]) and
            (prev_closes[3] < prev_opens[3]) and
            (prev_closes[1] < prev_closes[0]) and
            (prev_closes[2] < prev_closes[1]) and
            (prev_closes[3] < prev_closes[2])
        )

        # Current bar as reversal confirmation
        current_close = self.data.Close[-1]
        current_open = self.data.Open[-1]
        is_reversal = current_close > current_open  # Bullish candle

        # Downtrend filter
        in_downtrend = current_close < self.ema200[-1]

        # Oversold filter (proxy for harmonic PRZ + divergence)
        oversold = self.rsi[-1] < 30

        # Entry condition: 4 down bars + reversal + downtrend + oversold
        # Harmonic approximated by confluence; in practice, scan for patterns aligning with D point
        if is_down_sequence and is_reversal and in_downtrend and oversold:
            stop_price = min(prev_lows)  # Below lowest low of the 4 down bars
            entry_price = current_close
            risk = entry_price - stop_price

            if risk > 0:
                equity = self._broker.getvalue()
                risk_amount = 0.01 * equity  # 1% risk
                size = risk_amount / risk
                size = int(round(size))  # Ensure integer units as per rules

                # 1:2 RR for targets (primary 1:1, secondary 1:2 extension proxy)
                tp_price = entry_price + 2 * risk

                self.buy(size=size, sl=stop_price, tp=tp_price)
                print(f"🌙 Moon Dev's SequentialHarmony: 4 consecutive down bars exhausted! Reversal confirmed with RSI oversold. Entering LONG at {entry_price:.2f}, SL: {stop_price:.2f}, TP: {tp_price:.2f}, Size: {size} units 🚀✨")

# Run backtest
bt = Backtest(data, SequentialHarmony, cash=1000000, commission=0.001)
stats = bt.run()
print(stats)